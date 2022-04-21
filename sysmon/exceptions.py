"""Common exceptions."""

from hwdb import System


__all__ = ['NotChecked']


class NotChecked(Exception):
    """Indicates that a check was not yet performed on a system."""

    def __init__(self, system: System):
        super().__init__(system)
        self.system = system
