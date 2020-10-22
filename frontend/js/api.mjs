/*
    common.js - Systems monitoring common JavaScript library.

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

import { Cache, JSONStorage } from 'https://javascript.homeinfo.de/caching.mjs';
import { json } from 'https://javascript.homeinfo.de/requests.mjs';
import * as session from 'https://javascript.homeinfo.de/his/session.mjs';
import { systemCheckToDOM } from './dom.mjs';


const BASE_URL = 'https://backend.homeinfo.de/sysmon';
const UNHANDLED_ERROR = 'Unbehandelter Fehler. Bitte kontaktieren Sie uns.';
export const system = new JSONStorage('homeinfo.sysmon.system');
export const systems = new Cache('homeinfo.sysmon.systems', getStats);


/*
    Function to make a request and display an error message on error.
*/
export function checkSession (message) {
    return function (response) {
        if (response.status == 401 || response.message == 'Session expired.') {
            alert('Sitzung abgelaufen.');
            window.location = 'index.html';
        } else {
            alert(message);
        }
    };
}


/*
    Performs a login.
*/
export function login (account, passwd) {
    return session.login(account, passwd).then(
        function () {
            window.location = 'overview.html';
        },
        function () {
            alert('Ungültiger Benutzername und / oder Passwort.');
        }
    );
}


/*
    Retrieves systems from the API.
*/
export function getStats () {
    return json.get(BASE_URL + '/stats').then(
        response => response.json,
        checkSession('Die Liste der Systeme konnte nicht abgefragt werden.')
    );
}


/*
    Retrieves system details from the API.
*/
export function getSystemDetails (system, headers = {}) {
    return json.get(BASE_URL + '/details/' + system, headers).then(
        response => response.json,
        checkSession('Die Systemdetails konnten nicht abgefragt werden.')
    );
}


/*
    Issues a system check.
*/
export function checkSystem (system) {
    return json.get(BASE_URL + '/check/' + system).then(
        response => response.json,
        checkSession('Ein Systemcheck konnte nicht durchgeführt werden.')
    );
}


/*
    Lists the respective systems.
*/
export function render (systems, container, counter) {
    container.innerHTML = '';
    counter.innerHTML = '';
    let count = 0;

    for (const system of systems) {
        count += 1;
        let row = systemCheckToDOM(system);

        if (row != null)
            container.appendChild(row);
    }

    counter.innerHTML = '(' + count + ')';
}