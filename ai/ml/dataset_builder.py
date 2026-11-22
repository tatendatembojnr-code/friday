"""Chronological, leak-free dataset builder with embargo splitting."""

from __future__ import annotations

from typing import List, Tuple

import pandas as pd

from config.settings import SMCConfig
from core.market_context import summarize_timeframe
from strategy.killzone_vwap import compute_vwap_and_pdh_pdl, get_killzone, score_institutional_location
from strategy.smc_engine import SMCEngine

from ai.ml.feature_engineering import FEATURE_COLUMNS, extract_decision_features
from ai.ml.label_generator import generate_triple_barrier_label


def build_historical_dataset(
    df: pd.DataFrame,
    symbol: str,
    smc_cfg: SMCConfig | None = None,
    horizon_bars: int = 36,
    cost_r: float = 0.05,
) -> pd.DataFrame:
    """Walks chronologically through df, generating causal features and triple-barrier labels."""
    cfg = smc_cfg or SMCConfig(min_smc_score=45)
    engine = SMCEngine(cfg)
    rows: List[dict] = []

    for i in range(80, len(df) - horizon_bars - 1):
        window = df.iloc[: i + 1]
        htf_bias = summarize_timeframe(window, "M15").trend
        setup = engine.analyze(window, symbol, htf_bias)
        if setup is None:
            continue

        levels = compute_vwap_and_pdh_pdl(window)
        loc_bonus, loc_tags = score_institutional_location(
            setup.direction, setup.entry, levels["vwap"], levels["pdh"], levels["pdl"], get_killzone()
        )
        setup.smc_score = min(100, setup.smc_score + loc_bonus)
        setup.confluence_tags.extend(loc_tags)

        feats = extract_decision_features(window, setup, vwap=levels["vwap"])
        future = df.iloc[i + 1 : i + 1 + horizon_bars]
        lbl = generate_triple_barrier_label(future, setup, horizon_bars=horizon_bars, cost_r=cost_r)

        row = {"bar_index": i, "timestamp": str(df.index[i]), "symbol": symbol}
        row.update(feats)
        row["target_win"] = lbl.target_win
        row["outcome_class"] = lbl.outcome_class
        row["net_r_outcome"] = lbl.net_r_outcome
        row["mfe_r"] = lbl.mfe_r
        row["mae_r"] = lbl.mae_r
        row["bars_held"] = lbl.bars_held
        rows.append(row)

    return pd.DataFrame(rows)


def chronological_split_with_embargo(
    dataset: pd.DataFrame,
    train_frac: float = 0.65,
    embargo_rows: int = 5,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Splits dataset chronologically with an embargo gap to prevent overlapping label leakage."""
    n = len(dataset)
    split_idx = int(n * train_frac)
    train_df = dataset.iloc[:split_idx].copy()
    test_start = min(n, split_idx + embargo_rows)
    test_df = dataset.iloc[test_start:].copy()
    return train_df, test_df
