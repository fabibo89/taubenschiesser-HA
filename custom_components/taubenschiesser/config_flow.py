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


def _normalize_api_url(api_url: str) -> str:
    """Strip whitespace and trailing slash from API URL."""
    return api_url.strip().rstrip("/")


def _build_entry_data(
    *,
    api_url: str,
    email: str,
    password: str,
    tokens: dict[str, str],
    user_input: dict[str, Any],
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build config entry data from form input and login tokens."""
    data = {
        CONF_API_URL: api_url,
        CONF_EMAIL: email,
        CONF_PASSWORD: password,
        CONF_ACCESS_TOKEN: tokens["access_token"],
        CONF_REFRESH_TOKEN: tokens["refresh_token"],
    }
    broker = (user_input.get(CONF_MQTT_BROKER) or "").strip()
    if not broker:
        return data

    data[CONF_MQTT_BROKER] = broker
    data[CONF_MQTT_PORT] = user_input.get(CONF_MQTT_PORT, DEFAULT_MQTT_PORT)

    username = (user_input.get(CONF_MQTT_USERNAME) or "").strip()
    mqtt_password = user_input.get(CONF_MQTT_PASSWORD) or ""
    if previous:
        if not username:
            username = previous.get(CONF_MQTT_USERNAME) or ""
        if not mqtt_password:
            mqtt_password = previous.get(CONF_MQTT_PASSWORD) or ""
    if username:
        data[CONF_MQTT_USERNAME] = username
    if mqtt_password:
        data[CONF_MQTT_PASSWORD] = mqtt_password
    return data


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
    except InvalidAuth:
        raise
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
    except InvalidAuth:
        raise
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
                api_url = _normalize_api_url(user_input[CONF_API_URL])
                await self.async_set_unique_id(api_url)
                self._abort_if_unique_id_configured()

                config_data = _build_entry_data(
                    api_url=api_url,
                    email=user_input[CONF_EMAIL],
                    password=user_input[CONF_PASSWORD],
                    tokens=tokens,
                    user_input=user_input,
                )

                return self.async_create_entry(
                    title=f"Taubenschiesser ({api_url})",
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

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration after a server move or credential change."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            password = user_input.get(CONF_PASSWORD) or entry.data.get(CONF_PASSWORD)
            if not password:
                errors[CONF_PASSWORD] = "password_required"
            else:
                try:
                    tokens = await validate_login(
                        user_input[CONF_API_URL],
                        user_input[CONF_EMAIL],
                        password,
                    )
                    await validate_api_connection(
                        user_input[CONF_API_URL],
                        tokens["access_token"],
                    )
                except CannotConnect as err:
                    error_msg = str(err) if str(err) else "cannot_connect"
                    errors["base"] = (
                        error_msg if error_msg != "cannot_connect" else "cannot_connect"
                    )
                except InvalidAuth:
                    errors["base"] = "invalid_auth"
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected exception during reconfigure")
                    errors["base"] = "unknown"
                else:
                    api_url = _normalize_api_url(user_input[CONF_API_URL])
                    for other in self.hass.config_entries.async_entries(DOMAIN):
                        if (
                            other.entry_id != entry.entry_id
                            and other.unique_id == api_url
                        ):
                            return self.async_abort(reason="already_configured")

                    config_data = _build_entry_data(
                        api_url=api_url,
                        email=user_input[CONF_EMAIL],
                        password=password,
                        tokens=tokens,
                        user_input=user_input,
                        previous=dict(entry.data),
                    )
                    return self.async_update_reload_and_abort(
                        entry,
                        unique_id=api_url,
                        title=f"Taubenschiesser ({api_url})",
                        data=config_data,
                    )

        source = user_input if user_input is not None else entry.data
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_API_URL, default=source.get(CONF_API_URL, "")
                ): str,
                vol.Required(CONF_EMAIL, default=source.get(CONF_EMAIL, "")): str,
                vol.Optional(CONF_PASSWORD): str,
                vol.Optional(
                    CONF_MQTT_BROKER,
                    default=source.get(CONF_MQTT_BROKER, ""),
                ): str,
                vol.Optional(
                    CONF_MQTT_PORT,
                    default=source.get(CONF_MQTT_PORT, DEFAULT_MQTT_PORT),
                ): int,
                vol.Optional(
                    CONF_MQTT_USERNAME,
                    default=source.get(CONF_MQTT_USERNAME, ""),
                ): str,
                vol.Optional(CONF_MQTT_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=data_schema,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
