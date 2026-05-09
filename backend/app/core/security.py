"""
JWT authentication, RBAC stubs, and password utilities.
OAuth-ready architecture — swap credentials provider without touching business logic.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config.settings import get_settings
from app.core.exceptions import AuthenticationError, TokenExpiredError
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── RBAC ──────────────────────────────────────────────────────────────────────
class Role(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


ROLE_PERMISSIONS: Dict[Role, List[str]] = {
    Role.ADMIN: ["*"],
    Role.ANALYST: [
        "analyze:read", "analyze:write",
        "screenshot:read", "screenshot:write",
        "session:read", "session:write",
        "knowledge:read", "knowledge:write",
    ],
    Role.VIEWER: [
        "analyze:read",
        "screenshot:read",
        "session:read",
        "knowledge:read",
    ],
}


def has_permission(role: Role, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role, [])
    return "*" in perms or permission in perms


# ── Password Utilities ────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


# ── JWT ───────────────────────────────────────────────────────────────────────
def create_access_token(
    subject: str,
    role: Role = Role.VIEWER,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role.value,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str, role: Role = Role.VIEWER) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": subject,
        "role": role.value,
        "iat": now,
        "exp": expire,
        "type": "refresh",
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        if "expired" in str(e).lower():
            raise TokenExpiredError("Access token has expired")
        raise AuthenticationError(f"Invalid token: {e}")


def verify_internal_api_key(api_key: str) -> bool:
    expected = settings.INTERNAL_API_KEY
    return secrets.compare_digest(
        hashlib.sha256(api_key.encode()).digest(),
        hashlib.sha256(expected.encode()).digest(),
    )
