"""High-impact macroeconomic news guard to avoid whipsaw spikes."""

from __future__ import annotations

import logging
import time
import urllib.request
import xml.etree.ElementTree as ET
from typing import Tuple


HIGH_IMPACT_KEYWORDS = (
    "non-farm",
    "nonfarm",
    "nfp",
    "cpi",
    "inflation",
    "fomc",
    "rate decision",
    "interest rate",
    "powell",
    "federal reserve",
    "emergency rate",
)


class NewsGuard:
    """Checks cached financial RSS headlines for high-impact macro volatility triggers."""

    def __init__(self, cache_ttl: int = 300):
        self.logger = logging.getLogger("FRIDAY")
        self.cache_ttl = cache_ttl
        self._last_check = 0.0
        self._cached_alert: Tuple[bool, str] = (False, "")

    def check_macro_risk(self, headlines: list[str] | None = None) -> Tuple[bool, str]:
        """Returns (is_high_risk, matched_headline)."""
        if headlines is not None:
            return self._scan_headlines(headlines)

        if (time.monotonic() - self._last_check) < self.cache_ttl:
            return self._cached_alert

        fetched: list[str] = []
        try:
            url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=GC=F,EURUSD=X,GBPUSD=X,JPY=X&region=US&lang=en-US"
            req = urllib.request.Request(url, headers={"User-Agent": "FRIDAY-Bot/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                root = ET.fromstring(resp.read())
            for item in root.findall(".//item")[:10]:
                t = item.findtext("title", "")
                if t:
                    fetched.append(t)
        except Exception:
            pass

        self._last_check = time.monotonic()
        self._cached_alert = self._scan_headlines(fetched)
        return self._cached_alert

    @staticmethod
    def _scan_headlines(headlines: list[str]) -> Tuple[bool, str]:
        for title in headlines:
            low = title.lower()
            if any(kw in low for kw in HIGH_IMPACT_KEYWORDS):
                return True, title
        return False, ""
