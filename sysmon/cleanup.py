"""Records cleanup."""

from argparse import ArgumentParser
from datetime import datetime, timedelta
from logging import INFO, basicConfig, getLogger

from sysmon.config import LOG_FORMAT
from sysmon.orm import CHECKS


__all__ = ['main']


LOGGER = getLogger('sysmon-cleanup')


def days(string):
    """Returns a timedelta with the given days."""

    return timedelta(days=int(string))


def get_args():
    """Parses the CLI arguments."""

    parser = ArgumentParser(description='cleans old records')
    parser.add_argument('-t', '--tables', nargs='*',
                        default=CHECKS, help='tables to clean')
    parser.add_argument('-d', '--days', type=int, default=30,
                        help='days of records to keep')
    return parser.parse_args()


def main():
    """Runs the program."""

    args = get_args()
    basicConfig(format=LOG_FORMAT, level=INFO)
    timestamp = datetime.now() - timedelta(days=args.days)
    LOGGER.info('Deleting records older than %i days.', args.days)

    for table in args.tables:
        LOGGER.info('Cleaning up table: %s', table.__name__)
        count = table.delete().where(table.timestamp < timestamp).execute()
        LOGGER.info('Deleted %i records.', count)
