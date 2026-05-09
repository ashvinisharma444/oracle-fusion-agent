"""
Provider-agnostic AI interface (port).
Implement this to swap Gemini → Claude → OpenAI without touching business logic.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class DiagnosticResult:
    """Structured output from AI analysis."""
    root_cause: str
    root_cause_detail: str
    severity: Severity
    confidence_score: float  # 0.0 – 1.0
    impacted_modules: List[str]
    recommended_diagnostics: List[str]
    suggested_next_steps: List[str]
    supporting_evidence: List[str]
    raw_ai_response: str
    model_used: str
    tokens_used: int
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RCAReport:
    """Full Root Cause Analysis report."""
    diagnostic_result: DiagnosticResult
    transaction_reference: str
    module: str
    page_data_summary: str
    knowledge_context_used: List[str]
    screenshots_analyzed: List[str]
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AIProviderConfig:
    model: str
    max_tokens: int
    temperature: float
    api_key: str


class AIProvider(ABC):
    """
    Abstract AI provider — implement for Gemini, Claude, OpenAI, etc.
    All implementations must be async.
    """

    @abstractmethod
    async def analyze_screenshot(
        self,
        image_bytes: bytes,
        context: str,
        module: str,
        additional_context: Optional[str] = None,
    ) -> DiagnosticResult:
        """Analyze a Fusion screenshot and return structured diagnostics."""
        ...

    @abstractmethod
    async def generate_rca(
        self,
        page_data: Dict[str, Any],
        knowledge_context: List[str],
        module: str,
        transaction_ref: str,
    ) -> RCAReport:
        """Generate a full RCA report from page data and retrieved knowledge."""
        ...

    @abstractmethod
    async def structured_query(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run a structured query and return a validated JSON response."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify the AI provider is reachable."""
        ...
