"""Sensors for SHARP FP-S90T-W."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import CocoroAirStatus
from .const import DOMAIN
from .coordinator import CocoroAirCoordinator
from .entity import CocoroAirEntity


@dataclass(frozen=True, kw_only=True)
class CocoroSensorDescription:
    key: str
    translation_key: str
    value_fn: Callable[[CocoroAirStatus], int | float | None]
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = SensorStateClass.MEASUREMENT
    native_unit: str | None = None


SENSORS = (
    CocoroSensorDescription(
        key="temperature",
        translation_key="temperature",
        value_fn=lambda data: data.temperature,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit=UnitOfTemperature.CELSIUS,
    ),
    CocoroSensorDescription(
        key="humidity",
        translation_key="humidity",
        value_fn=lambda data: data.humidity,
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit=PERCENTAGE,
    ),
    CocoroSensorDescription(
        key="power",
        translation_key="power",
        value_fn=lambda data: data.power_w,
        device_class=SensorDeviceClass.POWER,
        native_unit=UnitOfPower.WATT,
    ),
    CocoroSensorDescription(
        key="energy",
        translation_key="energy",
        value_fn=lambda data: data.energy_kwh,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit=UnitOfEnergy.KILO_WATT_HOUR,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: CocoroAirCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CocoroAirSensor(coordinator, entry, description) for description in SENSORS
    )


class CocoroAirSensor(CocoroAirEntity, SensorEntity):
    """A decoded SHARP purifier sensor."""

    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: CocoroAirCoordinator,
        entry: ConfigEntry,
        description: CocoroSensorDescription,
    ) -> None:
        super().__init__(coordinator, entry)
        self._description = description
        self._attr_unique_id = f"{coordinator.api.config.device_id}_{description.key}"
        self._attr_translation_key = description.translation_key
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class
        self._attr_native_unit_of_measurement = description.native_unit

    @property
    def native_value(self) -> int | float | None:
        return self._description.value_fn(self.coordinator.data)
