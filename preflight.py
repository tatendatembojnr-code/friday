"""Zero-dependency preflight credential and environment validator for FRIDAY."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict


PLACEHOLDERS = {
    "12345678",
    "your_mt5_password",
    "YourBroker-Demo",
    "sk-your-openai-api-key",
    "",
}


def _parse_env(env_file: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, val = stripped.split("=", 1)
        values[key.strip()] = val.strip().strip('"').strip("'")
    return values


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

    if simulate:
        print("[FRIDAY] Preflight OK (simulation mode).")
        return 0

    env_vals = _parse_env(env_file) if env_file.exists() else {}
    login = os.getenv("MT5_LOGIN", env_vals.get("MT5_LOGIN", ""))
    password = os.getenv("MT5_PASSWORD", env_vals.get("MT5_PASSWORD", ""))
    server = os.getenv("MT5_SERVER", env_vals.get("MT5_SERVER", ""))
    openai_key = os.getenv("OPENAI_API_KEY", env_vals.get("OPENAI_API_KEY", ""))

    missing_mt5 = []
    if not login.isdigit() or login in PLACEHOLDERS:
        missing_mt5.append("MT5_LOGIN")
    if password in PLACEHOLDERS:
        missing_mt5.append("MT5_PASSWORD")
    if server in PLACEHOLDERS:
        missing_mt5.append("MT5_SERVER")

    if missing_mt5:
        print("[FRIDAY] Missing or placeholder MT5 credentials in .env:")
        for item in missing_mt5:
            print(f"  - {item}")
        print("[FRIDAY] Update .env and try again, or test with: run friday --simulate")
        return 1

    if openai_key in PLACEHOLDERS:
        print("[FRIDAY] Warning: OPENAI_API_KEY not set; FRIDAY will use local deterministic fallback.")

    print("[FRIDAY] Preflight checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
