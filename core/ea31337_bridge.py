"""Bridge for reading indicator consensus signals exported by EA31337 / MT5."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from config.settings import EA31337BridgeConfig


@dataclass
class EA31337Signal:
    symbol: str
    bias: str  # "BULLISH", "BEARISH", "NEUTRAL"
    consensus_score: int  # 0-100
    active_strategies: List[str] = field(default_factory=list)
    timestamp: str = ""
    is_stale: bool = False


class EA31337Bridge:
    """Reads JSON indicator consensus snapshots written by the MT5 EA31337 exporter."""

    def __init__(self, config: EA31337BridgeConfig):
        self.logger = logging.getLogger("FRIDAY")
        self.cfg = config

    def get_signal(self, symbol: str) -> Optional[EA31337Signal]:
        if not self.cfg.enabled:
            return None

        path = Path(self.cfg.signal_file)
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data: Dict = json.load(f)
        except Exception as exc:
            self.logger.warning(f"Failed to read EA31337 bridge file {path}: {exc}")
            return None

        entry = data.get(symbol)
        if not isinstance(entry, dict):
            return None

        ts_str = str(entry.get("timestamp", ""))
        is_stale = self._check_stale(ts_str)
        if is_stale:
            self.logger.debug(f"EA31337 signal for {symbol} is stale ({ts_str}); ignoring.")
            return None

        bias = str(entry.get("bias", "NEUTRAL")).upper()
        if bias not in ("BULLISH", "BEARISH", "NEUTRAL"):
            bias = "NEUTRAL"

        score = int(max(0, min(100, int(entry.get("consensus_score", 0)))))
        strategies = [str(s) for s in entry.get("active_strategies", [])]

        return EA31337Signal(
            symbol=symbol,
            bias=bias,
            consensus_score=score,
            active_strategies=strategies,
            timestamp=ts_str,
            is_stale=False,
        )

    def _check_stale(self, ts_str: str) -> bool:
        if not ts_str:
            return True
        try:
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - dt).total_seconds()
            return age > self.cfg.max_age_seconds
        except ValueError:
            return True
