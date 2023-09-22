"""Monthly customer mailing."""

from __future__ import annotations
from collections import defaultdict
from datetime import date, datetime, timedelta
from locale import LC_TIME, setlocale
from logging import basicConfig, getLogger
from pathlib import Path
from typing import Iterable, Iterator
from peewee import DoesNotExist

from emaillib import EMailsNotSent, EMail, Mailer
from hwdb import Deployment, System
from mdb import Customer

from his import ACCOUNT
from sysmon.config import get_config
from sysmon.mean_stats import MeanStats
from sysmon.orm import CheckResults, UserNotificationEmail, Newsletter


__all__ = ["main", "send_mailing", "get_newsletter_by_date", "send_test_mails"]


TEMPLATE = Path("/usr/local/etc/sysmon.d/customers-email.htt")
MAIL_START = """<!DOCTYPE html>
<html lang="de">
<head><meta charset=UTF-8></head>
<body>"""

MAIL_END = "</body></html>"

DDB_TEXT = """<p>Hiermit erhalten Sie einen Statusbericht für den Monat {month} {year} Ihre Digitalen Bretter:<br>
Im Monat {month} waren {percent_online}% Ihrer Digitalen Bretter online.
</p>
<p>
Sofern sich dazu im Vorfeld Fragen ergeben, stehen wir Ihnen natürlich wie gewohnt sehr gern zur Verfügung.<br>
Bitte nutzen Sie den Link zur detaillierten Monatsstatistik. Hier werden Ihnen auch weiterführende Abläufe beschrieben:<br>
<a href="https://typo3.homeinfo.de/ddb-report?customer={customer.id}">Link zur Webansicht</a>
</p>"""
LOGGER = getLogger("sysmon-mailing")
SUBJECT = "Service - Report Digitales Brett: {customer.name}"

FOOTER_TEXT = """<p>Mit freundlichen Grüßen Ihre</p>
<p><a href="http://mieterinfo.tv/">mieterinfo.tv</a><br>
Kommunikationssysteme GmbH & Co. KG
</p>
<p>
Burgstraße 6a
30826 Garbsen
</p>
<p>
Fon.: 0511 21 24 11 00
</p>
<p>
service@dasdigitalebrett.de<br>
https://dasdigitalebrett.de/
</p>
<p>
Möchten Sie diesen Newsletter nicht mehr bekommen klicken Sie bitte auf diesen <a href="mailto:r.haupt@homeinfo.de?subject=UNSUBSCRIBE&body=Bitte tragen sie diese Emailadresse aus der Newsletter aus">Link</a>.
</p>
"""


def main() -> None:
    """Main function for script invocation."""

    basicConfig()

    try:
        send_mailing()
    except EMailsNotSent as not_sent:
        for email in not_sent.emails:
            LOGGER.error("Email not sent: %s", email)


def send_mailing() -> None:
    """Send the mailing."""

    setlocale(LC_TIME, "de_DE.UTF-8")
    get_mailer().send(
        list(
            create_emails_for_customers(
                get_target_customers(), last_day_of_last_month(date.today())
            )
        )
    )


def send_test_mails(newsletter: int):
    get_mailer().send(
        [create_customer_test_email(newsletter, ACCOUNT.customer, ACCOUNT.email)]
    )
    get_mailer().send([create_other_test_email(newsletter, ACCOUNT.email)])


def create_other_test_email(newsletter: int, recipient: str):
    """Creates a Mail for non DDB clients"""
    sender = get_config().get(
        "mailing", "sender", fallback="service@dasdigitalebrett.de"
    )

    html = get_html_other(newsletter)

    return EMail(
        subject=get_newsletter_by_date(
            Newsletter.select().where(Newsletter.id == newsletter).get().period
        ).subject,
        sender=sender,
        recipient=recipient,
        html=html,
    )


def create_customer_test_email(newsletter: int, customer: Customer, recipient: str):
    """Creates a Mail for DDB clients"""
    sender = get_config().get(
        "mailing", "sender", fallback="service@dasdigitalebrett.de"
    )
    last_month = last_day_of_last_month(date.today())
    if not (
        check_results := check_results_by_system(
            get_check_results_for_month(customer, last_month)
        )
    ):
        return

    html = get_html(
        newsletter,
        customer,
        MeanStats.from_system_check_results(check_results),
        last_month,
    )

    return EMail(
        subject=SUBJECT.format(customer=customer),
        sender=sender,
        recipient=recipient,
        html=html,
    )


