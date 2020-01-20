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


sysmon.getConfig = function (data) {
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


sysmon.renderDiagram = function (records) {
    const data = [];

    for (const record of records) {
        console.log('DEBUG: ' + record.timestamp);
        const timestamp = new Date(record.timestamp);
        console.log('DEBUG: ' + timestamp);
        const item = {x: timestamp, y: record.online ? 1 : 0};
        data.push(item);
    }

    var ctx = document.getElementById('uptime').getContext('2d');
    console.log('Rendering chart.');
    window.myLine = new Chart(ctx, sysmon.getConfig(data));
    sysmon.stopLoading();
};


/*
    Queries the backend and render the diagram.
*/
function render() {
    const urlParams = new URLSearchParams(window.location.search);
    const system = urlParams.get('system');
    const dateFrom = document.getElementById('from');
    const dateUntil = document.getElementById('until');
    const headers = {
        'from': dateFrom.value,
        'until': dateUntil.value
    };
    return sysmon.getSystemDetails(system, headers).then(sysmon.renderDiagram);
}


/*
    Initializes the date input fields.
*/
function initDateInputs () {
    const today = new Date();
    const defaultTimespan = 30 * 24 * 3600 * 1000;  // 30 days.
    const startDate = new Date(today - defaultTimespan);
    const dateFrom = document.getElementById('from');
    dateFrom.value = startDate.toISOString().split('T')[0];
    const dateUntil = document.getElementById('until');
    dateUntil.value = today.toISOString().split('T')[0];
}


/*
    Initialize manage.html.
*/
function init () {
    initDateInputs();
    console.log('Setting locales.');
    render();
}


document.addEventListener('DOMContentLoaded', init);
