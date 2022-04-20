"""System check filter functions."""

from datetime import datetime, timedelta

from hwdb import Deployment, System

from sysmon.enumerations import ApplicationState, SuccessFailedUnsupported
from sysmon.orm import CheckResults


__all__ = [
    'application_not_running',
    'more_than_three_months_offline',
    'not_deployed',
    'os_out_of_date',
    'smart_check_failed',
    'testing'
]


def application_not_running(check_result: CheckResults) -> bool:
    """Checks whether the application is not running."""

    return check_result.application_state == ApplicationState.NOT_RUNNING


def more_than_three_months_offline(check_results: CheckResults) -> bool:
    """Yields systems that are offline more than three months."""

    return check_results.offline_since < datetime.now() + timedelta(days=3*30)


def not_deployed(system: System) -> bool:
    """Checks whether a system is not deployed."""

    return system.deployment is None


def os_out_of_date(check_resuts: CheckResults) -> bool:
    """Checks whether the operating system is out of date."""

    return False    # TODO: implement


def smart_check_failed(check_results: CheckResults) -> bool:
    """Checks whether the smart check failed."""

    return check_results.smart_check == SuccessFailedUnsupported.FAILED


def testing(deployment: Deployment) -> bool:
    """Checks whether the system is a testing system."""

    return deployment.testing
