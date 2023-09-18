"""Administrative systems monitoring."""

from datetime import date, timedelta
from typing import Union

from his import ACCOUNT, CUSTOMER, Application, authenticated, authorized, root
from hwdb import SystemOffline, Deployment, System
from notificationlib import get_wsgi_funcs
from requests.exceptions import Timeout
from wsgilib import Binary, JSON, JSONMessage, get_int

from flask import request

from sysmon.blacklist import authorized_blacklist, load_blacklist
from sysmon.checks import check_system
from sysmon.checks.common import get_sysinfo
from sysmon.checks.systemd import unit_status
from sysmon.checks.application import current_application_version
from sysmon.enumerations import SuccessFailedUnsupported
from sysmon.functions import get_check_results_for_system
from sysmon.functions import get_customer_check_results
from sysmon.functions import get_system
from sysmon.functions import get_latest_check_results_per_system
from sysmon.mailing import send_mailing
from sysmon.offline_history import get_offline_systems
from sysmon.offline_history import update_offline_systems
from sysmon.orm import UserNotificationEmail, Newsletter
from sysmon.json import check_results_to_json
from sysmon.preview import generate_preview_token


__all__ = ["APPLICATION"]


APPLICATION = Application("sysmon")
SERVICE_UNITS = {"hipster": "hipster.service", "sysmon": "sysmon.service"}


@APPLICATION.route("/patch_newsletter/<int:newsletter>", methods=["POST"], strict_slashes=False)
def patch_newsletter(newsletter: int):
    nl = Newsletter.select().where(Newsletter.id == newsletter).get()
    nl.patch_json(request.json)
    return JSON({"status": nl.save()})

@APPLICATION.route("/add_newsletter", methods=["POST"], strict_slashes=False)
def add_newsletter():
    nl = Newsletter.from_json(request.json)
    return JSON({"status": nl.save()})


@APPLICATION.route("/newsletter/<int:newsletter>", methods=["GET"], strict_slashes=False)
@authenticated
@authorized("sysmon")
def get_newsletter(newsletter: int):
    return JSON(list(Newsletter.select().where(Newsletter.id == newsletter).dicts()))


@APPLICATION.route("/newsletters", methods=["GET"], strict_slashes=False)
@authenticated
@authorized("sysmon")
def get_newsletters():
    """List Newsletters."""

    return JSON(list(Newsletter.select().where(1 == 1).dicts()))


@APPLICATION.route("/checks", methods=["GET"], strict_slashes=False)
@authenticated
@authorized("sysmon")
def list_latest_stats() -> JSON:
    """List systems and their latest stats."""

    return JSON(
        check_results_to_json(
            get_latest_check_results_per_system(
                ACCOUNT, date.today() - timedelta(days=get_int("days-ago", default=0))
            )
        )
    )


@APPLICATION.route("/checks/<int:system>", methods=["GET"], strict_slashes=False)
@authenticated
@authorized("sysmon")
def list_stats(system: int) -> JSON:
    """List latest stats of a system."""

    return JSON(check_results_to_json(get_check_results_for_system(system, ACCOUNT)))


@APPLICATION.route("/check/<int:system>", methods=["GET"], strict_slashes=False)
@authenticated
@authorized("sysmon")
def do_check_system(system: int) -> JSON:
    """List uptime details of a system."""

    system = get_system(system, ACCOUNT)
    check_result = check_system(system)
    update_offline_systems(date.today(), blacklist=load_blacklist())
    return JSON(check_result.to_json())


@APPLICATION.route("/screenshot/<int:system>", methods=["GET"], strict_slashes=False)
@authenticated
@authorized("sysmon")
def get_screenshot(system: int) -> Union[Binary, JSONMessage]:
    """Return a screenshot of the system."""

    try:
        system = get_system(system, ACCOUNT)
    except System.DoesNotExist:
        return JSONMessage("No such system.", status=404)

    try:
        response = system.screenshot()
    except SystemOffline:
        return JSONMessage("System is offline.", status=503)
    except ConnectionError:
        return JSONMessage("Connection error while requesting screenshot.", status=503)
    except Timeout:
        return JSONMessage(
            "Connection timed out while receiving screenshot.", status=503
        )

    if response.status_code != 200:
        return JSONMessage("Could not take screenshot.", status=500)

    return Binary(response.content)


@APPLICATION.route("/enduser", methods=["GET"], strict_slashes=False)
@authenticated
@authorized("sysmon")
def enduser_states() -> Union[JSON, JSONMessage]:
    """Check the system states for end-users."""

    return JSON(
        [
            check_result.to_json()
            for check_result in get_customer_check_results(CUSTOMER.id)
        ]
    )


@APPLICATION.route("/<service>-status", methods=["GET"], strict_slashes=False)
@authenticated
@authorized("sysmon")
def service_status(service: str) -> Union[JSON, JSONMessage]:
    """Return the status of the given system service."""

    try:
        unit = SERVICE_UNITS[service]
    except KeyError:
        return JSONMessage("Invalid service.", service=service, status=400)

    return JSON(unit_status(unit))


@APPLICATION.route(
    "/current-application-version/<typ>", methods=["GET"], strict_slashes=False
)
@authenticated
@authorized("sysmon")
def current_application_version_(typ: str) -> JSON:
    """Return the status of the HIPSTER daemon."""

    return JSON(current_application_version(typ))


@APPLICATION.route("/sysinfo/<int:ident>", methods=["GET"], strict_slashes=False)
@authenticated
@authorized("sysmon")
def sysinfo_(ident: int) -> Union[JSON, JSONMessage]:
    """Return the sysinfo dict of the given system."""

    http_request, sysinfo = get_sysinfo(get_system(ident, ACCOUNT))

    if http_request is SuccessFailedUnsupported.SUCCESS:
        return JSON(sysinfo)

    if http_request is SuccessFailedUnsupported.UNSUPPORTED:
        return JSONMessage("Sysinfo unsupported on this system.", status=400)

    return JSONMessage("Sysinfo failed on this system.", status=400)


@APPLICATION.route("/blacklist", methods=["GET"], strict_slashes=False)
@authenticated
@authorized("sysmon")
def get_blacklist() -> JSON:
    """List blacklisted systems."""

    return JSON(
        [system.to_json(cascade=True) for system in authorized_blacklist(ACCOUNT)]
    )


@APPLICATION.route("/offline-history/<int:days>", methods=["GET"], strict_slashes=False)
@authenticated
@authorized("sysmon")
def offline_history(days: int) -> JSON:
    """List offline systems count for the given amount of days."""

    return JSON(get_offline_systems(ACCOUNT, date.today() - timedelta(days=days)))


@APPLICATION.route("/preview/<int:deployment>", methods=["GET"], strict_slashes=False)
@authenticated
@authorized("sysmon")
def gen_preview_token(deployment: int) -> Union[JSON, JSONMessage]:
    """Generate a preview token for the given deployment."""

    try:
        token = generate_preview_token(deployment, ACCOUNT)
    except Deployment.DoesNotExist:
        return JSONMessage("No such deployment.", status=404)

    return JSON({"token": token.token.hex})


@APPLICATION.route("/send-mailing", methods=["GET"], strict_slashes=False)
@authenticated
@authorized("sysmon")
@root
def _send_mailing() -> Union[JSON, JSONMessage]:
    """Send monthly customer statistics mailing manually."""

    return JSON(send_mailing())


for function, method in zip(
    get_wsgi_funcs("sysmon", UserNotificationEmail), ["GET", "POST"]
):
    APPLICATION.route(
        "/user-notification-emails", methods=[method], strict_slashes=False
    )(function)
