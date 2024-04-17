"""Common functions."""

from pathlib import Path
from re import fullmatch
from typing import Any

from requests import ConnectionError, ReadTimeout, Timeout

from hwdb import System

from sysmon.enumerations import SuccessFailedUnsupported
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
    system: System, *, timeout: int = 15
) -> tuple[SuccessFailedUnsupported, dict[str, Any]]:
    """Returns the system info dict per HTTP request."""

    try:
        response = system.sysinfo(timeout=timeout)
    except (ConnectionError, ReadTimeout, Timeout):
        return SuccessFailedUnsupported.UNSUPPORTED, {}

    if response.status_code != 200:
        return SuccessFailedUnsupported.FAILED, {}
    temp_return = response.json()
    if system.ddb_os:
        temp_return["application"]["name"] = system.application().json()
        temp_return["application"]["mode"] = system.application().json()
        temp_return["application"]["unit"] = system.application().json()
        temp_return["application"]["package"] = system.application().json()
        temp_return["application"]["version"] = system.application().json()

    return SuccessFailedUnsupported.SUCCESS, temp_return
