"""Triple-barrier labeling for supervised & multi-output trade outcome prediction."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from strategy.smc_engine import TradeSetup


@dataclass
class TripleBarrierLabel:
    target_win: int  # 1 if TP hit before SL (with positive net return), else 0
    outcome_class: int  # 2=TP_FIRST, 1=TIME_BARRIER, 0=SL_FIRST
    net_r_outcome: float
    mfe_r: float
    mae_r: float
    bars_held: int


def generate_triple_barrier_label(
    future_df: pd.DataFrame,
    setup: TradeSetup,
    horizon_bars: int = 48,
    cost_r: float = 0.05,
) -> TripleBarrierLabel:
    """Labels a setup using strict future bars [t+1 : t+1+horizon] with transaction cost deduction."""
    sl_dist = abs(setup.entry - setup.stop_loss)
    if sl_dist <= 0 or future_df.empty:
        return TripleBarrierLabel(0, 1, 0.0, 0.0, 0.0, 0)

    bars = future_df.iloc[:horizon_bars]
    mfe_r = 0.0
    mae_r = 0.0
    outcome_class = 1
    gross_r = 0.0
    bars_held = len(bars)

    for idx, (_, row) in enumerate(bars.iterrows(), start=1):
        hi, lo, cl = float(row["high"]), float(row["low"]), float(row["close"])
        if setup.direction == "BUY":
            mfe_r = max(mfe_r, (hi - setup.entry) / sl_dist)
            mae_r = max(mae_r, (setup.entry - lo) / sl_dist)
            if lo <= setup.stop_loss:
                outcome_class = 0
                gross_r = -1.0
                bars_held = idx
                break
            if hi >= setup.take_profit:
                outcome_class = 2
                gross_r = setup.risk_reward
                bars_held = idx
                break
            gross_r = (cl - setup.entry) / sl_dist
        else:
            mfe_r = max(mfe_r, (setup.entry - lo) / sl_dist)
            mae_r = max(mae_r, (hi - setup.entry) / sl_dist)
            if hi >= setup.stop_loss:
                outcome_class = 0
                gross_r = -1.0
                bars_held = idx
                break
            if lo <= setup.take_profit:
                outcome_class = 2
                gross_r = setup.risk_reward
                bars_held = idx
                break
            gross_r = (setup.entry - cl) / sl_dist

    net_r = round(gross_r - cost_r, 4)
    target_win = 1 if (outcome_class == 2 and net_r > 0) else 0
    return TripleBarrierLabel(
        target_win=target_win,
        outcome_class=outcome_class,
        net_r_outcome=net_r,
        mfe_r=round(mfe_r, 4),
        mae_r=round(mae_r, 4),
        bars_held=bars_held,
    )
