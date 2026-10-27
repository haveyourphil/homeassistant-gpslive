"""Shared GPSLive entity behaviour, preserving the original device identifiers."""

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GPSLiveCoordinator


class GPSLiveEntity(CoordinatorEntity[GPSLiveCoordinator]):
    """Represent a tracker that may temporarily disappear from the API."""

    def __init__(self, coordinator: GPSLiveCoordinator, imei: str) -> None:
        """Initialize the entity without changing its identifier."""
        super().__init__(coordinator)
        self._imei = imei

    def _device(self) -> dict[str, Any] | None:
        """Find this tracker in the latest successful response."""
        return next(
            (d for d in self.coordinator.data if d.get("imei") == self._imei), None
        )

    def _value(self, *path: str) -> Any:
        """Read optional telemetry safely, including null or malformed subobjects."""
        value = self._device()
        for key in path:
            if not isinstance(value, dict):
                return None
            value = value.get(key)
        return value

    @property
    def available(self) -> bool:
        """Mark missing trackers and failed updates unavailable."""
        return super().available and self._device() is not None

    @property
    def device_info(self) -> DeviceInfo | None:
        """Keep the original IMEI identifier and device metadata."""
        if (device := self._device()) is None:
            return None
        return DeviceInfo(
            identifiers={(DOMAIN, self._imei)},
            name=device.get("name"),
            model=device.get("device"),
            manufacturer="GPSLive",
            serial_number=device.get("vin"),
        )
