"""Base entity: shared device info for a monitor's entities."""
from __future__ import annotations

from homeassistant.helpers.device_registry import (
    CONNECTION_BLUETOOTH,
    DeviceInfo,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import LeagendCoordinator


class LeagendEntity(CoordinatorEntity[LeagendCoordinator]):
    """An entity belonging to one monitor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: LeagendCoordinator, key: str) -> None:
        """Link the entity to the monitor's device."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_{key}"
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, coordinator.address)},
            name=coordinator.name,
            manufacturer="Leagend",
            model=coordinator.model.upper(),
        )
