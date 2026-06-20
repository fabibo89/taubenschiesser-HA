"""Binary sensor platform for Taubenschiesser."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_DEVICE_IP, ATTR_LAST_SEEN, ATTR_MONITOR_STATUS, ATTR_WATERTANK, DOMAIN
from .coordinator import TaubenschiesserDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Taubenschiesser binary sensors from a config entry."""
    coordinator: TaubenschiesserDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device_id, device in coordinator.data.get("devices", {}).items():
        entities.append(TaubenschiesserWaterTankBinarySensor(coordinator, device_id, device))

    async_add_entities(entities)


class TaubenschiesserWaterTankBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Wassertank status: on = OK, off = leer."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:water-alert"

    def __init__(
        self,
        coordinator: TaubenschiesserDataUpdateCoordinator,
        device_id: str,
        device: dict,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.device = device
        device_name = device.get("name", "Taubenschiesser")
        self._attr_unique_id = f"{device_id}_watertank"
        self._attr_name = f"{device_name} Wassertank leer"

    @property
    def is_on(self) -> bool:
        """Return True when the tank is empty (problem state)."""
        device = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device:
            return False
        watertank = device.get(ATTR_WATERTANK)
        if watertank is None:
            return False
        return watertank is False

    @property
    def available(self) -> bool:
        """Available when telemetry has been received."""
        device = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device:
            return False
        return device.get(ATTR_WATERTANK) is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device specific attributes."""
        device = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device:
            return {}

        attrs = {
            ATTR_DEVICE_IP: device.get("taubenschiesser", {}).get("ip"),
            ATTR_MONITOR_STATUS: device.get("monitorStatus", "unknown"),
        }
        live = device.get("liveTelemetry") or {}
        if live.get("updatedAt"):
            attrs["updated_at"] = live.get("updatedAt")
        if device.get("lastSeen"):
            attrs[ATTR_LAST_SEEN] = device["lastSeen"]
        return attrs

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
