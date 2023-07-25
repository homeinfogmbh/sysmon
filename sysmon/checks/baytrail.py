"""Baytrail architecture-related checks."""

from typing import Any

from sysmon.enumerations import BaytrailFreezeState


__all__ = ["get_baytrail_freeze_state"]


def get_baytrail_freeze_state(sysinfo: dict[str, Any]) -> BaytrailFreezeState:
    """Returns the baytrail freeze bug state."""

    if (baytrail := sysinfo.get("baytrail")) is None:
        return BaytrailFreezeState.UNKNOWN

    if not baytrail:
        return BaytrailFreezeState.NOT_AFFECTED

    if not (cmdline := sysinfo.get("cmdline")):
        return BaytrailFreezeState.UNKNOWN

    if cmdline.get("intel_idle.max_cstate") == "1":
        return BaytrailFreezeState.MITIGATED

    return BaytrailFreezeState.VULNERABLE
