"""Standalone CLI Backtest Runner across all configured FRIDAY symbols."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import FridaySettings
from core.backtester import run_backtest
from core.mt5_connector import MT5Connector


def main() -> None:
    parser = argparse.ArgumentParser(description="FRIDAY Multi-Symbol CLI Backtester")
    parser.add_argument("--bars", type=int, default=300, help="Number of M15 bars to replay")
    parser.add_argument("--live-data", action="store_true", help="Use live MT5 history instead of synthetic data")
    args = parser.parse_args()

    settings = FridaySettings.load()
    connector = MT5Connector(settings.credentials, simulate=not args.live_data)
    if not connector.connect():
        print("Failed to connect for backtest.")
        sys.exit(1)

    print(f"=== FRIDAY Backtest ({'MT5' if args.live_data else 'SIMULATE'}, {args.bars} bars) ===")
    for sym in settings.trading.symbols:
        res = run_backtest(connector, settings, symbol=sym, bars=args.bars)
        if "error" in res:
            print(f"{sym:8s} | ERROR: {res['error']}")
        else:
            print(
                f"{sym:8s} | Trades={res['total_trades']:2d} | WinRate={res['win_rate_pct']:5.1f}% | "
                f"PF={res['profit_factor']:5.2f} | Net={res['net_return_pct']:+6.2f}% | MaxDD={res['max_drawdown_pct']:5.2f}%"
            )
    connector.shutdown()


if __name__ == "__main__":
    main()
