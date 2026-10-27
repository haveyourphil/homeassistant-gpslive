"""API parsing, failure handling, and redaction through the real coordinator."""

from datetime import timedelta
import logging
from unittest.mock import patch

import aiohttp
import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.gpslive.const import API_DEVICE_ENDPOINT
from custom_components.gpslive.coordinator import (
    GPSLiveCoordinator,
    async_fetch_devices,
)

from .conftest import API_KEY


async def test_request(hass, api, device):
    api.get(API_DEVICE_ENDPOINT, json=[device])
    session = async_get_clientsession(hass)
    with patch.object(session, "get", wraps=session.get) as request:
        assert await async_fetch_devices(session, API_KEY) == [device]
    assert request.call_args.kwargs["headers"] == {"Authorization": f"Bearer {API_KEY}"}
    assert request.call_args.kwargs["timeout"].total == 30
    assert request.call_args.kwargs["allow_redirects"] is False
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
    api.get(API_DEVICE_ENDPOINT, json=payload)
    with pytest.raises(UpdateFailed):
        await async_fetch_devices(async_get_clientsession(hass), API_KEY)


@pytest.mark.parametrize(
    "response",
    [
        {"text": "not JSON"},
        {"exc": aiohttp.ContentTypeError(None, (), message="Unexpected content type")},
        {"exc": TimeoutError(API_KEY)},
        {"exc": aiohttp.ClientConnectionError(API_KEY)},
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
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY


@pytest.mark.parametrize("status", [401, 403])
async def test_first_refresh_starts_reauth(hass, entry, api, status):
    api.get(API_DEVICE_ENDPOINT, status=status)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    flows = hass.config_entries.flow.async_progress_by_handler(entry.domain)
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == "reauth"
    assert flows[0]["context"]["entry_id"] == entry.entry_id


async def test_poll_failure_and_recovery(hass, entry, api, device, caplog, freezer):
    api.get(API_DEVICE_ENDPOINT, json=[device])
    coordinator = GPSLiveCoordinator(hass, entry)
    await coordinator.async_refresh()
    api.clear_requests()
    caplog.set_level(logging.DEBUG)
    for _ in range(2):
        api.get(API_DEVICE_ENDPOINT, exc=aiohttp.ClientConnectionError(API_KEY))
        await coordinator.async_refresh()
        assert not coordinator.last_update_success
        assert coordinator.data == [device]
    errors = [r for r in caplog.records if "Error fetching gpslive data" in r.message]
    assert len(errors) == 1
    assert API_KEY not in caplog.text
    api.clear_requests()
    api.get(API_DEVICE_ENDPOINT, json=[device])
    freezer.tick(timedelta(seconds=1))
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    await coordinator.async_shutdown()
