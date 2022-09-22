"""ICMP echo request checks."""

from subprocess import CalledProcessError, TimeoutExpired
from typing import Optional

from hwdb import System


__all__ = ['check_icmp_request']


def check_icmp_request(system: System, timeout: Optional[int] = None) -> bool:
    """Pings the system."""

    try:
        system.ping(timeout=timeout)
    except (CalledProcessError, TimeoutExpired):
        return False

    return True
