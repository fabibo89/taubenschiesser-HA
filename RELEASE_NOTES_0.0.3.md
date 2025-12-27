# Release 0.0.3

**Veröffentlichungsdatum**: 27.12.2025

## 🎉 Neue Features

### 🔐 OAuth2 mit automatischem Token-Refresh
- **Email/Passwort-Authentifizierung**: Kein manueller API-Token mehr nötig - einfach Email und Passwort eingeben
- **Automatische Token-Erneuerung**: Access Tokens werden automatisch erneuert, wenn sie ablaufen (30 Minuten)
- **Refresh Tokens**: Langlebige Refresh Tokens (7 Tage) sorgen für nahtlose Authentifizierung
- **Keine Token-Verwaltung mehr**: Die Integration kümmert sich vollautomatisch um die Token-Verwaltung
- **Verbesserte Sicherheit**: Kurzlebige Access Tokens und automatische Erneuerung nach OAuth2-Best-Practices

### 🆕 Switch-Platform
- **Monitor-Steuerung**: Neuer Switch zum Starten/Pausieren des Taubenschiesser-Monitors
- **Einfache Bedienung**: Monitor-Status kann direkt aus Home Assistant gesteuert werden
- **Zustandssynchronisation**: Switch zeigt immer den aktuellen Monitor-Status an

### 📊 Neue Sensoren

#### "Letzte MQTT Nachricht"
- **Zeitstempel der letzten MQTT-Nachricht**: Zeigt den genauen Zeitpunkt der letzten empfangenen MQTT-Nachricht vom Gerät
- **Geräte-seitiger Zeitstempel**: Verwendet den Zeitstempel direkt vom ESP-Gerät (`timeMQTT`) für maximale Genauigkeit
- **Echtzeit-Updates**: Wird automatisch aktualisiert, sobald neue MQTT-Nachrichten eintreffen

#### "Status"
- **Gesamtstatus des Geräts**: Zeigt den kombinierten Status von Taubenschiesser-Hardware und Kamera
- **Automatische Berechnung**: Status wird dynamisch aus `taubenschiesserStatus` und `cameraStatus` berechnet
- **Status-Werte**: `online`, `offline`, `maintenance`, `error`
- **Immer aktuell**: Status wird bei jedem API-Abruf neu berechnet

### 🌐 Deutsche Übersetzungen
- **Vollständige Lokalisierung**: Alle UI-Elemente und Fehlermeldungen sind jetzt auf Deutsch verfügbar
- **Verbesserte Benutzerführung**: Deutsche Beschreibungen für alle Konfigurationsfelder

## 🐛 Bugfixes

### Status-Anzeige
- **Dynamische Status-Berechnung**: Status wird jetzt immer aktuell berechnet, nicht mehr aus veralteten DB-Werten
- **Korrekter Offline-Status**: Geräte werden jetzt korrekt als offline angezeigt, wenn sie nicht erreichbar sind
- **Keine veralteten Status-Werte mehr**: Status wird bei jedem API-Abruf basierend auf den aktuellen Komponenten-Statusen berechnet

### Config Flow
- **Verbesserte Validierung**: Bessere Fehlerbehandlung bei Konfigurationsfehlern
- **Umgebungsbasierte Vorschläge**: Automatische Erkennung von Docker-Umgebungen mit passenden API-URL-Vorschlägen
- **Detaillierte Fehlermeldungen**: Spezifische Fehlermeldungen für häufige Konfigurationsprobleme

### Token-Handling
- **Korrekte Token-Aktualisierung**: Refresh Tokens werden korrekt gespeichert und verwendet
- **Automatische Token-Erneuerung**: Tokens werden automatisch erneuert, bevor sie ablaufen
- **Verbesserte Fehlerbehandlung**: Bessere Fehlermeldungen bei Token-Problemen

## 🔧 Technische Verbesserungen

### Major Refactor
- **Coordinator-Neuimplementierung**: Komplett neu geschriebener Coordinator mit Unterstützung für API und MQTT
- **Vereinheitlichte Konstanten**: Alle Konstanten sind jetzt in einer Datei zentralisiert
- **Verbesserte Button-Logik**: Restrukturierte Button-Implementierung für bessere Wartbarkeit
- **Code-Bereinigung**: Entfernung veralteter Dateien (`coordinator_old.py`, `update.py`)

### Authentifizierung
- **OAuth2-ähnliches System**: Implementierung eines robusten Token-Systems mit Access- und Refresh-Tokens
- **Token-Typ-Validierung**: Sicherstellung, dass nur Access Tokens für API-Zugriffe verwendet werden
- **Automatische Token-Erneuerung**: Nahtlose Token-Erneuerung ohne Benutzer-Interaktion

### MQTT-Integration
- **timeMQTT-Extraktion**: Zeitstempel aus MQTT-Payload werden jetzt extrahiert und verwendet
- **Erweiterte Gerätedaten**: Mehr Informationen aus MQTT-Nachrichten werden verarbeitet
- **Verbesserte Echtzeit-Updates**: Zuverlässigere MQTT-Verbindung und Datenverarbeitung

### Code-Qualität
- **Entfernung von Legacy-Code**: Alle alten Token-bezogenen Code-Pfade wurden entfernt
- **Konsistente Status-Berechnung**: Status wird überall einheitlich berechnet
- **Verbesserte Fehlerbehandlung**: Robustere Fehlerbehandlung bei API- und Token-Fehlern
- **Bessere Code-Struktur**: Vereinfachte und besser wartbare Code-Organisation

## 📚 Dokumentation

- **Aktualisierte README**: Vollständig überarbeitete und konsolidierte README mit detaillierten Anleitungen
- **Konfigurationsdokumentation**: Neue `KONFIGURATION.md` mit ausführlichen Konfigurationsdetails
- **Klare Installationsanleitung**: Schritt-für-Schritt-Anleitung ohne Token-Verwaltung
- **Troubleshooting**: Aktualisierte Fehlerbehebung für die neue Authentifizierungsmethode
- **Beispiele**: Lovelace UI und Automatisierungsbeispiele hinzugefügt

## 🔄 Breaking Changes

### ⚠️ WICHTIG: Konfiguration muss neu eingerichtet werden

Diese Version verwendet ein neues Authentifizierungssystem. **Bestehende Konfigurationen müssen neu eingerichtet werden:**

1. Integration in Home Assistant entfernen
2. Integration neu hinzufügen
3. **Email und Passwort** eingeben (anstatt API-Token)
4. Optionale MQTT-Einstellungen konfigurieren (falls gewünscht)

**Migration von 0.0.2:**
- Die alte Token-basierte Konfiguration wird nicht mehr unterstützt
- Alle Konfigurationen müssen auf Email/Passwort umgestellt werden
- Keine automatische Migration möglich

**Hinweis**: Die Integration-Version im Manifest wurde von `0.0.2` auf `0.0.3` aktualisiert.

## 🙏 Danke

Vielen Dank an alle, die Feedback gegeben haben und zur Verbesserung dieser Integration beigetragen haben!

---

**Vollständige Changelog**: [Commits seit 0.0.2](https://github.com/fabibo89/taubenschiesser-HA/compare/0.0.2...0.0.3)
