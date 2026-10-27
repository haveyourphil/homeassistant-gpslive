"""GPSLive sensors, retaining the existing names, units and unique IDs."""

import math

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfSpeed,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import GPSLiveConfigEntry, GPSLiveCoordinator
from .entity import GPSLiveEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GPSLiveConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the same six sensors per tracker."""
    coordinator = entry.runtime_data
    async_add_entities(
        sensor_class(coordinator, device["imei"])
        for device in coordinator.data
        for sensor_class in (
            GPSLiveOdometerSensor,
            GPSLiveSpeedSensor,
            GPSLiveTrackerBatterySensor,
            GPSLiveCarBatterySensor,
            GPSLiveStatusSensor,
            GPSLiveIgnitionSensor,
        )
    )


class GPSLiveSensor(GPSLiveEntity, SensorEntity):
    """Base class for GPSLive sensors with legacy naming and identity."""

    def __init__(
        self, coordinator: GPSLiveCoordinator, imei: str, sensor_type: str
    ) -> None:
        super().__init__(coordinator, imei)
        self._sensor_type = sensor_type

    @property
    def name(self) -> str:
        if device := self._device():
            return f"{device.get('name', 'GPSLive')} {self._sensor_type.replace('_', ' ').capitalize()}"
        return f"{self._sensor_type} {self._imei}"

    @property
    def unique_id(self) -> str:
        return f"{self._imei}_{self._sensor_type}"

    def _number(self, *path: str, integer: bool = True) -> int | float | None:
        """Convert optional telemetry without swallowing programming errors."""
        try:
            value = self._value(*path)
            result = int(value) if integer else float(value)
            return result if math.isfinite(result) else None
        except (TypeError, ValueError, OverflowError):
            return None


class GPSLiveOdometerSensor(GPSLiveSensor):
    _attr_native_unit_of_measurement = UnitOfLength.MILES
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: GPSLiveCoordinator, imei: str) -> None:
        super().__init__(coordinator, imei, "odometer")

    @property
    def native_value(self) -> int | float | None:
        return self._number("odometer")


class GPSLiveSpeedSensor(GPSLiveSensor):
    _attr_native_unit_of_measurement = UnitOfSpeed.MILES_PER_HOUR
    _attr_device_class = SensorDeviceClass.SPEED
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: GPSLiveCoordinator, imei: str) -> None:
        super().__init__(coordinator, imei, "speed")

    @property
    def native_value(self) -> int | None:
        speed = self._number("objectData", "data", "params", "speed", integer=False)
        return int(speed * 0.621371) if speed is not None else None


class GPSLiveTrackerBatterySensor(GPSLiveSensor):
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: GPSLiveCoordinator, imei: str) -> None:
        super().__init__(coordinator, imei, "tracker_battery")

    @property
    def native_value(self) -> int | float | None:
        return self._number("objectData", "data", "params", "batp")


class GPSLiveCarBatterySensor(GPSLiveSensor):
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: GPSLiveCoordinator, imei: str) -> None:
        super().__init__(coordinator, imei, "car_battery")

    @property
    def native_value(self) -> int | float | None:
        return self._number("objectData", "data", "params", "accv", integer=False)


class GPSLiveStatusSensor(GPSLiveSensor):
    def __init__(self, coordinator: GPSLiveCoordinator, imei: str) -> None:
        super().__init__(coordinator, imei, "status")

    @property
    def native_value(self) -> str | None:
        return self._value("objectData", "status")

    @property
    def icon(self) -> str:
        return "mdi:car-arrow-right" if self.native_value == "moving" else "mdi:car"


class GPSLiveIgnitionSensor(GPSLiveSensor):
    def __init__(self, coordinator: GPSLiveCoordinator, imei: str) -> None:
        super().__init__(coordinator, imei, "ignition")

    @property
    def native_value(self) -> str | None:
        value = self._value("objectData", "data", "params", "io239")
        if value is None:
            return None
        return "on" if str(value) == "1" else "off"

    @property
    def icon(self) -> str:
        return "mdi:engine" if self.native_value == "on" else "mdi:engine-outline"
