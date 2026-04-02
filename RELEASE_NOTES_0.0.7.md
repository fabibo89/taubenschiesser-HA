# Release 0.0.7

**Veröffentlichungsdatum**: 06.03.2026

## 🎉 Neue Features

### ⏱️ Dynamischer Timer bis „Max Time“ (zwischen Bewegungen)

- **Max Time pro Gerät**: Die bestehende Einstellung `waitBetweenMovesSeconds` wird als **Maximum** interpretiert.
- **Dynamisches Verhalten**:
  - **Taube erkannt** → Wartezeit wird auf **0s** gesetzt (nächste Position sofort).
  - **Keine Taube erkannt** → Wartezeit erhöht sich **schrittweise (+1s)** bis zum Maximum.
  - **Maximum erreicht** → Gerät **bleibt stehen** und analysiert weiter, bis wieder eine Taube erkannt wird.

### 📡 Zusätzliche Monitor-Attribute in Home Assistant

Home Assistant zeigt (als Entity-Attribute) zusätzliche Werte aus dem Hardware-Monitor an:

- **`dynamic_threshold`**: aktueller dynamischer Wait-Wert (Sekunden)
- **`max_threshold`**: konfiguriertes Maximum (Sekunden)
- **`holding`**: `true`, wenn das Gerät beim Maximum stehen bleibt und weiter analysiert

## 🔧 Technische Verbesserungen

### Persistierte Hardware-Monitor-Events (für Poll-Clients)

- Der zuletzt empfangene Hardware-Monitor-Status wird serverseitig am Device gespeichert (`hardwareMonitor.lastEvent*`).
- Dadurch können Poll-basierte Clients (wie HA via `/api/devices`) die aktuellen Monitor-Werte zuverlässig auslesen.

## 📋 Kompatibilität / Hinweise

- **Backend erforderlich**: Für die neuen Attribute (`dynamic_threshold`, `max_threshold`, `holding`) muss die Taubenschiesser-Cloud/Backend-Version die Persistierung von Monitor-Events unterstützen.
- **Keine Breaking Changes**: Bestehende Entities bleiben erhalten; es kommen nur zusätzliche Attribute hinzu.

## 🔄 Migration von 0.0.6

1. **Integration aktualisieren**: Über HACS oder manuell aktualisieren.
2. **Home Assistant neu starten**.
3. Optional: In der Cloud die **Max Time** (ehemals „Wartezeit zwischen Bewegungen“) pro Gerät passend einstellen.

---

**Changelog (high level)**:
- Dynamische Wait-Logik bis Max Time im Hardware-Monitor
- Zusätzliche Monitor-Attribute in HA (dynamic/max/holding)

