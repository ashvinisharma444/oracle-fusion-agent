"""Authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.requests import LoginRequest
from app.api.schemas.responses import TokenResponse
from app.core.security import create_access_token, create_refresh_token, verify_password, Role
from app.domain.models.diagnostic import User
from app.infrastructure.database.postgres import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, summary="Authenticate and receive JWT tokens")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    role = Role(user.role) if user.role in [r.value for r in Role] else Role.VIEWER
    access_token = create_access_token(str(user.id), role=role)
    refresh_token = create_refresh_token(str(user.id), role=role)
    from app.config.settings import get_settings
    settings = get_settings()
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
