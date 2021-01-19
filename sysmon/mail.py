"""Emailing to administrators."""

from typing import Iterator
from xml.etree.ElementTree import Element, tostring

from emaillib import EMail, Mailer
from functoolsplus import coerce

from sysmon.config import CONFIG


__all__ = ['email']


def admins() -> Iterator[str]:
    """Yields admins's emails."""

    return filter(None, map(
        str.strip, CONFIG.get('mail', 'admins').split(','))
    )


@coerce(tuple)
def emails(html: Element) -> Iterator[EMail]:
    """Send emails to admins."""

    subject = CONFIG['mail']['subject']
    html = tostring(html, encoding='unicode', method='html')

    for admin in admins():
        yield EMail(subject, CONFIG['mail']['email'], admin, html=html)


def email(html: Element) -> None:
    """Sends emails to admins."""

    mailer = Mailer(
        CONFIG['mail']['host'], int(CONFIG['mail']['port']),
        CONFIG['mail']['user'], CONFIG['mail']['passwd'])
    mailer.send(emails(html))
