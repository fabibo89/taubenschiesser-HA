from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Konfigurierbare Button-Typen
BUTTON_TYPES = {
    "reset": {
        "name": "Reset",
        "url_path": "/reset",
        "icon": "mdi:restart",
        "use_post": False,
        "json_data": {"type": "reset"}
    },
    "move_left": {
        "name": "Links",
        "url_path": "/ConDB",
        "icon": "mdi:arrow-left",
        "use_post": True, 
        "json_data": {
            "type": "impulse",
            "speed": 1,
            "bounce": False,
            "position": {
                "rot": -10,
                "tilt": 0
            }
        }
    },
    "move_right": {
        "name": "Rechts", 
        "url_path": "/ConDB",
        "icon": "mdi:arrow-right",
        "use_post": True,
        "json_data": {
            "type": "impulse", 
            "speed": 1,
            "bounce": False,
            "position": {
                "rot": 10,
                "tilt": 0
            }
        }
    },
    "move_up": {
        "name": "Hoch",
        "url_path": "/ConDB", 
        "icon": "mdi:arrow-up",
        "use_post": True,
        "json_data": {
            "type": "impulse",
            "speed": 1, 
            "bounce": False,
            "position": {
                "rot": 0,
                "tilt": -10
            }
        }
    },
    "move_down": {
        "name": "Runter",
        "url_path": "/ConDB",
        "icon": "mdi:arrow-down", 
        "use_post": True,
        "json_data": {
            "type": "impulse",
            "speed": 1,
            "bounce": False, 
            "position": {
                "rot": 0,
                "tilt": 10
            }
        }
    },
    "shoot": {
        "name": "Schießen",
        "url_path": "/ConDB",
        "icon": "mdi:pistol",
        "use_post": True,
        "json_data": {
            "type": "shoot",
            "duration": 2000
        }
    }
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug("button.py gestartet – verfügbare Stationsdaten: %s", coordinator.data)
    buttons = []

    for station_id, station in coordinator.data.items():
        station_name = station.get("name", f"Station {station_id}")
        station_ip = station.get("ip", f"Station {station_id}")

        for button_key, button_conf in BUTTON_TYPES.items():
            button_name = f"{button_conf['name']} {station_name}"
            server_url = entry.data["server"] 
            _LOGGER.debug("Erzeuge Button: %s (station_id=%s, type=%s)", button_name, station_id, button_key)

            buttons.append(
                    TaubenschiesserButton(
                        coordinator,
                        hass,
                        station_name,
                        station_id,
                        station_ip,
                        button_key,
                        button_conf,
                        server_url
                    )
                )

    async_add_entities(buttons, True)


class TaubenschiesserButton(ButtonEntity):
    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"station_{self.station_id}")},
            "name": self.station_name,
            "manufacturer": "Taubenschießer",
            "model": "Taubenschießer",
            "configuration_url": f"http://{self.station_ip}"

        }    
    def __init__(self, coordinator, hass, station_name, station_id, station_ip, button_key, config, server_url):
        self._coordinator = coordinator
        self._session = async_get_clientsession(hass)
        self.station_id = station_id
        self.station_name = station_name
        self.station_ip = station_ip
        self.button_key = button_key
        self._config = config
        self._server_url = server_url

        self._attr_name = f"{config['name']} {station_name}"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = config.get("icon", "mdi:gesture-tap-button")
        self._attr_unique_id = f"{station_ip}_{button_key}_{station_id}"

    async def async_press(self):
        import json
        
        url_path = self._config["url_path"]
        url = f"http://{self.station_ip}{url_path}"
        
        _LOGGER.debug("Sende %s-Befehl an %s", self.button_key, url)

        try:
            if self._config.get("use_post", False):
                # POST Request mit JSON-Daten
                json_data = self._config.get("json_data", {})
                headers = {"Content-Type": "application/json"}
                
                # Für ConDB: JSON als "text" Parameter senden
                if url_path == "/ConDB":
                    post_data = {"text": json.dumps(json_data)}
                    _LOGGER.debug("Sende POST zu ConDB mit Daten: %s", post_data)
                    async with self._session.post(url, data=post_data, timeout=5, ssl=False) as response:
                        if response.status == 200:
                            result = await response.text()
                            _LOGGER.debug("Antwort von %s: %s", self._attr_name, result)
                        else:
                            _LOGGER.warning("Button-Request fehlgeschlagen (%s): HTTP %s", self._attr_name, response.status)
                else:
                    # Normaler JSON POST
                    async with self._session.post(url, json=json_data, timeout=5, ssl=False) as response:
                        if response.status == 200:
                            result = await response.text()
                            _LOGGER.debug("Antwort von %s: %s", self._attr_name, result)
                        else:
                            _LOGGER.warning("Button-Request fehlgeschlagen (%s): HTTP %s", self._attr_name, response.status)
            else:
                # GET Request
                async with self._session.get(url, timeout=5, ssl=False) as response:
                    if response.status == 200:
                        result = await response.text()
                        _LOGGER.debug("Antwort von %s: %s", self._attr_name, result)
                    else:
                        _LOGGER.warning("Button-Request fehlgeschlagen (%s): HTTP %s", self._attr_name, response.status)
                        
        except Exception as e:
            _LOGGER.error("Fehler beim Senden des Button-Requests an %s: %s", self._attr_name, e)
