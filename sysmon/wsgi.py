"""Administrative systems monitoring."""

from datetime import date, timedelta
from typing import Union
from filedb import File
from his import ACCOUNT, CUSTOMER, Application, authenticated, authorized, root, admin
from hwdb import SystemOffline, Deployment, System
from mdb import Customer, Company

from requests.exceptions import Timeout
from wsgilib import Binary, JSON, JSONMessage, get_int, get_bool

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
from sysmon.mailing import send_mailing, get_newsletter_by_date, send_test_mails
from sysmon.offline_history import get_offline_systems
from sysmon.offline_history import update_offline_systems
from sysmon.orm import (
    UserNotificationEmail,
    Newsletter,
    ExtraUserNotificationEmail,
    Newsletterlistitems,
    StatisticUserNotificationEmail,
    Warningmail,
)
from sysmon.json import check_results_to_json
from sysmon.preview import generate_preview_token


__all__ = ["APPLICATION"]


APPLICATION = Application("sysmon")
SERVICE_UNITS = {"hipster": "hipster.service", "sysmon": "sysmon.service"}


@authenticated
@authorized("sysmon")
@root
@APPLICATION.route(
    "/patch_warningmail/<int:warningmail>", methods=["POST"], strict_slashes=False
)
def patch_warningmail(warningmail: int):
    """Patches a  warningmail."""
    warning = Warningmail.select().where(Warningmail.id == warningmail).get()
    warning.patch_json(request.json)
    return JSON({"status": warning.save()})


@authenticated
@authorized("sysmon")
@root
@APPLICATION.route("/warningmail", methods=["GET"], strict_slashes=False)
def get_warningmail():
    """Gets Warningmail."""
    return JSON(Warningmail.select().get())


@authenticated
@authorized("sysmon")
@root
@APPLICATION.route("/customer_add", methods=["POST"], strict_slashes=False)
def add_customer():
    """Adds Customer and basic company information."""

    customer = Customer.from_json(request.json["customer"])

    customer.company = Company.from_json(request.json["company"])
    customer.company.save()
    customer.save(force_insert=True)
    return JSONMessage("New Customer created." + str(customer.id), status=200)


@authenticated
@authorized("sysmon")
@root
@APPLICATION.route(
    "/send_test_mails/<int:newsletter>", methods=["POST"], strict_slashes=False
)
def test_mail(newsletter: int):
    """Sends a Newsletter test to Account.email."""
    send_test_mails(newsletter)
    return JSONMessage("Testmail sent.", status=200)


@authenticated
@authorized("sysmon")
@root
@APPLICATION.route("/newsletter_by_date", methods=["GET"], strict_slashes=False)
def newsletter_by_date():
    """Gets Newsletter for now."""
    now = date.today()
    return JSON(get_newsletter_by_date(now).to_json())


@authenticated
@authorized("sysmon")
@root
@APPLICATION.route(
    "/patch_newsletter/<int:newsletter>", methods=["POST"], strict_slashes=False
)
def patch_newsletter(newsletter: int):
    """Patches a  Newsletter."""
    nl = Newsletter.select().where(Newsletter.id == newsletter).get()
    nl.patch_json(request.json)
    return JSON({"status": nl.save()})


@authenticated
@authorized("sysmon")
@root
@APPLICATION.route(
    "/newsletter_list_patch/<int:listitem>", methods=["POST"], strict_slashes=False
)
def patch_listitem(listitem: int):
    """Patches a  Newsletter list item."""
    li = Newsletterlistitems.select().where(Newsletterlistitems.id == listitem).get()
    li.patch_json(request.json)
    li.save()
    return JSON(li.to_json())


@authenticated
@authorized("sysmon")
@root
@APPLICATION.route("/newsletter_list_add/", methods=["POST"], strict_slashes=False)
def add_listitem():
    """Adds a  Newsletter list item."""
    li = Newsletterlistitems.from_json(request.json)
    li.save()
    return JSON(li.to_json())


@authenticated
@authorized("sysmon")
@root
@APPLICATION.route(
    "/newsletter_list_del/<int:listid>", methods=["POST"], strict_slashes=False
)
def del_listitem(listid: int):
    """Deletes a  Newsletter list item."""
    Newsletterlistitems.select().where(
        Newsletterlistitems.id == listid
    ).get().delete_instance()
    return JSON({"status": "deleted list"})


@authenticated
@authorized("sysmon")
@root
@APPLICATION.route("/add_newsletter", methods=["POST"], strict_slashes=False)
def add_newsletter():
    """Adds a  Newsletter ."""
    nl = Newsletter.from_json(request.json)
    nl.is_default = 0
    nl.save()
    return JSON(nl.to_json())


