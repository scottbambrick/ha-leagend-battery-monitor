"""Battery voltage (both models); temperature, charge and status (BM6)."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LeagendConfigEntry
from .const import MODEL_BM6
from .entity import LeagendEntity

VOLTAGE = SensorEntityDescription(
    key="voltage",
    name="Battery voltage",
    device_class=SensorDeviceClass.VOLTAGE,
    state_class=SensorStateClass.MEASUREMENT,
    native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    suggested_display_precision=2,
    icon="mdi:car-battery",
)
BM6_ONLY = (
    SensorEntityDescription(
        key="state_of_charge",
        name="Battery state of charge",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    SensorEntityDescription(
        key="temperature",
        name="Battery temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    SensorEntityDescription(
        key="status",
        name="Battery status",
        device_class=SensorDeviceClass.ENUM,
        options=["Normal", "Charging", "Low charge"],
        icon="mdi:car-battery",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LeagendConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add the sensors the monitor's model provides."""
    coordinator = entry.runtime_data
    descriptions = [VOLTAGE]
    if coordinator.model == MODEL_BM6:
        descriptions += BM6_ONLY
    async_add_entities(LeagendSensor(coordinator, d) for d in descriptions)


class LeagendSensor(LeagendEntity, SensorEntity):
    """Keeps the last reading while the car is away.

    Unknown until the first reading after Home Assistant starts.
    """

    def __init__(
        self, coordinator, description: SensorEntityDescription
    ) -> None:
        """Create the sensor described by `description`."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        """The latest reading for this sensor."""
        return (self.coordinator.data or {}).get(self.entity_description.key)

    @property
    def available(self) -> bool:
        """Always available: a missed poll keeps the last value."""
        return True

    @property
    def extra_state_attributes(self):
        """When the value was read."""
        seen = self.coordinator.last_seen
        return {"last_reading": seen.isoformat() if seen else None}
