# Release 0.0.5

**Veröffentlichungsdatum**: 16.01.2026

## 🎉 Neue Features

### 🔐 Automatische Re-Authentifizierung

#### Vollautomatische Token-Erneuerung
- **Keine manuelle Neu-Konfiguration mehr**: Wenn der Refresh Token abgelaufen ist (nach 7 Tagen), wird die Integration automatisch mit gespeicherten Anmeldedaten neu authentifiziert
- **Nahtlose Funktionalität**: Die Integration funktioniert weiter, ohne dass der Benutzer eingreifen muss
- **Automatische Token-Aktualisierung**: Neue Access- und Refresh-Tokens werden automatisch gespeichert
- **Intelligente Fehlerbehandlung**: Erkennt abgelaufene Refresh Tokens und startet automatisch die Re-Authentifizierung

#### Verbesserte Benutzererfahrung
- **Keine Unterbrechungen**: Die Integration bleibt auch nach Ablauf des Refresh Tokens funktionsfähig
- **Automatische Benachrichtigungen**: Benutzer werden nur benachrichtigt, wenn die automatische Re-Authentifizierung fehlschlägt
- **Transparente Token-Verwaltung**: Alle Token-Operationen laufen im Hintergrund ab

## 🔧 Technische Verbesserungen

### Authentifizierung
- **Erweiterte Token-Verwaltung**: Passwort wird jetzt sicher in der Config Entry gespeichert (für automatische Re-Authentifizierung)
- **Neue Re-Authentifizierungs-Methode**: `_reauthenticate()` Methode wurde hinzugefügt, die automatisch neue Tokens anfordert
- **Intelligente Token-Erkennung**: Erkennt automatisch, wenn ein Refresh Token abgelaufen ist (HTTP 401 mit "Refresh token expired")
- **Robuste Fehlerbehandlung**: Verbesserte Fehlerbehandlung bei Token-Problemen mit klaren Fehlermeldungen

### Code-Qualität
- **Konsistente Implementierung**: Re-Authentifizierung folgt dem gleichen Muster wie Token-Refresh
- **Verbesserte Logging**: Detailliertere Log-Nachrichten für Debugging und Monitoring
- **Code-Duplikation reduziert**: Beide Versionen (GitHub und Docker) wurden synchronisiert

## 🐛 Bugfixes

### Token-Expiry-Handling
- **Behoben**: "Refresh token expired" Fehler führt nicht mehr zu dauerhaften Einrichtungsfehlern
- **Behoben**: Integration versucht automatisch, sich neu zu authentifizieren, wenn der Refresh Token abgelaufen ist
- **Verbessert**: Klarere Fehlermeldungen, wenn Re-Authentifizierung fehlschlägt (z.B. wenn Passwort nicht gespeichert ist)

## 📋 Kompatibilität

### ⚠️ WICHTIG: Einmalige Neu-Konfiguration empfohlen

**Für bestehende Installationen (vor 0.0.5):**
- Das Passwort wurde bisher nicht in der Config Entry gespeichert
- **Empfehlung**: Integration einmal neu konfigurieren, damit das Passwort gespeichert wird
- **Alternativ**: Warten, bis der Refresh Token abläuft - dann wird eine Neu-Konfiguration erforderlich sein

**Für neue Installationen (ab 0.0.5):**
- Passwort wird automatisch bei der ersten Konfiguration gespeichert
- Automatische Re-Authentifizierung funktioniert sofort nach der ersten Konfiguration

### Keine Breaking Changes
- **Vollständig kompatibel**: Diese Version ist vollständig kompatibel mit Version 0.0.4
- **Automatische Aktualisierung**: Bestehende Konfigurationen funktionieren ohne Änderungen
- **Optionale Verbesserung**: Neu-Konfiguration ist optional, aber empfohlen für bestehende Installationen

## 🔍 Verwendung

Die automatische Re-Authentifizierung funktioniert vollautomatisch im Hintergrund:

1. **Bei der ersten Konfiguration**: Email und Passwort werden eingegeben und gespeichert
2. **Während des Betriebs**: Access Tokens werden automatisch erneuert (alle 30 Minuten)
3. **Nach 7 Tagen**: Wenn der Refresh Token abläuft, wird automatisch eine neue Anmeldung durchgeführt
4. **Keine Benutzer-Interaktion nötig**: Alles läuft automatisch ab

**Hinweis**: Falls die automatische Re-Authentifizierung fehlschlägt (z.B. wenn das Passwort geändert wurde), wird eine Fehlermeldung angezeigt und die Integration muss manuell neu konfiguriert werden.

## 🔄 Migration von 0.0.4

### Empfohlene Schritte

1. **Integration aktualisieren**: Kopiere die neue Version in dein `custom_components` Verzeichnis
2. **Home Assistant neu starten**: Starte Home Assistant neu, damit die Änderungen geladen werden
3. **Integration neu konfigurieren** (empfohlen):
   - Gehe zu: Einstellungen → Geräte & Dienste → Taubenschiesser → Konfigurieren
   - Email und Passwort erneut eingeben
   - Dies speichert das Passwort für die automatische Re-Authentifizierung
4. **Fertig**: Die Integration funktioniert jetzt mit automatischer Re-Authentifizierung

### Alternative (ohne Neu-Konfiguration)

- Die Integration funktioniert weiterhin wie bisher
- Wenn der Refresh Token nach 7 Tagen abläuft, muss die Integration dann neu konfiguriert werden
- Danach funktioniert die automatische Re-Authentifizierung

## 🙏 Danke

Vielen Dank an alle, die Feedback gegeben haben und zur Verbesserung dieser Integration beigetragen haben!

---

**Vollständige Changelog**: [Commits seit 0.0.4](https://github.com/fabibo89/taubenschiesser-HA/compare/0.0.4...0.0.5)

