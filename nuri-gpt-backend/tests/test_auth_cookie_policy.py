from fastapi import Response

from app.api.endpoints.auth import (
    COOKIE_MAX_AGE,
    _delete_auth_cookies,
    _set_auth_cookies,
)


def _get_set_cookie_headers(response: Response) -> list[str]:
    return response.headers.getlist("set-cookie")


def test_set_auth_cookies_persistent_when_remember_true() -> None:
    response = Response()

    _set_auth_cookies(response=response, refresh_token="refresh-token", remember=True)

    cookies = _get_set_cookie_headers(response)
    assert any("refresh_token=refresh-token" in cookie for cookie in cookies)
    assert any("remember_me=1" in cookie for cookie in cookies)
    assert any(f"Max-Age={COOKIE_MAX_AGE}" in cookie for cookie in cookies)


def test_set_auth_cookies_session_when_remember_false() -> None:
    response = Response()

    _set_auth_cookies(response=response, refresh_token="refresh-token", remember=False)

    cookies = _get_set_cookie_headers(response)
    assert any("refresh_token=refresh-token" in cookie for cookie in cookies)
    assert any("remember_me=0" in cookie for cookie in cookies)
    assert all(f"Max-Age={COOKIE_MAX_AGE}" not in cookie for cookie in cookies)


def test_delete_auth_cookies_removes_both_cookie_keys() -> None:
    response = Response()

    _delete_auth_cookies(response)

    cookies = _get_set_cookie_headers(response)
    assert any("refresh_token=" in cookie for cookie in cookies)
    assert any("remember_me=" in cookie for cookie in cookies)
