"""JSON file generation."""

from collections import defaultdict
from contextlib import suppress
from typing import Any, Iterable, Iterator

from hwdb import Deployment, System

from sysmon.filters import application_not_running
from sysmon.filters import more_than_three_months_offline
from sysmon.filters import not_deployed
from sysmon.filters import os_out_of_date
from sysmon.filters import smart_check_failed
from sysmon.filters import testing
from sysmon.functions import count
from sysmon.orm import CheckResults


__all__ = ['to_dict']


def to_dict(check_results: Iterable[CheckResults]) -> dict[str, Any]:
    """Creates the response dict."""

    return {
        'log': dict(serialize_by_system(
            system_checks := check_results_by_systems(check_results)
        )),
        'stats': {
            'smartFailures': count(filter(
                smart_check_failed,
                (last := last_check_of_each_system(system_checks))
            )),
            'notDeployed': count(filter(not_deployed, system_checks)),
            'testing': count(filter(
                testing, unique_deployments(system_checks)
            )),
            'applicationNotRunning': count(filter(
                application_not_running, last
            )),
            'osOutOfDate': count(filter(os_out_of_date, last)),
            'moreThanThreeMonthsOffline': count(filter(
                more_than_three_months_offline, last
            ))
        }
    }


def serialize_by_system(
        system_checks: dict[System, list[CheckResults]]
) -> Iterator[tuple[int, dict[str, Any]]]:
    """Serialize check results grouped by system."""

    for system, check_results in system_checks.items():
        yield system.id, serialize_system_and_checks(system, check_results)


def serialize_system_and_checks(
        system: System,
        check_results: Iterable[CheckResults]
) -> dict[str, Any]:
    """Serialize a systems and its check results."""

    json = system.to_json()
    json['checkResults'] = checks_results_json = []

    for check_result in check_results:
        checks_results_json.append(check_result.to_json())

    return json


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
