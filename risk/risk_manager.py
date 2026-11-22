"""Hard risk guardrails and accurate MT5 position sizing for FRIDAY."""

from __future__ import annotations

import logging
import math
from typing import Dict, List, Optional, Tuple

from config.settings import RiskConfig
from core.mt5_connector import AccountSnapshot, SymbolSpecs
from strategy.smc_engine import TradeSetup


def usd_direction_sign(symbol: str, side: str) -> int:
    """Returns +1 if trade is Long USD, -1 if Short USD, 0 if non-USD cross."""
    sym = symbol.upper()
    s = side.upper()
    if sym.startswith("USD"):
        return 1 if s == "BUY" else -1
    if sym.endswith("USD") or "XAUUSD" in sym:
        return -1 if s == "BUY" else 1
    return 0


class RiskManager:
    """Enforces non-negotiable risk limits and computes exact lot sizes."""

    def __init__(self, config: RiskConfig, db=None):
        self.logger = logging.getLogger("FRIDAY")
        self.cfg = config
        self.db = db
        saved_peak = db.get_state("peak_equity", "0.0") if db else "0.0"
        try:
            self.peak_equity = float(saved_peak)
        except ValueError:
            self.peak_equity = 0.0

    def validate_and_size(
        self,
        setup: TradeSetup,
        specs: SymbolSpecs,
        account: AccountSnapshot,
        open_positions_count: int,
        today_pnl: float,
        today_trades: int,
        session: str,
        symbol_open_count: int = 0,
        open_positions: Optional[List[Dict]] = None,
        vol_ratio: float = 1.0,
        recent_loss_streak: int = 0,
    ) -> Tuple[bool, float, str]:
        if account.balance <= 0:
            return False, 0.0, "Account balance is zero or unavailable."

        if account.equity > self.peak_equity:
            self.peak_equity = account.equity
            if self.db:
                self.db.set_state("peak_equity", f"{self.peak_equity:.2f}")

        if self.peak_equity > 0:
            drawdown_pct = ((self.peak_equity - account.equity) / self.peak_equity) * 100.0
            if drawdown_pct >= self.cfg.max_drawdown_pct:
                return False, 0.0, f"Max drawdown circuit breaker hit ({drawdown_pct:.2f}%)."

        if self.cfg.allowed_sessions and session not in self.cfg.allowed_sessions:
            return False, 0.0, f"Session '{session}' outside allowed sessions {self.cfg.allowed_sessions}."

        effective_max_open = self.cfg.max_open_trades
        if account.balance < 100:
            effective_max_open = 1
        elif account.balance < 1000:
            effective_max_open = min(effective_max_open, 2)

        if open_positions_count >= effective_max_open:
            return False, 0.0, f"Max open trades ({effective_max_open}) reached for balance ${account.balance:.2f}."

        if symbol_open_count >= self.cfg.max_trades_per_symbol:
            return False, 0.0, f"Max open trades per symbol ({self.cfg.max_trades_per_symbol}) reached for {setup.symbol}."

        if open_positions is not None and self.cfg.max_usd_exposure > 0:
            net_usd = sum(usd_direction_sign(p["symbol"], p["type"]) for p in open_positions)
            proposed = usd_direction_sign(setup.symbol, setup.direction)
            if abs(net_usd + proposed) > self.cfg.max_usd_exposure and abs(net_usd + proposed) > abs(net_usd):
                return (
                    False,
                    0.0,
                    f"USD correlation cap ({self.cfg.max_usd_exposure}) reached (net_usd={net_usd}, {setup.direction} {setup.symbol}).",
                )

        if today_trades >= self.cfg.max_daily_trades:
            return False, 0.0, f"Max daily trades ({self.cfg.max_daily_trades}) reached."

        max_daily_loss_amt = account.balance * (self.cfg.max_daily_loss_pct / 100.0)
        if today_pnl <= -max_daily_loss_amt:
            return False, 0.0, f"Max daily loss ({self.cfg.max_daily_loss_pct}%) reached ({today_pnl:.2f})."

        spread_price = specs.ask - specs.bid
        if setup.atr > 0 and (spread_price / setup.atr) > self.cfg.max_spread_atr_ratio:
            return False, 0.0, "Spread too wide relative to ATR."

        sl_dist = abs(setup.entry - setup.stop_loss)
        tp_dist = abs(setup.take_profit - setup.entry)
        if sl_dist <= 0 or (tp_dist / sl_dist) < self.cfg.min_risk_reward:
            return False, 0.0, f"Risk-to-reward below minimum {self.cfg.min_risk_reward}."

        if account.balance < 100:
            lot_size = round(specs.volume_min, 2)
        else:
            # Asymmetric conviction sizing: 0.75x on standard setups, 1.0x on A+ setups (>= 85), 0.5x on vol spikes / loss streaks
            conviction_mult = 1.0 if setup.smc_score >= 85 else 0.75
            vol_mult = 0.5 if vol_ratio > 1.8 else 1.0
            streak_mult = 0.5 if recent_loss_streak >= 2 else 1.0
            lot_size = self.calculate_lot_size(
                account.balance, sl_dist, specs, risk_mult=conviction_mult * vol_mult * streak_mult
            )
        if lot_size <= 0:
            return False, 0.0, "Calculated lot size is 0."

        # Small-account protection: ensure even volume_min doesn't exceed max_single_trade_risk_pct
        loss_per_lot = (sl_dist / specs.trade_tick_size) * specs.trade_tick_value if specs.trade_tick_size > 0 else 0.0
        actual_risk_pct = ((lot_size * loss_per_lot) / account.balance) * 100.0 if loss_per_lot > 0 else 0.0
        if actual_risk_pct > self.cfg.max_single_trade_risk_pct:
            return (
                False,
                0.0,
                f"Min lot ({lot_size}) risks {actual_risk_pct:.2f}% > cap {self.cfg.max_single_trade_risk_pct}% on ${account.balance:.2f}.",
            )

        if account.margin_free < account.balance * 0.15:
            return False, 0.0, f"Insufficient free margin (${account.margin_free:.2f})."

        return True, lot_size, "Approved by RiskManager"

    def calculate_lot_size(self, balance: float, sl_distance: float, specs: SymbolSpecs, risk_mult: float = 1.0) -> float:
        """Accurate MT5 lot sizing: risk_amount / ((sl_distance / tick_size) * tick_value)."""
        if sl_distance <= 0 or specs.trade_tick_size <= 0 or specs.trade_tick_value <= 0:
            return 0.0

        risk_amount = balance * (self.cfg.risk_per_trade_pct / 100.0) * risk_mult
        loss_per_lot = (sl_distance / specs.trade_tick_size) * specs.trade_tick_value
        if loss_per_lot <= 0:
            return 0.0

        raw_lots = risk_amount / loss_per_lot
        step = specs.volume_step if specs.volume_step > 0 else 0.01
        lots = math.floor(raw_lots / step) * step
        lots = round(max(specs.volume_min, min(specs.volume_max, lots)), 2)
        return lots
