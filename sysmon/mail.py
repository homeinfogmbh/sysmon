"""Emailing to administrators."""

from xml.etree.ElementTree import tostring

from emaillib import EMail, Mailer

from sysmon.config import CONFIG


__all__ = ['email']


def admins():
    """Yields admins's emails."""

    emails_ = CONFIG['mail']['admins'].split(',')
    return filter(None, map(lambda email: email.strip(), emails_))


def emails(html):
    """Send emails to admins."""

    subject = CONFIG['mail']['subject']
    html = tostring(html, encoding='UTF-8', method='html')

    for admin in admins():
        yield EMail(subject, CONFIG['mail']['email'], admin, html=html)


def email(html):
    """Sends emails to admins."""

    mailer = Mailer(
        CONFIG['mail']['host'], int(CONFIG['mail']['port']),
        CONFIG['mail']['user'], CONFIG['mail']['passwd'])
    mailer.send(emails(html))
