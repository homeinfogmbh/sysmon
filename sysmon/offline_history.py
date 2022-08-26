"""Offline history related functions."""

from datetime import date
from typing import Any

from peewee import ModelSelect

from his import Account
from hwdb import Group
from termacls import get_administerable_groups

from sysmon.functions import get_latest_check_results_per_group
from sysmon.orm import OfflineHistory


__all__ = ['update_offline_systems', 'get_offline_systems']


def count_offline_systems_in_group(
        group: int,
        timestamp: date,
        *,
        blacklist: set[int] = frozenset()
) -> int:
    """Counts the offline systems of the given group on the given day."""

    return sum(
        not check_results.online for check_results in
        get_latest_check_results_per_group(group, timestamp)
        if (
                (system := check_results.system).id not in blacklist
                and system.fitted
                and not system.testing
        )
    )


def update_offline_systems(
        timestamp: date,
        *,
        blacklist: set[int] = frozenset()
) -> None:
    """Updates the offline systems for the given date."""

    for group in Group.select().where(True):
        offline_systems = OfflineHistory.create_or_update(group.id, timestamp)
        offline_systems.offline = count_offline_systems_in_group(
            group.id, timestamp, blacklist=blacklist
        )
        offline_systems.save()


def get_offline_systems_by_group(group: int, since: date) -> ModelSelect:
    """Select offline history entries for the respective group."""

    return OfflineHistory.select().where(
        (OfflineHistory.group == group)
        & (OfflineHistory.timestamp >= since)
    ).order_by(
        OfflineHistory.timestamp
    )


def get_offline_systems(account: Account, since: date) -> dict[str, Any]:
    """Return offline system counts for the given account."""

    return {
        str(group): [
            history_item.to_json() for history_item in
            get_offline_systems_by_group(group.id, since)
        ] for group in get_administerable_groups(account)
    }
