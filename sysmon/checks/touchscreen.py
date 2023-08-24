"""Touchscreen related checks."""

from datetime import datetime, timedelta
from typing import Optional, Union

from digsigdb import Statistics
from hwdb import Deployment


__all__ = ["count_recent_touch_events"]


RECENT_TOUCH_EVENTS = timedelta(days=21)


def count_recent_touch_events(
    deployment: Optional[Union[Deployment, int]],
    start: datetime,
    *,
    span: timedelta = RECENT_TOUCH_EVENTS,
) -> Optional[int]:
    """Count recent touch events."""

    if deployment is None:
        return None

    return (
        Statistics.select()
        .where(
            (Statistics.deployment == deployment)
            & (Statistics.timestamp >= start - span)
            & (Statistics.timestamp <= start)
        )
        .count()
    )
