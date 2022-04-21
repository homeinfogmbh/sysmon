"""JSON file generation."""

from typing import Any, Iterable, Iterator

from hwdb import System

from sysmon.filtering import check_results_by_systems
from sysmon.orm import CheckResults


__all__ = ['check_results_to_json']


def check_results_to_json(
        check_results: Iterable[CheckResults]
) -> dict[int, Any]:
    """Converts a list of check results into
    a JSON object for the front-end.
    """

    return dict(serialize_by_system(check_results_by_systems(check_results)))


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

    json = system.to_json(cascade=3)
    json['checkResults'] = checks_results_json = []

    for check_result in check_results:
        checks_results_json.append(check_result.to_json())

    return json
