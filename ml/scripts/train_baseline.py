"""ml/scripts/train_baseline.py
Generates and serializes the baseline credit scoring model artifact for CrediShield AI.
Uses application_train.csv if available in data/raw/, or generates a calibrated synthetic dataset.
Saves model_v1.joblib and model_v1_meta.json to ml/artifacts/.
"""

import os
import sys
from pathlib import Path

# Add project root and ml root to path
ML_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ML_ROOT))

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score

from src.pipeline import clean_data, build_preprocessor, split_data, get_feature_lists
from src.thresholds import cost_based_sweep, save_thresholds
from src.serialize import ModelArtifact, save_artifact


def main():
    print("=" * 60)
    print("CrediShield AI — Baseline Model Training & Serialization")
    print("=" * 60)

    raw_path = ML_ROOT / "data" / "raw" / "application_train.csv"
    if raw_path.exists():
        print(f"Loading raw Kaggle Home Credit dataset from: {raw_path}")
        df = pd.read_csv(raw_path)
    else:
        print("Raw Kaggle dataset not found in ml/data/raw/. Generating synthetic development dataset...")
        np.random.seed(42)
        n = 15000
        inc = np.random.exponential(150000, size=n) + 5000
        cred = np.random.exponential(450000, size=n) + 30000
        ann = cred * np.random.uniform(0.04, 0.12, size=n)
        ext1 = np.random.uniform(0.1, 0.9, size=n)
        ext2 = np.random.uniform(0.1, 0.9, size=n)
        ext3 = np.random.uniform(0.1, 0.9, size=n)

        # Realistic default relationship:
        # High Debt-to-Income (DTI), high annuity burden, low income, and poor credit scores drive defaults
        dti = cred / np.maximum(inc, 1.0)
        annuity_burden = ann / np.maximum(inc, 1.0)
        score_deficit = (1.0 - ext2) + (1.0 - ext3) + (1.0 - ext1)

        risk_score = (
            3.5 * (dti > 4.0).astype(float)
            + 6.0 * (dti > 8.0).astype(float)
            + 4.0 * (inc < 35000).astype(float)
            + 3.0 * (annuity_burden > 0.35).astype(float)
            + 2.5 * score_deficit
            - 2.0 * (inc > 300000).astype(float)
            + np.random.normal(0, 1.0, size=n)
        )
        # Calibrate to ~8.5% default rate
        cutoff = np.percentile(risk_score, 91.5)
        target = (risk_score >= cutoff).astype(int)

        df = pd.DataFrame({
            "SK_ID_CURR": np.arange(100000, 100000 + n),
            "TARGET": target,
            "CODE_GENDER": np.random.choice(["M", "F"], size=n),
            "FLAG_OWN_CAR": np.random.choice(["Y", "N"], size=n),
            "FLAG_OWN_REALTY": np.random.choice(["Y", "N"], size=n),
            "CNT_CHILDREN": np.random.poisson(0.5, size=n),
            "AMT_INCOME_TOTAL": inc,
            "AMT_CREDIT": cred,
            "AMT_ANNUITY": ann,
            "AMT_GOODS_PRICE": cred * np.random.uniform(0.9, 1.1, size=n),
            "NAME_INCOME_TYPE": np.random.choice(["Working", "Commercial associate", "Pensioner", "State servant"], size=n),
            "NAME_EDUCATION_TYPE": np.random.choice(["Higher education", "Secondary / secondary special"], size=n),
            "NAME_FAMILY_STATUS": np.random.choice(["Married", "Single / not married", "Civil marriage"], size=n),
            "NAME_HOUSING_TYPE": np.random.choice(["House / apartment", "Rented apartment", "With parents"], size=n),
            "DAYS_BIRTH": -np.random.randint(7500, 25000, size=n),
            "DAYS_EMPLOYED": -np.random.randint(100, 10000, size=n),
            "DAYS_REGISTRATION": -np.random.randint(1000, 8000, size=n),
            "DAYS_ID_PUBLISH": -np.random.randint(500, 5000, size=n),
            "NAME_CONTRACT_TYPE": np.random.choice(["Cash loans", "Revolving loans"], size=n),
            "EXT_SOURCE_1": ext1,
            "EXT_SOURCE_2": ext2,
            "EXT_SOURCE_3": ext3,
            "ORGANIZATION_TYPE": np.random.choice(["Business Entity Type 3", "Self-employed", "Other"], size=n),
            "OCCUPATION_TYPE": np.random.choice(["Laborers", "Core staff", "Managers"], size=n),
            "OWN_CAR_AGE": np.random.choice([np.nan, 3.0, 7.0, 12.0], size=n),
            "CNT_FAM_MEMBERS": np.random.choice([1.0, 2.0, 3.0, 4.0], size=n),
        })

    print(f"Dataset shape: {df.shape[0]:,} rows, {df.shape[1]} columns. Default rate: {df['TARGET'].mean()*100:.2f}%")

    df_clean = clean_data(df)
    feature_cols = [c for c in df_clean.columns if c not in ["TARGET", "SK_ID_CURR"]]
    cat_cols = df_clean[feature_cols].select_dtypes(include=["object", "category"]).columns.tolist()
    num_cols = df_clean[feature_cols].select_dtypes(include=[np.number]).columns.tolist()

    X_train, X_val, X_test, y_train, y_val, y_test = split_data(df_clean, target_col="TARGET", test_size=0.15, val_size=0.15)

    print("Building ColumnTransformer preprocessor...")
    preprocessor = build_preprocessor(categorical_features=cat_cols, numerical_features=num_cols)
    X_train_trans = preprocessor.fit_transform(X_train[cat_cols + num_cols])
    X_val_trans = preprocessor.transform(X_val[cat_cols + num_cols])
    X_test_trans = preprocessor.transform(X_test[cat_cols + num_cols])

    feature_names = list(preprocessor.get_feature_names_out())
    print(f"Features transformed: {len(feature_names)} columns after encoding.")

    print("Training gradient boosting classifier with class weighting...")
    # Calculate class weighting for 8% default rate
    pos_weight = float((y_train == 0).sum() / max(1, (y_train == 1).sum()))
    
    # Use HistGradientBoosting or XGBoost if available
    try:
        from xgboost import XGBClassifier
        model = XGBClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.05,
            scale_pos_weight=pos_weight,
            random_state=42,
            eval_metric="auc",
            n_jobs=-1,
        )
    except ImportError:
        from sklearn.ensemble import HistGradientBoostingClassifier
        model = HistGradientBoostingClassifier(
            max_iter=150,
            max_depth=5,
            learning_rate=0.05,
            class_weight="balanced",
            random_state=42,
        )

    model.fit(X_train_trans, y_train)

    y_test_probs = model.predict_proba(X_test_trans)[:, 1]
    roc_auc = float(roc_auc_score(y_test, y_test_probs))
    print(f"Untouched Test Set ROC-AUC: {roc_auc:.4f}")

    y_val_probs = model.predict_proba(X_val_trans)[:, 1]
    thresholds = cost_based_sweep(y_val, y_val_probs, cost_fn_ratio=5.0)
    print(f"Cost-based thresholds: Low={thresholds['low_threshold']:.4f}, High={thresholds['high_threshold']:.4f}")

    artifacts_dir = ML_ROOT / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    artifact = ModelArtifact(
        preprocessor=preprocessor,
        model=model,
        feature_names=feature_names,
        categorical_features=cat_cols,
        numerical_features=num_cols,
        model_version="v1.0.0",
        trained_at=pd.Timestamp.now().isoformat(),
        training_metrics={"roc_auc": roc_auc},
        threshold_policy=thresholds,
    )

    save_artifact(artifact, output_dir=str(artifacts_dir), name="model_v1")

    # Also save thresholds to backend/policy/thresholds.json
    backend_policy = Path(__file__).resolve().parent.parent.parent / "backend" / "policy" / "thresholds.json"
    if backend_policy.parent.exists():
        save_thresholds(thresholds, str(backend_policy))
        print(f"Updated backend policy at: {backend_policy}")

    print("=" * 60)
    print("[SUCCESS] Successfully generated model_v1.joblib and metadata sidecar!")
    print("=" * 60)


if __name__ == "__main__":
    main()
