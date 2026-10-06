# CHECKLIST — openai-codex-auth

Maintained in-repo. `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked.
Repo: https://github.com/cvm-services/openai-codex-auth (private)

## 0. Scaffolding
- [x] Repo skeleton, `PLAN.md`, `CHECKLIST.md`, `README.md`
- [x] `requirements.txt`, `requirements-dev.txt`, `pytest.ini`, `.gitignore`

## 1. Flow implementation (`codex_device_auth/flow.py`)
- [x] `request_user_code` (429 backoff honoring `Retry-After`, field validation)
- [x] `poll_for_authorization` (pending 403/404, slow-down 429, timeout)
- [x] `exchange_code`; `device_login` + `on_code`; `DeviceAuthError.code`

## 2. CLI
- [x] `python -m codex_device_auth login` (+ `--out/--timeout/--no-store/--version`)

## 3. Tests
- [x] 7 offline tests (httpx.MockTransport); `pytest` green

## 4. Publish
- [x] GitHub Actions workflow; `cvm-services/openai-codex-auth` created + pushed

## 5. Part B — connect the operator's existing account (DONE 2026-10-06)
- [x] Device-code sign-in enabled in ChatGPT Security Settings
- [x] `hermes auth add openai-codex --type oauth` completed
- [x] `hermes auth list` → `openai-codex (1 credentials) #1 openai-codex-bootstrap oauth device_code`
- [x] `hermes auth status openai-codex` → `logged in`
- [x] Probe `GET /backend-api/codex/models` → **200**
- [x] Probe `GET /backend-api/wham/usage` → **200**

### Probe findings (2026-10-06)
- Live model slugs: `gpt-6-luna`, `gpt-reserve`, `gpt-5.6-terra`, `gpt-5.6-luna`,
  `gpt-5.5`, `codex-auto-review`. **No `gpt-6-astra`** — the lane serves the
  gpt-5.6/6-luna family.
- Usage: account `npub1yanw9p2…@nomail.name`, **`plan_type: "free"`**, no credits,
  primary window 30d at 0%. **There is no paid subscription on this account**, so
  the subscription lane has no paid capacity yet. Buying one is the operator's
  action (not automated here).
- Credential is stored by Hermes in the `manager` profile pool
  (`~/.hermes/profiles/manager/auth.json` → `credential_pool["openai-codex"][0]`),
  with `access_token` + `refresh_token` inline. Single holder; do not add another.

## 6. Out of scope (do NOT build)
- [x] Account creation / phone verification — refused
- [x] Subscription purchase / billing automation — refused
