# Konfiguration: API-URL und Token

## API-URL

Die API-URL ist die Adresse deines Taubenschiesser-Servers.

### Lokale Installation
```
http://localhost:5001
```

### Auf einem anderen Rechner im Netzwerk
```
http://192.168.1.100:5001
```
(Ersetze `192.168.1.100` mit der IP-Adresse deines Servers)

### Mit Hostname
```
http://casahosch:5001
```
(Ersetze `casahosch` mit deinem Hostname)

### Mit Domain
```
http://taubenschiesser.example.com:5001
```

**Wichtig**: 
- Port ist standardmäßig **5001**
- Verwende **http://** oder **https://** je nach Konfiguration
- Kein Slash am Ende!

## API Token

Das Token ist ein JWT (JSON Web Token), das du beim Login erhältst.

### Methode 1: Aus dem Browser (Einfachste Methode)

1. Öffne dein Taubenschiesser-Dashboard im Browser
2. Logge dich ein
3. Öffne die **Entwicklertools** (F12 oder Rechtsklick → Untersuchen)
4. Gehe zum Tab **Application** (Chrome) oder **Storage** (Firefox)
5. Klicke auf **Local Storage** → deine Domain
6. Suche nach dem Eintrag **`token`**
7. Kopiere den Wert (langer String, beginnt meist mit `eyJ...`)

### Methode 2: Über die API (Terminal)

```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"deine@email.de","password":"dein-passwort"}'
```

Die Antwort sieht so aus:
```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": { ... }
}
```

Kopiere den Wert aus dem `token` Feld.

### Methode 3: Mit Python

```python
import requests

response = requests.post(
    "http://localhost:5001/api/auth/login",
    json={
        "email": "deine@email.de",
        "password": "dein-passwort"
    }
)

token = response.json()["token"]
print(f"Token: {token}")
```

## Beispiel-Konfiguration

### Lokale Installation
- **API URL**: `http://localhost:5001`
- **API Token**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2Nz...`

### Server im Netzwerk
- **API URL**: `http://192.168.1.100:5001`
- **API Token**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2Nz...`

## Token-Gültigkeit

- Standard: **7 Tage** (kann in der Server-Konfiguration geändert werden)
- Nach Ablauf: Einfach neu einloggen und neues Token holen
- Token wird automatisch beim Login erneuert

## Troubleshooting

### "Cannot connect" Fehler
- Prüfe, ob der Server läuft: `curl http://localhost:5001/health`
- Prüfe die Firewall-Einstellungen
- Stelle sicher, dass der Port 5001 erreichbar ist

### "Invalid auth" Fehler
- Token könnte abgelaufen sein → Neues Token holen
- Prüfe, ob das Token vollständig kopiert wurde (keine Leerzeichen)
- Stelle sicher, dass du dich mit einem gültigen Account eingeloggt hast

### Port nicht erreichbar
- Prüfe, ob der Server auf dem richtigen Port läuft
- Bei Docker: Prüfe Port-Mappings
- Bei Firewall: Port 5001 freigeben

