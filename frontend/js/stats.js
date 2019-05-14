/*
    manage.js - Systems monitoring systems listing.

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
    return sysmon.getStats().then(filter).then(sysmon.stopLoading);
}


/*
    Filters, sorts and renders systems.
*/
function filter (systems) {
    if (systems == null) {
        sysmon.startLoading();
        systems = sysmon.loadSystems();
    }

    systems = sysmon.filtered(systems);
    systems = sysmon.sorted(systems);
    sysmon.listSystems(systems);
    sysmon.stopLoading();
}


/*
    Initialize manage.html.
*/
function init () {
    sysmon.startLoading();
    reload().then(sysmon.stopLoading);
    const btnFilter = document.getElementById('filter');
    btnFilter.addEventListener('click', sysmon.partial(filter), false);
    const btnReload = document.getElementById('reload');
    btnReload.addEventListener('click', sysmon.partial(reload), false);
    const radioButtons = [
        document.getElementById('sortAsc'),
        document.getElementById('sortDesc'),
        document.getElementById('sortById'),
        document.getElementById('sortByAddress')
    ];

    for (const radioButton of radioButtons) {
        radioButton.addEventListener('change', sysmon.partial(filter), false);
    }
}


document.addEventListener('DOMContentLoaded', init);
