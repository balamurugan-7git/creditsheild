"""
app/schemas.py
--------------
Pydantic v2 request / response schemas for the CrediShield API.

Organisation
------------
1. Auth schemas
2. Loan application input schema (Home Credit Bucket A features)
3. Prediction / SHAP output schemas
4. Application CRUD schemas
5. Helper utilities (display name converter)
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ===========================================================================
# Helper: feature name → human-readable display name
# ===========================================================================

_FEATURE_DISPLAY_MAP: dict[str, str] = {
    # External scores
    "EXT_SOURCE_1": "External Credit Score 1",
    "EXT_SOURCE_2": "External Credit Score 2",
    "EXT_SOURCE_3": "External Credit Score 3",
    # Income / credit amounts
    "AMT_INCOME_TOTAL": "Total Annual Income",
    "AMT_CREDIT": "Loan Credit Amount",
    "AMT_ANNUITY": "Loan Annuity Amount",
    "AMT_GOODS_PRICE": "Goods Price",
    # Days features
    "DAYS_BIRTH": "Applicant Age (days)",
    "DAYS_EMPLOYED": "Days Employed",
    "DAYS_REGISTRATION": "Days Since Registration",
    "DAYS_ID_PUBLISH": "Days Since ID Published",
    # Demographics
    "CODE_GENDER": "Gender",
    "CNT_CHILDREN": "Number of Children",
    "CNT_FAM_MEMBERS": "Family Members Count",
    "NAME_FAMILY_STATUS": "Family Status",
    "NAME_EDUCATION_TYPE": "Education Level",
    "NAME_INCOME_TYPE": "Income Type",
    "NAME_HOUSING_TYPE": "Housing Type",
    "NAME_CONTRACT_TYPE": "Contract Type",
    "NAME_TYPE_SUITE": "Accompanied By",
    "OCCUPATION_TYPE": "Occupation Type",
    "ORGANIZATION_TYPE": "Organization Type",
    # Ownership flags
    "FLAG_OWN_CAR": "Owns a Car",
    "FLAG_OWN_REALTY": "Owns Real Estate",
    "OWN_CAR_AGE": "Car Age (years)",
    # Contact flags
    "FLAG_MOBIL": "Mobile Phone Provided",
    "FLAG_EMP_PHONE": "Work Phone Provided",
    "FLAG_WORK_PHONE": "Work Phone Flag",
    "FLAG_CONT_MOBILE": "Contact Mobile Flag",
    "FLAG_PHONE": "Phone Provided",
    "FLAG_EMAIL": "Email Provided",
    # Region
    "REGION_POPULATION_RELATIVE": "Region Population (relative)",
    "REGION_RATING_CLIENT": "Region Rating",
    "REGION_RATING_CLIENT_W_CITY": "Region Rating (with city)",
    "REG_REGION_NOT_LIVE_REGION": "Reg/Live Region Mismatch",
    "REG_REGION_NOT_WORK_REGION": "Reg/Work Region Mismatch",
    "LIVE_REGION_NOT_WORK_REGION": "Live/Work Region Mismatch",
    "REG_CITY_NOT_LIVE_CITY": "Reg/Live City Mismatch",
    "REG_CITY_NOT_WORK_CITY": "Reg/Work City Mismatch",
    "LIVE_CITY_NOT_WORK_CITY": "Live/Work City Mismatch",
    # Application process
    "WEEKDAY_APPR_PROCESS_START": "Application Day of Week",
    "HOUR_APPR_PROCESS_START": "Application Hour",
}


def to_display_name(feature: str) -> str:
    """
    Convert a raw feature column name to a human-readable display name.

    Falls back to title-cased, space-separated words when no explicit mapping
    is found (e.g. ``MY_FEATURE_X`` → ``My Feature X``).
    """
    if feature in _FEATURE_DISPLAY_MAP:
        return _FEATURE_DISPLAY_MAP[feature]
    return feature.replace("_", " ").title()


# ===========================================================================
# 1. Auth schemas
# ===========================================================================


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=255)
    role: Literal["applicant", "loan_officer"] = "applicant"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    full_name: Optional[str] = None
    created_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: str
    role: str


# ===========================================================================
# 2. Loan application input schema (Home Credit Bucket A)
# ===========================================================================


class LoanApplicationInput(BaseModel):
    """
    Input features sourced from the Home Credit *application_train* dataset
    (Bucket A – core application-level features available at submission time).

    All categorical fields accept the raw string values used in the dataset.
    All day-based fields are negative integers representing days before the
    application date (except DAYS_EMPLOYED=365243 which signals unemployment).
    """

    # ---- Personal demographics ----
    CODE_GENDER: Literal["M", "F", "XNA"]
    FLAG_OWN_CAR: Literal["Y", "N"]
    FLAG_OWN_REALTY: Literal["Y", "N"]
    CNT_CHILDREN: int = Field(ge=0, le=20)

    # ---- Financial ----
    AMT_INCOME_TOTAL: float = Field(gt=0)
    AMT_CREDIT: float = Field(gt=0)
    AMT_ANNUITY: Optional[float] = None
    AMT_GOODS_PRICE: Optional[float] = None

    # ---- Categorical demographics ----
    NAME_TYPE_SUITE: Optional[str] = None
    NAME_INCOME_TYPE: str
    NAME_EDUCATION_TYPE: str
    NAME_FAMILY_STATUS: str
    NAME_HOUSING_TYPE: str
    NAME_CONTRACT_TYPE: str

    # ---- Region ----
    REGION_POPULATION_RELATIVE: Optional[float] = None

    # ---- Days features ----
    DAYS_BIRTH: int  # negative: days before application (proxy for age)
    DAYS_EMPLOYED: int  # negative = employed; 365243 = not employed (anomaly flag)
    DAYS_REGISTRATION: float
    DAYS_ID_PUBLISH: int

    # ---- Contact flags ----
    FLAG_MOBIL: Optional[int] = Field(default=None, ge=0, le=1)
    FLAG_EMP_PHONE: Optional[int] = Field(default=None, ge=0, le=1)
    FLAG_WORK_PHONE: Optional[int] = Field(default=None, ge=0, le=1)
    FLAG_CONT_MOBILE: Optional[int] = Field(default=None, ge=0, le=1)
    FLAG_PHONE: Optional[int] = Field(default=None, ge=0, le=1)
    FLAG_EMAIL: Optional[int] = Field(default=None, ge=0, le=1)

    # ---- Employment ----
    OCCUPATION_TYPE: Optional[str] = None
    ORGANIZATION_TYPE: Optional[str] = None

    # ---- Family ----
    CNT_FAM_MEMBERS: Optional[float] = None

    # ---- Region ratings ----
    REGION_RATING_CLIENT: Optional[int] = Field(default=None, ge=1, le=3)
    REGION_RATING_CLIENT_W_CITY: Optional[int] = Field(default=None, ge=1, le=3)

    # ---- Application process ----
    WEEKDAY_APPR_PROCESS_START: Optional[str] = None
    HOUR_APPR_PROCESS_START: Optional[int] = Field(default=None, ge=0, le=23)

    # ---- Region/city match flags ----
    REG_REGION_NOT_LIVE_REGION: Optional[int] = Field(default=None, ge=0, le=1)
    REG_REGION_NOT_WORK_REGION: Optional[int] = Field(default=None, ge=0, le=1)
    LIVE_REGION_NOT_WORK_REGION: Optional[int] = Field(default=None, ge=0, le=1)
    REG_CITY_NOT_LIVE_CITY: Optional[int] = Field(default=None, ge=0, le=1)
    REG_CITY_NOT_WORK_CITY: Optional[int] = Field(default=None, ge=0, le=1)
    LIVE_CITY_NOT_WORK_CITY: Optional[int] = Field(default=None, ge=0, le=1)

    # ---- External credit scores ----
    EXT_SOURCE_1: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    EXT_SOURCE_2: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    EXT_SOURCE_3: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    # ---- Car age ----
    OWN_CAR_AGE: Optional[float] = Field(default=None, ge=0.0)

    @field_validator("DAYS_BIRTH")
    @classmethod
    def days_birth_must_be_negative(cls, v: int) -> int:
        if v >= 0:
            raise ValueError("DAYS_BIRTH must be negative (days before application).")
        return v

    @field_validator("DAYS_REGISTRATION")
    @classmethod
    def days_registration_must_be_non_positive(cls, v: float) -> float:
        if v > 0:
            raise ValueError("DAYS_REGISTRATION must be non-positive.")
        return v

    @field_validator("DAYS_ID_PUBLISH")
    @classmethod
    def days_id_publish_must_be_non_positive(cls, v: int) -> int:
        if v > 0:
            raise ValueError("DAYS_ID_PUBLISH must be non-positive.")
        return v


# ===========================================================================
# 3. Prediction / SHAP output schemas
# ===========================================================================


class ShapFactor(BaseModel):
    """A single SHAP factor contributing to the model decision."""

    feature: str
    shap_value: float
    direction: Literal["increases_risk", "decreases_risk"]
    display_name: str


class PredictionResult(BaseModel):
    """Output of the ML prediction service for a single application."""

    probability: float = Field(ge=0.0, le=1.0)
    decision: Literal["approved", "manual_review", "rejected"]
    shap_top_factors: list[ShapFactor]


# ===========================================================================
# 4. Application CRUD schemas
# ===========================================================================


class ApplicationResponse(BaseModel):
    """Full application record returned to API consumers."""

    id: int
    applicant_id: int
    input_features: Optional[dict] = None
    probability: float
    decision: str
    model_version: str
    shap_top_factors: Optional[list[dict]] = None

    # Override fields
    officer_override: Optional[str] = None
    override_reason: Optional[str] = None
    override_by: Optional[int] = None
    override_at: Optional[datetime] = None

    scored_at: datetime

    model_config = {"from_attributes": True}


class OverrideRequest(BaseModel):
    """Body sent by a loan officer to override an automated decision."""

    decision: Literal["approved", "rejected"]
    reason: str = Field(min_length=10, max_length=2000)


class ApplicationListResponse(BaseModel):
    """Paginated list of applications."""

    total: int
    items: list[ApplicationResponse]
    applications: Optional[list[ApplicationResponse]] = None

    def __init__(self, **data):
        if "items" in data and "applications" not in data:
            data["applications"] = data["items"]
        elif "applications" in data and "items" not in data:
            data["items"] = data["applications"]
        super().__init__(**data)
