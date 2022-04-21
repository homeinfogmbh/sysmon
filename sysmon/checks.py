"""System checking."""

from datetime import datetime
from ipaddress import IPv6Address
from subprocess import CalledProcessError, run
from typing import Any, Iterable, Optional

from requests import ConnectTimeout, get

from hwdb import SystemOffline, System

from sysmon.enumerations import ApplicationState
from sysmon.enumerations import BaytrailFreezeState
from sysmon.enumerations import SuccessFailedUnsupported
from sysmon.orm import CheckResults


KEYFILE = '/usr/share/terminals/terminals'
SSH_USER = 'homeinfo'


__all__ = ['check_system', 'check_systems']


def check_system(system: System) -> CheckResults:
    """Checks a system."""

    http_request, sysinfo = get_sysinfo(system)
    check_results = CheckResults(
        system=system,
        icmp_request=check_icmp_request(system),
        ssh_login=check_ssh_login(system),
        root_login=check_root_login(system),
        http_request=http_request,
        application_state=get_application_state(system),
        smart_check=get_smart_results(sysinfo),
        baytrail_freeze=get_baytrail_freeze_state(sysinfo),
        application_version='unknown',      # TODO: implement
        ram_total=get_ram_total(sysinfo),
        ram_free=get_ram_free(sysinfo),
        ram_availablee=get_ram_available(sysinfo)
    )

    try:
        last_check = get_last_check(system)
    except CheckResults.DoesNotExist:
        last_check = None

    check_results.offline_since = get_offline_since(check_results, last_check)
    check_results.save()
    return check_results


def check_systems(systems: Iterable[System]) -> None:
    """Checks the given systems."""

    for system in systems:
        check_system(system)


def get_sysinfo(
        system: System,
        *,
        port: int = 8000,
        timeout: int = 15
) -> tuple[SuccessFailedUnsupported, dict[str, Any]]:
    """Returns the system info dict per HTTP request."""

    if isinstance(ip_address := system.ip_address, IPv6Address):
        socket = f'[{ip_address}]:{port}'
    else:
        socket = f'{ip_address}:{port}'

    try:
        response = get(f'http://{socket}', timeout=timeout)
    except ConnectTimeout:
        return SuccessFailedUnsupported.UNSUPPORTED, {}

    if response.status_code != 200:
        return SuccessFailedUnsupported.FAILED, {}

    return SuccessFailedUnsupported.SUCCESS, response.json()


def check_icmp_request(system: System) -> bool:
    """Pings the system."""

    try:
        system.ping()
    except CalledProcessError:
        return False

    return True


def check_ssh_login(
        system: System,
        *,
        keyfile: str = KEYFILE,
        timeout: int = 5,
        user: str = SSH_USER
) -> SuccessFailedUnsupported:
    """Checks the SSH login on the system."""

    try:
        run([
            '/usr/bin/ssh',
            '-e', keyfile,
            '-o', 'LogLevel=error',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'StrictHostKeyChecking=no',
            '-o', f'ConnectTimeout={timeout}',
            f'{user}@{system.ip_address}',
            '/usr/bin/true'
        ])
    except CalledProcessError as error:
        if error.returncode == 255:
            return SuccessFailedUnsupported.UNSUPPORTED

        return SuccessFailedUnsupported.FAILED

    return SuccessFailedUnsupported.SUCCESS


def check_root_login(system: System) -> SuccessFailedUnsupported:
    """Checks root login via SSH."""

    return check_ssh_login(system, user='root')


def get_application_state(system: System) -> ApplicationState:
    """Checks whether the application is running."""

    try:
        response = system.application()
    except SystemOffline:
        return ApplicationState.UNKNOWN

    if response.status_code != 200:
        return ApplicationState.UNKNOWN

    if not (running := (json := response.json()).get('running')):
        return ApplicationState.NOT_RUNNING

    if not (enabled := json.get('enabled')):
        return ApplicationState.NOT_ENABLED

    if running != enabled:
        return ApplicationState.CONFLICT

    if len(running) != 1 or len(enabled) != 1:
        return ApplicationState.CONFLICT

    if running[0] == 'air':
        return ApplicationState.AIR

    if running[0] == 'html':
        return ApplicationState.HTML


def get_smart_results(sysinfo: dict[str, Any]) -> SuccessFailedUnsupported:
    """Returns the SMART test results."""

    if not (results := sysinfo.get('smartctl')):
        return SuccessFailedUnsupported.UNSUPPORTED

    if any(result != 'PASSED' for result in results.values()):
        return SuccessFailedUnsupported.FAILED

    return SuccessFailedUnsupported.SUCCESS


def get_baytrail_freeze_state(sysinfo: dict[str, Any]) -> BaytrailFreezeState:
    """Returns the baytrail freeze bug state."""

    if (baytrail := sysinfo.get('baytrail')) is None:
        return BaytrailFreezeState.UNKNOWN

    if not baytrail:
        return BaytrailFreezeState.NOT_AFFECTED

    if not (cmdline := sysinfo.get('cmdline')):
        return BaytrailFreezeState.UNKNOWN

    if cmdline.get('intel_idle.max_cstate') == '1':
        return BaytrailFreezeState.MITIGATED

    return BaytrailFreezeState.VULNERABLE


def get_ram_total(sysinfo: dict[str, Any]) -> Optional[int]:
    """Returns the total memory in kilobytes."""

    return sysinfo.get('meminfo', {}).get('MemTotal', {}).get('value')


def get_ram_free(sysinfo: dict[str, Any]) -> Optional[int]:
    """Returns the free memory in kilobytes."""

    return sysinfo.get('meminfo', {}).get('MemFree', {}).get('value')


def get_ram_available(sysinfo: dict[str, Any]) -> Optional[int]:
    """Returns the available memory in kilobytes."""

    return sysinfo.get('meminfo', {}).get('MemAvailable', {}).get('value')


def get_last_check(system: System) -> CheckResults:
    """Returns the last check of the given system."""

    return CheckResults.select().where(
        CheckResults.system == system
    ).order_by(
        CheckResults.timestamp.desc()
    ).get()


def get_offline_since(
        current: CheckResults,
        last: Optional[CheckResults]
) -> Optional[datetime]:
    """Returns the datetime since when the check is considered offline."""

    if current.online:
        return None

    if last is None or last.offline_since is None:
        return datetime.now()

    return last.offline_since
