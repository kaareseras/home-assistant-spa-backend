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
        self._spas: list[dict] = []

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        description_placeholders = None
        backend_url = "https://api.norviq.dk"

        if user_input is not None:
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
                await self.hass.async_add_executor_job(self._client.login)
                spas = await self.hass.async_add_executor_job(
                    self._client.list_spas
                )
            except requests.RequestException as err:
                errors["base"] = get_login_error_key(err)
                description_placeholders = {"detail": get_login_error_detail(err)}
            except Exception as err:
                errors["base"] = "cannot_connect"
                description_placeholders = {"detail": f"{type(err).__name__}: {err}"}
            else:
                if not spas:
                    errors["base"] = "no_devices"
                else:
                    self._spas = spas
                    return await self.async_step_select_device()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                }
            ),
            errors=errors,
            description_placeholders=description_placeholders,
        )

    async def async_step_select_device(self, user_input=None) -> FlowResult:
        errors = {}

        if self._client is None or self._credentials is None or not self._spas:
            return await self.async_step_user()

        options = {
            str(spa["id"]): (
                spa.get("nickname") or f"Spa #{spa['id']}"
            )
            for spa in self._spas
            if spa.get("id") is not None
        }

        if user_input is not None:
            spa_id = int(user_input["spa_id"])
            try:
                device = await self.hass.async_add_executor_job(
                    self._client.find_device_for_spa, spa_id
                )
            except Exception:
                errors["base"] = "no_devices"
            else:
                spa_name = options.get(str(spa_id), f"Spa #{spa_id}")
                return self.async_create_entry(
                    title=spa_name,
                    data={
                        "backend_url": self._credentials["backend_url"],
                        "username": self._credentials["username"],
                        "password": self._credentials["password"],
                        "spa_id": spa_id,
                        "device_uid": device["device_uid"],
                        "device_id": device["id"],
                    },
                )

        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema(
                {
                    vol.Required("spa_id"): vol.In(options),
                }
            ),
            errors=errors,
        )
