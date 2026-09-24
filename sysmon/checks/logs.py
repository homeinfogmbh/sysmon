"""Log collection via SSH."""

import re
from json import JSONDecodeError, loads
from subprocess import PIPE, CalledProcessError, TimeoutExpired, run
from typing import Optional

from hwdb import OperatingSystem, System

from sysmon.config import get_config


__all__ = ["get_error_log", "get_chromium_log", "get_smartctl_full", "parse_hd_uptime", "get_disk_usage"]


# Nur root - siehe die ausfuehrliche Begruendung in checks/ssh.py. Hier fiel der Fallback
# zusaetzlich immer dann an, wenn das Remote-Kommando selbst nicht sauber zurueckkam
# (Exitcode != 0 oder Timeout): dann lief der naechste Versuch als homeinfo und scheiterte
# an der Anmeldung, statt das eigentliche Problem zu zeigen.
SSH_USERS = ("root",)
SSH_CAPABLE_OSS = {OperatingSystem.ARCH_LINUX, OperatingSystem.ARCH_LINUX_ARM}
SSH_TIMEOUT = 10
CHROMIUM_LOG_PATH = "/home/digsig/.config/chromium/chrome_debug.log"
# Das Debug-Log kann sehr gross werden. Frueher wurde es komplett per cat ueber den Tunnel
# geholt: der Transfer lief dann in seinen Timeout und hat dabei die Leitung fuer den
# unmittelbar folgenden check_ssh() blockiert, der nur wenige Sekunden Budget hat. Ergebnis
# waren sporadische, falsche ssh_login=failed bei einwandfrei erreichbaren Systemen.
# Ausgewertet werden ohnehin nur die letzten max_lines Zeilen, deshalb wird nur noch das
# Ende der Datei uebertragen. Das Fenster ist bewusst klein gewaehlt - auf schmalbandigen
# Anbindungen kostet jedes zusaetzliche Megabyte spuerbar Zeit und holt den alten Effekt
# zurueck.
CHROMIUM_LOG_MAX_BYTES = 256 * 1024
CHROM_KERN_RE = re.compile(
    r"\bchrome\b|\bchromium\b|\brenderer\b|gpu.process",
    re.IGNORECASE,
)
CHROM_NOISE_RE = re.compile(r":VERBOSE\d+:|:INFO:|:WARNING:|org\.chromium\.")


def _ssh_command(system: System, user: str, remote_cmd: str) -> list[str]:
    return [
        "/usr/bin/ssh",
        "-i", get_config().get("ssh", "keyfile"),
        "-o", "LogLevel=error",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "StrictHostKeyChecking=no",
        "-o", f"ConnectTimeout={SSH_TIMEOUT}",
        f"{user}@{system.ip_address}",
        remote_cmd,
    ]


def _run_ssh(system: System, remote_cmd: str) -> Optional[str]:
    """Run a command on the system via SSH, return stdout or None on failure."""
    if system.operating_system not in SSH_CAPABLE_OSS:
        return None

    for user in SSH_USERS:
        try:
            result = run(
                _ssh_command(system, user, remote_cmd),
                check=True,
                stdout=PIPE,
                stderr=PIPE,
                text=True,
                timeout=SSH_TIMEOUT + 20,
            )
            return result.stdout
        except (CalledProcessError, TimeoutExpired):
            continue

    return None


def get_error_log(
    system: System, *, since: str = "4 days ago", max_lines: int = 150
) -> Optional[str]:
    """Fetch critical journald entries from the system via SSH."""
    output = _run_ssh(
        system,
        f"/usr/bin/journalctl --priority=crit --since '{since}' --no-pager -o short-iso",
    )
    if output is None:
        return None

    ignored = ("sshd", "hidslcfg", "watchdog")
    lines = [
        line.strip()
        for line in output.splitlines()
        if line.strip()
        and not line.strip().startswith("--")
        and not any(p in line for p in ignored)
    ]
    return "\n".join(lines[:max_lines]) or None


def get_chromium_log(
    system: System, *, max_lines: int = 150
) -> Optional[str]:
    """Fetch the tail of the Chromium debug log from the system via SSH."""
    # tail -c schneidet mitten in der Zeile, deshalb faellt die erste Zeile weg - aber nur,
    # wenn die Datei tatsaechlich groesser als das Fenster war.
    output = _run_ssh(
        system,
        f'if [ "$(stat -c %s {CHROMIUM_LOG_PATH} 2>/dev/null || echo 0)" '
        f'-gt {CHROMIUM_LOG_MAX_BYTES} ]; '
        f'then tail -c {CHROMIUM_LOG_MAX_BYTES} {CHROMIUM_LOG_PATH} 2>/dev/null | tail -n +2; '
        f'else cat {CHROMIUM_LOG_PATH} 2>/dev/null; fi',
    )
    if output is None:
        return None

    lines = [
        line for line in output.splitlines()
        if line.strip()
        and not CHROM_NOISE_RE.search(line)
        and CHROM_KERN_RE.search(line)
    ]
    return "\n".join(lines[-max_lines:]) or None


def get_smartctl_full(system: System) -> Optional[str]:
    """Fetch full smartctl output as JSON from the system via SSH."""
    output = _run_ssh(
        system,
        "/usr/bin/smartctl -a --json /dev/sda 2>/dev/null || /usr/bin/smartctl -a --json /dev/nvme0 2>/dev/null",
    )
    if output is None:
        return None
    return output.strip() or None


def parse_hd_uptime(smartctl_json: Optional[str]) -> Optional[int]:
    """Extract power-on hours from a smartctl JSON string."""
    if not smartctl_json:
        return None
    try:
        return loads(smartctl_json)["power_on_time"]["hours"]
    except (JSONDecodeError, ValueError, KeyError):
        return None


def get_disk_usage(system: System) -> tuple:
    """Return (total_mb, free_mb) of the root partition via SSH, or (None, None) on failure."""
    output = _run_ssh(system, "df -BM / | awk 'NR==2 {gsub(/M/,\"\",$2); gsub(/M/,\"\",$4); print $2, $4}'")
    if output is None:
        return None, None
    parts = output.strip().split()
    if len(parts) != 2:
        return None, None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None, None
