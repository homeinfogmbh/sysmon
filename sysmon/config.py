"""Configuration file parsing."""

from datetime import timedelta
from functools import cache, partial
from logging import getLogger

from configlib import load_config


__all__ = [
    'LOGGER',
    'LOG_FORMAT',
    'MAX_RETENTION',
    'MIN_BANDWIDTH',
    'get_config'
]


LOGGER = getLogger('sysmon')
LOG_FORMAT = '[%(levelname)s] %(name)s: %(message)s'
MAX_RETENTION = timedelta(days=30)
MIN_BANDWIDTH = 2000    # kbps
get_config = partial(cache(load_config), 'sysmon.conf')
