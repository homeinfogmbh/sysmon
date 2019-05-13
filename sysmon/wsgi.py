"""Monitoring web interface."""

from his import ACCOUNT, CUSTOMER, authenticated, Application
from terminallib import Deployment, System
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


def get_checks(system):
    """Returns the checks for the respective system."""

    json = system.to_json(brief=True, cascade=True)

    for key, model in CHECKS.items():
        try:
            latest_check = model.select().where(
                model.system == system).order_by(
                    model.timestamp.desc()).limit(1).get()
        except model.DoesNotExist:
            check_json = None
        else:
            check_json = latest_check.to_json()

        json[key] = check_json

    return json


@APPLICATION.route('/', methods=['GET'])
@authenticated
def list_():
    """Lists all systems."""

    return JSON([get_checks(system) for system in get_systems()])
