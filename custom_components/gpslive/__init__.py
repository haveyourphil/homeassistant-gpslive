"""Set up the GPSLive integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import GPSLiveConfigEntry, GPSLiveCoordinator

PLATFORMS = [Platform.DEVICE_TRACKER, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: GPSLiveConfigEntry) -> bool:
    """Set up GPSLive without changing the stored config entry."""
    coordinator = GPSLiveCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GPSLiveConfigEntry) -> bool:
    """Unload both platforms; the config entry also shuts down its coordinator."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
