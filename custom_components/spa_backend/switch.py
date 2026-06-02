from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_SWITCHES, DOMAIN

_STATE_KEY_BY_COMMAND = {
    "jet_1": "jet_1",
    "jet_2": "jet_2",
    "toggle_blower": "blower",
    "toggle_lights": "light",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities = [
        SpaBackendSwitch(entry, data, command_type, label)
        for command_type, label in DEFAULT_SWITCHES
    ]
    async_add_entities(entities)


class SpaBackendSwitch(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        data: dict[str, Any],
        command_type: str,
        label: str,
    ) -> None:
        super().__init__(data["coordinator"])
        self.entry = entry
        self.client = data["client"]
        self.device_id = data["device_id"]
        self.command_type = command_type
        self._attr_name = label
        self._attr_unique_id = f"{entry.entry_id}-{command_type}"
        self._attr_translation_key = None
        self._attr_device_info = data["device_info"]
        self._state_key = _STATE_KEY_BY_COMMAND.get(command_type)

    @property
    def is_on(self) -> bool | None:
        if not self._state_key:
            return None
        state = self.coordinator.data or {}
        value = state.get(self._state_key)
        if value is None:
            return None
        return bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(
            self.client.send_toggle,
            self.device_id,
            self.command_type,
            True,
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(
            self.client.send_toggle,
            self.device_id,
            self.command_type,
            False,
        )
        await self.coordinator.async_request_refresh()
