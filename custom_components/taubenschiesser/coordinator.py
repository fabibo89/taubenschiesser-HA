"""Data update coordinator for Taubenschiesser."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
import paho.mqtt.client as mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_ENDPOINT_DEVICES,
    API_ENDPOINT_REFRESH,
    ATTR_DEVICE_IP,
    ATTR_LAST_MQTT,
    ATTR_LAST_SEEN,
    ATTR_MONITOR_STATUS,
    ATTR_MOVING,
    ATTR_ROTATION,
    ATTR_STATUS,
    ATTR_TILT,
    CONF_API_URL,
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_EMAIL,
    CONF_MQTT_BROKER,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_PORT,
    CONF_MQTT_USERNAME,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MQTT_TOPIC_STATUS,
)

_LOGGER = logging.getLogger(__name__)


class TaubenschiesserDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API and MQTT."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )
        self.hass = hass
        self.entry = entry
        self.api_url = entry.data[CONF_API_URL].rstrip("/")
        
        # Token management
        self.access_token = entry.data[CONF_ACCESS_TOKEN]
        self.refresh_token = entry.data.get(CONF_REFRESH_TOKEN)
        self.session = async_get_clientsession(hass)
        
        self.mqtt_broker = entry.data.get(CONF_MQTT_BROKER)
        self.mqtt_port = entry.data.get(CONF_MQTT_PORT, 1883)
        self.mqtt_username = entry.data.get(CONF_MQTT_USERNAME)
        self.mqtt_password = entry.data.get(CONF_MQTT_PASSWORD)
        
        self.mqtt_client: mqtt.Client | None = None
        self.devices: dict[str, dict[str, Any]] = {}
        self.device_positions: dict[str, dict[str, Any]] = {}
        self._token_expired_notified = False

    async def _ensure_token_valid(self) -> None:
        """Ensure access token is valid, refresh if needed."""
        if not self.access_token:
            raise UpdateFailed("Kein Access Token verfügbar")
        
        # Try a test request to check if token is still valid
        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            async with self.session.get(
                f"{self.api_url}/api/auth/me",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                if response.status == 200:
                    return  # Token is valid
                elif response.status == 401:
                    # Token expired, try refresh
                    _LOGGER.debug("Access Token abgelaufen, versuche Refresh")
                    await self._refresh_token()
        except Exception as e:
            _LOGGER.debug("Fehler beim Token-Check: %s", e)
            # Try refresh anyway if we have refresh token
            if self.refresh_token:
                await self._refresh_token()

    async def _refresh_token(self) -> None:
        """Refresh access token using refresh token."""
        if not self.refresh_token:
            raise UpdateFailed("Kein Refresh Token verfügbar")
        
        try:
            async with self.session.post(
                f"{self.api_url}{API_ENDPOINT_REFRESH}",
                json={"refresh_token": self.refresh_token},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    new_access_token = token_data.get("access_token")
                    new_refresh_token = token_data.get("refresh_token")
                    
                    if not new_access_token:
                        raise UpdateFailed("Kein Access Token in Refresh-Antwort erhalten")
                    
                    self.access_token = new_access_token
                    if new_refresh_token:
                        self.refresh_token = new_refresh_token
                    
                    # Update config entry with new tokens
                    new_data = self.entry.data.copy()
                    new_data[CONF_ACCESS_TOKEN] = self.access_token
                    if new_refresh_token:
                        new_data[CONF_REFRESH_TOKEN] = self.refresh_token
                    
                    self.hass.config_entries.async_update_entry(self.entry, data=new_data)
                    
                    _LOGGER.debug("Token erfolgreich aktualisiert")
                    
                    # Dismiss notification if shown
                    if self._token_expired_notified:
                        self.hass.async_create_task(
                            self.hass.services.async_call(
                                "persistent_notification",
                                "dismiss",
                                {"notification_id": f"{DOMAIN}_token_expired"},
                            )
                        )
                        self._token_expired_notified = False
                else:
                    error_text = await response.text()
                    raise UpdateFailed(f"Token-Refresh fehlgeschlagen: HTTP {response.status} - {error_text}")
        except aiohttp.ClientError as e:
            _LOGGER.error("Fehler beim Token-Refresh: %s", e)
            raise UpdateFailed(f"Token-Refresh fehlgeschlagen: {e}")
        except Exception as e:
            _LOGGER.error("Fehler beim Token-Refresh: %s", e)
            raise UpdateFailed(f"Token-Refresh fehlgeschlagen: {e}")

    def _show_token_expired_notification(self) -> None:
        """Show persistent notification about expired token."""
        if not self._token_expired_notified:
            # Use service call instead of direct import
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "🔑 Taubenschiesser: Token abgelaufen",
                        "message": (
                            "Dein Access Token ist abgelaufen.\n\n"
                            "**Automatische Erneuerung:**\n"
                            "Die Integration versucht automatisch, den Token zu erneuern. "
                            "Falls dies fehlschlägt, bitte die Integration neu konfigurieren.\n\n"
                            "Gehe zu: Einstellungen → Geräte & Dienste → Taubenschiesser → Konfigurieren"
                        ),
                        "notification_id": f"{DOMAIN}_token_expired",
                    },
                )
            )
            self._token_expired_notified = True
            _LOGGER.error(
                "Access Token ist abgelaufen. Versuche automatische Erneuerung..."
            )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # Ensure token is valid (will refresh if needed)
            if self.refresh_token:
                await self._ensure_token_valid()
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self.session.get(
                f"{self.api_url}{API_ENDPOINT_DEVICES}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    # Reset notification flag on successful request
                    if self._token_expired_notified:
                        self.hass.async_create_task(
                            self.hass.services.async_call(
                                "persistent_notification",
                                "dismiss",
                                {"notification_id": f"{DOMAIN}_token_expired"},
                            )
                        )
                        self._token_expired_notified = False
                    
                    devices = await response.json()
                    self.devices = {device["_id"]: device for device in devices}
                    
                    # Merge with MQTT position data
                    for device_id, device in self.devices.items():
                        device_ip = device.get("taubenschiesser", {}).get("ip")
                        if device_ip and device_ip in self.device_positions:
                            pos_data = self.device_positions[device_ip]
                            device[ATTR_ROTATION] = pos_data.get("rot", 0)
                            device[ATTR_TILT] = pos_data.get("tilt", 0)
                            device[ATTR_MOVING] = pos_data.get("moving", False)
                            # Extract timeMQTT if available
                            if "timeMQTT" in pos_data:
                                device[ATTR_LAST_MQTT] = pos_data.get("timeMQTT")
                        else:
                            device[ATTR_ROTATION] = 0
                            device[ATTR_TILT] = 0
                            device[ATTR_MOVING] = False
                        
                        # Set status - use overall status from device, or calculate from taubenschiesserStatus/cameraStatus
                        device[ATTR_STATUS] = device.get("status", "unknown")
                        if device[ATTR_STATUS] == "unknown" or not device.get("status"):
                            # Calculate status from component statuses
                            taubenschiesser_status = device.get("taubenschiesserStatus", "offline")
                            camera_status = device.get("cameraStatus", "offline")
                            if taubenschiesser_status == "online" and camera_status == "online":
                                device[ATTR_STATUS] = "online"
                            elif taubenschiesser_status == "error" or camera_status == "error":
                                device[ATTR_STATUS] = "error"
                            elif taubenschiesser_status == "maintenance" or camera_status == "maintenance":
                                device[ATTR_STATUS] = "maintenance"
                            else:
                                device[ATTR_STATUS] = "offline"
                    
                    # Subscribe to new devices if MQTT is connected
                    if self.mqtt_client and self.mqtt_client.is_connected():
                        await self.hass.async_add_executor_job(
                            self._subscribe_to_devices, self.mqtt_client
                        )
                    
                    return {"devices": self.devices}
                elif response.status == 401:
                    # Token expired or invalid
                    error_text = await response.text()
                    
                    # Try to refresh if we have refresh token
                    if self.refresh_token:
                        try:
                            self._show_token_expired_notification()
                            await self._refresh_token()
                            # Retry request with new token
                            headers = {"Authorization": f"Bearer {self.access_token}"}
                            async with self.session.get(
                                f"{self.api_url}{API_ENDPOINT_DEVICES}",
                                headers=headers,
                                timeout=aiohttp.ClientTimeout(total=10),
                            ) as retry_response:
                                if retry_response.status == 200:
                                    devices = await retry_response.json()
                                    self.devices = {device["_id"]: device for device in devices}
                                    
                                    # Merge with MQTT position data
                                    for device_id, device in self.devices.items():
                                        device_ip = device.get("taubenschiesser", {}).get("ip")
                                        if device_ip and device_ip in self.device_positions:
                                            pos_data = self.device_positions[device_ip]
                                            device[ATTR_ROTATION] = pos_data.get("rot", 0)
                                            device[ATTR_TILT] = pos_data.get("tilt", 0)
                                            device[ATTR_MOVING] = pos_data.get("moving", False)
                                            # Extract timeMQTT if available
                                            if "timeMQTT" in pos_data:
                                                device[ATTR_LAST_MQTT] = pos_data.get("timeMQTT")
                                        else:
                                            device[ATTR_ROTATION] = 0
                                            device[ATTR_TILT] = 0
                                            device[ATTR_MOVING] = False
                                        
                                        # Set status
                                        device[ATTR_STATUS] = device.get("status", "unknown")
                                        if device[ATTR_STATUS] == "unknown" or not device.get("status"):
                                            taubenschiesser_status = device.get("taubenschiesserStatus", "offline")
                                            camera_status = device.get("cameraStatus", "offline")
                                            if taubenschiesser_status == "online" and camera_status == "online":
                                                device[ATTR_STATUS] = "online"
                                            elif taubenschiesser_status == "error" or camera_status == "error":
                                                device[ATTR_STATUS] = "error"
                                            elif taubenschiesser_status == "maintenance" or camera_status == "maintenance":
                                                device[ATTR_STATUS] = "maintenance"
                                            else:
                                                device[ATTR_STATUS] = "offline"
                                    
                                    return {"devices": self.devices}
                                else:
                                    raise UpdateFailed(
                                        f"API-Fehler nach Token-Refresh (Status {retry_response.status})"
                                    )
                        except Exception as refresh_err:
                            _LOGGER.error("Fehler beim Token-Refresh: %s", refresh_err)
                            raise UpdateFailed(
                                "API Token ist abgelaufen und konnte nicht erneuert werden. "
                                "Bitte konfiguriere die Integration neu."
                            )
                    else:
                        self._show_token_expired_notification()
                        raise UpdateFailed(
                            "API Token ist abgelaufen. Bitte konfiguriere die Integration neu."
                        )
                else:
                    error_text = await response.text()
                    raise UpdateFailed(
                        f"API-Fehler (Status {response.status}): {error_text}"
                    )
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Netzwerkfehler bei API-Verbindung: {err}") from err

    async def async_config_entry_first_refresh(self) -> None:
        """Refresh data for the first time and setup MQTT if configured."""
        await super().async_config_entry_first_refresh()
        
        if self.mqtt_broker:
            await self._setup_mqtt()

    def _subscribe_to_devices(self, client: mqtt.Client) -> None:
        """Subscribe to MQTT topics for all devices."""
        for device in self.devices.values():
            device_ip = device.get("taubenschiesser", {}).get("ip")
            if device_ip:
                topic = MQTT_TOPIC_STATUS.format(ip=device_ip)
                client.subscribe(topic)
                _LOGGER.info("Subscribed to %s", topic)

    async def _setup_mqtt(self) -> None:
        """Setup MQTT connection for real-time updates."""
        if self.mqtt_client:
            return

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                _LOGGER.info("MQTT connected")
                # Subscribe to all device status topics
                self._subscribe_to_devices(client)
            else:
                _LOGGER.error("MQTT connection failed with code %s", rc)

        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                topic_parts = msg.topic.split("/")
                if len(topic_parts) >= 2:
                    device_ip = topic_parts[1]
                    
                    # Update position data - extract timeMQTT if available
                    position_data = {
                        "rot": payload.get("Rot", 0),
                        "tilt": payload.get("Tilt", 0),
                        "moving": payload.get("moving", False),
                        "watertank": payload.get("watertank", True),
                        "cam": payload.get("Cam", False),
                    }
                    # Extract timeMQTT if present
                    if "timeMQTT" in payload:
                        position_data["timeMQTT"] = payload.get("timeMQTT")
                    
                    self.device_positions[device_ip] = position_data
                    
                    # Update device data if we have it
                    for device_id, device in self.devices.items():
                        if device.get("taubenschiesser", {}).get("ip") == device_ip:
                            device[ATTR_ROTATION] = payload.get("Rot", 0)
                            device[ATTR_TILT] = payload.get("Tilt", 0)
                            device[ATTR_MOVING] = payload.get("moving", False)
                            # Update timeMQTT if available
                            if "timeMQTT" in payload:
                                device[ATTR_LAST_MQTT] = payload.get("timeMQTT")
                            break
                    
                    # Trigger coordinator update
                    self.hass.loop.call_soon_threadsafe(
                        self.async_set_updated_data, {"devices": self.devices}
                    )
            except Exception as err:
                _LOGGER.error("Error processing MQTT message: %s", err)

        def on_disconnect(client, userdata, rc):
            _LOGGER.warning("MQTT disconnected with code %s", rc)

        self.mqtt_client = mqtt.Client()
        if self.mqtt_username:
            self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)
        
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_message = on_message
        self.mqtt_client.on_disconnect = on_disconnect

        # Connect in executor to avoid blocking
        await self.hass.async_add_executor_job(
            self.mqtt_client.connect, self.mqtt_broker, self.mqtt_port, 60
        )
        self.mqtt_client.loop_start()
        _LOGGER.info("MQTT client started")
        
        # Subscribe to devices after initial data load
        if self.devices:
            await self.hass.async_add_executor_job(
                self._subscribe_to_devices, self.mqtt_client
            )

    async def async_shutdown(self) -> None:
        """Shutdown coordinator and MQTT connection."""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.mqtt_client = None

    async def send_mqtt_command(self, device_ip: str, command: dict[str, Any]) -> None:
        """Send MQTT command to device."""
        if not self.mqtt_client or not self.mqtt_client.is_connected():
            raise Exception("MQTT client not connected")
        
        topic = f"taubenschiesser/{device_ip}"
        payload = json.dumps(command)
        
        def publish():
            result = self.mqtt_client.publish(topic, payload)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                raise Exception(f"MQTT publish failed: {result.rc}")
        
        await self.hass.async_add_executor_job(publish)
        _LOGGER.info("Sent MQTT command to %s: %s", topic, payload)

    async def send_api_command(self, device_id: str, action: str) -> None:
        """Send command via API."""
        # Ensure token is valid
        if self.refresh_token:
            await self._ensure_token_valid()
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            async with self.session.post(
                f"{self.api_url}/api/device-control/{device_id}/control",
                headers=headers,
                json={"action": action},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 401:
                    # Try refresh if we have refresh token
                    if self.refresh_token:
                        await self._refresh_token()
                        headers = {"Authorization": f"Bearer {self.access_token}"}
                        async with self.session.post(
                            f"{self.api_url}/api/device-control/{device_id}/control",
                            headers=headers,
                            json={"action": action},
                            timeout=aiohttp.ClientTimeout(total=10),
                        ) as retry_response:
                            if retry_response.status != 200:
                                error_text = await retry_response.text()
                                raise Exception(
                                    f"API-Befehl fehlgeschlagen (Status {retry_response.status}): {error_text}"
                                )
                    else:
                        raise Exception(
                            "API Token ist abgelaufen. Bitte konfiguriere die Integration neu."
                        )
                elif response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"API-Befehl fehlgeschlagen (Status {response.status}): {error_text}"
                    )
        except aiohttp.ClientError as err:
            raise Exception(f"Netzwerkfehler beim Senden des Befehls: {err}") from err

    async def send_api_start_pause(self, device_id: str, action: str) -> None:
        """Send start/pause command via API."""
        # Ensure token is valid
        if self.refresh_token:
            await self._ensure_token_valid()
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            async with self.session.post(
                f"{self.api_url}/api/device-control/{device_id}/{action}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 401:
                    # Try refresh if we have refresh token
                    if self.refresh_token:
                        await self._refresh_token()
                        headers = {"Authorization": f"Bearer {self.access_token}"}
                        async with self.session.post(
                            f"{self.api_url}/api/device-control/{device_id}/{action}",
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=10),
                        ) as retry_response:
                            if retry_response.status != 200:
                                error_text = await retry_response.text()
                                raise Exception(
                                    f"API-Befehl fehlgeschlagen (Status {retry_response.status}): {error_text}"
                                )
                    else:
                        raise Exception(
                            "API Token ist abgelaufen. Bitte konfiguriere die Integration neu."
                        )
                elif response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"API-Befehl fehlgeschlagen (Status {response.status}): {error_text}"
                    )
        except aiohttp.ClientError as err:
            raise Exception(f"Netzwerkfehler beim Senden des Befehls: {err}") from err
