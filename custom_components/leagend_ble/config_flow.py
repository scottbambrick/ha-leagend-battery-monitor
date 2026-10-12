"""Config flow: add a monitor by its Bluetooth address and model."""
from __future__ import annotations

import re

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
)

from .const import CONF_MODEL, DOMAIN, MODEL_BM2, MODEL_BM6

MAC_RE = re.compile(r"([0-9A-F]{2}:){5}[0-9A-F]{2}")


class LeagendConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for the monitor's name, Bluetooth address and model."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle the only step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            address = (
                user_input[CONF_ADDRESS].strip().upper().replace("-", ":")
            )
            name = user_input[CONF_NAME].strip()
            if not MAC_RE.fullmatch(address):
                errors[CONF_ADDRESS] = "invalid_address"
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data={
                        **user_input,
                        CONF_NAME: name,
                        CONF_ADDRESS: address,
                    },
                )
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_ADDRESS): str,
                vol.Required(CONF_MODEL, default=MODEL_BM6): SelectSelector(
                    SelectSelectorConfig(options=[MODEL_BM2, MODEL_BM6])
                ),
            }
        )
        if user_input is not None:
            schema = self.add_suggested_values_to_schema(schema, user_input)
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
