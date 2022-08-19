"""Iperf3 speed measuring."""

from __future__ import annotations
from ipaddress import IPv4Address, IPv6Address
from re import Match, fullmatch
from subprocess import DEVNULL, PIPE, run
from typing import NamedTuple, Optional, Union


__all__ = ['iperf3']


REGEX = (
    r'\[\s*(\d+)]\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S*)'
    r'\s+(\S+)'
)
KBPS = 'Kbits/sec'
MBPS = 'Mbits/sec'
BPS = 'bits/sec'


class Speed(NamedTuple):
    """Transmission speed."""

    value: float
    unit: str

    def to_kbps(self) -> float:
        """Convert the speed to kbps."""
        if self.unit == KBPS:
            return self.value

        if self.unit == MBPS:
            return self.value * 1024

        if self.unit == BPS:
            return self.value / 1024

        raise ValueError('Cannot convert unit:', self.unit)


class Iperf3Result(NamedTuple):
    """Iperf3 measurement results."""

    sender: Speed
    receiver: Speed


def iperf3(
        host: Union[IPv4Address, IPv6Address, str],
        *,
        reverse: bool = False,
        timeout: Optional[int] = None
) -> Iperf3Result:
    """Returns the transmission speed."""

    command = ['/usr/bin/iperf3', '-c', str(host)]

    if reverse:
        command.append('-R')

    return parse_result(run(
        command, check=True, stdout=PIPE, stderr=DEVNULL, text=True,
        timeout=timeout
    ).stdout)


def parse_result(text: str) -> Iperf3Result:
    """Parses the iperf3 result."""

    return Iperf3Result(
        parse_speed(text, 'sender'),
        parse_speed(text, 'receiver')
    )


def parse_speed(text: str, typ: str) -> Speed:
    """Parse the sender speed."""

    for line in text.split('\n'):
        if match := fullmatch(REGEX, line.strip()):
            if match.group(9) == typ:
                return extract_speed(match)

    raise ValueError('Could not parse speed from text.')


def extract_speed(match: Match) -> Speed:
    """Extract the speed from the regex match."""

    return Speed(float(match.group(6)), match.group(7))
