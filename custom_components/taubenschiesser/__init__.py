import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN
from .coordinator import TaubenschiesserCoordinator
import asyncio

PLATFORMS = ["sensor","update","button"]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    mqtt_topic = entry.data.get("mqtt_topic", "taubenschiesser/+/info")
    coordinator = TaubenschiesserCoordinator(hass, entry.data["server"], mqtt_topic)
    await coordinator.async_config_entry_first_refresh()
    
    # Start MQTT listener
    await coordinator.async_start_mqtt_listener()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    coordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator:
        # Stop MQTT listener
        await coordinator.async_stop_mqtt_listener()
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok