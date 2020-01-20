/*
    dom.js - Systems monitoring DOM library.

    (C) 2019 HOMEINFO - Digitale Informationssysteme GmbH

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Maintainer: Richard Neumann <r dot neumann at homeinfo period de>
*/
'use strict';


var sysmon = sysmon || {};


/*
    Converts true, false and null into a string.
*/
sysmon.boolNaToString = function (boolean) {
    if (boolean == null) {
        return '?';
    }

    if (boolean) {
        return '✓';
    }

    return '✗';
};


/*
    Generates a terminal DOM entry.
*/
sysmon.systemCheckToDOM = function (systemCheck) {
    if (systemCheck.checks == null) {
        return null;
    }

    const deployment = systemCheck.deployment;
    let address = 'Keine Adresse';
    let customer = 'Kein Kunde';

    if (deployment != null) {
        address = sysmon.addressToString(deployment.address);
        customer = deployment.customer.company.name + ' (' + deployment.customer.id + ')';
    }

    const tableRow = document.createElement('tr');
    tableRow.setAttribute('onclick', 'sysmon.showSystemDetails(' + systemCheck.id + ');');
    tableRow.style.cursor = 'pointer';
    const columnSystem = document.createElement('td');
    columnSystem.textContent = '' + systemCheck.id;
    tableRow.appendChild(columnSystem);
    const columnAddress = document.createElement('td');
    columnAddress.textContent = address;
    tableRow.appendChild(columnAddress);
    const columnCustomer = document.createElement('td');
    columnCustomer.textContent = customer;
    tableRow.appendChild(columnCustomer);
    const columnLastSync = document.createElement('td');
    columnLastSync.textContent = systemCheck.lastSync || 'N/A';
    tableRow.appendChild(columnLastSync);
    return tableRow;
};
