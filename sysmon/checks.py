"""System checks."""

from multiprocessing import Pool
from typing import Iterable

from hwdb import System

from sysmon.config import LOGGER
from sysmon.orm import CHECKS


__all__ = ['check_systems']


def check_system(system: System):
    """Cheks tehe given system."""

    for check in CHECKS:
        LOGGER.info('Running %s on #%i.', check.__name__, system.id)
        check.run(system)


def check_systems(systems: Iterable[System]):
    """Checks the given systems."""

    with Pool() as pool:
        pool.map(check_system, set(systems))
