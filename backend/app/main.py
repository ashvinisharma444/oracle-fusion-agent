"""
Oracle Fusion AI Diagnostic Agent — FastAPI application entry point.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.v1.router import api_router
from app.config.settings import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import register_middleware
from app.infrastructure.browser.playwright_adapter import get_browser_adapter
from app.infrastructure.database.postgres import create_tables

settings = get_settings()
configure_logging(log_level=settings.LOG_LEVEL, json_logs=settings.is_production)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("agent_starting", env=settings.ENVIRONMENT, version=settings.APP_VERSION)

    # Create DB tables — non-fatal if DB isn't ready yet
    try:
        await create_tables()
        logger.info("database_ready")
    except Exception as e:
        logger.warning("database_not_ready_at_startup", error=str(e))

    # Seed admin user from env vars if provided and no users exist yet
    try:
        admin_email = os.environ.get("ADMIN_EMAIL")
        admin_password = os.environ.get("ADMIN_PASSWORD")
        if admin_email and admin_password:
            from sqlalchemy import select
            from app.infrastructure.database.postgres import get_session_factory
            async_session_factory = get_session_factory()
            from app.domain.models.diagnostic import User
            from app.core.security import hash_password
            async with async_session_factory() as db:
                result = await db.execute(select(User).where(User.email == admin_email))
                existing = result.scalar_one_or_none()
                if not existing:
                    admin = User(
                        email=admin_email,
                        hashed_password=hash_password(admin_password),
                        role="admin",
                        is_active=True,
                    )
                    db.add(admin)
                    await db.commit()
                    logger.info("admin_user_seeded", email=admin_email)
                else:
                    logger.info("admin_user_already_exists", email=admin_email)
    except Exception as e:
        logger.warning("admin_seed_failed", error=str(e))

    # Pre-warm Playwright — non-fatal if browser isn't available
    browser = None
    try:
        browser = get_browser_adapter()
        await browser.initialize()
        logger.info("browser_engine_ready")
    except Exception as e:
        logger.warning("browser_not_ready_at_startup", error=str(e))

    logger.info("agent_ready")
    yield

    # Shutdown
    try:
        if browser:
            await browser.shutdown()
    except Exception:
        pass
    logger.info("agent_shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise AI Diagnostic Agent for Oracle Fusion Cloud — Phase 1 (Read-Only)",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Custom middleware (order matters — outermost first)
register_middleware(app)

# Routes
app.include_router(api_router, prefix=settings.API_PREFIX)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["info"]["x-logo"] = {"url": "https://www.oracle.com/favicon.ico"}
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
