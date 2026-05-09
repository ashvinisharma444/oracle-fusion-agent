"""Async PostgreSQL connection using SQLAlchemy 2.0 + asyncpg."""
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine, AsyncEngine
from app.config.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Lazy engine — created on first use so the app starts even if DB isn't ready yet
_engine: Optional[AsyncEngine] = None
_AsyncSessionLocal: Optional[async_sessionmaker] = None


def get_engine() -> AsyncEngine:
    """Return (or lazily create) the SQLAlchemy async engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        if not settings.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not configured")
        _engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            echo=settings.DATABASE_ECHO,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        logger.info("database_engine_created", url=settings.DATABASE_URL.split("@")[-1])
    return _engine


def get_session_factory() -> async_sessionmaker:
    """Return (or lazily create) the session factory."""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a database session."""
    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all tables on startup (use Alembic for migrations in production)."""
    from app.domain.models.diagnostic import Base
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_tables_created")


async def check_connection() -> bool:
    """Health check — verify DB is reachable."""
    try:
        if not get_settings().DATABASE_URL:
            return False
        async with get_engine().connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        return False
