# CHECKLIST — openai-codex-auth

Maintained in-repo. `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked.

## 0. Scaffolding
- [x] Repo skeleton `~/repos/openai-codex-auth`
- [x] `PLAN.md`, `CHECKLIST.md`
- [ ] `README.md`, `requirements.txt`, `requirements-dev.txt`, `pytest.ini`, `.gitignore`

## 1. Flow implementation (`codex_device_auth/flow.py`)
- [ ] `request_user_code` (429 backoff, field validation)
- [ ] `poll_for_authorization` (pending 403/404, slow-down 429, timeout)
- [ ] `exchange_code` (authorization_code + code_verifier -> tokens)
- [ ] `device_login` orchestration + `on_code` callback
- [ ] `Credentials` / `UserCode` dataclasses + honest errors (`DeviceAuthError.code`)

## 2. CLI (`codex_device_auth/cli.py`)
- [ ] `login` subcommand: prints URL + code, polls, stores tokens 0600
- [ ] `--out`, `--timeout`, `--no-store` (print JSON), `--version`

## 3. Tests (offline, httpx.MockTransport)
- [ ] happy path end to end
- [ ] 429 backoff on user-code request
- [ ] pending poll (403) then success
- [ ] timeout raises `code=timeout`
- [ ] missing user_code/device_auth_id raises `code=incomplete`
- [ ] token exchange missing access_token raises
- [ ] `pytest` green

## 4. Publish
- [ ] GitHub Actions workflow (pytest)
- [ ] Create `cvm-services/openai-codex-auth` (private) + push

## 5. Part B — connect the operator's existing account (the goal of the lane)
- [ ] Device-code sign-in enabled in ChatGPT Security Settings (operator did)
- [ ] Run `hermes auth add openai-codex --type oauth`; approve the code
- [ ] `hermes auth list | grep openai-codex` → `openai-codex (1 credentials) oauth`
- [ ] `hermes auth status openai-codex` clean
- [ ] Probe `GET /backend-api/codex/models` and `GET /backend-api/wham/usage`

## 6. Out of scope (do NOT build)
- [x] Account creation / phone verification — refused
- [x] Subscription purchase / billing automation — refused
