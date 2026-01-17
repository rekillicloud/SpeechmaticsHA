"""The Speechmatics STT integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Speechmatics STT from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, ["stt"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, ["stt"])


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict,
    async_add_entities,
    discovery_info=None,
) -> None:
    """Set up Speechmatics STT platform (YAML configuration)."""
    from .stt import SpeechmaticsSTTEntity

    api_key = config.get("api_key")
    language = config.get("language", "en")
    operating_point = config.get("operating_point", "enhanced")
    max_delay = config.get("max_delay", 0.8)

    if not api_key:
        _LOGGER.error("API key is required for Speechmatics STT")
        return

    entity = SpeechmaticsSTTEntity(
        api_key=api_key,
        language=language,
        operating_point=operating_point,
        max_delay=max_delay,
    )

    async_add_entities([entity])
