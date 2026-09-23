"""
app/services/prediction.py
--------------------------
ML prediction service for CrediShield.

Architecture
------------
- ``ModelService``:  wraps a joblib pipeline, exposes ``predict()``.
- ``load_model_service()``:  called once at application startup.
- ``get_model_service()``:  FastAPI dependency – raises 503 if model not ready.

Expected joblib artifact structure
-----------------------------------
The saved artefact is a dict::

    {
        "preprocessor": sklearn.pipeline.Pipeline,   # fit ColumnTransformer / Pipeline
        "model":        xgboost.XGBClassifier,       # or any sklearn-compatible estimator
        "feature_names": list[str],                  # feature names in the correct order
        "version": str,                              # e.g. "v1"
    }

If the artefact is a plain sklearn Pipeline (preprocessor + classifier steps),
the service falls back to treating the whole object as the pipeline and reads
``feature_names_in_`` from the Pipeline's first step.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..schemas import PredictionResult, ShapFactor, to_display_name
from . import policy as policy_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
model_service: "ModelService | None" = None


# ---------------------------------------------------------------------------
# DAYS_EMPLOYED anomaly value used in Home Credit dataset
# ---------------------------------------------------------------------------
_DAYS_EMPLOYED_ANOMALY = 365243


class ModelService:
    """
    Wraps a trained ML pipeline and provides a ``predict`` method that returns
    a structured ``PredictionResult`` including SHAP-based explanations.
    """

    def __init__(self, model_path: str, meta_path: str) -> None:
        """
        Load the joblib artefact and (optionally) the JSON metadata file.

        Parameters
        ----------
        model_path:
            Absolute or relative path to the ``.joblib`` artefact.
        meta_path:
            Absolute or relative path to the ``_meta.json`` metadata file.
        """
        import sys
        import joblib

        backend_dir = Path(__file__).resolve().parent.parent.parent
        root_dir = backend_dir.parent
        ml_dir = root_dir / "ml"
        for p in (root_dir, ml_dir, backend_dir):
            if p.exists() and str(p) not in sys.path:
                sys.path.insert(0, str(p))

        artefact_path = Path(model_path)
        if not artefact_path.exists():
            for alt in (
                ml_dir / "artifacts" / Path(model_path).name,
                root_dir / "ml" / "artifacts" / Path(model_path).name,
                backend_dir.parent / "ml" / "artifacts" / Path(model_path).name,
            ):
                if alt.exists():
                    artefact_path = alt
                    break
            else:
                raise FileNotFoundError(
                    f"Model artefact not found at '{artefact_path.resolve()}'."
                )

        artefact = joblib.load(artefact_path)

        # Support ModelArtifact dataclass, dict, or plain Pipeline
        if hasattr(artefact, "model") and hasattr(artefact, "preprocessor"):
            self._preprocessor = artefact.preprocessor
            self._model = artefact.model
            self._categorical_features: list[str] = getattr(artefact, "categorical_features", []) or []
            self._numerical_features: list[str] = getattr(artefact, "numerical_features", []) or []
            self._raw_features: list[str] = self._categorical_features + self._numerical_features
            self._feature_names: list[str] = getattr(artefact, "feature_names", []) or []
            self._version: str = getattr(artefact, "model_version", "v1.0.0")
        elif isinstance(artefact, dict):
            self._preprocessor = artefact.get("preprocessor")
            self._model = artefact["model"]
            self._categorical_features = artefact.get("categorical_features", []) or []
            self._numerical_features = artefact.get("numerical_features", []) or []
            self._raw_features = self._categorical_features + self._numerical_features
            self._feature_names: list[str] = artefact.get("feature_names", [])
            self._version: str = artefact.get("version", "unknown")
        else:
            # Assume the artefact IS the full pipeline
            self._preprocessor = None
            self._model = artefact
            self._categorical_features = []
            self._numerical_features = []
            self._raw_features = []
            self._version = "unknown"
            # Try to introspect feature names from sklearn pipeline metadata
            try:
                self._feature_names = list(artefact.feature_names_in_)
            except AttributeError:
                self._feature_names = []

        # Override version from metadata file if available
        meta_file = Path(meta_path)
        if not meta_file.exists():
            for alt in (
                ml_dir / "artifacts" / Path(meta_path).name,
                root_dir / "ml" / "artifacts" / Path(meta_path).name,
                backend_dir.parent / "ml" / "artifacts" / Path(meta_path).name,
            ):
                if alt.exists():
                    meta_file = alt
                    break

        if meta_file.exists():
            try:
                with meta_file.open("r", encoding="utf-8") as fh:
                    meta = json.load(fh)
                self._version = meta.get("version", self._version)
                if not self._feature_names:
                    self._feature_names = meta.get("feature_names", [])
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not read meta file: %s", exc)

        logger.info(
            "ModelService loaded: version=%s, features=%d",
            self._version,
            len(self._feature_names),
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def is_loaded(self) -> bool:
        """Return True – instance only exists when successfully loaded."""
        return True

    def get_version(self) -> str:
        """Return the model version string."""
        return self._version

    def predict(self, input_data: dict[str, Any]) -> PredictionResult:
        """
        Score a single loan application.

        Parameters
        ----------
        input_data:
            Raw feature dict matching ``LoanApplicationInput`` field names.

        Returns
        -------
        PredictionResult
            Contains probability, decision, and top-5 SHAP factors.
        """
        row = dict(input_data)

        # 1. Prepare raw input DataFrame and transform
        if self._preprocessor is not None and self._raw_features:
            data = {}
            for col in self._categorical_features:
                val = row.get(col)
                if val is None or pd.isna(val) or val == "" or str(val).lower() == "nan":
                    data[col] = "Missing"
                else:
                    data[col] = str(val).strip()

            for col in self._numerical_features:
                val = row.get(col)
                if val is None or pd.isna(val) or val == "":
                    data[col] = np.nan
                elif col == "DAYS_EMPLOYED" and float(val) == _DAYS_EMPLOYED_ANOMALY:
                    data[col] = np.nan
                else:
                    try:
                        data[col] = float(val)
                    except (ValueError, TypeError):
                        data[col] = np.nan

            df = pd.DataFrame([data])
            df = df[self._raw_features]
            try:
                X_transformed = self._preprocessor.transform(df)
            except Exception as exc:
                logger.error("Preprocessing failed: %s", exc, exc_info=True)
                raise RuntimeError(f"Preprocessing error: {exc}") from exc
        else:
            df = pd.DataFrame([row])
            df = self._preprocess(df)
            if self._feature_names:
                for col in self._feature_names:
                    if col not in df.columns:
                        df[col] = np.nan
                df = df[self._feature_names]

            try:
                if self._preprocessor is not None:
                    X_transformed = self._preprocessor.transform(df)
                else:
                    X_transformed = df
            except Exception as exc:
                logger.error("Preprocessing failed: %s", exc, exc_info=True)
                raise RuntimeError(f"Preprocessing error: {exc}") from exc

        # 2. Run model inference
        try:
            proba_array = self._model.predict_proba(X_transformed)
            probability = float(proba_array[0, 1])  # P(default=1)
        except Exception as exc:
            logger.error("Model inference failed: %s", exc, exc_info=True)
            raise RuntimeError(f"Model inference error: {exc}") from exc

        # 3. Classify with policy DTI constraints
        decision = policy_service.classify(probability, input_data=row)

        # 4. Compute SHAP values
        shap_factors = self._compute_shap(X_transformed, probability)

        return PredictionResult(
            probability=probability,
            decision=decision,
            shap_top_factors=shap_factors,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _preprocess(df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply Home-Credit-specific feature engineering before the sklearn pipeline.

        Steps
        -----
        - Flag and zero-out the DAYS_EMPLOYED anomaly (365243).
        - Fill object/string NaN values with the sentinel string 'Missing'
          (many categorical imputers expect this).
        """
        df = df.copy()

        # DAYS_EMPLOYED anomaly handling
        if "DAYS_EMPLOYED" in df.columns:
            anomaly_mask = df["DAYS_EMPLOYED"] == _DAYS_EMPLOYED_ANOMALY
            df["DAYS_EMPLOYED_ANOM"] = anomaly_mask.astype(int)
            df.loc[anomaly_mask, "DAYS_EMPLOYED"] = np.nan

        # Fill categorical NaN with sentinel string
        cat_cols = df.select_dtypes(include=["object"]).columns
        df[cat_cols] = df[cat_cols].fillna("Missing")

        return df

    def _compute_shap(
        self, X_transformed: Any, probability: float
    ) -> list[ShapFactor]:
        """
        Compute SHAP values for *X_transformed* and return the top-5 factors.

        Falls back to an empty list if SHAP computation fails (e.g. model type
        not supported by TreeExplainer).
        """
        try:
            import shap  # lazy import

            # Use TreeExplainer for tree-based models (XGBoost, LightGBM, etc.)
            # If the model is wrapped in a pipeline step, unwrap it.
            raw_model = self._model
            if hasattr(raw_model, "named_steps"):
                # It's a sklearn Pipeline – grab the last step
                *_, last_step = raw_model.named_steps.values()
                raw_model = last_step

            explainer = shap.TreeExplainer(raw_model)
            shap_values = explainer.shap_values(X_transformed)

            # For binary classifiers SHAP may return list[ndarray] (one per class)
            if isinstance(shap_values, list):
                sv = shap_values[1]  # class 1 (default)
            else:
                sv = shap_values

            sv_row = np.array(sv).flatten()

            # Build feature name list for the transformed representation
            if self._preprocessor is not None and hasattr(
                self._preprocessor, "get_feature_names_out"
            ):
                try:
                    feat_names = list(self._preprocessor.get_feature_names_out())
                except Exception:
                    feat_names = [f"feature_{i}" for i in range(len(sv_row))]
            elif self._feature_names and len(self._feature_names) == len(sv_row):
                feat_names = self._feature_names
            else:
                feat_names = [f"feature_{i}" for i in range(len(sv_row))]

            # Rank by absolute SHAP value, take top 5
            top_indices = np.argsort(np.abs(sv_row))[::-1][:5]
            factors: list[ShapFactor] = []
            for idx in top_indices:
                raw_name = feat_names[idx] if idx < len(feat_names) else f"feature_{idx}"
                # Strip sklearn OHE prefix if present (e.g. "cat__CODE_GENDER_M" -> "CODE_GENDER")
                clean_name = _strip_transformer_prefix(raw_name)
                sv_val = float(sv_row[idx])
                factors.append(
                    ShapFactor(
                        feature=clean_name,
                        shap_value=sv_val,
                        direction="increases_risk" if sv_val > 0 else "decreases_risk",
                        display_name=to_display_name(clean_name),
                    )
                )
            return factors

        except Exception as exc:
            logger.warning("SHAP computation failed: %s", exc)
            return []


