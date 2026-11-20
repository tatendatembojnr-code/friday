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
        self._scaled_out_tickets: set[int] = set()
        self._peak_rr: Dict[int, float] = {}
        self._opened_at: Dict[int, float] = {}

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

            import time
            ticket = pos["ticket"]
            self._opened_at.setdefault(ticket, time.monotonic())
            age_minutes = (time.monotonic() - self._opened_at[ticket]) / 60.0

            rr_achieved = (
                (curr - entry) / risk_dist if pos["type"] == "BUY" else (entry - curr) / risk_dist
            )
            peak = max(self._peak_rr.get(ticket, 0.0), rr_achieved)
            self._peak_rr[ticket] = peak

            # 1. Peak-Profit Giveback Ratchet: if trade reached >= 0.6R and gives back 35% of peak profit, harvest it
            if peak >= 0.6 and rr_achieved > 0.15 and rr_achieved <= peak * 0.65:
                if self.close_position(pos, reason=f"ProfitGivebackExit (peak={peak:.2f}R -> {rr_achieved:.2f}R)"):
                    continue

            # 2. Freqtrade-style Time-Decay ROI: harvest stalled green trades to free capital for fresh setups
            if (age_minutes >= 45 and rr_achieved >= 0.25) or (age_minutes >= 15 and rr_achieved >= 0.60):
                if self.close_position(pos, reason=f"TimeDecayROI (age={age_minutes:.0f}m, rr={rr_achieved:.2f}R)"):
                    continue

            # 3. Early Loss-Cut (Structure Invalidation): cut losers at -0.50R when M15 trend flips against the trade
            if rr_achieved <= -0.50:
                df_m15 = self.connector.get_ohlc(pos["symbol"], "M15", 60)
                if df_m15 is not None and len(df_m15) >= 50:
                    ema20 = float(df_m15["close"].ewm(span=20, adjust=False).mean().iloc[-1])
                    ema50 = float(df_m15["close"].ewm(span=50, adjust=False).mean().iloc[-1])
                    flipped = (pos["type"] == "BUY" and ema20 < ema50) or (pos["type"] == "SELL" and ema20 > ema50)
                    if flipped:
                        if self.close_position(pos, reason=f"StructureInvalidationExit (rr={rr_achieved:.2f}R, M15 flipped)"):
                            continue

            if pos["type"] == "BUY":
                if rr_achieved >= self.risk_cfg.breakeven_at_rr and pos["ticket"] not in self._scaled_out_tickets:
                    self._partial_close(pos, specs)
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
                if rr_achieved >= self.risk_cfg.breakeven_at_rr and pos["ticket"] not in self._scaled_out_tickets:
                    self._partial_close(pos, specs)
                new_sl = None
                if rr_achieved >= self.risk_cfg.breakeven_at_rr and sl > entry:
                    new_sl = round(entry - specs.point * 5, specs.digits)
                elif rr_achieved >= self.risk_cfg.trailing_start_rr:
                    candidate = round(curr + risk_dist * self.risk_cfg.trailing_atr_mult, specs.digits)
                    if candidate < sl:
                        new_sl = candidate
                if new_sl and new_sl < sl:
                    self._modify_sl(pos["ticket"], pos["symbol"], new_sl, pos["tp"])

    def _partial_close(self, pos: Dict, specs) -> None:
        """Locks in 50% of the position at 1R profit while letting the remainder trail."""
        import math
        half_vol = math.floor((pos["volume"] * 0.5) / specs.volume_step) * specs.volume_step
        half_vol = round(half_vol, 2)
        if half_vol < specs.volume_min or (pos["volume"] - half_vol) < specs.volume_min:
            self._scaled_out_tickets.add(pos["ticket"])
            return
        close_type = mt5.ORDER_TYPE_SELL if pos["type"] == "BUY" else mt5.ORDER_TYPE_BUY
        price = specs.bid if pos["type"] == "BUY" else specs.ask
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos["symbol"],
            "volume": half_vol,
            "type": close_type,
            "position": pos["ticket"],
            "price": price,
            "deviation": 20,
            "magic": self.magic,
            "comment": "FRIDAY_SCALE_OUT",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": self._resolve_filling_mode(pos["symbol"]),
        }
        res = mt5.order_send(request)
        if res and res.retcode == mt5.TRADE_RETCODE_DONE:
            self._scaled_out_tickets.add(pos["ticket"])
            self.logger.info(
                f"PARTIAL TP (50% LOCKED) | Ticket={pos['ticket']} ({pos['symbol']}) | Closed {half_vol} lots"
            )

    def close_position(self, pos: Dict, reason: str = "") -> bool:
        """Close an open position at market (e.g., on AI/SMC reversal)."""
        if self.dry_run or not HAS_MT5:
            return False
        specs = self.connector.get_symbol_specs(pos["symbol"])
        if specs is None:
            return False
        close_type = mt5.ORDER_TYPE_SELL if pos["type"] == "BUY" else mt5.ORDER_TYPE_BUY
        price = specs.bid if pos["type"] == "BUY" else specs.ask
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos["symbol"],
            "volume": pos["volume"],
            "type": close_type,
            "position": pos["ticket"],
            "price": price,
            "deviation": 20,
            "magic": self.magic,
            "comment": "FRIDAY_REV_CLOSE",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": self._resolve_filling_mode(pos["symbol"]),
        }
        res = mt5.order_send(request)
        if res and res.retcode == mt5.TRADE_RETCODE_DONE:
            self.logger.info(
                f"AUTO-CLOSED Ticket={pos['ticket']} ({pos['symbol']} {pos['type']}) | PnL={pos['profit']:.2f} | {reason}"
            )
            return True
        return False

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
