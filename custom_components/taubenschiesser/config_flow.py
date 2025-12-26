"""Config flow for Taubenschiesser integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_API_URL,
    CONF_API_TOKEN,
    CONF_MQTT_BROKER,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_PORT,
    CONF_MQTT_USERNAME,
    DEFAULT_MQTT_PORT,
    DOMAIN,
    API_ENDPOINT_DEVICES,
)

_LOGGER = logging.getLogger(__name__)


async def validate_api_connection(api_url: str, api_token: str) -> bool:
    """Validate API connection and token."""
    try:
        headers = {"Authorization": f"Bearer {api_token}"}
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


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Taubenschiesser."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await validate_api_connection(
                    user_input[CONF_API_URL], user_input[CONF_API_TOKEN]
                )
            except CannotConnect as err:
                # Use the error message if available, otherwise use the default
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

                return self.async_create_entry(
                    title=f"Taubenschiesser ({user_input[CONF_API_URL]})",
                    data=user_input,
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_URL): str,
                vol.Required(CONF_API_TOKEN): str,
                vol.Optional(CONF_MQTT_BROKER): str,
                vol.Optional(CONF_MQTT_PORT, default=DEFAULT_MQTT_PORT): int,
                vol.Optional(CONF_MQTT_USERNAME): str,
                vol.Optional(CONF_MQTT_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""

