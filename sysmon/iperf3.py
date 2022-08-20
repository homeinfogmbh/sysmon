"""Iperf3 speed measuring."""

from __future__ import annotations
from ipaddress import IPv4Address, IPv6Address
from json import loads
from subprocess import DEVNULL, PIPE, run
from typing import Any, Optional, Union


__all__ = ['iperf3', 'receiver_kbps']


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


def receiver_kbps(result: dict[str, Any]) -> int:
    """Return the receiver speed in kilobits per second."""

    return round(
        result['end']['streams'][0]['receiver']['bits_per_second'] / 1024
    )
