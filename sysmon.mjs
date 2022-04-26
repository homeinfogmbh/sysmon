/*
    sysmon.mjs - Library for the Sysmon backend.

    (C) 2022 HOMEINFO - Digitale Informationssysteme GmbH

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

import { System } from 'https://javascript.homeinfo.de/hwdb.mjs';

const CURRENT_APPLICATION_VERSION = '2.48.0-1';
const ONE_DAY = 24 * 60 * 60 * 1000;    // milliseconds
const THREE_MONTHS = 3 * 30 * ONE_DAY;  // milliseconds

export class CheckResults {
    constructor (
        timestamp, icmpRequest, sshLogin, httpRequest, applicationState,
        applicationVersion, smartCheck, baytrailFreeze, ramTotal, ramFree,
        ramAvailable, offlineSince, blackscreenSince
    ) {
        this.timestamp = timestamp;
        this.icmpRequest = icmpRequest;
        this.sshLogin = sshLogin;
        this.httpRequest = httpRequest;
        this.applicationState = applicationState;
        this.applicationVersion = applicationVersion;
        this.smartCheck = smartCheck;
        this.baytrailFreeze = baytrailFreeze;
        this.ramTotal = ramTotal;
        this.ramFree = ramFree;
        this.ramAvailable = ramAvailable;
        this.offlineSince = offlineSince;
        this.blackscreenSince = blackscreenSince;
    }

    static fromJSON (json) {
        return new this(
            new Date(json.timestamp),
            json.icmpRequest,
            json.sshLogin,
            json.httpRequest,
            json.applicationState,
            json.applicationVersion,
            json.smartCheck,
            json.baytrailFreeze,
            json.ramTotal,
            json.ramFree,
            json.ramAvailable,
            (json.offlineSince == null) ? null : new Date(json.offlineSince),
            (json.blackscreenSince == null) ? null : new Date(json.blackscreenSince)
        );
    }

    get moreThanThreeMonthsOffline () {
        if (this.offlineSince == null)
            return false;

        return (new Date()) - this.offlineSince > THREE_MONTHS;
    }

    get online () {
        return this.icmpRequest && (this.sshLogin != 'failed');
    }

    get outOfDate () {
        return this.applicationVersion != CURRENT_APPLICATION_VERSION;
    }
}

export class CheckedSystem extends System {
    static fromJSON (json) {
        system = super.fromJSON(json)
        system.checkResults = [];

        for (const checkResult of json.checkResults)
            system.checkResults.push(CheckResults.fromJSON(checkResult));

        return system;
    }

    get lastCheck () {
        if (this.checkResults.length > 0)
            return this.checkResults[0];

        return null;
    }

    get synced () {
        if (this.lastSync == null)
            return false;

        return (new Date()) - this.lastSync < ONE_DAY;
    }

    get online () {
        if (this.lastCheck == null)
            return null;

        return this.lastCheck.online;
    }
}

export class GlobalStats {
    constructor (
        smartErrors, notDeployed, testingSystems, blackMode,
        outdatedApplication, moreThanThreeMonthsOffline
    ) {
        this.smartErrors = smartErrors;
        this.notDeployed = notDeployed;
        this.testingSystems = testingSystems;
        this.blackMode = blackMode;
        this.outdatedApplication = outdatedApplication;
        this.moreThanThreeMonthsOffline = moreThanThreeMonthsOffline;
    }

    static fromCheckedSystems(checkedSystems) {
        let smartErrors = 0;
        let notDeployed = 0;
        let testingSystems = 0;
        let blackMode = 0;
        let outdatedApplication = 0;
        let moreThanThreeMonthsOffline = 0;
        let lastCheck;

        for (checkedSystem of checkedSystems) {
            lastCheck = checkedSystem.lastCheck;

            if (lastCheck == null)
                continue;

            if (lastCheck.smartCheck == 'failed')
                smartErrors++;

            if (checkedSystem.deployment == null)
                notDeployed++;

            if (checkedSystem.testing)
                testingSystems++;

            if (lastCheck.applicationState == 'not running')
                blackMode++;

            if (lastCheck.outOfDate)
                outdatedApplication++;

            if (lastCheck.moreThanThreeMonthsOffline)
                moreThanThreeMonthsOffline++;
        }

        return new this(
            smartErrors, notDeployed, testingSystems, blackMode,
            outdatedApplication, moreThanThreeMonthsOffline
        );
    }
}
