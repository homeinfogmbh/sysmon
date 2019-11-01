"""Checking functions."""

from typing import NamedTuple

from simplejson.errors import JSONDecodeError

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

    try:
        json = response.json()
    except JSONDecodeError:
        return ApplicationState(None, None)

    return ApplicationState.from_json(json)


class ApplicationState(NamedTuple):
    """State of the application on a system."""

    enabled: bool
    running: bool

    @classmethod
    def from_json(cls, json):
        """Returns an application state from a JSON-ish dict."""
        return cls(json.get('enabled'), json.get('running'))
