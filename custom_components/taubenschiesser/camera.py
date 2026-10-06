"""Camera platform for Taubenschiesser (master + slave stills)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_DEVICE_IP, DOMAIN
from .coordinator import TaubenschiesserDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

LEGACY_CAMERA_ID = "legacy"


def _iter_cameras(device: dict) -> list[dict]:
    """Enabled cameras[] entries, or a synthetic legacy camera."""
    cams = device.get("cameras") or []
    enabled = [c for c in cams if isinstance(c, dict) and c.get("enabled", True)]
    if enabled:
        return enabled
    legacy = device.get("camera")
    if isinstance(legacy, dict) and legacy.get("type"):
        return [
            {
                "id": LEGACY_CAMERA_ID,
                "name": "Kamera",
                "role": "master",
                "type": legacy.get("type"),
            }
        ]
    return []


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Taubenschiesser cameras from a config entry."""
    coordinator: TaubenschiesserDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    known: set[tuple[str, str]] = set()
    entities: list[TaubenschiesserCamera] = []
    for device_id, device in coordinator.data.get("devices", {}).items():
        for cam in _iter_cameras(device):
            camera_id = str(cam.get("id") or LEGACY_CAMERA_ID)
            known.add((device_id, camera_id))
            entities.append(TaubenschiesserCamera(coordinator, device_id, camera_id))

    async_add_entities(entities)

    @callback
    def _add_new_cameras() -> None:
        new_entities: list[TaubenschiesserCamera] = []
        for device_id, device in coordinator.data.get("devices", {}).items():
            for cam in _iter_cameras(device):
                camera_id = str(cam.get("id") or LEGACY_CAMERA_ID)
                key = (device_id, camera_id)
                if key in known:
                    continue
                known.add(key)
                new_entities.append(
                    TaubenschiesserCamera(coordinator, device_id, camera_id)
                )
        if new_entities:
            async_add_entities(new_entities)

    entry.async_on_unload(coordinator.async_add_listener(_add_new_cameras))


class TaubenschiesserCamera(CoordinatorEntity, Camera):
    """Still camera for one master or slave slot."""

    _attr_icon = "mdi:cctv"

    def __init__(
        self,
        coordinator: TaubenschiesserDataUpdateCoordinator,
        device_id: str,
        camera_id: str,
    ) -> None:
        """Initialize the camera."""
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self.device_id = device_id
        self.camera_id = camera_id
        self._attr_unique_id = f"{device_id}_camera_{camera_id}"

    def _device(self) -> dict | None:
        return self.coordinator.data.get("devices", {}).get(self.device_id)

    def _cam(self) -> dict | None:
        device = self._device()
        if not device:
            return None
        for cam in _iter_cameras(device):
            if str(cam.get("id") or LEGACY_CAMERA_ID) == self.camera_id:
                return cam
        return None

    @property
    def name(self) -> str:
        """Return entity name including role."""
        device = self._device() or {}
        cam = self._cam() or {}
        device_name = device.get("name", "Taubenschiesser")
        cam_name = (cam.get("name") or "").strip()
        role = cam.get("role") or "slave"
        role_label = "Master" if role == "master" else "Slave"
        if cam_name:
            return f"{device_name} {cam_name}"
        return f"{device_name} {role_label}"

    @property
    def available(self) -> bool:
        """Available when the camera slot still exists on the device."""
        return self._cam() is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Role, type, and camera IP (no credentials)."""
        device = self._device()
        cam = self._cam()
        if not device or not cam:
            return {}
        ip = None
        if cam.get("type") == "tapo":
            ip = (cam.get("tapo") or {}).get("ip")
        elif cam.get("type") in ("raspberry-pi", "esp32-p4"):
            http = cam.get("esp32P4") or cam.get("raspberryPi") or {}
            ip = http.get("ip")
        attrs: dict[str, Any] = {
            "role": cam.get("role"),
            "camera_type": cam.get("type"),
            "camera_id": self.camera_id,
            ATTR_DEVICE_IP: device.get("taubenschiesser", {}).get("ip"),
        }
        if ip:
            attrs["camera_ip"] = ip
        return attrs

    @property
    def device_info(self) -> dict[str, Any]:
        """Attach to the parent Taubenschiesser device."""
        device = self._device()
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

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a JPEG still from the backend (specific cameraId when set)."""
        camera_id = None if self.camera_id == LEGACY_CAMERA_ID else self.camera_id
        return await self.coordinator.async_fetch_camera_jpeg(self.device_id, camera_id)
