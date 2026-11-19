"""Preflight credential and environment validator for FRIDAY."""

from __future__ import annotations

import sys
from pathlib import Path

from config.settings import FridaySettings


PLACEHOLDERS = {
    "12345678",
    "your_mt5_password",
    "YourBroker-Demo",
    "sk-your-openai-api-key",
    "",
}


def main() -> int:
    simulate = "--simulate" in sys.argv
    base_dir = Path(__file__).resolve().parent
    env_file = base_dir / ".env"
    example_file = base_dir / ".env.example"

    if not env_file.exists():
        if example_file.exists():
            env_file.write_text(example_file.read_text(encoding="utf-8"), encoding="utf-8")
        print("[FRIDAY] Created .env from .env.example.")
        if not simulate:
            print("[FRIDAY] Please fill in your MT5 and OpenAI credentials in .env, then run again.")
            print("[FRIDAY] Or run with: run friday --simulate")
            return 1

    settings = FridaySettings.load()
    creds = settings.credentials

    if simulate:
        print("[FRIDAY] Preflight OK (simulation mode).")
        return 0

    missing = []
    if not creds.mt5_login or str(creds.mt5_login) in PLACEHOLDERS:
        missing.append("MT5_LOGIN")
    if creds.mt5_password in PLACEHOLDERS:
        missing.append("MT5_PASSWORD")
    if creds.mt5_server in PLACEHOLDERS:
        missing.append("MT5_SERVER")
    if creds.openai_api_key in PLACEHOLDERS:
        missing.append("OPENAI_API_KEY (optional if using fallback, recommended for full AI)")

    if any(k in missing for k in ("MT5_LOGIN", "MT5_PASSWORD", "MT5_SERVER")):
        print("[FRIDAY] Missing or placeholder MT5 credentials in .env:")
        for item in missing:
            print(f"  - {item}")
        print("[FRIDAY] Update .env and try again, or test with: run friday --simulate")
        return 1

    if missing:
        print("[FRIDAY] Warning: OPENAI_API_KEY not set; FRIDAY will use local deterministic fallback.")

    print("[FRIDAY] Preflight checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
