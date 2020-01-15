"""Monitoring web interface."""

from flask import request

from functoolsplus import coerce
from his import ACCOUNT, authenticated, Application
from terminallib import Deployment, System, Type
from timelib import strpdatetime
from wsgilib import Error, JSON

from sysmon.orm import CHECKS, TypeAdmin


__all__ = ['APPLICATION']


APPLICATION = Application('sysmon')


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

    type_admins = TypeAdmin.select().where(TypeAdmin.account == ACCOUNT.id)
    authorized_types = {type_admin.type for type_admin in type_admins}
    condition &= Deployment.type << authorized_types
    return System.select().join(Deployment).where(condition)


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


@APPLICATION.route('/stats', methods=['GET'], strict_slashes=False)
@authenticated
def list_stats():
    """Lists systems and their stats."""

    systems = get_systems(
        systems=selected_systems(), customers=selected_customers(),
        types=selected_types())
    begin = strpdatetime(request.headers.get('begin'))
    end = strpdatetime(request.headers.get('end'))
    json = get_systems_checks(systems, begin=begin, end=end)
    return JSON(json)


@APPLICATION.route('/customers', methods=['GET'], strict_slashes=False)
@authenticated
def list_customers():
    """Lists all customers."""

    json = [customer.to_json(cascade=2) for customer in get_customers()]
    return JSON(json)


@APPLICATION.route('/types', methods=['GET'], strict_slashes=False)
@authenticated
def list_types():
    """Lists all types."""

    json = [type.value for type in get_types()]
    return JSON(json)
