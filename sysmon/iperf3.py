"""Iperf3 speed measuring."""

from __future__ import annotations
from ipaddress import IPv4Address, IPv6Address
from json import loads
from subprocess import DEVNULL, PIPE, run
from typing import NamedTuple, Optional, Union


__all__ = ['iperf3']


class Iperf3Result(NamedTuple):
    """Iperf3 measurement results in bits/sec."""

    sender: float
    receiver: float


def iperf3(
        host: Union[IPv4Address, IPv6Address, str],
        *,
        reverse: bool = False,
        timeout: Optional[int] = None
) -> Iperf3Result:
    """Return the transmission speed."""

    command = ['/usr/bin/iperf3', '-c', str(host), '-J']

    if reverse:
        command.append('-R')

    return parse_result(
        loads(
            run(
                command, check=True, stdout=PIPE, stderr=DEVNULL, text=True,
                timeout=timeout
            ).stdout
        )['end']['streams'][0]
    )


def parse_result(
        stream: dict[str, dict[str, Union[int, float, bool]]]
) -> Iperf3Result:
    """Parse the iperf3 result."""

    return Iperf3Result(
        stream['sender']['bits_per_second'],
        stream['receiver']['bits_per_second']
    )
