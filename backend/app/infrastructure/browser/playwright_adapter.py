"""
Playwright browser automation adapter.
Implements BrowserPort. PHASE 1: READ-ONLY.
Manages browser pool, sessions, screenshots, cookie persistence.
"""
import asyncio
import base64
import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import (
    Browser, BrowserContext, Page, Playwright,
    async_playwright, TimeoutError as PlaywrightTimeout,
)

from app.config.settings import get_settings
from app.core.exceptions import (
    BrowserPoolExhaustedError, BrowserSessionError,
    LoginFailedError, MFARequiredException, NavigationError, ScreenshotError,
)
from app.core.logging import get_logger
from app.domain.interfaces.browser_port import BrowserPort, BrowserSession, PageSnapshot, SessionStatus

logger = get_logger(__name__)
settings = get_settings()


class PlaywrightBrowserSession:
    """Internal session state."""
    def __init__(self, session_id: str, tenant_url: str):
        self.session_id = session_id
        self.tenant_url = tenant_url
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.status = SessionStatus.INITIALIZING
        self.authenticated = False
        self.created_at = datetime.utcnow()
        self.last_used_at = datetime.utcnow()
        self.current_url: Optional[str] = None
        self._cookie_file = Path(settings.SCREENSHOTS_DIR) / f"cookies_{session_id}.json"

    def to_domain(self) -> BrowserSession:
        return BrowserSession(
            session_id=self.session_id,
            status=self.status,
            tenant_url=self.tenant_url,
            created_at=self.created_at,
            last_used_at=self.last_used_at,
            current_url=self.current_url,
            authenticated=self.authenticated,
            metadata={},
        )

    def touch(self):
        self.last_used_at = datetime.utcnow()

    def is_expired(self) -> bool:
        ttl = timedelta(seconds=settings.BROWSER_SESSION_TTL_SECONDS)
        return datetime.utcnow() - self.last_used_at > ttl


