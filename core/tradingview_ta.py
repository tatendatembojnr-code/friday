"""TradingView Technical Analysis consensus client (inspired by python-tradingview-ta)."""

from __future__ import annotations

import json
import logging
import time
import urllib.request
from dataclasses import dataclass
from typing import Dict, Optional


TV_SYMBOL_MAP = {
    "EURUSD": ("forex", "FX:EURUSD"),
    "GBPUSD": ("forex", "FX:GBPUSD"),
    "USDJPY": ("forex", "FX:USDJPY"),
    "EURJPY": ("forex", "FX:EURJPY"),
    "AUDUSD": ("forex", "FX:AUDUSD"),
    "XAUUSD": ("cfd", "OANDA:XAUUSD"),
}


@dataclass
class TVConsensus:
    symbol: str
    recommendation: str  # "STRONG_BUY", "BUY", "NEUTRAL", "SELL", "STRONG_SELL"
    score: float  # -1.0 to +1.0


class TradingViewClient:
    """Fetches TradingView 26-indicator summary consensus with caching & safe fallback."""

    def __init__(self, cache_ttl: int = 60):
        self.logger = logging.getLogger("FRIDAY")
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, tuple[float, TVConsensus]] = {}

    def get_consensus(self, symbol: str, interval_suffix: str = "|15") -> Optional[TVConsensus]:
        mapped = TV_SYMBOL_MAP.get(symbol.upper())
        if not mapped:
            return None

        cache_key = f"{symbol}_{interval_suffix}"
        cached = self._cache.get(cache_key)
        if cached and (time.monotonic() - cached[0]) < self.cache_ttl:
            return cached[1]

        screener, tv_ticker = mapped
        url = f"https://scanner.tradingview.com/{screener}/scan"
        payload = json.dumps(
            {
                "symbols": {"tickers": [tv_ticker], "query": {"types": []}},
                "columns": [f"Recommend.All{interval_suffix}"],
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "FRIDAY-Bot/1.0"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            rows = body.get("data", [])
            if not rows or not rows[0].get("d"):
                return None
            val = float(rows[0]["d"][0])
            rec = self._classify(val)
            consensus = TVConsensus(symbol=symbol, recommendation=rec, score=round(val, 3))
            self._cache[cache_key] = (time.monotonic(), consensus)
            return consensus
        except Exception as exc:
            self.logger.debug(f"TradingView TA fetch skipped for {symbol}: {exc}")
            return None

    @staticmethod
    def _classify(val: float) -> str:
        if val >= 0.5:
            return "STRONG_BUY"
        if val >= 0.1:
            return "BUY"
        if val <= -0.5:
            return "STRONG_SELL"
        if val <= -0.1:
            return "SELL"
        return "NEUTRAL"
