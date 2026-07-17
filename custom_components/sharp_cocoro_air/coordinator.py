"""Data coordinator for SHARP COCORO AIR."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CocoroAirApi, CocoroAirError, CocoroAirStatus
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class CocoroAirCoordinator(DataUpdateCoordinator[CocoroAirStatus]):
    """Poll one SHARP air purifier without duplicating cloud requests."""

    def __init__(self, hass: HomeAssistant, api: CocoroAirApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            always_update=False,
        )
        self.api = api

    async def _async_update_data(self) -> CocoroAirStatus:
        try:
            return await self.api.async_get_status()
        except CocoroAirError as err:
            raise UpdateFailed(str(err)) from err
