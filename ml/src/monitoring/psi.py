"""
psi.py
======
Population Stability Index (PSI) monitoring for CrediShield AI.

PSI measures how much the distribution of a feature has shifted between
a reference (training) dataset and a current (production/new) dataset.

Severity bands (industry standard):
  PSI < 0.1   → 'stable'   — No significant change; model remains valid.
  0.1 ≤ PSI < 0.2 → 'warning' — Some change; investigate feature behaviour.
  PSI ≥ 0.2   → 'shift'    — Significant shift; model retraining likely needed.

Reference: Siddiqi, N. (2012). Credit Risk Scorecards. John Wiley & Sons.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# PSI severity classification
# ---------------------------------------------------------------------------

def _psi_severity(psi_value: float) -> str:
    """Map a PSI float to its severity label."""
    if psi_value < 0.1:
        return "stable"
    elif psi_value < 0.2:
        return "warning"
    else:
        return "shift"


# ---------------------------------------------------------------------------
# Core PSI computation
# ---------------------------------------------------------------------------

def compute_feature_psi(
    expected: np.ndarray,
    actual: np.ndarray,
    bins: int = 10,
) -> float:
    """
    Compute the Population Stability Index (PSI) for a single feature.

    The PSI is defined as:
        PSI = Σ (actual_pct_i - expected_pct_i) * ln(actual_pct_i / expected_pct_i)

    For **continuous** features, bin boundaries are computed from the *expected*
    (training) distribution using quantiles, then the actual distribution is
    bucketed into those same boundaries.

    For **categorical** features (dtype object or category), unique value counts
    are used directly as buckets.

    Parameters
    ----------
    expected : np.ndarray
        Feature values from the reference (training) dataset.
    actual : np.ndarray
        Feature values from the new (production) dataset.
    bins : int
        Number of quantile bins for continuous features. Ignored for categoricals.

    Returns
    -------
    float
        PSI value (non-negative). Returns 0.0 if the feature has only one
        unique value (no distribution to compare).
    """
    expected = np.asarray(expected)
    actual = np.asarray(actual)

    # Remove NaNs before computation
    expected = expected[~pd.isnull(expected)]
    actual = actual[~pd.isnull(actual)]

    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    # Determine if categorical (object/string) or numerical
    is_categorical = (
        expected.dtype == object
        or expected.dtype.name == "category"
        or not np.issubdtype(expected.dtype, np.number)
    )

    if is_categorical:
        return _psi_categorical(expected, actual)
    else:
        return _psi_continuous(expected, actual, bins)


def _psi_continuous(
    expected: np.ndarray,
    actual: np.ndarray,
    bins: int,
) -> float:
    """Internal: PSI for a continuous (numerical) feature using quantile bins."""
    # Build bin edges from the expected (training) distribution
    # Using linspace of percentiles to get quantile-based edges
    percentiles = np.linspace(0, 100, bins + 1)
    bin_edges = np.nanpercentile(expected, percentiles)

    # Deduplicate edges that collapse to the same value
    bin_edges = np.unique(bin_edges)
    if len(bin_edges) < 2:
        return 0.0  # All values are identical

    # Extend edges slightly to capture min/max of actual
    bin_edges[0] = min(bin_edges[0], actual.min()) - 1e-9
    bin_edges[-1] = max(bin_edges[-1], actual.max()) + 1e-9

    # Count observations per bin
    expected_counts, _ = np.histogram(expected, bins=bin_edges)
    actual_counts, _ = np.histogram(actual, bins=bin_edges)

    return _compute_psi_from_counts(expected_counts, actual_counts)


def _psi_categorical(expected: np.ndarray, actual: np.ndarray) -> float:
    """Internal: PSI for a categorical feature using value-count buckets."""
    # Get union of all categories
    all_categories = np.union1d(
        np.unique(expected.astype(str)),
        np.unique(actual.astype(str)),
    )

    expected_series = pd.Series(expected.astype(str))
    actual_series = pd.Series(actual.astype(str))

    expected_counts = np.array(
        [expected_series.value_counts().get(cat, 0) for cat in all_categories]
    )
    actual_counts = np.array(
        [actual_series.value_counts().get(cat, 0) for cat in all_categories]
    )

    return _compute_psi_from_counts(expected_counts, actual_counts)


def _compute_psi_from_counts(
    expected_counts: np.ndarray,
    actual_counts: np.ndarray,
) -> float:
    """
    Core PSI formula applied to raw bin counts.

    Applies a small epsilon to avoid division-by-zero and log(0) issues.
    """
    epsilon = 1e-6  # Smoothing constant

    expected_pct = (expected_counts + epsilon) / (expected_counts.sum() + epsilon * len(expected_counts))
    actual_pct = (actual_counts + epsilon) / (actual_counts.sum() + epsilon * len(actual_counts))

    psi_value = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return float(max(0.0, psi_value))  # PSI is non-negative by definition


# ---------------------------------------------------------------------------
# Dataset-level PSI
# ---------------------------------------------------------------------------

def compute_all_psi(
    training_df: pd.DataFrame,
    new_df: pd.DataFrame,
    feature_cols: List[str],
) -> Dict[str, float]:
    """
    Compute PSI for every column in `feature_cols` between two DataFrames.

    Parameters
    ----------
    training_df : pd.DataFrame
        Reference dataset (training distribution).
    new_df : pd.DataFrame
        New dataset (production / current month distribution).
    feature_cols : list of str
        Column names to compute PSI for. Columns missing from either
        DataFrame are skipped with a warning.

    Returns
    -------
    dict
        { feature_name: psi_value } for each available feature.
    """
    psi_results: Dict[str, float] = {}

    for col in feature_cols:
        if col not in training_df.columns:
            print(f"[compute_all_psi] WARNING: '{col}' not in training_df — skipping.")
            continue
        if col not in new_df.columns:
            print(f"[compute_all_psi] WARNING: '{col}' not in new_df — skipping.")
            continue

        psi_val = compute_feature_psi(
            expected=training_df[col].values,
            actual=new_df[col].values,
        )
        psi_results[col] = psi_val

    return psi_results


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_psi_report(
    training_df: pd.DataFrame,
    new_df: pd.DataFrame,
    feature_cols: List[str],
    threshold: float = 0.2,
    output_path: Optional[str] = None,
) -> Dict:
    """
    Generate a comprehensive PSI monitoring report.

    Parameters
    ----------
    training_df : pd.DataFrame
        Reference (training) dataset.
    new_df : pd.DataFrame
        New (production / current period) dataset.
    feature_cols : list of str
        Features to include in the report.
    threshold : float
        PSI value above which a feature is flagged as drifted.
        Default 0.2 (industry standard for 'shift' band).
    output_path : str, optional
        If provided, saves the report as a JSON file at this path.

    Returns
    -------
    dict with keys:
      computed_at     : str — ISO-8601 UTC timestamp
      total_features  : int — number of features evaluated
      flagged_features: list of str — features with PSI > threshold
      feature_psi     : dict { feature: psi_value }
      severity        : dict { feature: severity_label }
                         'stable' | 'warning' | 'shift'
    """
    feature_psi = compute_all_psi(training_df, new_df, feature_cols)

    severity = {feat: _psi_severity(psi_val) for feat, psi_val in feature_psi.items()}
    flagged = [feat for feat, psi_val in feature_psi.items() if psi_val > threshold]

    report = {
        "computed_at": datetime.now(tz=timezone.utc).isoformat(),
        "total_features": len(feature_psi),
        "flagged_features": sorted(flagged),
        "feature_psi": {k: round(v, 6) for k, v in feature_psi.items()},
        "severity": severity,
        "threshold_used": threshold,
        "training_rows": len(training_df),
        "new_rows": len(new_df),
    }

    if output_path is not None:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print(f"[generate_psi_report] Report saved → {out_path.resolve()}")

    print(
        f"[generate_psi_report] {len(feature_psi)} features evaluated, "
        f"{len(flagged)} flagged (PSI > {threshold})."
    )
    return report
