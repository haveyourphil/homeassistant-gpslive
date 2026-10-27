"""GPSLive device trackers."""

import math
from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import GPSLiveConfigEntry
from .entity import GPSLiveEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GPSLiveConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up trackers from the existing config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        GPSLiveTracker(coordinator, device["imei"]) for device in coordinator.data
    )


class GPSLiveTracker(GPSLiveEntity, TrackerEntity):
    """Represent a GPSLive tracker with its original IMEI unique ID."""

    _attr_source_type = SourceType.GPS

    @property
    def unique_id(self) -> str:
        return self._imei

    @property
    def name(self) -> str | None:
        return self._value("name")

    @property
    def latitude(self) -> float | None:
        return self._coordinate("latitude", 90)

    @property
    def longitude(self) -> float | None:
        return self._coordinate("longitude", 180)

    def _coordinate(self, key: str, limit: float) -> float | None:
        """Ignore malformed coordinates before Home Assistant calculates zones."""
        try:
            value = float(self._value("objectData", "data", key))
        except (TypeError, ValueError, OverflowError):
            return None
        return value if math.isfinite(value) and abs(value) <= limit else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attributes = {"last_seen": self._value("objectData", "data", "dtTracker")}
        # Keep the legacy state attribute without overriding HA's deprecated
        # TrackerEntity.battery_level. The battery sensor remains authoritative.
        try:
            attributes["battery_level"] = int(
                self._value("objectData", "data", "params", "batp")
            )
        except (TypeError, ValueError, OverflowError):
            pass
        return attributes
