import logging
from datetime import timedelta
import aiohttp
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN
import json
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import asyncio
from homeassistant.components import mqtt
from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)

class TaubenschiesserCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, server_url, mqtt_topic=None):
        self.hass = hass
        self.server_url = server_url
        self.mqtt_topic = mqtt_topic or "taubenschiesser/+/info"
        self.session = async_get_clientsession(hass)
        self._mqtt_unsub = None
        self._cached_data = {}
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )



    async def async_start_mqtt_listener(self):
        """Startet den MQTT-Listener für Position-Updates."""
        if not await mqtt.async_wait_for_mqtt_client(self.hass):
            _LOGGER.error("MQTT nicht verfügbar")
            return
            
        _LOGGER.info("Starte MQTT-Listener für Topic: %s", self.mqtt_topic)
        
        @callback
        def mqtt_message_received(msg):
            """Verarbeitet empfangene MQTT-Nachrichten."""
            try:
                _LOGGER.debug("MQTT empfangen von %s: %s", msg.topic, msg.payload)
                payload = json.loads(msg.payload)
                
                # Extract IP from topic (e.g., taubenschiesser/192.168.10.87/info)
                topic_parts = msg.topic.split('/')
                if len(topic_parts) >= 3:
                    device_ip = topic_parts[1]
                    station_id = f"station_{device_ip.replace('.', '_')}"
                    
                    # Update cached data with MQTT info
                    if station_id in self._cached_data:
                        # Merge MQTT data with existing data
                        self._cached_data[station_id].update(payload)
                        _LOGGER.debug("MQTT-Update für %s: Position Rot=%s, Tilt=%s", 
                                    station_id, payload.get('Rot'), payload.get('Tilt'))
                        
                        # Trigger update for all listeners
                        self.async_set_updated_data(self._cached_data)
                    else:
                        _LOGGER.warning("MQTT für unbekannte Station: %s", station_id)
                        
            except json.JSONDecodeError as e:
                _LOGGER.error("Ungültiges JSON in MQTT-Nachricht: %s", e)
            except Exception as e:
                _LOGGER.error("Fehler beim Verarbeiten der MQTT-Nachricht: %s", e)

        # Subscribe to MQTT topic
        self._mqtt_unsub = await mqtt.async_subscribe(
            self.hass, 
            self.mqtt_topic, 
            mqtt_message_received,
            qos=1
        )
        
    async def async_stop_mqtt_listener(self):
        """Stoppt den MQTT-Listener."""
        if self._mqtt_unsub:
            self._mqtt_unsub()
            self._mqtt_unsub = None
            _LOGGER.info("MQTT-Listener gestoppt")

    async def _fetch_device_data(self):
        """Ursprüngliche HTTP-Datenabfrage (jetzt als separate Methode)."""
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

    async def _async_update_data(self):
        """Ruft Daten vom Taubenschießer-Gerät ab und cached sie."""
        data = await self._fetch_device_data()
        # Cache the data for MQTT updates
        self._cached_data = data
        return data