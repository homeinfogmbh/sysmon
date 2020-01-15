/*
    system.js - Systems monitoring details.

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


sysmon.renderDiagram = function (records) {
    const data = [];

    for (const record of records) {
        const item = {x: new Date(record.timestamp), y: record.online ? 1 : -1};
        data.push(item);
    }

    const context = document.getElementById('uptime').getContext('2d');
    const chart = new Chart(context, {
        type: 'line',
        data: data
    });
    chart.render();
    sysmon.stopLoading();
};


/*
    Initialize manage.html.
*/
function init () {
    sysmon.getSystemDetails(12).then(sysmon.renderDiagram);
}


document.addEventListener('DOMContentLoaded', init);
