"""System checking."""

from datetime import datetime
from ipaddress import IPv6Address
from subprocess import DEVNULL
from subprocess import PIPE
from subprocess import TimeoutExpired
from subprocess import CalledProcessError
from subprocess import check_call
from subprocess import run
from typing import Any, Iterable, Optional

from requests import ConnectionError, ReadTimeout, get

from hwdb import OperatingSystem, System

from sysmon.config import LOGGER, get_config
from sysmon.enumerations import ApplicationState
from sysmon.enumerations import BaytrailFreezeState
from sysmon.enumerations import SuccessFailedUnsupported
from sysmon.iperf3 import iperf3
from sysmon.orm import CheckResults


SSH_USERS = {'root', 'homeinfo'}
SSH_CAPABLE_OSS = {
    OperatingSystem.ARCH_LINUX,
    OperatingSystem.ARCH_LINUX_ARM
}


__all__ = ['check_system', 'check_systems', 'hipster_status']


def check_system(system: System) -> CheckResults:
    """Checks a system."""

    http_request, sysinfo = get_sysinfo(system)
    check_results = CheckResults(
        system=system,
        icmp_request=check_icmp_request(system),
        ssh_login=check_ssh(system),
        http_request=http_request,
        application_state=get_application_state(sysinfo),
        smart_check=get_smart_results(sysinfo),
        baytrail_freeze=get_baytrail_freeze_state(sysinfo),
        application_version=get_application_version(sysinfo),
        ram_total=get_ram_total(sysinfo),
        ram_free=get_ram_free(sysinfo),
        ram_available=get_ram_available(sysinfo),
        efi_mount_ok=efi_mount_ok(sysinfo),
        download=measure_download_speed(system),
        upload=measure_upload_speed(system)
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


def check_systems(systems: Iterable[System]) -> None:
    """Checks the given systems."""

    for system in systems:
        LOGGER.info('Checking system: %i', system.id)
        system_check = check_system(system)
        system_check.save()


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
    except (ConnectionError, ReadTimeout):
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


def check_ssh(system: System) -> SuccessFailedUnsupported:
    """Checks the SSH connection to the system."""

    if system.operating_system not in SSH_CAPABLE_OSS:
        return SuccessFailedUnsupported.UNSUPPORTED

    for user in SSH_USERS:
        if check_ssh_login(system, user) is SuccessFailedUnsupported.SUCCESS:
            return SuccessFailedUnsupported.SUCCESS

    return SuccessFailedUnsupported.FAILED


def check_ssh_login(
        system: System,
        user: str,
        *,
        timeout: int = 5
) -> SuccessFailedUnsupported:
    """Checks the SSH login on the system."""

    command = [
        '/usr/bin/ssh',
        '-i', get_config().get('ssh', 'keyfile'),
        '-o', 'LogLevel=error',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-o', 'StrictHostKeyChecking=no',
        '-o', f'ConnectTimeout={timeout}',
        f'{user}@{system.ip_address}',
        '/usr/bin/true'
    ]

    try:
        run(
            command, check=True, stdout=DEVNULL, stderr=PIPE, text=True,
            timeout=timeout+1
        )
    except CalledProcessError as error:
        LOGGER.error('SSH connection error: %s', error.stderr)
        return SuccessFailedUnsupported.FAILED
    except TimeoutExpired:
        return SuccessFailedUnsupported.FAILED

    return SuccessFailedUnsupported.SUCCESS


def get_application_state(sysinfo: dict[str, Any]) -> ApplicationState:
    """Checks whether the application is running."""

    if (status := sysinfo.get('application', {}).get('status')) is None:
        return ApplicationState.UNKNOWN

    if not (running := status.get('running')):
        return ApplicationState.NOT_RUNNING

    if not (enabled := status.get('enabled')):
        return ApplicationState.NOT_ENABLED

    if running != enabled:
        return ApplicationState.CONFLICT

    if len(running) != 1 or len(enabled) != 1:
        return ApplicationState.CONFLICT

    if running[0] == 'air':
        return ApplicationState.AIR

    if running[0] == 'html':
        return ApplicationState.HTML

    return ApplicationState.UNKNOWN


def get_application_version(sysinfo: dict[str, Any]) -> Optional[str]:
    """Returns the application version string."""

    return sysinfo.get('application', {}).get('version')


def get_smart_results(sysinfo: dict[str, Any]) -> SuccessFailedUnsupported:
    """Returns the SMART test results."""

    if not (results := sysinfo.get('smartctl')):
        return SuccessFailedUnsupported.UNSUPPORTED

    if all(result == 'PASSED' for result in results.values()):
        return SuccessFailedUnsupported.SUCCESS

    return SuccessFailedUnsupported.FAILED


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


def get_blackscreen_since(
        current: CheckResults,
        last: Optional[CheckResults]
) -> Optional[datetime]:
    """Returns the datetime since when the application is not running."""

    if current.application_state is not ApplicationState.NOT_RUNNING:
        return None

    if last is None or last.blackscreen_since is None:
        return datetime.now()

    return last.blackscreen_since


def efi_mount_ok(sysinfo: dict[str, Any]) -> SuccessFailedUnsupported:
    """Returns True iff the EFI partition is mounted
    on /boot or there is no EFI partition to be mounted.
    """

    if (mounted := sysinfo.get('efi', {}).get('mounted')) is None:
        return SuccessFailedUnsupported.UNSUPPORTED

    if mounted:
        return SuccessFailedUnsupported.SUCCESS

    return SuccessFailedUnsupported.FAILED


def measure_download_speed(system: System) -> Optional[int]:
    """Measure the download speed of the system in kbps."""

    try:
        result = iperf3(system.ip_address)
    except (CalledProcessError, TimeoutExpired):
        return None

    return round(result.receiver.to_kbps().value)


def measure_upload_speed(system: System) -> Optional[int]:
    """Measure the upload speed of the system in kbps."""

    try:
        result = iperf3(system.ip_address, reverse=True)
    except (CalledProcessError, TimeoutExpired):
        return None

    return round(result.receiver.to_kbps().value)


def hipster_status() -> bool:
    """Determine the status of the HIPSTER daemon on the server."""

    try:
        check_call(['/bin/systemctl', 'status', 'hipster.service', '--quiet'])
    except CalledProcessError:
        return False

    return True
