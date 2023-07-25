"""Configuration file parsing."""

from datetime import timedelta
from functools import cache, partial
from logging import getLogger

from configlib import load_config


__all__ = [
    "LOGGER",
    "LOG_FORMAT",
    "MAX_RETENTION",
    "MIN_DOWNLOAD",
    "MIN_UPLOAD",
    "get_config",
]


LOGGER = getLogger("sysmon")
LOG_FORMAT = "[%(levelname)s] %(name)s: %(message)s"
MAX_RETENTION = timedelta(days=90)
MIN_DOWNLOAD = 1945.6  # Kilobits/s
MIN_UPLOAD = 358.4  # Kilobits/s
get_config = partial(cache(load_config), "sysmon.conf")
