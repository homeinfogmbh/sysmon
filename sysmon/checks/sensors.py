"""System sensors checks."""

from typing import Any

from sysmon.enumerations import SuccessFailedUnsupported


__all__ = ['check_system_sensors']


def check_system_sensors(sysinfo: dict[str, Any]) -> SuccessFailedUnsupported:
    """Check whether all system sensor values are ok."""

    if (sensors := sysinfo.get('sensors')) is None:
        return SuccessFailedUnsupported.UNSUPPORTED

    for sensor, fields in sensors.items():
        for field, temps in fields.items():
            if field == 'Adapter':
                continue

            if not isinstance(temps, dict):
                continue

            current = max_ = crit = None

            for name, value in temps.items():
                if name.endswith('_input'):
                    current = value

                if name.endswith('_max'):
                    max_ = value

                if name.endswith('_crit'):
                    crit = value

                if name.endswith('_crit_alarm') and value:
                    return SuccessFailedUnsupported.FAILED

            if current is None:
                continue

            if crit is not None and current >= crit:
                return SuccessFailedUnsupported.FAILED

            if max_ is not None and current > max_:
                return SuccessFailedUnsupported.FAILED

    return SuccessFailedUnsupported.SUCCESS
