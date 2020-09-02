#! /usr/bin/env python3

from distutils.core import setup

setup(
    name='sysmon',
    version='latest',
    author='HOMEINFO - Digitale Informationssysteme GmbH',
    author_email='<info at homeinfo dot de>',
    maintainer='Richard Neumann',
    maintainer_email='<r dot neumann at homeinfo priod de>',
    packages=['sysmon'],
    scripts=['files/sysmon', 'files/sysmon-cleanup', 'files/sysmon-notify'],
    data_files=[
        ('/usr/lib/systemd/system', [
            'files/sysmon.service',
            'files/sysmon-cleanup.service',
            'files/sysmon-cleanup.timer',
            'files/sysmon-notify.service',
            'files/sysmon-notify.timer'
        ])
    ],
    license='GPLv3',
    description='A systems monitoring system.')
