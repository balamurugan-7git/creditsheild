"""backend/tests/test_prediction_service.py
Unit tests for ModelService, policy functions, and SHAP formatting helpers.
"""

from pathlib import Path
import pytest
from app.services.prediction import ModelService, _strip_transformer_prefix
from app.services import policy
from app.schemas import to_display_name, PredictionResult


def test_strip_transformer_prefix():
    assert _strip_transformer_prefix("cat__CODE_GENDER_M") == "CODE_GENDER"
    assert _strip_transformer_prefix("cat__FLAG_OWN_CAR_Y") == "FLAG_OWN_CAR"
    assert _strip_transformer_prefix("num__AMT_CREDIT") == "AMT_CREDIT"
    assert _strip_transformer_prefix("DAYS_BIRTH") == "DAYS_BIRTH"


def test_to_display_name():
    assert to_display_name("EXT_SOURCE_1") == "External Credit Score 1"
    assert to_display_name("AMT_INCOME_TOTAL") == "Total Annual Income"
    assert to_display_name("SOME_CUSTOM_FEATURE") == "Some Custom Feature"


def test_policy_classify():
    assert policy.classify(0.01) == "approved"
    assert policy.classify(0.50) in ["approved", "manual_review", "rejected"]
    assert policy.classify(0.99) == "rejected"
    assert isinstance(policy.get_thresholds(), dict)


def test_model_service_missing_artifact():
    with pytest.raises(FileNotFoundError):
        ModelService(model_path="nonexistent_model.joblib", meta_path="none.json")


def test_model_service_real_artifact(sample_application_payload):
    model_path = Path(__file__).resolve().parent.parent.parent / "ml" / "artifacts" / "model_v1.joblib"
    meta_path = Path(__file__).resolve().parent.parent.parent / "ml" / "artifacts" / "model_v1_meta.json"
    
    if not model_path.exists():
        pytest.skip("model_v1.joblib not present")

    svc = ModelService(str(model_path), str(meta_path))
    assert svc.is_loaded() is True
    assert svc.get_version() != ""

    res = svc.predict(sample_application_payload)
    assert isinstance(res, PredictionResult)
    assert 0.0 <= res.probability <= 1.0
    assert res.decision in ["approved", "manual_review", "rejected"]
    assert len(res.shap_top_factors) > 0
    assert len(res.shap_top_factors) <= 5
    for factor in res.shap_top_factors:
        assert factor.feature != ""
        assert factor.direction in ["increases_risk", "decreases_risk"]
        assert factor.display_name != ""
