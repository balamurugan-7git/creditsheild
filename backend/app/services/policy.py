"""
app/services/policy.py
----------------------
Decision policy: maps a raw default probability to a categorical decision.

Thresholds are loaded from ``policy/thresholds.json`` at module import time
and can be hot-reloaded at runtime via ``reload_thresholds()``.

Default thresholds (used when the file is absent):
    low_threshold  = 0.35  → P < 0.35  ⟹ approved
    high_threshold = 0.65  → P > 0.65  ⟹ rejected
    otherwise              ⟹ manual_review
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from ..config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------
_DEFAULTS: dict = {
    "low_threshold": 0.35,
    "high_threshold": 0.65,
    "cost_ratio": 5.0,
    "description": "Default thresholds (policy file not found).",
    "model_version": "unknown",
}

_thresholds: dict = dict(_DEFAULTS)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------
def _load_from_file() -> dict:
    """Read and parse the policy JSON file, returning the config dict."""
    policy_path = Path(settings.policy_path)
    if not policy_path.exists():
        for alt in (
            Path(__file__).resolve().parent.parent.parent / "policy" / "thresholds.json",
            Path("backend/policy/thresholds.json"),
            Path("policy/thresholds.json"),
            Path("../backend/policy/thresholds.json"),
        ):
            if alt.exists():
                policy_path = alt
                break
        else:
            logger.warning(
                "Policy file not found at '%s'. Using default thresholds.", policy_path
            )
            return dict(_DEFAULTS)
    try:
        with policy_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        logger.info(
            "Loaded policy thresholds from '%s': low=%.2f high=%.2f",
            policy_path,
            data.get("low_threshold", _DEFAULTS["low_threshold"]),
            data.get("high_threshold", _DEFAULTS["high_threshold"]),
        )
        return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to parse policy file: %s. Using defaults.", exc)
        return dict(_DEFAULTS)


# Eagerly load at import time so the first request is fast.
_thresholds = _load_from_file()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def classify(probability: float, input_data: dict | None = None) -> str:
    """
    Map a default probability to a categorical lending decision,
    enforcing institutional Debt-to-Income (DTI) and minimum income policy rules.

    Parameters
    ----------
    probability:
        Model output P(default) in [0, 1].
    input_data:
        Optional raw feature dict containing AMT_INCOME_TOTAL and AMT_CREDIT.

    Returns
    -------
    str
        One of ``'approved'``, ``'manual_review'``, or ``'rejected'``.
    """
    if input_data:
        try:
            income = float(input_data.get("AMT_INCOME_TOTAL") or 0.0)
            credit = float(input_data.get("AMT_CREDIT") or 0.0)
            # Rule 1: Extreme Debt-to-Income (> 12x annual income) or sub-living income
            if (income > 0 and credit / income > 12.0) or (0 < income < 12000):
                return "rejected"
            # Rule 2: Elevated Debt-to-Income (> 6x annual income)
            if income > 0 and credit / income > 6.0:
                return "manual_review"
        except (ValueError, TypeError):
            pass

    low: float = _thresholds.get("low_threshold", _DEFAULTS["low_threshold"])
    high: float = _thresholds.get("high_threshold", _DEFAULTS["high_threshold"])

    if probability < low:
        return "approved"
    if probability > high:
        return "rejected"
    return "manual_review"


def get_thresholds() -> dict:
    """Return the currently active threshold configuration as a dict."""
    return dict(_thresholds)


def reload_thresholds() -> dict:
    """
    Re-read the policy file from disk and update the in-process state.

    Useful for hot-reloading thresholds without restarting the server.

    Returns
    -------
    dict
        The newly loaded threshold configuration.
    """
    global _thresholds
    _thresholds = _load_from_file()
    return dict(_thresholds)
