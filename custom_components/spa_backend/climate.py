from __future__ import annotations

from typing import Any

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SpaBackendClimate(entry, data)])


class SpaBackendClimate(CoordinatorEntity, ClimateEntity):
    _attr_has_entity_name = True
    _attr_name = "Climate"
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = ["heat", "off"]
    _attr_supported_hvac_modes = ["heat", "off"]
    _attr_min_temp = 10
    _attr_max_temp = 40
    _attr_target_temperature_step = 0.5

    def __init__(self, entry: ConfigEntry, data: dict[str, Any]) -> None:
        super().__init__(data["coordinator"])
        self.entry = entry
        self.client = data["client"]
        self.device_uid = data["device_uid"]
        self.device_id = data["device_id"]
        self._attr_unique_id = f"{entry.entry_id}-climate"
        self._attr_device_info = data["device_info"]

    @property
    def _state(self) -> dict:
        return self.coordinator.data or {}

    @property
    def current_temperature(self) -> float | None:
        value = self._state.get("water_temp_c")
        return float(value) if value is not None else None

    @property
    def target_temperature(self) -> float | None:
        value = self._state.get("temp_setpoint_c")
        return float(value) if value is not None else None

    @property
    def hvac_mode(self) -> str:
        return "heat"

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await self.hass.async_add_executor_job(
            self.client.set_temperature,
            self.device_id,
            temperature,
        )
        await self.coordinator.async_request_refresh()
