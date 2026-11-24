# Changelog

- 2026-11-24 — Tobias Erlacher: `/checks` und Offline-Historie laden `smartctl_full` (37 von 38 MB) nicht mehr: `CheckResults.select(cascade=True, skip=...)`; nginx-vhost sysmon komprimiert JSON (`gzip_types`, nur auf cthulhu)
- 2026-11-23 — Tobias Erlacher: Auth-Bypass behoben: `@APPLICATION.route` stand bei /patch_warningmail, /test_warningmail, /warningmail, /customer_add, /send_statistic_test_mail unter den Auth-Decorators (Flask registrierte die ungeschützte Funktion); `@authenticated` bei den *-user-notification-emails-Routen ergänzt
- 2026-08-04 — Tobias Erlacher: Zeilenenden auf LF normalisiert (setup.py/Makefile) + .gitattributes; behebt `env: python3\r` bei `make install`
- 2026-08-04 — Tobias Erlacher: Newsletter-Feature aus sysmon entfernt (ORM Newsletter/Newsletterlistitems, WSGI-Routen /newsletter*, Console-Script sysmon-send-mailing, systemd sysmon-mailing.service/.timer)
- 2026-07-29 — Tobias Erlacher: CHANGELOG eingeführt (Claude-Onboarding)
