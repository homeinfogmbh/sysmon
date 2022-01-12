"""Common types."""

from typing import NamedTuple, Optional


__all__ = ['ApplicationState']


class ApplicationState(NamedTuple):
    """State of the application."""

    enabled: Optional[bool]
    running: Optional[bool]
