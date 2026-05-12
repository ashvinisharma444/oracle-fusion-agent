"""
JWT authentication, RBAC stubs, and password utilities.
OAuth-ready architecture – swap credentials provider without touching business logic.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

# Monkey-patch bcrypt 4.x to restore __about__ attribute that passlib 1.7.4 expects
import bcrypt as _bcrypt_compat
if not hasattr(_bcrypt_compat, '__about__'):
    class _BcryptAbout:
        __version__ = '4.0.1'
    _bcrypt_compat.__about__ = _BcryptAbout()

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
    import bcrypt
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    import bcrypt
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


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
        "jti": secrets.token_urlsafe(16),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as exc:
        msg = str(exc).lower()
        if "expired" in msg:
            raise TokenExpiredError() from exc
        raise AuthenticationError("Invalid or malformed token") from exc


def get_token_subject(token: str) -> str:
    payload = decode_token(token)
    sub = payload.get("sub")
    if not sub:
        raise AuthenticationError("Token missing subject claim")
    return sub


def get_token_role(token: str) -> Role:
    payload = decode_token(token)
    role_str = payload.get("role", Role.VIEWER.value)
    try:
        return Role(role_str)
    except ValueError:
        return Role.VIEWER
