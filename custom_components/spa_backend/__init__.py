from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, MANUFACTURER
from .client import SpaBackendClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = SpaBackendClient(
        base_url=entry.data["backend_url"],
        username=entry.data["username"],
        password=entry.data["password"],
    )
    await hass.async_add_executor_job(client.login)

    device_uid = entry.data["device_uid"]
    device_id = entry.data["device_id"]

    async def _async_update() -> dict:
        try:
            return await hass.async_add_executor_job(
                client.fetch_device_state, device_id
            )
        except Exception as err:
            raise UpdateFailed(str(err)) from err

    coordinator: DataUpdateCoordinator[dict] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}-{entry.entry_id}",
        update_interval=timedelta(seconds=20),
        update_method=_async_update,
    )
    await coordinator.async_config_entry_first_refresh()

    device_info = DeviceInfo(
        identifiers={(DOMAIN, str(entry.entry_id))},
        manufacturer=MANUFACTURER,
        name=entry.title,
        model="Spa",
        serial_number=str(device_uid),
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "device_uid": device_uid,
        "device_id": device_id,
        "spa_id": entry.data.get("spa_id"),
        "device_info": device_info,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, ["climate", "switch"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["climate", "switch"])
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
