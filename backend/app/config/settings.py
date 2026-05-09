"""
Application configuration using Pydantic BaseSettings.
All values driven by environment variables — never hardcoded.
"""
from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ───────────────────────────────────────────────────
    ENVIRONMENT: str = Field(default="development")
    APP_NAME: str = Field(default="Oracle Fusion AI Diagnostic Agent")
    APP_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")

    # ── API ───────────────────────────────────────────────────────────
    API_PREFIX: str = Field(default="/api/v1")
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"])
    API_RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    REQUEST_TIMEOUT_SECONDS: int = Field(default=300)

    # ── Security ──────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = Field(default="change-me-in-production-minimum-32-chars!!")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    INTERNAL_API_KEY: str = Field(default="change-me-internal-key")

    # ── Oracle Fusion ─────────────────────────────────────────────────
    ORACLE_FUSION_BASE_URL: str = Field(default="https://your-tenant.fa.us2.oraclecloud.com")
    ORACLE_FUSION_USERNAME: str = Field(default="")
    ORACLE_FUSION_PASSWORD: str = Field(default="")
    ORACLE_FUSION_MFA_ENABLED: bool = Field(default=False)
    ORACLE_FUSION_LOGIN_TIMEOUT_MS: int = Field(default=30000)
    ORACLE_FUSION_NAV_TIMEOUT_MS: int = Field(default=60000)

    # ── Browser Automation ────────────────────────────────────────────
    PLAYWRIGHT_HEADLESS: bool = Field(default=True)
    BROWSER_POOL_MAX_SIZE: int = Field(default=5)
    BROWSER_SESSION_TTL_SECONDS: int = Field(default=3600)
    SCREENSHOTS_DIR: str = Field(default="/tmp/screenshots")
    BROWSER_TRACES_DIR: str = Field(default="/tmp/traces")

    # ── AI / Gemini ───────────────────────────────────────────────────
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = Field(default="gemini-2.5-pro")
    GEMINI_MAX_TOKENS: int = Field(default=8192)
    GEMINI_TEMPERATURE: float = Field(default=0.1)
    GEMINI_MAX_RETRIES: int = Field(default=3)
    GEMINI_RETRY_DELAY_SECONDS: float = Field(default=2.0)

    # ── Database (PostgreSQL) ─────────────────────────────────────────
    DATABASE_URL: str = Field(default="postgresql+asyncpg://fusion:fusion@localhost:5432/fusionagent")
    DATABASE_POOL_SIZE: int = Field(default=10)
    DATABASE_MAX_OVERFLOW: int = Field(default=20)
    DATABASE_ECHO: bool = Field(default=False)

    # ── Cache (Redis) ─────────────────────────────────────────────────
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_TTL_SECONDS: int = Field(default=3600)

    # ── Vector DB (ChromaDB) ──────────────────────────────────────────
    CHROMADB_HOST: str = Field(default="localhost")
    CHROMADB_PORT: int = Field(default=8001)
    CHROMADB_COLLECTION_ORACLE_DOCS: str = Field(default="oracle_docs")
    CHROMADB_COLLECTION_RCA_HISTORY: str = Field(default="rca_history")
    CHROMADB_COLLECTION_SQL_PATTERNS: str = Field(default="sql_patterns")
    CHROMADB_COLLECTION_CONFIG_GUIDES: str = Field(default="config_guides")
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2")
    RETRIEVAL_TOP_K: int = Field(default=5)
    RETRIEVAL_SCORE_THRESHOLD: float = Field(default=0.7)

    # ── Observability ─────────────────────────────────────────────────
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = Field(default=None)
    PROMETHEUS_METRICS_ENABLED: bool = Field(default=True)
    SENTRY_DSN: Optional[str] = Field(default=None)

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
