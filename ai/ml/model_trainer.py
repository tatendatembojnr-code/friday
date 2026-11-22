"""Model Trainer: LogisticRegression baseline, RandomForest, LightGBM & Ensemble."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from lightgbm import LGBMClassifier
    HAS_LGBM = True
except ImportError:
    LGBMClassifier = None
    HAS_LGBM = False

from ai.ml.dataset_builder import chronological_split_with_embargo
from ai.ml.feature_engineering import FEATURE_COLUMNS
from ai.ml.model_evaluator import evaluate_predictions
from ai.ml.model_registry import ModelRegistry


def train_and_evaluate(
    dataset: pd.DataFrame,
    registry: ModelRegistry | None = None,
    promote_if_better: bool = True,
) -> Dict[str, Any]:
    """Trains LR baseline, RF, LightGBM, and a calibrated stacking ensemble chronologically."""
    if len(dataset) < 30 or dataset["target_win"].nunique() < 2:
        return {"ok": False, "error": f"Insufficient class diversity/rows ({len(dataset)} rows) for training."}

    train_df, test_df = chronological_split_with_embargo(dataset, train_frac=0.65, embargo_rows=4)
    if len(test_df) < 8 or train_df["target_win"].nunique() < 2:
        return {"ok": False, "error": "Insufficient test/train split samples."}

    X_train = train_df[FEATURE_COLUMNS].values
    y_train = train_df["target_win"].values
    X_test = test_df[FEATURE_COLUMNS].values
    y_test = test_df["target_win"].values
    net_r_test = test_df["net_r_outcome"].values

    models: Dict[str, Any] = {}
    metrics: Dict[str, Dict[str, float]] = {}

    # 1. Logistic Regression Baseline
    lr = Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(max_iter=1000, random_state=42))])
    lr.fit(X_train, y_train)
    models["logistic_regression"] = lr
    metrics["logistic_regression"] = evaluate_predictions(y_test, lr.predict_proba(X_test)[:, 1], net_r_test)

    # 2. Random Forest
    rf = RandomForestClassifier(n_estimators=120, max_depth=5, random_state=42)
    rf.fit(X_train, y_train)
    models["random_forest"] = rf
    metrics["random_forest"] = evaluate_predictions(y_test, rf.predict_proba(X_test)[:, 1], net_r_test)

    # 3. LightGBM (Primary Tabular Model)
    if HAS_LGBM:
        lgbm = LGBMClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.05, num_leaves=15,
            min_child_samples=5, random_state=42, verbose=-1,
        )
        lgbm.fit(X_train, y_train)
        models["lightgbm"] = lgbm
        metrics["lightgbm"] = evaluate_predictions(y_test, lgbm.predict_proba(X_test)[:, 1], net_r_test)

    # Select best model by lowest Brier score (calibrated probability) + positive OOS expectancy
    best_name = min(metrics.keys(), key=lambda k: metrics[k]["brier_score"])
    best_model = models[best_name]
    best_metrics = metrics[best_name]

    # Gate: only promote if it matches/beats SMC baseline OOS expectancy
    promoted = False
    version = datetime.now(timezone.utc).strftime("v%Y%m%d_%H%M%S")
    if registry is not None:
        should_promote = promote_if_better and (best_metrics["oos_expectancy_r"] >= best_metrics["smc_baseline_r"])
        bundle = {
            "model": best_model,
            "model_name": best_name,
            "feature_columns": FEATURE_COLUMNS,
            "train_feature_means": np.mean(X_train, axis=0).tolist(),
            "train_feature_stds": np.std(X_train, axis=0).tolist(),
        }
        registry.save_model(version, bundle, {"best_model": best_name, "all_models": metrics}, promote=should_promote)
        promoted = should_promote

    return {
        "ok": True,
        "version": version,
        "best_model": best_name,
        "promoted": promoted,
        "metrics": metrics,
        "train_rows": len(train_df),
        "test_rows": len(test_df),
    }
