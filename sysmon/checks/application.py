"""Application-related checks"""

from typing import Any, Optional

from sysmon.enumerations import ApplicationState

from sysmon.checks.common import extract_package_version


__all__ = [
    'current_application_version',
    'get_application_state',
    'get_application_version'
]


APPLICATION_AIR_REGEX = r'application-air-(.+)-any\.pkg\.tar\.zst'
APPLICATION_HTML_REGEX = r'application-html-(.+)-any\.pkg\.tar\.zst'
APPLICATION_STATES = {
    'air': ApplicationState.AIR,
    'html': ApplicationState.HTML,
    'installation instructions': ApplicationState.INSTALLATION_INSTRUCTIONS,
    'not configured': ApplicationState.NOT_CONFIGURED
}


def current_application_version(typ: str) -> Optional[str]:
    """Returns the current application version in the repo."""

    if typ == 'html':
        return extract_package_version(APPLICATION_HTML_REGEX)

    if typ == 'air':
        return extract_package_version(APPLICATION_AIR_REGEX)

    return None


def get_application_state(sysinfo: dict[str, Any]) -> ApplicationState:
    """Checks whether the application is running."""

    if (status := sysinfo.get('application', {}).get('status')) is None:
        return ApplicationState.UNKNOWN

    if not (running := status.get('running')):
        return ApplicationState.NOT_RUNNING

    if not (enabled := status.get('enabled')):
        return ApplicationState.NOT_ENABLED

    if running != enabled:
        return ApplicationState.CONFLICT

    if len(running) != 1 or len(enabled) != 1:
        return ApplicationState.CONFLICT

    return APPLICATION_STATES.get(running[0], ApplicationState.UNKNOWN)


def get_application_version(sysinfo: dict[str, Any]) -> Optional[str]:
    """Returns the application version string."""

    return sysinfo.get('application', {}).get('version')
