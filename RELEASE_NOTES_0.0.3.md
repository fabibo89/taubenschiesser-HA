# Release 0.0.3

**Veröffentlichungsdatum**: 26. Dezember 2025

## 🎉 Neue Features

### 🔑 Token-Verwaltung im Dashboard
- **API Token direkt im Profil anzeigen**: Token kann jetzt einfach aus dem Dashboard-Profil kopiert werden
- **Token-Sichtbarkeit umschalten**: Token kann ein- und ausgeblendet werden
- **Ein-Klick-Kopieren**: Token wird mit einem Klick in die Zwischenablage kopiert

### 📱 Verbesserte Konfigurations-UI
- **Detaillierte Feldbeschreibungen**: Alle Eingabefelder haben jetzt ausführliche Erklärungen und Beispiele
- **Docker-spezifische Hinweise**: Automatische Erkennung und Hinweise für Docker-Umgebungen
- **Vorgeschlagene API-URL**: Intelligente Vorschläge basierend auf der Umgebung (Docker vs. nativ)

### 🏷️ Geräte-Gruppierung
- **Automatische Geräte-Zuordnung**: Alle Entities werden jetzt korrekt ihren Geräten zugeordnet
- **Geräte-Informationen**: Vollständige Geräte-Metadaten (Name, Hersteller, Modell, Konfigurations-URL)
- **Bessere Übersicht**: Entities erscheinen gruppiert in der Home Assistant Geräteübersicht

## 🐛 Bugfixes

### Token-Expiry-Handling
- **Benutzerfreundliche Fehlermeldungen**: Bei abgelaufenen Tokens erscheint eine hilfreiche Meldung mit Anleitung
- **Persistente Benachrichtigungen**: Token-Ablauf wird als persistente Benachrichtigung angezeigt
- **Automatische Benachrichtigungs-Verwaltung**: Benachrichtigung verschwindet automatisch nach Token-Erneuerung

### Docker-Kompatibilität
- **Verbesserte Fehlerbehandlung**: Spezifische Fehlermeldungen für `localhost`-Probleme in Docker
- **Hilfreiche Hinweise**: Automatische Erkennung von Docker-Umgebungen mit konkreten Lösungsvorschlägen

## 📚 Dokumentation

- **Aktualisierte README**: Vollständig überarbeitete README mit allen aktuellen Features
- **Detaillierte Konfigurationsanleitung**: Schritt-für-Schritt-Anleitung für alle Szenarien
- **Troubleshooting-Sektion**: Umfassende Fehlerbehebung mit häufigen Problemen und Lösungen
- **Beispiele**: Lovelace UI und Automatisierungsbeispiele hinzugefügt

## 🔧 Technische Verbesserungen

- **Service-basierte Notifications**: Umstellung auf Home Assistant Service-API für bessere Kompatibilität
- **Internationalisierung**: Deutsche Übersetzungen für alle UI-Elemente
- **Code-Qualität**: Verbesserte Fehlerbehandlung und Logging

## 📋 Migration von 0.0.2

Keine Breaking Changes! Die Integration kann einfach aktualisiert werden:

1. Neue Version herunterladen
2. Alte Version ersetzen
3. Home Assistant neu starten
4. Optional: Integration neu konfigurieren, um von den neuen Features zu profitieren

## 🙏 Danke

Vielen Dank an alle, die Feedback gegeben haben und zur Verbesserung dieser Integration beigetragen haben!

---

**Vollständige Changelog**: [Commits seit 0.0.2](https://github.com/fabibo89/taubenschiesser-HA/compare/0.0.2...main)



