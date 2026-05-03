"""Playwright-based page loader with JS rendering support."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from playwright.async_api import Browser, Page, async_playwright

from config.settings import Settings

log = logging.getLogger("autotester")


class BrowserManager:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._pw = None
        self._browser: Optional[Browser] = None

    async def start(self) -> None:
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=self._settings.headless)
        log.info("Browser launched (headless=%s)", self._settings.headless)

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()

    async def new_page(self) -> Page:
        ctx = await self._browser.new_context(
            viewport={"width": 1280, "height": 720},
            ignore_https_errors=True,
        )
        return await ctx.new_page()

    async def load_page(self, page: Page, url: str) -> str:
        try:
            await page.goto(url, wait_until="networkidle", timeout=self._settings.timeout_ms)
        except Exception:
            await page.goto(url, wait_until="domcontentloaded", timeout=self._settings.timeout_ms)
        return await page.content()

    async def screenshot(self, page: Page, url: str, output_dir: Path) -> str:
        output_dir.mkdir(parents=True, exist_ok=True)
        slug = urlparse(url).path.strip("/").replace("/", "_") or "index"
        path = output_dir / f"{slug}.png"
        await page.screenshot(path=str(path), full_page=True)
        return str(path)
