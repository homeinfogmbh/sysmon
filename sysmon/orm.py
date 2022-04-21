"""ORM models."""

from __future__ import annotations
from datetime import datetime

from peewee import JOIN
from peewee import BooleanField
from peewee import CharField
from peewee import DateTimeField
from peewee import ForeignKeyField
from peewee import IntegerField
from peewee import ModelSelect

from hwdb import Deployment, System
from mdb import Address, Company, Customer
from peeweeplus import EnumField, JSONModel, MySQLDatabaseProxy

from sysmon.enumerations import ApplicationState
from sysmon.enumerations import BaytrailFreezeState
from sysmon.enumerations import SuccessFailedUnsupported


__all__ = ['DATABASE', 'SysmonModel', 'CheckResults']


DATABASE = MySQLDatabaseProxy('sysmon')


class SysmonModel(JSONModel):
    """Abstract base model for the sysmon database."""

    class Meta:
        database = DATABASE
        schema = database.database


class CheckResults(SysmonModel):
    """Storage container for check results."""

    timestamp = DateTimeField(default=datetime.now)
    system = ForeignKeyField(
        System, column_name='system', on_delete='CASCADE', on_update='CASCADE',
        lazy_load=False
    )
    icmp_request = BooleanField()
    ssh_login = EnumField(SuccessFailedUnsupported)
    http_request = EnumField(SuccessFailedUnsupported)
    application_state = EnumField(ApplicationState)
    smart_check = EnumField(SuccessFailedUnsupported)
    baytrail_freeze = EnumField(BaytrailFreezeState)
    application_version = CharField(12)
    ram_total = IntegerField(null=True)
    ram_free = IntegerField(null=True)
    ram_available = IntegerField(null=True)
    # Failed-since timestamps
    offline_since = DateTimeField(null=True)
    blackscreen_since = DateTimeField(null=True)

    @classmethod
    def select(cls, *args, cascade: bool = False) -> ModelSelect:
        """Selects records."""
        if not cascade:
            return super().select(*args)

        dataset = Deployment.alias()
        args = {
            cls, System, Deployment, Customer, Company, Address, dataset,
            *args
        }
        return super().select(*args).join(System).join(
            Deployment, on=System.deployment == Deployment.id,
            join_type=JOIN.LEFT_OUTER
        ).join(
            Customer, join_type=JOIN.LEFT_OUTER
        ).join(
            Company, join_type=JOIN.LEFT_OUTER
        ).join_from(
            Deployment, Address, on=Deployment.address == Address.id,
            join_type=JOIN.LEFT_OUTER
        ).join_from(
            System, dataset, on=System.dataset == dataset.id,
            join_type=JOIN.LEFT_OUTER
        )

    @property
    def online(self) -> bool:
        """Determines whether the system is online."""
        return self.icmp_request and self.ssh_login

    @property
    def successful(self) -> bool:
        """Determines whether the check was considered successful."""
        if not self.icmp_request:
            return False

        return self.ssh_login == SuccessFailedUnsupported.SUCCESS
