"""EFI related checks."""

from typing import Any

from sysmon.enumerations import SuccessFailedUnsupported


__all__ = ['efi_mount_ok']


def efi_mount_ok(sysinfo: dict[str, Any]) -> SuccessFailedUnsupported:
    """Returns True iff the EFI partition is mounted
    on /boot or there is no EFI partition to be mounted.
    """

    if (mounted := sysinfo.get('efi', {}).get('mounted')) is None:
        return SuccessFailedUnsupported.UNSUPPORTED

    if mounted:
        return SuccessFailedUnsupported.SUCCESS

    return SuccessFailedUnsupported.FAILED
