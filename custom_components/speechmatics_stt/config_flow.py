"""Config flow for Speechmatics STT integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_LANGUAGE,
    CONF_OPERATING_POINT,
    CONF_MAX_DELAY,
    SUPPORTED_LANGUAGES,
    OPERATING_POINTS,
    DEFAULT_LANGUAGE,
    DEFAULT_OPERATING_POINT,
    DEFAULT_MAX_DELAY,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(
            SUPPORTED_LANGUAGES
        ),
        vol.Optional(
            CONF_OPERATING_POINT, default=DEFAULT_OPERATING_POINT
        ): vol.In(OPERATING_POINTS),
        vol.Optional(CONF_MAX_DELAY, default=DEFAULT_MAX_DELAY): vol.All(
            vol.Coerce(float), vol.Range(min=0.1, max=5.0)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input."""
    api_key = data[CONF_API_KEY]

    if not api_key or len(api_key.strip()) < 10:
        raise InvalidApiKey

    language = data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")

    return {"title": f"Speechmatics STT ({language})"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Speechmatics STT."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except InvalidApiKey:
            errors["base"] = "invalid_api_key"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            await self.async_set_unique_id(
                f"{DOMAIN}_{user_input[CONF_LANGUAGE]}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class InvalidApiKey(HomeAssistantError):
    """Error to indicate there is an invalid API key."""
