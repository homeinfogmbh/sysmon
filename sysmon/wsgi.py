"""Administrative systems monitoring."""

from datetime import datetime
from traceback import format_exc
from typing import Union

from flask import request

from his import ACCOUNT, CUSTOMER, authenticated, authorized, Application
from hwdb import SystemOffline, System
from wsgilib import Binary, JSON, JSONMessage

from sysmon.checks import check_system
from sysmon.functions import get_check_results
from sysmon.functions import get_customer_check_results
from sysmon.functions import get_system
from sysmon.json import check_results_to_json


__all__ = ['APPLICATION']


APPLICATION = Application('sysmon')


@APPLICATION.route('/checks', methods=['GET'], strict_slashes=False)
@authenticated
@authorized('sysmon')
def list_stats() -> JSON:
    """Lists systems and their stats."""

    if (begin := request.headers.get('begin')) is not None:
        begin = datetime.fromisoformat(begin)

    if (end := request.headers.get('end')) is not None:
        end = datetime.fromisoformat(begin)

    check_results = get_check_results(ACCOUNT, begin=begin, end=end)
    return JSON(check_results_to_json(check_results))


@APPLICATION.route(
    '/check/<int:system>',
    methods=['GET'],
    strict_slashes=False
)
@authenticated
@authorized('sysmon')
def do_check_system(system: int) -> JSON:
    """Lists uptime details of a system."""

    system = get_system(system, ACCOUNT)
    check_result = check_system(system)
    return JSON(check_result.to_json())


@APPLICATION.route(
    '/screenshot/<int:system>',
    methods=['GET'],
    strict_slashes=False
)
@authenticated
@authorized('sysmon')
def get_screenshot(system: int) -> Union[Binary, JSONMessage]:
    """Returns a screenshot of the system."""

    try:
        system = get_system(system, ACCOUNT)
    except System.DoesNotExist:
        return JSONMessage('No such system.', status=404)

    try:
        response = system.screenshot()
    except SystemOffline:
        return JSONMessage(format_exc(), status=503)

    if response.status_code != 200:
        return JSONMessage('Could not take screenshot.', status=500)

    return Binary(response.content)


@APPLICATION.route('/enduser', methods=['GET'], strict_slashes=False)
@authenticated
@authorized('sysmon')
def enduser_states() -> Union[JSON, JSONMessage]:
    """Checks the system states for end-users."""

    return JSON([
        check_result.to_json() for check_result in
        get_customer_check_results(CUSTOMER.id)
    ])
