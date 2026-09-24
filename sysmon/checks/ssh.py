"""SSH checks."""

from subprocess import PIPE
from subprocess import TimeoutExpired
from subprocess import CalledProcessError
from subprocess import run

from hwdb import OperatingSystem, System

from sysmon.config import get_config
from sysmon.enumerations import SuccessFailedUnsupported


__all__ = ["check_ssh"]


# Nur root. Der frueher zusaetzlich probierte User "homeinfo" existiert zwar auf den
# Terminals, hat dort aber keine authorized_keys - jeder Versuch war damit eine garantierte
# Fehlanmeldung. Das kostete Zeit in jedem Check, verrauschte die Journale der Terminals
# und war vor allem eine Falle: OpenSSH 9.9 hat PerSourcePenalties per Default an
# (authfail:5 ... min:15). Ab wenigen Fehlanmeldungen kurz hintereinander weist das Terminal
# die Quelladresse fuer alles ab - auch fuer root und auch fuer einen Login von Hand.
# Vor dem Entfernen flottenweit geprueft: die Terminals antworten als root, und die wenigen
# mit hinterlegtem homeinfo-Key sind ebenfalls als root erreichbar. Der Fallback konnte
# also nie einen Check retten.
# Nebenbei war SSH_USERS ein set: die Iterationsreihenfolge haengt am Hash-Seed des
# Prozesses, homeinfo kam mal vor und mal nach root dran.
SSH_USERS = ("root",)
SSH_CAPABLE_OSS = {OperatingSystem.ARCH_LINUX, OperatingSystem.ARCH_LINUX_ARM}


def check_ssh(system: System, timeout: int) -> SuccessFailedUnsupported:
    """Checks the SSH connection to the system."""

    if system.operating_system not in SSH_CAPABLE_OSS:
        return SuccessFailedUnsupported.UNSUPPORTED

    for user in SSH_USERS:
        if (
            check_ssh_login(system, user, timeout=timeout)
            is SuccessFailedUnsupported.SUCCESS
        ):
            return SuccessFailedUnsupported.SUCCESS

    return SuccessFailedUnsupported.FAILED


def check_ssh_login(
    system: System, user: str, *, timeout: int = 5
) -> SuccessFailedUnsupported:
    """Checks the SSH login on the system."""

    try:
        run(
            get_ssh_command(system, user=user, timeout=timeout),
            check=True,
            stdout=PIPE,
            stderr=PIPE,
            text=True,
            timeout=timeout + 1,
        )
    except CalledProcessError:
        return SuccessFailedUnsupported.FAILED
    except TimeoutExpired:
        return SuccessFailedUnsupported.FAILED

    return SuccessFailedUnsupported.SUCCESS


def get_ssh_command(system: System, *, user: str, timeout: int = 5) -> list[str]:
    """Return a list of SSH command and parameters for subprocess.run()."""

    return [
        "/usr/bin/ssh",
        "-i",
        get_config().get("ssh", "keyfile"),
        "-o",
        "LogLevel=error",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        f"ConnectTimeout={timeout}",
        f"{user}@{system.ip_address}",
        "/usr/bin/true",
    ]
