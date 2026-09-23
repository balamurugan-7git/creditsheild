"""
pipeline.py
===========
Core ML pipeline for CrediShield AI — Home Credit Default Risk.

Covers:
  - Data loading and cleaning
  - Feature engineering column lists (Bucket A / Bucket B separation)
  - Preprocessor construction (OHE + StandardScaler via ColumnTransformer)
  - Train / validation / test splitting
  - XGBoost model training
  - Model evaluation (precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix)
  - SHAP explainability helpers
"""

from __future__ import annotations

import warnings
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import shap
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

# ---------------------------------------------------------------------------
# Bucket B — columns to EXCLUDE from model features
# ---------------------------------------------------------------------------
# These columns represent:
#   (a) Post-approval / post-decision bureau data that would cause target leakage,
#   (b) Identifier columns that carry no predictive signal, or
#   (c) Direct derivatives of the target variable.
#
# Reference: Home Credit Default Risk Kaggle competition feature documentation.
# ---------------------------------------------------------------------------
BUCKET_B_COLUMNS: List[str] = [
    # --- Identifiers ---
    "SK_ID_CURR",
    # --- Direct bureau payment-status columns (post-decision leakage) ---
    "DAYS_CREDIT",               # bureau: days since credit bureau enquiry
    "CREDIT_DAY_OVERDUE",        # bureau: days credit is overdue (leakage)
    "DAYS_CREDIT_ENDDATE",       # bureau: credit end date (post-decision)
    "DAYS_ENDDATE_FACT",         # bureau: actual end date (post-decision)
    "AMT_CREDIT_SUM_OVERDUE",    # bureau: current overdue on credit (leakage)
    "CNT_CREDIT_PROLONG",        # bureau: number of times prolonged
    "DAYS_CREDIT_UPDATE",        # bureau: days since last bureau update
    # --- AMT_ANNUITY can reflect internal bureau contract terms ---
    # Keeping AMT_ANNUITY in bucket A as it's on the application itself;
    # only bureau-version excluded
    # --- Application columns that encode decision outcome implicitly ---
    # (none in standard application_train beyond the above)
]

# ---------------------------------------------------------------------------
# Bucket A — Categorical columns to one-hot encode
# ---------------------------------------------------------------------------
BUCKET_A_CATEGORICAL: List[str] = [
    "NAME_CONTRACT_TYPE",        # Cash loans / Revolving loans
    "CODE_GENDER",               # M / F / XNA
    "FLAG_OWN_CAR",              # Y / N
    "FLAG_OWN_REALTY",           # Y / N
    "NAME_TYPE_SUITE",           # Who accompanied client
    "NAME_INCOME_TYPE",          # Working, State servant, Commercial associate …
    "NAME_EDUCATION_TYPE",       # Secondary / higher education …
    "NAME_FAMILY_STATUS",        # Married, Single/not married …
    "NAME_HOUSING_TYPE",         # House / apartment …
    "OCCUPATION_TYPE",           # Laborers, Core staff …
    "WEEKDAY_APPR_PROCESS_START",# Day of week application started
    "ORGANIZATION_TYPE",         # Type of organization client works for
    "FONDKAPREMONT_MODE",        # Reg apartment — repair fund mode
    "HOUSETYPE_MODE",            # House type mode
    "WALLSMATERIAL_MODE",        # Walls material
    "EMERGENCYSTATE_MODE",       # Emergency state mode
]

