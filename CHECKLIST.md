# CHECKLIST — openai-codex-auth

Maintained in-repo. `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked.
Repo: https://github.com/cvm-services/openai-codex-auth (private)

## 0. Scaffolding
- [x] Repo skeleton `~/repos/openai-codex-auth`
- [x] `PLAN.md`, `CHECKLIST.md`, `README.md`
- [x] `requirements.txt`, `requirements-dev.txt`, `pytest.ini`, `.gitignore`

## 1. Flow implementation (`codex_device_auth/flow.py`)
- [x] `request_user_code` (429 backoff honoring `Retry-After`, field validation)
- [x] `poll_for_authorization` (pending 403/404, slow-down 429, timeout)
- [x] `exchange_code` (authorization_code + code_verifier -> tokens)
- [x] `device_login` orchestration + `on_code` callback
- [x] `Credentials` / `UserCode` dataclasses + `DeviceAuthError.code`

## 2. CLI (`codex_device_auth/cli.py`)
- [x] `login` subcommand: prints URL + code, polls, stores tokens 0600
- [x] `--out`, `--timeout`, `--no-store`, `--version`

## 3. Tests (offline, httpx.MockTransport)
- [x] happy path end to end
- [x] 429 backoff on user-code request (Retry-After)
- [x] pending poll (403) then success
- [x] timeout raises `code=timeout`
- [x] missing device_auth_id raises `code=incomplete`
- [x] token exchange missing access_token raises
- [x] `pytest` green (7 tests)

## 4. Publish
- [x] GitHub Actions workflow (pytest)
- [x] Create `cvm-services/openai-codex-auth` (private) + push

## 5. Part B — connect the operator's existing account
- [x] Device-code sign-in enabled in ChatGPT Security Settings (operator)
- [~] `hermes auth add openai-codex --type oauth` running (code `HJMY-BUB4Z`,
      waiting for operator approval)
- [ ] `hermes auth list | grep openai-codex` → `openai-codex (1 credentials) oauth`
- [ ] `hermes auth status openai-codex` clean
- [ ] Probe `GET /backend-api/codex/models` and `GET /backend-api/wham/usage`

## 6. Out of scope (do NOT build)
- [x] Account creation / phone verification — refused
- [x] Subscription purchase / billing automation — refused
