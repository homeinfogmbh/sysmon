"""Black screen related checks."""

from datetime import datetime
from typing import Optional

from sysmon.enumerations import ApplicationState
from sysmon.orm import CheckResults


__all__ = ["get_blackscreen_since"]


def get_blackscreen_since(
    current: CheckResults, last: Optional[CheckResults]
) -> Optional[datetime]:
    """Returns the datetime since when the application is not running."""

    if current.application_state is not ApplicationState.OFF:
        return None

    if last is None or last.blackscreen_since is None:
        return datetime.now()

    return last.blackscreen_since
