"""Monitoring web interface."""

from flask import request

from his import ACCOUNT, CUSTOMER, authenticated, Application
from terminallib import Deployment, System
from timelib import strpdatetime
from wsgilib import JSON

from sysmon.orm import ApplicationCheck, OnlineCheck, TypeAdmin


__all__ = ['APPLICATION']


APPLICATION = Application('sysmon')
CHECKS = {
    'online': OnlineCheck,
    'applicationStatus': ApplicationCheck
}


def get_systems(systems=None):
    """Yields the systems which the current user may monitor."""

    selection = True

    if systems is not None:
        selection &= System.id << systems

    selection &= ~(System.deployment >> None)

    if ACCOUNT.root:
        return System.select().where(selection)

    try:
        type_admin = TypeAdmin.get(TypeAdmin.customer == CUSTOMER.id)
    except TypeAdmin.DoesNotExist:
        return ()

    selection &= Deployment.type == type_admin.type
    return System.select().join(Deployment).where(selection)


def get_checks(system, *, begin=None, end=None):
    """Returns the checks for the respective system."""

    json = {}

    for key, model in CHECKS.items():
        selection = model.system == system

        if begin:
            selection &= model.timestamp >= begin

        if end:
            selection &= model.timestamp <= end

        ordering = model.timestamp.desc()
        models = model.select().where(selection).order_by(ordering)
        json[key] = [model.to_json() for model in models]

    return json


def get_systems_checks(systems, *, begin=None, end=None):
    """Yields JSON objects with system information and checks data."""

    for system in systems:
        json = system.to_json(brief=True, cascade=3)
        json['checks'] = get_checks(system, begin=begin, end=end)
        yield json


@APPLICATION.route('/', methods=['GET'], strict_slashes=False)
@authenticated
def list_():
    """Lists all systems."""

    systems = request.headers.get('systems')

    if systems:
        systems = set(int(system) for system in systems.split(','))

    systems = get_systems(systems=systems)
    begin = strpdatetime(request.headers.get('begin'))
    end = strpdatetime(request.headers.get('end'))
    json = list(get_systems_checks(systems, begin=begin, end=end))
    return JSON(json)
