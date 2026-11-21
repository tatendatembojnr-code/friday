"""Self-learning adaptive weight engine that scores setups from past WIN/LOSS outcomes."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict


class SelfLearner:
    """Learns symbol + direction edge from closed trades in SQLite and adjusts setup scores."""

    def __init__(self, db_path: str | Path = "data/friday_memory.db"):
        self.db_path = Path(db_path)

    def get_learned_adjustment(self, symbol: str, direction: str) -> tuple[int, str]:
        """Returns (-15 to +15) score adjustment based on realized WIN/LOSS history."""
        if not self.db_path.exists():
            return 0, "No history yet"
        try:
            with sqlite3.connect(self.db_path) as conn:
                has_tbl = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='closed_deals'"
                ).fetchone()
                if not has_tbl:
                    return 0, "No closed deals yet"
                rows = conn.execute(
                    "SELECT outcome, pnl FROM closed_deals WHERE symbol = ? AND direction = ? "
                    "ORDER BY ticket DESC LIMIT 20",
                    (symbol, direction),
                ).fetchall()
        except Exception:
            return 0, "DB unavailable"

        if len(rows) < 3:
            return 0, f"Insufficient sample ({len(rows)} trades)"

        wins = sum(1 for o, _ in rows if o == "WIN")
        win_rate = wins / len(rows)
        if win_rate >= 0.65:
            return 10, f"Learned strong edge ({wins}/{len(rows)} wins, +10)"
        if win_rate >= 0.50:
            return 5, f"Learned positive edge ({wins}/{len(rows)} wins, +5)"
        if win_rate <= 0.30:
            return -15, f"Learned weak edge ({wins}/{len(rows)} wins, -15)"
        return -5, f"Learned below-avg edge ({wins}/{len(rows)} wins, -5)"
