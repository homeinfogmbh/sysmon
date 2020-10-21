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


var sysmon = sysmon || {};


/*
    Filters, sorts and renders systems.
*/
function render (systems) {
    systems = sysmon.filtered(systems);
    const onlineSystems = sysmon.online(systems);
    const onlineContainer = document.getElementById('online');
    const onlineCounter = document.getElementById('onlineCount');
    sysmon.render(onlineSystems, onlineContainer, onlineCounter);
    const offlineSystems = sysmon.offline(systems);
    const offlineContainer = document.getElementById('offline');
    const offlineCounter = document.getElementById('offlineCount');
    sysmon.render(offlineSystems, offlineContainer, offlineCounter);
    const blackmodeSystems = sysmon.blackmode(systems);
    const blackmodeContainer = document.getElementById('blackmode');
    const blackmodeCounter = document.getElementById('blackmodeCount');
    sysmon.render(blackmodeSystems, blackmodeContainer, blackmodeCounter);
    const outdatedSystems = sysmon.outdated(systems);
    const outdatedContainer = document.getElementById('outdated');
    const outdatedCounter = document.getElementById('outdatedCount');
    sysmon.render(outdatedSystems, outdatedContainer, outdatedCounter);
}


/*
    Reloads the systems.
*/
function load (force = false) {
    sysmon.startLoading();
    return sysmon.systems.getValue(force).then(render).then(sysmon.stopLoading);
}


/*
    Initialize manage.html.
*/
function init () {
    load();
    const btnFilter = document.getElementById('filter');
    btnFilter.addEventListener('click', sysmon.partial(load), false);
    const btnReload = document.getElementById('reload');
    btnReload.addEventListener('click', sysmon.partial(load, true), false);
}


document.addEventListener('DOMContentLoaded', init);
