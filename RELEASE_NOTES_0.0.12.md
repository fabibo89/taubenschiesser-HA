# Release 0.0.12 – Kameras (Master + Slave) in Home Assistant

**Veröffentlichungsdatum**: 06.10.2026

---

## Home-Assistant-Integration

### Kamera-Entities

Pro Gerät erscheinen **alle** Einträge aus `cameras[]` als Home-Assistant-Kamera (Master und Slave). Ohne `cameras[]` bleibt eine Legacy-Kamera.

- Name: `{Gerät} {Kamera-Name}` (sonst `Master` / `Slave`)
- Still-Bild über die Cloud-API: `GET /api/device-image/{deviceId}?cameraId=…`
- Attribute: `role`, `camera_type`, `camera_ip` (keine Passwörter)

Die Entities hängen am bestehenden Taubenschiesser-Gerät. Neue Slave-Kameras werden beim nächsten API-Polling automatisch ergänzt.

### Backend

`GET /api/device-image/:deviceId?cameraId=` erfasst einen Still von genau diesem `cameras[]`-Slot (Tapo RTSP, PiCam/ESP-P4 HTTP).

---

## Migration von v0.0.11

1. **Backend** aktualisieren (Snapshot-API mit `cameraId`).
2. **Integration** auf **0.0.12** aktualisieren und Home Assistant neu starten.
3. Unter dem Gerät erscheinen die Kamera-Entities; bei Bedarf ins Dashboard legen.

**Hinweis:** Home Assistant holt die Bilder über den Taubenschiesser-Server, nicht direkt von der Kamera-IP. Der Server muss die Kameras erreichen.

---

## Kurzüberblick

| Thema | Inhalt |
|--------|--------|
| HA | Platform `camera` — Master + Slave als Still-Kamera |
| API | `?cameraId=` auf `/api/device-image` |
| Version | **0.0.12** |
