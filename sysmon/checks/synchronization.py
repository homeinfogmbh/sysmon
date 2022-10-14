"""Digital signage data synchronization related checks."""

from datetime import datetime, timedelta

from hwdb import System


__all__ = ['is_in_sync']


SYNC_INTERVAL = timedelta(days=1)


def is_in_sync(
        system: System,
        timestamp: datetime,
        *,
        threshold: timedelta = SYNC_INTERVAL
) -> bool:
    """Determine whether the system is synchronized."""

    if system.last_sync is None:
        return False

    return system.last_sync > timestamp - threshold
