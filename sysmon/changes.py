"""Processing of state changes."""

from contextlib import suppress
from typing import Iterator, NamedTuple
from xml.etree.ElementTree import Element, SubElement

from hwdb import System

from sysmon.enumerations import State
from sysmon.exceptions import NotChecked
from sysmon.orm import CheckResults


__all__ = ['CheckState', 'check_state_change', 'state_changes']


class CheckState(NamedTuple):
    """A system's service check state."""

    system: System
    state: State

    def to_html(self) -> Element:
        """Returns an HTML element."""
        row = Element('tr')
        header = SubElement(row, 'th')
        header.text = str(self.system.id)
        column = SubElement(row, 'td')

        if self.system.deployment is None:
            column.text = 'Not deployed'
        else:
            column.text = str(self.system.deployment)

        column = SubElement(row, 'td')
        column.text = self.state
        return row


def check_state_change(system: System) -> CheckState:
    """Checks the state change for the respective system and check."""

    select = CheckResults.select().where(
        CheckResults.system == system
    ).order_by(CheckResults.timestamp.desc()).limit(2)

    try:
        last, *previous = select
    except ValueError:
        raise NotChecked(system) from None

    if previous:
        previous, = previous

        if last.successful and not previous.successful:
            return CheckState(system, State.RECOVERED)

        if previous.successful and not last.successful:
            return CheckState(system, State.FAILED)

        return CheckState(system, State.UNCHANGED)

    if last.successful:
        return CheckState(system, State.RECOVERED)

    return CheckState(system, State.FAILED)


def state_changes() -> Iterator[CheckState]:
    """Yields state changes."""

    for system in System.monitored():
        with suppress(NotChecked):
            yield check_state_change(system)