# ---------------------------------------------------------------------------
# Bucket A — Numerical columns to standard-scale
# ---------------------------------------------------------------------------
BUCKET_A_NUMERICAL: List[str] = [
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "AMT_GOODS_PRICE",
    "REGION_POPULATION_RELATIVE",
    "DAYS_BIRTH",                # Negative integer — age in days
    "DAYS_EMPLOYED",             # Negative integer (or NaN after cleaning)
    "DAYS_REGISTRATION",
    "DAYS_ID_PUBLISH",
    "OWN_CAR_AGE",
    "CNT_FAM_MEMBERS",
    "CNT_CHILDREN",
    "FLAG_MOBIL",
    "FLAG_EMP_PHONE",
    "FLAG_WORK_PHONE",
    "FLAG_CONT_MOBILE",
    "FLAG_PHONE",
    "FLAG_EMAIL",
    "REGION_RATING_CLIENT",
    "REGION_RATING_CLIENT_W_CITY",
    "HOUR_APPR_PROCESS_START",
    "REG_REGION_NOT_LIVE_REGION",
    "REG_REGION_NOT_WORK_REGION",
    "LIVE_REGION_NOT_WORK_REGION",
    "REG_CITY_NOT_LIVE_CITY",
    "REG_CITY_NOT_WORK_CITY",
    "LIVE_CITY_NOT_WORK_CITY",
    "EXT_SOURCE_1",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3",
    "APARTMENTS_AVG",
    "BASEMENTAREA_AVG",
    "YEARS_BEGINEXPLUATATION_AVG",
    "YEARS_BUILD_AVG",
    "COMMONAREA_AVG",
    "ELEVATORS_AVG",
    "ENTRANCES_AVG",
    "FLOORSMAX_AVG",
    "FLOORSMIN_AVG",
    "LANDAREA_AVG",
    "LIVINGAPARTMENTS_AVG",
    "LIVINGAREA_AVG",
    "NONLIVINGAPARTMENTS_AVG",
    "NONLIVINGAREA_AVG",
    "TOTALAREA_MODE",
    "OBS_30_CNT_SOCIAL_CIRCLE",
    "DEF_30_CNT_SOCIAL_CIRCLE",
    "OBS_60_CNT_SOCIAL_CIRCLE",
    "DEF_60_CNT_SOCIAL_CIRCLE",
    "DAYS_LAST_PHONE_CHANGE",
    "AMT_REQ_CREDIT_BUREAU_HOUR",
    "AMT_REQ_CREDIT_BUREAU_DAY",
    "AMT_REQ_CREDIT_BUREAU_WEEK",
    "AMT_REQ_CREDIT_BUREAU_MON",
    "AMT_REQ_CREDIT_BUREAU_QRT",
    "AMT_REQ_CREDIT_BUREAU_YEAR",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_preprocessor(
    categorical_features: List[str],
    numerical_features: List[str],
) -> ColumnTransformer:
    """
    Build a ColumnTransformer that:
      - One-hot encodes categorical features (drops first to avoid
        multicollinearity, ignores unknown categories at inference time).
      - Standard-scales numerical features (zero mean, unit variance).

    Parameters
    ----------
    categorical_features : list of str
        Column names to be one-hot encoded.
    numerical_features : list of str
        Column names to be standard-scaled.

    Returns
    -------
    ColumnTransformer
        Unfitted sklearn ColumnTransformer ready to be fit/transformed.
    """
    categorical_transformer = OneHotEncoder(
        handle_unknown="ignore",
        sparse_output=False,
        drop="first",           # Avoids dummy-variable trap
    )

    numerical_transformer = StandardScaler()

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", categorical_transformer, categorical_features),
            ("num", numerical_transformer, numerical_features),
        ],
        remainder="drop",       # Silently drop any un-listed columns
        verbose_feature_names_out=True,
    )
    return preprocessor