@APPLICATION.route(
    "/newsletter/<int:newsletter>", methods=["GET"], strict_slashes=False
)
@authenticated
@authorized("sysmon")
def get_newsletter(newsletter: int):
    """Get Newsletter by id."""
    return JSON(Newsletter.select().where(Newsletter.id == newsletter).get().to_json())


@APPLICATION.route(
    "/newsletter-image/<int:newsletter>", methods=["POST"], strict_slashes=False
)
@authenticated
@authorized("sysmon")
def post(newsletter: int) -> JSONMessage:
    """Adds a new file."""
    data = request.files["file"]
    file = File.from_bytes(data.read())
    file.save()
    nl = Newsletter.select().where(Newsletter.id == newsletter).get()
    nl.image = file.id
    nl.save()
    return JSONMessage("The file has been created.", id=file.id, status=201)


@APPLICATION.route(
    "/newsletter-image/<int:image>", methods=["DELETE"], strict_slashes=False
)
@authenticated
@authorized("sysmon")
def delete_file(image: int):
    nl = Newsletter.select().where(Newsletter.image == image).get()
    nl.image = None
    nl.save()
    File.select().where(File.id == image).get().delete()
    return JSONMessage("The file has deleted.", id=image, status=201)


@APPLICATION.route(
    "/newsletter-image/<int:image>", methods=["GET"], strict_slashes=False
)
def get_file(image: int):
    """Get image for Newsletter."""
    return Binary(File.select().where(File.id == image).get().bytes)


@APPLICATION.route("/default_newsletter", methods=["GET"], strict_slashes=False)
@authenticated
@authorized("sysmon")
def get_default_newsletters():
    """Get default Newsletter"""

    return JSON(Newsletter.select().where(Newsletter.isdefault == 1).get().to_json())


@APPLICATION.route("/newsletters", methods=["GET"], strict_slashes=False)
@authenticated
@authorized("sysmon")
def get_newsletters():
    """List all Newsletters."""

    return JSON(
        [
            newsletter.to_json()
            for newsletter in Newsletter.select().where(Newsletter.isdefault == 0)
        ]
    )


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


@APPLICATION.route("/user-notification-emails", methods=["GET"], strict_slashes=False)
@authorized("sysmon")
def get_emails() -> JSON:
    """Deletes the respective message."""

    return JSON(
        [
            email.to_json()
            for email in UserNotificationEmail.select().where(
                UserNotificationEmail.customer == CUSTOMER.id
            )
        ]
    )


@APPLICATION.route("/user-notification-emails", methods=["POST"], strict_slashes=False)
@authorized("sysmon")
@root
def set_emails() -> JSONMessage:
    """Replaces all email address of the respective customer."""

    for email in UserNotificationEmail.select().where(
        UserNotificationEmail.customer == CUSTOMER.id
    ):
        email.delete_instance()

    for email in request.json:
        email = UserNotificationEmail.from_json(email, CUSTOMER.id)
        email.save()

    return JSONMessage("The emails list has been updated.", status=200)


@APPLICATION.route(
    "/extra-user-notification-emails", methods=["GET"], strict_slashes=False
)
@authorized("sysmon")
def get_extra_emails() -> JSON:
    """Get all extra emails"""

    return JSON([email.to_json() for email in ExtraUserNotificationEmail.select()])


@APPLICATION.route(
    "/extra-user-notification-emails", methods=["POST"], strict_slashes=False
)
@authorized("sysmon")
@root
def set_extra_emails() -> JSONMessage:
    """set extra email addresses."""

    ExtraUserNotificationEmail.delete().execute()
    for email in request.json:
        email = ExtraUserNotificationEmail.from_json(email)
        email.save()

    return JSONMessage("The emails list has been updated.", status=200)


@APPLICATION.route(
    "/statistic-user-notification-emails", methods=["GET"], strict_slashes=False
)
@authorized("sysmon")
def get_statistic_emails() -> JSON:
    """Get all statistic emails"""

    return JSON([email.to_json() for email in StatisticUserNotificationEmail.select()])


@APPLICATION.route(
    "/statistic-user-notification-emails", methods=["POST"], strict_slashes=False
)
@authorized("sysmon")
@root
def set_statistic_emails() -> JSONMessage:
    """set statistic email addresses."""

    StatisticUserNotificationEmail.delete().execute()
    for email in request.json:
        email = StatisticUserNotificationEmail.from_json(email)
        email.save()

    return JSONMessage("The emails list has been updated.", status=200)


@authenticated
@authorized("sysmon")
@root
@APPLICATION.route("/send_statistic_test_mail", methods=["POST"], strict_slashes=False)
def statistic_test_mail() -> JSONMessage:
    return JSONMessage("Statistic Testmail sent.", status=200)
