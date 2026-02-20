# Release 0.0.4

**Veröffentlichungsdatum**: 16.01.2026

## 🎉 Neue Features

### 📊 Neue Erkennungs-Zählsensoren

#### "Erkennungen heute"
- **Tägliche Erkennungsstatistik**: Zeigt die Anzahl der heute erkannten Tauben/Vögel
- **Echtzeit-Updates**: Wird automatisch aktualisiert, sobald neue Erkennungen eintreffen
- **Korrekte Datumslogik**: Zählt alle Erkennungen ab Mitternacht des aktuellen Tages
- **Einheit "Erkennungen"**: Sensor zeigt explizit die Anzahl der Erkennungen

#### "Erkennungen gestern"
- **Vergleichsstatistik**: Zeigt die Anzahl der gestern erkannten Tauben/Vögel
- **Tagesvergleich**: Ermöglicht einfachen Vergleich zwischen heute und gestern
- **Statistische Auswertung**: Unterstützt Trend-Analysen und Aktivitätsmuster
- **Konsistente Datumslogik**: Verwendet dieselbe Berechnungslogik wie der "heute"-Sensor

### 🔧 Technische Verbesserungen

- **Erweiterte Sensor-Plattform**: Zwei neue Sensoren wurden zur Integration hinzugefügt
- **Verbesserte Datenstruktur**: Nutzung der `detectionCounts`-Struktur aus der API
- **Konsistente Implementierung**: Neue Sensoren folgen dem gleichen Muster wie bestehende Sensoren

## 🔄 Versionierung

Diese Version markiert den Übergang von `0.0.3` zu `1.0.0` und signalisiert:
- **Stabilität**: Die Integration hat einen stabilen Funktionsumfang erreicht
- **Produktionsreife**: Vollständig funktionsfähige Integration mit allen Kernfeatures
- **API-Kompatibilität**: Nutzung der erweiterten API-Funktionalität für Erkennungsstatistiken

## 📋 Kompatibilität

- **Keine Breaking Changes**: Diese Version ist vollständig kompatibel mit Version 0.0.3
- **Automatische Aktualisierung**: Bestehende Konfigurationen funktionieren ohne Änderungen
- **Neue Sensoren**: Neue Sensoren werden automatisch bei der nächsten Aktualisierung hinzugefügt

## 🔍 Verwendung

Die neuen Sensoren sind nach dem Update automatisch verfügbar:
- `sensor.taubenschiesser_erkennungen_heute` - Anzahl der heutigen Erkennungen
- `sensor.taubenschiesser_erkennungen_gestern` - Anzahl der gestrigen Erkennungen

Die Sensoren können in Automatisierungen, Dashboards und Statistiken verwendet werden.

## 🙏 Danke

Vielen Dank an alle, die Feedback gegeben haben und zur Verbesserung dieser Integration beigetragen haben!

---

**Vollständige Changelog**: [Commits seit 0.0.3](https://github.com/fabibo89/taubenschiesser-HA/compare/0.0.3...1.0.0)

