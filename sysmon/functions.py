"""Common functions."""

from datetime import datetime, timedelta
from typing import Iterable, Iterator, Optional, Union

from flask import request
from peewee import ModelSelect

from functoolsplus import coerce
from his import ACCOUNT, CUSTOMER
from hwdb import Deployment, DeploymentType, System
from mdb import Address, Company, Customer
from termacls import get_system_admin_condition
from wsgilib import Error

from sysmon.exceptions import NotChecked
from sysmon.orm import CHECKS, OnlineCheck


__all__ = [
    'get_systems',
    'get_system',
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


def get_systems() -> ModelSelect:
    """Yields systems that are deployed."""

    condition = get_system_admin_condition(ACCOUNT)

    if 'all' not in request.args:
        condition &= System.monitoring_cond()

    select = System.select(System, Deployment, Address, Customer, Company)
    select = select.join_from(
        System, Deployment, on=System.deployment == Deployment.id)
    select = select.join_from(
        Deployment, Address, on=Deployment.address == Address.id)
    select = select.join_from(
        Deployment, Customer, on=Deployment.customer == Customer.id)
    select = select.join_from(
        Customer, Company, on=Customer.company == Company.id)
    return select.where(condition)


def get_system(system: Union[System, int]) -> System:
    """Returns a system by its ID."""

    if ACCOUNT.root:
        return System[system]

    systems = get_systems()
    return systems.select().where(System.id == system).get()


@coerce(set)
def get_customers() -> Iterator[Customer]:
    """Yields all allowed customers."""

    for system in get_systems():
        if system.deployment:
            yield system.deployment.customer


@coerce(set)
def get_types() -> Iterator[DeploymentType]:
    """Yields all allowed types."""

    for system in get_systems():
        if system.deployment:
            yield system.deployment.type


def get_stats(system: Union[System, int], *,
              begin: Optional[datetime] = None,
              end: Optional[datetime] = None) -> dict:
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
def get_systems_checks(systems: Iterable[System], *,
                       begin: Optional[datetime] = None,
                       end: Optional[datetime] = None) -> Iterator[dict]:
    """Yields JSON objects with system information and checks data."""

    for system in systems:
        json = system.to_json(brief=True, cascade=3)
        json['checks'] = get_stats(system, begin=begin, end=end)
        yield json


def get_customer_systems() -> ModelSelect:
    """Reuturns monitored systems of the current customer."""

    return System.monitored().where(Deployment.customer == CUSTOMER.id)


def check_customer_system(system: Union[System, int]) -> bool:
    """Returns the customer online check for the respective system."""

    end = datetime.now()
    start = end - CUSTOMER_INTERVAL
    condition = OnlineCheck.system == system
    condition &= OnlineCheck.timestamp >= start
    condition &= OnlineCheck.timestamp <= end
    query = OnlineCheck.select().where(condition)

    if query:
        return any(online_check.online for online_check in query)

    raise NotChecked(system, OnlineCheck)


def check_customer_systems() -> dict:
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
            failures += not state

    if failures >= systems * CUSTOMER_MAX_OFFLINE:
        raise Error('Failure limit exceeded.')

    return states
