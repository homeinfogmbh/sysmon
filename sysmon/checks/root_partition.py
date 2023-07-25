"""Root partition checks."""

from typing import Any

from sysmon.enumerations import SuccessFailedUnsupported


__all__ = ["check_root_not_ro"]


def check_root_not_ro(sysinfo: dict[str, Any]) -> SuccessFailedUnsupported:
    """Check whether the / partition is not mounted read-only."""

    if (root_ro := sysinfo.get("root_ro")) is None:
        return SuccessFailedUnsupported.UNSUPPORTED

    if root_ro:
        return SuccessFailedUnsupported.FAILED

    return SuccessFailedUnsupported.SUCCESS
