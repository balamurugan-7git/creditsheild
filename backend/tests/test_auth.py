"""backend/tests/test_auth.py
Tests for authentication, registration, token generation, and role authorization.
"""

def test_register_applicant_success(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "newapplicant@example.com",
            "password": "Password123!",
            "role": "applicant",
            "full_name": "New Applicant",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newapplicant@example.com"
    assert data["role"] == "applicant"
    assert "id" in data


def test_register_duplicate_email_conflict(client, applicant_user):
    response = client.post(
        "/api/auth/register",
        json={
            "email": applicant_user.email,
            "password": "AnyPassword123!",
            "role": "applicant",
            "full_name": "Duplicate User",
        },
    )
    assert response.status_code == 409


def test_login_success(client, applicant_user):
    response = client.post(
        "/api/auth/login",
        data={"username": applicant_user.email, "password": "Secret123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client, applicant_user):
    response = client.post(
        "/api/auth/login",
        data={"username": applicant_user.email, "password": "WrongPassword!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401


def test_get_current_user_me(client, applicant_token):
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "applicant@test.com"


def test_unauthenticated_request_fails(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
