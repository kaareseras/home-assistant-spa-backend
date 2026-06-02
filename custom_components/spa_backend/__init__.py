from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_component

from .const import DOMAIN
from .client import SpaBackendClient


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = SpaBackendClient(
        base_url=entry.data["backend_url"],
        username=entry.data["username"],
        password=entry.data["password"],
    )
    client.login()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "device_uid": entry.data["device_uid"],
        "device_id": entry.data["device_id"],
    }

    async def _handle_ws_message(message: dict) -> None:
        if message.get("type") != "telemetry":
            return
        for domain in ("climate", "switch"):
            for state in hass.states.async_all(domain):
                if state.attributes.get("friendly_name", "").startswith("Spa Backend"):
                    await entity_component.async_update_entity(hass, state.entity_id)

    async def _listen_forever() -> None:
        await hass.async_add_executor_job(client.listen_updates, _handle_ws_message)

    await hass.config_entries.async_forward_entry_setups(entry, ["climate", "switch"])
    hass.async_create_task(_listen_forever())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["climate", "switch"])
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
