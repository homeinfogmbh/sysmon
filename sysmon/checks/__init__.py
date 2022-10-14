"""System checking."""

from datetime import datetime
from multiprocessing import Pool
from typing import Iterable

from hwdb import System

from sysmon.config import LOGGER
from sysmon.orm import CheckResults

from sysmon.checks.application import get_application_state
from sysmon.checks.application import get_application_version
from sysmon.checks.baytrail import get_baytrail_freeze_state
from sysmon.checks.black_screen import get_blackscreen_since
from sysmon.checks.common import get_last_check, get_sysinfo
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


__all__ = ['check_system', 'check_systems']


TCP_TIMEOUT = 5     # seconds


def check_system(system: System) -> CheckResults:
    """Check the given system."""

    LOGGER.info('Checking system: %i', system.id)
    system_check = create_check(system)
    system_check.save()
    return system_check


def check_systems(systems: Iterable[System], *, chunk_size: int = 10) -> None:
    """Checks the given systems."""

    with Pool() as pool:
        pool.map(check_system, systems, chunksize=chunk_size)


def create_check(system: System) -> CheckResults:
    """Checks a system."""

    now = datetime.now()
    http_request, sysinfo = get_sysinfo(system)
    check_results = CheckResults(
        system=system,
        icmp_request=check_icmp_request(system, timeout=TCP_TIMEOUT),
        ssh_login=check_ssh(system, timeout=TCP_TIMEOUT),
        http_request=http_request,
        application_state=get_application_state(sysinfo),
        smart_check=get_smart_results(sysinfo),
        baytrail_freeze=get_baytrail_freeze_state(sysinfo),
        fsck_repair=sysinfo.get('cmdline', {}).get('fsck.repair'),
        application_version=get_application_version(sysinfo),
        ram_total=get_ram_total(sysinfo),
        ram_free=get_ram_free(sysinfo),
        ram_available=get_ram_available(sysinfo),
        efi_mount_ok=efi_mount_ok(sysinfo),
        download=measure_speed(system),
        upload=measure_speed(system, reverse=True),
        root_not_ro=check_root_not_ro(sysinfo),
        sensors=check_system_sensors(sysinfo),
        in_sync=is_in_sync(system, now),
        recent_touch_events=count_recent_touch_events(system.deployment, now)
    )

    try:
        last_check = get_last_check(system)
    except CheckResults.DoesNotExist:
        last_check = None

    check_results.offline_since = get_offline_since(check_results, last_check)
    check_results.blackscreen_since = get_blackscreen_since(
        check_results, last_check
    )
    return check_results
