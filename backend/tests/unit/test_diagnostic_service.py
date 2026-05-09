"""Unit tests for DiagnosticService."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.models.diagnostic import DiagnosticModule, DiagnosticReport, RCAReport, Severity


class TestDiagnosticService:
    @pytest.fixture
    def mock_services(self):
        with (
            patch("app.application.services.diagnostic_service.session_service") as mock_session,
            patch("app.application.services.diagnostic_service.fusion_navigator") as mock_nav,
            patch("app.application.services.diagnostic_service.knowledge_service") as mock_knowledge,
            patch("app.application.services.diagnostic_service.get_gemini_adapter") as mock_ai_factory,
            patch("app.application.services.diagnostic_service.screenshot_service") as mock_ss,
        ):
            mock_session.create_authenticated_session = AsyncMock(return_value=MagicMock(id="sess-001"))

            # Mock subscription data
            mock_sub_data = MagicMock()
            mock_sub_data.to_dict.return_value = {"subscription_number": "SUB-001", "status": "ACTIVE"}
            mock_screenshot = MagicMock(id="screenshot-001")
            mock_nav.navigate_and_extract_subscription = AsyncMock(
                return_value=(mock_sub_data, mock_screenshot)
            )

            mock_knowledge.search_for_diagnostic = AsyncMock(return_value="Oracle docs context")
            mock_knowledge.ingest_rca = AsyncMock(return_value=["id-1"])

            mock_ai = AsyncMock()
            mock_ai.analyze_screenshot = AsyncMock(return_value={"observations": [], "anomalies": []})
            mock_ai.generate_rca = AsyncMock(return_value=RCAReport(
                root_cause="Test root cause",
                impacted_modules=["subscription"],
                severity=Severity.MEDIUM,
                recommended_diagnostics=["Step 1", "Step 2"],
                confidence_score=0.85,
            ))
            mock_ai_factory.return_value = mock_ai

            mock_ss.capture = AsyncMock(return_value=(mock_screenshot, b"image_bytes"))
            mock_ss.read_screenshot_bytes = MagicMock(return_value=b"image_bytes")

            yield {
                "session": mock_session,
                "nav": mock_nav,
                "knowledge": mock_knowledge,
                "ai": mock_ai,
            }

    @pytest.mark.asyncio
    async def test_run_subscription_diagnostic_success(self, mock_services):
        with patch("app.application.services.diagnostic_service.DiagnosticService._persist_report", AsyncMock()):
            from app.application.services.diagnostic_service import DiagnosticService
            service = DiagnosticService()
            report = await service.run_subscription_diagnostic(
                subscription_number="SUB-001",
                tenant_url="https://test.oraclecloud.com",
                user_id="test-user",
            )

        assert report.status == "completed"
        assert report.entity_id == "SUB-001"
        assert report.module == DiagnosticModule.SUBSCRIPTION
        assert report.rca is not None
        assert report.rca.confidence_score == 0.85

    @pytest.mark.asyncio
    async def test_run_subscription_diagnostic_handles_error(self, mock_services):
        mock_services["session"].create_authenticated_session.side_effect = Exception("Auth failed")
        with patch("app.application.services.diagnostic_service.DiagnosticService._persist_report", AsyncMock()):
            from app.application.services.diagnostic_service import DiagnosticService
            service = DiagnosticService()
            report = await service.run_subscription_diagnostic(
                subscription_number="SUB-ERR",
                tenant_url="https://test.oraclecloud.com",
            )

        assert report.status == "failed"
        assert "Auth failed" in report.error
