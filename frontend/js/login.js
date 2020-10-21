/*
    login.js - Systems monitoring login handling.

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

import { suppressEvent } from 'https://javascript.homeinfo.de/lib.js';
import * as api from './api.js';


/*
    Performs the initial login.
*/
function login () {
    const account = document.getElementById('account').value;
    const passwd = document.getElementById('passwd').value;
    return api.login(account, passwd);
}


/*
    Initialize index.html.
*/
export function init () {
    const loginButton = document.getElementById('login');
    loginButton.addEventListener('click', suppressEvent(login), false);
}
