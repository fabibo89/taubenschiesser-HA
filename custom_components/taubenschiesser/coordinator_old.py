import logging
from datetime import timedelta
import aiohttp
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN
import json
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import asyncio

_LOGGER = logging.getLogger(__name__)

class TaubenschiesserCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, server_url):
        self.hass = hass
        self.server_url = server_url
        self.session = async_get_clientsession(hass)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )



    async def _async_update_data(self):
        try:
            # Versuche zuerst Server-Endpunkt
            full_url = f"{self.server_url}/status"
            _LOGGER.info("Taubenschießer: Versuche Verbindung zu %s", full_url)
            
            # Kürzeres Timeout für ersten Versuch
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            async with self.session.get(full_url, ssl=False, timeout=timeout) as response:
                _LOGGER.debug("HTTP Status %s von: %s", response.status, full_url)
                if response.status == 200:
                    raw = await response.json()
                    _LOGGER.debug("Antwort-JSON: %s", raw)
                    
                    # Prüfe zuerst auf Taubenschießer-Format (direktes JSON mit "ip" und "Taubenschiesser")
                    if "ip" in raw and "Taubenschiesser" in raw and isinstance(raw, dict):
                        _LOGGER.debug("Taubenschießer-Format erkannt!")
                        device_data = raw.copy()
                        
                        # Station ID aus IP ableiten
                        station_id = device_data.get("ip", "single").replace(".", "_")
                        station_name = f"Taubenschießer {device_data.get('ip', 'Device')}"
                        
                        device_data["name"] = station_name
                        device_data["source"] = "device"
                        device_data["id"] = station_id
                        
                        _LOGGER.debug("Verarbeitete Taubenschießer-Daten für Station %s: %s", station_id, device_data)
                        return {f"station_{station_id}": device_data}
                    
                    # Prüfe ob Server-Antwort (Liste von Stationen)
                    elif raw.get("status") == "success" and isinstance(raw.get("data"), list):
                        basis_data = raw["data"]
                        _LOGGER.debug("Server-Basis-Daten: %s", basis_data)
                        result = {f"station_{station['id']}": station for station in basis_data}
                        
                        # Server-ID aus URL extrahieren (z.B. aus http://192.168.1.100:3000)
                        server_id = self.server_url.split("://")[1].split(":")[0].split(".")[-1]  # Letztes Oktett der IP
                        
                        # Für jede Station: Hole Detaildaten vom Gerät, falls IP vorhanden
                        for station in basis_data:
                            ip = station.get("ip")
                            station_id = station['id']
                            key_station_id = f"station_{station_id}"
                            
                            # Markiere als Server-Connection und füge Server-ID hinzu
                            result[key_station_id]["source"] = "server"
                            result[key_station_id]["server_id"] = server_id
                            
                            if ip:
                                try:
                                    _LOGGER.debug("Versuche Device-Verbindung zu: http://%s/status", ip)
                                    async with self.session.get(f"http://{ip}/status", timeout=10) as dev_resp:
                                        if dev_resp.status == 200:
                                            device_data = await dev_resp.json()
                                            _LOGGER.debug("Device-Daten von %s: %s", ip, device_data)
                                            
                                            # Name aus Gerätedaten übernehmen, falls vorhanden
                                            if "name" in device_data:
                                                result[key_station_id]["name"] = device_data["name"]
                                            
                                            # Device-Daten übernehmen
                                            result[key_station_id].update(device_data)
                                            
                                            _LOGGER.debug("Daten für Station %s aktualisiert", station_id)
                                        else:
                                            self.last_update_success = False
                                            _LOGGER.warning("Gerät %s antwortet nicht wie erwartet (%s)", ip, dev_resp.status)
                                except asyncio.TimeoutError:
                                    _LOGGER.warning("Timeout beim Statusabruf von Gerät %s (>10s) - Gerät möglicherweise offline", ip)
                                    # Nicht als Fehler markieren, da Server-Daten noch verfügbar sind
                                except aiohttp.ClientError as e:
                                    _LOGGER.warning("Netzwerkfehler beim Statusabruf von Gerät %s: %s", ip, e)
                                    # Nicht als Fehler markieren, da Server-Daten noch verfügbar sind
                                except Exception as e:
                                    _LOGGER.warning("Unerwarteter Fehler beim Statusabruf von Gerät %s: %s", ip, e)
                                    # Nicht als Fehler markieren, da Server-Daten noch verfügbar sind
                        return result
                    # Einzelgerät-Modus: Daten direkt als Station
                    elif "status" in raw and "data" in raw and isinstance(raw["data"], dict):
                        # Einzelgerät liefert ein dict unter "data"
                        station = raw["data"]
                        station_id = station.get("id", "single")
                        station_name = station.get("name") or station.get("ip") or f"Station {station_id}"
                        station["name"] = station_name
                        station["source"] = "device"  # Markiere als Device-Connection
                        return {f"station_{station_id}": station}
                    else:
                        _LOGGER.warning("Unbekanntes JSON-Format empfangen: %s", raw)
                        raise UpdateFailed(f"Unbekanntes JSON-Format")
                else:
                    # Kein Erfolg beim Server-Endpunkt, versuche Einzelgerät
                    async with self.session.get(f"{self.server_url}/status", ssl=False) as dev_resp:
                        if dev_resp.status == 200:
                            device_data = await dev_resp.json()
                            # Prüfe auf Taubenschießer-Format
                            if "ip" in device_data and "Taubenschiesser" in device_data and isinstance(device_data, dict):
                                _LOGGER.debug("Taubenschießer-Format im Fallback erkannt!")
                                station_id = device_data.get("ip", "single").replace(".", "_")
                                station_name = f"Taubenschießer {device_data.get('ip', 'Device')}"
                                device_data["name"] = station_name
                                device_data["source"] = "device"
                                device_data["id"] = station_id
                                return {f"station_{station_id}": device_data}
                            else:
                                station_id = device_data.get("id", "single")
                                device_data["source"] = "device"
                                return {f"station_{station_id}": device_data}
                        else:
                            raise UpdateFailed(f"Status {dev_resp.status}")
        except asyncio.CancelledError:
            _LOGGER.warning("Abbruch während Datenabruf – vermutlich durch Shutdown oder Timeout")
            self.last_update_success = False
            raise
        except asyncio.TimeoutError as err:
            _LOGGER.error("Taubenschießer: Timeout nach 10s bei %s", self.server_url)
            _LOGGER.error("Mögliche Ursachen:")
            _LOGGER.error("1. Gerät ist offline oder nicht erreichbar")
            _LOGGER.error("2. Home Assistant läuft in Docker mit Netzwerk-Isolation")
            _LOGGER.error("3. Firewall blockiert die Verbindung")
            _LOGGER.error("4. Falsche IP-Adresse oder Port konfiguriert")
            _LOGGER.error("Teste bitte: curl -m 5 %s/status", self.server_url)
            
            # Weniger häufige Updates bei anhaltenden Problemen
            self.update_interval = timedelta(minutes=2)
            self.last_update_success = False
            
            # Fallback: Dummy-Daten bereitstellen, damit Integration nicht komplett fehlschlägt
            _LOGGER.warning("Verwende Fallback-Daten für Taubenschießer wegen Netzwerkproblem")
            dummy_data = {
                "ip": self.server_url.replace("http://", "").replace("https://", ""),
                "wifi": -99,
                "runtime": 0,
                "compiled": "unknown",
                "Rot": 0,
                "Tilt": 0,
                "Cam": False,
                "timeMQTT": 0,
                "watertank": False,
                "moving": False,
                "Taubenschiesser": {
                    "ip": self.server_url.replace("http://", "").replace("https://", ""),
                    "status": "offline"
                },
                "name": f"Taubenschießer {self.server_url.replace('http://', '')} (Offline)",
                "source": "fallback",
                "id": self.server_url.replace("http://", "").replace("https://", "").replace(".", "_")
            }
            station_id = f"station_{dummy_data['id']}"
            return {station_id: dummy_data}
        except aiohttp.ClientConnectorError as err:
            _LOGGER.error("Taubenschießer: Verbindungsfehler zu %s: %s", self.server_url, err)
            _LOGGER.error("Das Gerät ist wahrscheinlich offline oder nicht im Netzwerk erreichbar")
            self.last_update_success = False
            raise UpdateFailed(f"Gerät nicht erreichbar: {self.server_url}") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Netzwerkfehler bei Verbindung zu Taubenschießer Server %s: %s", self.server_url, err)
            self.last_update_success = False
            raise UpdateFailed(f"Netzwerkfehler: {err}") from err
        except Exception as err:
            _LOGGER.exception("Fehler bei der Kommunikation mit Taubenschießer:")
            self.last_update_success = False
            raise UpdateFailed(f"Fehler: {err}")

