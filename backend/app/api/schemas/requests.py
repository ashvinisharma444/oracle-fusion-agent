"""API request schemas."""
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class AnalyzeSubscriptionRequest(BaseModel):
    subscription_number: str = Field(..., min_length=1, max_length=100, description="Oracle Fusion subscription number")
    tenant_url: str = Field(..., description="Oracle Fusion tenant base URL")
    navigation_url: Optional[str] = Field(None, description="Direct navigation URL (optional)")
    issue_description: Optional[str] = Field(None, max_length=2000, description="Optional description of the reported issue")
    use_cache: bool = Field(True, description="Return cached result if available")

    @field_validator("tenant_url")
    @classmethod
    def validate_tenant_url(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError("tenant_url must start with https://")
        return v.rstrip("/")


class AnalyzeOrderRequest(BaseModel):
    order_number: str = Field(..., min_length=1, max_length=100)
    tenant_url: str = Field(..., description="Oracle Fusion tenant base URL")
    navigation_url: Optional[str] = None
    issue_description: Optional[str] = Field(None, max_length=2000)
    use_cache: bool = True

    @field_validator("tenant_url")
    @classmethod
    def validate_tenant_url(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError("tenant_url must start with https://")
        return v.rstrip("/")


class AnalyzeOrchestrationRequest(BaseModel):
    orchestration_id: str = Field(..., min_length=1, max_length=100)
    tenant_url: str
    navigation_url: Optional[str] = None
    issue_description: Optional[str] = None
    use_cache: bool = True


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000)
    module: Optional[str] = Field(None, description="Filter by module: subscription, order, orchestration, billing, pricing")
    n_results: int = Field(5, ge=1, le=20)


class KnowledgeIngestRequest(BaseModel):
    documents: list[str] = Field(..., min_length=1)
    collection: str = Field(..., description="Collection name: oracle_docs, rca_history, sql_patterns, config_guides")
    module: Optional[str] = None
    source: Optional[str] = None
    titles: Optional[list[str]] = None


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=1, description="User password")


class CreateSessionRequest(BaseModel):
    tenant_url: str = Field(..., description="Oracle Fusion tenant URL")
