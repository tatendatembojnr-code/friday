"""Fast historical strategy backtester for FRIDAY's SMC + Exit rules."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from config.settings import FridaySettings
from core.market_context import summarize_timeframe
from core.mt5_connector import MT5Connector
from strategy.smc_engine import SMCEngine


def run_backtest(
    connector: MT5Connector,
    settings: FridaySettings,
    symbol: str = "XAUUSD",
    bars: int = 300,
) -> Dict[str, Any]:
    """Replays SMCEngine + 0.5R breakeven + 1.8R TP on historical M15 candles."""
    df = connector.get_ohlc(symbol, settings.trading.ltf_timeframe, max(120, min(bars, 1000)))
    if df is None or len(df) < 100:
        return {"error": f"Insufficient historical data for {symbol}"}

    engine = SMCEngine(settings.smc)
    balance = 10000.0
    peak = balance
    max_dd = 0.0
    wins = 0
    losses = 0
    gross_profit = 0.0
    gross_loss = 0.0
    equity_curve: List[Dict[str, Any]] = [{"bar": 0, "equity": balance}]

    i = 80
    while i < len(df) - 5:
        window = df.iloc[: i + 1]
        htf_bias = summarize_timeframe(window, "M15").trend
        setup = engine.analyze(window, symbol, htf_bias)
        if setup is None:
            i += 1
            continue

        risk_amt = balance * (settings.risk.risk_per_trade_pct / 100.0)
        sl_dist = abs(setup.entry - setup.stop_loss)
        if sl_dist <= 0:
            i += 1
            continue

        be_triggered = False
        outcome_pnl = 0.0
        exit_bar = i + 1

        for j in range(i + 1, min(i + 48, len(df))):
            bar = df.iloc[j]
            hi, lo = float(bar["high"]), float(bar["low"])
            exit_bar = j

            if setup.direction == "BUY":
                if not be_triggered and hi >= setup.entry + sl_dist * settings.risk.breakeven_at_rr:
                    be_triggered = True
                if hi >= setup.take_profit:
                    outcome_pnl = risk_amt * settings.smc.default_rr_target
                    break
                stop_lvl = setup.entry if be_triggered else setup.stop_loss
                if lo <= stop_lvl:
                    outcome_pnl = 0.0 if be_triggered else -risk_amt
                    break
            else:
                if not be_triggered and lo <= setup.entry - sl_dist * settings.risk.breakeven_at_rr:
                    be_triggered = True
                if lo <= setup.take_profit:
                    outcome_pnl = risk_amt * settings.smc.default_rr_target
                    break
                stop_lvl = setup.entry if be_triggered else setup.stop_loss
                if hi >= stop_lvl:
                    outcome_pnl = 0.0 if be_triggered else -risk_amt
                    break

        balance += outcome_pnl
        if outcome_pnl > 0:
            wins += 1
            gross_profit += outcome_pnl
        elif outcome_pnl < 0:
            losses += 1
            gross_loss += abs(outcome_pnl)

        peak = max(peak, balance)
        dd = ((peak - balance) / peak) * 100.0 if peak > 0 else 0.0
        max_dd = max(max_dd, dd)
        equity_curve.append({"bar": exit_bar, "equity": round(balance, 2)})
        i = exit_bar + 1

    total = wins + losses
    win_rate = round((wins / total) * 100.0, 1) if total > 0 else 0.0
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)
    net_return_pct = round(((balance - 10000.0) / 10000.0) * 100.0, 2)

    return {
        "symbol": symbol,
        "bars": len(df),
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate_pct": win_rate,
        "profit_factor": profit_factor,
        "net_return_pct": net_return_pct,
        "max_drawdown_pct": round(max_dd, 2),
        "final_balance": round(balance, 2),
        "equity_curve": equity_curve,
    }
