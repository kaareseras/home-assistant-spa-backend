from unittest.mock import Mock, patch

import requests

from custom_components.spa_backend.client import SpaBackendClient


def test_login_prefers_auth_login_endpoint():
    client = SpaBackendClient("https://example.test", "user", "pass")
    fake_response = Mock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = {"access_token": "token", "refresh_token": "refresh"}

    with patch("custom_components.spa_backend.client.requests.post", return_value=fake_response) as post:
        result = client.login()

    assert result["access_token"] == "token"
    assert client.access_token == "token"
    post.assert_called_once_with(
        "https://example.test/auth/login",
        data={"username": "user", "password": "pass"},
        timeout=30,
    )


def test_login_falls_back_to_users_login_on_404():
    client = SpaBackendClient("https://example.test", "user", "pass")

    first = Mock()
    first.raise_for_status.side_effect = requests.HTTPError(response=Mock(status_code=404))
    first.status_code = 404

    second = Mock()
    second.raise_for_status.return_value = None
    second.json.return_value = {"access_token": "token", "refresh_token": "refresh"}

    with patch(
        "custom_components.spa_backend.client.requests.post",
        side_effect=[first, second],
    ) as post:
        result = client.login()

    assert result["access_token"] == "token"
    assert post.call_count == 2
    assert post.call_args_list[0].args[0] == "https://example.test/auth/login"
    assert post.call_args_list[1].args[0] == "https://example.test/users/login"
