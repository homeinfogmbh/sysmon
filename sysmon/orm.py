"""ORM models."""

from datetime import datetime

from peewee import BooleanField, DateTimeField, ForeignKeyField

from peeweeplus import JSONModel, MySQLDatabase
from terminallib import is_online, System

from sysmon.config import CONFIG
from sysmon.checks import check_application


__all__ = [
    'CHECKS',
    'DATABASE',
    'MODELS',
    'create_tables',
    'SysmonModel',
    'SystemCheck',
    'OnlineCheck',
    'ApplicationCheck']


DATABASE = MySQLDatabase.from_config(CONFIG['db'])


def create_tables(*args, **kwargs):
    """Creates the respective tables."""

    for model in MODELS:
        model.create_table(*args, **kwargs)


class SysmonModel(JSONModel):
    """Abstract base model for the sysmon database."""

    class Meta:     # pylint: disable=C0111,R0903
        database = DATABASE
        schema = database.database


class SystemCheck(SysmonModel):
    """Abstract model for checks."""

    timestamp = DateTimeField(default=datetime.now)
    system = ForeignKeyField(
        System, column_name='system', on_delete='CASCADE', on_update='CASCADE')


class OnlineCheck(SystemCheck):
    """List of online checks of systems."""

    class Meta:     # pylint: disable=C0111,R0903
        table_name = 'online_check'

    online = BooleanField(default=False)

    @classmethod
    def run(cls, system):
        """Runs the checks on the respective systems."""
        record = cls(system=system, online=is_online(system))
        record.save()


class ApplicationCheck(SystemCheck):
    """List of application status checks for systems."""

    class Meta:     # pylint: disable=C0111,R0903
        table_name = 'application_check'

    enabled = BooleanField(null=True)
    running = BooleanField(null=True)

    @classmethod
    def run(cls, system):
        """Runs the checks on the respective systems."""
        enabled, running = check_application(system)
        record = cls(system=system, enabled=enabled, running=running)
        record.save()


CHECKS = (OnlineCheck, ApplicationCheck)
MODELS = CHECKS
