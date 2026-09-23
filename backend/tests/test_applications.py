"""backend/tests/test_applications.py
Tests for role-scoped application access, details view, and loan officer overrides.
"""

def test_applicant_sees_only_own_applications(
    client, applicant_token, officer_token, sample_application_payload
):
    # Submit one application as applicant
    post_res = client.post(
        "/api/applications/",
        json=sample_application_payload,
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    assert post_res.status_code == 201
    created_id = post_res.json()["id"]

    # Applicant queries their list
    res = client.get(
        "/api/applications/",
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    assert res.status_code == 200
    apps = res.json()["applications"]
    assert len(apps) >= 1
    assert any(a["id"] == created_id for a in apps)


def test_officer_can_override_application(
    client, applicant_token, officer_token, sample_application_payload
):
    # Applicant submits loan
    post_res = client.post(
        "/api/applications/",
        json=sample_application_payload,
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    app_id = post_res.json()["id"]

    # Loan officer applies override
    override_res = client.patch(
        f"/api/applications/{app_id}/override",
        json={
            "decision": "approved",
            "reason": "Co-signor provided verified primary liquid assets to cover collateral requirement.",
        },
        headers={"Authorization": f"Bearer {officer_token}"},
    )
    assert override_res.status_code == 200
    updated = override_res.json()
    assert updated["officer_override"] == "approved"
    assert "Co-signor provided" in updated["override_reason"]
    assert updated["override_by"] is not None


def test_applicant_cannot_override(
    client, applicant_token, sample_application_payload
):
    post_res = client.post(
        "/api/applications/",
        json=sample_application_payload,
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    app_id = post_res.json()["id"]

    override_res = client.patch(
        f"/api/applications/{app_id}/override",
        json={
            "decision": "approved",
            "reason": "Applicant attempting to self-override.",
        },
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    assert override_res.status_code == 403


def test_override_reason_must_meet_min_length(
    client, applicant_token, officer_token, sample_application_payload
):
    post_res = client.post(
        "/api/applications/",
        json=sample_application_payload,
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    app_id = post_res.json()["id"]

    override_res = client.patch(
        f"/api/applications/{app_id}/override",
        json={
            "decision": "approved",
            "reason": "too short",
        },
        headers={"Authorization": f"Bearer {officer_token}"},
    )
    assert override_res.status_code == 422
