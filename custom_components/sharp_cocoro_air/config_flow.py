"""Config flow for SHARP COCORO AIR Taiwan."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    CocoroAirApi,
    CocoroAirAuthError,
    CocoroAirConfig,
    CocoroAirConnectionError,
    CocoroAirError,
)
from .const import (
    CONF_APP_SECRET,
    CONF_BASE_URL,
    CONF_BOX_ID,
    CONF_DEVICE_ID,
    CONF_ECHONET_NODE,
    CONF_ECHONET_OBJECT,
    CONF_TERMINAL_APP_ID,
    CONF_USER_AGENT,
    DEFAULT_BASE_URL,
    DEFAULT_ECHONET_OBJECT,
    DEFAULT_NAME,
    DEFAULT_USER_AGENT,
    DOMAIN,
)


STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_APP_SECRET): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
        vol.Required(CONF_TERMINAL_APP_ID): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
        vol.Required(CONF_BOX_ID): str,
        vol.Required(CONF_DEVICE_ID): str,
        vol.Required(CONF_ECHONET_NODE): str,
        vol.Required(CONF_ECHONET_OBJECT, default=DEFAULT_ECHONET_OBJECT): str,
        vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
        vol.Required(CONF_USER_AGENT, default=DEFAULT_USER_AGENT): str,
    }
)


class CocoroAirConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a COCORO AIR config flow."""

    VERSION = 1

    async def async_step_import(self, import_config: dict[str, Any]) -> FlowResult:
        """Create a config entry from configuration.yaml."""
        data = dict(import_config)
        name = data.pop(CONF_NAME, DEFAULT_NAME)
        await self.async_set_unique_id(data[CONF_DEVICE_ID])
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=name, data=data)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            config = CocoroAirConfig(
                base_url=user_input[CONF_BASE_URL].rstrip("/"),
                app_secret=user_input[CONF_APP_SECRET],
                terminal_app_id=user_input[CONF_TERMINAL_APP_ID],
                box_id=user_input[CONF_BOX_ID],
                device_id=user_input[CONF_DEVICE_ID],
                echonet_node=user_input[CONF_ECHONET_NODE],
                echonet_object=user_input[CONF_ECHONET_OBJECT],
                user_agent=user_input[CONF_USER_AGENT],
            )
            try:
                await CocoroAirApi(
                    async_get_clientsession(self.hass), config
                ).async_get_status()
            except CocoroAirAuthError:
                errors["base"] = "invalid_auth"
            except CocoroAirConnectionError:
                errors["base"] = "cannot_connect"
            except CocoroAirError:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
                self._abort_if_unique_id_configured()
                name = user_input.pop(CONF_NAME)
                user_input[CONF_BASE_URL] = config.base_url
                return self.async_create_entry(title=name, data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )
