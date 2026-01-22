"""System checking."""

from datetime import datetime
from functools import partial
from json import dumps
from multiprocessing import Pool
from typing import Iterable, Optional
from requests import post

from hwdb import System

from sysmon.config import LOGGER
from sysmon.orm import CheckResults, NewestCheckResults

from sysmon.checks.application import get_application_state
from sysmon.checks.application import get_application_version
from sysmon.checks.baytrail import get_baytrail_freeze_state
from sysmon.checks.black_screen import get_blackscreen_since
from sysmon.checks.common import get_last_check, get_sysinfo, get_application
from sysmon.checks.efi import efi_mount_ok
from sysmon.checks.icmp import check_icmp_request
from sysmon.checks.iperf3 import measure_speed
from sysmon.checks.meminfo import get_ram_available
from sysmon.checks.meminfo import get_ram_free
from sysmon.checks.meminfo import get_ram_total
from sysmon.checks.offline import get_offline_since
from sysmon.checks.root_partition import check_root_not_ro
from sysmon.checks.sensors import check_system_sensors
from sysmon.checks.smart import get_smart_results
from sysmon.checks.ssh import check_ssh
from sysmon.checks.synchronization import is_in_sync
from sysmon.checks.touchscreen import count_recent_touch_events
from sysmon.config import get_config

from hwdb.enumerations import Connection

__all__ = ["check_system", "check_systems"]


TCP_TIMEOUT = 5  # seconds


def check_systems(systems: Iterable[System], *, chunk_size: int = 10) -> None:
    """Checks the given systems."""

    with Pool(processes=6) as pool:
        pool.map(partial(check_system, nobwiflte=True), systems, chunksize=chunk_size)


def check_system(system: System, nobwiflte: Optional[bool] = False) -> CheckResults:
    """Check the given system."""
    islte = False
    try:
        if nobwiflte and system.deployment.connection == Connection.LTE:
            LOGGER.info("Checking LTE ( no bandwith test system: %i", system.id)
            system_check = create_check(system, nobwiflte, islte)
            islte = True
        else:
            LOGGER.info("Checking system: %i", system.id)
            system_check = create_check(system)
    except AttributeError:
        LOGGER.info("Checking system: %i, no connection type found", system.id)
        system_check = create_check(system)

    system_check.save()

    # delete old check and add newest check to db
    NewestCheckResults.delete().where(
        NewestCheckResults.system == system_check.system
    ).execute()
    if islte:
        newest_check_results = NewestCheckResults(
            system=system_check.system,
            icmp_request=system_check.icmp_request,
            ssh_login=system_check.ssh_login,
            http_request=system_check.http_request,
            application_state=system_check.application_state,
            smart_check=system_check.smart_check,
            baytrail_freeze=system_check.baytrail_freeze,
            fsck_repair=system_check.fsck_repair,
            application_version=system_check.application_version,
            efi_mount_ok=system_check.efi_mount_ok,
            root_not_ro=system_check.root_not_ro,
            sensors=system_check.sensors,
            in_sync=system_check.in_sync,
            recent_touch_events=system_check.recent_touch_events,
            application_mode=system_check.application_mode,
        )
    else:
        newest_check_results = NewestCheckResults(
            system=system_check.system,
            icmp_request=system_check.icmp_request,
            ssh_login=system_check.ssh_login,
            http_request=system_check.http_request,
            application_state=system_check.application_state,
            smart_check=system_check.smart_check,
            baytrail_freeze=system_check.baytrail_freeze,
            fsck_repair=system_check.fsck_repair,
            application_version=system_check.application_version,
            efi_mount_ok=system_check.efi_mount_ok,
            download=system_check.download,
            upload=system_check.upload,
            root_not_ro=system_check.root_not_ro,
            sensors=system_check.sensors,
            in_sync=system_check.in_sync,
            recent_touch_events=system_check.recent_touch_events,
            application_mode=system_check.application_mode,
        )
    newest_check_results.offline_since = system_check.offline_since
    newest_check_results.save()

    try:
        post(
            get_config().get("smitrac", "url"),
            data=dumps(
                {
                    "customer": system_check.system.deployment.customer.id,
                    "system": system_check.system.id,
                    "password": get_config().get("smitrac", "apipassword"),
                }
            ),
        )
    except:
        print("error sending check to smitrac api system ", system_check.system.id)
    return system_check


