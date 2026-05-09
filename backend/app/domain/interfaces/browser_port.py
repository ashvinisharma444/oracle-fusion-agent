"""
Abstract browser automation interface.
Implementations: PlaywrightAdapter (prod), MockBrowserAdapter (tests).
PHASE 1: Read-only operations ONLY. No write/submit methods.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SessionStatus(str, Enum):
    INITIALIZING = "initializing"
    ACTIVE = "active"
    IDLE = "idle"
    MFA_PENDING = "mfa_pending"
    ERROR = "error"
    CLOSED = "closed"


@dataclass
class BrowserSession:
    session_id: str
    status: SessionStatus
    tenant_url: str
    created_at: datetime
    last_used_at: datetime
    current_url: Optional[str] = None
    authenticated: bool = False
    metadata: Dict[str, Any] = None


@dataclass
class PageSnapshot:
    url: str
    title: str
    content: str         # Extracted text content
    html_structure: str  # Simplified DOM structure
    screenshot_bytes: Optional[bytes]
    extracted_data: Dict[str, Any]
    captured_at: datetime
    page_type: str


class BrowserPort(ABC):
    """
    Read-only browser automation interface.
    NEVER add create/update/delete/submit methods.
    """

    @abstractmethod
    async def create_session(self, tenant_url: str) -> BrowserSession:
        """Create and authenticate a new browser session."""
        ...

    @abstractmethod
    async def close_session(self, session_id: str) -> None:
        """Close and clean up a browser session."""
        ...

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[BrowserSession]:
        """Retrieve an existing session."""
        ...

    @abstractmethod
    async def navigate_to(self, session_id: str, url: str) -> PageSnapshot:
        """Navigate to a URL and return page snapshot."""
        ...

    @abstractmethod
    async def capture_screenshot(self, session_id: str, full_page: bool = True) -> bytes:
        """Capture screenshot of current page."""
        ...

    @abstractmethod
    async def extract_page_data(
        self, session_id: str, selectors: Dict[str, str]
    ) -> Dict[str, Any]:
        """Extract structured data from current page using CSS selectors."""
        ...

    @abstractmethod
    async def wait_for_selector(
        self, session_id: str, selector: str, timeout_ms: int = 10000
    ) -> bool:
        """Wait for a CSS selector to appear on page."""
        ...

    @abstractmethod
    async def get_active_sessions(self) -> List[BrowserSession]:
        """Return all active browser sessions."""
        ...
