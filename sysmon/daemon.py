"""Monitoring daemon."""

from logging import INFO, basicConfig

from hwdb import System

from sysmon.checks import check_systems
from sysmon.config import LOG_FORMAT


__all__ = ['spawn']


def spawn() -> None:
    """Runs the daemon."""

    basicConfig(level=INFO, format=LOG_FORMAT)
    check_systems(System.monitored())
