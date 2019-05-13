"""Checking functions."""

from subprocess import CalledProcessError
from typing import NamedTuple

from terminallib import SystemOffline, RemoteController

from sysmon.config import CONFIG


__all__ = ['check_application']


def check_application(system):
    """Determines whether the digital signage application
    is eabled and running on the respective system.
    """

    ctrl = RemoteController(CONFIG['checks']['user'], system)
    application_service = CONFIG['checks']['application_service']

    try:
        enabled = ctrl.execute('systemctl', 'is-enabled', application_service)
    except SystemOffline:
        return ApplicationState(None, None)
    except CalledProcessError:
        enabled = False

    try:
        running = ctrl.execute('systemctl', 'status', application_service)
    except SystemOffline:
        return ApplicationState(enabled, None)
    except CalledProcessError:
        running = False

    return ApplicationState(enabled, running)


class ApplicationState(NamedTuple):
    """State of the application on a system."""

    enabled: bool
    running: bool
