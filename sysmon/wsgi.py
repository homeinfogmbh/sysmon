"""Administrative systems monitoring."""

from datetime import timedelta

from flask import request

from his import authenticated, authorized, Application
from hwdb import System
from timelib import strpdatetime
from wsgilib import JSON

from sysmon.functions import check_customer_systems
from sysmon.functions import get_system
from sysmon.functions import get_systems
from sysmon.functions import get_systems_checks
from sysmon.orm import OnlineCheck


__all__ = ['APPLICATION']


APPLICATION = Application('sysmon')


@APPLICATION.route('/stats', methods=['GET'], strict_slashes=False)
@authenticated
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
def check_system(system):
    """Performs a system check."""

    try:
        system = get_system(system)
    except System.DoesNotExist:
        return ('No such system.', 404)

    online_check = OnlineCheck.run(system)
    return JSON(online_check.to_json())


@APPLICATION.route('/enduser', methods=['GET'], strict_slashes=False)
@authenticated
@authorized('sysmon')
def endsuser_states():
    """Checks the system states for end-users."""

    return JSON(check_customer_systems())
