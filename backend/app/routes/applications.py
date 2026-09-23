"""
app/routes/applications.py
--------------------------
Loan application scoring and management endpoints.

Endpoints
---------
POST   /applications/            – score a new application (rate-limited)
GET    /applications/            – list applications (own for applicants, all for officers)
GET    /applications/{id}        – fetch a single application
PATCH  /applications/{id}/override – officer decision override
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_role
from ..database import get_db
from ..models import Application, User
from ..schemas import (
    ApplicationListResponse,
    ApplicationResponse,
    LoanApplicationInput,
    OverrideRequest,
)
from ..services.prediction import ModelService, get_model_service

# Rate-limiter (shared with main app, key by remote IP)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/applications", tags=["applications"])


# ---------------------------------------------------------------------------
# Helper: ORM Application → ApplicationResponse
# ---------------------------------------------------------------------------
def _to_response(app: Application) -> ApplicationResponse:
    return ApplicationResponse(
        id=app.id,
        applicant_id=app.applicant_id,
        input_features=app.input_features,
        probability=app.probability,
        decision=app.decision,
        model_version=app.model_version,
        shap_top_factors=app.shap_top_factors,
        officer_override=app.officer_override,
        override_reason=app.override_reason,
        override_by=app.override_by,
        override_at=app.override_at,
        scored_at=app.scored_at,
    )


# ---------------------------------------------------------------------------
# POST /applications/
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Score a new loan application",
)
@limiter.limit("10/minute")
def create_application(
    request: Request,  # required by slowapi
    payload: LoanApplicationInput,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[ModelService, Depends(get_model_service)],
) -> ApplicationResponse:
    """
    Submit a loan application for automated scoring.

    The endpoint is rate-limited to **10 requests per minute** per IP address.
    Both *applicants* and *loan officers* may call this endpoint.

    Returns **503** if the ML model has not been loaded.
    """
    # Run prediction
    input_dict = payload.model_dump()
    result = svc.predict(input_dict)

    # Persist to DB
    app = Application(
        applicant_id=current_user.id,
        input_features=input_dict,
        probability=result.probability,
        decision=result.decision,
        model_version=svc.get_version(),
        shap_top_factors=[f.model_dump() for f in result.shap_top_factors],
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    return _to_response(app)


# ---------------------------------------------------------------------------
# GET /applications/
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=ApplicationListResponse,
    summary="List applications (paginated)",
)
def list_applications(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationListResponse:
    """
    Return a paginated list of loan applications.

    - **Applicants** see only their own applications.
    - **Loan officers** see all applications.

    Use ``?skip=0&limit=20`` for pagination.
    """
    query = db.query(Application)
    if current_user.role == "applicant":
        query = query.filter(Application.applicant_id == current_user.id)

    total = query.count()
    items = query.order_by(Application.scored_at.desc()).offset(skip).limit(limit).all()

    return ApplicationListResponse(
        total=total,
        items=[_to_response(a) for a in items],
    )


# ---------------------------------------------------------------------------
# GET /applications/{id}
# ---------------------------------------------------------------------------
@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Fetch a single application",
)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplicationResponse:
    """
    Retrieve a single application by ID.

    - **Applicants** receive **403 Forbidden** if the application belongs to
      another user.
    - **Loan officers** can access any application.
    """
    app = db.query(Application).filter(Application.id == application_id).first()
    if app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found.",
        )

    if current_user.role == "applicant" and app.applicant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this application.",
        )

    return _to_response(app)


# ---------------------------------------------------------------------------
# PATCH /applications/{id}/override
# ---------------------------------------------------------------------------
@router.patch(
    "/{application_id}/override",
    response_model=ApplicationResponse,
    summary="Override the automated lending decision (loan officers only)",
)
def override_decision(
    application_id: int,
    payload: OverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("loan_officer")),
) -> ApplicationResponse:
    """
    Override the model's automated decision for a specific application.

    Only **loan officers** can call this endpoint (403 otherwise).
    A minimum 10-character ``reason`` is required for audit purposes.
    """
    app = db.query(Application).filter(Application.id == application_id).first()
    if app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found.",
        )

    app.officer_override = payload.decision
    app.override_reason = payload.reason
    app.override_by = current_user.id
    app.override_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(app)

    return _to_response(app)
