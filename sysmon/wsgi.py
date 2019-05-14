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

    if ACCOUNT.root:
        selection &= ~(System.deployment >> None)
        return System.select().where(selection)

    try:
        type_admin = TypeAdmin.get(TypeAdmin.customer == CUSTOMER.id)
    except TypeAdmin.DoesNotExist:
        return ()

    selection &= Deployment.type == type_admin.type
    return System.select().join(Deployment).where(selection)


def get_checks(system, *, begin=None, end=None):
    """Returns the checks for the respective system."""

    json = system.to_json(brief=True, cascade=True)


    for key, model in CHECKS.items():
        selection = model.system == system

        if begin:
            selection &= model.timestamp >= begin

        if end:
            selection &= model.timestamp <= end

        ordering = model.timestamp.desc()
        records = model.select().where(selection).order_by(ordering)
        json[key] = list(record.to_json() for record in records)

    return json


@APPLICATION.route('/', methods=['GET'])
@authenticated
def list_():
    """Lists all systems."""

    systems = request.headers.get('systems')

    if systems:
        systems = set(int(system) for system in systems.split(','))

    begin = strpdatetime(request.headers.get('begin'))
    end = strpdatetime(request.headers.get('end'))
    json = {
        str(system.id): get_checks(system, begin=begin, end=end)
        for system in get_systems()
    }
    return JSON(json)
