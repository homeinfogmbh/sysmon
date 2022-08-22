"""Iperf3 speed measuring."""

from __future__ import annotations
from ipaddress import IPv4Address, IPv6Address
from json import loads
from subprocess import DEVNULL, PIPE, run
from typing import Any, Optional, Union


__all__ = ['iperf3']


def iperf3(
        host: Union[IPv4Address, IPv6Address, str],
        *,
        reverse: bool = False,
        timeout: Optional[int] = None
) -> dict[str, Any]:
    """Return the transmission speed."""

    command = ['/usr/bin/iperf3', '-c', str(host), '-J']

    if reverse:
        command.append('-R')

    return loads(
        run(
            command, check=True, stdout=PIPE, stderr=DEVNULL, text=True,
            timeout=timeout
        ).stdout
    )
