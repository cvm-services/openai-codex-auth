"""OpenAI Codex OAuth device-code login.

Signs into an OpenAI/ChatGPT account **you already own** — the flow behind
``codex login --device-auth`` and ``hermes auth add openai-codex --type oauth``.
It does not create accounts and does not touch billing.

SINGLE HOLDER: Codex refresh tokens are a rotating family; two independent
holders revoke each other. Run this for exactly one holder per account.

Pure orchestration over an injected ``httpx.Client`` so the whole thing is
unit-testable offline (see tests/test_flow.py, httpx.MockTransport).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

import httpx

CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
ISSUER = "https://auth.openai.com"
USERCODE_URL = f"{ISSUER}/api/accounts/deviceauth/usercode"
POLL_URL = f"{ISSUER}/api/accounts/deviceauth/token"
TOKEN_URL = f"{ISSUER}/oauth/token"
VERIFY_URL = f"{ISSUER}/codex/device"
REDIRECT_URI = f"{ISSUER}/deviceauth/callback"

DEFAULT_POLL_INTERVAL = 5
DEFAULT_TIMEOUT_SECONDS = 15 * 60
DEFAULT_BASE_URL = "https://chatgpt.com/backend-api/codex"
JSON_HEADERS = {"Content-Type": "application/json"}
FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}


class DeviceAuthError(RuntimeError):
    """A device-auth failure with a machine-readable ``code``."""

    def __init__(self, message: str, code: str = ""):
        super().__init__(message)
        self.code = code


@dataclass
class UserCode:
    user_code: str
    device_auth_id: str
    interval: int
    expires_in: int | None = None
    verification_url: str = VERIFY_URL


@dataclass
class Credentials:
    access_token: str
    refresh_token: str = ""
    token_type: str = "Bearer"
    expires_in: int | None = None
    base_url: str = DEFAULT_BASE_URL
    source: str = "device-code"
    issued_at: float = field(default_factory=time.time)

    def as_dict(self) -> dict:
        return {
            "tokens": {"access_token": self.access_token,
                       "refresh_token": self.refresh_token,
                       "token_type": self.token_type,
                       "expires_in": self.expires_in},
            "base_url": self.base_url,
            "source": self.source,
            "issued_at": self.issued_at,
        }


def _retry_after(response) -> int | None:
    headers = getattr(response, "headers", None)
    if not headers:
        return None
    raw = headers.get("retry-after")
    if not raw:
        return None
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return None


def request_user_code(client: httpx.Client, client_id: str = CLIENT_ID,
                      *, max_attempts: int = 4,
                      sleep: Callable[[float], None] = time.sleep) -> UserCode:
    """Step 1: request a device + user code. Retries 429 with capped backoff."""
    response = None
    for attempt in range(1, max_attempts + 1):
        response = client.post(USERCODE_URL, json={"client_id": client_id},
                               headers=JSON_HEADERS)
        if response.status_code != 429:
            break
        if attempt < max_attempts:
            delay = _retry_after(response)
            if delay is None:
                delay = 2 ** attempt
            sleep(max(1, min(int(delay), 60)))

    if response is None:
        raise DeviceAuthError("no response from the user-code endpoint",
                              "usercode_no_response")
    if response.status_code == 429:
        raise DeviceAuthError(
            "OpenAI is rate-limiting login requests (HTTP 429); try again shortly.",
            "rate_limited")
    if response.status_code != 200:
        raise DeviceAuthError(
            f"user-code request returned status {response.status_code}",
            "usercode_error")

    data = response.json()
    user_code = data.get("user_code")
    device_auth_id = data.get("device_auth_id")
    if not user_code or not device_auth_id:
        raise DeviceAuthError(
            "device-code response is missing user_code/device_auth_id", "incomplete")
    try:
        interval = max(3, int(data.get("interval", DEFAULT_POLL_INTERVAL)))
    except (TypeError, ValueError):
        interval = DEFAULT_POLL_INTERVAL
    expires_in = data.get("expires_in")
    return UserCode(str(user_code), str(device_auth_id), interval,
                    int(expires_in) if expires_in is not None else None)


def poll_for_authorization(client: httpx.Client, device_auth_id: str, user_code: str,
                           interval: int = DEFAULT_POLL_INTERVAL, *,
                           timeout: float = DEFAULT_TIMEOUT_SECONDS,
                           sleep: Callable[[float], None] = time.sleep,
                           clock: Callable[[], float] = time.monotonic) -> dict:
    """Step 3: poll until the user approves. Returns the auth code + verifier."""
    current = max(3, int(interval))
    start = clock()
    while clock() - start < timeout:
        sleep(current)
        response = client.post(POLL_URL,
                               json={"device_auth_id": device_auth_id,
                                     "user_code": user_code},
                               headers=JSON_HEADERS)
        if response.status_code == 200:
            data = response.json()
            if not data.get("authorization_code") or not data.get("code_verifier"):
                raise DeviceAuthError(
                    "poll response missing authorization_code/code_verifier",
                    "incomplete_exchange")
            return data
        if response.status_code in (403, 404):
            continue                                   # not approved yet
        if response.status_code == 429:
            current = min(current + 1, 30)             # slow down
            continue
        raise DeviceAuthError(
            f"device-auth polling returned status {response.status_code}",
            "poll_error")
    raise DeviceAuthError("timed out waiting for sign-in", "timeout")


def exchange_code(client: httpx.Client, authorization_code: str, code_verifier: str,
                  client_id: str = CLIENT_ID) -> Credentials:
    """Step 4: exchange the authorization code for tokens."""
    response = client.post(TOKEN_URL, data={
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "code_verifier": code_verifier,
    }, headers=FORM_HEADERS)
    if response.status_code == 429:
        raise DeviceAuthError(
            "OpenAI is rate-limiting the token exchange (HTTP 429); try again shortly.",
            "rate_limited")
    if response.status_code != 200:
        raise DeviceAuthError(
            f"token exchange returned status {response.status_code}",
            "token_exchange_error")
    data = response.json()
    access_token = data.get("access_token")
    if not access_token:
        raise DeviceAuthError("token exchange did not return an access_token",
                              "token_exchange_no_access_token")
    return Credentials(
        access_token=str(access_token),
        refresh_token=str(data.get("refresh_token", "") or ""),
        token_type=str(data.get("token_type", "Bearer") or "Bearer"),
        expires_in=data.get("expires_in"),
    )


def device_login(client: httpx.Client | None = None, client_id: str = CLIENT_ID,
                 on_code: Callable[[UserCode], None] | None = None, *,
                 timeout: float = DEFAULT_TIMEOUT_SECONDS,
                 sleep: Callable[[float], None] = time.sleep) -> Credentials:
    """Run the full device-code login. ``on_code`` receives the :class:`UserCode`."""
    owns_client = client is None
    http = client or httpx.Client(timeout=httpx.Timeout(15.0))
    try:
        user_code = request_user_code(http, client_id, sleep=sleep)
        if on_code is not None:
            on_code(user_code)
        auth = poll_for_authorization(http, user_code.device_auth_id,
                                      user_code.user_code, user_code.interval,
                                      timeout=timeout, sleep=sleep)
        return exchange_code(http, auth["authorization_code"],
                             auth["code_verifier"], client_id)
    finally:
        if owns_client:
            http.close()
