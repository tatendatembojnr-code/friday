"""Institutional portfolio analytics: Profit Factor, Expectancy, and Sharpe-like ratio."""

from __future__ import annotations

import math
import sqlite3
from pathlib import Path
from typing import Dict, List


def compute_portfolio_analytics(db_path: str | Path = "data/friday_memory.db") -> Dict[str, float]:
    """Computes institutional metrics from realized closed_deals in SQLite."""
    default = {
        "total_trades": 0,
        "win_rate_pct": 0.0,
        "profit_factor": 0.0,
        "expectancy": 0.0,
        "sharpe_ratio": 0.0,
    }
    path = Path(db_path)
    if not path.exists():
        return default

    try:
        with sqlite3.connect(path) as conn:
            has_tbl = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='closed_deals'"
            ).fetchone()
            if not has_tbl:
                return default
            pnls: List[float] = [float(r[0]) for r in conn.execute("SELECT pnl FROM closed_deals ORDER BY ticket ASC").fetchall()]
    except Exception:
        return default

    if not pnls:
        return default

    wins = [p for p in pnls if p > 0]
    losses = [abs(p) for p in pnls if p < 0]
    gross_profit = sum(wins)
    gross_loss = sum(losses)

    win_rate = (len(wins) / len(pnls)) * 100.0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)
    expectancy = sum(pnls) / len(pnls)

    mean_p = expectancy
    var_p = sum((p - mean_p) ** 2 for p in pnls) / len(pnls)
    std_p = math.sqrt(var_p)
    sharpe = (mean_p / std_p) * math.sqrt(len(pnls)) if std_p > 0 else 0.0

    return {
        "total_trades": len(pnls),
        "win_rate_pct": round(win_rate, 1),
        "profit_factor": round(profit_factor, 2),
        "expectancy": round(expectancy, 2),
        "sharpe_ratio": round(sharpe, 2),
    }
