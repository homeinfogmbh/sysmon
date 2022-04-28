"""Common functions."""

from datetime import datetime
from typing import Any, Iterable, Iterator, Optional, Union

from peewee import ModelSelect, fn

from his import Account
from hwdb import Deployment, System
from mdb import Customer
from termacls import get_system_admin_condition

from sysmon.filtering import check_results_by_systems
from sysmon.filtering import last_check_of_each_system
from sysmon.orm import CheckResults


__all__ = [
    'count',
    'get_system',
    'get_systems',
    'get_check_results',
    'get_customer_check_results',
    'get_latest_check_results_per_system'
]


def count(items: Iterable[Any]) -> int:
    """Counts the items."""

    return sum(1 for _ in items)


def get_customer_system_checks(customer: Union[Customer, int]) -> dict:
    """Selects all system checks of systems of the respective customer."""

    return CheckResults.select().join(System).join(Deployment).where(
        (Deployment.customer == customer)
        & (Deployment.testing == 0)
    )


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


def get_customer_check_results(
        customer: Union[Customer, int]
) -> Iterator[CheckResults]:
    """Checks all systems of the respective customer."""

    return last_check_of_each_system(check_results_by_systems(
        get_customer_system_checks(customer)
    ))


def get_latest_check_results_per_system(account: Account) -> ModelSelect:
    """Yields the latest check results for each system."""

    return (
        CheckResults.select(
            CheckResults, System
        ).join(System).switch(CheckResults).join(
            subquery := (
                (CheckResultsAlias := CheckResults.alias()).select(
                    CheckResultsAlias.system,
                    fn.MAX(CheckResultsAlias.timestamp).alias(
                        'latest_timestamp'
                    )
                ).group_by(CheckResultsAlias.system)
            ), on=(
                (CheckResults.timestamp == subquery.c.latest_timestamp) &
                (CheckResults.system == subquery.c.system)
            )
        ).where(
            get_system_admin_condition(account)
        )
    )
