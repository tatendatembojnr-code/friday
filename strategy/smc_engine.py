"""Smart Money Concepts (SMC) deterministic strategy engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from config.settings import SMCConfig
from core.market_context import compute_atr


@dataclass
class TradeSetup:
    symbol: str
    direction: str  # "BUY" or "SELL"
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    smc_score: int
    atr: float
    htf_bias: str
    confluence_tags: List[str] = field(default_factory=list)
    notes: str = ""


class SMCEngine:
    """Detects swing liquidity, liquidity sweeps, BOS/CHoCH, Order Blocks, and FVGs."""

    def __init__(self, config: SMCConfig):
        self.cfg = config

    def _find_swings(self, df: pd.DataFrame) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
        lb = self.cfg.swing_lookback
        highs = df["high"].values
        lows = df["low"].values
        swing_highs: List[Tuple[int, float]] = []
        swing_lows: List[Tuple[int, float]] = []

        for i in range(lb, len(df) - lb):
            window_h = highs[i - lb : i + lb + 1]
            window_l = lows[i - lb : i + lb + 1]
            if highs[i] == np.max(window_h):
                swing_highs.append((i, float(highs[i])))
            if lows[i] == np.min(window_l):
                swing_lows.append((i, float(lows[i])))

        return swing_highs, swing_lows

    def _detect_fvg(self, df: pd.DataFrame, atr: float, direction: str) -> Optional[Tuple[float, float]]:
        min_gap = atr * self.cfg.fvg_min_atr_ratio
        # Inspect recent 15 candles for an unmitigated FVG
        start = max(2, len(df) - 15)
        for i in range(len(df) - 1, start - 1, -1):
            c1_high, c1_low = float(df["high"].iloc[i - 2]), float(df["low"].iloc[i - 2])
            c3_high, c3_low = float(df["high"].iloc[i]), float(df["low"].iloc[i])
            if direction == "BUY" and c3_low > c1_high and (c3_low - c1_high) >= min_gap:
                return (c1_high, c3_low)
            if direction == "SELL" and c3_high < c1_low and (c1_low - c3_high) >= min_gap:
                return (c3_high, c1_low)
        return None

    def _detect_order_block(self, df: pd.DataFrame, direction: str) -> Optional[Tuple[float, float]]:
        lookback = min(20, len(df) - 2)
        for i in range(len(df) - 2, len(df) - lookback, -1):
            o = float(df["open"].iloc[i])
            c = float(df["close"].iloc[i])
            next_c = float(df["close"].iloc[i + 1])
            next_o = float(df["open"].iloc[i + 1])
            if direction == "BUY" and c < o and next_c > next_o and next_c > float(df["high"].iloc[i]):
                return (float(df["low"].iloc[i]), float(df["high"].iloc[i]))
            if direction == "SELL" and c > o and next_c < next_o and next_c < float(df["low"].iloc[i]):
                return (float(df["low"].iloc[i]), float(df["high"].iloc[i]))
        return None

    def analyze(self, df: pd.DataFrame, symbol: str, htf_bias: str) -> Optional[TradeSetup]:
        if df is None or len(df) < 60:
            return None

        atr_series = compute_atr(df, 14)
        atr = float(atr_series.iloc[-1])
        if np.isnan(atr) or atr <= 0:
            return None

        swing_highs, swing_lows = self._find_swings(df)
        if not swing_highs or not swing_lows:
            return None

        recent_close = float(df["close"].iloc[-1])
        recent_lows = df["low"].iloc[-12:]
        recent_highs = df["high"].iloc[-12:]

        candidates: List[TradeSetup] = []

        # --- Check Bullish Setup (Liquidity sweep below swing low + BOS above prior swing high) ---
        prior_lows = [lvl for idx, lvl in swing_lows if idx < len(df) - 6]
        prior_highs = [lvl for idx, lvl in swing_highs if idx < len(df) - 4]
        if prior_lows and prior_highs:
            key_low = prior_lows[-1]
            key_high = prior_highs[-1]

            swept_low = float(recent_lows.min()) < key_low and recent_close > key_low
            bos_up = recent_close > key_high or float(df["close"].iloc[-3:].max()) > key_high
            fvg = self._detect_fvg(df, atr, "BUY")
            ob = self._detect_order_block(df, "BUY")

            score = 0
            tags: List[str] = []
            if swept_low:
                score += 30
                tags.append("LiquiditySweepLow")
            if bos_up:
                score += 25
                tags.append("BullishBOS")
            if fvg is not None:
                score += 15
                tags.append("BullishFVG")
            if ob is not None:
                score += 15
                tags.append("BullishOB")
            if htf_bias == "BULLISH":
                score += 15
                tags.append("HTFAligned")

            if score >= self.cfg.min_smc_score and swept_low:
                sl = min(float(recent_lows.min()), ob[0] if ob else float(recent_lows.min())) - (
                    atr * self.cfg.sl_atr_buffer
                )
                risk = recent_close - sl
                if risk > 0:
                    tp = recent_close + risk * self.cfg.default_rr_target
                    candidates.append(
                        TradeSetup(
                            symbol=symbol,
                            direction="BUY",
                            entry=recent_close,
                            stop_loss=sl,
                            take_profit=tp,
                            risk_reward=self.cfg.default_rr_target,
                            smc_score=min(score, 100),
                            atr=atr,
                            htf_bias=htf_bias,
                            confluence_tags=tags,
                            notes=f"Swept low {key_low:.5f}, BOS target {key_high:.5f}",
                        )
                    )

        # --- Check Bearish Setup (Liquidity sweep above swing high + BOS below prior swing low) ---
        if prior_lows and prior_highs:
            key_low = prior_lows[-1]
            key_high = prior_highs[-1]

            swept_high = float(recent_highs.max()) > key_high and recent_close < key_high
            bos_down = recent_close < key_low or float(df["close"].iloc[-3:].min()) < key_low
            fvg = self._detect_fvg(df, atr, "SELL")
            ob = self._detect_order_block(df, "SELL")

            score = 0
            tags = []
            if swept_high:
                score += 30
                tags.append("LiquiditySweepHigh")
            if bos_down:
                score += 25
                tags.append("BearishBOS")
            if fvg is not None:
                score += 15
                tags.append("BearishFVG")
            if ob is not None:
                score += 15
                tags.append("BearishOB")
            if htf_bias == "BEARISH":
                score += 15
                tags.append("HTFAligned")

            if score >= self.cfg.min_smc_score and swept_high:
                sl = max(float(recent_highs.max()), ob[1] if ob else float(recent_highs.max())) + (
                    atr * self.cfg.sl_atr_buffer
                )
                risk = sl - recent_close
                if risk > 0:
                    tp = recent_close - risk * self.cfg.default_rr_target
                    candidates.append(
                        TradeSetup(
                            symbol=symbol,
                            direction="SELL",
                            entry=recent_close,
                            stop_loss=sl,
                            take_profit=tp,
                            risk_reward=self.cfg.default_rr_target,
                            smc_score=min(score, 100),
                            atr=atr,
                            htf_bias=htf_bias,
                            confluence_tags=tags,
                            notes=f"Swept high {key_high:.5f}, BOS target {key_low:.5f}",
                        )
                    )

        if not candidates:
            return None
        return max(candidates, key=lambda s: s.smc_score)
