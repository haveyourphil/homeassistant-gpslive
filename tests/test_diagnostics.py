"""Diagnostics never include the stored key or personal tracker data."""

import json

from custom_components.gpslive.const import API_DEVICE_ENDPOINT
from custom_components.gpslive.diagnostics import async_get_config_entry_diagnostics

from .conftest import API_KEY, IMEI


async def test_diagnostics(hass, entry, api, device):
    api.get(API_DEVICE_ENDPOINT, json=[device])
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result == {
        "config_entry_version": 1,
        "last_update_success": True,
        "device_count": 1,
        "polling_interval_seconds": 60,
    }
    serialized = json.dumps(result)
    for private_value in (API_KEY, IMEI, device["vin"], device["name"]):
        assert private_value not in serialized
