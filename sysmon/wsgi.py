"""Administrative systems monitoring."""

from datetime import timedelta
from traceback import print_exc

from flask import request

from his import authenticated, authorized, Application
from hwdb import SystemOffline, System
from timelib import strpdatetime
from wsgilib import Binary, JSON

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
def list_stats():
    """Lists systems and their stats."""

    systems = get_systems()
    begin = strpdatetime(request.headers.get('begin'))
    end = strpdatetime(request.headers.get('end'))
    json = get_systems_checks(systems, begin=begin, end=end)
    return JSON(json)


@APPLICATION.route('/details/<int:system>', methods=['GET'],
                   strict_slashes=False)
@authenticated
@authorized('sysmon')
def system_details(system):
    """Lists uptime details of a system."""

    try:
        system = get_system(system)
    except System.DoesNotExist:
        return ('No such system.', 404)

    select = OnlineCheck.system == system
    start = strpdatetime(request.headers.get('from'))
    end = strpdatetime(request.headers.get('until'))

    if start:
        select &= OnlineCheck.timestamp >= start

    if end:
        end += timedelta(days=1)    # Compensate for rest of day.
        select &= OnlineCheck.timestamp <= end

    online_checks = OnlineCheck.select().where(select)
    online_checks = online_checks.order_by(OnlineCheck.timestamp)
    return JSON([online_check.to_json() for online_check in online_checks])


@APPLICATION.route('/check/<int:system>', methods=['GET'],
                   strict_slashes=False)
@authenticated
@authorized('sysmon')
def check_system(system):
    """Performs a system check."""

    try:
        system = get_system(system)
    except System.DoesNotExist:
        return ('No such system.', 404)

    online_check = OnlineCheck.run(system)
    return JSON(online_check.to_json())


@APPLICATION.route('/screenshot/<int:system>', methods=['GET'],
                   strict_slashes=False)
@authenticated
@authorized('sysmon')
def get_screenshot(system):
    """Returns a screenshot of the system."""

    try:
        system = get_system(system)
    except System.DoesNotExist:
        return ('No such system.', 404)

    try:
        response = system.screenshot()
    except SystemOffline:
        return (print_exc(), 503)

    if response.status_code != 200:
        return ('Could not take screenshot.', 500)

    return Binary(response.content)


@APPLICATION.route('/enduser', methods=['GET'], strict_slashes=False)
@authenticated
@authorized('sysmon')
def endsuser_states():
    """Checks the system states for end-users."""

    return JSON(check_customer_systems())
