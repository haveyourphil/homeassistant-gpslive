import logging
import aiohttp
from datetime import timedelta
from homeassistant.components.device_tracker import TrackerEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from .const import DOMAIN, API_DEVICE_ENDPOINT, CONF_API_KEY

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.debug("[GPSLive] Setting up device tracker")
    try:
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    except Exception as e:
        _LOGGER.error("Coordinator not found in hass.data: %s", e)
        return

    entities = [
        GPSLiveTracker(coordinator, device["imei"])
        for device in coordinator.data
    ]
    _LOGGER.info("[GPSLive] Initializing %d tracker entities", len(entities))
    async_add_entities(entities)

class GPSLiveTracker(CoordinatorEntity, TrackerEntity):
    def __init__(self, coordinator, imei):
        super().__init__(coordinator)
        self._imei = imei
        _LOGGER.debug("[GPSLive] Tracker entity initialized for IMEI: %s", imei)

    def _device(self):
        dev = next((d for d in self.coordinator.data if d.get("imei") == self._imei), None)
        if dev is None:
            _LOGGER.error("[GPSLive] Device with IMEI %s not found in coordinator data", self._imei)
        return dev

    @property
    def unique_id(self):
        return self._imei

    @property
    def name(self):
        d = self._device()
        return d.get("name") if d else None

    @property
    def latitude(self):
        d = self._device()
        return d["objectData"]["data"].get("latitude") if d else None

    @property
    def longitude(self):
        d = self._device()
        return d["objectData"]["data"].get("longitude") if d else None

    @property
    def battery_level(self):
        d = self._device()
        try:
            return int(d["objectData"]["data"]["params"].get("batp"))
        except Exception:
            return None

    @property
    def source_type(self):
        return "gps"

    @property
    def extra_state_attributes(self):
        d = self._device()
        return {
            "last_seen": d["objectData"]["data"].get("dtTracker") if d else None,
        }

    @property
    def device_info(self):
        d = self._device()
        if not d:
            return None
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": d.get("name"),
            "model": d.get("device"),
            "manufacturer": "GPSLive",
            "serial_number": d.get("vin"),
        }
