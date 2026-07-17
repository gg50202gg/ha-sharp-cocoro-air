"""SHARP COCORO AIR Taiwan integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CocoroAirApi, CocoroAirConfig
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
    PLATFORMS,
)
from .coordinator import CocoroAirCoordinator


CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(DOMAIN): vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Required(CONF_APP_SECRET): cv.string,
                vol.Required(CONF_TERMINAL_APP_ID): cv.string,
                vol.Required(CONF_BOX_ID): cv.string,
                vol.Required(CONF_DEVICE_ID): cv.string,
                vol.Required(CONF_ECHONET_NODE): cv.string,
                vol.Optional(
                    CONF_ECHONET_OBJECT, default=DEFAULT_ECHONET_OBJECT
                ): cv.string,
                vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): cv.url,
                vol.Optional(CONF_USER_AGENT, default=DEFAULT_USER_AGENT): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Import a YAML configuration into the config-entry UI."""
    if yaml_config := config.get(DOMAIN):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=dict(yaml_config),
            )
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up an air purifier from a config entry."""
    api = CocoroAirApi(
        async_get_clientsession(hass),
        CocoroAirConfig(
            base_url=entry.data[CONF_BASE_URL],
            app_secret=entry.data[CONF_APP_SECRET],
            terminal_app_id=entry.data[CONF_TERMINAL_APP_ID],
            box_id=entry.data[CONF_BOX_ID],
            device_id=entry.data[CONF_DEVICE_ID],
            echonet_node=entry.data[CONF_ECHONET_NODE],
            echonet_object=entry.data[CONF_ECHONET_OBJECT],
            user_agent=entry.data[CONF_USER_AGENT],
        ),
    )
    coordinator = CocoroAirCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
