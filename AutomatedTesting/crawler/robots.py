"""robots.txt parser — checks whether a path is allowed before crawling."""

from __future__ import annotations

import logging
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx

log = logging.getLogger("autotester")


class RobotsChecker:
    def __init__(self, base_url: str, respect: bool = True):
        self._respect = respect
        self._parser = RobotFileParser()
        self._loaded = False
        self._base = base_url

    async def load(self) -> None:
        if not self._respect:
            self._loaded = True
            return
        robots_url = urljoin(self._base, "/robots.txt")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(robots_url)
            if resp.status_code == 200:
                self._parser.parse(resp.text.splitlines())
                log.info("Loaded robots.txt from %s", robots_url)
            else:
                log.info("No robots.txt found (status %d) — all paths allowed", resp.status_code)
        except Exception as exc:
            log.warning("Failed to fetch robots.txt: %s", exc)
        self._loaded = True

    def is_allowed(self, url: str) -> bool:
        if not self._respect:
            return True
        path = urlparse(url).path
        return self._parser.can_fetch("*", path)
