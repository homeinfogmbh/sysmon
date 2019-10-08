"""Checking functions."""

from typing import NamedTuple

from terminallib import SystemOffline


__all__ = ['check_application']


def check_application(system):
    """Determines whether the digital signage application
    is eabled and running on the respective system.
    """

    try:
        response = system.exec('application')
    except SystemOffline:
        return ApplicationState(None, None)

    json = response.json()

    if json:
        return ApplicationState(json.get('enabled'), json.get('running'))

    return ApplicationState(None, None)


class ApplicationState(NamedTuple):
    """State of the application on a system."""

    enabled: bool
    running: bool
