"""System state notification."""

from enum import Enum
from xml.etree.ElementTree import Element, SubElement
from typing import NamedTuple

from terminallib import System

from sysmon.mail import email
from sysmon.orm import CHECKS, SystemCheck


__all__ = ['notify']


def state_changes():
    """Yields state changes."""

    for system in System.monitored():
        for check in CHECKS:
            try:
                last, *previous = check.select().where(
                    check.system == system).order_by(
                        check.timestamp.desc()).limit(2)
            except ValueError:
                continue

            if previous:
                previous, *_ = previous

                if last.successful and not previous.successful:
                    yield CheckState(system, check, State.RECOVERED)
                elif previous.successful and not last.successful:
                    yield CheckState(system, check, State.FAILED)
                else:
                    yield CheckState(system, check, State.UNCHANGED)
            else:
                if last.successful:
                    yield CheckState(system, check, State.RECOVERED)
                else:
                    yield CheckState(system, check, State.FAILED)


def mk_html_table(check_states):
    """Returns a HTML table."""

    table = Element('table', attrib={'border': '1'})

    for check_state in check_states:
        sub_element = check_state.to_xml()
        table.append(sub_element)

    return table


def mk_html_msg(recovered, failed):
    """Returns a HTML message."""

    html = Element('html')
    header = SubElement(html, 'header')
    SubElement(header, 'meta', attrib={'charset': 'UTF-8'})
    title = SubElement(header, 'title')
    title.text = 'HOMEINFO system status report'
    body = SubElement(html, 'body')
    salutation = SubElement(body, 'span')
    salutation.text = 'Dear Administrator,'
    SubElement(body, 'br')
    SubElement(body, 'br')
    text = SubElement(body, 'span')
    text.text = 'the following state changes have occured:'
    SubElement(body, 'br')
    SubElement(body, 'br')
    header = SubElement(body, 'h2')
    header.text = 'Recoveries:'
    recoveries = mk_html_table(recovered)
    body.append(recoveries)
    header = SubElement(body, 'h2')
    header.text = 'Failures:'
    failures = mk_html_table(failed)
    body.append(failures)
    return html


def notify():
    """Notifies about state changes."""

    recovered = []
    failed = []

    for check_state in state_changes():
        if check_state.state == State.RECOVERED:
            recovered.append(check_state)
        elif check_state.state == State.FAILED:
            failed.append(check_state)

    html = mk_html_msg(recovered, failed)
    email(html)


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
            column.text = '-'
        else:
            column.text = str(self.system.deployment)

        column = SubElement(row, 'td')
        column.text = self.check.message
        return row
