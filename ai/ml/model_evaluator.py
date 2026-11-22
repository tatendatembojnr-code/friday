"""Out-of-sample model evaluation: Calibration (Brier), Log-Loss, AUC, and Net Expectancy."""

from __future__ import annotations

from typing import Dict

import numpy as np
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score


def evaluate_predictions(
    y_true: np.ndarray,
    probs: np.ndarray,
    net_r: np.ndarray,
    threshold: float = 0.55,
) -> Dict[str, float]:
    probs = np.clip(probs, 1e-6, 1.0 - 1e-6)
    brier = float(brier_score_loss(y_true, probs))
    ll = float(log_loss(y_true, probs, labels=[0, 1]))
    auc = float(roc_auc_score(y_true, probs)) if len(np.unique(y_true)) > 1 else 0.5

    taken = probs >= threshold
    n_taken = int(np.sum(taken))
    expectancy_r = float(np.mean(net_r[taken])) if n_taken > 0 else 0.0
    baseline_r = float(np.mean(net_r)) if len(net_r) > 0 else 0.0
    win_rate = float(np.mean(y_true[taken]) * 100.0) if n_taken > 0 else 0.0

    return {
        "brier_score": round(brier, 4),
        "log_loss": round(ll, 4),
        "roc_auc": round(auc, 4),
        "trades_taken": n_taken,
        "win_rate_pct": round(win_rate, 1),
        "oos_expectancy_r": round(expectancy_r, 4),
        "smc_baseline_r": round(baseline_r, 4),
    }
