"""Monthly customer mailing."""

from __future__ import annotations
from collections import defaultdict
from datetime import date, timedelta
from math import floor
from typing import Iterable, Iterator, NamedTuple

from emaillib import EMail
from hwdb import Deployment, System
from mdb import Customer

from sysmon.enumerations import SuccessFailedUnsupported
from sysmon.orm import CheckResults


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
MIN_DOWNLOAD = 1953.125     # Kilobits/s
MIN_UPLOAD = 488.28125      # Kilobits/s


class MonthlyStats(NamedTuple):
    """Monthly display stats."""

    systems: frozenset[System]
    online: frozenset[System]
    download_critical: frozenset[System]
    upload_critical: frozenset[System]
    not_fitted: frozenset[System]
    overheated: frozenset[System]

    @property
    def percent_online(self) -> int:
        """Return percentage of online systems."""
        return floor(len(self.online) / len(self.systems) * 100)

    @property
    def upload_download_critical(self) -> frozenset[System]:
        """Return the systems where upload and/or download are critical."""
        return self.download_critical | self.upload_critical

    @classmethod
    def from_system_check_results(
            cls,
            system_check_results: dict[System, Iterable[CheckResults]]
    ) -> MonthlyStats:
        """Create monthly stats from monthly check results."""
        online = set()
        download_critical = set()
        upload_critical = set()
        not_fitted = set()
        overheated = set()

        for system, check_results in system_check_results.items():
            if any(check_result.online for check_result in check_results):
                online.add(system)

            if all(
                    check_result.download < MIN_DOWNLOAD
                    for check_result in check_results
            ):
                download_critical.add(system)

            if all(
                    check_result.upload < MIN_UPLOAD
                    for check_result in check_results
            ):
                upload_critical.add(system)

            if system.deployment is not None and not system.fitted:
                not_fitted.add(system)

            if all(
                    check_result.sensors is SuccessFailedUnsupported.FAILED
                    for check_result in check_results
            ):
                overheated.add(system)

        return MonthlyStats(
            frozenset(system_check_results),
            frozenset(online),
            frozenset(download_critical),
            frozenset(upload_critical),
            frozenset(not_fitted),
            frozenset(overheated)
        )


def create_emails(
        customer: Customer,
        today: date
) -> Iterator[EMail]:
    """Create the system status summary emails for the given month."""

    subject = SUBJECT.format(date=today.strftime('%b %Y'))
    text = get_text(
        customer,
        MonthlyStats.from_system_check_results(
            check_results_by_system(
                get_check_results_for_month(
                    customer, today
                )
            )
        ),
        today
    )

    for recipient in get_recipients(customer):
        return EMail(
            subject=subject,
            sender=SENDER,
            recipient=recipient,
            plain=text
        )


def get_text(
        customer: Customer,
        stats: MonthlyStats,
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

    raise NotImplementedError()


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
