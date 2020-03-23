"""Processing of state changes."""

from contextlib import suppress
from enum import Enum
from typing import NamedTuple
from xml.etree.ElementTree import Element, SubElement

from terminallib import System

from sysmon.exceptions import NotChecked
from sysmon.orm import CHECKS, SystemCheck


__all__ = ['State', 'CheckState', 'check_state_change', 'state_changes']


class State(Enum):
    """State change of a system check."""

    RECOVERED = 'recovered'
    FAILED = 'failed'
    UNCHANGED = 'unchanged'


class CheckState(NamedTuple):
    """A system's service check state."""

    system: System
    check: SystemCheck
    state: State

    def to_xml(self):
        """Returns an XML element."""
        row = Element('tr')
        header = SubElement(row, 'th')
        header.text = str(self.system.id)
        column = SubElement(row, 'td')

        if self.system.deployment is None:
            column.text = 'Not deployed'
        else:
            column.text = str(self.system.deployment)

        column = SubElement(row, 'td')
        column.text = self.check.message
        return row


def check_state_change(system, check):
    """Checks the state change for the respective system and check."""

    select = check.select().where(check.system == system)
    select = select.order_by(check.timestamp.desc()).limit(2)

    try:
        last, *previous = select
    except ValueError:
        raise NotChecked(system, check)

    if previous:
        previous, = previous

        if last.successful and not previous.successful:
            return CheckState(system, last, State.RECOVERED)

        if previous.successful and not last.successful:
            return CheckState(system, last, State.FAILED)

        return CheckState(system, last, State.UNCHANGED)

    if last.successful:
        return CheckState(system, last, State.RECOVERED)

    return CheckState(system, last, State.FAILED)


def state_changes():
    """Yields state changes."""

    for system in System.monitored():
        for check in CHECKS:
            with suppress(NotChecked):
                yield check_state_change(system, check)
