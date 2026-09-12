# Release 0.0.11 – Änderungen seit v0.0.10

**Veröffentlichungsdatum**: 12.09.2026

---

## Warum ein neues Minor-Release?

HACS/Home Assistant hat **v0.0.10 mehrfach überschrieben**. Gleiche Versionsnummer = oft **kein Update**. Deshalb **0.0.11**.

---

## Bugfix: MQTT blockiert die Integration nicht mehr

Der Fehler `[Errno -5] Name has no usable address` kam sehr wahrscheinlich **nicht** von `http://192.168.10.73:5001`, sondern vom **MQTT-Broker** (alter Hostname wie `localhost`, `casahosch`, `host.docker.internal`). Die Fehlermeldung hat fälschlich die API-URL genannt, weil MQTT-Connect **nach** dem API-Login die komplette Einrichtung abgebrochen hat.

- MQTT-Connect-Fehler werden geloggt (**Broker-Host steht im Log**).
- Die Integration **startet trotzdem** (ohne Live-MQTT).
- MQTT unter **Neu konfigurieren** auf die neue Broker-IP setzen oder **leer lassen**.

---

## Migration von v0.0.10

1. In HACS / GitHub auf **0.0.11** aktualisieren (nicht 0.0.10 erneut laden).
2. Home Assistant neu starten.
3. **Neu konfigurieren**: API `http://192.168.10.73:5001`; MQTT-Broker neue IP oder leer.
4. Im Log sollte stehen: `Connecting to Taubenschiesser API at http://192.168.10.73:5001 (MQTT broker: …)`.

---

## Kurzüberblick

| Thema | Inhalt |
|--------|--------|
| MQTT | Connect-Fehler stoppen die Integration nicht mehr |
| Log | API-URL und MQTT-Broker getrennt sichtbar |
| Version | **0.0.11** (damit HACS den Build wirklich zieht) |

---

**Git**: `v0.0.10...HEAD`
