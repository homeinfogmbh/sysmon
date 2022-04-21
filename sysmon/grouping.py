"""Functions to group check results."""

from collections import defaultdict
from contextlib import suppress
from typing import Iterable, Iterator

from hwdb import System

from sysmon.orm import CheckResults


__all__ = ['check_results_by_systems', 'last_check_of_each_system']


def check_results_by_systems(
        check_results: Iterable[CheckResults]
) -> dict[System, list[CheckResults]]:
    """Returns a dict of systems and their respective
    check results sorted by timestamp.
    """

    result = defaultdict(list)

    for check_result in check_results:
        result[check_result.system].append(check_result)

    for check_results in result.values():
        check_results.sort(key=lambda item: item.timestamp, reverse=True)

    return result


def last_check_of_each_system(
        checks_per_system: dict[System, list[CheckResults]]
) -> Iterator[CheckResults]:
    """Returns the last checks for each system."""

    for check_results in checks_per_system.values():
        with suppress(IndexError):
            yield check_results[-1]
