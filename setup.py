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
        'digsigdb',
        'emaillib',
        'flask',
        'functoolsplus',
        'his',
        'hwdb',
        'mdb',
        'notificationlib',
        'peewee',
        'peeweeplus',
        'previewlib',
        'requests',
        'setuptools',
        'termacls',
        'wsgilib'
    ],
    author='HOMEINFO - Digitale Informationssysteme GmbH',
    author_email='<info at homeinfo dot de>',
    maintainer='Richard Neumann',
    maintainer_email='<r dot neumann at homeinfo priod de>',
    packages=[
        'sysmon',
        'sysmon.checks'
    ],
    entry_points={
        'console_scripts': [
            'sysmon = sysmon.daemon:spawn',
            'sysmon-cleanup = sysmon.cleanup:main',
            'sysmon-notify = sysmon.notify:notify',
            'sysmon-generate-blacklist = sysmon.blacklist:generate_blacklist',
            'sysmon-send-mailing = sysmon.mailing:main'
        ]
    },
    data_files=[
        ('/usr/lib/systemd/system', [
            'files/sysmon.service',
            'files/sysmon.timer',
            'files/sysmon-cleanup.service',
            'files/sysmon-cleanup.timer',
            'files/sysmon-generate-blacklist.service',
            'files/sysmon-generate-blacklist.timer',
            'files/sysmon-mailing.service',
            'files/sysmon-mailing.timer'
        ])
    ],
    license='GPLv3',
    description='A systems monitoring system.'
)
