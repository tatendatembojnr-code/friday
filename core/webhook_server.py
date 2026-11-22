"""TradingView Webhook alert parser & validator (inspired by TradingView-Webhook-Bot)."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple


def parse_webhook_alert(payload: Dict[str, Any], expected_secret: str | None = None) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Validates incoming TradingView JSON alert: {"secret": "...", "symbol": "XAUUSD", "action": "BUY"}."""
    secret = expected_secret if expected_secret is not None else os.getenv("WEBHOOK_SECRET", "").strip()
    if secret and str(payload.get("secret", "")) != secret:
        return False, None, "Invalid webhook secret"

    symbol = str(payload.get("symbol", "")).strip().upper()
    action = str(payload.get("action", "")).strip().upper()
    if not symbol or action not in ("BUY", "SELL", "CLOSE"):
        return False, None, "Payload must include valid 'symbol' and 'action' (BUY/SELL/CLOSE)"

    return True, {"symbol": symbol, "action": action, "comment": str(payload.get("comment", "TV_WEBHOOK"))}, "OK"
