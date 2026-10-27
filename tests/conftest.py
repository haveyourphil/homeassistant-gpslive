"""Small, synthetic fixtures; never use real keys or tracker data here."""

from copy import deepcopy

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gpslive.const import CONF_API_KEY, DOMAIN

IMEI = "000000000000001"
API_KEY = "test-api-key"
DEVICE = {
    "imei": IMEI,
    "name": "Test Car",
    "device": "Test Tracker",
    "vin": "TEST-VIN",
    "odometer": "12345",
    "objectData": {
        "status": "moving",
        "data": {
            "latitude": 0.0,
            "longitude": 0.0,
            "dtTracker": "2026-01-01 00:00:00",
            "params": {"speed": "100", "batp": "80", "accv": "12.65", "io239": "1"},
        },
    },
}


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    """Use this repository's integration in a real Home Assistant test instance."""


@pytest.fixture
def device():
    return deepcopy(DEVICE)


@pytest.fixture
def entry(hass):
    """Mirror an existing entry, without a unique ID or data migration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="GPSLive Tracker",
        version=1,
        unique_id=None,
        data={CONF_API_KEY: API_KEY, "existing_setting": "keep"},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def api(aioclient_mock):
    """Use Home Assistant's HTTP mock, without an additional mocking library."""
    return aioclient_mock
