"""Security regression tests for FRIDAY."""

from __future__ import annotations

import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

FORBIDDEN_PATTERNS = [
    r"ethplorer\.io",
    r"ethereum\.publicnode",
    r"\bos\.system\s*\(",
    r"\bsubprocess\.",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\b__import__\s*\(",
    r"sk-proj-[A-Za-z0-9_-]{20,}",
    r"ghp_[A-Za-z0-9]{20,}",
]


def test_no_suspicious_rce_or_hardcoded_secrets():
    assert not (BASE_DIR / "utils" / "transport.py").exists()
    for path in BASE_DIR.rglob("*.py"):
        rel = path.relative_to(BASE_DIR)
        if any(part in (".venv", ".git", "tests") for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pat in FORBIDDEN_PATTERNS:
            assert not re.search(pat, text), f"Forbidden pattern '{pat}' found in {rel}"


def test_webhook_rejects_missing_or_wrong_secret():
    from core.webhook_server import parse_webhook_alert

    ok, _, _ = parse_webhook_alert({"symbol": "EURUSD", "action": "BUY"}, expected_secret="topsecret")
    assert not ok
    ok2, _, _ = parse_webhook_alert(
        {"secret": "wrong", "symbol": "EURUSD", "action": "BUY"}, expected_secret="topsecret"
    )
    assert not ok2
