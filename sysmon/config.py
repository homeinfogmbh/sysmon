"""Configuration file parsing."""

from logging import getLogger

from configlib import loadcfg


__all__ = ['CONFIG', 'LOGGER', 'LOG_FORMAT']


CONFIG = loadcfg('sysmon.conf')
LOGGER = getLogger('sysmon')
LOG_FORMAT = '[%(levelname)s] %(name)s: %(message)s'
