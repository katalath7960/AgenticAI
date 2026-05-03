"""Network traffic interception — capture XHR/fetch API calls."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from playwright.async_api import Page, Request, Response

from crawler.models import APICall

log = logging.getLogger("autotester")


class NetworkInterceptor:
    def __init__(self):
        self.calls: list[APICall] = []
        self._base_domain: str = ""

    def attach(self, page: Page, base_url: str) -> None:
        self._base_domain = urlparse(base_url).netloc
        self.calls = []
        page.on("response", self._on_response)

    async def _on_response(self, response: Response) -> None:
        request: Request = response.request
        if request.resource_type not in ("xhr", "fetch"):
            return
        url = request.url
        if urlparse(url).netloc != self._base_domain:
            return
        self.calls.append(APICall(
            url=url,
            method=request.method,
            request_headers=dict(request.headers),
            response_status=response.status,
            content_type=response.headers.get("content-type", ""),
        ))
        log.debug("API call captured: %s %s → %d", request.method, url, response.status)
