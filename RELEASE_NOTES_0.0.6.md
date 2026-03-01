# Release 0.0.6

**Veröffentlichungsdatum**: 01.03.2025

## 🎉 Neue Features

### 🔫 Switch „Armed“ (Schießen bei Erkennung)

#### Neuer Switch „Armed“ pro Gerät
- **Schießen bei Erkennung**: Steuert, ob bei einer Taubenerkennung geschossen wird (an) oder nur die Erkennung gespeichert wird (aus)
- **Synchron mit der Cloud**: Zustand wird aus der API gelesen und Änderungen in HA werden per API (`PATCH …/arm`) an die Taubenschiesser-Cloud gesendet
- **Anzeige in HA**: Pro Gerät erscheint neben dem bestehenden „Monitor“-Switch ein weiterer Switch „Armed“ (z. B. „Taubenschiesser West Armed“)
- **Hardware-Monitor**: Der Monitor nutzt den gleichen `monitorArmed`-Wert – Scharfstellung in HA und in der Cloud-Oberfläche bleiben synchron

### 📡 WLAN-Signal-Sensor

#### Neuer Sensor „WLAN-Signal“
- **Signalstärke in dBm**: Zeigt die WLAN-Empfangsqualität des Geräts (sofern vom Gerät gesendet)
- **Aus API und MQTT**: Wert wird aus den Gerätedaten sowie aus MQTT-Position-Updates übernommen
- **Device Class**: Verwendet `SensorDeviceClass.SIGNAL_STRENGTH` für einheitliche Darstellung in Home Assistant
- **Icon**: mdi:wifi

### 📦 HACS-Installation

#### Vollständige HACS-Unterstützung
- **Installation über HACS**: Die Integration kann jetzt zuverlässig über den HACS (Home Assistant Community Store) installiert und aktualisiert werden
- **hacs.json hinzugefügt**: Repositories-Manifest im Repository-Root erfüllt die HACS v2-Anforderungen
- **Keine Fehlermeldung mehr**: Der Fehler „The version … for this integration can not be used with HACS“ tritt bei korrekter Release-Versionierung nicht mehr auf

#### Einfache Installation
- **Custom Repository**: Repo in HACS unter „Custom repositories“ hinzufügen und die Integration wie gewohnt installieren
- **Updates über HACS**: Neue Versionen werden in HACS angezeigt und können mit einem Klick installiert werden

## 🔧 Technische Verbesserungen

### Switches
- **Neue API-Methode**: `send_api_arm(device_id, armed)` im Coordinator für Scharfstellung
- **Switch-Plattform**: Zwei Switches pro Gerät (Monitor, Armed) über gemeinsame Klasse mit `switch_kind`

### Sensoren
- **„Letzte MQTT Nachricht“**: Zeigt jetzt die Sekunden seit der letzten MQTT-Nachricht (Integer) statt eines Zeitstempels – besser für Verlaufsdiagramme und Statistiken
- **State Class**: „Letzte MQTT Nachricht“ nutzt `SensorStateClass.MEASUREMENT` für korrekte Auswertung in HA

### Coordinator / MQTT
- **MQTT-Debounce**: Bei eingehenden MQTT-Nachrichten (z. B. jede Sekunde vom ESP) wird die Aktualisierung der Entities nur noch nach 3 Sekunden Ruhe ausgelöst (Debounce). Der 30-Sekunden-API-Refresh kann so wieder zuverlässig laufen – der Switch „Armed“ und andere API-Werte (z. B. Scharfstellung aus der Cloud) aktualisieren sich ohne Reload.
- **Stabilerer Coordinator**: Nach dem Debounce wird `async_set_updated_data` korrekt mit `await` aufgerufen.

### Metadaten & Repository
- **Manifest**: Dokumentations- und Issue-Tracker-Links zeigen auf `github.com/fabibo89/taubenschiesser`
- **Codeowner**: Maintainer in `manifest.json` auf @fabibo89 gesetzt
- **Version**: 0.0.6 in `manifest.json` für HACS-konforme Releases

## 📋 Kompatibilität

- **Keine Breaking Changes**: Diese Version ist vollständig kompatibel mit Version 0.0.5
- **Bestehende Installationen**: Manuelle Installationen (ohne HACS) funktionieren weiterhin unverändert
- **Neuer Switch „Armed“**: Pro Gerät erscheint nach dem Update ein weiterer Switch; Zustand wird aus der API übernommen und bleibt mit der Cloud synchron (auch bei Änderung in der App)
- **Neuer Sensor**: „WLAN-Signal“ erscheint automatisch, sobald das Gerät WiFi-Daten sendet
- **„Letzte MQTT Nachricht“**: Anzeige wechselt von Zeitstempel zu Sekunden – Automatisierungen/Dashboards, die den alten Wert nutzen, ggf. anpassen

## 🔄 Migration von 0.0.5

### Für alle Nutzer

1. **Integration aktualisieren**: Über HACS aktualisieren oder die neue Version in dein `custom_components` Verzeichnis kopieren
2. **Home Assistant neu starten**: Starte Home Assistant neu, damit die Änderungen geladen werden
3. **Fertig**: Keine weiteren Schritte nötig

### Für HACS-Nutzer (ab diesem Release)

- Repo als Custom Repository in HACS hinzufügen (falls noch nicht geschehen)
- Integration über HACS installieren oder auf 0.0.6 aktualisieren
- Zukünftige Updates erscheinen in HACS und können dort installiert werden

## 🙏 Danke

Vielen Dank an alle, die Feedback gegeben haben und zur Verbesserung dieser Integration beigetragen haben!

---

**Vollständige Changelog**: [Commits seit 0.0.5](https://github.com/fabibo89/taubenschiesser-HA/compare/0.0.5...0.0.6)
