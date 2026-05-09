"""
Domain exception hierarchy for the Oracle Fusion Diagnostic Agent.
All exceptions carry HTTP status codes and structured error payloads.
"""
from typing import Any, Dict, Optional


class AgentBaseException(Exception):
    """Base for all agent exceptions."""
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# ── Authentication / Authorization ────────────────────────────────────────────
class AuthenticationError(AgentBaseException):
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"


class AuthorizationError(AgentBaseException):
    status_code = 403
    error_code = "FORBIDDEN"


class TokenExpiredError(AuthenticationError):
    error_code = "TOKEN_EXPIRED"


# ── Browser / Automation ──────────────────────────────────────────────────────
class BrowserSessionError(AgentBaseException):
    status_code = 503
    error_code = "BROWSER_SESSION_ERROR"


class BrowserPoolExhaustedError(BrowserSessionError):
    error_code = "BROWSER_POOL_EXHAUSTED"


class NavigationError(BrowserSessionError):
    error_code = "NAVIGATION_FAILED"


class LoginFailedError(BrowserSessionError):
    status_code = 401
    error_code = "FUSION_LOGIN_FAILED"


class MFARequiredException(BrowserSessionError):
    status_code = 428
    error_code = "MFA_REQUIRED"


class PageExtractionError(BrowserSessionError):
    error_code = "PAGE_EXTRACTION_FAILED"


class ScreenshotError(BrowserSessionError):
    error_code = "SCREENSHOT_FAILED"


# ── Oracle Fusion Domain ──────────────────────────────────────────────────────
class FusionResourceNotFoundError(AgentBaseException):
    status_code = 404
    error_code = "FUSION_RESOURCE_NOT_FOUND"


class FusionTimeoutError(AgentBaseException):
    status_code = 504
    error_code = "FUSION_TIMEOUT"


# ── AI / Gemini ───────────────────────────────────────────────────────────────
class AIProviderError(AgentBaseException):
    status_code = 502
    error_code = "AI_PROVIDER_ERROR"


class AIRateLimitError(AIProviderError):
    status_code = 429
    error_code = "AI_RATE_LIMIT"


class AIResponseParseError(AIProviderError):
    error_code = "AI_RESPONSE_PARSE_ERROR"


# ── Vector / Knowledge ────────────────────────────────────────────────────────
class VectorStoreError(AgentBaseException):
    status_code = 503
    error_code = "VECTOR_STORE_ERROR"


class KnowledgeIngestError(VectorStoreError):
    error_code = "KNOWLEDGE_INGEST_FAILED"


# ── Configuration ─────────────────────────────────────────────────────────────
class ConfigurationError(AgentBaseException):
    status_code = 500
    error_code = "CONFIGURATION_ERROR"


# ── Validation ────────────────────────────────────────────────────────────────
class ValidationError(AgentBaseException):
    status_code = 422
    error_code = "VALIDATION_ERROR"
