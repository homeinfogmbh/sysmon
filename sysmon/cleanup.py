"""Records cleanup."""

from argparse import ArgumentParser
from datetime import datetime, timedelta
from logging import INFO, basicConfig, getLogger

from sysmon.config import LOG_FORMAT
from sysmon.orm import CHECKS


__all__ = ['main']


LOGGER = getLogger('sysmon-cleanup')
TABLES = {table.__name__: table for table in CHECKS}


def get_tables(names):
    """Returns the respective type by its name."""

    for name in names:
        try:
            yield TABLES[name]
        except KeyError:
            LOGGER.error('No such table: %s', name)


def get_args():
    """Parses the CLI arguments."""

    parser = ArgumentParser(description='cleans old records')
    parser.add_argument('-t', '--tables', nargs='*', default=TABLES.keys(),
                        help='tables to clean')
    parser.add_argument('-d', '--days', type=int, default=30,
                        help='days of records to keep')
    return parser.parse_args()


def main():
    """Runs the program."""

    args = get_args()
    basicConfig(format=LOG_FORMAT, level=INFO)
    timestamp = datetime.now() - timedelta(days=args.days)
    LOGGER.info('Deleting records older than %i days.', args.days)

    for table in get_tables(args.tables):
        LOGGER.info('Cleaning up table: %s', table.__name__)
        count = table.delete().where(table.timestamp < timestamp).execute()
        LOGGER.info('Deleted %i records.', count)
