"""Systemd related checks."""

from subprocess import PIPE, CalledProcessError, check_call


__all__ = ['unit_status']


def unit_status(service: str) -> bool:
    """Determine the status of a systemd unit on the server."""

    try:
        check_call(
            ['/bin/systemctl', 'status', service, '--quiet'],
            stdout=PIPE,
            stderr=PIPE
        )
    except CalledProcessError:
        return False

    return True
