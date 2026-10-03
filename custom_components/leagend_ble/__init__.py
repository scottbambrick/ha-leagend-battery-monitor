"""Leagend BM2 / BM6 battery monitors over Home Assistant's Bluetooth.

Each config entry is one monitor. Readings are taken through whichever
connectable Bluetooth adapter or ESPHome Bluetooth proxy hears it best.
"""
from __future__ import annotations

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_NAME, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_MODEL
from .coordinator import LeagendCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

type LeagendConfigEntry = ConfigEntry[LeagendCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: LeagendConfigEntry
) -> bool:
    """Set up one monitor."""
    coordinator = LeagendCoordinator(
        hass,
        entry.data[CONF_ADDRESS],
        entry.data[CONF_MODEL],
        entry.data[CONF_NAME],
    )
    entry.runtime_data = coordinator

    # Read straight away when the monitor is heard again after a gap
    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            coordinator.async_advertisement,
            {"address": coordinator.address},
            bluetooth.BluetoothScanningMode.PASSIVE,
        )
    )

    # Don't hold up start-up for a car that's away: the first read runs
    # in the background
    entry.async_create_background_task(
        hass, coordinator.async_refresh(), "leagend_ble_first_read"
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: LeagendConfigEntry
) -> bool:
    """Unload a monitor."""
    return await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )
