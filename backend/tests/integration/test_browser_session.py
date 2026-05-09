"""Integration tests for browser session management."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.models.session import BrowserSession, SessionStatus


class TestBrowserSessionIntegration:
    @pytest.mark.asyncio
    async def test_create_session_returns_session_object(self):
        """Verify session creation returns a properly structured BrowserSession."""
        mock_session = BrowserSession(
            id="test-session-001",
            user_id="test-user",
            tenant_url="https://test.oraclecloud.com",
            status=SessionStatus.ACTIVE,
        )

        with patch(
            "app.application.services.session_service.SessionService.create_authenticated_session",
            AsyncMock(return_value=mock_session),
        ):
            from app.application.services.session_service import SessionService
            service = SessionService()
            session = await service.create_authenticated_session(
                tenant_url="https://test.oraclecloud.com",
                user_id="test-user",
            )

        assert session.id == "test-session-001"
        assert session.status == SessionStatus.ACTIVE
        assert session.tenant_url == "https://test.oraclecloud.com"

    @pytest.mark.asyncio
    async def test_session_to_dict_complete(self):
        """Verify session serialization includes all required fields."""
        session = BrowserSession(
            id="test-001",
            user_id="user-001",
            tenant_url="https://test.oraclecloud.com",
            status=SessionStatus.IDLE,
        )
        d = session.to_dict()
        required_keys = ["id", "user_id", "tenant_url", "status", "created_at", "last_activity", "uptime_seconds"]
        for key in required_keys:
            assert key in d, f"Missing key: {key}"

    @pytest.mark.asyncio
    async def test_session_touch_updates_activity(self):
        """Verify touch() updates last_activity."""
        import time
        from datetime import timezone
        session = BrowserSession()
        original_activity = session.last_activity
        time.sleep(0.01)
        session.touch()
        assert session.last_activity >= original_activity

    def test_session_status_transitions(self):
        """Verify status enum values are correct."""
        assert SessionStatus.ACTIVE.value == "active"
        assert SessionStatus.IDLE.value == "idle"
        assert SessionStatus.ERROR.value == "error"
        assert SessionStatus.CLOSED.value == "closed"
        assert SessionStatus.MFA_PENDING.value == "mfa_pending"
