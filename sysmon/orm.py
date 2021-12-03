"""ORM models."""

from __future__ import annotations
from datetime import datetime

from requests import Timeout
from simplejson.errors import JSONDecodeError

from peewee import JOIN
from peewee import BooleanField
from peewee import DateTimeField
from peewee import ForeignKeyField
from peewee import ModelSelect

from hwdb import SystemOffline, Deployment, System
from mdb import Address, Company, Customer
from peeweeplus import JSONModel, MySQLDatabaseProxy

from sysmon.types import ApplicationState


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


DATABASE = MySQLDatabaseProxy('sysmon')


def create_tables(*args, **kwargs) -> None:
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
        System, column_name='system', on_delete='CASCADE', on_update='CASCADE',
        lazy_load=False)

    @classmethod
    def run(cls, system: System):
        """Runs the checks on the respective systems."""
        raise NotImplementedError()

    @classmethod
    def select(cls, *args, cascade: bool = False, **kwargs) -> ModelSelect:
        """Selects records."""
        if not cascade:
            return super().select(*args, **kwargs)

        dataset = Deployment.alias()
        args = {
            cls, System, Deployment, Customer, Company, Address, dataset,
            *args
        }
        return super().select(*args).join(System).join(
            Deployment, on=System.deployment == Deployment.id,
            join_type=JOIN.LEFT_OUTER).join(
            Customer, join_type=JOIN.LEFT_OUTER).join(
            Company, join_type=JOIN.LEFT_OUTER).join_from(
            Deployment, Address, on=Deployment.address == Address.id,
            join_type=JOIN.LEFT_OUTER).join_from(
            System, dataset, on=System.dataset == dataset.id,
            join_type=JOIN.LEFT_OUTER)

    @property
    def successful(self):
        """Checks whether the check was successful."""
        raise NotImplementedError()

    @property
    def message(self):
        """Returns the state message."""
        raise NotImplementedError()

    def to_json(self, **kwargs) -> dict:
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
    def run(cls, system: System) -> OnlineCheck:
        """Runs the checks on the respective systems."""
        record = cls(system=system, online=system.online)
        record.save()
        return record

    @property
    def successful(self) -> bool:
        """Checks whether the check was successful."""
        return self.online

    @property
    def message(self) -> str:
        """Returns the state message."""
        return 'is online' if self.online else 'is offline'


class ApplicationCheck(SystemCheck):
    """List of application status checks for systems."""

    class Meta:     # pylint: disable=C0111,R0903
        table_name = 'application_check'

    enabled = BooleanField(null=True)
    running = BooleanField(null=True)

    @classmethod
    def _get_states(cls, system: System) -> ApplicationState:
        """Gets the application states from the respective system."""
        try:
            response = system.exec('application', state=None)
        except (Timeout, SystemOffline):
            return ApplicationState(None, None)

        try:
            json = response.json()
        except JSONDecodeError:
            return ApplicationState(None, None)

        return ApplicationState(json.get('enabled'), json.get('running'))

    @classmethod
    def run(cls, system: System) -> ApplicationCheck:
        """Runs the checks on the respective systems."""
        enabled, running = cls._get_states(system)
        record = cls(system=system, enabled=enabled, running=running)
        record.save()
        return record

    @property
    def successful(self) -> bool:
        """Checks whether the check was successful."""
        return self.enabled and self.running

    @property
    def message(self) -> str:
        """Returns the state message."""
        if self.enabled and self.running:
            return 'Application is up and running'

        if self.enabled and not self.running:
            return 'Application enabled but not running'

        if not self.enabled and self.running:
            return 'Application is disabled but running'

        return 'Application is disabled and not running'


MODELS = CHECKS = (OnlineCheck, ApplicationCheck)
