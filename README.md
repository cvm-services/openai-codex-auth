# openai-codex-auth

Reusable **OpenAI Codex OAuth device-code login** — the flow behind
`codex login --device-auth` and `hermes auth add openai-codex --type oauth`.
It signs into an OpenAI/ChatGPT account **you already own**.

> Canonical operator runbook for the **Hermes router lane** (single-holder,
> migration, recovery, kill-switches):
> `hermes-orchestration/docs/RUNBOOK-openai-codex-oauth.md`.
> This repo provides the reusable device-code client; the lane runbook is the
> source of truth for how the credential is owned and recovered.

> Out of scope by design: creating OpenAI accounts (incl. phone verification)
> and purchasing subscriptions. This connects one account you control.

## Use

```bash
pip install -r requirements.txt
python -m codex_device_auth login
# prints: open https://auth.openai.com/codex/device and enter a code
# on success: writes ~/.config/openai-codex/tokens.json (mode 0600)
```

Options: `--out PATH`, `--timeout SECONDS`, `--no-store` (print JSON).

Library:

```python
from codex_device_auth import device_login
creds = device_login(on_code=lambda uc: print(uc.verification_url, uc.user_code))
print(creds.access_token)
```

## Prerequisite

In ChatGPT: **Settings → Security → Enable device code sign-in for Codex, Excel,
PowerPoint, and Word**. It is off by default; without it, approval fails.

## Single holder (important)

Codex refresh tokens are a rotating family — a second holder revokes the first.
Run this for exactly one holder per account. The intended holder for the Hermes
router lane is Hermes itself; do not also run this CLI for the same account
while Hermes holds it.

## Test

```bash
pip install -r requirements-dev.txt
pytest        # offline; httpx.MockTransport, no network
```
