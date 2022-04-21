"""Common functions."""

from datetime import datetime, timedelta
from typing import Any, Iterable, Optional, Union

from peewee import ModelSelect

from his import Account
from hwdb import Deployment, System
from mdb import Customer
from termacls import get_system_admin_condition

from sysmon.exceptions import FailureLimitExceeded, NotChecked
from sysmon.orm import CheckResults


__all__ = [
    'check_customer_systems',
    'count',
    'get_system',
    'get_systems',
    'get_check_results',
    'get_check_results_of_system'
]


CUSTOMER_INTERVAL = timedelta(hours=48)
CUSTOMER_MAX_OFFLINE = 0.2


def check_customer_systems(customer: Union[Customer, int]) -> dict:
    """Checks all systems of the respective customer."""

    states = {}
    failures = 0
    systems = 0

    for systems, system in enumerate(get_customer_systems(customer), start=1):
        try:
            states[system.id] = state = check_customer_system(system)
        except NotChecked:
            states[system.id] = None
        else:
            failures += not state

    if failures >= systems * CUSTOMER_MAX_OFFLINE:
        raise FailureLimitExceeded()

    return states


def count(items: Iterable[Any]) -> int:
    """Counts the items."""

    return sum(1 for _ in items)


def get_system(system: Union[System, int], account: Account) -> System:
    """Returns a system by its ID."""

    return get_systems(account).where(System.id == system).get()


def get_systems(account: Account) -> ModelSelect:
    """Yields systems that are subject to
    checking that the given account may view.
    """

    return System.select(cascade=True).where(
        get_system_admin_condition(account)
    )


def get_check_results(
        account: Account,
        *,
        begin: Optional[datetime] = None,
        end: Optional[datetime] = None
) -> ModelSelect:
    """Selects checks results for the given account."""

    condition = get_system_admin_condition(account)

    if begin:
        condition &= CheckResults.timestamp >= begin

    if end:
        condition &= CheckResults.timestamp <= end

    return CheckResults.select(cascade=True).where(condition).order_by(
        CheckResults.timestamp.desc()
    )


def get_check_results_of_system(
        system: Union[System, int],
        account: Account,
        *,
        begin: Optional[datetime] = None,
        end: Optional[datetime] = None
) -> ModelSelect:
    """Selects checks for the respective system and account."""

    return get_check_results(account, begin=begin, end=end).where(
        CheckResults.system == system
    )


def get_customer_systems(customer: Union[Customer, int]) -> ModelSelect:
    """Returns monitored systems of the current customer."""

    return System.monitored().where(Deployment.customer == customer)


def check_customer_system(system: Union[System, int]) -> bool:
    """Returns the customer online check for the respective system."""

    start = (end := datetime.now()) - CUSTOMER_INTERVAL
    query = CheckResults.select().where(
        (CheckResults.system == system)
        & (CheckResults.timestamp >= start)
        & (CheckResults.timestamp <= end)
    )

    if query:
        return any(online_check.success for online_check in query)

    raise NotChecked(system)
