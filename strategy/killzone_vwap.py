"""Institutional Killzones, Previous Day High/Low (PDH/PDL), and VWAP Premium/Discount filter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

import numpy as np
import pandas as pd


def get_killzone(now_utc: datetime | None = None) -> str:
    utc = now_utc or datetime.now(timezone.utc)
    h = utc.hour
    if 7 <= h < 10:
        return "LondonKillzone"
    if 12 <= h < 15:
        return "NYKillzone"
    if 15 <= h < 17:
        return "LondonClose"
    return "Standard"


def compute_vwap_and_pdh_pdl(df_ltf: pd.DataFrame, df_d1: pd.DataFrame | None = None) -> Dict[str, float]:
    """Computes rolling session VWAP and Previous Day High/Low for Premium/Discount filtering."""
    typical = (df_ltf["high"] + df_ltf["low"] + df_ltf["close"]) / 3.0
    vol = df_ltf["tick_volume"].replace(0, 1)
    window = min(96, len(df_ltf))  # ~24h of M15 bars
    vwap = float((typical.tail(window) * vol.tail(window)).sum() / vol.tail(window).sum())

    pdh = float(df_ltf["high"].tail(window).max())
    pdl = float(df_ltf["low"].tail(window).min())
    if df_d1 is not None and len(df_d1) >= 2:
        pdh = float(df_d1["high"].iloc[-2])
        pdl = float(df_d1["low"].iloc[-2])

    return {
        "vwap": round(vwap, 6),
        "pdh": round(pdh, 6),
        "pdl": round(pdl, 6),
    }


def score_institutional_location(
    direction: str,
    price: float,
    vwap: float,
    pdh: float,
    pdl: float,
    killzone: str,
) -> tuple[int, list[str]]:
    """Awards bonus points for Discount buys / Premium sells and Killzone timing."""
    bonus = 0
    tags: list[str] = []

    if direction == "BUY" and price <= vwap:
        bonus += 8
        tags.append("DiscountVWAP")
    elif direction == "SELL" and price >= vwap:
        bonus += 8
        tags.append("PremiumVWAP")

    rng = max(pdh - pdl, 1e-9)
    if direction == "BUY" and (price - pdl) / rng <= 0.30:
        bonus += 7
        tags.append("NearPDL")
    elif direction == "SELL" and (pdh - price) / rng <= 0.30:
        bonus += 7
        tags.append("NearPDH")

    if killzone in ("LondonKillzone", "NYKillzone"):
        bonus += 5
        tags.append(killzone)

    return bonus, tags
