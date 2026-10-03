"""In range: the monitor answered recently (in practice: car is home)."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from . import LeagendConfigEntry
from .const import IN_RANGE_MINUTES
from .entity import LeagendEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LeagendConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add the in-range sensor."""
    async_add_entities([LeagendInRange(entry.runtime_data)])


class LeagendInRange(LeagendEntity, BinarySensorEntity):
    """On while the monitor answered within IN_RANGE_MINUTES."""

    _attr_name = "In range"
    _attr_device_class = BinarySensorDeviceClass.PRESENCE

    def __init__(self, coordinator) -> None:
        """Create the sensor."""
        super().__init__(coordinator, "in_range")

    async def async_added_to_hass(self) -> None:
        """Re-check every minute, so it turns off without a poll."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._tick, timedelta(minutes=1)
            )
        )

    @callback
    def _tick(self, _now) -> None:
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Always available."""
        return True

    @property
    def is_on(self) -> bool:
        """Whether the last reading is recent enough."""
        seen = self.coordinator.last_seen
        return seen is not None and (
            dt_util.utcnow() - seen < timedelta(minutes=IN_RANGE_MINUTES)
        )

    @property
    def extra_state_attributes(self):
        """Troubleshooting details."""
        c = self.coordinator
        return {
            "last_reading": c.last_seen.isoformat() if c.last_seen else None,
            "last_heard": c.last_heard.isoformat() if c.last_heard else None,
            "last_error": c.last_error,
        }
