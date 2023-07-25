"""meminfo-related checks."""

from typing import Any, Optional


__all__ = ["get_ram_available", "get_ram_free", "get_ram_total"]


def get_ram_total(sysinfo: dict[str, Any]) -> Optional[int]:
    """Returns the total memory in kilobytes."""

    return sysinfo.get("meminfo", {}).get("MemTotal", {}).get("value")


def get_ram_free(sysinfo: dict[str, Any]) -> Optional[int]:
    """Returns the free memory in kilobytes."""

    return sysinfo.get("meminfo", {}).get("MemFree", {}).get("value")


def get_ram_available(sysinfo: dict[str, Any]) -> Optional[int]:
    """Returns the available memory in kilobytes."""

    return sysinfo.get("meminfo", {}).get("MemAvailable", {}).get("value")
