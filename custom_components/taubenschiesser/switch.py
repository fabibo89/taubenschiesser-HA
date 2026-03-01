"""Switch platform for Taubenschiesser."""
from __future__ import annotations

import logging
from typing import Any, Literal

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DEVICE_IP,
    ATTR_LAST_SEEN,
    ATTR_MONITOR_STATUS,
    DOMAIN,
    MONITOR_STATUS_PAUSED,
    MONITOR_STATUS_RUNNING,
)
from .coordinator import TaubenschiesserDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SwitchKind = Literal["monitor", "armed"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Taubenschiesser switches from a config entry."""
    coordinator: TaubenschiesserDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device_id, device in coordinator.data.get("devices", {}).items():
        entities.append(
            TaubenschiesserSwitch(coordinator, device_id, device, "monitor")
        )
        entities.append(
            TaubenschiesserSwitch(coordinator, device_id, device, "armed")
        )

    async_add_entities(entities)


class TaubenschiesserSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Taubenschiesser switch (Monitor or Armed)."""

    def __init__(
        self,
        coordinator: TaubenschiesserDataUpdateCoordinator,
        device_id: str,
        device: dict,
        switch_kind: SwitchKind,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.device = device
        self.switch_kind = switch_kind
        device_name = device.get("name", "Taubenschiesser")
        if switch_kind == "monitor":
            self._attr_unique_id = f"{device_id}_monitor"
            self._attr_name = f"{device_name} Monitor"
        else:
            self._attr_unique_id = f"{device_id}_armed"
            self._attr_name = f"{device_name} Armed"

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        device = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device:
            return False
        if self.switch_kind == "monitor":
            return device.get("monitorStatus") == MONITOR_STATUS_RUNNING
        return bool(device.get("monitorArmed", False))

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on the switch."""
        if self.switch_kind == "monitor":
            try:
                await self.coordinator.send_api_start_pause(self.device_id, "start")
                if self.device_id in self.coordinator.data.get("devices", {}):
                    self.coordinator.data["devices"][self.device_id]["monitorStatus"] = (
                        MONITOR_STATUS_RUNNING
                    )
                await self.coordinator.async_request_refresh()
            except Exception as err:
                _LOGGER.error("Error starting device %s: %s", self.device_id, err)
                raise
        else:
            try:
                await self.coordinator.send_api_arm(self.device_id, True)
                if self.device_id in self.coordinator.data.get("devices", {}):
                    self.coordinator.data["devices"][self.device_id]["monitorArmed"] = True
                await self.coordinator.async_request_refresh()
            except Exception as err:
                _LOGGER.error("Error arming device %s: %s", self.device_id, err)
                raise

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the switch."""
        if self.switch_kind == "monitor":
            try:
                await self.coordinator.send_api_start_pause(self.device_id, "pause")
                if self.device_id in self.coordinator.data.get("devices", {}):
                    self.coordinator.data["devices"][self.device_id]["monitorStatus"] = (
                        MONITOR_STATUS_PAUSED
                    )
                await self.coordinator.async_request_refresh()
            except Exception as err:
                _LOGGER.error("Error pausing device %s: %s", self.device_id, err)
                raise
        else:
            try:
                await self.coordinator.send_api_arm(self.device_id, False)
                if self.device_id in self.coordinator.data.get("devices", {}):
                    self.coordinator.data["devices"][self.device_id]["monitorArmed"] = False
                await self.coordinator.async_request_refresh()
            except Exception as err:
                _LOGGER.error("Error disarming device %s: %s", self.device_id, err)
                raise

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

