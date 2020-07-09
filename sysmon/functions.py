"""Common functions."""

from datetime import datetime, timedelta

from flask import request

from functoolsplus import coerce
from his import ACCOUNT, CUSTOMER
from hwdb import Deployment, System
from termacls import get_administerable_systems
from wsgilib import Error

from sysmon.exceptions import NotChecked
from sysmon.orm import CHECKS, OnlineCheck


__all__ = [
    'get_system',
    'get_systems',
    'get_customers',
    'get_types',
    'get_stats',
    'get_systems_checks',
    'get_customer_systems',
    'check_customer_system',
    'check_customer_systems'
]


CUSTOMER_INTERVAL = timedelta(hours=48)
CUSTOMER_MAX_OFFLINE = 0.2


def get_system(system):
    """Returns a system by its ID."""

    if ACCOUNT.root:
        return System[system]

    systems = get_systems()
    return systems.select().where(System.id == system).get()


def get_systems():
    """Yields systems that are deployed."""

    if 'all' in request.args:
        condition = True
    else:
        condition = System.monitor == 1
        condition |= ~ (System.deployment >> None)

    return get_administerable_systems(ACCOUNT).where(condition)


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
        raise NotChecked(system, OnlineCheck)

    # Select all systems within the CUSTOMER_INTERVAL.
    selection = OnlineCheck.system == system
    selection &= OnlineCheck.timestamp >= start
    selection &= OnlineCheck.timestamp <= until
    # System is deemed OK, iff any check
    # within CUSTOMER_INTERVAL was successful.
    query = OnlineCheck.select().where(selection)
    return any(online_check.online for online_check in query)


def check_customer_systems():
    """Checks all systems of the respective customer."""

    states = {}
    failures = 0
    systems = 0

    for systems, system in enumerate(get_customer_systems(), start=1):
        try:
            states[system.id] = state = check_customer_system(system)
        except NotChecked:
            states[system.id] = None
        else:
            if not state:
                failures += 1

    if failures >= systems * CUSTOMER_MAX_OFFLINE:
        raise Error('Failure limit exceeded.')

    return states
