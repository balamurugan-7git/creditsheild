"""
app/main.py
-----------
FastAPI application factory for CrediShield AI.

Features
--------
- Lifespan context manager: loads ML model and creates DB tables on startup.
- CORS middleware configured from settings.
- SlowAPI rate limiting (10 req/min default per remote IP).
- Custom exception handlers for rate-limit and validation errors.
- Structured JSON logging.
- Root redirect to /docs.
"""

from __future__ import annotations

import json
import logging
import logging.config
import sys
from pathlib import Path

# Ensure ML package directory is on sys.path for model artifact unpickling
ml_dir = Path(__file__).resolve().parent.parent.parent / "ml"
if ml_dir.exists() and str(ml_dir) not in sys.path:
    sys.path.insert(0, str(ml_dir))

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from .config import settings
from .database import create_tables
from .routes import auth as auth_router
from .routes import applications as applications_router
from .routes import health as health_router
from .services.prediction import load_model_service

# ---------------------------------------------------------------------------
# Logging – emit structured JSON to stdout for easy ingestion by log aggregators
# ---------------------------------------------------------------------------
class _JsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def _configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root_logger = logging.getLogger()
    root_logger.setLevel(
        logging.DEBUG if settings.app_env == "development" else logging.INFO
    )
    root_logger.handlers = [handler]


_configure_logging()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Rate limiter (module-level so routers can import and reuse it)
# ---------------------------------------------------------------------------
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit],
)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Startup
    -------
    1. Create database tables (idempotent, safe for dev; use Alembic in prod).
    2. Attempt to load the ML model service from the configured artefact path.

    Shutdown
    --------
    Log a graceful shutdown message.
    """
    logger.info("CrediShield AI API starting up (env=%s).", settings.app_env)

    # Create DB tables (no-op if they already exist)
    try:
        create_tables()
        logger.info("Database tables verified / created.")
    except Exception as exc:
        logger.error("Failed to create database tables: %s", exc, exc_info=True)

    # Load ML model
    load_model_service(
        model_path=settings.model_path,
        meta_path=settings.model_meta_path,
    )

    yield  # ← application runs here

    logger.info("CrediShield AI API shutting down.")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title="CrediShield AI API",
    description=(
        "Explainable AI-powered credit risk scoring API. "
        "Supports loan application scoring, SHAP explanations, and officer overrides."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---- Rate limiting state ----
app.state.limiter = limiter

# ---- Middleware ----
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https://.*\.onrender\.com|http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Routers ----
app.include_router(auth_router.router, prefix="/api")
app.include_router(applications_router.router, prefix="/api")
app.include_router(health_router.router, prefix="/api")


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a structured 429 response when a rate limit is exceeded."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded. Please slow down.",
            "retry_after": str(exc.retry_after) if hasattr(exc, "retry_after") else None,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a 422 response with structured field-level error messages."""
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": " → ".join(str(loc) for loc in error.get("loc", [])),
                "message": error.get("msg", "Validation error"),
                "type": error.get("type", ""),
            }
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Request validation failed.", "errors": errors},
    )


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """Redirect bare root to the interactive API documentation."""
    return RedirectResponse(url="/docs")
