"""JSON file generation."""

from collections import defaultdict
from contextlib import suppress
from typing import Any, Iterable, Iterator

from hwdb import Deployment, System

from sysmon.filters import application_not_running
from sysmon.filters import more_than_three_months_offline
from sysmon.filters import not_deployed
from sysmon.filters import smart_check_failed
from sysmon.filters import testing
from sysmon.orm import CheckResults


__all__ = ['to_dict']


def to_dict(check_results: Iterable[CheckResults]) -> dict[str, Any]:
    """Creates the response dict."""

    return {
        'log': [check_result.to_json() for check_result in check_results],
        'smartFailures': count(filter(
            smart_check_failed,
            (last := last_check_of_each_system(
                system_checks := check_results_by_systems(check_results)
            ))
        )),
        'notDeployed': count(filter(not_deployed, system_checks)),
        'testing': count(filter(testing, unique_deployments(system_checks))),
        'applicationNotRunning': count(filter(application_not_running, last)),
        'oldOs': 0,     # TODO: implement
        'moreThanThreeMonthsOffline': count(filter(
            more_than_three_months_offline, last
        ))
    }


def count(items: Iterable[Any]) -> int:
    """Counts the items."""

    return sum(1 for _ in items)


def last_check_of_each_system(
        checks_per_system: dict[System, list[CheckResults]]
) -> Iterator[CheckResults]:
    """Returns the last checks for each system."""

    for check_results in checks_per_system.values():
        with suppress(IndexError):
            yield check_results[-1]


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
        check_results.sort(key=lambda item: item.timestamp)

    return result


def unique_systems(check_results: Iterable[CheckResults]) -> set[System]:
    """Extracts a set of unique systems from the check results."""

    return {check_result.system for check_result in check_results}


def unique_deployments(systems: Iterable[System]) -> set[Deployment]:
    """Extracts a set of unique deployments from the check results."""

    return {system.deployment for system in systems}
