import asyncio

from playwright.async_api import Page, Locator, TimeoutError as PWTimeout

from utilities.config_loader import config
from utilities.logger import get_logger

log = get_logger(test="WaitStrategy")

_SPINNER_SELECTORS = [
    ".loading", ".spinner", ".loader", "[aria-busy='true']",
    ".overlay", ".wait", "#loadingOverlay", ".ajax-loader",
]


async def wait_for_navigation(page: Page, timeout_ms: int | None = None) -> None:
    t = timeout_ms or config.browser.timeout_ms
    try:
        await page.wait_for_load_state("networkidle", timeout=t)
    except PWTimeout:
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=t)
        except PWTimeout:
            log.warning("Navigation wait timed out — continuing")


async def wait_for_element(
    locator: Locator,
    state: str = "visible",
    timeout_ms: int | None = None,
) -> bool:
    t = timeout_ms or config.browser.timeout_ms
    try:
        await locator.wait_for(state=state, timeout=t)
        return True
    except PWTimeout:
        return False


async def wait_for_spinner_gone(page: Page, timeout_ms: int | None = None) -> None:
    t = timeout_ms or config.browser.timeout_ms
    for selector in _SPINNER_SELECTORS:
        try:
            spinner = page.locator(selector)
            count = await spinner.count()
            if count > 0:
                await spinner.wait_for(state="hidden", timeout=t)
        except PWTimeout:
            pass
        except Exception:
            pass


async def wait_for_ajax(page: Page, settle_ms: int = 500) -> None:
    """Wait until no pending fetch/XHR requests for settle_ms."""
    script = """
    () => {
        if (typeof window.__pendingRequests === 'undefined') return true;
        return window.__pendingRequests === 0;
    }
    """
    deadline = asyncio.get_event_loop().time() + (config.browser.timeout_ms / 1000)
    while asyncio.get_event_loop().time() < deadline:
        try:
            idle = await page.evaluate(script)
            if idle:
                await asyncio.sleep(settle_ms / 1000)
                idle2 = await page.evaluate(script)
                if idle2:
                    return
        except Exception:
            return
        await asyncio.sleep(0.2)


async def smart_wait(page: Page) -> None:
    await wait_for_spinner_gone(page)
    await wait_for_ajax(page)
