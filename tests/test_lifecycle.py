"""Check the existing registry survives setup, unload, reload and missing data."""

from copy import deepcopy
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.gpslive import async_unload_entry
from custom_components.gpslive.const import API_DEVICE_ENDPOINT, CONF_API_KEY, DOMAIN

from .conftest import API_KEY, IMEI

SUFFIXES = ("odometer", "speed", "tracker_battery", "car_battery", "status", "ignition")


async def test_manual_install_registry_survives(hass, entry, api, device):
    """Seed the exact legacy IDs, including a user-renamed entity."""
    devices = dr.async_get(hass)
    old_device = devices.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(DOMAIN, IMEI)}, name="Test Car"
    )
    registry = er.async_get(hass)
    old_entities = [
        registry.async_get_or_create(
            platform=DOMAIN,
            domain=platform,
            unique_id=unique_id,
            config_entry=entry,
            device_id=old_device.id,
            suggested_object_id=object_id,
        )
        for platform, unique_id, object_id in [
            ("device_tracker", IMEI, "my_car"),
            *(
                ("sensor", f"{IMEI}_{suffix}", f"my_car_{suffix}")
                for suffix in SUFFIXES
            ),
        ]
    ]
    registry.async_update_entity(
        old_entities[1].entity_id, name="My mileage", icon="mdi:counter"
    )
    api.get(API_DEVICE_ENDPOINT, payload=[device], repeat=True)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert len(er.async_entries_for_config_entry(registry, entry.entry_id)) == 7
    assert len(dr.async_entries_for_config_entry(devices, entry.entry_id)) == 1
    for entity in old_entities:
        assert registry.async_get(entity.entity_id).id == entity.id
        assert registry.async_get(entity.entity_id).device_id == old_device.id
        assert hass.states.get(entity.entity_id).state != STATE_UNAVAILABLE
    assert registry.async_get(old_entities[1].entity_id).name == "My mileage"
    assert registry.async_get(old_entities[1].entity_id).icon == "mdi:counter"
    assert hass.states.get("sensor.my_car_odometer").state == "12345"
    assert hass.states.get("sensor.my_car_speed").state == "62"
    assert hass.states.get("sensor.my_car_ignition").state == "on"
    assert entry.data[CONF_API_KEY] == API_KEY
    assert entry.unique_id is None

    coordinator = entry.runtime_data
    assert coordinator._listeners
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert not coordinator._listeners
    assert coordinator._unsub_refresh is None
    assert coordinator._shutdown_requested
    assert not async_get_clientsession(hass).closed

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data is not coordinator
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert len(er.async_entries_for_config_entry(registry, entry.entry_id)) == 7
    assert devices.async_get_device(identifiers={(DOMAIN, IMEI)}).id == old_device.id
    for entity in old_entities:
        assert registry.async_get(entity.entity_id).id == entity.id
        assert hass.states.get(entity.entity_id).state != STATE_UNAVAILABLE


async def test_unload_failure_is_reported(hass, entry):
    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        new_callable=AsyncMock,
        return_value=False,
    ) as unload:
        assert not await async_unload_entry(hass, entry)
    unload.assert_awaited_once()


@pytest.mark.parametrize(
    "telemetry",
    [
        None,
        {},
        {"data": None},
        {"data": {"params": None}},
        {"data": {"params": {"batp": "bad", "speed": "nan", "accv": "inf"}}},
    ],
)
async def test_partial_telemetry(hass, entry, api, device, telemetry):
    device["objectData"] = telemetry
    api.get(API_DEVICE_ENDPOINT, payload=[device])
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("sensor.test_car_speed").state == "unknown"
    assert hass.states.get("sensor.test_car_ignition").state == "unknown"


async def test_device_disappears_and_returns(hass, entry, api, device):
    api.get(API_DEVICE_ENDPOINT, payload=[device])
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = entry.runtime_data
    registry = er.async_get(hass)
    entity_ids = [
        e.entity_id for e in er.async_entries_for_config_entry(registry, entry.entry_id)
    ]
    coordinator.async_set_updated_data([])
    await hass.async_block_till_done()
    assert all(hass.states.get(e).state == STATE_UNAVAILABLE for e in entity_ids)
    coordinator.async_set_updated_data([deepcopy(device)])
    await hass.async_block_till_done()
    assert all(hass.states.get(e).state != STATE_UNAVAILABLE for e in entity_ids)
