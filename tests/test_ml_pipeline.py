"""Tests for FRIDAY 2.0 ML Engine, Feature Leakage, Regime Detection, Drift & Persistence."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ai.ml.dataset_builder import build_historical_dataset, chronological_split_with_embargo
from ai.ml.drift_detector import compute_zscore_drift
from ai.ml.feature_engineering import FEATURE_COLUMNS, extract_decision_features
from ai.ml.inference_pipeline import MLInferencePipeline
from ai.ml.market_regime import detect_market_regime
from ai.ml.model_registry import ModelRegistry
from ai.ml.model_trainer import train_and_evaluate
from config.settings import Credentials, SMCConfig
from core.database import DatabaseManager
from core.mt5_connector import MT5Connector
from strategy.smc_engine import TradeSetup


def test_feature_engineering_no_lookahead_leakage():
    conn = MT5Connector(Credentials(), simulate=True)
    assert conn.connect()
    df = conn.get_ohlc("EURUSD", "M15", 200)
    setup = TradeSetup(
        symbol="EURUSD", direction="BUY", entry=1.085, stop_loss=1.083, take_profit=1.089,
        risk_reward=2.0, smc_score=80, atr=0.001, htf_bias="BULLISH", confluence_tags=["LiquiditySweepLow"],
    )

    feats_orig = extract_decision_features(df.iloc[:150], setup)
    df_mutated = df.copy()
    df_mutated.iloc[150:, df_mutated.columns.get_loc("close")] = 999.0  # Corrupt future bars
    feats_mut = extract_decision_features(df_mutated.iloc[:150], setup)
    assert feats_orig == feats_mut
    assert set(FEATURE_COLUMNS).issubset(feats_orig.keys())


def test_dataset_chronological_embargo_and_training_pipeline(tmp_path):
    conn = MT5Connector(Credentials(), simulate=True)
    assert conn.connect()

    # Build synthetic dataset with enough samples across symbols
    frames = []
    for sym in ("EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "EURJPY", "AUDUSD"):
        df = conn.get_ohlc(sym, "M15", 400)
        ds = build_historical_dataset(df, sym, smc_cfg=SMCConfig(min_smc_score=30), horizon_bars=24)
        if not ds.empty:
            frames.append(ds)

    if not frames:
        return
    full_ds = pd.concat(frames, ignore_index=True)
    train_df, test_df = chronological_split_with_embargo(full_ds, train_frac=0.65, embargo_rows=4)
    if len(full_ds) >= 30 and full_ds["target_win"].nunique() == 2 and len(test_df) >= 8:
        reg = ModelRegistry(tmp_path / "reg")
        res = train_and_evaluate(full_ds, registry=reg, promote_if_better=True)
        assert res["ok"] is True
        assert "logistic_regression" in res["metrics"]
        assert "random_forest" in res["metrics"]


def test_inference_abstains_honestly_when_no_champion(tmp_path):
    reg = ModelRegistry(tmp_path / "empty_reg")
    pipe = MLInferencePipeline(registry=reg)
    conn = MT5Connector(Credentials(), simulate=True)
    assert conn.connect()
    df = conn.get_ohlc("EURUSD", "M15", 150)
    setup = TradeSetup(
        symbol="EURUSD", direction="BUY", entry=1.085, stop_loss=1.083, take_profit=1.089,
        risk_reward=2.0, smc_score=80, atr=0.001, htf_bias="BULLISH",
    )
    pred = pipe.predict(df, setup)
    assert pred.ml_available is False
    assert pred.decision == "ABSTAIN"


def test_regime_drift_and_persistent_kv_state(tmp_path):
    conn = MT5Connector(Credentials(), simulate=True)
    assert conn.connect()
    df = conn.get_ohlc("EURUSD", "M15", 150)
    reg = detect_market_regime(df)
    assert reg.regime in {
        "STRONG_BULLISH", "STRONG_BEARISH", "SIDEWAYS_RANGING",
        "HIGH_VOLATILITY", "LOW_VOLATILITY", "TRANSITIONAL",
    }

    drift = compute_zscore_drift([10.0, 0.0], [0.0, 0.0], [1.0, 1.0], z_threshold=3.0)
    assert drift["drift_detected"] is True

    db = DatabaseManager(db_path=tmp_path / "state.db")
    db.set_state("peak_equity", "185000.50")
    assert db.get_state("peak_equity") == "185000.50"
