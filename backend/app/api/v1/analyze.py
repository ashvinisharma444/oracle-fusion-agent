"""
Analyze endpoints — trigger diagnostic analysis for Fusion modules.
POST /api/v1/analyze/subscription
POST /api/v1/analyze/order
POST /api/v1/analyze/orchestration
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.requests import (
    AnalyzeSubscriptionRequest,
    AnalyzeOrderRequest,
    AnalyzeOrchestrationRequest,
)
from app.api.schemas.responses import DiagnosticReportResponse
from app.application.services.diagnostic_service import DiagnosticService
from app.infrastructure.database.postgres import get_db

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post("/subscription", response_model=DiagnosticReportResponse, summary="Analyze Oracle Fusion Subscription")
async def analyze_subscription(
    request: Request,
    body: AnalyzeSubscriptionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Perform AI-powered RCA on an Oracle Fusion subscription record.
    Opens the subscription in a browser, extracts data, and returns Gemini-powered diagnostics.
    READ-ONLY: does not modify any Fusion data.
    """
    user_id = getattr(request.state, "user_id", None)
    service = DiagnosticService(db)
    result = await service.analyze(
        module="subscription",
        transaction_ref=body.subscription_number,
        tenant_url=body.tenant_url,
        navigation_url=body.navigation_url,
        issue_description=body.issue_description,
        user_id=user_id,
        use_cache=body.use_cache,
    )
    return DiagnosticReportResponse(**result)


@router.post("/order", response_model=DiagnosticReportResponse, summary="Analyze Oracle Fusion Order")
async def analyze_order(
    request: Request,
    body: AnalyzeOrderRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Perform AI-powered RCA on an Oracle Fusion Order Management record.
    READ-ONLY.
    """
    user_id = getattr(request.state, "user_id", None)
    service = DiagnosticService(db)
    result = await service.analyze(
        module="order",
        transaction_ref=body.order_number,
        tenant_url=body.tenant_url,
        navigation_url=body.navigation_url,
        issue_description=body.issue_description,
        user_id=user_id,
        use_cache=body.use_cache,
    )
    return DiagnosticReportResponse(**result)


@router.post("/orchestration", response_model=DiagnosticReportResponse, summary="Analyze Oracle Fusion Orchestration")
async def analyze_orchestration(
    request: Request,
    body: AnalyzeOrchestrationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Perform AI-powered RCA on an Oracle Fusion Orchestration (DOO) process.
    READ-ONLY.
    """
    user_id = getattr(request.state, "user_id", None)
    service = DiagnosticService(db)
    result = await service.analyze(
        module="orchestration",
        transaction_ref=body.orchestration_id,
        tenant_url=body.tenant_url,
        navigation_url=body.navigation_url,
        issue_description=body.issue_description,
        user_id=user_id,
        use_cache=body.use_cache,
    )
    return DiagnosticReportResponse(**result)
