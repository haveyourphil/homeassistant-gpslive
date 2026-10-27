"""Configure GPSLive and replace expired API keys in the existing entry."""

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import CONF_API_KEY, DOMAIN
from .coordinator import async_fetch_devices

STEP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        )
    }
)


class GPSLiveConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Manage one GPSLive account without adding credential-based unique IDs."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate credentials before creating the entry."""
        return await self._async_api_key_step("user", user_input)

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start reauthentication without copying the old key into the form."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Replace a rejected key in the original entry."""
        return await self._async_api_key_step("reauth_confirm", user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow API key rotation without deleting devices or entities."""
        return await self._async_api_key_step("reconfigure", user_input)

    async def _async_api_key_step(
        self, step_id: str, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        """Share validation between setup, reauthentication and key rotation."""
        errors: dict[str, str] = {}
        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            if not api_key:
                errors["base"] = "invalid_auth"
            else:
                try:
                    await async_fetch_devices(
                        async_get_clientsession(self.hass), api_key
                    )
                except ConfigEntryAuthFailed:
                    errors["base"] = "invalid_auth"
                except UpdateFailed:
                    errors["base"] = "cannot_connect"
                else:
                    data = {CONF_API_KEY: api_key}
                    if step_id == "reauth_confirm":
                        return self.async_update_reload_and_abort(
                            self._get_reauth_entry(), data_updates=data
                        )
                    if step_id == "reconfigure":
                        return self.async_update_reload_and_abort(
                            self._get_reconfigure_entry(), data_updates=data
                        )
                    return self.async_create_entry(title="GPSLive Tracker", data=data)

        return self.async_show_form(
            step_id=step_id, data_schema=STEP_SCHEMA, errors=errors
        )
