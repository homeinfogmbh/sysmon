"""Common functions."""

from datetime import date, datetime, timedelta
from ipaddress import IPv4Address, IPv6Address
from typing import Any, Iterable, Iterator, Optional, Union

from peewee import DateTimeField, ModelSelect, fn

from his import Account
from hwdb import Deployment, System
from mdb import Customer
from termacls import get_system_admin_condition

from sysmon.filtering import check_results_by_systems
from sysmon.filtering import last_check_of_each_system
from sysmon.orm import CheckResults


__all__ = [
    'count',
    'get_socket',
    'get_url',
    'get_system',
    'get_systems',
    'get_check_results',
    'get_check_results_for_system',
    'get_customer_check_results',
    'get_latest_check_results_per_system',
    'get_authenticated_systems',
    'get_latest_check_results_per_system_span',
    'get_latest_offline_count_span'
]


def count(items: Iterable[Any]) -> int:
    """Counts the items."""

    return sum(1 for _ in items)


def get_url(
        ip_address: Union[IPv4Address, IPv6Address],
        *,
        port: Optional[int] = None,
        protocol: str = 'http'
) -> str:
    """Returns the URL to the given IP address."""

    return f'{protocol}://{get_socket(ip_address, port=port)}'


def get_socket(
        ip_address: Union[IPv4Address, IPv6Address],
        *,
        port: Optional[int] = None
) -> str:
    """Returns an IP socket as string."""

    if port is None:
        return str(ip_address)

    if isinstance(ip_address, IPv6Address):
        return f'[{ip_address}]:{port}'

    return f'{ip_address}:{port}'


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


def get_check_results_for_system(
        system: Union[System, int],
        account: Account
) -> ModelSelect:
    """Selects check results for the given system."""

    return CheckResults.select(cascade=True).where(
        (CheckResults.system == system)
        & get_system_admin_condition(account)
    ).order_by(
        CheckResults.timestamp.desc()
    )


def get_customer_check_results(
        customer: Union[Customer, int]
) -> Iterator[CheckResults]:
    """Checks all systems of the respective customer."""

    return last_check_of_each_system(check_results_by_systems(
        get_customer_system_checks(customer)
    ))


def get_latest_check_results_per_system(
        account: Account,
        date_: Optional[date] = None
) -> ModelSelect:
    """Yields the latest check results for each system."""

    return CheckResults.select(cascade=True).join_from(
        CheckResults,
        subquery := (CheckResultsAlias := CheckResults.alias()).select(
            CheckResultsAlias.system,
            fn.MAX(CheckResultsAlias.timestamp).alias('latest_timestamp')
        ).where(
            True if date_ is None else get_datetime_range_condition(
                CheckResultsAlias.timestamp, date_
            )
        ).group_by(
            CheckResultsAlias.system
        ),
        on=(
            (CheckResults.timestamp == subquery.c.latest_timestamp) &
            (CheckResults.system == subquery.c.system)
        )
    ).where(
        get_system_admin_condition(account)
    )


def get_authenticated_systems(
        systems: Iterable[Union[System, int]],
        account: Account
) -> ModelSelect:
    """Select systems with termacls authentication."""

    return System.select(cascade=True).where(
        (System.id << systems)
        & get_system_admin_condition(account)
    )


def get_datetime_range_condition(
        date_time_field: DateTimeField,
        date_: date
) -> bool:
    """Return an expression to restrict the
    date time field to the given date.
    """

    start, end = date_to_datetime_range(date_)
    return (date_time_field >= start) & (date_time_field < end)


def date_to_datetime_range(date_: date) -> tuple[datetime, datetime]:
    """Convert a date to datetime boundaries."""

    return (
        datetime(year=date_.year, month=date_.month, day=date_.day),
        datetime(
            year=(next_day := date_ + timedelta(days=1)).year,
            month=next_day.month, day=next_day.day
        )
    )


def get_latest_check_results_per_system_span(
        account: Account,
        days: int,
        start: date
) -> Iterator[tuple[date, list[CheckResults]]]:
    """Return a dict of system checks for
    each day for the given amount of days.
    """

    for offset in range(days):
        day = start - timedelta(days=offset)
        yield day, get_latest_check_results_per_system(
            account, day
        )


def get_latest_offline_count_span(
        account: Account,
        days: int,
        start: date
) -> Iterator[tuple[date, list[CheckResults]]]:
    """Return a dict of system checks for
    each day for the given amount of days.
    """

    for offset in range(days):
        day = start - timedelta(days=offset)
        yield day, {
            system.id: sum(
                not check_result.online for check_result in check_results
            )
            for system, check_results in check_results_by_systems(
                get_latest_check_results_per_system(account, day)
            )
        }
