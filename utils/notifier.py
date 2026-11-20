"""Optional Telegram trade & alert notifier (inspired by TradingView-Webhook-Bot)."""

from __future__ import annotations

import json
import logging
import os
import urllib.request


class TelegramNotifier:
    """Sends non-blocking Telegram notifications when TELEGRAM_BOT_TOKEN & TELEGRAM_CHAT_ID are set."""

    def __init__(self):
        self.logger = logging.getLogger("FRIDAY")
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        self.enabled = bool(self.token and self.chat_id)

    def send(self, message: str) -> bool:
        if not self.enabled:
            return False
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = json.dumps({"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=3.0):
                return True
        except Exception as exc:
            self.logger.debug(f"Telegram notification failed: {exc}")
            return False
