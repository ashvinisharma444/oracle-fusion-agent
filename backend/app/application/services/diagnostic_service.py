"""
Diagnostic Service — orchestrates the full diagnostic workflow.
Browser navigation → page extraction → screenshot → knowledge retrieval → Gemini RCA.
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.exceptions import FusionResourceNotFoundError, NavigationError
from app.core.logging import get_logger
from app.domain.interfaces.ai_port import RCAReport
from app.domain.interfaces.browser_port import BrowserPort
from app.domain.models.diagnostic import DiagnosticReport, DiagnosticSession, Screenshot
from app.infrastructure.ai.gemini_adapter import get_ai_provider
from app.infrastructure.browser.playwright_adapter import get_browser_adapter
from app.infrastructure.browser.page_objects.subscription_page import SubscriptionPage
from app.infrastructure.browser.page_objects.order_page import OrderPage
from app.infrastructure.browser.page_objects.orchestration_page import OrchestrationPage
from app.infrastructure.vector.chromadb_adapter import get_vector_store
from app.infrastructure.database.redis_client import cache_get, cache_set

logger = get_logger(__name__)
settings = get_settings()

PAGE_CLASS_MAP = {
    "subscription": SubscriptionPage,
    "order": OrderPage,
    "orchestration": OrchestrationPage,
}


class DiagnosticService:
    """
    Orchestrates end-to-end diagnostic analysis for Oracle Fusion records.
    All operations are READ-ONLY.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.browser = get_browser_adapter()
        self.ai = get_ai_provider()

    async def analyze(
        self,
        module: str,
        transaction_ref: str,
        tenant_url: str,
        navigation_url: Optional[str] = None,
        issue_description: Optional[str] = None,
        user_id: Optional[str] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Full diagnostic flow:
        1. Check cache
        2. Create diagnostic session record
        3. Get/create browser session
        4. Navigate to the relevant Fusion page
        5. Extract structured page data
        6. Capture screenshot
        7. Save screenshot to disk
        8. Retrieve relevant knowledge context
        9. Call Gemini for RCA
        10. Persist report
        11. Return structured result
        """
        cache_key = f"diagnostic:{module}:{transaction_ref}"
        if use_cache:
            cached = await cache_get(cache_key)
            if cached:
                logger.info("diagnostic_cache_hit", module=module, transaction_ref=transaction_ref)
                return cached

        # Create diagnostic session
        diag_session = DiagnosticSession(
            user_id=user_id,
            tenant_url=tenant_url,
            module=module,
            transaction_ref=transaction_ref,
            status="running",
        )
        self.db.add(diag_session)
        await self.db.flush()
        session_id = str(diag_session.id)

        try:
            # Get browser session
            browser_sessions = await self.browser.get_active_sessions()
            matching = [s for s in browser_sessions if s.tenant_url == tenant_url and s.authenticated]

            if matching:
                browser_session_id = matching[0].session_id
                logger.info("browser_session_reused", session_id=browser_session_id)
            else:
                browser_session_obj = await self.browser.create_session(tenant_url)
                browser_session_id = browser_session_obj.session_id
                logger.info("browser_session_created", session_id=browser_session_id)

            # Navigate to page
            target_url = navigation_url or self._build_url(tenant_url, module, transaction_ref)
            snapshot = await self.browser.navigate_to(browser_session_id, target_url)

            # Extract structured data using page objects
            page_class = PAGE_CLASS_MAP.get(module.lower())
            extracted_data = snapshot.extracted_data
            if page_class and snapshot.screenshot_bytes:
                try:
                    # Re-use page from adapter for structured extraction
                    adapter_session = self.browser._sessions.get(browser_session_id)
                    if adapter_session and adapter_session.page:
                        page_obj = page_class(adapter_session.page)
                        page_snapshot = await page_obj.extract()
                        extracted_data = page_snapshot.structured_data
                except Exception as e:
                    logger.warning("page_object_extraction_failed", error=str(e))

            # Save screenshot
            screenshot_path = None
            if snapshot.screenshot_bytes:
                screenshot_path = await self._save_screenshot(
                    snapshot.screenshot_bytes, module, transaction_ref, session_id
                )
                screenshot_record = Screenshot(
                    report_id=None,
                    session_id=diag_session.id,
                    filename=Path(screenshot_path).name,
                    file_path=screenshot_path,
                    page_url=snapshot.url,
                    page_type=module,
                    file_size_bytes=len(snapshot.screenshot_bytes),
                )
                self.db.add(screenshot_record)

            # Retrieve knowledge context
            knowledge_context = []
            try:
                vector_store = await get_vector_store()
                query = f"{module} {transaction_ref} {issue_description or ''}"
                knowledge_context = await vector_store.search_all_collections(
                    query=query, module_filter=module
                )
            except Exception as e:
                logger.warning("knowledge_retrieval_failed", error=str(e))

            # Generate RCA via Gemini
            rca_report = await self.ai.generate_rca(
                page_data={
                    "module": module,
                    "transaction_ref": transaction_ref,
                    "url": snapshot.url,
                    "title": snapshot.title,
                    "extracted_data": extracted_data,
                    "issue_description": issue_description,
                },
                knowledge_context=knowledge_context,
                module=module,
                transaction_ref=transaction_ref,
            )

            # Persist diagnostic report
            report = DiagnosticReport(
                session_id=diag_session.id,
                transaction_ref=transaction_ref,
                module=module,
                root_cause=rca_report.diagnostic_result.root_cause,
                root_cause_detail=rca_report.diagnostic_result.root_cause_detail,
                severity=rca_report.diagnostic_result.severity.value,
                confidence_score=rca_report.diagnostic_result.confidence_score,
                impacted_modules=rca_report.diagnostic_result.impacted_modules,
                recommended_diagnostics=rca_report.diagnostic_result.recommended_diagnostics,
                suggested_next_steps=rca_report.diagnostic_result.suggested_next_steps,
                supporting_evidence=rca_report.diagnostic_result.supporting_evidence,
                raw_page_data=extracted_data,
                model_used=rca_report.diagnostic_result.model_used,
                tokens_used=rca_report.diagnostic_result.tokens_used,
            )
            self.db.add(report)

            diag_session.status = "completed"
            diag_session.completed_at = datetime.utcnow()
            diag_session.browser_session_id = browser_session_id
            await self.db.flush()

            result = {
                "session_id": session_id,
                "report_id": str(report.id),
                "module": module,
                "transaction_ref": transaction_ref,
                "root_cause": rca_report.diagnostic_result.root_cause,
                "root_cause_detail": rca_report.diagnostic_result.root_cause_detail,
                "severity": rca_report.diagnostic_result.severity.value,
                "confidence_score": rca_report.diagnostic_result.confidence_score,
                "impacted_modules": rca_report.diagnostic_result.impacted_modules,
                "recommended_diagnostics": rca_report.diagnostic_result.recommended_diagnostics,
                "suggested_next_steps": rca_report.diagnostic_result.suggested_next_steps,
                "supporting_evidence": rca_report.diagnostic_result.supporting_evidence,
                "screenshot_path": screenshot_path,
                "knowledge_context_count": len(knowledge_context),
                "page_url": snapshot.url,
                "analyzed_at": datetime.utcnow().isoformat(),
            }

            await cache_set(cache_key, result, ttl=1800)
            logger.info("diagnostic_complete", module=module, transaction_ref=transaction_ref, severity=result["severity"])
            return result

        except Exception as e:
            diag_session.status = "failed"
            diag_session.error_message = str(e)[:1000]
            await self.db.flush()
            logger.error("diagnostic_failed", module=module, transaction_ref=transaction_ref, error=str(e))
            raise

    def _build_url(self, tenant_url: str, module: str, transaction_ref: str) -> str:
        module_url_map = {
            "subscription": f"{tenant_url}/fscmUI/faces/FuseWelcome?fnd=%3B%3B%3B%3B%3BokRenderModule%3DokPageId%3DOkSubscriptionManagement",
            "order": f"{tenant_url}/fscmUI/faces/FuseWelcome?fnd=%3B%3B%3B%3B%3BokRenderModule%3DokPageId%3DSalesOrdersOverview",
            "orchestration": f"{tenant_url}/fscmUI/faces/FuseWelcome?fnd=%3B%3B%3B%3B%3BokRenderModule%3DokPageId%3DManageOrchestrationOrders",
        }
        return module_url_map.get(module.lower(), tenant_url)

    async def _save_screenshot(
        self, image_bytes: bytes, module: str, transaction_ref: str, session_id: str
    ) -> str:
        os.makedirs(settings.SCREENSHOTS_DIR, exist_ok=True)
        filename = f"{module}_{transaction_ref}_{session_id[:8]}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(settings.SCREENSHOTS_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        logger.info("screenshot_saved", filepath=filepath, size_bytes=len(image_bytes))
        return filepath
