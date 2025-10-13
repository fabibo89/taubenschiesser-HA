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
            async with self.session.get(f"{self.server_url}/status", ssl=False) as response:
                _LOGGER.debug("Empfangene Daten vom Server/Device: %s", f"{self.server_url}/status")
                if response.status == 200:
                    raw = await response.json()
                    _LOGGER.debug("Antwort-JSON: %s", raw)
                    # Prüfe ob Server-Antwort (Liste von Stationen)
                    if raw.get("status") == "success" and isinstance(raw.get("data"), list):
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
                                    async with self.session.get(f"http://{ip}/status", timeout=5) as dev_resp:
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
                                except Exception as e:
                                    _LOGGER.warning("Fehler beim Statusabruf von Gerät %s: %s", ip, e)
                                    self.last_update_success = False
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
                        # Fallback: Versuche /status direkt (Einzelgerät)
                        async with self.session.get(f"{self.server_url}/status", ssl=False) as dev_resp:
                            if dev_resp.status == 200:
                                device_data = await dev_resp.json()
                                station_id = device_data.get("id", "single")
                                station_name = device_data.get("name") or device_data.get("ip") or f"Station {station_id}"
                                device_data["name"] = station_name
                                device_data["source"] = "device"  # Markiere als Device-Connection
                                return {f"station_{station_id}": device_data}
                            else:
                                raise UpdateFailed(f"Status {dev_resp.status}")
                else:
                    # Kein Erfolg beim Server-Endpunkt, versuche Einzelgerät
                    async with self.session.get(f"{self.server_url}/status", ssl=False) as dev_resp:
                        if dev_resp.status == 200:
                            device_data = await dev_resp.json()
                            station_id = device_data.get("id", "single")
                            device_data["source"] = "device"  # Markiere als Device-Connection
                            return {f"station_{station_id}": device_data}
                        else:
                            raise UpdateFailed(f"Status {dev_resp.status}")
        except asyncio.CancelledError:
            _LOGGER.warning("Abbruch während Datenabruf – vermutlich durch Shutdown oder Timeout")
            self.last_update_success = False
            raise
        except aiohttp.ClientError as err:
            _LOGGER.error("Verbindung zu Taubenschießer fehlgeschlagen: %s", err)
            self.last_update_success = False
            raise UpdateFailed from err
        except Exception as err:
            _LOGGER.exception("Fehler bei der Kommunikation mit Taubenschießer:")
            self.last_update_success = False
            raise UpdateFailed(f"Fehler: {err}")

