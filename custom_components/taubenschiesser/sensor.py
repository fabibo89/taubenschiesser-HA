"""Sensor platform for Taubenschiesser."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
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
    ATTR_TODAY_DETECTIONS,
    ATTR_WIFI,
    ATTR_YESTERDAY_DETECTIONS,
    ATTR_DYNAMIC_THRESHOLD,
    ATTR_HOLDING,
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
        native_unit_of_measurement="s",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:clock-outline",
    ),
    SensorEntityDescription(
        key=ATTR_WIFI,
        name="WLAN-Signal",
        native_unit_of_measurement="dBm",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        icon="mdi:wifi",
    ),
    SensorEntityDescription(
        key=ATTR_STATUS,
        name="Status",
        icon="mdi:information",
    ),
    SensorEntityDescription(
        key=ATTR_TODAY_DETECTIONS,
        name="Erkennungen heute",
        native_unit_of_measurement="Erkennungen",
        icon="mdi:counter",
    ),
    SensorEntityDescription(
        key=ATTR_YESTERDAY_DETECTIONS,
        name="Erkennungen gestern",
        native_unit_of_measurement="Erkennungen",
        icon="mdi:counter",
    ),
    SensorEntityDescription(
        key=ATTR_DYNAMIC_THRESHOLD,
        name="Dyn Wait",
        native_unit_of_measurement="s",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer-sand",
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
                # Sekunden seit letzter MQTT-Nachricht (Integer für Diagramm)
                value = device.get(key)
                if value is not None:
                    try:
                        return int(value)
                    except (TypeError, ValueError):
                        return None
                return None
            elif key == ATTR_WIFI:
                # WiFi signal strength (dBm), only when sent by device
                return device.get(key)
            elif key == ATTR_STATUS:
                # Return status as string
                return device.get(key, "unknown")
            elif key == ATTR_TODAY_DETECTIONS:
                # Return today's detection count
                counts = device.get("detectionCounts", {})
                return counts.get("today", 0)
            elif key == ATTR_YESTERDAY_DETECTIONS:
                # Return yesterday's detection count
                counts = device.get("detectionCounts", {})
                return counts.get("yesterday", 0)
            elif key == ATTR_DYNAMIC_THRESHOLD:
                hm = device.get("hardwareMonitor", {}) or {}
                hm_data = hm.get("lastWaitingData") or hm.get("lastEventData", {}) or {}
                raw = hm_data.get("dynamic_threshold")
                if raw is None:
                    return None
                try:
                    return int(raw)
                except (TypeError, ValueError):
                    return None
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

        # holding: optional context (dyn wait is only on the Dyn Wait sensor state)
        hm = device.get("hardwareMonitor", {}) or {}
        hm_data = hm.get("lastWaitingData") or hm.get("lastEventData", {}) or {}
        if "holding" in hm_data:
            attrs[ATTR_HOLDING] = hm_data.get("holding")

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

