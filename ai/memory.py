"""SQLite adaptive trade memory and journal for FRIDAY."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


class FridayMemory:
    """Stores AI decisions, setups, and trade outcomes to provide adaptive context."""

    def __init__(self, db_path: str | Path = "data/friday_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    session TEXT NOT NULL,
                    htf_bias TEXT NOT NULL,
                    smc_score INTEGER NOT NULL,
                    ai_decision TEXT NOT NULL,
                    ai_confidence INTEGER NOT NULL,
                    ai_regime TEXT NOT NULL,
                    ai_reasoning TEXT NOT NULL,
                    entry REAL NOT NULL,
                    sl REAL NOT NULL,
                    tp REAL NOT NULL,
                    lot_size REAL DEFAULT 0.0,
                    executed INTEGER DEFAULT 0,
                    outcome TEXT DEFAULT 'OPEN',
                    pnl REAL DEFAULT 0.0
                )
                """
            )
            conn.commit()

    def record_decision(
        self,
        symbol: str,
        direction: str,
        session: str,
        htf_bias: str,
        smc_score: int,
        ai_decision: str,
        ai_confidence: int,
        ai_regime: str,
        ai_reasoning: str,
        entry: float,
        sl: float,
        tp: float,
        lot_size: float = 0.0,
        executed: bool = False,
    ) -> int:
        ts = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO trade_journal (
                    timestamp, symbol, direction, session, htf_bias, smc_score,
                    ai_decision, ai_confidence, ai_regime, ai_reasoning,
                    entry, sl, tp, lot_size, executed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ts, symbol, direction, session, htf_bias, smc_score,
                    ai_decision, ai_confidence, ai_regime, ai_reasoning,
                    entry, sl, tp, lot_size, 1 if executed else 0,
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def get_recent_context(self, symbol: str, limit: int = 5) -> List[Dict]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT timestamp, symbol, direction, session, htf_bias, smc_score,
                       ai_decision, ai_confidence, ai_regime, outcome, pnl
                FROM trade_journal
                WHERE symbol = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (symbol, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_performance_summary(self) -> Dict[str, float]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
                    COALESCE(SUM(pnl), 0.0) as net_pnl
                FROM trade_journal
                WHERE executed = 1 AND outcome IN ('WIN', 'LOSS')
                """
            ).fetchone()
        total, wins, losses, net_pnl = row
        closed = (wins or 0) + (losses or 0)
        win_rate = (wins / closed * 100.0) if closed > 0 else 0.0
        return {
            "closed_trades": closed,
            "wins": wins or 0,
            "losses": losses or 0,
            "win_rate_pct": round(win_rate, 2),
            "net_pnl": round(float(net_pnl or 0.0), 2),
        }
