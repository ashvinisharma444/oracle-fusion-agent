"""Base page object — all Fusion pages extend this."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
from app.config.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class ExtractedPageData:
    page_type: str
    url: str
    title: str
    raw_text: str
    structured_data: Dict[str, Any] = field(default_factory=dict)
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    warnings: list = field(default_factory=list)


class BasePage:
    """Base class for all Oracle Fusion page objects."""

    def __init__(self, page: Page):
        self.page = page
        self.timeout_ms = settings.ORACLE_FUSION_NAV_TIMEOUT_MS
        self.logger = get_logger(self.__class__.__name__)

    async def wait_for_page_load(self) -> None:
        await self.page.wait_for_load_state("networkidle", timeout=self.timeout_ms)
        await self.page.wait_for_timeout(1500)

    async def safe_get_text(self, selector: str, default: str = "") -> str:
        try:
            el = await self.page.query_selector(selector)
            return (await el.inner_text()).strip() if el else default
        except Exception:
            return default

    async def safe_get_attribute(self, selector: str, attr: str, default: str = "") -> str:
        try:
            return await self.page.get_attribute(selector, attr) or default
        except Exception:
            return default

    async def get_all_text(self, selector: str) -> list:
        try:
            els = await self.page.query_selector_all(selector)
            return [(await el.inner_text()).strip() for el in els]
        except Exception:
            return []

    async def extract(self) -> ExtractedPageData:
        raise NotImplementedError("Subclasses must implement extract()")
