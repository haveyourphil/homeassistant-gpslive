import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import (
    UnitOfSpeed,
    UnitOfLength,
    UnitOfElectricPotential,
    PERCENTAGE,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.debug("[GPSLive] Setting up sensors")
    try:
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    except Exception as e:
        _LOGGER.error("Coordinator not found in hass.data: %s", e)
        return

    sensors = []
    for device in coordinator.data:
        imei = device["imei"]
        sensors += [
            GPSLiveOdometerSensor(coordinator, imei),
            GPSLiveSpeedSensor(coordinator, imei),
            GPSLiveTrackerBatterySensor(coordinator, imei),
            GPSLiveCarBatterySensor(coordinator, imei),
            GPSLiveStatusSensor(coordinator, imei),
            GPSLiveIgnitionSensor(coordinator, imei),
        ]
    _LOGGER.info("[GPSLive] Initializing %d sensors", len(sensors))
    async_add_entities(sensors)

class GPSLiveSensor(CoordinatorEntity, SensorEntity):
    """Base class for all GPSLive sensors."""
    def __init__(self, coordinator, imei, sensor_type):
        super().__init__(coordinator)
        self._imei = imei
        self._sensor_type = sensor_type
        _LOGGER.debug("[GPSLive] Sensor '%s' initialized for IMEI: %s", sensor_type, imei)

    def _device(self):
        return next((d for d in self.coordinator.data if d.get("imei") == self._imei), None)

    @property
    def name(self):
        d = self._device()
        return f"{d['name']} {self._sensor_type.replace('_', ' ').capitalize()}" if d else f"{self._sensor_type} {self._imei}"

    @property
    def unique_id(self):
        return f"{self._imei}_{self._sensor_type}"

    @property
    def device_info(self):
        d = self._device()
        if not d:
            return None
        return {
            "identifiers": {(DOMAIN, self._imei)},
            "name": d.get("name"),
            "model": d.get("device"),
            "manufacturer": "GPSLive",
            "serial_number": d.get("vin"),
        }

# --- Specific Sensors ---

class GPSLiveOdometerSensor(GPSLiveSensor):
    def __init__(self, coordinator, imei):
        super().__init__(coordinator, imei, "odometer")

    @property
    def native_value(self):
        d = self._device()
        try:
            return int(d.get("odometer"))
        except Exception as ex:
            _LOGGER.debug("Odometer sensor error: %s", ex)
            return None

    @property
    def native_unit_of_measurement(self):
        return UnitOfLength.MILES

    @property
    def device_class(self):
        return SensorDeviceClass.DISTANCE

    @property
    def state_class(self):
        return SensorStateClass.TOTAL

    @property
    def suggested_display_precision(self):
        return 0

class GPSLiveSpeedSensor(GPSLiveSensor):
    def __init__(self, coordinator, imei):
        super().__init__(coordinator, imei, "speed")

    @property
    def native_value(self):
        d = self._device()
        try:
            return int(float(d["objectData"]["data"]["params"].get("speed")) * 0.621371)
        except Exception as ex:
            _LOGGER.debug("Speed sensor error: %s", ex)
            return None

    @property
    def native_unit_of_measurement(self):
        return UnitOfSpeed.MILES_PER_HOUR

    @property
    def device_class(self):
        return SensorDeviceClass.SPEED

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def suggested_display_precision(self):
        return 0

class GPSLiveTrackerBatterySensor(GPSLiveSensor):
    def __init__(self, coordinator, imei):
        super().__init__(coordinator, imei, "tracker_battery")

    @property
    def native_value(self):
        d = self._device()
        try:
            return int(d["objectData"]["data"]["params"].get("batp"))
        except Exception as ex:
            _LOGGER.debug("Tracker battery sensor error: %s", ex)
            return None

    @property
    def native_unit_of_measurement(self):
        return PERCENTAGE

    @property
    def device_class(self):
        return SensorDeviceClass.BATTERY

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def suggested_display_precision(self):
        return 0

class GPSLiveCarBatterySensor(GPSLiveSensor):
    def __init__(self, coordinator, imei):
        super().__init__(coordinator, imei, "car_battery")

    @property
    def native_value(self):
        d = self._device()
        try:
            return float(d["objectData"]["data"]["params"].get("accv"))
        except Exception as ex:
            _LOGGER.debug("Car battery sensor error: %s", ex)
            return None

    @property
    def native_unit_of_measurement(self):
        return UnitOfElectricPotential.VOLT

    @property
    def device_class(self):
        return SensorDeviceClass.VOLTAGE

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def suggested_display_precision(self):
        return 2

class GPSLiveStatusSensor(GPSLiveSensor):
    def __init__(self, coordinator, imei):
        super().__init__(coordinator, imei, "status")

    @property
    def native_value(self):
        d = self._device()
        try:
            return d["objectData"].get("status")
        except Exception as ex:
            _LOGGER.debug("Status sensor error: %s", ex)
            return None

    @property
    def icon(self):
        state = self.native_value
        if state == "moving":
            return "mdi:car-arrow-right"
        return "mdi:car"

class GPSLiveIgnitionSensor(GPSLiveSensor):
    def __init__(self, coordinator, imei):
        super().__init__(coordinator, imei, "ignition")

    @property
    def native_value(self):
        d = self._device()
        try:
            value = d["objectData"]["data"]["params"].get("io239")
            return "on" if value == "1" else "off"
        except Exception as ex:
            _LOGGER.debug("Ignition sensor error: %s", ex)
            return None

    @property
    def icon(self):
        state = self.native_value
        if state == "on":
            return "mdi:engine"
        return "mdi:engine-outline"