def load_data(
    train_path: str,
    test_path: str,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load training and test CSV files from disk.

    Parameters
    ----------
    train_path : str
        Absolute or relative path to application_train.csv.
    test_path : str
        Absolute or relative path to application_test.csv.

    Returns
    -------
    (train_df, test_df) : tuple of DataFrames
    """
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    print(f"[load_data] train shape: {train_df.shape}, test shape: {test_df.shape}")
    return train_df, test_df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply standard cleaning steps to a Home Credit dataframe:

    1. Replace the DAYS_EMPLOYED anomaly value (365243) with NaN.
       In the raw dataset, unemployed applicants have DAYS_EMPLOYED=365243
       as a sentinel; this is not a real duration and must be nullified.

    2. Strip leading/trailing whitespace from all object (string) columns.

    3. Fill remaining NaN values in object columns with the string 'Missing'
       so that downstream OHE can handle them without errors.

    Parameters
    ----------
    df : pd.DataFrame
        Raw dataframe (modified in-place on a copy).

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe.
    """
    df = df.copy()

    # 1. DAYS_EMPLOYED anomaly: sentinel 365243 -> NaN
    if "DAYS_EMPLOYED" in df.columns:
        anomaly_mask = df["DAYS_EMPLOYED"] == 365243
        n_anomalies = anomaly_mask.sum()
        df.loc[anomaly_mask, "DAYS_EMPLOYED"] = np.nan
        if n_anomalies > 0:
            print(f"[clean_data] Replaced {n_anomalies} DAYS_EMPLOYED anomalies with NaN.")

    # 2. Strip whitespace from string columns
    str_cols = df.select_dtypes(include=["object"]).columns
    for col in str_cols:
        df[col] = df[col].str.strip()

    # 3. Fill categorical NaN with 'Missing'
    for col in str_cols:
        df[col] = df[col].fillna("Missing")

    return df


def split_data(
    df: pd.DataFrame,
    target_col: str,
    test_size: float = 0.2,
    val_size: float = 0.1,
    random_state: int = 42,
) -> Tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame,
    pd.Series, pd.Series, pd.Series,
]:
    """
    Perform a stratified 3-way split: train / validation / test.

    The split is done in two steps:
      1. Split off `test_size` fraction as the held-out test set.
      2. From the remainder, split off `val_size / (1 - test_size)` as
         the validation set so that the final validation set is approximately
         `val_size` of the original data.

    Parameters
    ----------
    df : pd.DataFrame
        Full cleaned dataframe including target column.
    target_col : str
        Name of the binary target column (0/1).
    test_size : float
        Fraction of total data reserved for the test set.
    val_size : float
        Fraction of total data reserved for the validation set.
    random_state : int
        Random seed for reproducibility.

    Returns
    -------
    X_train, X_val, X_test, y_train, y_val, y_test
    """
    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Step 1: carve out test set
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    # Step 2: carve out validation set from the remainder
    # Adjust val fraction relative to the remaining data
    adjusted_val_size = val_size / (1.0 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp,
        test_size=adjusted_val_size,
        random_state=random_state,
        stratify=y_temp,
    )

    print(
        f"[split_data] train: {len(X_train)}, val: {len(X_val)}, test: {len(X_test)}"
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def get_feature_lists(
    df: pd.DataFrame,
    bucket_b_cols: List[str],
    target_col: str,
) -> Tuple[List[str], List[str]]:
    """
    Derive the actual categorical and numerical feature lists present in `df`,
    excluding Bucket B columns and the target column.

    Uses the global BUCKET_A_CATEGORICAL and BUCKET_A_NUMERICAL as candidate
    lists, then filters to only those actually present in the dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        The dataframe to inspect (post-cleaning, pre-split).
    bucket_b_cols : list of str
        Columns to exclude (target leakage / identifiers).
    target_col : str
        Name of the target column to exclude.

    Returns
    -------
    (categorical_cols, numerical_cols) : tuple of lists
        Features to pass to build_preprocessor().
    """
    exclude = set(bucket_b_cols) | {target_col}
    available_cols = set(df.columns) - exclude

    categorical_cols = [c for c in BUCKET_A_CATEGORICAL if c in available_cols]
    numerical_cols = [c for c in BUCKET_A_NUMERICAL if c in available_cols]

    print(
        f"[get_feature_lists] categorical: {len(categorical_cols)}, "
        f"numerical: {len(numerical_cols)}"
    )
    return categorical_cols, numerical_cols


def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    scale_pos_weight: float,
    params: Optional[Dict] = None,
) -> XGBClassifier:
    """
    Train an XGBoost binary classifier with class-weight balancing.

    The `scale_pos_weight` parameter compensates for the class imbalance
    (typically ~91% negative, ~9% positive in Home Credit data):
        scale_pos_weight = count(negative) / count(positive)

    Parameters
    ----------
    X_train : pd.DataFrame
        Transformed (preprocessed) training features.
    y_train : pd.Series
        Binary training labels.
    scale_pos_weight : float
        Weight ratio to apply to the positive class.
    params : dict, optional
        Override default XGBoost hyperparameters. Any key not provided
        will fall back to the defaults below.

    Returns
    -------
    XGBClassifier
        Fitted XGBoost model.
    """
    default_params: Dict = {
        "n_estimators": 500,
        "max_depth": 6,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 5,
        "gamma": 1.0,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "scale_pos_weight": scale_pos_weight,
        "objective": "binary:logistic",
        "eval_metric": "aucpr",
        "tree_method": "hist",
        "random_state": 42,
        "n_jobs": -1,
        "early_stopping_rounds": 50,
    }

    if params:
        default_params.update(params)

    model = XGBClassifier(**default_params)
    model.fit(X_train, y_train, verbose=50)
    print(f"[train_model] Training complete. Best iteration: {model.best_iteration}")
    return model


