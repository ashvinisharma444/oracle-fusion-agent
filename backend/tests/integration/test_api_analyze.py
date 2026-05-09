"""Integration tests for /api/v1/analyze endpoints."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.domain.models.diagnostic import DiagnosticModule, DiagnosticReport, RCAReport, Severity


def make_mock_report(entity_id: str = "TEST-001", module: str = "subscription") -> DiagnosticReport:
    report = DiagnosticReport(
        id="report-test-001",
        session_id="session-001",
        module=DiagnosticModule.SUBSCRIPTION,
        entity_id=entity_id,
        tenant_url="https://test.oraclecloud.com",
        status="completed",
        duration_ms=1234.5,
    )
    report.rca = RCAReport(
        root_cause="Integration test root cause",
        impacted_modules=["subscription", "billing"],
        severity=Severity.HIGH,
        recommended_diagnostics=["Check subscription status", "Verify billing account"],
        confidence_score=0.92,
        evidence=["Status shows ERROR"],
    )
    return report


@pytest.fixture
def test_token():
    from app.core.security import create_access_token, Role
    return create_access_token(subject="test-user", role=Role.ANALYST)


@pytest.fixture
def app_client(test_token):
    from app.main import app
    return AsyncClient(app=app, base_url="http://test")


@pytest.mark.asyncio
async def test_analyze_subscription_success(test_token):
    mock_report = make_mock_report("SUB-001")

    with patch(
        "app.api.v1.analyze.diagnostic_service.run_subscription_diagnostic",
        AsyncMock(return_value=mock_report),
    ):
        from app.main import app
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/analyze/subscription",
                json={"subscription_number": "SUB-001", "tenant_url": "https://test.oraclecloud.com"},
                headers={"Authorization": f"Bearer {test_token}"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["entity_id"] == "SUB-001"
    assert data["status"] == "completed"
    assert data["rca"]["severity"] == "HIGH"
    assert data["rca"]["confidence_score"] == 0.92


@pytest.mark.asyncio
async def test_analyze_subscription_unauthorized():
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/analyze/subscription",
            json={"subscription_number": "SUB-001", "tenant_url": "https://test.oraclecloud.com"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_endpoint():
    with (
        patch("app.api.v1.health.get_redis", AsyncMock(return_value=AsyncMock(ping=AsyncMock()))),
        patch("app.api.v1.health.get_playwright_adapter", AsyncMock(return_value=AsyncMock(health_check=AsyncMock(return_value=True)))),
        patch("app.api.v1.health.get_chromadb_adapter", MagicMock(return_value=MagicMock(health_check=AsyncMock(return_value=True)))),
    ):
        from app.main import app
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
