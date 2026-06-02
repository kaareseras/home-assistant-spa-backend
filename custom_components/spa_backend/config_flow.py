from __future__ import annotations

import requests
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .client import SpaBackendClient


def get_login_error_key(err: Exception) -> str:
    status = getattr(getattr(err, "response", None), "status_code", None)
    if status in (400, 401, 403, 422):
        return "invalid_auth"
    return "cannot_connect"


def get_login_error_detail(err: Exception) -> str:
    response = getattr(err, "response", None)
    if response is not None:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict):
            detail = payload.get("detail")
            if isinstance(detail, str) and detail.strip():
                return detail
        text = getattr(response, "text", "")
        if isinstance(text, str) and text.strip():
            return text
    return "Invalid email or password."


class SpaBackendConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._client: SpaBackendClient | None = None
        self._credentials: dict[str, str] | None = None

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        description_placeholders = None
        default_backend_url = "https://api.norviq.dk"

        if user_input is not None:
            backend_url = user_input.get("backend_url", default_backend_url).strip()
            if not backend_url:
                backend_url = default_backend_url

            self._credentials = {
                "backend_url": backend_url,
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
            except requests.RequestException as err:
                errors["base"] = get_login_error_key(err)
                description_placeholders = {"detail": get_login_error_detail(err)}
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
                    vol.Required("backend_url", default=default_backend_url): str,
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                }
            ),
            errors=errors,
            description_placeholders=description_placeholders,
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