def evaluate_model(
    model: XGBClassifier,
    preprocessor: ColumnTransformer,
    X: pd.DataFrame,
    y: pd.Series,
    label: str = "Test",
) -> Dict:
    """
    Evaluate a fitted model + preprocessor on a given dataset split.

    Metrics computed:
      - Precision, Recall, F1 (threshold = 0.5)
      - ROC-AUC
      - PR-AUC (Average Precision Score)
      - Confusion Matrix

    Parameters
    ----------
    model : XGBClassifier
        Fitted XGBoost model.
    preprocessor : ColumnTransformer
        Fitted preprocessor.
    X : pd.DataFrame
        Raw (un-transformed) feature dataframe.
    y : pd.Series
        True binary labels.
    label : str
        Display label for the printed table.

    Returns
    -------
    dict
        Keys: precision, recall, f1, roc_auc, pr_auc, confusion_matrix
    """
    X_transformed = preprocessor.transform(X)
    y_prob = model.predict_proba(X_transformed)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    metrics = {
        "precision": float(precision_score(y, y_pred, zero_division=0)),
        "recall": float(recall_score(y, y_pred, zero_division=0)),
        "f1": float(f1_score(y, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, y_prob)),
        "pr_auc": float(average_precision_score(y, y_prob)),
        "confusion_matrix": confusion_matrix(y, y_pred).tolist(),
    }

    # Pretty-print formatted table
    border = "=" * 45
    print(f"\n{border}")
    print(f"  Evaluation — {label}")
    print(border)
    print(f"  {'Metric':<20} {'Value':>10}")
    print("-" * 45)
    for key in ("precision", "recall", "f1", "roc_auc", "pr_auc"):
        print(f"  {key:<20} {metrics[key]:>10.4f}")
    print("-" * 45)
    cm = metrics["confusion_matrix"]
    print(f"  Confusion Matrix:")
    print(f"    TN={cm[0][0]:>6}   FP={cm[0][1]:>6}")
    print(f"    FN={cm[1][0]:>6}   TP={cm[1][1]:>6}")
    print(border)

    return metrics


def compute_shap_values(
    model: XGBClassifier,
    X_transformed: np.ndarray,
    feature_names: List[str],
) -> Tuple[np.ndarray, float]:
    """
    Compute SHAP values for a transformed feature array using TreeExplainer.

    Parameters
    ----------
    model : XGBClassifier
        Fitted XGBoost model.
    X_transformed : np.ndarray
        Preprocessed feature matrix (output of preprocessor.transform()).
    feature_names : list of str
        Feature names corresponding to columns of X_transformed.

    Returns
    -------
    (shap_values, expected_value) : tuple
        shap_values  — array of shape (n_samples, n_features)
        expected_value — float baseline (log-odds of the model)
    """
    explainer = shap.TreeExplainer(model)

    # Wrap in DataFrame for named features (optional but good practice)
    X_df = pd.DataFrame(X_transformed, columns=feature_names)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        shap_values = explainer.shap_values(X_df)

    expected_value = float(explainer.expected_value)
    print(
        f"[compute_shap_values] SHAP computed for {X_transformed.shape[0]} samples, "
        f"{X_transformed.shape[1]} features. Base value: {expected_value:.4f}"
    )
    return shap_values, expected_value


def get_top_shap_factors(
    shap_values_row: np.ndarray,
    feature_names: List[str],
    n: int = 5,
) -> List[Dict]:
    """
    Return the top-N most influential features for a single prediction,
    based on absolute SHAP values.

    Parameters
    ----------
    shap_values_row : np.ndarray
        1-D array of SHAP values for one sample (length == n_features).
    feature_names : list of str
        Feature names corresponding to each SHAP value.
    n : int
        Number of top factors to return (default 5).

    Returns
    -------
    list of dict
        Each dict has keys:
          - 'feature'    : str  — feature name
          - 'shap_value' : float — raw SHAP value (signed)
          - 'direction'  : str  — 'increases_risk' | 'decreases_risk'
    """
    if len(shap_values_row) != len(feature_names):
        raise ValueError(
            f"shap_values_row length ({len(shap_values_row)}) must match "
            f"feature_names length ({len(feature_names)})."
        )

    # Sort by absolute SHAP value descending
    indices = np.argsort(np.abs(shap_values_row))[::-1][:n]

    factors = []
    for idx in indices:
        sv = float(shap_values_row[idx])
        factors.append(
            {
                "feature": feature_names[idx],
                "shap_value": sv,
                "direction": "increases_risk" if sv > 0 else "decreases_risk",
            }
        )
    return factors
