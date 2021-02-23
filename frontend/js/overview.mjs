/*
    overview.mjs - Systems monitoring overview.

    (C) 2019-2021 HOMEINFO - Digitale Informationssysteme GmbH

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

import { Loader, suppressEvent } from 'https://javascript.homeinfo.de/lib.mjs';
import * as api from './api.mjs';
import { blackmode, filtered, offline, online, outdated } from './filter.mjs';
import { openTab } from './navigation.mjs';


/*
    Filters, sorts and renders systems.
*/
function render (systems) {
    systems = filtered(systems);
    api.render(online(systems), document.getElementById('online'), document.getElementById('onlineCount'));
    api.render(offline(systems), document.getElementById('offline'), document.getElementById('offlineCount'));
    api.render(blackmode(systems), document.getElementById('blackmode'), document.getElementById('blackmodeCount'), true);
    api.render(outdated(systems), document.getElementById('outdated'), document.getElementById('outdatedCount'), true);
}


/*
    Reloads the systems.
*/
function load (force = false) {
    return Loader.wrap(api.systems.get(force).then(render));
}


/*
    Initialize overview.html.
*/
export function init () {
    load();

    const btnFilter = document.getElementById('filter');
    btnFilter.addEventListener('click', suppressEvent(load), false);

    const btnReload = document.getElementById('reload');
    btnReload.addEventListener('click', suppressEvent(load, true), false);

    const btnOffline = document.getElementById('btnOffline');
    btnOffline.addEventListener('click', openTab('offlineTab'), false);

    const btnOnline = document.getElementById('btnOnline');
    btnOnline.addEventListener('click', openTab('onlineTab'), false);

    const btnBlackmode = document.getElementById('btnBlackmode');
    btnBlackmode.addEventListener('click', openTab('blackmodeTab'), false);

    const btnOutdated = document.getElementById('btnOutdated');
    btnOutdated.addEventListener('click', openTab('outdatedTab'), false);
}
