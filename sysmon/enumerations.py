"""Common enumerations."""

from enum import Enum


__all__ = ["ApplicationState", "BaytrailFreezeState", "SuccessFailedUnsupported"]


class ApplicationState(str, Enum):
    """Digital signage application state."""

    AIR = "air"
    HTML = "html"
    INSTALLATION_INSTRUCTIONS = "installation instructions"
    NOT_CONFIGURED = "not configured"
    UNKNOWN = "unknown"
    OFF = "off"


class BaytrailFreezeState(str, Enum):
    """State for the baytrail freeze bug."""

    NOT_AFFECTED = "not affected"
    MITIGATED = "mitigated"
    VULNERABLE = "vulnerable"
    UNKNOWN = "unknown"


class SuccessFailedUnsupported(str, Enum):
    """Trinary check result."""

    SUCCESS = "success"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"
