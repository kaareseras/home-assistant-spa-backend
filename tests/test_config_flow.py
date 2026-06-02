import requests

from custom_components.spa_backend.config_flow import get_login_error_key


def test_login_error_key_marks_invalid_credentials_for_400():
    err = requests.HTTPError(response=type("Resp", (), {"status_code": 400})())
    assert get_login_error_key(err) == "invalid_auth"


def test_login_error_key_marks_invalid_credentials_for_401_and_403():
    for status in (401, 403, 422):
        err = requests.HTTPError(response=type("Resp", (), {"status_code": status})())
        assert get_login_error_key(err) == "invalid_auth"


def test_login_error_key_keeps_connection_errors_for_500():
    err = requests.HTTPError(response=type("Resp", (), {"status_code": 500})())
    assert get_login_error_key(err) == "cannot_connect"
