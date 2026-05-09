"""Oracle Fusion login page object."""
from app.infrastructure.browser.page_objects.base_page import BasePage, ExtractedPageData


class LoginPage(BasePage):
    """Handles Oracle Fusion / IdCS login flow."""

    USERNAME_SELECTORS = [
        'input[name="userid"]',
        'input[id="userid"]',
        '#idcs-signin-basic-signin-form-username',
        'input[autocomplete="username"]',
    ]
    PASSWORD_SELECTORS = [
        'input[name="password"]',
        'input[type="password"]',
        '#idcs-signin-basic-signin-form-password',
    ]
    SUBMIT_SELECTORS = [
        'button[id*="signIn"]',
        'button[type="submit"]',
        'input[type="submit"]',
    ]

    async def extract(self) -> ExtractedPageData:
        title = await self.page.title()
        return ExtractedPageData(
            page_type="login",
            url=self.page.url,
            title=title,
            raw_text="Login page",
            structured_data={"page": "login"},
        )
