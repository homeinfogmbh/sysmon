# sysmon
Stand: 2026-08-04, geprüft gegen Commit af6c113

## Zweck
Systems-Monitoring der Digital-Signage-Systeme. Ein Dienst sammelt periodisch
Statusinformationen der Systeme (Erreichbarkeit, Applikations-Zustand, SMART,
Speicher, Sensoren u. v. m.) und schreibt sie in eine Datenbank. Zusätzlich ein
Web-Application-Backend, um diese Informationen berechtigten Nutzern anzuzeigen
(sysmon.homeinfo.de), plus Statistik-/Warnungs-Mailings.

## Stack & Einstiegspunkte
Python 3, Flask über das Homeinfo-`his`-Framework (WSGI), Peewee-ORM via
`peeweeplus` (MySQL-DB `sysmon`). Package `sysmon` + Subpackage `sysmon.checks`.
Frontend-Modul `sysmon.mjs`; JSON-Schemas unter `jsonschema/`.

Console-Scripts (`setup.py`):
- `sysmon` = `sysmon.daemon:spawn` — Monitoring-Daemon (Sammellauf).
- `sysmon-cleanup`, `sysmon-notify`, `sysmon-generate-blacklist`,
  `sysmon-send-statistic`, `sysmon-send-warning`.

Der Daemon iteriert über `hwdb.System` (deployt, nicht virtuell) und führt die
Checks in `sysmon/checks/` aus (parallel via Pool): `application` (Zustand/
Version), `black_screen`, `baytrail`, `efi`, `icmp`, `iperf3`, `meminfo`,
`offline`, `root_partition`, `sensors`, `smart`, `ssh`, `synchronization`,
`touchscreen`, `logs`.

## Schnittstellen
### Konsumiert
- **`hwdb`** — `System`-Modell/Selektion als Prüfziel; `ApplicationMode`/`Connection`.
- **Systeme selbst** — Checks per ICMP (Ping), SSH, HTTP-Request an die
  Geräte-RPC (`digsigctl`), iperf3, Screenshot-Abruf.
- **Weitere Homeinfo-Libraries:** `digsigdb`, `his` (Auth), `mdb`, `previewlib`,
  `termacls` (ACLs), `notificationlib`, `emaillib` (Mailversand), `configlib`,
  `functoolsplus`, `wsgilib`.

### Bietet an
- **Eigene MySQL-DB `sysmon`** mit Modellen: `CheckResults`,
  `NewestCheckResults`, `Warningmail`, Notification-Email-Modelle
  (`UserNotificationEmail`, `ExtraUserNotificationEmail`,
  `StatisticUserNotificationEmail`). ⚠️ Das entfernte Newsletter-Feature ließ die
  DB-Tabellen `newsletter`/`newsletterlistitems` verwaist zurück (bei Bedarf droppen).
- **HTTP-Endpoints** (Auth via `his`, `@authorized("sysmon")`, `@root`), u. a.:
  `GET /checks` (alle Check-Ergebnisse), `GET /check/<system>` (Live-Check),
  `GET /screenshot/<system>` (JPEG), sowie Warningmail-/Customer-/
  Notification-Email-Endpoints. Details in `doc/apidoc.md`.
- **systemd-Units + Timer** (installiert nach `/usr/lib/systemd/system`):
  `sysmon`, `sysmon-cleanup`, `sysmon-generate-blacklist`,
  `sysmon-statistic`, `sysmon-warning` — je `.service` + `.timer`.
- **JSON-Schemas** für Check-Ergebnisse (`check-results`, `checked-systems` …).

## Deployment / Laufzeit
Python-Package (`setuptools_scm`-Versionierung). Der Sammellauf läuft
timer-gesteuert (`sysmon.timer`) als systemd-Dienst; weitere Timer für Cleanup,
Blacklist-Generierung und Mailings. Das WSGI-Backend wird unter
`sysmon.homeinfo.de` bereitgestellt. ⚠️ ANNAHME: Auslieferung per mod_wsgi/uwsgi
hinter dem HIS-Stack; genaues Webserver-Setup nicht aus dem Repo ersichtlich.

## Ersetzbarkeit
Kopplungsgrad: **mittel–hoch**. Fachlich in sich geschlossen (eigene DB, eigene
Checks), aber fest an `hwdb` (Prüfziele/Modell), die HIS-Authentifizierung und
die Geräte-Schnittstellen (digsigctl-RPC, SSH, ICMP) gebunden. Die Check-Logik
in `sysmon/checks/` ist modular erweiterbar; ein Komplettersatz müsste das
Datenmodell, die Endpoints (siehe `apidoc.md`) und die Timer-Dienste nachbilden.

## Weitere Doku
- `README.md` (Kurzbeschreibung: Monitoring-Backend).
- `doc/apidoc.md` — **API-Dokumentation** (Base-URL `sysmon.homeinfo.de`,
  Endpoints/Responses); bei API-Änderungen dort ergänzen statt hier doppeln.
- `jsonschema/` — Schemas der Check-Ergebnisse.
- Abhängige/verwandte Komponenten: `hwdb`, `digsigctl`.
- ⚠️ ANNAHME: Zentrales Repo `homeinfo-architektur` (Ordner `komponenten/`) noch
  nicht geprüft — dort ggf. übergeordnete Doku ergänzen/verlinken.
