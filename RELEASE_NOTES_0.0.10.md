# Release 0.0.10 – Änderungen seit v0.0.9

**Veröffentlichungsdatum**: 12.09.2026

Dieses Dokument fasst **alle relevanten Änderungen** seit **v0.0.9** zusammen. Der Reconfigure-Flow (API-URL, Login, MQTT nach einem Server-Umzug) kam **nach** dem 0.0.9-Release auf `main` und erscheint mit **0.0.10**.

---

## Home-Assistant-Integration

### Neu konfigurieren (Reconfigure-Flow)

Unter **Einstellungen → Geräte & Dienste → Taubenschiesser → Neu konfigurieren** können die Verbindungsdaten geändert werden, **ohne** die Integration zu löschen. Entities, Gerätezuordnung und Dashboards bleiben erhalten.

Änderbar:

- **API-URL** des Taubenschiesser-Servers
- **E-Mail / Passwort**
- **MQTT** (Broker, Port, Benutzername, Passwort)

Verhalten:

- Login und Geräte-API werden gegen den **neuen** Server geprüft; Access- und Refresh-Token werden neu geholt.
- Die Config-Entry-**Unique-ID** folgt der neuen API-URL (wichtig nach Host-/IP-Wechsel).
- **Passwort leer lassen**: gespeichertes Passwort weiterverwenden.
- **MQTT-Passwort / -Benutzername leer lassen**: gespeicherte MQTT-Zugangsdaten weiterverwenden.
- **MQTT-Broker leeren**: MQTT deaktivieren (alte Broker-Daten werden entfernt).
- Nach erfolgreicher Prüfung wird die Integration neu geladen (`async_update_reload_and_abort`).

**Voraussetzung:** Home Assistant **2024.11** oder neuer (sonst erscheint der Button „Neu konfigurieren“ nicht).

### API-URL nach Neu-Konfigurieren (Bugfix)

Der Coordinator hat die API-URL bisher nur **beim Start** gespeichert. Nach einem Server-Umzug lief der Token-Refresh weiter gegen die **alte** URL (z. B. `localhost:5001`).

- API-URL, E-Mail und Passwort kommen jetzt **live** aus der Config Entry.
- Wechsel von API-URL oder MQTT löst ein Reload aus; reiner Token-Refresh nicht.
- Token-Updates überschreiben die neue URL nicht mehr.

### API-URL ohne `http://` und Logging

- Fehlt das Schema, wird **`http://` automatisch ergänzt** (`192.168.10.73:5001` → `http://192.168.10.73:5001`). Ohne Schema scheitert DNS mit *Name has no usable address*.
- Verbindungsfehler schreiben jetzt die **tatsächliche API-URL** ins Home-Assistant-Protokoll (Logger `custom_components.taubenschiesser`). Einrichtungsfehler (`ConfigEntryNotReady`) waren bisher unsichtbar.
- API-HTTP-Requests nutzen **IPv4** (`AF_INET`). In Home Assistant / Docker schlägt `getaddrinfo` sonst oft mit `[Errno -5] Name has no usable address` fehl, obwohl die URL eine IPv4-Adresse ist.

### Auth-Fehlerbehandlung

`InvalidAuth` (z. B. HTTP 401) wird im Config-Flow nicht mehr als allgemeiner Verbindungsfehler verschluckt. Falsche Anmeldedaten erscheinen als **ungültige Anmeldedaten**.

### Metadaten

- **`manifest.json`**: Version **0.0.10**.

---

## Migration von v0.0.9

1. **Integration** aktualisieren (HACS oder `custom_components` kopieren).
2. **Home Assistant neu starten**.
3. Nach einem Server-Umzug: **Neu konfigurieren** wählen und die neue API-URL **mit** `http://` eintragen (z. B. `http://192.168.10.73:5001`).
4. Passwort nur eingeben, wenn es sich geändert hat oder keines gespeichert ist.
5. Danach **Integration neu laden** (oder Home Assistant neu starten), damit der Coordinator die neue URL nutzt.

**Hinweis:** Die Integration muss nicht mehr gelöscht und neu hinzugefügt werden. Das war der bisherige Workaround und würde bei neuen Cloud-`device_id`s Lovelace-Entities zerreißen.

---

## Kurzüberblick

| Thema | Inhalt |
|--------|--------|
| HA | Reconfigure-Flow: API-URL, Login, MQTT ohne Löschen der Integration |
| Bugfix | Coordinator nutzt die aktuelle API-URL; fehlendes `http://` wird ergänzt; Fehler mit URL im Log |
| Unique-ID | folgt der API-URL nach Umzug |
| MQTT | Broker leer = MQTT aus; leere Credentials = gespeicherte Werte |
| HA-Version | 2024.11+ für den Button „Neu konfigurieren“ |

---

**Git (nur Integration)**: `v0.0.9...HEAD` – z. B. `git log v0.0.9..HEAD` / `git diff v0.0.9..HEAD`.