def create_check(
    system: System, nobwiflte: Optional[bool] = False, islte: Optional[bool] = False
) -> CheckResults:
    """Checks a system."""

    now = datetime.now()
    try:
        http_request, sysinfo = get_sysinfo(system)
    except Exception as e:
        print(e)
    if system.ddb_os:
        if nobwiflte and islte:
            check_results = CheckResults(
                system=system,
                icmp_request=check_icmp_request(system, timeout=TCP_TIMEOUT),
                ssh_login=check_ssh(system, timeout=TCP_TIMEOUT),
                http_request=http_request,
                application_state=get_application_state(sysinfo),
                smart_check=get_smart_results(sysinfo),
                baytrail_freeze=get_baytrail_freeze_state(sysinfo),
                fsck_repair=sysinfo.get("cmdline", {}).get("fsck.repair"),
                application_version=get_application_version(sysinfo),
                efi_mount_ok=efi_mount_ok(sysinfo),
                root_not_ro=check_root_not_ro(sysinfo),
                sensors=check_system_sensors(sysinfo),
                in_sync=is_in_sync(system, now),
                recent_touch_events=count_recent_touch_events(system.deployment, now),
                application_mode=get_application(system),
            )
        else:
            check_results = CheckResults(
                system=system,
                icmp_request=check_icmp_request(system, timeout=TCP_TIMEOUT),
                ssh_login=check_ssh(system, timeout=TCP_TIMEOUT),
                http_request=http_request,
                application_state=get_application_state(sysinfo),
                smart_check=get_smart_results(sysinfo),
                baytrail_freeze=get_baytrail_freeze_state(sysinfo),
                fsck_repair=sysinfo.get("cmdline", {}).get("fsck.repair"),
                application_version=get_application_version(sysinfo),
                efi_mount_ok=efi_mount_ok(sysinfo),
                download=measure_speed(system),
                upload=measure_speed(system, reverse=True),
                root_not_ro=check_root_not_ro(sysinfo),
                sensors=check_system_sensors(sysinfo),
                in_sync=is_in_sync(system, now),
                recent_touch_events=count_recent_touch_events(system.deployment, now),
                application_mode=get_application(system),
            )
    else:
        if nobwiflte and islte:
            check_results = CheckResults(
                system=system,
                icmp_request=check_icmp_request(system, timeout=TCP_TIMEOUT),
                ssh_login=check_ssh(system, timeout=TCP_TIMEOUT),
                http_request=http_request,
                application_state=get_application_state(sysinfo),
                smart_check=get_smart_results(sysinfo),
                baytrail_freeze=get_baytrail_freeze_state(sysinfo),
                fsck_repair=sysinfo.get("cmdline", {}).get("fsck.repair"),
                application_version=get_application_version(sysinfo),
                ram_total=get_ram_total(sysinfo),
                ram_free=get_ram_free(sysinfo),
                ram_available=get_ram_available(sysinfo),
                efi_mount_ok=efi_mount_ok(sysinfo),
                root_not_ro=check_root_not_ro(sysinfo),
                sensors=check_system_sensors(sysinfo),
                recent_touch_events=count_recent_touch_events(system.deployment, now),
                application_mode=get_application(system),
            )
        else:
            check_results = CheckResults(
                system=system,
                icmp_request=check_icmp_request(system, timeout=TCP_TIMEOUT),
                ssh_login=check_ssh(system, timeout=TCP_TIMEOUT),
                http_request=http_request,
                application_state=get_application_state(sysinfo),
                smart_check=get_smart_results(sysinfo),
                baytrail_freeze=get_baytrail_freeze_state(sysinfo),
                fsck_repair=sysinfo.get("cmdline", {}).get("fsck.repair"),
                application_version=get_application_version(sysinfo),
                ram_total=get_ram_total(sysinfo),
                ram_free=get_ram_free(sysinfo),
                ram_available=get_ram_available(sysinfo),
                efi_mount_ok=efi_mount_ok(sysinfo),
                download=measure_speed(system),
                upload=measure_speed(system, reverse=True),
                root_not_ro=check_root_not_ro(sysinfo),
                sensors=check_system_sensors(sysinfo),
                recent_touch_events=count_recent_touch_events(system.deployment, now),
                application_mode=get_application(system),
            )

    try:
        last_check = get_last_check(system)
    except CheckResults.DoesNotExist:
        last_check = None

    check_results.offline_since = get_offline_since(check_results, last_check)
    check_results.blackscreen_since = get_blackscreen_since(check_results, last_check)
    return check_results