def _strip_transformer_prefix(name: str) -> str:
    """
    Remove sklearn ColumnTransformer / Pipeline prefixes.

    Examples
    --------
    ``"cat__CODE_GENDER_M"`` → ``"CODE_GENDER"``
    ``"num__EXT_SOURCE_2"``  → ``"EXT_SOURCE_2"``
    ``"remainder__DAYS_BIRTH"`` → ``"DAYS_BIRTH"``
    """
    if "__" in name:
        # Drop everything up to and including the last "__"
        name = name.split("__", 1)[-1]
    # Also strip one-hot-encoded suffix (e.g. "_M", "_F") for known binary features
    # Keep the base feature name only
    for suffix in ("_Y", "_N", "_M", "_F", "_XNA"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    return name


# ---------------------------------------------------------------------------
# Module-level initialiser and FastAPI dependency
# ---------------------------------------------------------------------------

def load_model_service(model_path: str, meta_path: str) -> None:
    """
    Initialise the module-level ``model_service`` singleton.

    Called once during application startup (lifespan).  Failures are logged
    but do not crash the server – instead ``model_service`` remains ``None``
    and the ``/api/applications/`` endpoint will return 503.
    """
    global model_service
    try:
        model_service = ModelService(model_path=model_path, meta_path=meta_path)
        logger.info("Model service initialised successfully (version=%s).", model_service.get_version())
    except FileNotFoundError as exc:
        logger.warning(
            "Model file not found – prediction endpoints will return 503. (%s)", exc
        )
        model_service = None
    except Exception as exc:
        logger.error("Failed to initialise ModelService: %s", exc, exc_info=True)
        model_service = None


def get_model_service() -> ModelService:
    """
    FastAPI dependency that returns the loaded ``ModelService``.

    Raises
    ------
    HTTPException(503)
        When the model has not been loaded yet.
    """
    from fastapi import HTTPException, status  # local import avoids circular deps

    if model_service is None or not model_service.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "ML model is not loaded. "
                "Ensure the model artefact exists and the service has started correctly."
            ),
        )
    return model_service
