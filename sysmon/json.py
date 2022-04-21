"""JSON file generation."""

from typing import Any, Iterable, Iterator

from hwdb import System

from sysmon.filters import application_not_running
from sysmon.filters import more_than_three_months_offline
from sysmon.filters import not_deployed
from sysmon.filters import os_out_of_date
from sysmon.filters import smart_check_failed
from sysmon.filters import testing
from sysmon.functions import count
from sysmon.grouping import check_results_by_systems
from sysmon.grouping import last_check_of_each_system
from sysmon.grouping import unique_deployments
from sysmon.orm import CheckResults


__all__ = ['check_results_to_json']


def check_results_to_json(
        check_results: Iterable[CheckResults]
) -> dict[str, Any]:
    """Converts a list of check results into
    a JSON object for the front-end.
    """

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
