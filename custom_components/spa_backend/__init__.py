from __future__ import annotations

import logging
import threading
import time
from datetime import timedelta

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
        update_interval=timedelta(seconds=60),
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

    ws_state: dict = {"app": None, "thread": None, "stop": False}
    loop = hass.loop

    def _apply_telemetry(message: dict) -> None:
        if message.get("device_uid") != device_uid:
            return
        state = message.get("state") or {}
        if not isinstance(state, dict):
            return
        merged = dict(coordinator.data or {})
        merged.update(state)
        coordinator.async_set_updated_data(merged)

    def _on_ws_message(message: dict) -> None:
        msg_type = message.get("type")
        if msg_type == "telemetry":
            loop.call_soon_threadsafe(_apply_telemetry, message)
        elif msg_type in ("command_update", "device_status"):
            loop.call_soon_threadsafe(
                lambda: hass.async_create_task(coordinator.async_request_refresh())
            )

    def _ws_runner() -> None:
        backoff = 1.0
        while not ws_state["stop"]:
            try:
                app = client.build_ws_app(_on_ws_message)
                ws_state["app"] = app
                app.run_forever(ping_interval=30, ping_timeout=10)
            except Exception:
                _LOGGER.debug("Spa Backend WS error", exc_info=True)
            if ws_state["stop"]:
                return
            time.sleep(backoff)
            backoff = min(backoff * 2, 60.0)
            try:
                client.login()
            except Exception:
                _LOGGER.debug("Spa Backend WS re-login failed", exc_info=True)

    thread = threading.Thread(
        target=_ws_runner, name=f"{DOMAIN}-ws-{entry.entry_id}", daemon=True
    )
    ws_state["thread"] = thread
    thread.start()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "device_uid": device_uid,
        "device_id": device_id,
        "spa_id": entry.data.get("spa_id"),
        "device_info": device_info,
        "coordinator": coordinator,
        "ws_state": ws_state,
    }

    await hass.config_entries.async_forward_entry_setups(entry, ["climate", "switch"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["climate", "switch"])
    data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if data:
        ws_state = data.get("ws_state") or {}
        ws_state["stop"] = True
        app = ws_state.get("app")
        if app is not None:
            try:
                app.close()
            except Exception:
                pass
    return unload_ok
