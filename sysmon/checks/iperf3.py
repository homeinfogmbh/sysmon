"""iperf speed measurement."""

from subprocess import CalledProcessError, TimeoutExpired
from typing import Optional

from hwdb import System

from sysmon.iperf3 import iperf3


__all__ = ["measure_speed"]


IPERF_TIMEOUT = 15  # seconds


def measure_speed(
    system: System, *, reverse: bool = False, timeout: Optional[int] = IPERF_TIMEOUT
) -> Optional[int]:
    """Measure the up- or download speed of the system in kbps."""

    try:
        result = iperf3(system.ip_address, reverse=reverse, timeout=timeout)
    except (CalledProcessError, TimeoutExpired):
        return None

    return round(result["end"]["streams"][0]["receiver"]["bits_per_second"] / 1024)
