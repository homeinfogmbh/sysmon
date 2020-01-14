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
    Reloads the systems.
*/
function reload () {
    sysmon.startLoading();
    return sysmon.getStats().then(render);
}


/*
    Filters, sorts and renders systems.
*/
function render (systems) {
    sysmon.startLoading();

    if (systems == null) {
        sysmon.startLoading();
        systems = sysmon.loadSystems();
    }

    systems = sysmon.filtered(systems);
    const offlineSystems = sysmon.offline(systems);
    const offlineContainer = document.getElementById('offline');
    sysmon.render(offlineSystems, offlineContainer);
    const blackmodeSystems = sysmon.blackmode(systems);
    const blackmodeContainer = document.getElementById('blackmode');
    sysmon.render(blackmodeSystems, blackmodeContainer);
    const outdatedSystems = sysmon.outdated(systems);
    const outdatedContainer = document.getElementById('outdated');
    sysmon.render(outdatedSystems, outdatedContainer);
    sysmon.stopLoading();
}


/*
    Initialize manage.html.
*/
function init () {
    reload();
    const btnFilter = document.getElementById('filter');
    btnFilter.addEventListener('click', sysmon.partial(render), false);
    const btnReload = document.getElementById('reload');
    btnReload.addEventListener('click', sysmon.partial(reload), false);
}


document.addEventListener('DOMContentLoaded', init);
