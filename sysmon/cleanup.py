"""Records cleanup."""

from argparse import ArgumentParser, Namespace
from datetime import datetime, timedelta
from logging import INFO, basicConfig, getLogger

from sysmon.config import LOG_FORMAT
from sysmon.orm import CheckResults


__all__ = ['cleanup']


LOGGER = getLogger('sysmon-cleanup')
MAX_RETENTION = timedelta(days=90)


def remove_checks_older_than(age: timedelta) -> int:
    """Removes system checks older than the specified time."""

    return remove_checks_before(datetime.now() - age)


def remove_checks_before(timestamp: datetime) -> int:
    """Removes system checks older than the given timestamp."""

    return CheckResults.delete().where(
        CheckResults.timestamp < timestamp
    ).execute()


def get_args() -> Namespace:
    """Parses the CLI arguments."""

    parser = ArgumentParser(description='cleans old records')
    parser.add_argument(
        '-d', '--days', type=lambda days: timedelta(days=days),
        default=MAX_RETENTION, help='days of records to keep'
    )
    return parser.parse_args()


def main() -> None:
    """Runs the program."""

    args = get_args()
    basicConfig(format=LOG_FORMAT, level=INFO)
    LOGGER.info('Deleting records older than %i days.', args.days)
    count = remove_checks_older_than(args.days)
    LOGGER.info('Deleted %i records.', count)
