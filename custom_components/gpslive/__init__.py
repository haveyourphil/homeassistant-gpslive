from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import aiohttp
from datetime import timedelta
import logging
from .const import DOMAIN, CONF_API_KEY

PLATFORMS = ["device_tracker", "sensor"]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api_key = entry.data[CONF_API_KEY]

    async def async_fetch():
        ## API Docs: https://api.gpslive.app/api-docs/v1
        headers = {"Authorization": f"Bearer {api_key}"}
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.gpslive.app/v1/devices", headers=headers) as response:
                data = await response.json()
                _LOGGER.debug("[GPSLive] API returned %d devices", len(data))
                return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="gpslive_tracker",
        update_method=async_fetch,
        update_interval=timedelta(minutes=1),
    )
    await coordinator.async_config_entry_first_refresh()
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return True
