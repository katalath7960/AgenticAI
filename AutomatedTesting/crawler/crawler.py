"""BFS crawler — discovers pages, extracts elements, captures API calls."""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from pathlib import Path
from urllib.parse import urlparse

from config.settings import Settings
from crawler.auth import handle_login
from crawler.browser import BrowserManager
from crawler.extractor import extract_page_data
from crawler.models import SiteMap
from crawler.network import NetworkInterceptor
from crawler.robots import RobotsChecker

log = logging.getLogger("autotester")


async def crawl(settings: Settings) -> SiteMap:
    robots = RobotsChecker(settings.target_url, settings.respect_robots_txt)
    await robots.load()

    browser = BrowserManager(settings)
    await browser.start()

    site_map = SiteMap(root_url=settings.target_url)
    visited: set[str] = set()
    broken: list[str] = []
    queue: deque[tuple[str, int]] = deque()
    queue.append((settings.target_url, 0))

    base_domain = urlparse(settings.target_url).netloc
    delay = 1.0 / settings.rate_limit_rps
    screenshot_dir = Path(settings.output_dir) / "screenshots"

    page = await browser.new_page()

    if settings.login_credentials:
        await handle_login(page, settings.login_credentials)

    interceptor = NetworkInterceptor()

    while queue:
        url, depth = queue.popleft()
        normalized = _normalize(url)

        if normalized in visited:
            continue
        if depth > settings.max_depth:
            continue
        if urlparse(url).netloc != base_domain:
            continue
        if not robots.is_allowed(url):
            log.info("Blocked by robots.txt: %s", url)
            continue

        visited.add(normalized)
        log.info("Crawling [depth=%d]: %s", depth, url)

        interceptor.attach(page, settings.target_url)

        try:
            html = await browser.load_page(page, url)
        except Exception as exc:
            log.warning("Failed to load %s: %s", url, exc)
            broken.append(url)
            continue

        page_data = extract_page_data(html, url)
        page_data.api_calls = list(interceptor.calls)

        try:
            page_data.screenshot_path = await browser.screenshot(page, url, screenshot_dir)
        except Exception:
            pass

        site_map.pages.append(page_data)

        for link in page_data.links:
            link_norm = _normalize(link)
            if link_norm not in visited and urlparse(link).netloc == base_domain:
                queue.append((link, depth + 1))

        await asyncio.sleep(delay)

    await browser.stop()

    site_map.broken_links = broken
    site_map.total_links_found = len(visited)
    log.info("Crawl complete: %d pages, %d broken links", len(site_map.pages), len(broken))
    return site_map


def _normalize(url: str) -> str:
    p = urlparse(url)
    path = p.path.rstrip("/") or "/"
    return f"{p.scheme}://{p.netloc}{path}"
