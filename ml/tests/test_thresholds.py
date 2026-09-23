"""ml/tests/test_thresholds.py
Unit tests for business decision thresholds and cost-based optimization.
"""

import numpy as np
import pytest
from src.thresholds import (
    apply_threshold,
    cost_based_sweep,
    youdens_j_threshold,
)


def test_apply_threshold_tiers():
    assert apply_threshold(0.15, low_threshold=0.35, high_threshold=0.65) == "approved"
    assert apply_threshold(0.50, low_threshold=0.35, high_threshold=0.65) == "manual_review"
    assert apply_threshold(0.85, low_threshold=0.35, high_threshold=0.65) == "rejected"


def test_cost_based_sweep_returns_valid_thresholds():
    np.random.seed(42)
    y_true = np.array([0] * 900 + [1] * 100)
    # Predicted probabilities loosely aligned with true label
    y_prob = np.concatenate([
        np.random.beta(1, 5, size=900),  # low probs for non-defaults
        np.random.beta(5, 2, size=100),  # high probs for defaults
    ])

    results = cost_based_sweep(y_true, y_prob, cost_fn_ratio=5.0)

    assert "low_threshold" in results
    assert "high_threshold" in results
    assert 0.0 < results["low_threshold"] < results["high_threshold"] < 1.0


def test_youdens_j_statistic():
    y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9])

    best_thresh = youdens_j_threshold(y_true, y_prob)
    assert 0.4 <= best_thresh <= 0.6
