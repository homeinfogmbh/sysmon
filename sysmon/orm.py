"""ORM models."""

from __future__ import annotations
from datetime import date, datetime
from typing import Any

from peewee import JOIN
from peewee import BooleanField
from peewee import CharField
from peewee import DateField
from peewee import DateTimeField
from peewee import ForeignKeyField
from peewee import IntegerField
from peewee import ModelSelect

from hwdb import Deployment, System
from mdb import Address, Company, Customer
from peeweeplus import EnumField, JSONModel, MySQLDatabaseProxy

from sysmon.config import MIN_BANDWIDTH
from sysmon.enumerations import ApplicationState
from sysmon.enumerations import BaytrailFreezeState
from sysmon.enumerations import SuccessFailedUnsupported


__all__ = ['DATABASE', 'SysmonModel', 'CheckResults', 'OfflineHistory']


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
    fsck_repair = CharField(3, null=True)
    application_version = CharField(12, null=True)
    ram_total = IntegerField(null=True)
    ram_free = IntegerField(null=True)
    ram_available = IntegerField(null=True)
    efi_mount_ok = EnumField(SuccessFailedUnsupported)
    download = IntegerField(null=True)      # kbps
    upload = IntegerField(null=True)        # kbps
    root_not_ro = EnumField(SuccessFailedUnsupported)
    sensors = EnumField(SuccessFailedUnsupported)
    in_sync = BooleanField(null=True)
    recent_touch_events = IntegerField(null=True)
    # Failed-since timestamps
    offline_since = DateTimeField(null=True)
    blackscreen_since = DateTimeField(null=True)

    @classmethod
    def select(cls, *args, cascade: bool = False) -> ModelSelect:
        """Selects records."""
        if not cascade:
            return super().select(*args)

        lpt_address = Address.alias()
        return super().select(
            cls, System, Deployment, Customer, Company, Address, lpt_address,
            *args
        ).join(System).join(
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
            Deployment, lpt_address,
            on=Deployment.lpt_address == lpt_address.id,
            join_type=JOIN.LEFT_OUTER
        )

    @property
    def online(self) -> bool:
        """Determines whether the system is online."""
        return (
            self.icmp_request
            and self.ssh_login is not SuccessFailedUnsupported.FAILED
        )

    def low_bandwidth(self, required: int = MIN_BANDWIDTH) -> bool:
        """Determine whether the system has a low bandwidth."""
        if self.download is None:
            return True

        return self.download < required

    def to_json(self, *args, **kwargs) -> dict[str, Any]:
        """Return a JSON-ish dict."""
        json = super().to_json(*args, **kwargs)
        json['online'] = self.online
        return json


class OfflineHistory(SysmonModel):
    """History entries for offline systems."""

    group = IntegerField()
    timestamp = DateField()
    offline = IntegerField()

    @classmethod
    def create_or_update(cls, group: int, timestamp: date) -> OfflineHistory:
        """Creates or updates the record for the given group and date."""
        try:
            return cls.get((cls.group == group) & (cls.timestamp == timestamp))
        except cls.DoesNotExist:
            return cls(group=group, timestamp=timestamp)

    @classmethod
    def since(cls, timestamp: date) -> ModelSelect:
        """Selects entries for the given period of time."""
        return cls.select().where(cls.timestamp >= timestamp)
