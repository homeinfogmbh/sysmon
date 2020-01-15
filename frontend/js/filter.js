/*
    filter.js - Systems monitoring systems filtering.

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
    Case-insensitively returns the index of the substring.
*/
sysmon.includesIgnoreCase = function (haystack, needle) {
    if (! haystack) {
        return false;
    }

    return haystack.toLowerCase().includes(needle.toLowerCase());
};


/*
    Returns the respective address as a one-line string.
*/
sysmon.addressToString = function (address) {
    return address.street + ' ' + address.houseNumber + ', ' + address.zipCode + ' ' + address.city;
};


/*
    Filters the provided system by the respective keywords.
*/
sysmon.filterSystems = function* (systems, keyword) {
    for (const system of systems) {
        // Yield any copy on empty keyword.
        if (keyword == null || keyword == '') {
            yield system;
            continue;
        }

        // Exact ID matching.
        if (keyword.startsWith('#')) {
            let fragments = keyword.split('#');
            let id = parseInt(fragments[1]);

            if (system.id == id) {
                yield system;
            }

            continue;
        }

        let deployment = system.deployment;

        if (deployment == null) {
            continue;
        }

        let cid = '' + deployment.customer.id;

        if (sysmon.includesIgnoreCase(cid, keyword)) {
            yield system;
            continue;
        }

        let customerName = deployment.customer.company.name;

        if (sysmon.includesIgnoreCase(customerName, keyword)) {
            yield system;
            continue;
        }

        let address = sysmon.addressToString(deployment.address);

        if (sysmon.includesIgnoreCase(address, keyword)) {
            yield system;
            continue;
        }
    }
};


/*
    Filters systems.
*/
sysmon.filtered = function (systems) {
    const keyword = document.getElementById('searchField').value;
    systems = sysmon.filterSystems(systems, keyword);
    return Array.from(systems);
};


/*
    Yields online systems.
*/
sysmon.online = function* (systems) {
    for (const system of systems) {
        if (system.checks != null && system.checks.OnlineCheck != null) {
            if (system.checks.OnlineCheck.successful) {
                yield system;
            }
        }
    }
};


/*
    Yields offline systems.
*/
sysmon.offline = function* (systems) {
    for (const system of systems) {
        if (system.checks != null && system.checks.OnlineCheck != null) {
            if (! system.checks.OnlineCheck.successful) {
                yield system;
            }
        }
    }
};


/*
    Yields systems in black mode.
*/
sysmon.blackmode = function* (systems) {
    for (const system of systems) {
        if (system.checks != null && system.checks.ApplicationCheck != null) {
            if (! system.checks.ApplicationCheck.successful) {
                // Exclude unknown states if system was offline.
                if (system.checks.ApplicationCheck.enabled != null && system.checks.ApplicationCheck.running != null) {
                    yield system;
                }
            }
        }
    }
};


/*
    Yields systems out of sync.
*/
sysmon.outdated = function* (systems) {
    const now = Date.now();

    for (const system of systems) {
        if (system.lastSync != null) {
            const lastSync = new Date(system.lastSync);
            const timedelta = now - lastSync;
            console.log('Time delta: ', timedelta);

            if (! system.checks.SyncCheck.successful) {
                yield system;
            }
        }
    }
};
