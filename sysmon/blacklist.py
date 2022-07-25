"""Blacklist generation and loading."""

from collections import defaultdict
from datetime import datetime, timedelta
from json import dump, load
from pathlib import Path
from typing import Iterator, Sequence

from peewee import ModelSelect

from his import Account

from sysmon.functions import get_authenticated_systems
from sysmon.orm import CheckResults


__all__ = ['generate_blacklist', 'load_blacklist', 'get_blacklist']


BLACKLIST = Path('/tmp/sysmon-blacklist.json')
RETENTION = timedelta(days=90)
THRESHOLD = 0.8


def generate_blacklist() -> int:
    """Genrates the blacklist."""

    with BLACKLIST.open('w', encoding='utf-8') as file:
        dump(list(get_blacklist(datetime.now() - RETENTION)), file)

    return 0


def load_blacklist(account: Account) -> ModelSelect:
    """Loads the systems from the blacklist."""

    with BLACKLIST.open('r', encoding='utf-8') as file:
        systems = load(file)

    return get_authenticated_systems(systems, account=account)


def get_blacklist(
        since: datetime,
        *,
        threshold: float = THRESHOLD
) -> Iterator[int]:
    """Determine whether the given system is blacklisted."""

    for system, check_results in get_check_results_by_system(since).items():
        if is_blacklisted(check_results, threshold=threshold):
            yield system


def get_check_results_by_system(
        since: datetime
) -> dict[int, list[CheckResults]]:
    """Return a dict of systems and their check results."""

    system_check_results = defaultdict(list)

    for check_result in CheckResults.select().where(
            CheckResults.timestamp > since
    ):
        system_check_results[check_result.system].append(check_result)

    return system_check_results


def is_blacklisted(
        check_results: Sequence[CheckResults],
        *,
        threshold: float = THRESHOLD
) -> bool:
    """Determine whether the given system is blacklisted."""

    return all(
        percentage > threshold for percentage in (
            offline_percent(check_results),
            low_bandwidth_percent(check_results)
        )
    )


def offline_percent(check_results: Sequence[CheckResults]) -> float:
    """Return the percentage of checks that yielded offline."""

    return len(list(filter(
        lambda check_result: not check_result.online, check_results
    ))) / len(check_results)


def low_bandwidth_percent(check_results: Sequence[CheckResults]) -> float:
    """Return the percentage of checks that yielded a low bandwidth."""

    return len(list(filter(
        lambda check_result: check_result.low_bandwidth(), check_results
    ))) / len(check_results)
