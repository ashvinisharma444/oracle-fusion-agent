"""
Oracle Fusion Subscription Management page object.
READ-ONLY extraction of subscription details.
Supports Redwood UI and Classic UI selectors with fallback strategy.
"""
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.infrastructure.browser.page_objects.base_page import BasePage, ExtractedPageData


@dataclass
class SubscriptionData:
    subscription_number: str
    subscription_name: Optional[str]
    status: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    billing_account: Optional[str]
    sold_to_account: Optional[str]
    product: Optional[str]
    revenue_contract: Optional[str]
    currency: Optional[str]
    total_value: Optional[str]
    charges: List[Dict[str, Any]] = field(default_factory=list)
    orchestration_orders: List[str] = field(default_factory=list)
    service_events: List[str] = field(default_factory=list)
    raw_fields: Dict[str, Any] = field(default_factory=dict)


class SubscriptionPage(BasePage):
    """Extracts subscription data from Oracle Fusion Subscription Management UI."""

    # Redwood UI selectors (newer UI)
    REDWOOD_SELECTORS = {
        "subscription_number": '[data-field="subscriptionNumber"], .oj-label-value:has-text("Subscription Number") + .oj-label-value',
        "status": '[data-field="statusCode"], .subscription-status, [class*="status-badge"]',
        "start_date": '[data-field="startDate"], .oj-label-value:has-text("Start Date") + .oj-label-value',
        "end_date": '[data-field="endDate"], .oj-label-value:has-text("End Date") + .oj-label-value',
        "billing_account": '[data-field="billToCustomerName"], [class*="billing-account"]',
        "product": '[data-field="productName"], .subscription-product',
    }

    # Classic Fusion selectors (fallback)
    CLASSIC_SELECTORS = {
        "subscription_number": 'td:has-text("Subscription Number") + td, .af_outputText[id*="subscriptionNum"]',
        "status": '.af_outputText[id*="status"], td:has-text("Status") + td',
        "start_date": '.af_outputText[id*="startDate"], td:has-text("Start Date") + td',
        "end_date": '.af_outputText[id*="endDate"], td:has-text("End Date") + td',
        "billing_account": '.af_outputText[id*="billTo"], td:has-text("Bill-to Account") + td',
    }

    async def navigate_to_subscription(self, subscription_number: str) -> None:
        """Navigate to a specific subscription."""
        base_url = self.page.url.split("/fscmUI")[0]
        search_url = (
            f"{base_url}/fscmUI/faces/FuseWelcome"
            f"?fnd=%3BokRenderModule%3DokPageId%3DOkSubscriptionManagement"
        )
        await self.page.goto(search_url, wait_until="networkidle")
        await self.wait_for_page_load()

        # Search for subscription number
        search_selectors = [
            'input[placeholder*="subscription"]',
            'input[id*="searchField"]',
            'input[aria-label*="Search"]',
        ]
        for sel in search_selectors:
            try:
                await self.page.wait_for_selector(sel, timeout=3000)
                await self.page.fill(sel, subscription_number)
                await self.page.keyboard.press("Enter")
                await self.wait_for_page_load()
                break
            except Exception:
                continue

    async def extract(self) -> ExtractedPageData:
        """Extract all available subscription data from the current page."""
        await self.wait_for_page_load()
        sub_data = await self._extract_subscription_details()
        charges = await self._extract_charges()
        sub_data.charges = charges

        return ExtractedPageData(
            page_type="subscription",
            url=self.page.url,
            title=await self.page.title(),
            raw_text=await self.safe_get_text("body"),
            structured_data={
                "subscription_number": sub_data.subscription_number,
                "status": sub_data.status,
                "start_date": sub_data.start_date,
                "end_date": sub_data.end_date,
                "billing_account": sub_data.billing_account,
                "product": sub_data.product,
                "currency": sub_data.currency,
                "total_value": sub_data.total_value,
                "charges": charges,
                "raw_fields": sub_data.raw_fields,
            },
        )

    async def _extract_subscription_details(self) -> SubscriptionData:
        raw_fields = {}

        # Try Redwood selectors first, fall back to Classic
        for field_name, selector in self.REDWOOD_SELECTORS.items():
            value = await self.safe_get_text(selector)
            if not value:
                classic_sel = self.CLASSIC_SELECTORS.get(field_name, "")
                if classic_sel:
                    value = await self.safe_get_text(classic_sel)
            raw_fields[field_name] = value

        # Generic fallback: extract all label-value pairs visible on page
        label_values = await self._extract_label_value_pairs()
        raw_fields.update(label_values)

        return SubscriptionData(
            subscription_number=raw_fields.get("subscription_number", ""),
            subscription_name=raw_fields.get("subscription_name"),
            status=raw_fields.get("status"),
            start_date=raw_fields.get("start_date"),
            end_date=raw_fields.get("end_date"),
            billing_account=raw_fields.get("billing_account"),
            sold_to_account=raw_fields.get("sold_to_account"),
            product=raw_fields.get("product"),
            revenue_contract=raw_fields.get("revenue_contract"),
            currency=raw_fields.get("currency"),
            total_value=raw_fields.get("total_value"),
            raw_fields=raw_fields,
        )

    async def _extract_label_value_pairs(self) -> Dict[str, str]:
        """Generic extraction of all label-value pairs on the page."""
        result = {}
        try:
            js_result = await self.page.evaluate("""
                () => {
                    const pairs = {};
                    const labels = document.querySelectorAll(
                        '.oj-label, label, th, .af_panelFormLayout_label-cell, [class*="label"]'
                    );
                    labels.forEach(label => {
                        const text = label.innerText?.trim();
                        if (!text || text.length > 100) return;
                        const next = label.nextElementSibling || label.parentElement?.nextElementSibling;
                        if (next) {
                            const value = next.innerText?.trim();
                            if (value && value.length < 500) {
                                const key = text.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/__+/g, '_');
                                pairs[key] = value;
                            }
                        }
                    });
                    return pairs;
                }
            """)
            if isinstance(js_result, dict):
                result.update(js_result)
        except Exception as e:
            self.logger.warning("label_value_extraction_failed", error=str(e))
        return result

    async def _extract_charges(self) -> List[Dict[str, Any]]:
        """Extract charge lines from the subscription."""
        charges = []
        try:
            charge_rows = await self.page.query_selector_all(
                'tr[class*="charge"], tr[data-row-index], .oj-table-row'
            )
            for row in charge_rows[:20]:  # Limit to 20 rows
                row_text = await row.inner_text()
                cells = await row.query_selector_all("td")
                cell_texts = [(await c.inner_text()).strip() for c in cells]
                if any(cell_texts):
                    charges.append({"cells": cell_texts, "raw": row_text[:200]})
        except Exception as e:
            self.logger.warning("charge_extraction_failed", error=str(e))
        return charges
