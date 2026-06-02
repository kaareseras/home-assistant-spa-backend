from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_NAME, DEFAULT_SWITCHES, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities = [
        SpaBackendSwitch(hass, entry, data, command_type, label)
        for command_type, label in DEFAULT_SWITCHES
    ]
    async_add_entities(entities, update_before_add=True)


class SpaBackendSwitch(SwitchEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        data: dict[str, Any],
        command_type: str,
        label: str,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.client = data["client"]
        self.device_id = data["device_id"]
        self.command_type = command_type
        self._attr_name = label
        self._attr_unique_id = f"{entry.entry_id}-{command_type}"
        self._attr_translation_key = None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(
            self.client.send_toggle,
            self.device_id,
            self.command_type,
            True,
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(
            self.client.send_toggle,
            self.device_id,
            self.command_type,
            False,
        )

    def update(self) -> None:
        self._attr_is_on = False
