"""
thresholds.py
=============
Decision threshold utilities for the CrediShield AI risk scoring engine.

The model outputs a continuous probability [0, 1] for default risk.
Rather than applying a single 0.5 threshold, CrediShield uses a
three-band decision policy:

    probability < low_threshold   →  'approved'
    low_threshold ≤ prob ≤ high_threshold  →  'manual_review'
    probability > high_threshold  →  'rejected'

This module provides tools to:
  - Find optimal thresholds via cost-based grid sweep
  - Find the Youden's-J optimal threshold (maximises sensitivity + specificity)
  - Apply the three-band policy to a single probability
  - Persist and reload threshold configuration as JSON
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_curve,
)


def cost_based_sweep(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    cost_fn_ratio: float = 5.0,
    n_steps: int = 100,
) -> Dict:
    """
    Grid-search over (low_threshold, high_threshold) pairs to minimise a
    business-defined cost function:

        total_cost = cost_fn_ratio * false_negatives + false_positives

    The rationale: missing a defaulter (false negative) is typically
    5× more costly than incorrectly flagging a good payer (false positive).

    The search space is:
      low_threshold  ∈ [0.05, 0.50]  (step = 1/n_steps)
      high_threshold ∈ [low+step, 0.95]

    Parameters
    ----------
    y_true : np.ndarray
        True binary labels (0 / 1).
    y_prob : np.ndarray
        Predicted probabilities for the positive class.
    cost_fn_ratio : float
        Multiplier for false negatives relative to false positives.
        Default 5.0 (missing a defaulter costs 5× more).
    n_steps : int
        Number of evenly-spaced steps across [0, 1] for the sweep.

    Returns
    -------
    dict with keys:
      low_threshold      : float — optimal lower decision boundary
      high_threshold     : float — optimal upper decision boundary
      cost_fn_ratio      : float — the ratio used
      total_cost         : float — minimum cost achieved
      metrics_at_thresholds : dict — precision, recall, f1 at each band boundary
    """
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)

    step = 1.0 / n_steps
    thresholds = np.arange(step, 1.0, step)

    best_cost = np.inf
    best_low = 0.3
    best_high = 0.7

    for low in thresholds:
        for high in thresholds:
            if high <= low:
                continue  # Must maintain low < high

            # Classify: anything ≥ high_threshold is 'rejected' (predicted positive)
            # For cost-metric purposes we compare against hard-threshold at `high`
            y_pred_high = (y_prob >= high).astype(int)
            tn, fp, fn, tp = confusion_matrix(y_true, y_pred_high, labels=[0, 1]).ravel()

            cost = cost_fn_ratio * fn + fp
            if cost < best_cost:
                best_cost = cost
                best_low = float(low)
                best_high = float(high)

    # Compute detailed metrics at the best thresholds
    y_pred_low = (y_prob >= best_low).astype(int)
    y_pred_high = (y_prob >= best_high).astype(int)

    metrics_at_thresholds = {
        "at_low_threshold": {
            "precision": float(precision_score(y_true, y_pred_low, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred_low, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred_low, zero_division=0)),
        },
        "at_high_threshold": {
            "precision": float(precision_score(y_true, y_pred_high, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred_high, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred_high, zero_division=0)),
        },
    }

    result = {
        "low_threshold": best_low,
        "high_threshold": best_high,
        "cost_fn_ratio": cost_fn_ratio,
        "total_cost": float(best_cost),
        "metrics_at_thresholds": metrics_at_thresholds,
    }

    print(
        f"[cost_based_sweep] Best: low={best_low:.3f}, high={best_high:.3f}, "
        f"cost={best_cost:.1f} (cost_fn_ratio={cost_fn_ratio})"
    )
    return result


def youdens_j_threshold(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> float:
    """
    Compute the optimal decision threshold using Youden's J statistic:

        J = Sensitivity + Specificity - 1
          = TPR - FPR

    The threshold that maximises J is the point on the ROC curve furthest
    from the random-chance diagonal.

    Parameters
    ----------
    y_true : np.ndarray
        True binary labels.
    y_prob : np.ndarray
        Predicted probabilities for the positive class.

    Returns
    -------
    float
        Optimal threshold value in [0, 1].
    """
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)

    fpr, tpr, thresholds = roc_curve(y_true, y_prob)
    j_scores = tpr - fpr                       # Youden's J
    best_idx = int(np.argmax(j_scores))
    optimal_threshold = float(thresholds[best_idx])

    # Clamp to [0, 1] in case of floating-point edge cases
    optimal_threshold = max(0.0, min(1.0, optimal_threshold))

    print(
        f"[youdens_j_threshold] Optimal threshold: {optimal_threshold:.4f} "
        f"(J={j_scores[best_idx]:.4f})"
    )
    return optimal_threshold


def apply_threshold(
    probability: float,
    low_threshold: float,
    high_threshold: float,
) -> str:
    """
    Map a single default-risk probability to a three-band decision.

    Decision bands:
      probability < low_threshold             → 'approved'
      low_threshold ≤ probability ≤ high_threshold → 'manual_review'
      probability > high_threshold            → 'rejected'

    Parameters
    ----------
    probability : float
        Model-predicted default probability in [0, 1].
    low_threshold : float
        Lower boundary separating 'approved' from 'manual_review'.
    high_threshold : float
        Upper boundary separating 'manual_review' from 'rejected'.

    Returns
    -------
    str
        One of: 'approved', 'manual_review', 'rejected'.

    Raises
    ------
    ValueError
        If low_threshold >= high_threshold or probability is out of range.
    """
    if not (0.0 <= probability <= 1.0):
        raise ValueError(f"probability must be in [0, 1], got {probability}")
    if low_threshold >= high_threshold:
        raise ValueError(
            f"low_threshold ({low_threshold}) must be < high_threshold ({high_threshold})"
        )

    if probability < low_threshold:
        return "approved"
    elif probability > high_threshold:
        return "rejected"
    else:
        return "manual_review"


def save_thresholds(thresholds_dict: Dict, path: str) -> None:
    """
    Persist a thresholds dictionary to a JSON file.

    Parameters
    ----------
    thresholds_dict : dict
        Dictionary containing at least 'low_threshold' and 'high_threshold'.
        Typically the output of cost_based_sweep() or a manually constructed dict.
    path : str
        File path to write (parent directories created if they don't exist).
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(thresholds_dict, fh, indent=2)

    print(f"[save_thresholds] Saved to {output_path.resolve()}")


def load_thresholds(path: str) -> Dict:
    """
    Load a thresholds dictionary from a JSON file.

    Parameters
    ----------
    path : str
        Path to the JSON file previously saved by save_thresholds().

    Returns
    -------
    dict
        The deserialized thresholds dictionary.

    Raises
    ------
    FileNotFoundError
        If the JSON file does not exist at the given path.
    """
    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(f"Thresholds file not found: {input_path.resolve()}")

    with input_path.open("r", encoding="utf-8") as fh:
        thresholds_dict = json.load(fh)

    print(f"[load_thresholds] Loaded from {input_path.resolve()}")
    return thresholds_dict
