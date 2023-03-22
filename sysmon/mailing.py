"""Monthly customer mailing."""

from __future__ import annotations
from collections import defaultdict
from datetime import date, timedelta
from typing import Iterable, Iterator

from emaillib import EMail
from hwdb import Deployment, System
from mdb import Customer

from sysmon.mean_stats import MeanStats
from sysmon.orm import CheckResults, UserNotificationEmail


__all__ = ['create_emails']


BODY = '''Sehr geehrter Kunde,

hiermit erhalten Sie eine Übersicht für den Monat {month} {year} Ihrer 
Systeme.

Im Monat {month} sind {percent_online}% der {customer_name} Displays Online gewesen.
Sie haben {upload_download_critical} Systeme bei denen der Download/Upload unter den Mindestanforderungen liegt.
Die Anzahl der bereits bereitgestellten, jedoch noch nicht verbaute Displays ist {systems_not_fitted}.
Durch Überhitzung sind möglicherweise {overheated_systems} Systeme gefährdet.

Mit freundlichen Grüßen Ihre...

HOMEINFO Medienservice GmbH
Mobil: +49 172 5113221
technik@homeinfo-medienservice.de
'''
SENDER = 'info@homeinfo.de'
SUBJECT = 'HOMEINFO: Displaystatistik {date}'


def create_emails(
        customer: Customer,
        today: date
) -> Iterator[EMail]:
    """Create the system status summary emails for the given month."""

    subject = SUBJECT.format(date=today.strftime('%b %Y'))
    text = get_text(
        customer,
        MeanStats.from_system_check_results(
            check_results_by_system(
                get_check_results_for_month(
                    customer, today
                )
            )
        ),
        today
    )

    for recipient in get_recipients(customer):
        yield EMail(
            subject=subject,
            sender=SENDER,
            recipient=recipient,
            plain=text
        )


def get_text(
        customer: Customer,
        stats: MeanStats,
        today: date
) -> str:
    """Return the email body's text."""

    return BODY.format(
        month=today.strftime('%b'),
        year=today.strftime('%Y'),
        customer_name=customer.name,
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
