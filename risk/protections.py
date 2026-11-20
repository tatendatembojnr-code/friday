"""Freqtrade-inspired trading protections: StoplossGuard & CooldownPeriod."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple


class ProtectionManager:
    """Prevents revenge-trading and over-trading during choppy whipsaw regimes."""

    def __init__(self, stoploss_limit: int = 2, lookback_minutes: int = 60, cooldown_minutes: int = 30):
        self.logger = logging.getLogger("FRIDAY")
        self.stoploss_limit = stoploss_limit
        self.lookback_minutes = lookback_minutes
        self.cooldown_minutes = cooldown_minutes
        self._symbol_losses: Dict[str, list[datetime]] = {}
        self._cooldown_until: Dict[str, datetime] = {}

    def record_trade_result(self, symbol: str, profit: float, now: datetime | None = None) -> None:
        ts = now or datetime.now(timezone.utc)
        if profit < 0:
            losses = self._symbol_losses.setdefault(symbol, [])
            losses.append(ts)
            cutoff = ts - timedelta(minutes=self.lookback_minutes)
            losses[:] = [t for t in losses if t >= cutoff]
            if len(losses) >= self.stoploss_limit:
                until = ts + timedelta(minutes=self.cooldown_minutes)
                self._cooldown_until[symbol] = until
                self.logger.warning(
                    f"StoplossGuard triggered for {symbol}: {len(losses)} losses in {self.lookback_minutes}m. "
                    f"Cooling down for {self.cooldown_minutes}m."
                )

    def is_symbol_locked(self, symbol: str, now: datetime | None = None) -> Tuple[bool, str]:
        ts = now or datetime.now(timezone.utc)
        until = self._cooldown_until.get(symbol)
        if until and ts < until:
            remaining = int((until - ts).total_seconds() // 60) + 1
            return True, f"StoplossGuard cooldown active for {symbol} ({remaining}m remaining)"
        if until and ts >= until:
            self._cooldown_until.pop(symbol, None)
            self._symbol_losses.pop(symbol, None)
        return False, ""
