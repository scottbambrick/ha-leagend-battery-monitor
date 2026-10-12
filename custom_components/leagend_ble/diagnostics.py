"""Diagnostics: settings and the latest reading (address redacted)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant

from . import LeagendConfigEntry

TO_REDACT = {CONF_ADDRESS}


def _iso(value) -> str | None:
    return value.isoformat() if value else None


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: LeagendConfigEntry
) -> dict[str, Any]:
    """Return the entry's settings, reading and connection state."""
    c = entry.runtime_data
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "reading": dict(c.data),
        "last_reading": _iso(c.last_seen),
        "last_heard": _iso(c.last_heard),
        "last_error": c.last_error,
    }
