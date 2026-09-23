"""
app/routes/health.py
--------------------
Health-check endpoint.  Returns a JSON snapshot of application readiness:
database connectivity and ML model load status.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db, check_db_connection
from ..services import prediction as prediction_service

router = APIRouter(tags=["health"])


@router.get("/health", summary="Application health check")
def health_check(db: Session = Depends(get_db)):
    """
    Return the operational status of the API.

    Response fields
    ---------------
    - ``status``: always ``"ok"`` when the API process is reachable.
    - ``timestamp``: ISO-8601 UTC timestamp of the check.
    - ``model_loaded``: True if the ML model artefact has been loaded.
    - ``db_ok``: True if a test query to the database succeeded.
    """
    db_ok = check_db_connection()
    ms = prediction_service.model_service
    loaded = ms is not None and ms.is_loaded()

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_loaded": loaded,
        "db_ok": db_ok,
    }
