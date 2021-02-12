/*
    filter.js - Systems monitoring systems filtering.

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

import { filterSystems } from 'https://javascript.homeinfo.de/hwdb.mjs';
import { addressToString } from 'https://javascript.homeinfo.de/mdb.mjs';


/*
    Filters systems.
*/
export function filtered (systems) {
    const keyword = document.getElementById('searchField').value;
    systems = filterSystems(systems, keyword);
    return Array.from(systems);
}


/*
    Yields online systems.
*/
export function *online (systems) {
    for (const system of systems) {
        if (system.checks != null && system.checks.OnlineCheck != null) {
            if (system.checks.OnlineCheck.successful)
                yield system;
        }
    }
}


/*
    Yields offline systems.
*/
export function *offline (systems) {
    for (const system of systems) {
        if (system.checks != null && system.checks.OnlineCheck != null) {
            if (! system.checks.OnlineCheck.successful)
                yield system;
        }
    }
}


/*
    Yields systems in black mode.
*/
export function *blackmode (systems) {
    for (const system of systems) {
        if (system.checks != null && system.checks.ApplicationCheck != null) {
            if (! system.checks.ApplicationCheck.successful) {
                // Exclude unknown states if system was offline.
                if (system.checks.ApplicationCheck.enabled != null && system.checks.ApplicationCheck.running != null)
                    yield system;
            }
        }
    }
}


/*
    Yields systems out of sync.
*/
export function *outdated (systems) {
    const outdated = 3 * 24 * 60 * 60 * 1000;  // Three days in milliseconds.
    const now = Date.now();

    for (const system of systems) {
        if (system.lastSync != null) {
            const lastSync = new Date(system.lastSync);
            const timedelta = now - lastSync;

            if (timedelta >= outdated)
                yield system;
        }
    }
}
