from playwright.async_api import BrowserContext, Page

from utilities.logger import get_logger

log = get_logger(test="TabManager")


class TabManager:
    def __init__(self, context: BrowserContext, initial_page: Page):
        self._context = context
        self._pages: list[Page] = [initial_page]
        context.on("page", self._on_new_page)

    def _on_new_page(self, page: Page):
        self._pages.append(page)
        log.info(f"New tab opened: {page.url!r} (total tabs: {len(self._pages)})")

    async def switch_to_tab(self, index: int) -> Page:
        await self._refresh()
        if index >= len(self._pages):
            raise IndexError(f"Tab index {index} out of range ({len(self._pages)} tabs open)")
        page = self._pages[index]
        await page.bring_to_front()
        log.info(f"Switched to tab {index}: {page.url!r}")
        return page

    async def close_tab(self, index: int) -> Page:
        await self._refresh()
        page = self._pages.pop(index)
        await page.close()
        log.info(f"Closed tab {index}")
        return self._pages[-1]

    async def _refresh(self):
        self._pages = [p for p in self._context.pages]

    @property
    def current_page(self) -> Page:
        return self._pages[-1]
