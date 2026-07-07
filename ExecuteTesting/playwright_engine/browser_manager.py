from typing import Optional

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
)

from utilities.config_loader import config
from utilities.logger import get_logger

log = get_logger(test="BrowserManager")


class BrowserManager:
    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._console_errors: list[str] = []

    async def __aenter__(self) -> "BrowserManager":
        self._playwright = await async_playwright().start()
        browser_type = config.browser.type.lower()
        launcher = getattr(self._playwright, browser_type)

        log.info(f"Launching {browser_type} (headless={config.browser.headless})")
        self.browser = await launcher.launch(
            headless=config.browser.headless,
            slow_mo=config.browser.slow_mo_ms,
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True,
            ignore_https_errors=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        )
        self.page = await self.context.new_page()
        self.page.on("console", self._capture_console)
        self.page.set_default_timeout(config.browser.timeout_ms)
        return self

    async def __aexit__(self, *_):
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            log.warning(f"Browser teardown error: {e}")

    def _capture_console(self, msg):
        if msg.type in ("error", "warning"):
            self._console_errors.append(f"[{msg.type.upper()}] {msg.text}")

    def drain_console_errors(self) -> list[str]:
        errors = list(self._console_errors)
        self._console_errors.clear()
        return errors
