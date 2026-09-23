"""backend/tests/test_predictions.py
Tests for loan scoring endpoint, SHAP attribution delivery, and input validation.
"""

def test_score_application_success(client, applicant_token, sample_application_payload):
    response = client.post(
        "/api/applications/",
        json=sample_application_payload,
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "probability" in data
    assert data["decision"] in ["approved", "manual_review", "rejected"]
    assert len(data["shap_top_factors"]) > 0
    assert data["shap_top_factors"][0]["display_name"] != ""


def test_score_application_requires_auth(client, sample_application_payload):
    response = client.post("/api/applications/", json=sample_application_payload)
    assert response.status_code == 401


def test_score_application_invalid_payload(client, applicant_token):
    # Missing required fields
    response = client.post(
        "/api/applications/",
        json={"CODE_GENDER": "M"},
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    assert response.status_code == 422
    assert "errors" in response.json()
