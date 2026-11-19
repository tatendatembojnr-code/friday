"""Hard risk guardrails and accurate MT5 position sizing for FRIDAY."""

from __future__ import annotations

import logging
import math
from typing import Tuple

from config.settings import RiskConfig
from core.mt5_connector import AccountSnapshot, SymbolSpecs
from strategy.smc_engine import TradeSetup


class RiskManager:
    """Enforces non-negotiable risk limits and computes exact lot sizes."""

    def __init__(self, config: RiskConfig):
        self.logger = logging.getLogger("FRIDAY")
        self.cfg = config
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
    ) -> Tuple[bool, float, str]:
        if account.balance <= 0:
            return False, 0.0, "Account balance is zero or unavailable."

        if account.equity > self.peak_equity:
            self.peak_equity = account.equity

        if self.peak_equity > 0:
            drawdown_pct = ((self.peak_equity - account.equity) / self.peak_equity) * 100.0
            if drawdown_pct >= self.cfg.max_drawdown_pct:
                return False, 0.0, f"Max drawdown circuit breaker hit ({drawdown_pct:.2f}%)."

        if self.cfg.allowed_sessions and session not in self.cfg.allowed_sessions:
            return False, 0.0, f"Session '{session}' outside allowed sessions {self.cfg.allowed_sessions}."

        if open_positions_count >= self.cfg.max_open_trades:
            return False, 0.0, f"Max open trades ({self.cfg.max_open_trades}) reached."

        if symbol_open_count >= self.cfg.max_trades_per_symbol:
            return False, 0.0, f"Max open trades per symbol ({self.cfg.max_trades_per_symbol}) reached for {setup.symbol}."

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

        lot_size = self.calculate_lot_size(account.balance, sl_dist, specs)
        if lot_size <= 0:
            return False, 0.0, "Calculated lot size is 0."

        return True, lot_size, "Approved by RiskManager"

    def calculate_lot_size(self, balance: float, sl_distance: float, specs: SymbolSpecs) -> float:
        """Accurate MT5 lot sizing: risk_amount / ((sl_distance / tick_size) * tick_value)."""
        if sl_distance <= 0 or specs.trade_tick_size <= 0 or specs.trade_tick_value <= 0:
            return 0.0

        risk_amount = balance * (self.cfg.risk_per_trade_pct / 100.0)
        loss_per_lot = (sl_distance / specs.trade_tick_size) * specs.trade_tick_value
        if loss_per_lot <= 0:
            return 0.0

        raw_lots = risk_amount / loss_per_lot
        step = specs.volume_step if specs.volume_step > 0 else 0.01
        lots = math.floor(raw_lots / step) * step
        lots = round(max(specs.volume_min, min(specs.volume_max, lots)), 2)
        return lots
