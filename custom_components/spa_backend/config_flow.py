from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .client import SpaBackendClient


class SpaBackendConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            client = SpaBackendClient(
                base_url=user_input["backend_url"],
                username=user_input["username"],
                password=user_input["password"],
            )
            try:
                client.login()
                device = client.find_device_by_uid(user_input["device_uid"])
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Spa {device['device_uid']}",
                    data={
                        "backend_url": user_input["backend_url"],
                        "username": user_input["username"],
                        "password": user_input["password"],
                        "device_uid": device["device_uid"],
                        "device_id": device["id"],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("backend_url", default="http://localhost:8000"): str,
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                    vol.Required("device_uid"): str,
                }
            ),
            errors=errors,
        )
