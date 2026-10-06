"""Offline tests for the device-code flow (httpx.MockTransport; no network)."""
from __future__ import annotations

import httpx
import pytest

from codex_device_auth.flow import (
    POLL_URL,
    TOKEN_URL,
    USERCODE_URL,
    VERIFY_URL,
    DeviceAuthError,
    device_login,
    exchange_code,
    poll_for_authorization,
    request_user_code,
)

USER_CODE_BODY = {"user_code": "UC-123", "device_auth_id": "did-1",
                  "interval": "3", "expires_in": 900}


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_device_login_happy_path():
    polls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url == USERCODE_URL:
            return httpx.Response(200, json=USER_CODE_BODY)
        if url == POLL_URL:
            polls["n"] += 1
            if polls["n"] == 1:
                return httpx.Response(403, json={"error": "pending"})
            return httpx.Response(200, json={"authorization_code": "ac",
                                             "code_verifier": "cv"})
        if url == TOKEN_URL:
            return httpx.Response(200, json={"access_token": "at",
                                             "refresh_token": "rt",
                                             "token_type": "Bearer"})
        return httpx.Response(404)

    seen = []
    creds = device_login(client=_client(handler), on_code=seen.append,
                         sleep=lambda _s: None)
    assert seen and seen[0].user_code == "UC-123"
    assert seen[0].verification_url == VERIFY_URL
    assert seen[0].interval == 3
    assert creds.access_token == "at"
    assert creds.refresh_token == "rt"
    assert creds.as_dict()["tokens"]["access_token"] == "at"
    assert polls["n"] == 2


def test_request_user_code_retries_429_honoring_retry_after():
    calls = {"n": 0}
    sleeps = []

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"retry-after": "7"}, json={})
        return httpx.Response(200, json=USER_CODE_BODY)

    uc = request_user_code(_client(handler), sleep=sleeps.append)
    assert uc.user_code == "UC-123"
    assert sleeps == [7]
    assert calls["n"] == 2


def test_request_user_code_gives_up_and_names_rate_limit():
    def handler(request):
        return httpx.Response(429, json={})

    with pytest.raises(DeviceAuthError) as exc:
        request_user_code(_client(handler), max_attempts=2, sleep=lambda _s: None)
    assert exc.value.code == "rate_limited"


def test_request_user_code_missing_fields():
    def handler(request):
        return httpx.Response(200, json={"user_code": "x"})   # no device_auth_id

    with pytest.raises(DeviceAuthError) as exc:
        request_user_code(_client(handler), sleep=lambda _s: None)
    assert exc.value.code == "incomplete"


def test_poll_times_out():
    def handler(request):
        return httpx.Response(403, json={"error": "pending"})

    with pytest.raises(DeviceAuthError) as exc:
        poll_for_authorization(_client(handler), "did", "uc", 3,
                               timeout=0, sleep=lambda _s: None)
    assert exc.value.code == "timeout"


def test_exchange_without_access_token_is_refused():
    def handler(request):
        return httpx.Response(200, json={"refresh_token": "rt"})

    with pytest.raises(DeviceAuthError) as exc:
        exchange_code(_client(handler), "ac", "cv")
    assert exc.value.code == "token_exchange_no_access_token"


def test_exchange_error_status_is_named():
    def handler(request):
        return httpx.Response(500, json={})

    with pytest.raises(DeviceAuthError) as exc:
        exchange_code(_client(handler), "ac", "cv")
    assert exc.value.code == "token_exchange_error"
