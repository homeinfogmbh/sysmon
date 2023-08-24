"""Mean system statistics."""

from __future__ import annotations
from datetime import datetime
from functools import partial
from itertools import filterfalse
from math import floor
from typing import Iterable, NamedTuple

from hwdb import System

from sysmon.config import MIN_DOWNLOAD, MIN_UPLOAD
from sysmon.enumerations import SuccessFailedUnsupported
from sysmon.functions import is_in_sync
from sysmon.orm import CheckResults


__all__ = ["MeanStats"]


class MeanStats(NamedTuple):
    """Mean system check result statistics."""

    systems: frozenset[System]
    online: frozenset[System]
    download_critical: frozenset[System]
    upload_critical: frozenset[System]
    not_fitted: frozenset[System]
    overheated: frozenset[System]

    @classmethod
    def from_system_check_results(
        cls, system_check_results: dict[System, Iterable[CheckResults]]
    ) -> MeanStats:
        """Create mean system stats from system-mapped check results."""
        online = set()
        download_critical = set()
        upload_critical = set()
        not_fitted = set()
        overheated = set()

        for system, check_results in system_check_results.items():
            if any(check_result.online for check_result in check_results):
                online.add(system)

            if all(
                check_result.download is None or check_result.download < MIN_DOWNLOAD
                for check_result in check_results
            ):
                download_critical.add(system)

            if all(
                check_result.upload is None or check_result.upload < MIN_UPLOAD
                for check_result in check_results
            ):
                upload_critical.add(system)

            if system.deployment is not None and not system.fitted:
                not_fitted.add(system)

            # System is considered overheated, iff it was never measured as
            # not overheated, but measured as overheated.
            # Thus, the system was always either overheated or could not be
            # measured.
            if not any(
                check_result.sensors is SuccessFailedUnsupported.SUCCESS
                for check_result in check_results
            ) and any(
                check_result.sensors is SuccessFailedUnsupported.FAILED
                for check_result in check_results
            ):
                overheated.add(system)

        return cls(
            frozenset(system_check_results),
            frozenset(online),
            frozenset(download_critical),
            frozenset(upload_critical),
            frozenset(not_fitted),
            frozenset(overheated),
        )

    @property
    def percent_online(self) -> int:
        """Return percentage of online systems."""
        return floor(len(self.online) / len(self.systems) * 100)

    @property
    def upload_download_critical(self) -> frozenset[System]:
        """Return the systems where upload and/or download are critical."""
        return self.download_critical | self.upload_critical

    def out_of_date(self, now: datetime) -> frozenset[System]:
        """Returns systems that are online but out of date."""
        return frozenset(filterfalse(partial(is_in_sync, now=now), self.online))
