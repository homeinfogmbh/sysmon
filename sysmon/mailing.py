"""Monthly customer mailing."""

from __future__ import annotations
from collections import defaultdict
from datetime import date, timedelta
from locale import LC_TIME, setlocale
from logging import basicConfig, getLogger
from pathlib import Path
from typing import Iterable, Iterator

from emaillib import EMailsNotSent, EMail, Mailer
from hwdb import Deployment, System
from mdb import Customer

from sysmon.config import get_config
from sysmon.mean_stats import MeanStats
from sysmon.orm import CheckResults, UserNotificationEmail


__all__ = ['main', 'send_mailing']


TEMPLATE = Path('/usr/local/etc/sysmon.d/customers-email.htt')
LOGGER = getLogger('sysmon-mailing')
SUBJECT = 'Service - Report digitales Brett: {customer.name}'


def main() -> None:
    """Main function for script invocation."""

    basicConfig()

    try:
        send_mailing()
    except EMailsNotSent as not_sent:
        for email in not_sent.emails:
            LOGGER.error('Email not sent: %s', email)


def send_mailing() -> None:
    """Send the mailing."""

    setlocale(LC_TIME, 'de_DE.UTF-8')
    get_mailer().send(
        list(
            create_emails_for_customers(
                get_target_customers(),
                first_day_of_last_month(date.today())
            )
        )
    )


def get_target_customers() -> set[Customer]:
    """Yield customers that shall receive the mailing."""

    customers = set()

    for system in System.select(cascade=True).where(
            ~(System.deployment >> None)
    ):
        customers.add(system.deployment.customer)

    return customers


def get_mailer() -> Mailer:
    """Return the mailer."""

    return Mailer.from_config(get_config())


def create_emails_for_customers(
        customers: Iterable[Customer],
        last_month: date
) -> Iterator[EMail]:
    """Create monthly notification emails for the given customers."""

    sender = get_config().get('email', 'sender', fallback='info@homeinfo.de')

    for customer in customers:
        yield from create_customer_emails(
            customer,
            sender=sender,
            last_month=last_month
        )


def create_customer_emails(
        customer: Customer,
        sender: str,
        last_month: date
) -> Iterator[EMail]:
    """Create the system status summary emails for the given month."""

    if not (check_results := check_results_by_system(
            get_check_results_for_month(customer, last_month)
        )
    ):
        return

    html = get_html(
        customer,
        MeanStats.from_system_check_results(check_results),
        last_month
    )

    for recipient in get_recipients(customer):
        yield EMail(
            subject=SUBJECT.format(customer=customer),
            sender=sender,
            recipient=recipient,
            html=html
        )


def get_html(
        customer: Customer,
        stats: MeanStats,
        last_month: date
) -> str:
    """Return the email body's text."""

    with TEMPLATE.open('r', encoding='utf-8') as file:
        template = file.read()

    return template.format(
        month=last_month.strftime('%B'),
        year=last_month.strftime('%Y'),
        customer=customer,
        percent_online=stats.percent_online,
        upload_download_critical=len(stats.upload_download_critical),
        systems_not_fitted=len(stats.not_fitted),
        overheated_systems=len(stats.overheated)
    )


def get_recipients(customer: Customer) -> Iterator[str]:
    """Yield email addresses for the given customer."""

    for user_notification_email in UserNotificationEmail.select().where(
            UserNotificationEmail.customer == customer
    ):
        yield user_notification_email.email


def check_results_by_system(
        check_results: Iterable[CheckResults]
) -> dict[System, list[CheckResults]]:
    """Convert an iterable of check results into a dict of systems and its
    respective checks results.
    """

    result = defaultdict(list)

    for check_result in check_results:
        result[check_result.system].append(check_result)

    return result


def get_check_results_for_month(
        customer: Customer,
        month: date
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


def first_day_of_last_month(today: date) -> date:
    """Return the first day of the last month."""

    return today.replace(day=1) - timedelta(days=1)
