"""Emailing to administrators."""

from typing import Iterator
from xml.etree.ElementTree import Element, tostring

from emaillib import EMail, Mailer

from sysmon.config import get_config


__all__ = ['email']


def admins() -> Iterator[str]:
    """Yields admins's emails."""

    return filter(None, map(
        str.strip, get_config().get('mail', 'admins').split(','))
    )


def emails(html: Element) -> Iterator[EMail]:
    """Send emails to admins."""

    subject = (config := get_config()).get('mail', 'subject')
    html = tostring(html, encoding='unicode', method='html')

    for admin in admins():
        yield EMail(subject, config.get('mail', 'email'), admin, html=html)


def email(html: Element) -> bool:
    """Sends emails to admins."""

    return Mailer(
        (config := get_config()).get('mail', 'host'),
        config.getint('mail', 'port'),
        config.get('mail', 'user'),
        config.get('mail', 'passwd')
    ).send(emails(html))
