/*
    autologin.js - Systems monitoring automatic login.

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
    Initialize index.html.
*/
function init () {
    const account = localStorage.getItem('sysmon.account');
    const passwd = localStorage.getItem('sysmon.passwd');
    console.log('Account: ' + account);
    console.log('Password: ' + typeof passwd);

    if (account == null || passwd == null) {
        console.log('Account and password are null.');
        window.location = 'login.html';
    } else {
        console.log('Attempting auto login.');
        sysmon.login(account, passwd).then(
            function () {
                console.log('Autologin succeeded.');
                //window.location = 'overview.html';
            },
            function () {
                console.log('Autologin failed.');
                //window.location = 'login.html';
            }
        );
    }
}


document.addEventListener('DOMContentLoaded', init);
