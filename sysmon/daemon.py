"""Monitoring daemon."""

from logging import INFO, basicConfig

from terminallib import System

from sysmon.config import LOG_FORMAT, LOGGER
from sysmon.notify import notify
from sysmon.orm import CHECKS


__all__ = ['spawn']


def run_checks():
    """Monitors deployed systems."""

    for system in System.monitored():
        for check in CHECKS:
            LOGGER.info('Running %s on #%i.', check.__name__, system.id)
            check.run(system)

    notify()


def spawn():
    """Runs the daemon."""

    basicConfig(level=INFO, format=LOG_FORMAT)

    while True:
        try:
            run_checks()
        except KeyboardInterrupt:
            return
