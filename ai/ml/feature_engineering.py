"""Decision-time feature engineering with strict no-lookahead guarantees."""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from core.market_context import compute_adx, compute_atr, compute_rsi
from strategy.smc_engine import TradeSetup


FEATURE_COLUMNS = [
    "rsi_14",
    "ema20_dist_atr",
    "ema50_dist_atr",
    "atr_pct",
    "adx_14",
    "bb_width",
    "macd_hist",
    "vwap_dist_atr",
    "rel_volume",
    "body_ratio",
    "upper_wick_ratio",
    "lower_wick_ratio",
    "ret_1",
    "ret_4",
    "ret_12",
    "smc_score",
    "has_sweep",
    "has_bos",
    "has_ob",
    "has_fvg",
    "has_pinbar",
    "htf_aligned",
    "in_killzone",
    "near_pdh_pdl",
    "spread_atr_ratio",
    "vol_ratio",
    "direction_sign",
    "sl_dist_atr",
    "tp_dist_atr",
    "risk_reward",
]


def extract_decision_features(
    df: pd.DataFrame,
    setup: TradeSetup,
    vwap: float = 0.0,
    spread_atr_ratio: float = 0.05,
    vol_ratio: float = 1.0,
) -> Dict[str, float]:
    """Extracts strictly causal (decision-time) features from df[:t+1] and setup."""
    close = df["close"]
    last_close = float(close.iloc[-1])
    last_open = float(df["open"].iloc[-1])
    last_high = float(df["high"].iloc[-1])
    last_low = float(df["low"].iloc[-1])

    atr_series = compute_atr(df, 14)
    atr = float(atr_series.iloc[-1])
    if np.isnan(atr) or atr <= 0:
        atr = max(last_high - last_low, 1e-6)

    rsi = float(compute_rsi(close, 14).iloc[-1])
    rsi = 50.0 if np.isnan(rsi) else rsi

    ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
    adx = compute_adx(df, 14)

    ma20 = close.rolling(20).mean().iloc[-1]
    std20 = close.rolling(20).std().iloc[-1]
    bb_width = float((4 * std20) / ma20) if (ma20 and not np.isnan(std20) and ma20 > 0) else 0.0

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    sig = macd.ewm(span=9, adjust=False).mean()
    macd_hist = float((macd.iloc[-1] - sig.iloc[-1]) / atr)

    vol = df["tick_volume"].astype(float)
    vol_ma = float(vol.rolling(20).mean().iloc[-1]) if len(vol) >= 20 else float(vol.mean())
    rel_vol = float(vol.iloc[-1] / max(vol_ma, 1.0))

    candle_rng = max(last_high - last_low, 1e-9)
    body_ratio = abs(last_close - last_open) / candle_rng
    upper_wick_ratio = (last_high - max(last_open, last_close)) / candle_rng
    lower_wick_ratio = (min(last_open, last_close) - last_low) / candle_rng

    def _ret(k: int) -> float:
        if len(close) <= k:
            return 0.0
        prev = float(close.iloc[-1 - k])
        return (last_close - prev) / max(prev, 1e-9)

    vwap_ref = vwap if vwap > 0 else ema20
    tags = set(setup.confluence_tags)
    sl_dist = abs(setup.entry - setup.stop_loss)
    tp_dist = abs(setup.take_profit - setup.entry)

    return {
        "rsi_14": round(rsi, 4),
        "ema20_dist_atr": round((last_close - ema20) / atr, 4),
        "ema50_dist_atr": round((last_close - ema50) / atr, 4),
        "atr_pct": round(atr / max(last_close, 1e-9), 6),
        "adx_14": round(adx, 4),
        "bb_width": round(bb_width, 6),
        "macd_hist": round(macd_hist, 4),
        "vwap_dist_atr": round((last_close - vwap_ref) / atr, 4),
        "rel_volume": round(rel_vol, 4),
        "body_ratio": round(body_ratio, 4),
        "upper_wick_ratio": round(upper_wick_ratio, 4),
        "lower_wick_ratio": round(lower_wick_ratio, 4),
        "ret_1": round(_ret(1), 6),
        "ret_4": round(_ret(4), 6),
        "ret_12": round(_ret(12), 6),
        "smc_score": float(setup.smc_score),
        "has_sweep": float(any("Sweep" in t for t in tags)),
        "has_bos": float(any("BOS" in t for t in tags)),
        "has_ob": float(any("OB" in t for t in tags)),
        "has_fvg": float(any("FVG" in t for t in tags)),
        "has_pinbar": float(any("PinBar" in t for t in tags)),
        "htf_aligned": float("HTFAligned" in tags),
        "in_killzone": float(any("Killzone" in t for t in tags)),
        "near_pdh_pdl": float(any("PDH" in t or "PDL" in t for t in tags)),
        "spread_atr_ratio": round(spread_atr_ratio, 4),
        "vol_ratio": round(vol_ratio, 4),
        "direction_sign": 1.0 if setup.direction == "BUY" else -1.0,
        "sl_dist_atr": round(sl_dist / atr, 4),
        "tp_dist_atr": round(tp_dist / atr, 4),
        "risk_reward": round(setup.risk_reward, 4),
    }
