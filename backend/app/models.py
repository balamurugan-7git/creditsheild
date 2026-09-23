"""
app/models.py
-------------
SQLAlchemy ORM models for CrediShield.

Tables
------
- users       : registered applicants and loan officers
- applications: scored loan applications with SHAP explanations and optional overrides
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    """Return timezone-aware UTC datetime (avoids DeprecationWarning in Python 3.12+)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class User(Base):
    """
    Registered user of the CrediShield system.

    Roles
    -----
    - ``applicant``   : can submit applications and view their own results
    - ``loan_officer``: can view all applications and override decisions
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="applicant"
    )  # 'applicant' | 'loan_officer'
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    applications: Mapped[list["Application"]] = relationship(
        "Application",
        back_populates="applicant",
        foreign_keys="Application.applicant_id",
    )
    overrides_performed: Mapped[list["Application"]] = relationship(
        "Application",
        back_populates="overriding_officer",
        foreign_keys="Application.override_by",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
class Application(Base):
    """
    A scored loan application.

    The raw feature dict is persisted in ``input_features`` (JSON column) so
    results can always be reproduced or audited.  SHAP explanations are stored
    as a JSON list of ``{feature, shap_value, direction}`` objects.
    """

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ---- applicant ----
    applicant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # ---- model inputs / outputs ----
    input_features: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # raw feature dict sent to the model
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'approved' | 'manual_review' | 'rejected'
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    shap_top_factors: Mapped[list | None] = mapped_column(
        JSON, nullable=True
    )  # [{feature, shap_value, direction, display_name}, ...]

    # ---- officer override (optional) ----
    officer_override: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # 'approved' | 'rejected'
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    override_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    override_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ---- metadata ----
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # ---- relationships ----
    applicant: Mapped["User"] = relationship(
        "User",
        back_populates="applications",
        foreign_keys=[applicant_id],
    )
    overriding_officer: Mapped["User | None"] = relationship(
        "User",
        back_populates="overrides_performed",
        foreign_keys=[override_by],
    )

    def __repr__(self) -> str:
        return (
            f"<Application id={self.id} applicant_id={self.applicant_id} "
            f"decision={self.decision!r} probability={self.probability:.4f}>"
        )
