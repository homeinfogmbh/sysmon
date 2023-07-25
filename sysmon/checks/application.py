"""Application-related checks"""

from typing import Any, Optional

from sysmon.enumerations import ApplicationState

from sysmon.checks.common import extract_package_version


__all__ = [
    "current_application_version",
    "get_application_state",
    "get_application_version",
]


APPLICATION_AIR_REGEX = r"application-air-(.+)-any\.pkg\.tar\.zst"
APPLICATION_HTML_REGEX = r"application-html-(.+)-any\.pkg\.tar\.zst"


def current_application_version(typ: str) -> Optional[str]:
    """Returns the current application version in the repo."""

    if typ == "html":
        return extract_package_version(APPLICATION_HTML_REGEX)

    if typ == "air":
        return extract_package_version(APPLICATION_AIR_REGEX)

    return None


def get_application_state(sysinfo: dict[str, Any]) -> ApplicationState:
    """Checks whether the application is running."""

    if name := sysinfo.get("application", {}).get("name"):
        try:
            return ApplicationState(name)
        except ValueError:
            return ApplicationState.UNKNOWN

    return ApplicationState.UNKNOWN


def get_application_version(sysinfo: dict[str, Any]) -> Optional[str]:
    """Returns the application version string."""

    return sysinfo.get("application", {}).get("version")
