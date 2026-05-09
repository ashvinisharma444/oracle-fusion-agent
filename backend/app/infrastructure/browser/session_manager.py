"""Browser session pool manager with health monitoring."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.config.settings import settings
from app.core.exceptions import BrowserSessionNotFoundError
from app.core.logging import get_logger
from app.domain.models.session import BrowserSession, SessionStatus
from app.infrastructure.browser.playwright_adapter import PlaywrightAdapter, get_playwright_adapter

logger = get_logger(__name__)

# Session idle timeout: 30 minutes
SESSION_IDLE_TIMEOUT = timedelta(minutes=30)


class SessionManager:
    """Manages browser session lifecycle including cleanup and health monitoring."""

    def __init__(self, adapter: Optional[PlaywrightAdapter] = None) -> None:
        self._adapter = adapter
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        if self._adapter is None:
            self._adapter = await get_playwright_adapter()
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("session_manager_started")

    async def stop(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()
        logger.info("session_manager_stopped")

    async def get_or_create_session(self, tenant_url: str, user_id: str) -> BrowserSession:
        """Return an existing idle session for this user+tenant or create a new one."""
        assert self._adapter is not None
        sessions = await self._adapter.list_sessions()
        for session in sessions:
            if (
                session.user_id == user_id
                and session.tenant_url == tenant_url
                and session.status in (SessionStatus.ACTIVE, SessionStatus.IDLE)
            ):
                session.touch()
                logger.info("session_reused", session_id=session.id)
                return session

        return await self._adapter.create_session(tenant_url, user_id)

    async def close_session(self, session_id: str) -> None:
        assert self._adapter is not None
        await self._adapter.close_session(session_id)

    async def list_sessions(self) -> List[BrowserSession]:
        assert self._adapter is not None
        return await self._adapter.list_sessions()

    async def get_session(self, session_id: str) -> BrowserSession:
        assert self._adapter is not None
        session = await self._adapter.get_session(session_id)
        if not session:
            raise BrowserSessionNotFoundError(session_id)
        return session

    async def _cleanup_loop(self) -> None:
        """Periodically close idle/errored sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # every 5 minutes
                assert self._adapter is not None
                sessions = await self._adapter.list_sessions()
                now = datetime.now(timezone.utc)
                for session in sessions:
                    if session.status == SessionStatus.CLOSED:
                        continue
                    idle_time = now - session.last_activity
                    if idle_time > SESSION_IDLE_TIMEOUT or session.status == SessionStatus.ERROR:
                        logger.info(
                            "session_cleanup",
                            session_id=session.id,
                            reason="idle_timeout" if idle_time > SESSION_IDLE_TIMEOUT else "error_state",
                        )
                        await self._adapter.close_session(session.id)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("cleanup_loop_error", error=str(exc))


# ── Singleton ────────────────────────────────────────────────────────────────
_manager: Optional[SessionManager] = None


async def get_session_manager() -> SessionManager:
    global _manager
    if _manager is None:
        _manager = SessionManager()
        await _manager.start()
    return _manager
