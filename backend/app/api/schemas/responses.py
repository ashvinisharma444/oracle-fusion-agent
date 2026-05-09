"""API response schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class DiagnosticReportResponse(BaseModel):
    session_id: str
    report_id: Optional[str]
    module: str
    transaction_ref: str
    root_cause: str
    root_cause_detail: Optional[str]
    severity: str
    confidence_score: float
    impacted_modules: List[str]
    recommended_diagnostics: List[str]
    suggested_next_steps: List[str]
    supporting_evidence: List[str]
    screenshot_path: Optional[str]
    knowledge_context_count: int
    page_url: Optional[str]
    analyzed_at: str


class SessionStatusResponse(BaseModel):
    session_id: str
    status: str
    tenant_url: str
    authenticated: bool
    current_url: Optional[str]
    created_at: datetime
    last_used_at: datetime


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    count: int


class HealthResponse(BaseModel):
    status: str
    version: str
    components: Dict[str, bool]
    timestamp: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Dict[str, Any] = {}
