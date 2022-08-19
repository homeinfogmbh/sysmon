"""Iperf3 speed measuring."""

from __future__ import annotations
from enum import Enum
from ipaddress import IPv4Address, IPv6Address
from json import loads
from subprocess import DEVNULL, PIPE, run
from typing import Any, NamedTuple, Optional, Union


__all__ = ['SpeedUnit', 'Speed', 'iperf3']


class SpeedUnit(str, Enum):
    """Available speed units."""

    BPS = 'bits/sec'
    KBPS = 'Kbits/sec'
    MBPS = 'Mbits/sec'

    def factor_to(self: SpeedUnit, dst: SpeedUnit) -> float:
        """Return the respective conversion factor."""
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
    """Return the transmission speed."""

    command = ['/usr/bin/iperf3', '-c', str(host), '-J']

    if reverse:
        command.append('-R')

    return parse_result(loads(run(
        command, check=True, stdout=PIPE, stderr=DEVNULL, text=True,
        timeout=timeout
    ).stdout))


def parse_result(result: dict[str, Any]) -> Iperf3Result:
    """Parse the iperf3 result."""

    return Iperf3Result(
        Speed(
            (stream := result['streams'][0])['sender']['bits_per_second'],
            SpeedUnit.BPS
        ),
        Speed(stream['receiver']['bits_per_second'], SpeedUnit.BPS)
    )
