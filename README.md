# taubenschiesser-HA

Kurzbeschreibung
----------------
taubenschiesser-HA ist eine Home Assistant Integration zur Anbindung und Überwachung eines Tauben‑Abwehrsystems. Die Integration ermöglicht das Abrufen von Statusinformationen, das Auslösen von Aktionen über Home Assistant und das Einbinden in Automatisierungen.

Wichtig: Rechtliches & Ethik
---------------------------
Dieses Projekt liefert rein technische Integrations‑ und Überwachungsfunktionen. Die Nutzung muss stets den lokalen Gesetzen, Verordnungen und tierschutzrechtlichen Vorgaben entsprechen. Verwende dieses Repository nicht für rechtswidrige oder nicht tierschutzkonforme Handlungen. Der Betreiber dieses Repositories übernimmt keine Verantwortung für missbräuchliche Nutzung.

Features
--------
- Einbinden des Tauben‑Abwehrsystems in Home Assistant als Integration
- Anzeige von System‑Status, Sensordaten und Ereignissen
- Auslösen von Aktionen (z. B. Übermittlung eines Befehls an das System) via Home Assistant
- Beispiele für Automatisierungen und Notifications
- Platz für Erweiterungen (Integrationen, Templates, Skripte)

Installation (kurz)
-------------------
1. Repository klonen:
   ```
   git clone https://github.com/fabibo89/taubenschiesser-HA.git
   ```
2. Dateien der Integration in dein Home Assistant Verzeichnis kopieren (z. B. `custom_components/taubenschiesser`)
3. Home Assistant neu starten und die Integration über die Integrations‑Übersicht oder YAML konfigurieren.

Konfiguration (allgemein)
-------------------------
- Die Integration wird als Custom Component ausgeliefert (z. B. `custom_components/taubenschiesser`).
- Konfiguration erfolgt über YAML oder über die Integrations‑UI (sofern implementiert).
- Sensible Zugangsdaten (API‑Keys, Zugangspasswörter) sicher verwalten (z. B. Secrets).
- Beispiel‑Konfigurationsplatzhalter:
  ```yaml
  taubenschiesser:
    host: "192.168.x.x"
    port: 1234
    api_key: !secret taubenschiesser_api_key
  ```

Benutzung
--------
- Nach der Installation werden Sensoren und Entitäten in Home Assistant verfügbar.
- Erstelle Automatisierungen basierend auf Status‑Entitäten (z. B. Alarm, Betriebszustand).
- Verwende Benachrichtigungen, um bei bestimmten Ereignissen informiert zu werden.

Sicherheit & Verantwortung
--------------------------
- Stelle sicher, dass alle Steuerungsbefehle autorisiert und dokumentiert sind.
- Prüfe bevor du Aktionen in das reale System sendest, dass die Ausführung rechtlich und ethisch zulässig ist.
- Nutze Logging und Rückmeldung (Feedback) aus dem System, um unbeabsichtigte Aktionen zu vermeiden.

Beitragen
---------
Beiträge sind willkommen — Bugreports, Verbesserungsvorschläge und Pull Requests. Bitte:
- Issues mit einer genauen Fehlerbeschreibung und Reproduktionsschritten öffnen.
- Bei Code‑Änderungen auf Stil und Tests achten.
- Beschreibe in Pull Requests kurz die Motivation und Auswirkungen.

Lizenz
------
Wähle eine passende Lizenz (z. B. MIT) oder trage hier die gewünschte Lizenz ein.

Support
-------
Für Fragen oder Probleme öffne bitte ein Issue im Repository oder kontaktiere den Maintainer (fabibo89).
