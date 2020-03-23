"""Administrative systems monitoring."""

from flask import request

from his import authenticated, authorized, Application
from timelib import strpdatetime
from wsgilib import JSON

from sysmon.functions import check_customer_systems
from sysmon.functions import get_customers
from sysmon.functions import get_systems
from sysmon.functions import get_systems_checks
from sysmon.functions import get_types
from sysmon.functions import selected_customers
from sysmon.functions import selected_systems
from sysmon.functions import selected_types


__all__ = ['APPLICATION']


APPLICATION = Application('sysmon')


@APPLICATION.route('/stats', methods=['GET'], strict_slashes=False)
@authenticated
def list_stats():
    """Lists systems and their stats."""

    systems = get_systems(
        systems=selected_systems(), customers=selected_customers(),
        types=selected_types())
    begin = strpdatetime(request.headers.get('begin'))
    end = strpdatetime(request.headers.get('end'))
    json = get_systems_checks(systems, begin=begin, end=end)
    return JSON(json)


@APPLICATION.route('/customers', methods=['GET'], strict_slashes=False)
@authenticated
def list_customers():
    """Lists all customers."""

    json = [customer.to_json(cascade=2) for customer in get_customers()]
    return JSON(json)


@APPLICATION.route('/types', methods=['GET'], strict_slashes=False)
@authenticated
def list_types():
    """Lists all types."""

    json = [type.value for type in get_types()]
    return JSON(json)


@APPLICATION.route('/enduser', methods=['GET'], strict_slashes=False)
@authenticated
@authorized('sysmon')
def endsuser_states():
    """Checks the system states for end-users."""

    return JSON(check_customer_systems())