class PlaywrightAdapter(BrowserPort):
    """
    Production Playwright adapter with connection pooling.
    Thread-safe via asyncio locks. READ-ONLY by design.
    """

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._sessions: Dict[str, PlaywrightBrowserSession] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

        os.makedirs(settings.SCREENSHOTS_DIR, exist_ok=True)
        os.makedirs(settings.BROWSER_TRACES_DIR, exist_ok=True)

    async def initialize(self) -> None:
        if self._initialized:
            return
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=settings.PLAYWRIGHT_HEADLESS,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        self._initialized = True
        logger.info("playwright_initialized", headless=settings.PLAYWRIGHT_HEADLESS)

    async def shutdown(self) -> None:
        for session_id in list(self._sessions.keys()):
            await self.close_session(session_id)
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("playwright_shutdown")

    async def create_session(self, tenant_url: str) -> BrowserSession:
        await self.initialize()

        async with self._lock:
            active = [s for s in self._sessions.values()
                      if s.status in (SessionStatus.ACTIVE, SessionStatus.IDLE, SessionStatus.INITIALIZING)]
            if len(active) >= settings.BROWSER_POOL_MAX_SIZE:
                raise BrowserPoolExhaustedError(
                    f"Browser pool exhausted (max={settings.BROWSER_POOL_MAX_SIZE}). "
                    "Close an existing session before creating a new one."
                )

        session_id = str(uuid.uuid4())
        session = PlaywrightBrowserSession(session_id, tenant_url)

        context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            ignore_https_errors=True,
            java_script_enabled=True,
        )

        # Restore cookies if available
        if session._cookie_file.exists():
            try:
                cookies = json.loads(session._cookie_file.read_text())
                await context.add_cookies(cookies)
                logger.info("session_cookies_restored", session_id=session_id)
            except Exception as e:
                logger.warning("cookie_restore_failed", session_id=session_id, error=str(e))

        session.context = context
        session.page = await context.new_page()
        session.page.set_default_timeout(settings.ORACLE_FUSION_NAV_TIMEOUT_MS)
        session.page.set_default_navigation_timeout(settings.ORACLE_FUSION_NAV_TIMEOUT_MS)

        self._sessions[session_id] = session

        # Attempt login
        await self._login(session)
        return session.to_domain()

    async def _login(self, session: PlaywrightBrowserSession) -> None:
        """Navigate to Oracle Fusion and authenticate."""
        page = session.page
        login_url = f"{session.tenant_url}/fscmUI/faces/FuseWelcome"

        for attempt in range(1, 4):
            try:
                logger.info("fusion_login_attempt", session_id=session.session_id, attempt=attempt)
                await page.goto(login_url, wait_until="networkidle", timeout=settings.ORACLE_FUSION_LOGIN_TIMEOUT_MS)

                # Check if already authenticated (cookie-based)
                if await self._is_authenticated(page):
                    session.authenticated = True
                    session.status = SessionStatus.ACTIVE
                    logger.info("session_already_authenticated", session_id=session.session_id)
                    return

                # Fill username
                username_selectors = [
                    'input[name="userid"]',
                    'input[id="userid"]',
                    'input[type="text"][autocomplete="username"]',
                    '#idcs-signin-basic-signin-form-username',
                ]
                await self._fill_field(page, username_selectors, settings.ORACLE_FUSION_USERNAME)

                # Click Next / Continue
                next_selectors = ['button[id*="nextButton"]', 'input[type="submit"]', 'button[type="submit"]']
                for sel in next_selectors:
                    try:
                        await page.click(sel, timeout=3000)
                        break
                    except Exception:
                        continue

                await page.wait_for_timeout(1000)

                # Fill password
                password_selectors = [
                    'input[name="password"]',
                    'input[type="password"]',
                    '#idcs-signin-basic-signin-form-password',
                ]
                await self._fill_field(page, password_selectors, settings.ORACLE_FUSION_PASSWORD)

                # Submit
                submit_selectors = [
                    'button[id*="signInButton"]',
                    'button[type="submit"]',
                    'input[type="submit"]',
                ]
                for sel in submit_selectors:
                    try:
                        await page.click(sel, timeout=3000)
                        break
                    except Exception:
                        continue

                await page.wait_for_load_state("networkidle", timeout=settings.ORACLE_FUSION_LOGIN_TIMEOUT_MS)

                # Check for MFA
                mfa_indicators = ['input[id*="mfa"]', '[class*="mfa"]', 'input[id*="otp"]', 'input[name*="factor"]']
                for sel in mfa_indicators:
                    try:
                        await page.wait_for_selector(sel, timeout=2000)
                        session.status = SessionStatus.MFA_PENDING
                        raise MFARequiredException("MFA challenge detected. Provide OTP to continue.")
                    except PlaywrightTimeout:
                        continue

                # Validate login success
                if await self._is_authenticated(page):
                    session.authenticated = True
                    session.status = SessionStatus.ACTIVE
                    # Save cookies
                    cookies = await session.context.cookies()
                    session._cookie_file.write_text(json.dumps(cookies))
                    logger.info("fusion_login_success", session_id=session.session_id)
                    return

                raise LoginFailedError(f"Login validation failed after attempt {attempt}")

            except MFARequiredException:
                raise
            except LoginFailedError:
                if attempt == 3:
                    raise
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                if attempt == 3:
                    session.status = SessionStatus.ERROR
                    raise LoginFailedError(f"Login failed: {str(e)}")
                await asyncio.sleep(2 ** attempt)

    async def _is_authenticated(self, page: Page) -> bool:
        """Check if the current session is authenticated."""
        auth_indicators = [
            '.oj-navigationlist',
            '#fndCLovDialogContainer',
            '.AFMaskingPane',
            '[data-nav-type]',
            '.oj-flex-item',
        ]
        for sel in auth_indicators:
            try:
                await page.wait_for_selector(sel, timeout=2000)
                return True
            except PlaywrightTimeout:
                continue
        # Fallback: check URL
        current_url = page.url
        return "FuseWelcome" in current_url or "/homePage" in current_url

    async def _fill_field(self, page: Page, selectors: List[str], value: str) -> None:
        """Try multiple selectors to fill a form field."""
        for sel in selectors:
            try:
                await page.wait_for_selector(sel, timeout=3000)
                await page.fill(sel, value)
                return
            except Exception:
                continue
        raise LoginFailedError(f"Could not find input field using selectors: {selectors}")

    async def close_session(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if not session:
            return
        try:
            if session.context:
                await session.context.close()
            if session._cookie_file.exists():
                session._cookie_file.unlink()
        except Exception as e:
            logger.warning("session_close_error", session_id=session_id, error=str(e))
        finally:
            self._sessions.pop(session_id, None)
            logger.info("session_closed", session_id=session_id)

    async def get_session(self, session_id: str) -> Optional[BrowserSession]:
        session = self._sessions.get(session_id)
        return session.to_domain() if session else None

    async def navigate_to(self, session_id: str, url: str) -> PageSnapshot:
        session = self._get_active_session(session_id)
        session.touch()
        page = session.page

        try:
            await page.goto(url, wait_until="networkidle", timeout=settings.ORACLE_FUSION_NAV_TIMEOUT_MS)
            await page.wait_for_timeout(2000)  # Wait for dynamic content

            title = await page.title()
            content = await page.inner_text("body")
            session.current_url = page.url

            screenshot_bytes = await self.capture_screenshot(session_id)

            return PageSnapshot(
                url=page.url,
                title=title,
                content=content[:10000],  # Limit to 10k chars
                html_structure="",
                screenshot_bytes=screenshot_bytes,
                extracted_data={},
                captured_at=datetime.utcnow(),
                page_type="generic",
            )
        except PlaywrightTimeout:
            raise NavigationError(f"Timeout navigating to {url}")
        except Exception as e:
            raise NavigationError(f"Navigation failed: {str(e)}")

    async def capture_screenshot(self, session_id: str, full_page: bool = True) -> bytes:
        session = self._get_active_session(session_id)
        try:
            screenshot = await session.page.screenshot(
                full_page=full_page,
                type="png",
            )
            return screenshot
        except Exception as e:
            raise ScreenshotError(f"Screenshot failed: {str(e)}")

    async def extract_page_data(self, session_id: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        session = self._get_active_session(session_id)
        result = {}
        for key, selector in selectors.items():
            try:
                element = await session.page.query_selector(selector)
                if element:
                    result[key] = await element.inner_text()
                else:
                    result[key] = None
            except Exception:
                result[key] = None
        return result

    async def wait_for_selector(self, session_id: str, selector: str, timeout_ms: int = 10000) -> bool:
        session = self._get_active_session(session_id)
        try:
            await session.page.wait_for_selector(selector, timeout=timeout_ms)
            return True
        except PlaywrightTimeout:
            return False

    async def get_active_sessions(self) -> List[BrowserSession]:
        # Evict expired sessions
        expired = [sid for sid, s in self._sessions.items() if s.is_expired()]
        for sid in expired:
            await self.close_session(sid)
        return [s.to_domain() for s in self._sessions.values()]

    def _get_active_session(self, session_id: str) -> PlaywrightBrowserSession:
        session = self._sessions.get(session_id)
        if not session:
            raise BrowserSessionError(f"Session {session_id} not found")
        if session.status == SessionStatus.ERROR:
            raise BrowserSessionError(f"Session {session_id} is in error state")
        return session


# Singleton adapter instance
_adapter: Optional[PlaywrightAdapter] = None


def get_browser_adapter() -> PlaywrightAdapter:
    global _adapter
    if _adapter is None:
        _adapter = PlaywrightAdapter()
    return _adapter
