"""Session lifecycle service."""
from __future__ import annotations

from typing import List, Optional

from app.core.exceptions import BrowserSessionNotFoundError
from app.core.logging import get_logger
from app.domain.models.session import BrowserSession, SessionStatus
from app.infrastructure.browser.playwright_adapter import get_playwright_adapter
from app.infrastructure.browser.page_objects.login_page import LoginPage
from app.infrastructure.browser.session_manager import get_session_manager
from app.infrastructure.database.postgres import AsyncSessionLocal, SessionORM
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class SessionService:
    """Manages browser session lifecycle with database persistence."""

    async def create_authenticated_session(
        self,
        tenant_url: str,
        user_id: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> BrowserSession:
        """Create a browser session and authenticate with Oracle Fusion."""
        manager = await get_session_manager()
        session = await manager.get_or_create_session(tenant_url, user_id)

        # Check if already authenticated
        adapter = await get_playwright_adapter()
        handle = adapter._sessions.get(session.id)
        if handle:
            login_page = LoginPage(handle.page)
            if await login_page.is_logged_in():
                logger.info("session_already_authenticated", session_id=session.id)
                session.status = SessionStatus.ACTIVE
                await self._persist_session(session)
                return session

            # Perform login
            await login_page.navigate_to_login(tenant_url)
            await login_page.login(username=username, password=password, session_id=session.id)

        session.status = SessionStatus.ACTIVE
        session.touch()
        await self._persist_session(session)
        logger.info("session_authenticated", session_id=session.id, tenant_url=tenant_url)
        return session

    async def get_session(self, session_id: str) -> BrowserSession:
        manager = await get_session_manager()
        return await manager.get_session(session_id)

    async def list_sessions(self, user_id: Optional[str] = None) -> List[BrowserSession]:
        manager = await get_session_manager()
        sessions = await manager.list_sessions()
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        return sessions

    async def close_session(self, session_id: str) -> None:
        manager = await get_session_manager()
        await manager.close_session(session_id)
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(SessionORM)
                .where(SessionORM.id == session_id)
                .values(status="closed")
            )
            await db.commit()

    async def _persist_session(self, session: BrowserSession) -> None:
        async with AsyncSessionLocal() as db:
            existing = await db.get(SessionORM, session.id)
            if existing:
                existing.status = session.status.value
                existing.current_url = session.current_url
                existing.page_title = session.page_title
                existing.error_message = session.error_message
            else:
                db.add(SessionORM(
                    id=session.id,
                    user_id=session.user_id,
                    tenant_url=session.tenant_url,
                    status=session.status.value,
                    current_url=session.current_url,
                    cookies_path=session.cookies_path,
                    page_title=session.page_title,
                    error_message=session.error_message,
                ))
            await db.commit()


session_service = SessionService()
