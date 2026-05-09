"""High-level Oracle Fusion navigation service."""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from app.core.logging import get_logger
from app.domain.models.diagnostic import DiagnosticModule
from app.domain.models.screenshot import Screenshot
from app.infrastructure.browser.page_objects.login_page import LoginPage
from app.infrastructure.browser.page_objects.order_page import OrderPage, OrderData
from app.infrastructure.browser.page_objects.orchestration_page import OrchestrationPage, OrchestrationData
from app.infrastructure.browser.page_objects.subscription_page import SubscriptionPage, SubscriptionData
from app.infrastructure.browser.playwright_adapter import get_playwright_adapter
from app.infrastructure.browser.screenshot_service import screenshot_service

logger = get_logger(__name__)


class FusionNavigator:
    """Orchestrates navigation to Oracle Fusion pages and data extraction (READ-ONLY)."""

    async def navigate_and_extract_subscription(
        self,
        session_id: str,
        tenant_url: str,
        subscription_number: str,
    ) -> Tuple[SubscriptionData, Screenshot]:
        adapter = await get_playwright_adapter()
        handle = adapter._sessions.get(session_id)
        if not handle:
            from app.core.exceptions import BrowserSessionNotFoundError
            raise BrowserSessionNotFoundError(session_id)

        page = SubscriptionPage(handle.page)
        await page.navigate_to_subscription(tenant_url, subscription_number)
        data = await page.extract_subscription_data(subscription_number)
        shot, _ = await screenshot_service.capture(
            session_id=session_id,
            page_type="subscription",
            description=f"Subscription {subscription_number}",
        )
        return data, shot

    async def navigate_and_extract_order(
        self,
        session_id: str,
        tenant_url: str,
        order_number: str,
    ) -> Tuple[OrderData, Screenshot]:
        adapter = await get_playwright_adapter()
        handle = adapter._sessions.get(session_id)
        if not handle:
            from app.core.exceptions import BrowserSessionNotFoundError
            raise BrowserSessionNotFoundError(session_id)

        page = OrderPage(handle.page)
        await page.navigate_to_order(tenant_url, order_number)
        data = await page.extract_order_data(order_number)
        shot, _ = await screenshot_service.capture(
            session_id=session_id,
            page_type="order",
            description=f"Order {order_number}",
        )
        return data, shot

    async def navigate_and_extract_orchestration(
        self,
        session_id: str,
        tenant_url: str,
        orchestration_id: str,
    ) -> Tuple[OrchestrationData, Screenshot]:
        adapter = await get_playwright_adapter()
        handle = adapter._sessions.get(session_id)
        if not handle:
            from app.core.exceptions import BrowserSessionNotFoundError
            raise BrowserSessionNotFoundError(session_id)

        page = OrchestrationPage(handle.page)
        await page.navigate_to_orchestration(tenant_url, orchestration_id)
        data = await page.extract_orchestration_data(orchestration_id)
        shot, _ = await screenshot_service.capture(
            session_id=session_id,
            page_type="orchestration",
            description=f"Orchestration {orchestration_id}",
        )
        return data, shot

    async def capture_screenshot_with_analysis(
        self,
        session_id: str,
        page_type: str,
    ) -> Tuple[Screenshot, bytes]:
        return await screenshot_service.capture(session_id=session_id, page_type=page_type)


fusion_navigator = FusionNavigator()
