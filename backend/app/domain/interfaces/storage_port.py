"""Abstract storage port for session and diagnostic persistence."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.domain.models.diagnostic import DiagnosticReport
from app.domain.models.session import BrowserSession
from app.domain.models.screenshot import Screenshot


class StoragePort(ABC):
    """Async persistence interface. Implementations: PostgresAdapter."""

    # ── Sessions ──────────────────────────────────────────────────────────────
    @abstractmethod
    async def save_session(self, session: BrowserSession) -> BrowserSession:
        ...

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[BrowserSession]:
        ...

    @abstractmethod
    async def list_sessions(self, user_id: Optional[str] = None) -> List[BrowserSession]:
        ...

    @abstractmethod
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> Optional[BrowserSession]:
        ...

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        ...

    # ── Diagnostics ───────────────────────────────────────────────────────────
    @abstractmethod
    async def save_diagnostic(self, report: DiagnosticReport) -> DiagnosticReport:
        ...

    @abstractmethod
    async def get_diagnostic(self, diagnostic_id: str) -> Optional[DiagnosticReport]:
        ...

    @abstractmethod
    async def list_diagnostics(
        self,
        module: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DiagnosticReport]:
        ...

    # ── Screenshots ───────────────────────────────────────────────────────────
    @abstractmethod
    async def save_screenshot(self, screenshot: Screenshot) -> Screenshot:
        ...

    @abstractmethod
    async def get_screenshot(self, screenshot_id: str) -> Optional[Screenshot]:
        ...

    @abstractmethod
    async def list_screenshots(
        self,
        session_id: Optional[str] = None,
        diagnostic_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Screenshot]:
        ...
