"""Live ML Inference Pipeline (Meta-Labeling + Regime + Drift Check)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd

from ai.ml.drift_detector import compute_zscore_drift
from ai.ml.feature_engineering import FEATURE_COLUMNS, extract_decision_features
from ai.ml.market_regime import RegimeState, detect_market_regime
from ai.ml.model_registry import ModelRegistry
from strategy.smc_engine import TradeSetup


@dataclass
class MLPrediction:
    ml_available: bool
    model_version: str
    model_name: str
    p_win: float
    expected_r: float
    regime: RegimeState
    drift_detected: bool
    decision: str  # "APPROVE", "REJECT", "ABSTAIN"


class MLInferencePipeline:
    """Runs trained Champion ML model on live decision-time features; never fakes ML if untrained."""

    def __init__(self, registry: ModelRegistry | None = None, min_p_win: float = 0.52):
        self.registry = registry or ModelRegistry()
        self.min_p_win = min_p_win
        self.version, self.bundle, self.meta = self.registry.load_champion()

    def reload(self) -> None:
        self.version, self.bundle, self.meta = self.registry.load_champion()

    def predict(
        self,
        df_ltf: pd.DataFrame,
        setup: TradeSetup,
        vwap: float = 0.0,
        spread_atr_ratio: float = 0.05,
        vol_ratio: float = 1.0,
    ) -> MLPrediction:
        regime = detect_market_regime(df_ltf)
        if not self.bundle or not self.version:
            return MLPrediction(
                ml_available=False,
                model_version="NONE",
                model_name="untrained",
                p_win=0.0,
                expected_r=0.0,
                regime=regime,
                drift_detected=False,
                decision="ABSTAIN",
            )

        feats = extract_decision_features(df_ltf, setup, vwap=vwap, spread_atr_ratio=spread_atr_ratio, vol_ratio=vol_ratio)
        cols = self.bundle.get("feature_columns", FEATURE_COLUMNS)
        vec = [feats[c] for c in cols]
        X = np.array([vec], dtype=float)

        drift = compute_zscore_drift(
            vec,
            self.bundle.get("train_feature_means", []),
            self.bundle.get("train_feature_stds", []),
        )

        model = self.bundle["model"]
        p_win = float(model.predict_proba(X)[0, 1])
        expected_r = round((p_win * setup.risk_reward) - ((1.0 - p_win) * 1.0), 4)

        if drift["drift_detected"] or regime.uncertainty > 0.75:
            decision = "ABSTAIN"
        elif p_win >= self.min_p_win and expected_r > 0:
            decision = "APPROVE"
        else:
            decision = "REJECT"

        return MLPrediction(
            ml_available=True,
            model_version=self.version,
            model_name=self.bundle.get("model_name", "unknown"),
            p_win=round(p_win, 4),
            expected_r=expected_r,
            regime=regime,
            drift_detected=bool(drift["drift_detected"]),
            decision=decision,
        )
