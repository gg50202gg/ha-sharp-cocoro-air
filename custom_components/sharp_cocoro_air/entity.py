"""Entity base for SHARP COCORO AIR."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CocoroAirCoordinator


class CocoroAirEntity(CoordinatorEntity[CocoroAirCoordinator]):
    """Base class shared by purifier entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CocoroAirCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        device_id = coordinator.api.config.device_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer="SHARP",
            model="FP-S90T-W",
            name=entry.title,
        )
