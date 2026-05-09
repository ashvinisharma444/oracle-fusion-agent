"""Oracle Fusion Orchestration / DOO page object. READ-ONLY."""
from typing import Any, Dict, List
from app.infrastructure.browser.page_objects.base_page import BasePage, ExtractedPageData


class OrchestrationPage(BasePage):
    """Extracts orchestration process data from Oracle Fusion DOO."""

    async def extract(self) -> ExtractedPageData:
        await self.wait_for_page_load()
        process_data = await self._extract_process_details()
        steps = await self._extract_process_steps()
        errors = await self._extract_errors()

        return ExtractedPageData(
            page_type="orchestration",
            url=self.page.url,
            title=await self.page.title(),
            raw_text=(await self.safe_get_text("body"))[:8000],
            structured_data={
                "process_details": process_data,
                "process_steps": steps,
                "errors": errors,
            },
        )

    async def _extract_process_details(self) -> Dict[str, Any]:
        selectors = {
            "process_id": '[id*="processId"], [class*="processId"]',
            "status": '[id*="processStatus"], [class*="status"]',
            "started_at": '[id*="startTime"], [class*="startDate"]',
            "completed_at": '[id*="endTime"], [class*="endDate"]',
            "order_ref": '[id*="orderNumber"], [class*="sourceOrderRef"]',
        }
        return await self.extract_page_data_multi(selectors)

    async def extract_page_data_multi(self, selectors: Dict[str, str]) -> Dict[str, Any]:
        result = {}
        for key, sel in selectors.items():
            result[key] = await self.safe_get_text(sel)
        return result

    async def _extract_process_steps(self) -> List[Dict[str, Any]]:
        steps = []
        try:
            rows = await self.page.query_selector_all('[class*="step-row"], [class*="task-row"], tr[class*="row"]')
            for row in rows[:50]:
                step_name = await self.safe_get_text_from_element(row, '[class*="step-name"], td:first-child')
                step_status = await self.safe_get_text_from_element(row, '[class*="status"], td:nth-child(2)')
                if step_name:
                    steps.append({"name": step_name, "status": step_status})
        except Exception:
            pass
        return steps

    async def safe_get_text_from_element(self, parent, selector: str) -> str:
        try:
            el = await parent.query_selector(selector)
            return (await el.inner_text()).strip() if el else ""
        except Exception:
            return ""

    async def _extract_errors(self) -> List[str]:
        return await self.get_all_text(
            '[class*="error-message"], [class*="alert-danger"], .oj-message-error, [severity="error"]'
        )
