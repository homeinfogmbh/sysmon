"""Administrative systems monitoring."""

from datetime import datetime
from traceback import format_exc
from typing import Union

from flask import request

from his import ACCOUNT, CUSTOMER, authenticated, authorized, Application
from hwdb import SystemOffline, System
from wsgilib import Binary, JSON, JSONMessage

from sysmon.checks import check_system
from sysmon.exceptions import FailureLimitExceeded
from sysmon.functions import check_customer_systems
from sysmon.functions import get_system
from sysmon.functions import get_check_results
from sysmon.functions import get_check_results_of_system


__all__ = ['APPLICATION']


APPLICATION = Application('sysmon')


@APPLICATION.route('/stats', methods=['GET'], strict_slashes=False)
@authenticated
@authorized('sysmon')
def list_stats() -> JSON:
    """Lists systems and their stats."""

    if (begin := request.headers.get('begin')) is not None:
        begin = datetime.fromisoformat(begin)

    if (end := request.headers.get('end')) is not None:
        end = datetime.fromisoformat(begin)

    check_results = get_check_results(ACCOUNT.id, begin=begin, end=end)
    return JSON([
        check_result.to_json(cascade=3) for check_result in check_results
    ])


@APPLICATION.route(
    '/details/<int:system>',
    methods=['GET'],
    strict_slashes=False
)
@authenticated
@authorized('sysmon')
def system_details(system: int) -> Union[JSON, JSONMessage]:
    """Lists uptime details of a system."""

    if (begin := request.headers.get('begin')) is not None:
        begin = datetime.fromisoformat(begin)

    if (end := request.headers.get('end')) is not None:
        end = datetime.fromisoformat(end)

    check_results = get_check_results_of_system(
        system, ACCOUNT.id, begin=begin, end=end
    )
    return JSON([
        check_result.to_json(cascade=3) for check_result in check_results
    ])


@APPLICATION.route(
    '/check/<int:system>',
    methods=['GET'],
    strict_slashes=False
)
@authenticated
@authorized('sysmon')
def run_system_check(system: int) -> Union[JSON, JSONMessage]:
    """Performs a system check."""

    try:
        system = get_system(system, ACCOUNT.id)
    except System.DoesNotExist:
        return JSONMessage('No such system.', status=404)

    return JSON(check_system(system).to_json(cascade=3))


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
        system = get_system(system, ACCOUNT.id)
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
def endsuser_states() -> Union[JSON, JSONMessage]:
    """Checks the system states for end-users."""

    try:
        return JSON(check_customer_systems(CUSTOMER.id))
    except FailureLimitExceeded:
        return JSONMessage('Failure limit exceeded.', status=400)
