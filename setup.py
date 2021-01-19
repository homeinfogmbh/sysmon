#! /usr/bin/env python3

from setuptools import setup

setup(
    name='sysmon',
    use_scm_version={
        "local_scheme": "node-and-timestamp"
    },
    setup_requires=['setuptools_scm'],
    install_requires=[
        'configlib',
        'emaillib',
        'flask',
        'functoolsplus',
        'his',
        'hwdb',
        'peewee',
        'peeweeplus',
        'requests',
        'setuptools',
        'simplejson',
        'termacls',
        'timelib',
        'wsgilib'
    ],
    author='HOMEINFO - Digitale Informationssysteme GmbH',
    author_email='<info at homeinfo dot de>',
    maintainer='Richard Neumann',
    maintainer_email='<r dot neumann at homeinfo priod de>',
    packages=['sysmon'],
    entry_points={
        'console_scripts': [
            'sysmon = sysmon.daemon:spawn',
            'sysmon-cleanup = sysmon.cleanup:main',
            'sysmon-notify = sysmon.notify:notify'
        ]
    },
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
    description='A systems monitoring system.'
)
