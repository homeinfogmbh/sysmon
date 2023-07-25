"""Common functions."""

from pathlib import Path
from re import fullmatch
from typing import Any

from requests import ConnectionError, ReadTimeout, get

from hwdb import System

from sysmon.enumerations import SuccessFailedUnsupported
from sysmon.functions import get_url
from sysmon.orm import CheckResults


__all__ = ["extract_package_version", "get_last_check", "get_sysinfo"]


REPO_DIR = Path("/srv/http/de/homeinfo/mirror/prop/pacman")


def extract_package_version(regex: str, *, repo: Path = REPO_DIR) -> str:
    """Extracts the package version."""

    for file in repo.iterdir():
        if match := fullmatch(regex, file.name):
            return match.group(1)

    raise ValueError("Could not determine any package version.")


def get_last_check(system: System) -> CheckResults:
    """Returns the last check of the given system."""

    return (
        CheckResults.select()
        .where(CheckResults.system == system)
        .order_by(CheckResults.timestamp.desc())
        .get()
    )


def get_sysinfo(
    system: System, *, port: int = 8000, timeout: int = 15
) -> tuple[SuccessFailedUnsupported, dict[str, Any]]:
    """Returns the system info dict per HTTP request."""

    try:
        response = get(get_url(system.ip_address, port=port), timeout=timeout)
    except (ConnectionError, ReadTimeout):
        return SuccessFailedUnsupported.UNSUPPORTED, {}

    if response.status_code != 200:
        return SuccessFailedUnsupported.FAILED, {}

    return SuccessFailedUnsupported.SUCCESS, response.json()
