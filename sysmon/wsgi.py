"""Monitoring web interface."""

from flask import request

from functoolsplus import coerce
from his import ACCOUNT, CUSTOMER, authenticated, Application
from terminallib import Deployment, System, Type
from timelib import strpdatetime
from wsgilib import Error, JSON

from sysmon.orm import ApplicationCheck, OnlineCheck, TypeAdmin


__all__ = ['APPLICATION']


APPLICATION = Application('sysmon')
CHECKS = {
    'online': OnlineCheck,
    'applicationStatus': ApplicationCheck
}


def get_systems(*, systems=None, customers=None, types=None):
    """Yields the systems which the current user may monitor."""

    condition = True

    if systems:
        condition &= System.id << systems

    if customers:
        condition &= Deployment.customer << customers

    if types:
        condition &= Deployment.type << types

    if ACCOUNT.root:
        return System.select().where(condition)

    try:
        type_admins = TypeAdmin.select().where(
            TypeAdmin.customer == CUSTOMER.id)
    except TypeAdmin.DoesNotExist:
        return ()

    authorized_types = set(type_admin.type for type_admin in type_admins)
    condition &= Deployment.type << authorized_types
    return System.select().join(Deployment).where(condition)


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


@coerce(set)
def selected_customers():
    """Yields the selected customers."""

    customers = request.headers.get('customers')

    if customers:
        for customer in customers.split(','):
            try:
                yield int(customer)
            except ValueError:
                raise Error('Invalid customer ID: "%s".' % customer)


@coerce(set)
def selected_types():
    """Yields the selected types."""

    types = request.headers.get('types')

    if types:
        for type_ in types.split(','):
            try:
                yield Type(type_)
            except ValueError:
                raise Error('Invalid system type: "%s".' % type_)


@coerce(set)
def selected_systems():
    """Yields the selected systems."""

    systems = request.headers.get('systems')

    if systems:
        for system in systems.split(','):
            try:
                yield int(system)
            except ValueError:
                raise Error('Invalid system ID: "%s".' % system)


@APPLICATION.route('/', methods=['GET'], strict_slashes=False)
@authenticated
def list_():
    """Lists all systems."""

    systems = get_systems(
        systems=selected_systems(), customers=selected_customers(),
        types=selected_types())
    begin = strpdatetime(request.headers.get('begin'))
    end = strpdatetime(request.headers.get('end'))
    json = list(get_systems_checks(systems, begin=begin, end=end))
    return JSON(json)
