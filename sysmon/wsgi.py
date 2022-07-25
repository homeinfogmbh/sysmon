"""Administrative systems monitoring."""

from typing import Union

from his import ACCOUNT, CUSTOMER, authenticated, authorized, Application
from hwdb import SystemOffline, System
from wsgilib import Binary, JSON, JSONMessage

from sysmon.blacklist import load_blacklist
from sysmon.checks import check_system
from sysmon.checks import get_sysinfo
from sysmon.checks import hipster_status
from sysmon.checks import current_application_version
from sysmon.enumerations import SuccessFailedUnsupported
from sysmon.functions import get_check_results_for_system
from sysmon.functions import get_customer_check_results
from sysmon.functions import get_system
from sysmon.functions import get_latest_check_results_per_system
from sysmon.json import check_results_to_json


__all__ = ['APPLICATION']


APPLICATION = Application('sysmon')


@APPLICATION.route('/checks', methods=['GET'], strict_slashes=False)
@authenticated
@authorized('sysmon')
def list_latest_stats() -> JSON:
    """List systems and their latest stats."""

    return JSON(check_results_to_json(
        get_latest_check_results_per_system(ACCOUNT)
    ))


@APPLICATION.route(
    '/checks/<int:system>',
    methods=['GET'],
    strict_slashes=False
)
@authenticated
@authorized('sysmon')
def list_stats(system: int) -> JSON:
    """List latest stats of a system."""

    return JSON(check_results_to_json(
        get_check_results_for_system(system, ACCOUNT)
    ))


@APPLICATION.route(
    '/check/<int:system>',
    methods=['GET'],
    strict_slashes=False
)
@authenticated
@authorized('sysmon')
def do_check_system(system: int) -> JSON:
    """List uptime details of a system."""

    system = get_system(system, ACCOUNT)
    check_result = check_system(system)
    check_result.save()
    return JSON(check_result.to_json())


@APPLICATION.route(
    '/screenshot/<int:system>',
    methods=['GET'],
    strict_slashes=False
)
@authenticated
@authorized('sysmon')
def get_screenshot(system: int) -> Union[Binary, JSONMessage]:
    """Return a screenshot of the system."""

    try:
        system = get_system(system, ACCOUNT)
    except System.DoesNotExist:
        return JSONMessage('No such system.', status=404)

    try:
        response = system.screenshot()
    except SystemOffline:
        return JSONMessage('System is offline.', status=503)

    if response.status_code != 200:
        return JSONMessage('Could not take screenshot.', status=500)

    return Binary(response.content)


@APPLICATION.route('/enduser', methods=['GET'], strict_slashes=False)
@authenticated
@authorized('sysmon')
def enduser_states() -> Union[JSON, JSONMessage]:
    """Check the system states for end-users."""

    return JSON([
        check_result.to_json() for check_result in
        get_customer_check_results(CUSTOMER.id)
    ])


@APPLICATION.route('/hipster-status', methods=['GET'], strict_slashes=False)
@authenticated
@authorized('sysmon')
def hipster_status_() -> JSON:
    """Return the status of the HIPSTER daemon."""

    return JSON(hipster_status())


@APPLICATION.route(
    '/current-application-version/<typ>',
    methods=['GET'],
    strict_slashes=False
)
@authenticated
@authorized('sysmon')
def current_application_version_(typ: str) -> JSON:
    """Return the status of the HIPSTER daemon."""

    return JSON(current_application_version(typ))


@APPLICATION.route(
    '/sysinfo/<int:ident>',
    methods=['GET'],
    strict_slashes=False
)
@authenticated
@authorized('sysmon')
def sysinfo_(ident: int) -> Union[JSON, JSONMessage]:
    """Return the sysinfo dict of the given system."""

    http_request, sysinfo = get_sysinfo(get_system(ident, ACCOUNT))

    if http_request is SuccessFailedUnsupported.SUCCESS:
        return JSON(sysinfo)

    if http_request is SuccessFailedUnsupported.UNSUPPORTED:
        return JSONMessage('Sysinfo unsupported on this system.', status=400)

    return JSONMessage('Sysinfo failed on this system.', status=400)


@APPLICATION.route(
    '/blacklist',
    methods=['GET'],
    strict_slashes=False
)
@authenticated
@authorized('sysmon')
def blacklist() -> JSON:
    """List blacklisted systems."""

    return JSON([
        system.to_json(cascade=True) for system in load_blacklist(ACCOUNT)
    ])
