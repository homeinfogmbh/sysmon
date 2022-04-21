"""Monitoring daemon."""

from logging import INFO, basicConfig

from peewee import JOIN

from hwdb import Deployment, System

from sysmon.checks import check_systems
from sysmon.config import LOG_FORMAT


__all__ = ['spawn']


def spawn() -> None:
    """Runs the daemon."""

    basicConfig(level=INFO, format=LOG_FORMAT)
    check_systems(
        System.select(System, Deployment).join(
            Deployment, on=System.deployment == Deployment.id,
            join_type=JOIN.LEFT_OUTER
        )
    )
