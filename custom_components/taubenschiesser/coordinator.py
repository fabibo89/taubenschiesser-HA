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
        """Ruft Daten vom Taubenschießer-Gerät ab."""
        try:
            url = f"{self.server_url}/status"
            _LOGGER.debug("Taubenschießer: Hole Daten von %s", url)
            
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            async with self.session.get(url, ssl=False, timeout=timeout) as response:
                if response.status == 200:
                    raw = await response.json()
                    _LOGGER.debug("Empfangene Daten: %s", raw)
                    
                    # Prüfe auf Taubenschießer-Format
                    if "ip" in raw and "Taubenschiesser" in raw and isinstance(raw, dict):
                        # Station ID aus IP ableiten
                        station_id = raw.get("ip", "unknown").replace(".", "_")
                        station_name = f"Taubenschießer {raw.get('ip', 'Device')}"
                        
                        # Daten für Home Assistant aufbereiten
                        device_data = raw.copy()
                        device_data["name"] = station_name
                        device_data["source"] = "device"
                        device_data["id"] = station_id
                        
                        _LOGGER.debug("Taubenschießer-Gerät erkannt: %s", station_name)
                        return {f"station_{station_id}": device_data}
                    else:
                        _LOGGER.error("Unerwartetes JSON-Format: %s", raw)
                        raise UpdateFailed("Unbekanntes JSON-Format vom Gerät")
                else:
                    _LOGGER.error("HTTP Fehler %s von %s", response.status, url)
                    raise UpdateFailed(f"HTTP {response.status}")
                    
        except asyncio.CancelledError:
            _LOGGER.warning("Update abgebrochen")
            self.last_update_success = False
            raise
        except asyncio.TimeoutError as err:
            _LOGGER.warning("Timeout bei %s - Gerät nicht erreichbar", self.server_url)
            self.last_update_success = False
            raise UpdateFailed(f"Timeout: {self.server_url}") from err
        except aiohttp.ClientError as err:
            _LOGGER.warning("Netzwerkfehler bei %s: %s", self.server_url, err)
            self.last_update_success = False
            raise UpdateFailed(f"Netzwerkfehler: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unerwarteter Fehler:")
            self.last_update_success = False
            raise UpdateFailed(f"Fehler: {err}") from err