"""
app/database.py
---------------
SQLAlchemy engine, session factory, declarative base, and FastAPI dependency.
Supports MySQL (production/development) and SQLite via DATABASE_URL.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
# check_same_thread=False is required for SQLite only; safe to include for
# non-SQLite databases as well (ignored by other dialects).
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    # Pool settings suitable for a single-process web server.
    # For production with PostgreSQL, use NullPool or QueuePool with higher values.
    pool_pre_ping=True,
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ---------------------------------------------------------------------------
# Declarative base – all ORM models inherit from this
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Project-wide SQLAlchemy declarative base."""
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db():
    """
    Yield a SQLAlchemy Session for use within a single HTTP request.
    The session is always closed in the finally block to return the connection
    back to the pool.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Table creation helper (called at application startup)
# ---------------------------------------------------------------------------
def create_tables() -> None:
    """
    Create all tables defined via ORM models if they do not already exist.
    In production, prefer running Alembic migrations instead.
    """
    # Import here to ensure models are registered with Base before create_all.
    from . import models  # noqa: F401  (side-effect import)
    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """
    Quick liveness check: run a trivial query and return True if successful.
    Used by the /health endpoint.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