def get_target_customers() -> set[Customer]:
    """Yield customers that shall receive the mailing."""

    customers = set()

    for system in System.select(cascade=True).where(
        ~(System.deployment >> None) & (System.fitted == 1)
    ):
        customers.add(system.deployment.customer)

    return customers


def get_mailer() -> Mailer:
    """Return the mailer."""

    return Mailer.from_config(get_config())


def get_newsletter_by_date(now) -> Newsletter:
    """Returns Newsletter for current year/month"""

    try:
        nl = (
            Newsletter.select()
            .where(
                (Newsletter.period.month == now.month)
                & (Newsletter.period.year == now.year)
                & (Newsletter.visible == 1)
            )
            .get()
        )
    except DoesNotExist:
        return Newsletter.select().where(Newsletter.isdefault == 1).get()
    return nl


def create_emails_for_customers(
    customers: Iterable[Customer], last_month: date
) -> Iterator[EMail]:
    """Create monthly notification emails for the given customers."""

    sender = get_config().get(
        "mailing", "sender", fallback="service@dasdigitalebrett.de"
    )

    for customer in customers:
        yield from create_customer_emails(
            customer, sender=sender, last_month=last_month
        )


def create_customer_emails(
    customer: Customer, sender: str, last_month: date
) -> Iterator[EMail]:
    """Create the system status summary emails for the given month."""

    if not (
        check_results := check_results_by_system(
            get_check_results_for_month(customer, last_month)
        )
    ):
        return

    html = get_html(
        1, customer, MeanStats.from_system_check_results(check_results), last_month
    )

    for recipient in get_recipients(customer):
        yield EMail(
            subject=SUBJECT.format(customer=customer),
            sender=sender,
            recipient=recipient,
            html=html,
        )


def get_html(
    newsletter: int, customer: Customer, stats: MeanStats, last_month: date
) -> str:
    """Return the email body's for DDB customers."""

    template = (
        MAIL_START
        + get_newsletter_by_date(
            Newsletter.select().where(Newsletter.id == newsletter).get().period
        ).text
        + DDB_TEXT
        + FOOTER_TEXT
        + MAIL_END
    )
    return template.format(
        month=last_month.strftime("%B"),
        year=last_month.strftime("%Y"),
        customer=customer,
        percent_online=stats.percent_online,
        out_of_sync_but_online=len(stats.out_of_date(datetime.now())),
    )


def get_html_other(newsletter: int) -> str:
    """Return the email body's for non DDB customers."""

    template = (
        MAIL_START
        + get_newsletter_by_date(
            Newsletter.select().where(Newsletter.id == newsletter).get().period
        ).text
        + FOOTER_TEXT
        + MAIL_END
    )
    return template


def get_recipients(customer: Customer) -> Iterator[str]:
    """Yield email addresses for the given customer."""

    for user_notification_email in UserNotificationEmail.select().where(
        UserNotificationEmail.customer == customer
    ):
        yield user_notification_email.email


def check_results_by_system(
    check_results: Iterable[CheckResults],
) -> dict[System, list[CheckResults]]:
    """Convert an iterable of check results into a dict of systems and its
    respective checks results.
    """

    result = defaultdict(list)

    for check_result in check_results:
        result[check_result.system].append(check_result)

    return result


def get_check_results_for_month(
    customer: Customer, month: date
) -> Iterable[CheckResults]:
    """Get the check results for the given customer and month."""

    return CheckResults.select(cascade=True).where(
        (Deployment.customer == customer)
        & (CheckResults.timestamp >= month.replace(day=1))
        & (CheckResults.timestamp < first_day_of_next_month(month))
    )


def first_day_of_next_month(month: date) -> date:
    """Return the date of the first day of the next month."""

    return (month.replace(day=28) + timedelta(days=4)).replace(day=1)


def last_day_of_last_month(today: date) -> date:
    """Return the last day of the last month."""

    return today.replace(day=1) - timedelta(days=1)
