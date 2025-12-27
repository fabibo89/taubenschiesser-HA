# Taubenschiesser Home Assistant Integration

Home Assistant Custom Component für die Steuerung von Taubenschiesser-Geräten.

## Features

- **Sensoren**: Rotation und Tilt-Werte in Echtzeit
- **Switch**: Start/Pause des Taubenschiesser-Monitors
- **Buttons**: Steuerung (Links, Rechts, Hoch, Runter, Schießen, Reset)
- **MQTT-Integration**: Echtzeit-Updates über MQTT (optional)
- **Auto-Discovery**: Automatische Erkennung aller konfigurierten Geräte

## Installation

1. Kopiere den `taubenschiesser_HA` Ordner in dein Home Assistant `custom_components` Verzeichnis:
   ```
   /config/custom_components/taubenschiesser_HA/
   ```

2. Starte Home Assistant neu

3. Gehe zu **Einstellungen** → **Geräte & Dienste** → **Integration hinzufügen**

4. Suche nach **"Taubenschiesser"** und füge die Integration hinzu

## Konfiguration

### Erforderliche Einstellungen

- **API URL**: Die URL deines Taubenschiesser-Servers (z.B. `http://localhost:5001`)
- **Email**: Deine E-Mail-Adresse für die Anmeldung am Taubenschiesser-Server
- **Passwort**: Dein Passwort für die Anmeldung

Die Integration verwendet OAuth2 mit automatischem Token-Refresh. Nach der Eingabe von Email und Passwort werden die Tokens automatisch gespeichert und bei Bedarf erneuert. Du musst dich nicht mehr um Token-Verwaltung kümmern!

### Optionale Einstellungen (für MQTT-Echtzeit-Updates)

**Hinweis:** MQTT ist **optional**. Die Integration funktioniert auch ohne MQTT, aber dann gibt es keine Echtzeit-Updates der Gerätepositionen (Rotation, Tilt). Die Daten werden dann nur alle 30 Sekunden über die API abgerufen.

**MQTT-Konfiguration:**

- **MQTT Broker**: 
  - **Lokaler Mosquitto (Standard)**: `localhost` oder `host.docker.internal` (wenn HA in Docker)
  - **Im Netzwerk**: `192.168.1.100` (IP-Adresse deines MQTT-Brokers)
  - **Cloud-Service**: z.B. `broker.hivemq.com` (HiveMQ Cloud)
  - **Leer lassen**: Wenn du keinen MQTT-Broker hast oder verwenden möchtest

- **MQTT Port**: 
  - **Standard**: `1883` (unverschlüsselt)
  - **SSL/TLS**: `8883` (für Cloud-Services)

- **MQTT Username**: Benutzername für MQTT (optional, leer lassen wenn nicht benötigt)
- **MQTT Password**: Passwort für MQTT (optional, leer lassen wenn nicht benötigt)

**Beispiele:**

1. **Lokaler Mosquitto (ohne Docker)**: 
   - Broker: `localhost`
   - Port: `1883`
   - Username/Password: leer

2. **Lokaler Mosquitto (HA in Docker)**: 
   - Broker: `host.docker.internal` oder `192.168.1.100` (Host-IP)
   - Port: `1883`
   - Username/Password: leer

3. **Ohne MQTT (empfohlen für Start)**: 
   - Alle Felder leer lassen
   - Integration funktioniert trotzdem, nur ohne Echtzeit-Updates

### API URL

Die API-URL ist die Adresse deines Taubenschiesser-Servers:

- **Home Assistant in Docker (macOS/Windows)**: `http://host.docker.internal:5001`
- **Home Assistant in Docker (Linux)**: `http://192.168.1.100:5001` (ersetze mit deiner Host-IP)
- **Home Assistant nativ (ohne Docker)**: `http://localhost:5001`
- **Im Netzwerk**: `http://192.168.1.100:5001` (ersetze mit deiner Server-IP)
- **Mit Hostname**: `http://casahosch:5001` (ersetze mit deinem Hostname)

**Wichtig**: 
- Port ist standardmäßig **5001**, kein Slash am Ende!
- **Wenn Home Assistant in Docker läuft**, funktioniert `localhost` **nicht**! Verwende stattdessen:
  - macOS/Windows: `host.docker.internal:5001`
  - Linux: Die IP-Adresse deines Hosts (finde mit `hostname -I` oder `ip addr`)

