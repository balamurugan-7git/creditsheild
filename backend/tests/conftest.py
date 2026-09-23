"""backend/tests/conftest.py
Pytest fixtures with SQLite in-memory database and mocked model service.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.auth import create_access_token, hash_password
from app.models import User
from app.schemas import PredictionResult, ShapFactor
from app.services.prediction import get_model_service, ModelService

# In-memory SQLite engine
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh in-memory database per test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class MockModelService:
    def __init__(self):
        self.version = "v1-test"

    def is_loaded(self) -> bool:
        return True

    def get_version(self) -> str:
        return self.version

    def predict(self, input_dict: dict) -> PredictionResult:
        income = float(input_dict.get("AMT_INCOME_TOTAL", 100000))
        credit = float(input_dict.get("AMT_CREDIT", 200000))
        ext2 = float(input_dict.get("EXT_SOURCE_2", 0.5) or 0.5)

        # Illustrative probability calculation
        prob = 0.20
        if credit > income * 5 or ext2 < 0.3:
            prob = 0.72
        elif credit > income * 3:
            prob = 0.45

        decision = "approved" if prob < 0.35 else ("manual_review" if prob <= 0.65 else "rejected")

        factors = [
            ShapFactor(
                feature="EXT_SOURCE_2",
                shap_value=-0.12 if ext2 >= 0.5 else 0.25,
                direction="decreases_risk" if ext2 >= 0.5 else "increases_risk",
                display_name="External Credit Score 2",
            ),
            ShapFactor(
                feature="AMT_CREDIT",
                shap_value=0.15 if credit > 300000 else -0.05,
                direction="increases_risk" if credit > 300000 else "decreases_risk",
                display_name="Loan Credit Amount",
            ),
            ShapFactor(
                feature="DAYS_EMPLOYED",
                shap_value=-0.08,
                direction="decreases_risk",
                display_name="Employment Duration",
            ),
        ]

        return PredictionResult(
            probability=prob,
            decision=decision,
            shap_top_factors=factors,
        )


@pytest.fixture(scope="function")
def mock_model():
    return MockModelService()


@pytest.fixture(scope="function")
def client(db, mock_model):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    def override_get_model_service():
        return mock_model

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_model_service] = override_get_model_service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def applicant_user(db):
    user = User(
        email="applicant@test.com",
        hashed_password=hash_password("Secret123!"),
        role="applicant",
        full_name="Test Applicant",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def applicant_token(applicant_user):
    return create_access_token(data={"sub": applicant_user.email, "role": applicant_user.role})


@pytest.fixture
def officer_user(db):
    user = User(
        email="officer@test.com",
        hashed_password=hash_password("Secret123!"),
        role="loan_officer",
        full_name="Test Loan Officer",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def officer_token(officer_user):
    return create_access_token(data={"sub": officer_user.email, "role": officer_user.role})


@pytest.fixture
def sample_application_payload():
    return {
        "CODE_GENDER": "M",
        "FLAG_OWN_CAR": "N",
        "FLAG_OWN_REALTY": "Y",
        "CNT_CHILDREN": 0,
        "AMT_INCOME_TOTAL": 180000.0,
        "AMT_CREDIT": 350000.0,
        "AMT_ANNUITY": 20000.0,
        "AMT_GOODS_PRICE": 350000.0,
        "NAME_INCOME_TYPE": "Working",
        "NAME_EDUCATION_TYPE": "Higher education",
        "NAME_FAMILY_STATUS": "Married",
        "NAME_HOUSING_TYPE": "House / apartment",
        "DAYS_BIRTH": -12000,
        "DAYS_EMPLOYED": -1800,
        "DAYS_REGISTRATION": -4500.0,
        "DAYS_ID_PUBLISH": -2500,
        "NAME_CONTRACT_TYPE": "Cash loans",
        "EXT_SOURCE_1": 0.65,
        "EXT_SOURCE_2": 0.70,
        "EXT_SOURCE_3": 0.60,
    }
