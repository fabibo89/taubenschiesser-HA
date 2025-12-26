# taubenschiesser-HA

Home Assistant Integration für das Taubenschiesser-System.

## Übersicht

Diese Integration verbindet Home Assistant mit dem Taubenschiesser-Backend (`taubenschiesser_AWS`) und ermöglicht die Steuerung und Überwachung von Taubenschiesser-Geräten direkt aus Home Assistant heraus.

## Features

- **Sensoren**: Rotation und Tilt-Werte in Echtzeit
- **Switch**: Start/Pause des Taubenschiesser-Monitors  
- **Buttons**: Steuerung (Links, Rechts, Hoch, Runter, Schießen, Reset)
- **MQTT-Integration**: Echtzeit-Updates über MQTT (optional)
- **Auto-Discovery**: Automatische Erkennung aller konfigurierten Geräte
- **Geräte-Gruppierung**: Alle Entitäten werden korrekt den Geräten zugeordnet
- **Token-Expiry-Handling**: Benutzerfreundliche Meldungen bei abgelaufenen Tokens

## Installation

1. Repository klonen:
   ```bash
   git clone https://github.com/fabibo89/taubenschiesser-HA.git
   ```

2. Integration kopieren:
   ```bash
   cp -r taubenschiesser-HA/custom_components/taubenschiesser /config/custom_components/
   ```

3. Home Assistant neu starten

4. Integration hinzufügen:
   - Einstellungen → Geräte & Dienste → Integration hinzufügen
   - Suche nach "Taubenschiesser"

## Konfiguration

Die Integration wird über die UI konfiguriert. Du benötigst:

### Erforderliche Einstellungen

- **API URL**: Die URL deines Taubenschiesser-Servers
  - **HA in Docker (macOS/Windows)**: `http://host.docker.internal:5001`
  - **HA in Docker (Linux)**: `http://192.168.1.100:5001` (ersetze mit deiner Host-IP)
  - **HA nativ**: `http://localhost:5001`
  - **Im Netzwerk**: `http://192.168.1.100:5001` (ersetze mit deiner Server-IP)
  
  **Wichtig**: Port ist standardmäßig **5001**, kein Slash am Ende! Wenn Home Assistant in Docker läuft, funktioniert `localhost` **nicht**!

- **API Token**: Dein JWT-Token für die API-Authentifizierung
  
  **Methode 1: Aus dem Dashboard (Einfachste Methode)**
  1. Öffne dein Taubenschiesser-Dashboard im Browser
  2. Logge dich ein
  3. Gehe zu **Profil** (oben rechts)
  4. Scrolle zur Sektion **"🔑 API Token (für Home Assistant)"**
  5. Klicke auf das **Auge-Icon** um den Token anzuzeigen
  6. Klicke auf das **Kopieren-Icon** um den Token zu kopieren
  
  **Alternative: Entwicklertools**
  1. Entwicklertools (F12) → Application → Local Storage → 'token'
  2. Kopiere den Wert (langer String, beginnt meist mit `eyJ...`)
  
  **Alternative: Über die API (Terminal)**
  ```bash
  curl -X POST http://localhost:5001/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"deine@email.de","password":"dein-passwort"}'
  ```

### Optionale Einstellungen (MQTT für Echtzeit-Updates)

**Hinweis:** MQTT ist **optional**. Die Integration funktioniert auch ohne MQTT, aber dann gibt es keine Echtzeit-Updates der Gerätepositionen (Rotation, Tilt). Die Daten werden dann nur alle 30 Sekunden über die API abgerufen.

- **MQTT Broker**: 
  - Lokaler Mosquitto: `localhost` oder `host.docker.internal` (wenn HA in Docker)
  - Im Netzwerk: `192.168.1.100` (IP-Adresse deines MQTT-Brokers)
  - Cloud-Service: z.B. `broker.hivemq.com`
  - **Leer lassen**: Wenn du keinen MQTT-Broker hast

- **MQTT Port**: Standard `1883` (unverschlüsselt) oder `8883` (SSL/TLS)
- **MQTT Username/Password**: Optional, leer lassen wenn nicht benötigt

**Beispiele:**
- **Lokaler Mosquitto (ohne Docker)**: Broker: `localhost`, Port: `1883`
- **Lokaler Mosquitto (HA in Docker)**: Broker: `host.docker.internal`, Port: `1883`
- **Ohne MQTT**: Alle Felder leer lassen (empfohlen für Start)

## Voraussetzungen

- Taubenschiesser-Backend (`taubenschiesser_AWS`) muss laufen und erreichbar sein
- Home Assistant 2023.1 oder neuer
- Optional: MQTT-Broker für Echtzeit-Updates (ohne MQTT funktioniert die Integration auch, nur ohne Echtzeit-Updates)

## Wichtige Hinweise

### Docker-Umgebung

Wenn Home Assistant in Docker läuft, funktioniert `localhost` **nicht**! Verwende stattdessen:
- **macOS/Windows**: `host.docker.internal:5001`
- **Linux**: Die IP-Adresse deines Hosts

### API Token

- Der Token ist **7 Tage gültig**
- Bei Ablauf erscheint eine benutzerfreundliche Meldung in Home Assistant
- Neuen Token einfach aus dem Dashboard kopieren und in den Integrationseinstellungen eintragen

## Verwendung

Nach der Konfiguration werden automatisch für jedes Gerät folgende Entities erstellt. Alle Entities werden automatisch dem entsprechenden Gerät zugeordnet und erscheinen gruppiert in der Home Assistant Geräteübersicht.

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

## Rechtliches & Ethik

Dieses Projekt liefert rein technische Integrations- und Überwachungsfunktionen. Die Nutzung muss stets den lokalen Gesetzen, Verordnungen und tierschutzrechtlichen Vorgaben entsprechen. Verwende dieses Repository nicht für rechtswidrige oder nicht tierschutzkonforme Handlungen. Der Betreiber dieses Repositories übernimmt keine Verantwortung für missbräuchliche Nutzung.

## Beitragen

Beiträge sind willkommen — Bugreports, Verbesserungsvorschläge und Pull Requests. Bitte:
- Issues mit einer genauen Fehlerbeschreibung und Reproduktionsschritten öffnen
- Bei Code-Änderungen auf Stil und Tests achten
- Beschreibe in Pull Requests kurz die Motivation und Auswirkungen

## Troubleshooting

### Integration wird nicht gefunden

- Stelle sicher, dass der Ordner `taubenschiesser` (nicht `taubenschiesser_HA`) heißt
- Prüfe, ob alle Dateien vorhanden sind
- Starte Home Assistant neu

### API-Verbindungsfehler

- Prüfe, ob die API-URL korrekt ist (besonders bei Docker: `host.docker.internal` statt `localhost`)
- Stelle sicher, dass der API-Token gültig ist
- Prüfe die Home Assistant Logs für detaillierte Fehlermeldungen

### MQTT-Verbindungsfehler

- Prüfe, ob der MQTT-Broker erreichbar ist
- Stelle sicher, dass Username/Password korrekt sind (falls erforderlich)
- Ohne MQTT funktioniert die Integration auch, aber ohne Echtzeit-Updates

### Keine Geräte gefunden

- Stelle sicher, dass Geräte in der Taubenschiesser-API konfiguriert sind
- Prüfe, ob der API-Token Zugriff auf die Geräte hat
- Prüfe die Home Assistant Logs

## Support

Bei Problemen oder Fragen, erstelle ein Issue im GitHub Repository oder kontaktiere den Maintainer (fabibo89).

## Lizenz

Siehe [LICENSE](LICENSE) Datei für Details.
