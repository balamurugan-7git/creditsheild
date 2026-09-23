"""ml/tests/test_pipeline.py
Unit tests for data preprocessing and feature transformations.
"""

import numpy as np
import pandas as pd
import pytest

from src.pipeline import (
    clean_data,
    build_preprocessor,
    split_data,
    BUCKET_A_CATEGORICAL,
    BUCKET_A_NUMERICAL,
)


def test_clean_data_handles_days_employed_anomaly():
    df = pd.DataFrame({
        "DAYS_EMPLOYED": [365243, -1200, 365243, -500],
        "NAME_INCOME_TYPE": ["Pensioner", "Working", "Pensioner", "Commercial associate"],
    })
    cleaned = clean_data(df)
    assert np.isnan(cleaned["DAYS_EMPLOYED"].iloc[0])
    assert np.isnan(cleaned["DAYS_EMPLOYED"].iloc[2])
    assert cleaned["DAYS_EMPLOYED"].iloc[1] == -1200


def test_build_preprocessor_handles_unseen_categories():
    train_df = pd.DataFrame({
        "NAME_CONTRACT_TYPE": ["Cash loans", "Revolving loans", "Cash loans"],
        "AMT_INCOME_TOTAL": [100000.0, 150000.0, 200000.0],
    })
    test_df = pd.DataFrame({
        "NAME_CONTRACT_TYPE": ["Cash loans", "Unseen Type", "Revolving loans"],
        "AMT_INCOME_TOTAL": [120000.0, 180000.0, 90000.0],
    })

    preprocessor = build_preprocessor(
        categorical_features=["NAME_CONTRACT_TYPE"],
        numerical_features=["AMT_INCOME_TOTAL"],
    )
    preprocessor.fit(train_df)

    # Transform test set containing unseen category - must not raise exception
    transformed = preprocessor.transform(test_df)
    assert transformed.shape[0] == 3
    assert not np.isnan(transformed).any()


def test_split_data_preserves_class_stratification():
    np.random.seed(42)
    n_samples = 1000
    df = pd.DataFrame({
        "feature1": np.random.randn(n_samples),
        "TARGET": np.random.choice([0, 1], size=n_samples, p=[0.92, 0.08]),
    })

    X_train, X_val, X_test, y_train, y_val, y_test = split_data(df, target_col="TARGET")

    train_rate = y_train.mean()
    val_rate = y_val.mean()
    test_rate = y_test.mean()

    assert abs(train_rate - 0.08) < 0.03
    assert abs(val_rate - 0.08) < 0.04
    assert abs(test_rate - 0.08) < 0.04
