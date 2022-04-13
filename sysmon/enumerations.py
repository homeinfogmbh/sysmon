"""Common enumerations."""

from enum import Enum


__all__ = [
    'ApplicationState',
    'BaytrailFreezeState',
    'State',
    'SuccessFailedUnsupported'
]


class ApplicationState(str, Enum):
    """Digital signage application state."""

    AIR = 'air'
    HTML = 'html'
    CONFLICT = 'conflict'
    NOT_ENABLED = 'not enabled'
    NOT_RUNNING = 'not running'
    UNKNOWN = 'unknown'


class BaytrailFreezeState(str, Enum):
    """State for the baytrail freeze bug."""

    NOT_AFFECTED = 'not affected'
    MITIGATED = 'mitigated'
    VULNERABLE = 'vulnerable'
    UNKNOWN = 'unknown'


class State(str, Enum):
    """State change of a system check."""

    RECOVERED = 'recovered'
    FAILED = 'failed'
    UNCHANGED = 'unchanged'


class SuccessFailedUnsupported(str, Enum):
    """Trinary check result."""

    SUCCESS = 'success'
    FAILED = 'failed'
    UNSUPPORTED = 'unsupported'