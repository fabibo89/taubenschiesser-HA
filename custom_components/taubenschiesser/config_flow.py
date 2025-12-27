"""Config flow for Taubenschiesser integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_API_URL,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_MQTT_BROKER,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_PORT,
    CONF_MQTT_USERNAME,
    DEFAULT_MQTT_PORT,
    DOMAIN,
    API_ENDPOINT_DEVICES,
    API_ENDPOINT_AUTH,
    API_ENDPOINT_REFRESH,
)

_LOGGER = logging.getLogger(__name__)


async def validate_login(api_url: str, email: str, password: str) -> dict[str, str]:
    """Validate login and get tokens."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url.rstrip('/')}{API_ENDPOINT_AUTH}",
                json={"email": email, "password": password},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    access_token = data.get("access_token")
                    refresh_token = data.get("refresh_token")
                    
                    if not access_token:
                        raise InvalidAuth("Kein Token in der Antwort erhalten")
                    
                    return {
                        "access_token": access_token,
                        "refresh_token": refresh_token or "",
                    }
                elif response.status == 401:
                    raise InvalidAuth("Ungültige Anmeldedaten")
                else:
                    error_text = await response.text()
                    raise CannotConnect(f"Login fehlgeschlagen: HTTP {response.status} - {error_text}")
    except aiohttp.ClientConnectorError as err:
        _LOGGER.error("API connection error: %s", err)
        # Check if localhost is used (common Docker issue)
        if "localhost" in api_url.lower() or "127.0.0.1" in api_url:
            raise CannotConnect(
                "Verbindung zu localhost fehlgeschlagen. "
                "Wenn Home Assistant in Docker läuft, verwende stattdessen:\n"
                "- macOS/Windows: host.docker.internal:5001\n"
                "- Linux: Die IP-Adresse deines Hosts (z.B. 192.168.1.100:5001)\n\n"
                f"Original-Fehler: {err}"
            )
        raise CannotConnect(f"Verbindung fehlgeschlagen: {err}")
    except aiohttp.ClientError as err:
        _LOGGER.error("API connection error: %s", err)
        raise CannotConnect(f"Netzwerkfehler: {err}")
    except Exception as err:
        _LOGGER.error("Unexpected error: %s", err)
        raise CannotConnect(f"Unerwarteter Fehler: {err}")


async def validate_api_connection(api_url: str, access_token: str) -> bool:
    """Validate API connection with access token."""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{api_url.rstrip('/')}{API_ENDPOINT_DEVICES}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    return True
                elif response.status == 401:
                    raise InvalidAuth
                else:
                    raise CannotConnect
    except (aiohttp.ClientConnectorError, aiohttp.ClientError, Exception) as err:
        _LOGGER.error("API connection error: %s", err)
        raise CannotConnect(f"Verbindung fehlgeschlagen: {err}")


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Taubenschiesser."""

    VERSION = 2  # Increment version for breaking changes

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Try login with email/password
                tokens = await validate_login(
                    user_input[CONF_API_URL],
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                )
                
                # Validate connection with access token
                await validate_api_connection(
                    user_input[CONF_API_URL],
                    tokens["access_token"],
                )
            except CannotConnect as err:
                error_msg = str(err) if str(err) else "cannot_connect"
                if error_msg != "cannot_connect":
                    errors["base"] = error_msg
                else:
                    errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(user_input[CONF_API_URL])
                self._abort_if_unique_id_configured()

                # Store tokens in config entry
                config_data = {
                    CONF_API_URL: user_input[CONF_API_URL],
                    CONF_EMAIL: user_input[CONF_EMAIL],
                    CONF_ACCESS_TOKEN: tokens["access_token"],
                    CONF_REFRESH_TOKEN: tokens["refresh_token"],
                }
                
                # Add MQTT config if provided
                if user_input.get(CONF_MQTT_BROKER):
                    config_data[CONF_MQTT_BROKER] = user_input[CONF_MQTT_BROKER]
                    config_data[CONF_MQTT_PORT] = user_input.get(CONF_MQTT_PORT, DEFAULT_MQTT_PORT)
                    if user_input.get(CONF_MQTT_USERNAME):
                        config_data[CONF_MQTT_USERNAME] = user_input[CONF_MQTT_USERNAME]
                    if user_input.get(CONF_MQTT_PASSWORD):
                        config_data[CONF_MQTT_PASSWORD] = user_input[CONF_MQTT_PASSWORD]

                return self.async_create_entry(
                    title=f"Taubenschiesser ({user_input[CONF_API_URL]})",
                    data=config_data,
                )

        # Get suggested API URL based on environment
        suggested_api_url = "http://host.docker.internal:5001"
        try:
            # Try to detect if running in Docker
            if self.hass.config.config_dir.startswith("/config"):
                suggested_api_url = "http://host.docker.internal:5001"
            else:
                suggested_api_url = "http://localhost:5001"
        except Exception:
            suggested_api_url = "http://localhost:5001"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_URL, default=suggested_api_url): str,
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_MQTT_BROKER): str,
                vol.Optional(CONF_MQTT_PORT, default=DEFAULT_MQTT_PORT): int,
                vol.Optional(CONF_MQTT_USERNAME): str,
                vol.Optional(CONF_MQTT_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "api_url_example": suggested_api_url,
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
