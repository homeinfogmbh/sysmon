"""Common functions."""

from datetime import datetime, timedelta

from flask import request

from functoolsplus import coerce
from his import ACCOUNT, CUSTOMER
from terminallib import Deployment, Type, System
from wsgilib import Error

from sysmon.orm import CHECKS, OnlineCheck, TypeAdmin


__all__ = [
    'get_systems',
    'get_customers',
    'get_types',
    'get_stats',
    'get_systems_checks',
    'selected_customers',
    'selected_types',
    'selected_systems',
    'get_customer_systems',
    'check_customer_system',
    'check_customer_systems'
]


CUSTOMER_INTERVAL = timedelta(hours=48)
CUSTOMER_MAX_OFFLINE = 0.2


def get_systems(*, systems=None, customers=None, types=None):
    """Yields the systems which the current user may monitor."""

    condition = True

    if systems:
        condition &= System.id << systems

    if customers:
        condition &= Deployment.customer << customers

    if types:
        condition &= Deployment.type << types

    if ACCOUNT.root:
        return System.select().where(condition)

    try:
        type_admins = TypeAdmin.select().where(
            TypeAdmin.customer == CUSTOMER.id)
    except TypeAdmin.DoesNotExist:
        return ()

    authorized_types = set(type_admin.type for type_admin in type_admins)
    condition &= Deployment.type << authorized_types
    return System.select().join(Deployment).where(condition)


@coerce(set)
def get_customers():
    """Yields all allowed customers."""

    for system in get_systems():
        if system.deployment:
            yield system.deployment.customer


@coerce(set)
def get_types():
    """Yields all allowed types."""

    for system in get_systems():
        if system.deployment:
            yield system.deployment.type


def get_stats(system, *, begin=None, end=None):
    """Returns the checks for the respective system."""

    json = {}

    for model in CHECKS:
        selection = model.system == system

        if begin:
            selection &= model.timestamp >= begin

        if end:
            selection &= model.timestamp <= end

        ordering = model.timestamp.desc()
        query = model.select().where(selection).order_by(ordering)

        try:
            latest = query.limit(1).get()
        except model.DoesNotExist:
            continue

        json[model.__name__] = latest.to_json()

    return json


@coerce(list)
def get_systems_checks(systems, *, begin=None, end=None):
    """Yields JSON objects with system information and checks data."""

    for system in systems:
        json = system.to_json(brief=True, cascade=3)
        json['checks'] = get_stats(system, begin=begin, end=end)
        yield json


@coerce(set)
def selected_customers():
    """Yields the selected customers."""

    customers = request.headers.get('customers')

    if customers:
        for customer in customers.split(','):
            try:
                yield int(customer)
            except ValueError:
                raise Error('Invalid customer ID: "%s".' % customer)


@coerce(set)
def selected_types():
    """Yields the selected types."""

    types = request.headers.get('types')

    if types:
        for type_ in types.split(','):
            try:
                yield Type(type_)
            except ValueError:
                raise Error('Invalid system type: "%s".' % type_)


@coerce(set)
def selected_systems():
    """Yields the selected systems."""

    systems = request.headers.get('systems')

    if systems:
        for system in systems.split(','):
            try:
                yield int(system)
            except ValueError:
                raise Error('Invalid system ID: "%s".' % system)


def get_customer_systems():
    """Reuturns systems of the current customer."""

    return System.select().join(Deployment).where(
        Deployment.customer == CUSTOMER.id)


def check_customer_system(system):
    """Returns the customer online check for the respective system."""

    until = datetime.now()
    start = until - CUSTOMER_INTERVAL
    # Check whether the system has been checked CUSTOMER_INTERVAL ago.
    selection = OnlineCheck.system == system
    selection &= OnlineCheck.timestamp <= start

    try:
        OnlineCheck.get(selection)
    except OnlineCheck.DoesNotExist:
        return None     # System is not checked yet.

    # Select all systems within the CUSTOMER_INTERVAL.
    selection = OnlineCheck.system == system
    selection &= OnlineCheck.timestamp >= start
    selection &= OnlineCheck.timestamp <= until
    # System is deemed OK, iff any check
    # within CUSTOMER_INTERVAL was successful.
    query = OnlineCheck.select().where(selection)
    return any(check.success for check in query)


def check_customer_systems():
    """Checks all systems of the respective customer."""

    states = {}
    failures = 0
    systems = 0

    for systems, system in enumerate(get_customer_systems(), start=1):
        states[system.id] = state = check_customer_system(system)

        if state is False:  # False but not None.
            failures += 1

    if failures >= systems * CUSTOMER_MAX_OFFLINE:
        raise Error('Failure limit exceeded.')

    return states
