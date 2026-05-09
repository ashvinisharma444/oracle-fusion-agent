"""Health, readiness, and metrics endpoints."""
from datetime import datetime
from fastapi import APIRouter
from app.api.schemas.responses import HealthResponse
from app.config.settings import get_settings
from app.infrastructure.database.postgres import check_connection
from app.infrastructure.database.redis_client import check_redis_connection

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse, include_in_schema=True)
async def health():
    db_ok = await check_connection()
    redis_ok = await check_redis_connection()
    components = {"database": db_ok, "redis": redis_ok, "api": True}
    status = "healthy" if all(components.values()) else "degraded"
    return HealthResponse(status=status, version=settings.APP_VERSION, components=components, timestamp=datetime.utcnow())


@router.get("/ready")
async def readiness():
    db_ok = await check_connection()
    if not db_ok:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content={"ready": False, "reason": "database unavailable"})
    return {"ready": True}
