"""Common types."""

from typing import NamedTuple, Union


__all__ = ['ApplicationState']


class ApplicationState(NamedTuple):
    """State of the application."""

    enabled: Union[bool, None]
    running: Union[bool, None]
