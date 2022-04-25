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

const THREE_MONTHS = 3 * 30 * 24 * 60 * 60 * 1000;  // milliseconds
const CURRENT_APPLICATION_VERSION = '2.48.0-1';

export class CheckResults {
    static fromJSON (json) {
        return Object.assign(new this(), json);
    }

    get online () {
        return this.icmpRequest && (this.sshLogin == 'success');
    }

    get moreThanThreeMonthsOffline () {
        return (new Date()) - (new Date(this.offlineSince)) > THREE_MONTHS;
    }
}

export class CheckedSystem {
    static fromJSON (json) {
        instance = Object.assign(new this(), json);
        instance.checkResults = [];

        for (const checkResult of json.checkResults)
            instance.checkResults.push(CheckResults.fromJSON(checkResult));

        return instance;
    }

    get lastCheck () {
        if (this.checkResults.length > 0)
            return this.checkResults[0];

        return null;
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

            if (lastCheck.applicationVersion != CURRENT_APPLICATION_VERSION)
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
