"""ml/tests/test_psi.py
Unit tests for Population Stability Index (PSI) drift monitoring.
"""

import numpy as np
import pandas as pd
import pytest
from src.monitoring.psi import (
    compute_feature_psi,
    compute_all_psi,
    generate_psi_report,
)


def test_psi_identical_distributions_low():
    np.random.seed(42)
    expected = np.random.normal(loc=50, scale=10, size=5000)
    actual = np.random.normal(loc=50, scale=10, size=5000)

    psi = compute_feature_psi(expected, actual, bins=10)
    assert psi < 0.1  # Stable threshold


def test_psi_shifted_distribution_high():
    np.random.seed(42)
    expected = np.random.normal(loc=50, scale=10, size=5000)
    actual = np.random.normal(loc=70, scale=10, size=5000)  # Significant shift

    psi = compute_feature_psi(expected, actual, bins=10)
    assert psi > 0.2  # Shift threshold


def test_generate_psi_report_flags_drift():
    np.random.seed(42)
    train_df = pd.DataFrame({
        "income": np.random.normal(50000, 15000, 2000),
        "credit": np.random.normal(200000, 50000, 2000),
    })
    # 'credit' shifts significantly in production
    prod_df = pd.DataFrame({
        "income": np.random.normal(50000, 15000, 1000),
        "credit": np.random.normal(400000, 50000, 1000),
    })

    report = generate_psi_report(train_df, prod_df, feature_cols=["income", "credit"], threshold=0.2)

    assert "flagged_features" in report
    assert "credit" in report["flagged_features"]
    assert "income" not in report["flagged_features"]
