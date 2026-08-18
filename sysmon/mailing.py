"""Customer statistics and warning mailing."""

from __future__ import annotations
from logging import getLogger
from math import floor

from emaillib import Mailer, EMail
from his import ACCOUNT
from hwdb import Deployment, System

from sysmon.config import get_config
from sysmon.functions import get_latest_check_results_48h
from sysmon.orm import (
    UserNotificationEmail,
    StatisticUserNotificationEmail,
    Warningmail,
)


__all__ = [
    "statistic",
    "send_warning_mails",
    "send_warning_test_mails",
    "send_statistic_test_mails",
]


LOGGER = getLogger("sysmon-mailing")


def get_mailer() -> Mailer:
    """Return the mailer."""

    return Mailer.from_config(get_config())


class StatsSystemsByCustomer:
    customer: object
    systemsOnline: int
    systemsOffline: int
    systemsAll: int

    def __init__(self, customer, systemsOnline=0, systemsOffline=0, systemsAll=0):
        self.customer = customer
        self.systemsOnline = systemsOnline
        self.systemsOffline = systemsOffline
        self.systemsAll = systemsAll

    @property
    def percentOffline(self):
        if self.systemsOffline == 0:
            return 0
        if self.systemsAll == 0:
            return 0
        return floor(self.systemsOffline / self.systemsAll * 100)


def create_warning_email(email, customer):
    # creates email with Customers who have more than minpercent offline systems

    sender = get_config().get(
        "mailing", "sender", fallback="service@dasdigitalebrett.de"
    )
    mailbody = Warningmail.select().get().text
    mailsubject = Warningmail.select().get().subject
    minpercent = Warningmail.select().get().minpercent
    minsystems = Warningmail.select().get().minsystems
    stats = []
    stat = StatsSystemsByCustomer(customer)
    for checkresult in get_latest_check_results_48h(
        (
            (Deployment.customer == customer)
            & (Deployment.testing == 0)
            & (System.testing == 0)
        )
    ):
        stat.systemsAll = stat.systemsAll + 1
        if checkresult.icmp_request:
            stat.systemsOnline = stat.systemsOnline + 1
        else:
            stat.systemsOffline = stat.systemsOffline + 1
        stats.append(stat)

    for stat in stats:
        try:
            customername = stat.customer.abbreviation
        except:
            customername = stat.customer
        if stat.percentOffline >= minpercent and stat.systemsAll >= minsystems:
            mailbody = mailbody.format(
                customer=customername,
                percentOffline=stat.percentOffline,
                systemsAll=stat.systemsAll,
                systemsOffline=stat.systemsOffline,
                customerId=stat.customer.id,
                weblink='<a href="https://portal.homeinfo.de/ddb-report?customer='
                + str(stat.customer.id)
                + '">Link zur Webansicht</a>',
            )
            mailsubject = mailsubject.format(
                customer=customername,
                percentOffline=stat.percentOffline,
                systemsAll=stat.systemsAll,
                systemsOffline=stat.systemsOffline,
            )
            return EMail(
                subject=mailsubject,
                sender=sender,
                recipient=email,
                html=mailbody,
            )


def create_statistic_email(email):
    sender = get_config().get(
        "mailing", "sender", fallback="service@dasdigitalebrett.de"
    )
    mailbody = """
    <style>
    td { padding: 10px; padding-bottom:0px; }
    </style>
    <p>Hier finden Sie eine Liste der Kunden, bei denen in den letzten 48 Stunden mehr als 10% ihrer Systeme offline waren
    </p>"""

    # Single query for all customers at once
    stats: dict[int, StatsSystemsByCustomer] = {}
    for checkresult in get_latest_check_results_48h(
        (Deployment.testing == 0) & (System.testing == 0)
    ):
        customer = checkresult.system.deployment.customer
        if customer.id not in stats:
            stats[customer.id] = StatsSystemsByCustomer(customer)
        stat = stats[customer.id]
        stat.systemsAll += 1
        if checkresult.icmp_request:
            stat.systemsOnline += 1
        else:
            stat.systemsOffline += 1

    html = ""
    htmlSystemsHighlighted = ""
    for stat in stats.values():
        try:
            customername = stat.customer.abbreviation
        except Exception:
            customername = stat.customer
        row = (
            f"<tr><td>{customername}</td>"
            f"<td>{stat.percentOffline}% ({stat.systemsOffline})</td>"
            f"<td>{stat.systemsAll}</td></tr>"
        )
        if stat.percentOffline > 9:
            htmlSystemsHighlighted += row
        else:
            html += row

    html = (
        "<h1>Alle Kunden</h1>"
        "<table><tr><th>Kunde</th><th>Offline</th><th>Gesamt</th></tr>"
        + html + "</table>"
    )
    htmlSystemsHighlighted = (
        "<table><tr><th>Kunde</th><th>Offline</th><th>Gesamt</th></tr>"
        + htmlSystemsHighlighted + "</table>"
    )

    return EMail(
        subject="Homeinfo Service Notification",
        sender=sender,
        recipient=email,
        html=mailbody + htmlSystemsHighlighted + html,
    )


def send_statistic_test_mails():
    # send statistic mail to user logged into sysmon
    get_mailer().send([create_statistic_email(ACCOUNT.email)])


def send_warning_test_mails():
    # send warning mails to user logged into sysmon
    get_mailer().send(get_warning_mails_test())


def get_warning_mails_test():
    for email in UserNotificationEmail.select():
        message = create_warning_email(ACCOUNT.email, email.customer)
        if message is not None:
            yield message


def send_warning_mails():
    # send warning mails to users in database
    get_mailer().send(list(get_warning_mails()))


def get_warning_mails():
    for email in UserNotificationEmail.select():
        message = create_warning_email(email.email, email.customer)
        if message is not None:
            yield message


def statistic():
    # sends statistic mailing to users in database
    get_mailer().send(list(create_statistic_emails()))


def create_statistic_emails():
    for email in StatisticUserNotificationEmail.select():
        yield create_statistic_email(email.email)
