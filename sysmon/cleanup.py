"""Records cleanup."""

from argparse import ArgumentParser, Namespace
from datetime import datetime, timedelta
from logging import INFO, basicConfig, getLogger

from sysmon.config import LOG_FORMAT
from sysmon.orm import CheckResults


__all__ = ['main']


LOGGER = getLogger('sysmon-cleanup')


def get_args() -> Namespace:
    """Parses the CLI arguments."""

    parser = ArgumentParser(description='cleans old records')
    parser.add_argument(
        '-d', '--days', type=int, default=30, help='days of records to keep'
    )
    return parser.parse_args()


def main() -> None:
    """Runs the program."""

    args = get_args()
    basicConfig(format=LOG_FORMAT, level=INFO)
    LOGGER.info('Deleting records older than %i days.', args.days)
    count = CheckResults.delete().where(
        CheckResults.timestamp < datetime.now() - timedelta(days=args.days)
    ).execute()
    LOGGER.info('Deleted %i records.', count)
