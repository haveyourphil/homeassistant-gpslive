"""API parsing, failure handling, and redaction through the real coordinator."""

from datetime import timedelta
import logging

import aiohttp
import pytest

from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.gpslive.const import API_DEVICE_ENDPOINT
from custom_components.gpslive.coordinator import (
    GPSLiveCoordinator,
    async_fetch_devices,
)

from .conftest import API_KEY


async def test_request(hass, api, device):
    api.get(API_DEVICE_ENDPOINT, payload=[device])
    session = async_get_clientsession(hass)
    assert await async_fetch_devices(session, API_KEY) == [device]
    request = next(iter(api.requests.values()))[0]
    assert request.kwargs["headers"] == {"Authorization": f"Bearer {API_KEY}"}
    assert request.kwargs["timeout"].total == 30
    assert request.kwargs["allow_redirects"] is False
    assert not session.closed


@pytest.mark.parametrize("status", [401, 403])
async def test_authentication(hass, api, status):
    api.get(API_DEVICE_ENDPOINT, status=status)
    with pytest.raises(ConfigEntryAuthFailed):
        await async_fetch_devices(async_get_clientsession(hass), API_KEY)


@pytest.mark.parametrize("status", [204, 301, 429, 500, 503])
async def test_http_failure(hass, api, status):
    api.get(API_DEVICE_ENDPOINT, status=status)
    with pytest.raises(UpdateFailed, match=f"HTTP {status}"):
        await async_fetch_devices(async_get_clientsession(hass), API_KEY)


@pytest.mark.parametrize(
    "payload",
    [
        {"error": "bad"},
        None,
        [None],
        [{}],
        [{"imei": ""}],
        [{"imei": "x"}, {"imei": "x"}],
    ],
)
async def test_malformed_devices(hass, api, payload):
    api.get(API_DEVICE_ENDPOINT, payload=payload)
    with pytest.raises(UpdateFailed):
        await async_fetch_devices(async_get_clientsession(hass), API_KEY)


@pytest.mark.parametrize(
    "response",
    [
        {"body": "not JSON", "content_type": "application/json"},
        {"body": "<html>oops</html>", "content_type": "text/html"},
        {"exception": TimeoutError(API_KEY)},
        {"exception": aiohttp.ClientConnectionError(API_KEY)},
    ],
)
async def test_response_errors(hass, api, response, caplog):
    api.get(API_DEVICE_ENDPOINT, **response)
    with pytest.raises(UpdateFailed) as error:
        await async_fetch_devices(async_get_clientsession(hass), API_KEY)
    assert API_KEY not in str(error.value)
    assert API_KEY not in caplog.text


async def test_first_refresh_retries(hass, entry, api):
    api.get(API_DEVICE_ENDPOINT, status=500)
    coordinator = GPSLiveCoordinator(hass, entry)
    with pytest.raises(ConfigEntryNotReady):
        await coordinator.async_config_entry_first_refresh()
    await coordinator.async_shutdown()


async def test_poll_failure_and_recovery(hass, entry, api, device, caplog, freezer):
    api.get(API_DEVICE_ENDPOINT, payload=[device])
    coordinator = GPSLiveCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    caplog.set_level(logging.DEBUG)
    for _ in range(2):
        api.get(API_DEVICE_ENDPOINT, exception=aiohttp.ClientConnectionError(API_KEY))
        await coordinator.async_refresh()
        assert not coordinator.last_update_success
        assert coordinator.data == [device]
    errors = [r for r in caplog.records if "Error fetching gpslive data" in r.message]
    assert len(errors) == 1
    assert API_KEY not in caplog.text
    api.get(API_DEVICE_ENDPOINT, payload=[device])
    freezer.tick(timedelta(seconds=1))
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    await coordinator.async_shutdown()