### Authentifizierung

Die Integration verwendet **OAuth2 mit automatischem Token-Refresh**:

- Gib einfach deine **Email** und dein **Passwort** ein
- Die Integration holt automatisch die erforderlichen Tokens
- Access Tokens werden automatisch erneuert, wenn sie ablaufen (30 Minuten)
- Refresh Tokens sind 7 Tage gültig
- **Keine manuelle Token-Verwaltung mehr nötig!**

## Verwendung

Nach der Konfiguration werden automatisch für jedes Gerät folgende Entities erstellt:

### Sensoren

- `sensor.taubenschiesser_<name>_rotation` - Aktuelle Rotation in Grad (0-360°)
- `sensor.taubenschiesser_<name>_tilt` - Aktueller Tilt in Grad (-180° bis 180°)

### Switch

- `switch.taubenschiesser_<name>_monitor` - Start/Pause des Monitors

### Buttons

- `button.taubenschiesser_<name>_links` - Nach links drehen
- `button.taubenschiesser_<name>_rechts` - Nach rechts drehen
- `button.taubenschiesser_<name>_hoch` - Nach oben bewegen
- `button.taubenschiesser_<name>_runter` - Nach unten bewegen
- `button.taubenschiesser_<name>_schießen` - Schießen
- `button.taubenschiesser_<name>_reset` - Reset

## Lovelace UI Beispiel

```yaml
type: vertical-stack
cards:
  - type: entities
    title: Taubenschiesser Status
    entities:
      - sensor.taubenschiesser_gerät1_rotation
      - sensor.taubenschiesser_gerät1_tilt
      - switch.taubenschiesser_gerät1_monitor
  
  - type: grid
    columns: 3
    square: false
    cards:
      - type: button
        entity: button.taubenschiesser_gerät1_links
        icon: mdi:arrow-left
      - type: button
        entity: button.taubenschiesser_gerät1_hoch
        icon: mdi:arrow-up
      - type: button
        entity: button.taubenschiesser_gerät1_schießen
        icon: mdi:target
      - type: button
        entity: button.taubenschiesser_gerät1_rechts
        icon: mdi:arrow-right
      - type: button
        entity: button.taubenschiesser_gerät1_runter
        icon: mdi:arrow-down
      - type: button
        entity: button.taubenschiesser_gerät1_reset
        icon: mdi:restore
```

## Automatisierungen

### Beispiel: Automatisches Pausieren bei Sonnenuntergang

```yaml
automation:
  - alias: "Taubenschiesser bei Sonnenuntergang pausieren"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: switch.turn_off
        entity_id: switch.taubenschiesser_gerät1_monitor
```

### Beispiel: Rotation überwachen

```yaml
automation:
  - alias: "Taubenschiesser Rotation Warnung"
    trigger:
      - platform: numeric_state
        entity_id: sensor.taubenschiesser_gerät1_rotation
        above: 350
    action:
      - service: notify.mobile_app_iphone
        data:
          message: "Taubenschiesser Rotation bei {{ states('sensor.taubenschiesser_gerät1_rotation') }}°"
```

## Troubleshooting

### Integration wird nicht gefunden

- Stelle sicher, dass der Ordner `taubenschiesser_HA` (nicht `taubenschiesser_HA`) heißt
- Prüfe, ob alle Dateien vorhanden sind
- Starte Home Assistant neu

### API-Verbindungsfehler

- Prüfe, ob die API-URL korrekt ist
- Stelle sicher, dass Email und Passwort korrekt sind
- Prüfe die Home Assistant Logs für detaillierte Fehlermeldungen

### MQTT-Verbindungsfehler

- Prüfe, ob der MQTT-Broker erreichbar ist
- Stelle sicher, dass Username/Password korrekt sind (falls erforderlich)
- Ohne MQTT funktioniert die Integration auch, aber ohne Echtzeit-Updates

### Keine Geräte gefunden

- Stelle sicher, dass Geräte in der Taubenschiesser-API konfiguriert sind
- Prüfe, ob der Benutzer-Zugriff auf die Geräte hat
- Prüfe die Home Assistant Logs

## Support

Bei Problemen oder Fragen, erstelle ein Issue im GitHub Repository.

