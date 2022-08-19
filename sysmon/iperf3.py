"""Iperf3 speed measuring."""

from __future__ import annotations
from enum import Enum
from ipaddress import IPv4Address, IPv6Address
from re import Match, fullmatch
from subprocess import DEVNULL, PIPE, run
from typing import NamedTuple, Optional, Union


__all__ = ['SpeedUnit', 'Speed', 'iperf3']


REGEX = (
    r'\[\s*(\d+)]\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S*)'
    r'\s+(\S+)'
)


class SpeedUnit(str, Enum):
    """Available speed units."""

    BPS = 'bits/sec'
    KBPS = 'Kbits/sec'
    MBPS = 'Mbits/sec'

    def factor_to(self: SpeedUnit, dst: SpeedUnit) -> float:
        """Returns the respective conversion factor."""
        if self is dst:
            return 1

        if self is self.BPS:
            if dst is self.KBPS:
                return 1 / 1024

            if dst is self.MBPS:
                return self.factor_to(self.KBPS) ** 2

        if self is self.KBPS:
            if dst is self.BPS:
                return 1024

            if dst is self.MBPS:
                return 1 / self.factor_to(self.BPS)

        if self is self.MBPS:
            if dst is self.BPS:
                return self.factor_to(self.KBPS) ** 2

            if dst is self.KBPS:
                return 1024

        raise ValueError(f'Cannot convert from {self} to {dst}.')


class Speed(NamedTuple):
    """Transmission speed."""

    value: float
    unit: SpeedUnit

    def to_kbps(self) -> float:
        """Convert the speed to kbps."""
        return self.value * self.unit.factor_to(SpeedUnit.KBPS)


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

    return Speed(float(match.group(6)), SpeedUnit(match.group(7)))
