"""Monitoring daemon."""

from datetime import date
from logging import INFO, basicConfig

from hwdb import System

from sysmon.blacklist import load_blacklist
from sysmon.checks import check_systems
from sysmon.config import LOG_FORMAT
from sysmon.offline_history import update_offline_systems


__all__ = ["spawn"]


def spawn() -> None:
    """Runs the daemon."""

    basicConfig(level=INFO, format=LOG_FORMAT)
    check_systems(
        System.select(cascade=True).where(
            (System.deployment is None) & (System.isvirtual == 0)
        )
    )
    update_offline_systems(date.today(), blacklist=load_blacklist())
