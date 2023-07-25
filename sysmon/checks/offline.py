"""Offline state checks."""

from datetime import datetime
from typing import Optional

from sysmon.orm import CheckResults


__all__ = ["get_offline_since"]


def get_offline_since(
    current: CheckResults, last: Optional[CheckResults]
) -> Optional[datetime]:
    """Returns the datetime since when the check is considered offline."""

    if current.online:
        return None

    if last is None or last.offline_since is None:
        return datetime.now()

    return last.offline_since
