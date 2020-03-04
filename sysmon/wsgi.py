"""Monitoring web interface."""

from datetime import timedelta

from flask import request

from functoolsplus import coerce
from his import ACCOUNT, authenticated, Application
from termacls import get_administerable_systems
from terminallib import System
from timelib import strpdatetime
from wsgilib import JSON

from sysmon.orm import CHECKS, OnlineCheck


__all__ = ['APPLICATION']


APPLICATION = Application('sysmon')


def get_system(system):
    """Returns a system by its ID."""

    if ACCOUNT.root:
        return System[system]

    systems = get_administerable_systems(ACCOUNT)
    return systems.select().where(System.id == system).get()


@coerce(set)
def get_customers():
    """Yields all allowed customers."""

    for system in get_administerable_systems(ACCOUNT):
        if system.deployment:
            yield system.deployment.customer


@coerce(set)
def get_types():
    """Yields all allowed types."""

    for system in get_administerable_systems(ACCOUNT):
        if system.deployment:
            yield system.deployment.type


def get_stats(system, *, begin=None, end=None):
    """Returns the checks for the respective system."""

    json = {}

    for model in CHECKS:
        selection = model.system == system

        if begin:
            selection &= model.timestamp >= begin

        if end:
            selection &= model.timestamp <= end

        ordering = model.timestamp.desc()
        query = model.select().where(selection).order_by(ordering)

        try:
            latest = query.limit(1).get()
        except model.DoesNotExist:
            continue

        json[model.__name__] = latest.to_json()

    return json


@coerce(list)
def get_systems_checks(systems, *, begin=None, end=None):
    """Yields JSON objects with system information and checks data."""

    for system in systems:
        json = system.to_json(brief=True, cascade=3)
        json['checks'] = get_stats(system, begin=begin, end=end)
        yield json


@APPLICATION.route('/stats', methods=['GET'], strict_slashes=False)
@authenticated
def list_stats():
    """Lists systems and their stats."""

    systems = get_administerable_systems(ACCOUNT)
    begin = strpdatetime(request.headers.get('begin'))
    end = strpdatetime(request.headers.get('end'))
    json = get_systems_checks(systems, begin=begin, end=end)
    return JSON(json)


@APPLICATION.route('/details/<int:system>', methods=['GET'],
                   strict_slashes=False)
@authenticated
def system_details(system):
    """Lists uptime details of a system."""

    try:
        system = get_system(system)
    except System.DoesNotExist:
        return ('No such system.', 404)

    select = OnlineCheck.system == system
    start = strpdatetime(request.headers.get('from'))
    end = strpdatetime(request.headers.get('until'))

    if start:
        select &= OnlineCheck.timestamp >= start

    if end:
        end += timedelta(days=1)    # Compensate for rest of day.
        select &= OnlineCheck.timestamp <= end

    online_checks = OnlineCheck.select().where(select)
    online_checks = online_checks.order_by(OnlineCheck.timestamp)
    return JSON([online_check.to_json() for online_check in online_checks])


@APPLICATION.route('/check/<int:system>', methods=['GET'],
                   strict_slashes=False)
@authenticated
def check_system(system):
    """Performs a system check."""

    try:
        system = get_system(system)
    except System.DoesNotExist:
        return ('No such system.', 404)

    online_check = OnlineCheck.run(system)
    return JSON(online_check.to_json())
