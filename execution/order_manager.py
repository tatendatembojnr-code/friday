"""Order execution and dynamic trade management for FRIDAY."""

from __future__ import annotations

import logging
from typing import Dict

try:
    import MetaTrader5 as mt5
    HAS_MT5 = True
except ImportError:
    mt5 = None
    HAS_MT5 = False

from config.settings import RiskConfig
from core.mt5_connector import MT5Connector
from strategy.smc_engine import TradeSetup


class OrderManager:
    """Places market orders (live or dry-run) and manages breakeven / trailing stops."""

    def __init__(self, connector: MT5Connector, risk_cfg: RiskConfig, magic_number: int, dry_run: bool = True):
        self.logger = logging.getLogger("FRIDAY")
        self.connector = connector
        self.risk_cfg = risk_cfg
        self.magic = magic_number
        self.dry_run = dry_run or connector.simulate

    def execute_setup(self, setup: TradeSetup, lot_size: float) -> Dict:
        specs = self.connector.get_symbol_specs(setup.symbol)
        if specs is None:
            return {"success": False, "error": f"No symbol specs for {setup.symbol}"}

        exec_price = specs.ask if setup.direction == "BUY" else specs.bid
        sl_dist = abs(setup.entry - setup.stop_loss)
        tp_dist = abs(setup.take_profit - setup.entry)
        if setup.direction == "BUY":
            sl = round(exec_price - sl_dist, specs.digits)
            tp = round(exec_price + tp_dist, specs.digits)
        else:
            sl = round(exec_price + sl_dist, specs.digits)
            tp = round(exec_price - tp_dist, specs.digits)

        if self.dry_run:
            self.logger.info(
                f"[DRY-RUN] {setup.direction} {setup.symbol} | Lots={lot_size} | "
                f"Entry={exec_price:.{specs.digits}f} | SL={sl:.{specs.digits}f} | TP={tp:.{specs.digits}f}"
            )
            return {"success": True, "order_id": "DRY_RUN", "price": exec_price}

        if not HAS_MT5:
            return {"success": False, "error": "MetaTrader5 package unavailable"}

        order_type = mt5.ORDER_TYPE_BUY if setup.direction == "BUY" else mt5.ORDER_TYPE_SELL
        filling_mode = self._resolve_filling_mode(setup.symbol)
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": setup.symbol,
            "volume": lot_size,
            "type": order_type,
            "price": exec_price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": self.magic,
            "comment": f"FRIDAY_{setup.smc_score}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }

        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            err = mt5.last_error() if result is None else f"retcode={result.retcode} ({result.comment})"
            self.logger.error(f"Order failed for {setup.symbol}: {err}")
            return {"success": False, "error": err}

        self.logger.info(f"LIVE ORDER EXECUTED | Ticket={result.order} | {setup.direction} {setup.symbol} {lot_size} lots")
        return {"success": True, "order_id": result.order, "price": result.price}

    def manage_open_positions(self) -> None:
        if self.dry_run or not HAS_MT5:
            return

        positions = self.connector.get_open_positions(magic=self.magic)
        for pos in positions:
            if pos["sl"] <= 0:
                continue
            specs = self.connector.get_symbol_specs(pos["symbol"])
            if specs is None:
                continue

            entry = pos["price_open"]
            curr = pos["price_current"]
            sl = pos["sl"]
            risk_dist = abs(entry - sl)
            if risk_dist <= 0:
                continue

            if pos["type"] == "BUY":
                rr_achieved = (curr - entry) / risk_dist
                new_sl = None
                if rr_achieved >= self.risk_cfg.breakeven_at_rr and sl < entry:
                    new_sl = round(entry + specs.point * 5, specs.digits)
                elif rr_achieved >= self.risk_cfg.trailing_start_rr:
                    candidate = round(curr - risk_dist * self.risk_cfg.trailing_atr_mult, specs.digits)
                    if candidate > sl:
                        new_sl = candidate
                if new_sl and new_sl > sl:
                    self._modify_sl(pos["ticket"], pos["symbol"], new_sl, pos["tp"])

            else:  # SELL
                rr_achieved = (entry - curr) / risk_dist
                new_sl = None
                if rr_achieved >= self.risk_cfg.breakeven_at_rr and sl > entry:
                    new_sl = round(entry - specs.point * 5, specs.digits)
                elif rr_achieved >= self.risk_cfg.trailing_start_rr:
                    candidate = round(curr + risk_dist * self.risk_cfg.trailing_atr_mult, specs.digits)
                    if candidate < sl:
                        new_sl = candidate
                if new_sl and new_sl < sl:
                    self._modify_sl(pos["ticket"], pos["symbol"], new_sl, pos["tp"])

    def _resolve_filling_mode(self, symbol: str) -> int:
        info = mt5.symbol_info(symbol)
        if info is None:
            return mt5.ORDER_FILLING_IOC
        mode = info.filling_mode
        if mode & 2:  # SYMBOL_FILLING_IOC
            return mt5.ORDER_FILLING_IOC
        if mode & 1:  # SYMBOL_FILLING_FOK
            return mt5.ORDER_FILLING_FOK
        return mt5.ORDER_FILLING_RETURN

    def _modify_sl(self, ticket: int, symbol: str, new_sl: float, tp: float) -> None:
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": symbol,
            "sl": new_sl,
            "tp": tp,
        }
        res = mt5.order_send(request)
        if res and res.retcode == mt5.TRADE_RETCODE_DONE:
            self.logger.info(f"Updated SL for ticket {ticket} ({symbol}) -> {new_sl}")
