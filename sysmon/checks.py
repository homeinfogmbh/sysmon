"""System checking."""

from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from re import fullmatch
from subprocess import DEVNULL
from subprocess import PIPE
from subprocess import TimeoutExpired
from subprocess import CalledProcessError
from subprocess import check_call
from subprocess import run
from typing import Any, Iterable, Iterator, Optional, Sequence

from requests import ConnectionError, ReadTimeout, get

from hwdb import OperatingSystem, System

from sysmon.config import LOGGER, get_config
from sysmon.enumerations import ApplicationState
from sysmon.enumerations import BaytrailFreezeState
from sysmon.enumerations import SuccessFailedUnsupported
from sysmon.functions import get_url
from sysmon.iperf3 import iperf3
from sysmon.orm import CheckResults


__all__ = [
    'check_system',
    'check_systems',
    'get_sysinfo',
    'hipster_status',
    'current_application_version',
    'get_blacklist'
]


APPLICATION_AIR = r'application-air-(.+)-any\.pkg\.tar\.zst'
APPLICATION_HTML = r'application-html-(.+)-any\.pkg\.tar\.zst'
REPO_DIR = Path('/srv/http/de/homeinfo/mirror/prop/pacman')
SSH_USERS = {'root', 'homeinfo'}
SSH_CAPABLE_OSS = {
    OperatingSystem.ARCH_LINUX,
    OperatingSystem.ARCH_LINUX_ARM
}
IPERF_TIMEOUT = 15  # seconds
TCP_TIMEOUT = 5     # seconds


def check_system(system: System) -> CheckResults:
    """Checks a system."""

    http_request, sysinfo = get_sysinfo(system)
    check_results = CheckResults(
        system=system,
        icmp_request=check_icmp_request(system, timeout=TCP_TIMEOUT),
        ssh_login=check_ssh(system, timeout=TCP_TIMEOUT),
        http_request=http_request,
        application_state=get_application_state(sysinfo),
        smart_check=get_smart_results(sysinfo),
        baytrail_freeze=get_baytrail_freeze_state(sysinfo),
        application_version=get_application_version(sysinfo),
        ram_total=get_ram_total(sysinfo),
        ram_free=get_ram_free(sysinfo),
        ram_available=get_ram_available(sysinfo),
        efi_mount_ok=efi_mount_ok(sysinfo),
        download=measure_download_speed(system, timeout=IPERF_TIMEOUT),
        upload=measure_upload_speed(system, timeout=IPERF_TIMEOUT)
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

    try:
        response = get(get_url(system.ip_address, port=port), timeout=timeout)
    except (ConnectionError, ReadTimeout):
        return SuccessFailedUnsupported.UNSUPPORTED, {}

    if response.status_code != 200:
        return SuccessFailedUnsupported.FAILED, {}

    return SuccessFailedUnsupported.SUCCESS, response.json()


def check_icmp_request(system: System, timeout: Optional[int] = None) -> bool:
    """Pings the system."""

    try:
        system.ping(timeout=timeout)
    except (CalledProcessError, TimeoutExpired):
        return False

    return True


def check_ssh(
        system: System,
        timeout: Optional[int] = None
) -> SuccessFailedUnsupported:
    """Checks the SSH connection to the system."""

    if system.operating_system not in SSH_CAPABLE_OSS:
        return SuccessFailedUnsupported.UNSUPPORTED

    for user in SSH_USERS:
        if (
                check_ssh_login(system, user, timeout=timeout) is
                SuccessFailedUnsupported.SUCCESS
        ):
            return SuccessFailedUnsupported.SUCCESS

    return SuccessFailedUnsupported.FAILED


def check_ssh_login(
        system: System,
        user: str,
        *,
        timeout: int = 5
) -> SuccessFailedUnsupported:
    """Checks the SSH login on the system."""

    try:
        run(
            get_ssh_command(system, user=user, timeout=timeout), check=True,
            stdout=DEVNULL, stderr=PIPE, text=True, timeout=timeout+1
        )
    except CalledProcessError as error:
        LOGGER.error('SSH connection error: %s', error.stderr)
        return SuccessFailedUnsupported.FAILED
    except TimeoutExpired:
        return SuccessFailedUnsupported.FAILED

    return SuccessFailedUnsupported.SUCCESS


def get_ssh_command(
        system: System,
        *,
        user: str,
        timeout: int = 5
) -> list[str]:
    """Return a list of SSH command and parameters for subprocess.run()."""

    return [
        '/usr/bin/ssh',
        '-i', get_config().get('ssh', 'keyfile'),
        '-o', 'LogLevel=error',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-o', 'StrictHostKeyChecking=no',
        '-o', f'ConnectTimeout={timeout}',
        f'{user}@{system.ip_address}',
        '/usr/bin/true'
    ]


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


def measure_download_speed(
        system: System,
        timeout: Optional[int] = None
) -> Optional[int]:
    """Measure the download speed of the system in kbps."""

    try:
        result = iperf3(system.ip_address, timeout=timeout)
    except (CalledProcessError, TimeoutExpired):
        return None

    return round(result.receiver.to_kbps().value)


def measure_upload_speed(
        system: System,
        timeout: Optional[int] = None
) -> Optional[int]:
    """Measure the upload speed of the system in kbps."""

    try:
        result = iperf3(system.ip_address, reverse=True, timeout=timeout)
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


def current_application_version(typ: str) -> Optional[str]:
    """Returns the current application version in the repo."""

    if typ == 'html':
        return extract_package_version(APPLICATION_HTML)

    if typ == 'air':
        return extract_package_version(APPLICATION_AIR)

    return None


def extract_package_version(regex: str) -> str:
    """Extracts the package version."""

    for file in REPO_DIR.iterdir():
        if match := fullmatch(regex, file.name):
            return match.group(1)

    raise ValueError('Could not determine any package version.')


def offline_percent(check_results: Sequence[CheckResults]) -> float:
    """Return the percentage the system was offline within the given checks."""

    return len(
        list(filter(lambda check: not check.online, check_results))
    ) / len(check_results)


def get_blacklist(
        *,
        retention: timedelta = timedelta(days=90),
        threshold: float = 0.8
) -> Iterator[System]:
    """Determine whether the given system is blacklisted."""

    check_results = CheckResults.select(cascade=True).where(
        CheckResults.timestamp > datetime.now() - retention
    )
    system_check_results = defaultdict(list)

    for check_result in check_results:
        system_check_results[check_result.system].append(check_result)

    for system, check_results in system_check_results.items():
        if is_blacklisted(check_results, threshold=threshold):
            yield system


def is_blacklisted(
        check_results: Sequence[CheckResults],
        *,
        threshold: float = 0.8
) -> bool:
    """Determine whether the given system is blacklisted."""

    total = len(check_results)
    return all(
        percentage > threshold for percentage in (
            len(list(filter(
                lambda check: not check.online, check_results
            ))) / total,
            len(list(filter(
                lambda check: check.low_bandwidth(), check_results
            ))) / total
        )
    )
