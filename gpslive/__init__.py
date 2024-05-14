from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from . import DOMAIN

def setup(hass: HomeAssistant, config: dict):
    # Initialize your integration
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    # Set up your integration from a config entry
    hass.data[DOMAIN] = {
        "api": GpsLiveAPI(entry.data["api_key"])
    }
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    # Unload a config entry
    return True