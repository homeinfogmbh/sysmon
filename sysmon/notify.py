"""System state notification."""

from typing import Iterable
from xml.etree.ElementTree import Element, SubElement

from sysmon.changes import CheckState, state_changes
from sysmon.config import LOGGER
from sysmon.enumerations import State
from sysmon.mail import email


__all__ = ['notify']


def mk_html_table(check_states: Iterable[CheckState]) -> Element:
    """Returns a HTML table."""

    table = Element('table', attrib={'border': '1'})

    for check_state in check_states:
        table.append(check_state.to_html())

    return table


def mk_html_msg(
        recovered: Iterable[CheckState],
        failed: Iterable[CheckState]
) -> Element:
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


def notify() -> None:
    """Notifies about state changes."""

    recovered = []
    failed = []

    for check_state in state_changes():
        if check_state.state == State.RECOVERED:
            recovered.append(check_state)
        elif check_state.state == State.FAILED:
            failed.append(check_state)

    html = mk_html_msg(recovered, failed)
    LOGGER.info('Notifying admins about state changes.')
    email(html)
