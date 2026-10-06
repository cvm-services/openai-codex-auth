"""CLI: `python -m codex_device_auth login`."""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

from . import __version__
from .flow import DEFAULT_TIMEOUT_SECONDS, UserCode, device_login

DEFAULT_OUT = "~/.config/openai-codex/tokens.json"


def _print_code(uc: UserCode) -> None:
    print("To continue, follow these steps:\n")
    print("  1. Open this URL in your browser:")
    print(f"     {uc.verification_url}\n")
    print("  2. Enter this code:")
    print(f"     {uc.user_code}\n")
    print("Waiting for sign-in... (Ctrl+C to cancel)")


def _store(path: str, payload: dict) -> str:
    p = pathlib.Path(os.path.expanduser(path))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2) + "\n")
    p.chmod(0o600)
    return str(p)


def cmd_login(args) -> int:
    try:
        creds = device_login(on_code=_print_code, timeout=args.timeout)
    except KeyboardInterrupt:
        print("\nLogin cancelled.")
        return 130
    payload = creds.as_dict()
    if args.no_store:
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    where = _store(args.out, payload)
    print(f"\nSigned in. Credentials written to {where} (mode 0600).")
    print("Reminder: Codex refresh tokens are single-holder — do not also run this "
          "for the same account elsewhere, or the two holders revoke each other.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex_device_auth",
        description="OpenAI Codex device-code login for an account you own.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")
    login = sub.add_parser("login", help="run the device-code login flow")
    login.add_argument("--out", default=DEFAULT_OUT,
                       help=f"token output path (default {DEFAULT_OUT})")
    login.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS,
                       help="seconds to wait for sign-in (default 900)")
    login.add_argument("--no-store", action="store_true",
                       help="print tokens to stdout instead of writing a file")
    login.set_defaults(func=cmd_login)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
