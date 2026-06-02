from __future__ import annotations

import json

import requests
import websocket


class SpaBackendClient:
    """Small REST + WebSocket helper for the spa backend."""

    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.access_token = ""
        self.refresh_token = ""

    def login(self) -> dict:
        last_error = None

        for path in ("/auth/login", "/users/login"):
            try:
                response = requests.post(
                    f"{self.base_url}{path}",
                    data={"username": self.username, "password": self.password},
                    timeout=30,
                )
                response.raise_for_status()
                payload = response.json()
                self.access_token = payload.get("access_token", "")
                self.refresh_token = payload.get("refresh_token", "")
                return payload
            except requests.HTTPError as err:
                last_error = err
                if response.status_code != 404:
                    raise

        if last_error is not None:
            raise last_error

        raise RuntimeError("Unable to authenticate with backend")

    def _headers(self) -> dict:
        if not self.access_token:
            self.login()
        return {"Authorization": f"Bearer {self.access_token}"}

    def list_devices(self) -> list[dict]:
        response = requests.get(
            f"{self.base_url}/devices",
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def find_device_by_uid(self, device_uid: str) -> dict:
        for device in self.list_devices():
            if str(device.get("device_uid", "")) == device_uid:
                return device
        raise ValueError(f"Device UID {device_uid!r} not found")

    def list_spas(self) -> list[dict]:
        response = requests.get(
            f"{self.base_url}/spas",
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def list_my_devices(self) -> list[dict]:
        """Return the user's adopted devices (with spa_id), via the dashboard."""
        response = requests.get(
            f"{self.base_url}/dashboard/devices",
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def find_device_for_spa(self, spa_id: int) -> dict:
        for device in self.list_my_devices():
            if device.get("spa_id") == spa_id:
                return device
        raise ValueError(f"No device found for spa {spa_id}")

    def set_temperature(self, device_id: int, temperature: float) -> dict:
        response = requests.post(
            f"{self.base_url}/devices/{device_id}/commands",
            headers=self._headers(),
            json={
                "command_type": "set_temp_setpoint",
                "payload": {"temperature": float(temperature)},
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def send_toggle(self, device_id: int, command_type: str, enabled: bool) -> dict:
        response = requests.post(
            f"{self.base_url}/devices/{device_id}/commands",
            headers=self._headers(),
            json={
                "command_type": command_type,
                "payload": {"enabled": bool(enabled)},
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def fetch_latest_telemetry(self, device_uid: str) -> dict:
        response = requests.get(
            f"{self.base_url}/telemetry/history/{device_uid}?fields=water_temp_c,temp_setpoint_c&max_rows=1",
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        samples = payload.get("samples", [])
        if samples:
            return samples[-1].get("values", {})
        return {}

    def fetch_device_state(self, device_id: int) -> dict:
        """Return the latest cached state for a device via the dashboard endpoint."""
        for device in self.list_my_devices():
            if device.get("id") == device_id:
                state = device.get("state") or {}
                return state if isinstance(state, dict) else {}
        return {}

    def ws_url(self) -> str:
        return f"{self.base_url.replace('http://', 'ws://').replace('https://', 'wss://')}/ws/telemetry?token={self.access_token}"

    def build_ws_app(self, on_message, on_open=None, on_close=None):
        """Build a WebSocketApp the caller can ``run_forever`` and ``close``."""
        if not self.access_token:
            self.login()

        def _on_message(_ws, message):
            try:
                on_message(json.loads(message))
            except Exception:
                pass

        websocket.enableTrace(False)
        return websocket.WebSocketApp(
            self.ws_url(),
            on_message=_on_message,
            on_open=(lambda _ws: on_open()) if on_open else None,
            on_close=(lambda _ws, *_: on_close()) if on_close else None,
            on_error=lambda _ws, _err: None,
        )

    def listen_updates(self, callback) -> None:
        ws = self.build_ws_app(callback)
        ws.run_forever()
