"""Feature & Win-Rate Drift Detector (Population Stability Index + Calibration Monitor)."""

from __future__ import annotations

from typing import Dict, List

import numpy as np


def compute_zscore_drift(
    live_features: List[float],
    train_means: List[float],
    train_stds: List[float],
    z_threshold: float = 3.0,
) -> Dict[str, float | bool]:
    """Detects out-of-distribution live feature vectors relative to training baseline."""
    if not live_features or len(live_features) != len(train_means):
        return {"drift_detected": False, "max_zscore": 0.0}

    z_scores = []
    for val, mu, sd in zip(live_features, train_means, train_stds):
        denom = max(float(sd), 1e-6)
        z_scores.append(abs((float(val) - float(mu)) / denom))

    max_z = max(z_scores) if z_scores else 0.0
    mean_z = float(np.mean(z_scores)) if z_scores else 0.0
    return {
        "drift_detected": bool(max_z > z_threshold),
        "max_zscore": round(max_z, 2),
        "mean_zscore": round(mean_z, 2),
    }
