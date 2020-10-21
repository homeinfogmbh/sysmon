/*
    overview.js - Systems monitoring overview.

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

import { Loader, suppressEvent } from 'https://javascript.homeinfo.de/lib.js';
import * as api from './api.js';
import { blackmode, filtered, offline, online, outdated } from './filter.js';
import { openTab } from './navigation.js';


/*
    Filters, sorts and renders systems.
*/
function render (systems) {
    systems = filtered(systems);

    const onlineSystems = online(systems);
    const onlineContainer = document.getElementById('online');
    const onlineCounter = document.getElementById('onlineCount');
    api.render(onlineSystems, onlineContainer, onlineCounter);

    const offlineSystems = offline(systems);
    const offlineContainer = document.getElementById('offline');
    const offlineCounter = document.getElementById('offlineCount');
    api.render(offlineSystems, offlineContainer, offlineCounter);

    const blackmodeSystems = blackmode(systems);
    const blackmodeContainer = document.getElementById('blackmode');
    const blackmodeCounter = document.getElementById('blackmodeCount');
    api.render(blackmodeSystems, blackmodeContainer, blackmodeCounter);

    const outdatedSystems = outdated(systems);
    const outdatedContainer = document.getElementById('outdated');
    const outdatedCounter = document.getElementById('outdatedCount');
    api.render(outdatedSystems, outdatedContainer, outdatedCounter);
}


/*
    Reloads the systems.
*/
function load (force = false) {
    return Loader.wrap(api.systems.getValue(force).then(render));
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
    btnOffline = document.getElementById('btnOffline');
    btnOffline.addEventListener('click', openTab('offlineTab'), false);
    btnOnline = document.getElementById('btnOnline');
    btnOnline.addEventListener('click', openTab('onlineTab'), false);
    btnBlackmode = document.getElementById('btnBlackmode');
    btnBlackmode.addEventListener('click', openTab('blackmodeTab'), false);
    btnOutdated = document.getElementById('btnOutdated');
    btnOutdated.addEventListener('click', openTab('outdatedTab'), false);
}
