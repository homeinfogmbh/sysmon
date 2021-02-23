/*
    system.mjs - Systems monitoring details.

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
import { checkSystem, getSystemDetails, system } from './api.mjs';


let chart;


function getConfig (data) {
    const color = Chart.helpers.color;
    return {
        type: 'line',
        data: {
            datasets: [{
                label: 'Systemstatus',
                backgroundColor: color(window.chartColors.red).alpha(0.5).rgbString(),
                borderColor: window.chartColors.red,
                fill: false,
                data: data
            }]
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'System Up- und Downtime'
            },
            scales: {
                xAxes: [{
                    type: 'time',
                    time: {
                        tooltipFormat: 'DD.MM.YYYY HH:mm',
                        displayFormats: {
                            hour: 'HH:mm'
                        }
                    },
                    display: true,
                    scaleLabel: {
                        display: true,
                        labelString: 'Datum'
                    },
                    ticks: {
                        major: {
                            fontStyle: 'bold',
                            fontColor: '#FF0000'
                        }
                    }
                }],
                yAxes: [{
                    display: true,
                    scaleLabel: {
                        display: true,
                        labelString: 'Online'
                    },
                    ticks: {
                        max: 1,
                        min: 0,
                        stepSize: 1
                    }
                }]
            }
        }
    };
};


function renderDiagram (records) {
    const data = [];

    for (const record of records) {
        const item = {x: record.timestamp, y: record.online ? 1 : 0};
        data.push(item);
    }

    if (chart == null) {
        const config = getConfig(data);
        const ctx = document.getElementById('uptime').getContext('2d');
        chart = new Chart(ctx, config);
    } else {
        chart.data.datasets[0].data = data;
        chart.update();
    }
}


/*
    Queries the backend and render the diagram.
*/
function render() {
    const dateFrom = document.getElementById('from');
    const dateUntil = document.getElementById('until');
    const headers = {
        'from': dateFrom.value,
        'until': dateUntil.value
    };
    return Loader.wrap(getSystemDetails(system.get(), headers).then(renderDiagram));
}


/*
    Issues a live system check.
*/
function checkNow (event) {
    const target = event.currentTarget;
    target.disabled = true;
    const systemId = system.get();
    return checkSystem(systemId).then(
        function (json) {
            const state = json.online ? 'online' : 'offline';
            target.disabled = false;
            alert('Das System #' + systemId + ' ist aktuell ' + state + '.');
        }
    ).finally(
        function () {
            target.disabled = false;
        }
    );
}


/*
    Initializes the date input fields.
*/
function initUI () {
    const systemId = document.getElementById('systemId');
    systemId.innerHTML = system.get();
    const today = new Date();
    const defaultTimespan = 30 * 24 * 3600 * 1000;  // 30 days.
    const startDate = new Date(today - defaultTimespan);

    const dateFrom = document.getElementById('from');
    dateFrom.value = startDate.toISOString().split('T')[0];
    dateFrom.addEventListener('change', suppressEvent(render), false);

    const dateUntil = document.getElementById('until');
    dateUntil.value = today.toISOString().split('T')[0];
    dateUntil.addEventListener('change', suppressEvent(render), false);

    const btnCheck = document.getElementById('btnCheck');
    btnCheck.addEventListener('click', checkNow, false);
}


/*
    Initialize system.html.
*/
export function init () {
    initUI();
    render();
}
