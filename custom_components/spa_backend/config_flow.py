from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .client import SpaBackendClient


class SpaBackendConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._client: SpaBackendClient | None = None
        self._credentials: dict[str, str] | None = None

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            self._credentials = {
                "backend_url": user_input["backend_url"],
                "username": user_input["username"],
                "password": user_input["password"],
            }
            self._client = SpaBackendClient(
                base_url=self._credentials["backend_url"],
                username=self._credentials["username"],
                password=self._credentials["password"],
            )

            try:
                self._client.login()
                devices = await self.hass.async_add_executor_job(
                    self._client.list_devices
                )
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    return await self.async_step_select_device()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("backend_url", default="http://localhost:8000"): str,
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_select_device(self, user_input=None) -> FlowResult:
        errors = {}

        if self._client is None or self._credentials is None:
            return await self.async_step_user()

        devices = await self.hass.async_add_executor_job(self._client.list_devices)
        options = {
            str(device.get("device_uid")): (
                f"{device.get('device_uid')}"
                + (f" — {device.get('serial_number')}" if device.get("serial_number") else "")
            )
            for device in devices
            if device.get("device_uid")
        }

        if user_input is not None:
            try:
                device = self._client.find_device_by_uid(user_input["device_uid"])
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Spa {device['device_uid']}",
                    data={
                        "backend_url": self._credentials["backend_url"],
                        "username": self._credentials["username"],
                        "password": self._credentials["password"],
                        "device_uid": device["device_uid"],
                        "device_id": device["id"],
                    },
                )

        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema(
                {
                    vol.Required("device_uid"): vol.In(options),
                }
            ),
            errors=errors,
        )
