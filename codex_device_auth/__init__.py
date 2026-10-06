"""Reusable OpenAI Codex OAuth device-code login (account you own)."""
from .flow import (
    CLIENT_ID,
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT_SECONDS,
    ISSUER,
    REDIRECT_URI,
    TOKEN_URL,
    USERCODE_URL,
    VERIFY_URL,
    Credentials,
    DeviceAuthError,
    UserCode,
    device_login,
    exchange_code,
    poll_for_authorization,
    request_user_code,
)

__version__ = "0.1.0"
__all__ = [
    "CLIENT_ID", "ISSUER", "USERCODE_URL", "TOKEN_URL", "VERIFY_URL", "REDIRECT_URI",
    "DEFAULT_BASE_URL", "DEFAULT_TIMEOUT_SECONDS",
    "UserCode", "Credentials", "DeviceAuthError",
    "request_user_code", "poll_for_authorization", "exchange_code", "device_login",
    "__version__",
]
