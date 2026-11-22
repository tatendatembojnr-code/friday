"""CLI script to build historical datasets and train FRIDAY's ML models."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ai.ml.dataset_builder import build_historical_dataset
from ai.ml.model_registry import ModelRegistry
from ai.ml.model_trainer import train_and_evaluate
from config.settings import FridaySettings, SMCConfig
from core.mt5_connector import MT5Connector


def main() -> None:
    parser = argparse.ArgumentParser(description="FRIDAY 2.0 ML Training Pipeline")
    parser.add_argument("--bars", type=int, default=600, help="Historical M15 bars per symbol")
    parser.add_argument("--live-data", action="store_true", help="Fetch real MT5 history instead of synthetic")
    args = parser.parse_args()

    settings = FridaySettings.load()
    conn = MT5Connector(settings.credentials, simulate=not args.live_data)
    if not conn.connect():
        print("Failed to connect to data source.")
        sys.exit(1)

    frames = []
    for sym in settings.trading.symbols:
        df = conn.get_ohlc(sym, settings.trading.ltf_timeframe, args.bars)
        if df is not None and len(df) >= 150:
            ds = build_historical_dataset(df, sym, smc_cfg=SMCConfig(min_smc_score=45))
            if not ds.empty:
                frames.append(ds)
    conn.shutdown()

    if not frames:
        print("No training samples generated.")
        sys.exit(1)

    full_ds = pd.concat(frames, ignore_index=True)
    print(f"Built dataset: {len(full_ds)} candidate setups across {len(frames)} symbols.")
    registry = ModelRegistry(BASE_DIR / "models" / "registry")
    res = train_and_evaluate(full_ds, registry=registry, promote_if_better=True)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
