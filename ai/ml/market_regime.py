"""Causal Market Regime Detection using Gaussian Mixture + Trend/Volatility State."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from core.market_context import compute_adx, compute_atr

try:
    from sklearn.mixture import GaussianMixture
    HAS_SKLEARN = True
except ImportError:
    GaussianMixture = None
    HAS_SKLEARN = False


@dataclass
class RegimeState:
    regime: str  # STRONG_BULLISH, STRONG_BEARISH, SIDEWAYS_RANGING, HIGH_VOLATILITY, LOW_VOLATILITY, TRANSITIONAL
    uncertainty: float  # 0.0 (certain) to 1.0 (uncertain)
    recommended_risk_mult: float
    adx: float
    vol_ratio: float


def detect_market_regime(df: pd.DataFrame) -> RegimeState:
    """Detects market regime strictly from causal past bars df[:t+1]."""
    if df is None or len(df) < 60:
        return RegimeState("TRANSITIONAL", 0.8, 0.5, 20.0, 1.0)

    close = df["close"]
    ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
    adx = compute_adx(df, 14)

    atr = compute_atr(df, 14)
    atr_now = float(atr.iloc[-1])
    atr_base = float(atr.rolling(50).mean().iloc[-1])
    vol_ratio = atr_now / max(atr_base, 1e-9) if (not np.isnan(atr_now) and not np.isnan(atr_base)) else 1.0

    uncertainty = 0.35
    if HAS_SKLEARN and len(df) >= 120:
        try:
            rets = close.pct_change().fillna(0.0).values[-120:]
            vol_s = (atr / close.replace(0, np.nan)).fillna(0.0).values[-120:]
            X = np.column_stack([rets, vol_s])
            gmm = GaussianMixture(n_components=3, covariance_type="diag", random_state=42, n_init=2)
            gmm.fit(X[:-1])  # Fit strictly on prior bars, predict on latest bar
            probs = gmm.predict_proba(X[-1:])[0]
            max_p = float(np.max(probs))
            uncertainty = round(1.0 - max_p, 3)
        except Exception:
            uncertainty = 0.5

    if vol_ratio >= 1.8:
        return RegimeState("HIGH_VOLATILITY", uncertainty, 0.5, round(adx, 2), round(vol_ratio, 2))
    if vol_ratio <= 0.65 and adx < 18:
        return RegimeState("LOW_VOLATILITY", uncertainty, 0.75, round(adx, 2), round(vol_ratio, 2))
    if adx >= 25 and ema20 > ema50 and float(close.iloc[-1]) > ema20:
        return RegimeState("STRONG_BULLISH", uncertainty, 1.0, round(adx, 2), round(vol_ratio, 2))
    if adx >= 25 and ema20 < ema50 and float(close.iloc[-1]) < ema20:
        return RegimeState("STRONG_BEARISH", uncertainty, 1.0, round(adx, 2), round(vol_ratio, 2))
    if adx < 18:
        return RegimeState("SIDEWAYS_RANGING", uncertainty, 0.6, round(adx, 2), round(vol_ratio, 2))
    return RegimeState("TRANSITIONAL", uncertainty, 0.75, round(adx, 2), round(vol_ratio, 2))
