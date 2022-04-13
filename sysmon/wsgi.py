"""Administrative systems monitoring."""

from datetime import datetime, timedelta
from traceback import format_exc
from typing import Union

from flask import request

from his import ACCOUNT, CUSTOMER, authenticated, authorized, Application
from hwdb import SystemOffline, System
from wsgilib import Binary, JSON, JSONMessage

from sysmon.exceptions import FailureLimitExceeded
from sysmon.functions import check_customer_systems
from sysmon.functions import get_system
from sysmon.functions import get_systems
from sysmon.functions import get_systems_checks
from sysmon.orm import OnlineCheck


__all__ = ['APPLICATION']


APPLICATION = Application('sysmon')


@APPLICATION.route('/stats', methods=['GET'], strict_slashes=False)
@authenticated
@authorized('sysmon')
def list_stats() -> JSON:
    """Lists systems and their stats."""

    systems = get_systems(ACCOUNT.id)

    if (begin := request.headers.get('begin')) is not None:
        begin = datetime.fromisoformat(begin)

    if (end := request.headers.get('end')) is not None:
        end = datetime.fromisoformat(begin)

    json = get_systems_checks(systems, begin=begin, end=end)
    return JSON(json)


@APPLICATION.route(
    '/details/<int:system>',
    methods=['GET'],
    strict_slashes=False
)
@authenticated
@authorized('sysmon')
def system_details(system: int) -> Union[JSON, JSONMessage]:
    """Lists uptime details of a system."""

    try:
        system = get_system(syste, ACCOUNT.id)
    except System.DoesNotExist:
        return JSONMessage('No such system.', status=404)

    select = OnlineCheck.system == system

    if (start := request.headers.get('from')) is not None:
        start = datetime.fromisoformat(start)

    if (end := request.headers.get('until')) is not None:
        end = datetime.fromisoformat(end)

    if start:
        select &= OnlineCheck.timestamp >= start

    if end:
        end += timedelta(days=1)    # Compensate for rest of day.
        select &= OnlineCheck.timestamp <= end

    online_checks = OnlineCheck.select().where(select)
    online_checks = online_checks.order_by(OnlineCheck.timestamp)
    return JSON([online_check.to_json() for online_check in online_checks])


@APPLICATION.route(
    '/check/<int:system>',
    methods=['GET'],
    strict_slashes=False
)
@authenticated
@authorized('sysmon')
def check_system(system: int) -> Union[JSON, JSONMessage]:
    """Performs a system check."""

    try:
        system = get_system(system, ACCOUNT.id)
    except System.DoesNotExist:
        return JSONMessage('No such system.', status=404)

    online_check = OnlineCheck.run(system)
    return JSON(online_check.to_json())


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
