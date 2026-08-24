# Release 0.0.9 – Änderungen seit v0.0.8

**Veröffentlichungsdatum**: 24.08.2026

Dieses Dokument fasst **alle relevanten Änderungen** seit **v0.0.8** zusammen. Der getaggte Release **v0.0.8** enthielt den Wassertank-Status noch nicht; die Anzeige liegt auf `main` erst nach dem Tag und erscheint mit **0.0.9**.

---

## Verhalten in der Cloud & am ESP

### Wassertank-Telemetrie (bereits vorhanden)

Die **ESP-Firmware** sendet im MQTT-Status (`taubenschiesser/{ip}/info`) das Feld **`watertank`**:

- **`true`** – Tank OK (Sensor nicht ausgelöst)
- **`false`** – Tank leer

Der **Hardware-Monitor** übernimmt den Wert und meldet ihn an die Cloud-API (`liveTelemetry`). Der Status wird **nicht** in MongoDB persistiert, sondern nur live geführt.

*(Details im Backend- und Hardware-Repository.)*

---

## Home-Assistant-Integration

### Binary Sensor „Wassertank leer“

Neuer Binary Sensor pro Gerät: **„… Wassertank leer“** (Entity-Suffix `_watertank`).

| Zustand | Bedeutung |
|---------|-----------|
| **An** (`on`) | Tank leer (Problem) |
| **Aus** (`off`) | Tank OK |
| **Nicht verfügbar** | Noch keine Telemetrie empfangen |

- **Device Class**: `problem` (Home Assistant markiert den Sensor als Problem, wenn er an ist)
- **Icon**: `mdi:water-alert`
- **Verfügbarkeit**: erst nach MQTT-`/info` oder API-`liveTelemetry` mit `watertank`

### Coordinator & Telemetrie

- **`_merge_device_telemetry()`** übernimmt `watertank` aus dem MQTT-Cache oder, falls MQTT fehlt, aus **`liveTelemetry`** der Geräte-API.
- MQTT-`/info`-Nachrichten speichern `watertank` in `device_positions` (Echtzeit).
- Ohne MQTT aktualisiert sich der Sensor beim API-Polling (Standard: 30 s), sobald der Hardware-Monitor Telemetrie liefert.

### Plattform

- Neue Platform **`binary_sensor`** in `PLATFORMS`.
- **`manifest.json`**: Version **0.0.9**.

---

## Migration von v0.0.8

1. **Integration** aktualisieren (HACS oder `custom_components` kopieren).
2. **Home Assistant neu starten**.
3. Pro Gerät erscheint der Binary Sensor **„… Wassertank leer“** automatisch in der Geräteübersicht.
4. Optional: Entity ins Lovelace-Dashboard legen (im README-Beispiel von 0.0.8 noch nicht enthalten).

**Hinweis:** Der Sensor bleibt **grau/unavailable**, bis die erste Telemetrie da ist. Dafür MQTT konfigurieren **oder** Hardware-Monitor mit Cloud-API laufen lassen. Die ESP-Firmware muss `watertank` im Status senden (bestehende Firmware tut das bereits).

---

## Kurzüberblick

| Thema | Inhalt |
|--------|--------|
| ESP | MQTT-Feld `watertank` (`true` = OK, `false` = leer) |
| Cloud | `liveTelemetry.watertank` über Hardware-Monitor (nicht persistiert) |
| HA | Binary Sensor „Wassertank leer“ (`problem`: an = leer) |
| MQTT | Echtzeit aus `/info`; Fallback API-Polling |

---

**Git (nur Integration)**: `v0.0.8...HEAD` – z. B. `git log v0.0.8..HEAD` / `git diff v0.0.8..HEAD`.
