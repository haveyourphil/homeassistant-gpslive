"""Fetch GPSLive data using Home Assistant's shared HTTP session."""

from datetime import timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_DEVICE_ENDPOINT, CONF_API_KEY, DOMAIN

_LOGGER = logging.getLogger(__name__)
type GPSLiveData = list[dict[str, Any]]
type GPSLiveConfigEntry = ConfigEntry[GPSLiveCoordinator]


async def async_fetch_devices(
    session: aiohttp.ClientSession, api_key: str
) -> GPSLiveData:
    """Fetch and validate devices without exposing credentials or response bodies."""
    try:
        async with session.get(
            API_DEVICE_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=aiohttp.ClientTimeout(total=30),
            allow_redirects=False,
        ) as response:
            if response.status in (401, 403):
                raise ConfigEntryAuthFailed("GPSLive rejected the API key")
            if response.status != 200:
                raise UpdateFailed(f"GPSLive returned HTTP {response.status}")
            data = await response.json()
    except TimeoutError:
        raise UpdateFailed("Timed out connecting to GPSLive") from None
    except (aiohttp.ClientError, ValueError, UnicodeError):
        # HTTP exception strings may contain headers, URLs or response data.
        raise UpdateFailed("Unable to read a valid response from GPSLive") from None

    if not isinstance(data, list):
        raise UpdateFailed("GPSLive returned an invalid device list")
    identifiers: set[str] = set()
    for device in data:
        if (
            not isinstance(device, dict)
            or not isinstance(imei := device.get("imei"), str)
            or not imei
            or imei in identifiers
        ):
            raise UpdateFailed(
                "GPSLive returned missing or duplicate device identifiers"
            )
        identifiers.add(imei)
    return data


class GPSLiveCoordinator(DataUpdateCoordinator[GPSLiveData]):
    """Poll all trackers once per minute while entities are listening."""

    config_entry: GPSLiveConfigEntry

    def __init__(self, hass: HomeAssistant, entry: GPSLiveConfigEntry) -> None:
        """Initialize polling and register cleanup with the config entry."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
            always_update=False,
        )
        self._session = async_get_clientsession(hass)

    async def _async_update_data(self) -> GPSLiveData:
        """Fetch data; the coordinator handles retries, availability and reauth."""
        return await async_fetch_devices(
            self._session, self.config_entry.data[CONF_API_KEY]
        )
