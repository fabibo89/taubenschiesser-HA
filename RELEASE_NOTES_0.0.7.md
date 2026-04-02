# Release 0.0.7 – Änderungen seit v0.0.6 (kumulativ)

**Veröffentlichungsdatum**: 02.04.2026

Dieses Dokument fasst **alle relevanten Änderungen** seit **v0.0.6** zusammen: Verhalten der **Taubenschiesser-Cloud / des Hardware-Monitors** (Kontext) und **Anpassungen in dieser Home-Assistant-Integration**.

---

## Verhalten in der Cloud (Hardware-Monitor)

### Dynamischer Timer bis „Max Time“ (zwischen Bewegungen)

- **Max Time pro Gerät**: Die Einstellung `waitBetweenMovesSeconds` wird als **Obergrenze** interpretiert.
- **Dynamisches Verhalten**:
  - **Taube erkannt** → Wartezeit wird auf **0 s** gesetzt (nächste Bewegung sobald möglich).
  - **Keine Taube erkannt** → Wartezeit steigt **schrittweise (+1 s)** bis zum Maximum.
  - **Maximum erreicht** → Gerät **hält die Position** und analysiert weiter, bis wieder eine Taube erkannt wird.

*(Details und Releases im Backend-Repository der Taubenschiesser-Cloud.)*

---

## Home-Assistant-Integration

### Persistierte Hardware-Monitor-Daten

- Die Integration liest Monitor-Daten aus den Geräteobjekten der API (`hardwareMonitor.lastWaitingData`, Fallback `lastEventData`), sobald die Cloud diese Felder persistiert.
- Voraussetzung: **Backend-Version** mit Speicherung von Hardware-Monitor-Events am Device.

### Sensor „Dyn Wait“

- Neuer Sensor pro Gerät: **„Dyn Wait“** (Entity-Suffix `dynamic_threshold`).
- **Zustand**: aktueller dynamischer Warte-Wert in **Sekunden**, aus den persistierten Monitor-Daten.
- **Einheit**: s, **Icon**: `mdi:timer-sand`, **State Class**: Messwert (Diagramme/Statistik).
- Ohne passendes Payload: Zustand **unbekannt**.

### Attribute in HA (bewusst schlank)

- **`max_threshold`** wird in dieser Integration **nicht** als Sensor und **nicht** als Entity-Attribut angezeigt.
- **`dynamic_threshold`** erscheint **nicht** redundant auf allen Sensoren – nur noch über den Sensor **„Dyn Wait“**.
- **`holding`** (Halten am Maximum mit weiterer Analyse) bleibt optional als **Attribut**, wenn die Cloud es liefert.

### Button: Schuss per MQTT

- **TaubenschiesserButton**: Schuss-Aktion nutzt **`shootingTimeMs`** (falls am Gerät gesetzt) und sendet ein **strukturiertes MQTT-Kommando** statt eines festen Strings.

### Metadaten

- **`manifest.json`**: Version **0.0.7**.

---

## Migration von v0.0.6

1. **Taubenschiesser-Cloud / Backend** auf eine Version mit persistiertem `hardwareMonitor` aktualisieren (falls noch nicht geschehen).
2. **Integration** aktualisieren (HACS oder `custom_components` kopieren).
3. **Home Assistant neu starten**.
4. Optional: **Max Time** pro Gerät in der Cloud prüfen.
5. Der Sensor **„… Dyn Wait“** erscheint pro Gerät automatisch.

---

## Kurzüberblick

| Thema | Inhalt |
|--------|--------|
| Cloud | Dynamische Wartezeit bis konfiguriertes Maximum; Halten + Analyse am Maximum |
| HA | Sensor „Dyn Wait“; kein Max-Wert in der Integration; `holding` optional als Attribut |
| Button | Schuss über `shootingTimeMs` + MQTT-Objekt |
| API | Lesen von `hardwareMonitor` am Gerät |

---

**Git (nur Integration)**: `v0.0.6...HEAD` – z. B. `git log v0.0.6..HEAD` / `git diff v0.0.6..HEAD`.
