"""Oracle Fusion Order Management page object. READ-ONLY."""
from typing import Any, Dict, List
from app.infrastructure.browser.page_objects.base_page import BasePage, ExtractedPageData


class OrderPage(BasePage):
    """Extracts order data from Oracle Fusion Order Management."""

    async def extract(self) -> ExtractedPageData:
        await self.wait_for_page_load()
        label_pairs = await self._extract_all_label_values()
        lines = await self._extract_order_lines()
        orchestration_data = await self._extract_orchestration_info()

        return ExtractedPageData(
            page_type="order",
            url=self.page.url,
            title=await self.page.title(),
            raw_text=(await self.safe_get_text("body"))[:8000],
            structured_data={
                "order_fields": label_pairs,
                "order_lines": lines,
                "orchestration": orchestration_data,
            },
        )

    async def _extract_all_label_values(self) -> Dict[str, str]:
        try:
            return await self.page.evaluate("""
                () => {
                    const pairs = {};
                    document.querySelectorAll('label, .oj-label, th').forEach(el => {
                        const key = (el.innerText || '').trim().toLowerCase().replace(/[\\s:]+/g, '_').slice(0, 50);
                        const sib = el.nextElementSibling;
                        if (key && sib) pairs[key] = (sib.innerText || '').trim().slice(0, 200);
                    });
                    return pairs;
                }
            """) or {}
        except Exception:
            return {}

    async def _extract_order_lines(self) -> List[Dict[str, Any]]:
        lines = []
        try:
            rows = await self.page.query_selector_all('.oj-table-row, tr[data-rownumber]')
            for row in rows[:30]:
                cells = await row.query_selector_all('td')
                texts = [(await c.inner_text()).strip() for c in cells]
                if any(texts):
                    lines.append({"cells": texts})
        except Exception:
            pass
        return lines

    async def _extract_orchestration_info(self) -> Dict[str, Any]:
        return {
            "fulfillment_lines": await self.get_all_text('[class*="fulfillment"], [class*="orchestration"]'),
            "status_history": await self.get_all_text('[class*="status-history"], [class*="history"]'),
        }
