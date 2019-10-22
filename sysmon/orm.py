"""ORM models."""

from datetime import datetime, timedelta

from peewee import BooleanField, DateTimeField, ForeignKeyField

from mdb import Customer
from peeweeplus import EnumField, JSONModel, MySQLDatabase
from terminallib import System, Type

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
    'ApplicationCheck'
]


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

    @classmethod
    def run(cls, system):
        """Runs the checks on the respective systems."""
        raise NotImplementedError()

    @property
    def successful(self):
        """Checks whether the check was successful."""
        raise NotImplementedError()

    @property
    def message(self):
        """Returns the state message."""
        raise NotImplementedError()

    def to_json(self, **kwargs):
        """Returns a JSON-ish dict."""
        json = super().to_json(**kwargs)
        json['successful'] = self.successful
        return json


class OnlineCheck(SystemCheck):
    """List of online checks of systems."""

    class Meta:     # pylint: disable=C0111,R0903
        table_name = 'online_check'

    online = BooleanField(default=False)

    @classmethod
    def run(cls, system):
        """Runs the checks on the respective systems."""
        record = cls(system=system, online=system.online)
        record.save()
        return record

    @property
    def successful(self):
        """Checks whether the check was successful."""
        return self.online

    @property
    def message(self):
        """Returns the state message."""
        return 'is online' if self.online else 'is offline'


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
        return record

    @property
    def successful(self):
        """Checks whether the check was successful."""
        return self.enabled and self.running

    @property
    def message(self):
        """Returns the state message."""
        if self.enabled and self.running:
            return 'Application is up and running'

        if self.enabled and not self.running:
            return 'Application enabled but not running'

        if not self.enabled and self.running:
            return 'Application is disabled but running'

        return 'Application is disabled and not running'


class TypeAdmin(SysmonModel):
    """Administrators of a certain type."""

    type = EnumField(Type)
    customer = ForeignKeyField(
        Customer, column_name='customer', on_delete='CASCADE',
        on_update='CASCADE')


CHECKS = (OnlineCheck, ApplicationCheck)
MODELS = (TypeAdmin,) + CHECKS
