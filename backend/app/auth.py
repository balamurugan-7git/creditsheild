"""
app/auth.py
-----------
Authentication utilities for CrediShield:

- Password hashing / verification (bcrypt via passlib)
- JWT creation and decoding (python-jose)
- FastAPI dependencies: get_current_user, require_role
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User
from .schemas import TokenData

# ---------------------------------------------------------------------------
# Password hashing (using direct bcrypt for Python 3.13+ compatibility)
# ---------------------------------------------------------------------------
import bcrypt


def hash_password(password: str) -> str:
    """Return bcrypt hash of *password*."""
    # Ensure password is truncated to 72 bytes max as required by bcrypt
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    try:
        plain_bytes = plain.encode("utf-8")[:72]
        hashed_bytes = hashed.encode("utf-8")
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# OAuth2 scheme – looks for a Bearer token in the Authorization header
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------
def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Encode *data* into a signed JWT.

    Parameters
    ----------
    data:
        Payload dict.  ``sub`` and ``role`` are the expected keys.
    expires_delta:
        Custom expiry; falls back to ``settings.access_token_expire_minutes``.

    Returns
    -------
    str
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT.

    Raises
    ------
    HTTPException(401)
        If the token is invalid, expired, or missing required claims.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        email: str | None = payload.get("sub")
        role: str | None = payload.get("role")
        if email is None or role is None:
            raise credentials_exception
        return TokenData(email=email, role=role)
    except JWTError:
        raise credentials_exception


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------
def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    FastAPI dependency that validates the Bearer token and returns the
    corresponding active ``User`` ORM instance.

    Raises
    ------
    HTTPException(401)
        Invalid / expired token, or user not found / inactive.
    """
    token_data = decode_token(token)
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(role: str):
    """
    Factory that returns a FastAPI dependency enforcing a specific role.

    Usage
    -----
    ::

        @router.get("/admin-only")
        def admin_route(user: User = Depends(require_role("loan_officer"))):
            ...

    Raises
    ------
    HTTPException(403)
        When the authenticated user does not have the required role.
    """

    def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to role '{role}'.",
            )
        return current_user

    return role_checker
