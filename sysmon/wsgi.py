"""Monitoring web interface."""

from flask import request

from functoolsplus import coerce
from his import ACCOUNT, authenticated, Application
from terminallib import Deployment, System
from timelib import strpdatetime
from wsgilib import JSON

from sysmon.orm import CHECKS, TypeAdmin, OnlineCheck


__all__ = ['APPLICATION']


APPLICATION = Application('sysmon')


@coerce(set)
def get_authorized_types():
    """Yields authorized types."""

    for admin in TypeAdmin.select().where(TypeAdmin.account == ACCOUNT.id):
        yield admin.type


def get_systems():
    """Yields the systems which the current user may monitor."""

    if ACCOUNT.root:
        return System.select().where(True)

    condition = Deployment.type << get_authorized_types()
    return System.select().join(Deployment).where(condition)


def get_system(system):
    """Returns a system by its ID."""

    if ACCOUNT.root:
        return System[system]

    condition = System.id == system
    condition &= Deployment.type << get_authorized_types()
    return System.select().join(Deployment).where(condition).get()


@coerce(set)
def get_customers():
    """Yields all allowed customers."""

    for system in get_systems():
        if system.deployment:
            yield system.deployment.customer


@coerce(set)
def get_types():
    """Yields all allowed types."""

    for system in get_systems():
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

    systems = get_systems()
    begin = strpdatetime(request.headers.get('begin'))
    end = strpdatetime(request.headers.get('end'))
    json = get_systems_checks(systems, begin=begin, end=end)
    return JSON(json)


@APPLICATION.route(
    '/details/<int:system>', methods=['GET'], strict_slashes=False)
@authenticated
def system_details(system):
    """Lists uptime details of a system."""

    try:
        system = get_system(system)
    except System.DoesNotExist:
        return ('No such system.', 404)

    online_checks = OnlineCheck.select().where(OnlineCheck.system == system)
    online_checks = online_checks.order_by(OnlineCheck.timestamp)
    return JSON([online_check.to_json() for online_check in online_checks])
