"""Provide useful status without credentials or location and vehicle data."""

from typing import Any

from homeassistant.core import HomeAssistant

from .coordinator import GPSLiveConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: GPSLiveConfigEntry
) -> dict[str, Any]:
    """Report only operational counts and flags, never raw API/entry data."""
    coordinator = entry.runtime_data
    return {
        "config_entry_version": entry.version,
        "last_update_success": coordinator.last_update_success,
        "device_count": len(coordinator.data) if coordinator.data is not None else 0,
        "polling_interval_seconds": coordinator.update_interval.total_seconds(),
    }
