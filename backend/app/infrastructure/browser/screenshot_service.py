"""Screenshot capture and storage service."""
from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Optional

from app.config.settings import settings
from app.core.logging import get_logger
from app.domain.models.screenshot import Screenshot
from app.infrastructure.browser.playwright_adapter import get_playwright_adapter

logger = get_logger(__name__)


class ScreenshotService:
    """Handles screenshot capture, storage, and base64 encoding."""

    async def capture(
        self,
        session_id: str,
        page_type: str = "generic",
        description: Optional[str] = None,
        diagnostic_id: Optional[str] = None,
    ) -> tuple[Screenshot, bytes]:
        """Capture screenshot and return (Screenshot metadata, raw PNG bytes)."""
        adapter = await get_playwright_adapter()
        screenshot = await adapter.capture_screenshot(session_id, page_type, description)
        if diagnostic_id:
            screenshot.diagnostic_id = diagnostic_id

        # Read bytes back for AI analysis
        image_bytes = b""
        if screenshot.file_path and os.path.exists(screenshot.file_path):
            with open(screenshot.file_path, "rb") as f:
                image_bytes = f.read()
        else:
            # Capture again to bytes if not stored
            image_bytes = await adapter.capture_screenshot_bytes(session_id)

        return screenshot, image_bytes

    def to_base64(self, image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode("utf-8")

    def get_screenshot_path(self, screenshot_id: str) -> Optional[str]:
        path = os.path.join(settings.browser_screenshot_dir, f"{screenshot_id}.png")
        return path if os.path.exists(path) else None

    def read_screenshot_bytes(self, screenshot_id: str) -> Optional[bytes]:
        path = self.get_screenshot_path(screenshot_id)
        if path:
            with open(path, "rb") as f:
                return f.read()
        return None


screenshot_service = ScreenshotService()
