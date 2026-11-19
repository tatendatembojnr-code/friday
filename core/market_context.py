"""Multi-timeframe market context and technical feature builder."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict

import numpy as np
import pandas as pd


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift(1)).abs()
    low_close = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def detect_trading_session(now_utc: datetime | None = None) -> str:
    now = now_utc or datetime.now(timezone.utc)
    hour = now.hour
    in_london = 7 <= hour < 16
    in_ny = 12 <= hour < 21
    if in_london and in_ny:
        return "London-NY Overlap"
    if in_london:
        return "London"
    if in_ny:
        return "New York"
    return "Asian"


@dataclass
class TimeframeSummary:
    timeframe: str
    trend: str  # "BULLISH", "BEARISH", "RANGING"
    ema_20: float
    ema_50: float
    rsi_14: float
    atr_14: float
    last_close: float


def summarize_timeframe(df: pd.DataFrame, tf_name: str) -> TimeframeSummary:
    close = df["close"]
    ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
    rsi14 = float(compute_rsi(close, 14).iloc[-1])
    atr14 = float(compute_atr(df, 14).iloc[-1])
    last_close = float(close.iloc[-1])

    if np.isnan(rsi14):
        rsi14 = 50.0
    if np.isnan(atr14):
        atr14 = float((df["high"] - df["low"]).mean())

    spread_pct = abs(ema20 - ema50) / max(last_close, 1e-9)
    if ema20 > ema50 and last_close > ema20 and spread_pct > 0.0003:
        trend = "BULLISH"
    elif ema20 < ema50 and last_close < ema20 and spread_pct > 0.0003:
        trend = "BEARISH"
    else:
        trend = "RANGING"

    return TimeframeSummary(
        timeframe=tf_name,
        trend=trend,
        ema_20=round(ema20, 6),
        ema_50=round(ema50, 6),
        rsi_14=round(rsi14, 2),
        atr_14=round(atr14, 6),
        last_close=round(last_close, 6),
    )


def build_htf_bias(summaries: Dict[str, TimeframeSummary]) -> str:
    bull = sum(1 for s in summaries.values() if s.trend == "BULLISH")
    bear = sum(1 for s in summaries.values() if s.trend == "BEARISH")
    if bull > bear:
        return "BULLISH"
    if bear > bull:
        return "BEARISH"
    return "NEUTRAL"
