"""Button platform for Taubenschiesser."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_DEVICE_IP, DOMAIN
from .coordinator import TaubenschiesserDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

BUTTON_TYPES = [
    {"key": "rotate_left", "name": "Links", "icon": "mdi:arrow-left", "command": {"type": "impulse", "speed": 1, "bounce": 0, "position": {"rot": -10, "tilt": 0}}},
    {"key": "rotate_right", "name": "Rechts", "icon": "mdi:arrow-right", "command": {"type": "impulse", "speed": 1, "bounce": 0, "position": {"rot": 10, "tilt": 0}}},
    {"key": "move_up", "name": "Hoch", "icon": "mdi:arrow-up", "command": {"type": "impulse", "speed": 1, "bounce": 0, "position": {"rot": 0, "tilt": 10}}},
    {"key": "move_down", "name": "Runter", "icon": "mdi:arrow-down", "command": {"type": "impulse", "speed": 1, "bounce": 0, "position": {"rot": 0, "tilt": -10}}},
    {"key": "shoot", "name": "Schießen", "icon": "mdi:target", "command": {"type": "shoot", "duration": 500}},
    {"key": "reset", "name": "Reset", "icon": "mdi:restore", "command": {"type": "reset"}},
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Taubenschiesser buttons from a config entry."""
    coordinator: TaubenschiesserDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device_id, device in coordinator.data.get("devices", {}).items():
        for button_type in BUTTON_TYPES:
            entities.append(
                TaubenschiesserButton(coordinator, device_id, device, button_type)
            )

    async_add_entities(entities)


class TaubenschiesserButton(CoordinatorEntity, ButtonEntity):
    """Representation of a Taubenschiesser button."""

    def __init__(
        self,
        coordinator: TaubenschiesserDataUpdateCoordinator,
        device_id: str,
        device: dict,
        button_type: dict,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.device = device
        self.button_type = button_type
        self._attr_unique_id = f"{device_id}_{button_type['key']}"
        self._attr_name = f"{device.get('name', 'Taubenschiesser')} {button_type['name']}"
        self._attr_icon = button_type["icon"]

    async def async_press(self) -> None:
        """Handle the button press."""
        device = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device:
            _LOGGER.error("Device %s not found", self.device_id)
            return

        device_ip = device.get("taubenschiesser", {}).get("ip")
        if not device_ip:
            _LOGGER.error("Device IP not found for device %s", self.device_id)
            return

        try:
            # Try MQTT first if available
            if self.coordinator.mqtt_client and self.coordinator.mqtt_client.is_connected():
                await self.coordinator.send_mqtt_command(
                    device_ip, self.button_type["command"]
                )
            else:
                # Fallback to API
                action = self.button_type["key"]
                await self.coordinator.send_api_command(self.device_id, action)
        except Exception as err:
            _LOGGER.error(
                "Error sending command %s to device %s: %s",
                self.button_type["key"],
                self.device_id,
                err,
            )
            raise

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device specific attributes."""
        device = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device:
            return {}

        return {
            ATTR_DEVICE_IP: device.get("taubenschiesser", {}).get("ip"),
        }

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        device = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device:
            return {}
        
        device_ip = device.get("taubenschiesser", {}).get("ip", "")
        return {
            "identifiers": {(DOMAIN, self.device_id)},
            "name": device.get("name", "Taubenschiesser"),
            "manufacturer": "Taubenschiesser",
            "model": "Taubenschiesser Device",
            "configuration_url": f"http://{device_ip}" if device_ip else None,
        }

