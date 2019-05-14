/*
    functions.js - Systems monitoring functions library.

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
sysmon.STORAGE_KEY = 'sysmon.systems';


/*
    Starts loading.
*/
sysmon.startLoading = function () {
    const loader = document.getElementById('loader');
    const target = document.getElementById('target');
    target.style.display = 'none';
    loader.style.display = 'block';
};


/*
    Stops loading.
*/
sysmon.stopLoading = function () {
    const loader = document.getElementById('loader');
    const target = document.getElementById('target');
    loader.style.display = 'none';
    target.style.display = 'block';
};


/*
    Stores the systems in local storage.
*/
sysmon.storeSystems = function (systems) {
    systems = Array.from(systems);
    const json = JSON.stringify(systems);
    return localStorage.setItem(sysmon.STORAGE_KEY, json);
};


/*
    Loads the systems from local storage.
*/
sysmon.loadSystems = function () {
    const raw = localStorage.getItem(sysmon.STORAGE_KEY);

    if (raw == null) {
        return [];
    }

    return JSON.parse(raw);
};


/*
    Performs a login.
*/
sysmon.login = function (account, passwd) {
    const payload = {'account': account, 'passwd': passwd};
    const data = JSON.stringify(payload);
    const headers = {'Content-Type': 'application/json'};
    return sysmon.makeRequest('POST', 'https://his.homeinfo.de/session', data, headers).then(
        function () {
            window.location = 'manage.html';
        },
        function () {
            alert('Ungültiger Benutzername und / oder Passwort.');
        }
    );
};


/*
    Retrieves systems from the API.
*/
sysmon.getStats = function () {
    return sysmon.makeRequest('GET', sysmon.BASE_URL + '/stats').then(
        function (response) {
            const systems = response.json;
            sysmon.storeSystems(systems);
            return systems;
        },
        sysmon.checkSession('Die Liste der Systeme konnte nicht abgefragt werden.')
    );
};


/*
    Retrieves customers from the backend,
    which the current user is allowed to deploy to.
*/
sysmon.getCustomers = function () {
    return sysmon.makeRequest('GET', sysmon.BASE_URL + '/customers').catch(
        sysmon.checkSession('Die Liste der Kunden konnte nicht abgefragt werden.')
    );
};


/*
    Retrieves types from the backend.
*/
sysmon.getTypes = function () {
    return sysmon.makeRequest('GET', sysmon.BASE_URL + '/types').catch(
        sysmon.checkSession('Die Liste der Terminal-Typen konnte nicht abgefragt werden.')
    );
};


/*
    Lists the respective systems.
*/
sysmon.render = function (systems, container) {
    container.innerHTML = '';

    for (const system of systems) {
        let row = sysmon.systemCheckToDOM(system);

        if (row != null) {
            container.appendChild(row);
        }
    }
};


/*
    Renders the respective customers.
*/
sysmon.renderCustomers = function (customers) {
    const select = document.getElementById('customer');
    select.innerHTML = '';

    for (const customer of customers) {
        let option = document.createElement('option');
        option.setAttribute('value', customer.id);
        option.textContent = customer.company.name;
        select.appendChild(option);
    }
};


/*
    Renders the respective connections.
*/
sysmon.renderConnections = function (connections) {
    const select = document.getElementById('connection');
    select.innerHTML = '';

    for (const connection of connections) {
        let option = document.createElement('option');
        option.setAttribute('value', connection);
        option.textContent = connection;
        select.appendChild(option);
    }
};


/*
    Renders the respective types.
*/
sysmon.renderTypes = function (types) {
    const select = document.getElementById('type');
    select.innerHTML = '';

    for (const type of types) {
        let option = document.createElement('option');
        option.setAttribute('value', type);
        option.textContent = type;
        select.appendChild(option);
    }
};


/*
    Function to wrap a function and disable default events.
*/
sysmon.partial = function (func, ...args) {
    return function (event) {
        if (event != null) {
            event.preventDefault();
        }

        return func(...args);
    };
};
