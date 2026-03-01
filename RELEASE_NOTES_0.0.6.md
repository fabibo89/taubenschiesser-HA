# Release 0.0.6

**Veröffentlichungsdatum**: 01.03.2025

## 🎉 Neue Features

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

### Sensoren
- **„Letzte MQTT Nachricht“**: Zeigt jetzt die Sekunden seit der letzten MQTT-Nachricht (Integer) statt eines Zeitstempels – besser für Verlaufsdiagramme und Statistiken
- **State Class**: „Letzte MQTT Nachricht“ nutzt `SensorStateClass.MEASUREMENT` für korrekte Auswertung in HA

### Metadaten & Repository
- **Manifest**: Dokumentations- und Issue-Tracker-Links zeigen auf `github.com/fabibo89/taubenschiesser`
- **Codeowner**: Maintainer in `manifest.json` auf @fabibo89 gesetzt
- **Version**: 0.0.6 in `manifest.json` für HACS-konforme Releases

## 📋 Kompatibilität

- **Keine Breaking Changes**: Diese Version ist vollständig kompatibel mit Version 0.0.5
- **Bestehende Installationen**: Manuelle Installationen (ohne HACS) funktionieren weiterhin unverändert
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
