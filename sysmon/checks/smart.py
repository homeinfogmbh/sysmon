"""S.M.A.R.T. related checks."""

from typing import Any

from sysmon.enumerations import SuccessFailedUnsupported


__all__ = ["get_smart_results"]


def get_smart_results(sysinfo: dict[str, Any]) -> SuccessFailedUnsupported:
    """Returns the SMART test results."""

    if not (results := sysinfo.get("smartctl")):
        return SuccessFailedUnsupported.UNSUPPORTED

    if all(result.lstrip() == "PASSED" for result in results.values()):
        return SuccessFailedUnsupported.SUCCESS

    return SuccessFailedUnsupported.FAILED
