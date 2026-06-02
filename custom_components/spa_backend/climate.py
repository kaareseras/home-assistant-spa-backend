from __future__ import annotations

from typing import Any

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const import DEFAULT_NAME, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SpaBackendClimate(hass, entry, data)], update_before_add=True)


class SpaBackendClimate(ClimateEntity):
    _attr_has_entity_name = True
    _attr_name = "Climate"
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = ["heat", "off"]
    _attr_supported_hvac_modes = ["heat", "off"]

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, data: dict[str, Any]) -> None:
        self.hass = hass
        self.entry = entry
        self.client = data["client"]
        self.device_uid = data["device_uid"]
        self.device_id = data["device_id"]
        self._attr_unique_id = f"{entry.entry_id}-climate"
        self._attr_name = f"{DEFAULT_NAME} {self.device_uid}"

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await self.hass.async_add_executor_job(
            self.client.set_temperature,
            self.device_id,
            temperature,
        )
        await self.async_update_ha_state()

    def update(self) -> None:
        telemetry = self.client.fetch_latest_telemetry(self.device_uid)
        current = float(telemetry.get("water_temp_c", 0.0) or 0.0)
        target = float(telemetry.get("temp_setpoint_c", current) or current)
        self._attr_current_temperature = current
        self._attr_target_temperature = target
        self._attr_hvac_mode = "heat"
