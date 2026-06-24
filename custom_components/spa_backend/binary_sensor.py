from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SpaBackendHeatingBinarySensor(entry, data)])


class SpaBackendHeatingBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Heating"
    _attr_device_class = BinarySensorDeviceClass.HEAT

    def __init__(self, entry: ConfigEntry, data: dict[str, Any]) -> None:
        super().__init__(data["coordinator"])
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}-heating"
        self._attr_device_info = data["device_info"]

    @property
    def is_on(self) -> bool | None:
        state = self.coordinator.data or {}
        value = state.get("heater")
        if value is None:
            return None
        return bool(value)
