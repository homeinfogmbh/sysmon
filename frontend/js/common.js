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


var sysmon = sysmon ||  {};

sysmon.BASE_URL = 'https://backend.homeinfo.de/sysmon';
sysmon.UNHANDLED_ERROR = 'Unbehandelter Fehler. Bitte kontaktieren Sie uns.';


/*
  Makes a request returning a promise.
*/
sysmon.makeRequest = function (method, url, data = null, headers = {}) {
    function parseResponse (response) {
        try {
            return JSON.parse(response);
        } catch (error) {
            return response;
        }
    }

    function executor (resolve, reject) {
        function onload () {
            if (this.status >= 200 && this.status < 300) {
                resolve({
                    response: xhr.response,
                    json: parseResponse(xhr.response),
                    status: this.status,
                    statusText: xhr.statusText
                });
            } else {
                reject({
                    response: xhr.response,
                    json: parseResponse(xhr.response),
                    status: this.status,
                    statusText: xhr.statusText
                });
            }
        }

        function onerror () {
            reject({
                response: xhr.response,
                json: parseResponse(xhr.response),
                status: this.status,
                statusText: xhr.statusText
            });
        }

        const xhr = new XMLHttpRequest();
        xhr.withCredentials = true;
        xhr.open(method, url);

        for (const header in headers) {
            xhr.setRequestHeader(header, headers[header]);
        }

        xhr.onload = onload;
        xhr.onerror = onerror;

        if (data == null) {
            xhr.send();
        } else {
            xhr.send(data);
        }
    }

    return new Promise(executor);
};


/*
    Function to make a request and display an error message on error.
*/
sysmon.checkSession = function (message) {
    return function (response) {
        if (response.status == 401 || response.message == 'Session expired.') {
            alert('Sitzung abgelaufen.');
            window.location = 'index.html';
        } else {
            alert(message);
        }
    };
};
