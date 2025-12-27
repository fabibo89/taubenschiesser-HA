"""Sensor platform for Taubenschiesser."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DEVICE_IP,
    ATTR_LAST_MQTT,
    ATTR_LAST_SEEN,
    ATTR_MONITOR_STATUS,
    ATTR_MOVING,
    ATTR_ROTATION,
    ATTR_STATUS,
    ATTR_TILT,
    DOMAIN,
)
from .coordinator import TaubenschiesserDataUpdateCoordinator

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=ATTR_ROTATION,
        name="Rotation",
        native_unit_of_measurement="°",
        icon="mdi:rotate-3d-variant",
    ),
    SensorEntityDescription(
        key=ATTR_TILT,
        name="Tilt",
        native_unit_of_measurement="°",
        icon="mdi:angle-acute",
    ),
    SensorEntityDescription(
        key=ATTR_LAST_MQTT,
        name="Letzte MQTT Nachricht",
        icon="mdi:clock-outline",
    ),
    SensorEntityDescription(
        key=ATTR_STATUS,
        name="Status",
        icon="mdi:information",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Taubenschiesser sensors from a config entry."""
    coordinator: TaubenschiesserDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device_id, device in coordinator.data.get("devices", {}).items():
        for description in SENSOR_TYPES:
            entities.append(
                TaubenschiesserSensor(coordinator, device_id, device, description)
            )

    async_add_entities(entities)


class TaubenschiesserSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Taubenschiesser sensor."""

    def __init__(
        self,
        coordinator: TaubenschiesserDataUpdateCoordinator,
        device_id: str,
        device: dict,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.device = device
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_name = f"{device.get('name', 'Taubenschiesser')} {description.name}"

    @property
    def native_value(self) -> float | str | None:
        """Return the state of the sensor."""
        device = self.coordinator.data.get("devices", {}).get(self.device_id)
        if device:
            key = self.entity_description.key
            if key == ATTR_LAST_MQTT:
                # Return timestamp as ISO string or None
                value = device.get(key)
                if value:
                    return value
                return None
            elif key == ATTR_STATUS:
                # Return status as string
                return device.get(key, "unknown")
            else:
                # Numeric values (rotation, tilt)
                return device.get(key, 0)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device specific attributes."""
        device = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device:
            return {}

        attrs = {
            ATTR_DEVICE_IP: device.get("taubenschiesser", {}).get("ip"),
            ATTR_MONITOR_STATUS: device.get("monitorStatus", "unknown"),
            ATTR_MOVING: device.get(ATTR_MOVING, False),
        }

        if device.get("lastSeen"):
            attrs[ATTR_LAST_SEEN] = device["lastSeen"]
        
        if device.get(ATTR_LAST_MQTT):
            attrs[ATTR_LAST_MQTT] = device[ATTR_LAST_MQTT]

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

