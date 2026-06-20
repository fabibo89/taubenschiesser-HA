# Release 0.0.8 – Änderungen seit v0.0.7

**Veröffentlichungsdatum**: 20.06.2026

Dieses Dokument fasst **alle relevanten Änderungen** seit **v0.0.7** zusammen: neue **Schuss-Einstellungen** in der **Taubenschiesser-Cloud** (Kontext), **ESP-Firmware** und **Anpassungen in dieser Home-Assistant-Integration**.

---

## Verhalten in der Cloud & am ESP

### Konfigurierbare Schuss-Optionen pro Gerät

In der Cloud-Oberfläche (Gerät bearbeiten) sind unter den Taubenschiesser-Einstellungen neu:

- **Laser nutzen** (`shootUseLaser`) – Laser beim Schuss ein/aus (Standard: an)
- **Akustische Signale** (`shootUseAudio`) – Audio-Stack beim Schuss ein/aus (Standard: aus)
- **Laser blinkend** (`shootLaserBlink`) – Laser blinkt statt durchgehend an
- **Blink-Intervall** (`shootLaserBlinkMs`, 20–500 ms)

Diese Werte werden in der Gerätekonfiguration gespeichert und vom **Hardware-Monitor** sowie der **API** beim automatischen Schuss berücksichtigt.

### MQTT-Schussbefehl (ESP)

Der strukturierte Shoot-Befehl enthält jetzt u. a.:

- `useLaser`, `useAudio`
- optional `laserBlink`, `laserBlinkMs`

Zusätzlich unterstützt die **ESP-Firmware** einen MQTT-`config`-Befehl (`useLaserOnShoot`, `useAudioOnShoot`) für persistente Einstellungen auf dem Gerät.

**Voraussetzung für Laser/Audio am ESP**: aktuelle **Taubenschiesser-ESP-Firmware** flashen. Für Audio eine MP3/WAV auf dem Gerät (z. B. `/shoot.mp3` über die ESP-Audio-Seite).

*(Details im Backend- und Hardware-Repository.)*

---

## Home-Assistant-Integration

### Neue Switches pro Gerät

| Switch | Entity-Suffix | Funktion |
|--------|---------------|----------|
| **Laser** | `_laser` | Laser manuell an/aus (MQTT `type: laser`) |
| **Schuss: Laser nutzen** | `_shoot_use_laser` | Schuss-Laser in Cloud speichern + optional an ESP syncen |
| **Schuss: Akustische Signale** | `_shoot_use_audio` | Audio beim Schuss in Cloud speichern + optional an ESP syncen |
| **Schuss: Laser blinkt** | `_shoot_laser_blink` | Blink-Modus in Cloud speichern (cloud-persistent, nicht nur Session) |

Bestehende Switches **Monitor** und **Armed** bleiben unverändert.

### Button „Schießen“

- Nutzt zentrale Methode **`build_shoot_command()`** im Coordinator.
- Berücksichtigt **`shootingTimeMs`**, **`shootUseLaser`**, **`shootUseAudio`**, **`shootLaserBlink`** und **`shootLaserBlinkMs`** aus den Cloud-Gerätedaten.
- Sendet das vollständige MQTT-Objekt an den ESP (nicht nur `duration`).

### Coordinator & API

- **`build_shoot_command(taubenschiesser)`** – einheitlicher Shoot-Payload für Button und künftige Aufrufer.
- **`send_api_update_taubenschiesser(device_id, fields)`** – Geräteeinstellungen per `PUT /api/devices/{id}` aktualisieren (für die neuen Schuss-Switches).
- **`send_esp_device_config(device_ip, …)`** – Laser-/Audio-Defaults per MQTT `type: config` an den ESP (wenn MQTT verbunden).

### MQTT-Status

- Laser-Zustand (`laser`) aus MQTT-`/info`-Nachrichten wird im Coordinator übernommen (für den **Laser**-Switch).

### Metadaten

- **`manifest.json`**: Version **0.0.8**.

---

## Migration von v0.0.7

1. **Taubenschiesser-Cloud / Backend** aktualisieren (Schuss-Felder am Gerät).
2. **ESP-Firmware** aktualisieren, wenn Laser/Audio-Schuss genutzt werden soll.
3. **Integration** aktualisieren (HACS oder `custom_components` kopieren).
4. **Home Assistant neu starten**.
5. Pro Gerät erscheinen die **neuen Switches** automatisch (Laser, Schuss: Laser nutzen, Schuss: Akustische Signale, Schuss: Laser blinkt).
6. Optional: Schuss-Optionen in der **Cloud-App** oder direkt in **HA** setzen.

**Hinweis:** Bestehende Geräte ohne explizite Werte nutzen die Defaults: Laser an, Audio aus, kein Blinken.

---

## Kurzüberblick

| Thema | Inhalt |
|--------|--------|
| Cloud | `shootUseLaser`, `shootUseAudio`, `shootLaserBlink`, `shootLaserBlinkMs` pro Gerät |
| ESP | Shoot mit `useLaser`/`useAudio`; optional `config`-MQTT; Audio aus SPIFFS |
| HA | 4 neue/erweiterte Switches; Schuss-Button mit vollem Payload |
| API | `PUT /api/devices` für Schuss-Einstellungen aus HA |
| MQTT | Laser-Status + Config-Sync + strukturierter Shoot-Befehl |

---

**Git (nur Integration)**: `v0.0.7...HEAD` – z. B. `git log v0.0.7..HEAD` / `git diff v0.0.7..HEAD`.
