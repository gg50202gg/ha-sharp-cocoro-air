"""Fan entity for SHARP FP-S90T-W."""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, PRESET_TO_CODE
from .coordinator import CocoroAirCoordinator
from .entity import CocoroAirEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: CocoroAirCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CocoroAirFan(coordinator, entry)])


class CocoroAirFan(CocoroAirEntity, FanEntity):
    """Representation of a SHARP COCORO AIR purifier."""

    _attr_translation_key = "air_purifier"
    _attr_supported_features = (
        FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = list(PRESET_TO_CODE)

    def __init__(self, coordinator: CocoroAirCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = coordinator.api.config.device_id

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.is_on

    @property
    def preset_mode(self) -> str | None:
        return self.coordinator.data.preset_mode

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        if not self.is_on:
            await self.coordinator.api.async_set_power(True)
            # The purifier needs five seconds before it accepts mode commands.
            await asyncio.sleep(5)
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
        else:
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api.async_set_power(False)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode not in PRESET_TO_CODE:
            raise ValueError(f"Unsupported preset mode: {preset_mode}")
        await self.coordinator.api.async_set_preset(PRESET_TO_CODE[preset_mode])
        await self.coordinator.async_request_refresh()
