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

from .const import (
    API_ENDPOINT_DEVICES,
    ATTR_DEVICE_IP,
    ATTR_LAST_SEEN,
    ATTR_MONITOR_STATUS,
    ATTR_MOVING,
    ATTR_ROTATION,
    ATTR_TILT,
    CONF_API_TOKEN,
    CONF_API_URL,
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
        self.api_token = entry.data[CONF_API_TOKEN]
        self.mqtt_broker = entry.data.get(CONF_MQTT_BROKER)
        self.mqtt_port = entry.data.get(CONF_MQTT_PORT, 1883)
        self.mqtt_username = entry.data.get(CONF_MQTT_USERNAME)
        self.mqtt_password = entry.data.get(CONF_MQTT_PASSWORD)
        
        self.mqtt_client: mqtt.Client | None = None
        self.devices: dict[str, dict[str, Any]] = {}
        self.device_positions: dict[str, dict[str, Any]] = {}
        self._token_expired_notified = False

    def _show_token_expired_notification(self) -> None:
        """Show persistent notification about expired token."""
        if not self._token_expired_notified:
            # Use service call instead of direct import
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "🔑 Taubenschiesser: API Token abgelaufen",
                        "message": (
                            "Dein API Token ist abgelaufen (Gültigkeit: 7 Tage).\n\n"
                            "**So bekommst du einen neuen Token:**\n"
                            "1. Öffne das Taubenschiesser Dashboard\n"
                            "2. Logge dich ein\n"
                            "3. Entwicklertools (F12) → Application → Local Storage → 'token'\n"
                            "4. Kopiere den Token\n"
                            "5. Gehe zu: Einstellungen → Geräte & Dienste → Taubenschiesser → Konfigurieren\n"
                            "6. Füge den neuen Token ein und speichere\n\n"
                            "**Alternative:** Terminal: `curl -X POST http://localhost:5001/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"deine@email.de\",\"password\":\"dein-passwort\"}'`"
                        ),
                        "notification_id": f"{DOMAIN}_token_expired",
                    },
                )
            )
            self._token_expired_notified = True
            _LOGGER.error(
                "API Token ist abgelaufen. Bitte erneuere den Token in den Integrationseinstellungen."
            )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            headers = {"Authorization": f"Bearer {self.api_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(
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
                            else:
                                device[ATTR_ROTATION] = 0
                                device[ATTR_TILT] = 0
                                device[ATTR_MOVING] = False
                        
                        # Subscribe to new devices if MQTT is connected
                        if self.mqtt_client and self.mqtt_client.is_connected():
                            await self.hass.async_add_executor_job(
                                self._subscribe_to_devices, self.mqtt_client
                            )
                        
                        return {"devices": self.devices}
                    elif response.status == 401:
                        # Token expired or invalid
                        error_text = await response.text()
                        self._show_token_expired_notification()
                        raise UpdateFailed(
                            "API Token ist abgelaufen oder ungültig. "
                            "Bitte erneuere den Token in den Integrationseinstellungen. "
                            f"API-Antwort: {error_text}"
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
                    
                    # Update position data
                    self.device_positions[device_ip] = {
                        "rot": payload.get("Rot", 0),
                        "tilt": payload.get("Tilt", 0),
                        "moving": payload.get("moving", False),
                        "watertank": payload.get("watertank", True),
                        "cam": payload.get("Cam", False),
                    }
                    
                    # Update device data if we have it
                    for device_id, device in self.devices.items():
                        if device.get("taubenschiesser", {}).get("ip") == device_ip:
                            device[ATTR_ROTATION] = payload.get("Rot", 0)
                            device[ATTR_TILT] = payload.get("Tilt", 0)
                            device[ATTR_MOVING] = payload.get("moving", False)
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
        headers = {"Authorization": f"Bearer {self.api_token}"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/device-control/{device_id}/control",
                    headers=headers,
                    json={"action": action},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 401:
                        self._show_token_expired_notification()
                        raise Exception(
                            "API Token ist abgelaufen. Bitte erneuere den Token in den Integrationseinstellungen."
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
        headers = {"Authorization": f"Bearer {self.api_token}"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/device-control/{device_id}/{action}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 401:
                        self._show_token_expired_notification()
                        raise Exception(
                            "API Token ist abgelaufen. Bitte erneuere den Token in den Integrationseinstellungen."
                        )
                    elif response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"API-Befehl fehlgeschlagen (Status {response.status}): {error_text}"
                        )
        except aiohttp.ClientError as err:
            raise Exception(f"Netzwerkfehler beim Senden des Befehls: {err}") from err

