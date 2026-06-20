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
    ATTR_LASER,
    ATTR_MONITOR_STATUS,
    DOMAIN,
    MONITOR_STATUS_PAUSED,
    MONITOR_STATUS_RUNNING,
)
from .coordinator import TaubenschiesserDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SwitchKind = Literal[
    "monitor",
    "armed",
    "laser",
    "shoot_use_laser",
    "shoot_use_audio",
    "shoot_laser_blink",
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Taubenschiesser switches from a config entry."""
    coordinator: TaubenschiesserDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device_id, device in coordinator.data.get("devices", {}).items():
        for switch_kind in (
            "monitor",
            "armed",
            "laser",
            "shoot_use_laser",
            "shoot_use_audio",
            "shoot_laser_blink",
        ):
            entities.append(
                TaubenschiesserSwitch(coordinator, device_id, device, switch_kind)
            )

    async_add_entities(entities)


class TaubenschiesserSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Taubenschiesser switch."""

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
        elif switch_kind == "armed":
            self._attr_unique_id = f"{device_id}_armed"
            self._attr_name = f"{device_name} Armed"
        elif switch_kind == "laser":
            self._attr_unique_id = f"{device_id}_laser"
            self._attr_name = f"{device_name} Laser"
            self._attr_icon = "mdi:laser-pointer"
        elif switch_kind == "shoot_use_laser":
            self._attr_unique_id = f"{device_id}_shoot_use_laser"
            self._attr_name = f"{device_name} Schuss: Laser nutzen"
            self._attr_icon = "mdi:target"
        elif switch_kind == "shoot_use_audio":
            self._attr_unique_id = f"{device_id}_shoot_use_audio"
            self._attr_name = f"{device_name} Schuss: Akustische Signale"
            self._attr_icon = "mdi:volume-high"
        else:
            self._attr_unique_id = f"{device_id}_shoot_laser_blink"
            self._attr_name = f"{device_name} Schuss: Laser blinkt"
            self._attr_icon = "mdi:flash-alert"

    def _get_taubenschiesser(self) -> dict[str, Any]:
        device = self.coordinator.data.get("devices", {}).get(self.device_id, {})
        taubenschiesser = device.get("taubenschiesser", {})
        return taubenschiesser if isinstance(taubenschiesser, dict) else {}

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        device = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device:
            return False
        if self.switch_kind == "monitor":
            return device.get("monitorStatus") == MONITOR_STATUS_RUNNING
        if self.switch_kind == "armed":
            return bool(device.get("monitorArmed", False))
        if self.switch_kind == "shoot_use_laser":
            return self._get_taubenschiesser().get("shootUseLaser", True) is not False
        if self.switch_kind == "shoot_use_audio":
            return bool(self._get_taubenschiesser().get("shootUseAudio", False))
        if self.switch_kind == "shoot_laser_blink":
            return bool(self._get_taubenschiesser().get("shootLaserBlink", False))
        return bool(device.get(ATTR_LASER, False))

    async def _async_update_taubenschiesser_setting(
        self, fields: dict[str, Any], sync_esp: bool = False
    ) -> None:
        device = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device:
            raise Exception(f"Device {self.device_id} not found")

        await self.coordinator.send_api_update_taubenschiesser(self.device_id, fields)

        if sync_esp:
            device_ip = device.get("taubenschiesser", {}).get("ip")
            if device_ip and self.coordinator.mqtt_client and self.coordinator.mqtt_client.is_connected():
                await self.coordinator.send_esp_device_config(
                    device_ip,
                    use_laser_on_shoot=fields.get("shootUseLaser"),
                    use_audio_on_shoot=fields.get("shootUseAudio"),
                )

        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()

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
        elif self.switch_kind == "armed":
            try:
                await self.coordinator.send_api_arm(self.device_id, True)
                if self.device_id in self.coordinator.data.get("devices", {}):
                    self.coordinator.data["devices"][self.device_id]["monitorArmed"] = True
                await self.coordinator.async_request_refresh()
            except Exception as err:
                _LOGGER.error("Error arming device %s: %s", self.device_id, err)
                raise
        elif self.switch_kind == "shoot_use_laser":
            try:
                await self._async_update_taubenschiesser_setting(
                    {"shootUseLaser": True}, sync_esp=True
                )
            except Exception as err:
                _LOGGER.error("Error enabling shoot laser for device %s: %s", self.device_id, err)
                raise
        elif self.switch_kind == "shoot_use_audio":
            try:
                await self._async_update_taubenschiesser_setting(
                    {"shootUseAudio": True}, sync_esp=True
                )
            except Exception as err:
                _LOGGER.error("Error enabling shoot audio for device %s: %s", self.device_id, err)
                raise
        elif self.switch_kind == "shoot_laser_blink":
            try:
                await self._async_update_taubenschiesser_setting({"shootLaserBlink": True})
            except Exception as err:
                _LOGGER.error("Error enabling shoot laser blink for device %s: %s", self.device_id, err)
                raise
        else:
            try:
                await self._async_set_laser(True)
            except Exception as err:
                _LOGGER.error("Error turning laser on for device %s: %s", self.device_id, err)
                raise

    async def _async_set_laser(self, on: bool) -> None:
        device = self.coordinator.data.get("devices", {}).get(self.device_id)
        if not device:
            raise Exception(f"Device {self.device_id} not found")

        device_ip = device.get("taubenschiesser", {}).get("ip")
        if not device_ip:
            raise Exception(f"Device IP not found for device {self.device_id}")

        if not self.coordinator.mqtt_client or not self.coordinator.mqtt_client.is_connected():
            raise Exception("MQTT client not connected")

        await self.coordinator.send_mqtt_command(
            device_ip, {"type": "laser", "state": on}
        )
        if self.device_id in self.coordinator.data.get("devices", {}):
            self.coordinator.data["devices"][self.device_id][ATTR_LASER] = on
        await self.coordinator.async_request_refresh()

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
        elif self.switch_kind == "armed":
            try:
                await self.coordinator.send_api_arm(self.device_id, False)
                if self.device_id in self.coordinator.data.get("devices", {}):
                    self.coordinator.data["devices"][self.device_id]["monitorArmed"] = False
                await self.coordinator.async_request_refresh()
            except Exception as err:
                _LOGGER.error("Error disarming device %s: %s", self.device_id, err)
                raise
        elif self.switch_kind == "shoot_use_laser":
            try:
                await self._async_update_taubenschiesser_setting(
                    {"shootUseLaser": False}, sync_esp=True
                )
            except Exception as err:
                _LOGGER.error("Error disabling shoot laser for device %s: %s", self.device_id, err)
                raise
        elif self.switch_kind == "shoot_use_audio":
            try:
                await self._async_update_taubenschiesser_setting(
                    {"shootUseAudio": False}, sync_esp=True
                )
            except Exception as err:
                _LOGGER.error("Error disabling shoot audio for device %s: %s", self.device_id, err)
                raise
        elif self.switch_kind == "shoot_laser_blink":
            try:
                await self._async_update_taubenschiesser_setting({"shootLaserBlink": False})
            except Exception as err:
                _LOGGER.error("Error disabling shoot laser blink for device %s: %s", self.device_id, err)
                raise
        else:
            try:
                await self._async_set_laser(False)
            except Exception as err:
                _LOGGER.error("Error turning laser off for device %s: %s", self.device_id, err)
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
