"""Common exceptions."""


__all__ = ['NotChecked']


class NotChecked(Exception):
    """Indicates that a check was not yet performed on a system."""

    def __init__(self, system, check):
        """Sets system an check."""
        super().__init__(system, check)
        self.system = system
        self.check = check
