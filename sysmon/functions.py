"""Common functions."""

from datetime import datetime, timedelta
from typing import Optional, Union

from peewee import ModelSelect

from his import Account
from hwdb import System
from termacls import get_system_admin_condition

from sysmon.orm import CheckResults


__all__ = [
    'get_systems',
    'get_system',
    'get_check_results',
    'get_check_results_of_system'
]


CUSTOMER_INTERVAL = timedelta(hours=48)
CUSTOMER_MAX_OFFLINE = 0.2


def get_systems(account: Account, *, all: bool = False) -> ModelSelect:
    """Yields systems that are subject to
    checking that the given account may view.
    """

    condition = get_system_admin_condition(account)

    if not all:
        condition &= System.monitoring_cond()

    return System.select(cascade=True).where(condition)


def get_system(system: Union[System, int], account: Account) -> System:
    """Returns a system by its ID."""

    return get_systems(account).where(System.id == system).get()


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
        System.id == system
    )
