"""Config flow for the Panasonic CW window A/C integration.

One config entry per physical A/C. The user supplies a friendly name and picks
which native ``infrared`` emitter (e.g. a Broadlink blaster) should transmit the
codes. If no emitter exists yet, the flow aborts with a helpful message.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import infrared
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
)

from .const import CONF_EMITTER, CONF_NAME, DOMAIN


class PanasonicWindowAcHKConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for one Panasonic HK/Macau window A/C."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Single step: name + emitter selection."""
        if not infrared.async_get_emitters(self.hass):
            return self.async_abort(reason="no_emitters")

        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_EMITTER: user_input[CONF_EMITTER],
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_EMITTER): EntitySelector(
                    EntitySelectorConfig(domain="infrared")
                ),
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
