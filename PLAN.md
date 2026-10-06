# PLAN — openai-codex-auth

Status: **implementation in progress**. Owner: c03rad0r. Started: 2026-10-06.
Repo: `cvm-services/openai-codex-auth` (private).

## 1. Goal

A small, dependency-light, reusable Python implementation of the **OpenAI Codex
OAuth device-code login** — the flow behind `codex login --device-auth` /
`hermes auth add openai-codex --type oauth`. It signs into an OpenAI/ChatGPT
account **that you already own** and returns the tokens.

## 2. Explicit scope

**In scope**
- Request a device code, display the verification URL + user code, poll for
  approval, exchange the authorization code for tokens.
- A CLI (`python -m codex_device_auth login`) and a library API.
- Optional token persistence to a 0600 JSON file.
- Offline tests against `httpx.MockTransport` (no network in CI).

**Out of scope (refused, by design)**
- Creating OpenAI accounts (incl. phone/disposable-number verification).
- Purchasing subscriptions or any automated billing.
- Bulk/farmed accounts. This tool connects one account you control.

## 3. The flow (mirrors `hermes_cli.auth._codex_device_code_login`, 2026-10)

Client id `app_EMoamEEZ73f0CkXaXp7hrann`, issuer `https://auth.openai.com`.

1. `POST /api/accounts/deviceauth/usercode` `{client_id}` → `user_code`,
   `device_auth_id`, `interval` (429 → capped backoff honoring `Retry-After`).
2. Show `https://auth.openai.com/codex/device` + `user_code`.
3. Poll `POST /api/accounts/deviceauth/token` `{device_auth_id, user_code}` every
   `interval` (min 3 s); 200 → `authorization_code` + `code_verifier`; 403/404 =
   pending; 429 = slow down. 15-min timeout.
4. `POST /oauth/token` (form) `grant_type=authorization_code`, `code`,
   `code_verifier`, `redirect_uri=https://auth.openai.com/deviceauth/callback`,
   `client_id` → `access_token` (+ `refresh_token`).

Prerequisite the operator must set in ChatGPT: **Settings → Security → Enable
device code sign-in for Codex, Excel, PowerPoint, and Word** (off by default).

## 4. Single-holder warning (important)

Codex refresh tokens are a **rotating family**: whenever a holder refreshes, the
older family is revoked. Two independent holders (e.g. this CLI *and* the Hermes
router lane) revoke each other. Use exactly **one** holder per account. Hermes is
the intended holder for the router lane; run this CLI only when you want to be
that holder, and never both at once.

## 5. Identity / storage

- `Credentials` dataclass + `as_dict()`.
- CLI default output `~/.config/openai-codex/tokens.json` (0600). The Hermes
  lane stores its own copy in `~/.hermes/auth.json`; this repo does not write
  there (avoid cross-holder confusion).

## 6. Layout

```
codex_device_auth/
  flow.py     request_user_code / poll_for_authorization / exchange_code / device_login
  cli.py      `login` subcommand
  __main__.py
tests/test_flow.py
PLAN.md CHECKLIST.md README.md requirements*.txt pytest.ini
.github/workflows/tests.yml
```

## 7. Verification

- `pytest` green offline (MockTransport): happy path, 429 backoff, pending poll,
  timeout, missing fields, no access_token.
- Live proof: run the CLI / `hermes auth add openai-codex --type oauth` and see
  `hermes auth list` show `openai-codex (1 credentials) oauth`, then a 200 on
  `GET https://chatgpt.com/backend-api/wham/usage`.
