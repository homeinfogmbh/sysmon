"""Monitoring daemon."""

from terminallib import System

from sysmon.config import LOGGER
from sysmon.orm import CHECKS


def run_checks():
    """Monitors deployed systems."""

    for system in System.select().where(~(System.deployment >> None)):
        for check in CHECKS:
            LOGGER.info('Running %s on #%i.', check.__name__, system.id)
            check.run(system)
