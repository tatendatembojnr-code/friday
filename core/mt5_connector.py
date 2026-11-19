"""MetaTrader 5 connection manager with simulation fallback."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

try:
    import MetaTrader5 as mt5
    HAS_MT5 = True
except ImportError:
    mt5 = None
    HAS_MT5 = False

from config.settings import Credentials


TIMEFRAME_MINUTES = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}


@dataclass
class SymbolSpecs:
    symbol: str
    digits: int
    point: float
    trade_tick_size: float
    trade_tick_value: float
    volume_min: float
    volume_max: float
    volume_step: float
    bid: float
    ask: float
    spread_points: float


@dataclass
class AccountSnapshot:
    balance: float
    equity: float
    margin_free: float
    profit: float


class MT5Connector:
    """Manages MetaTrader 5 initialization, data fetching, and simulated fallback."""

    def __init__(self, credentials: Credentials, simulate: bool = False):
        self.logger = logging.getLogger("FRIDAY")
        self.credentials = credentials
        self.simulate = simulate
        self.connected = False

    def connect(self) -> bool:
        if self.simulate:
            self.logger.info("Running in SIMULATION mode (synthetic market data, no MT5 required).")
            self.connected = True
            return True

        if not HAS_MT5:
            self.logger.error("MetaTrader5 package is not installed. Run: pip install MetaTrader5")
            return False

        init_kwargs = {}
        if self.credentials.mt5_path:
            init_kwargs["path"] = self.credentials.mt5_path

        if not mt5.initialize(**init_kwargs):
            self.logger.error(f"MT5 initialize() failed: {mt5.last_error()}")
            return False

        if self.credentials.mt5_login and self.credentials.mt5_password and self.credentials.mt5_server:
            authorized = mt5.login(
                login=self.credentials.mt5_login,
                password=self.credentials.mt5_password,
                server=self.credentials.mt5_server,
            )
            if not authorized:
                self.logger.error(f"MT5 login() failed: {mt5.last_error()}")
                mt5.shutdown()
                return False

        info = mt5.account_info()
        if info:
            self.logger.info(
                f"Connected to MT5 | Account={info.login} | Server={info.server} | Balance={info.balance:.2f}"
            )
        self.connected = True
        return True

    def shutdown(self) -> None:
        if not self.simulate and HAS_MT5 and self.connected:
            mt5.shutdown()
        self.connected = False

    def _tf_to_mt5(self, tf_name: str) -> int:
        mapping = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }
        return mapping[tf_name]

    def get_ohlc(self, symbol: str, tf_name: str, bars: int = 250) -> Optional[pd.DataFrame]:
        if self.simulate:
            return self._generate_synthetic_ohlc(symbol, tf_name, bars)

        if not mt5.symbol_select(symbol, True):
            self.logger.warning(f"Could not select symbol {symbol} in MT5")
            return None

        rates = mt5.copy_rates_from_pos(symbol, self._tf_to_mt5(tf_name), 0, bars)
        if rates is None or len(rates) == 0:
            import time
            time.sleep(0.5)
            rates = mt5.copy_rates_from_pos(symbol, self._tf_to_mt5(tf_name), 0, bars)
        if rates is None or len(rates) == 0:
            self.logger.warning(f"No rates returned for {symbol} {tf_name}")
            return None

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        df.set_index("time", inplace=True)
        return df[["open", "high", "low", "close", "tick_volume"]].copy()

    def get_symbol_specs(self, symbol: str) -> Optional[SymbolSpecs]:
        if self.simulate:
            is_jpy = "JPY" in symbol
            is_gold = "XAU" in symbol
            point = 0.01 if is_gold else (0.001 if is_jpy else 0.00001)
            digits = 2 if is_gold else (3 if is_jpy else 5)
            base = 2650.0 if is_gold else (154.5 if is_jpy else 1.0850)
            spread = point * 15
            return SymbolSpecs(
                symbol=symbol,
                digits=digits,
                point=point,
                trade_tick_size=point,
                trade_tick_value=1.0 if is_gold else (0.65 if is_jpy else 1.0),
                volume_min=0.01,
                volume_max=100.0,
                volume_step=0.01,
                bid=base,
                ask=base + spread,
                spread_points=15.0,
            )

        info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        if info is None or tick is None:
            return None
        spread_points = (tick.ask - tick.bid) / info.point if info.point else 0.0
        return SymbolSpecs(
            symbol=symbol,
            digits=info.digits,
            point=info.point,
            trade_tick_size=info.trade_tick_size or info.point,
            trade_tick_value=info.trade_tick_value or 1.0,
            volume_min=info.volume_min,
            volume_max=info.volume_max,
            volume_step=info.volume_step,
            bid=tick.bid,
            ask=tick.ask,
            spread_points=spread_points,
        )

    def get_account_snapshot(self) -> AccountSnapshot:
        if self.simulate:
            return AccountSnapshot(balance=10000.0, equity=10000.0, margin_free=10000.0, profit=0.0)
        info = mt5.account_info()
        if info is None:
            return AccountSnapshot(balance=0.0, equity=0.0, margin_free=0.0, profit=0.0)
        return AccountSnapshot(
            balance=info.balance,
            equity=info.equity,
            margin_free=info.margin_free,
            profit=info.profit,
        )

    def get_open_positions(self, magic: int | None = None) -> List[dict]:
        if self.simulate:
            return []
        positions = mt5.positions_get() or []
        results = []
        for p in positions:
            if magic is not None and p.magic != magic:
                continue
            results.append(
                {
                    "ticket": p.ticket,
                    "symbol": p.symbol,
                    "type": "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL",
                    "volume": p.volume,
                    "price_open": p.price_open,
                    "price_current": p.price_current,
                    "sl": p.sl,
                    "tp": p.tp,
                    "profit": p.profit,
                    "magic": p.magic,
                }
            )
        return results

    def get_today_closed_pnl(self) -> tuple[float, int]:
        if self.simulate:
            return 0.0, 0
        now = datetime.now(timezone.utc)
        start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        deals = mt5.history_deals_get(start, now)
        if deals is None:
            return 0.0, 0
        trade_deals = [d for d in deals if d.type in (mt5.DEAL_TYPE_BUY, mt5.DEAL_TYPE_SELL)]
        pnl = sum(d.profit + d.swap + d.commission for d in trade_deals if d.entry in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_INOUT))
        entry_deals = sum(1 for d in trade_deals if d.entry == mt5.DEAL_ENTRY_IN)
        return pnl, entry_deals

    def _generate_synthetic_ohlc(self, symbol: str, tf_name: str, bars: int) -> pd.DataFrame:
        """Generates realistic trend + liquidity sweep + BOS price action for simulation tests."""
        import zlib
        seed = zlib.crc32(f"{symbol}_{tf_name}".encode("utf-8"))
        rng = np.random.default_rng(seed)

        is_jpy = "JPY" in symbol
        is_gold = "XAU" in symbol
        base = 2650.0 if is_gold else (154.5 if is_jpy else 1.0850)
        step = 1.8 if is_gold else (0.12 if is_jpy else 0.0008)

        minutes = TIMEFRAME_MINUTES[tf_name]
        end = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        idx = [end - timedelta(minutes=minutes * i) for i in range(bars)][::-1]

        # Build an uptrend with a liquidity sweep and bullish BOS near the end
        closes = [base]
        for i in range(1, bars):
            drift = step * 0.08
            noise = rng.normal(0, step * 0.45)
            closes.append(closes[-1] + drift + noise)

        if tf_name == "M15" and bars >= 30:
            # Create a clear swing low at -18, swing high at -12, sweep at -5, then bullish BOS
            ref = closes[-25]
            closes[-20] = ref + step * 0.6
            closes[-19] = ref + step * 0.1
            closes[-18] = ref - step * 1.2  # Clear fractal swing low
            closes[-17] = ref + step * 0.1
            closes[-16] = ref + step * 0.5
            closes[-14] = ref + step * 0.8
            closes[-13] = ref + step * 1.2
            closes[-12] = ref + step * 1.6  # Clear fractal swing high
            closes[-11] = ref + step * 1.1
            closes[-10] = ref + step * 0.7
            closes[-5] = ref - step * 2.2   # Liquidity sweep below swing low (-18)
            closes[-4] = ref + step * 0.3   # Bullish engulfing rejection
            closes[-3] = ref + step * 1.2
            closes[-2] = ref + step * 1.9   # BOS above swing high (-12)
            closes[-1] = ref + step * 2.1

        closes_arr = np.array(closes)
        opens = np.roll(closes_arr, 1)
        opens[0] = closes_arr[0]
        highs = np.maximum(opens, closes_arr) + np.abs(rng.normal(0, step * 0.25, bars))
        lows = np.minimum(opens, closes_arr) - np.abs(rng.normal(0, step * 0.25, bars))

        if tf_name == "M15" and bars >= 30:
            lows[-18] = closes_arr[-18] - step * 0.4
            highs[-12] = closes_arr[-12] + step * 0.4
            lows[-5] = closes_arr[-18] - step * 1.5  # Deep sweep wick below -18's low
            closes_arr[-4] = closes_arr[-5] + step * 2.5
            opens[-4] = closes_arr[-5]
            closes_arr[-1] = float(np.max(highs[-15:-1])) + step * 0.6
            highs[-1] = closes_arr[-1] + step * 0.1

        vol = rng.integers(150, 1200, size=bars)
        df = pd.DataFrame(
            {"open": opens, "high": highs, "low": lows, "close": closes_arr, "tick_volume": vol},
            index=pd.DatetimeIndex(idx, name="time"),
        )
        return df
