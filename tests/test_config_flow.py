"""Regression tests for setup, single entry and credential replacement."""

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType

from custom_components.gpslive.const import API_DEVICE_ENDPOINT, CONF_API_KEY, DOMAIN


async def test_user_flow(hass, api, device):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["data_schema"]({CONF_API_KEY: "test"}) == {CONF_API_KEY: "test"}
    api.get(API_DEVICE_ENDPOINT, json=[device])
    with patch("custom_components.gpslive.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: " new-test-key "}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_API_KEY: "new-test-key"}
    assert result["result"].unique_id is None


async def test_single_entry(hass, entry):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


@pytest.mark.parametrize(
    "status,error",
    [(401, "invalid_auth"), (403, "invalid_auth"), (500, "cannot_connect")],
)
async def test_flow_errors(hass, api, status, error):
    api.get(API_DEVICE_ENDPOINT, status=status)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_API_KEY: "bad-test-key"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}
    assert not hass.config_entries.async_entries(DOMAIN)


async def test_empty_key(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_API_KEY: "   "}
    )
    assert result["errors"] == {"base": "invalid_auth"}


@pytest.mark.parametrize(
    "source,step,reason",
    [
        (SOURCE_REAUTH, "reauth_confirm", "reauth_successful"),
        (SOURCE_RECONFIGURE, "reconfigure", "reconfigure_successful"),
    ],
)
async def test_replace_key_preserves_entry(hass, entry, api, source, step, reason):
    api.get(API_DEVICE_ENDPOINT, json=[])
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": source, "entry_id": entry.entry_id},
        data=entry.data if source == SOURCE_REAUTH else None,
    )
    assert result["step_id"] == step
    with patch.object(
        hass.config_entries, "async_reload", new_callable=AsyncMock
    ) as reload:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: "rotated-test-key"}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == reason
    assert hass.config_entries.async_entries(DOMAIN) == [entry]
    assert entry.version == 1
    assert entry.unique_id is None
    assert entry.data == {CONF_API_KEY: "rotated-test-key", "existing_setting": "keep"}
    reload.assert_awaited_once_with(entry.entry_id)
