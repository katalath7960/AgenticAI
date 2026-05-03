"""Generate API test scripts from detected API endpoints."""

from __future__ import annotations

from pathlib import Path

from analyzer.models import SiteAnalysis

HEADER = '''\
"""Auto-generated API tests for {url}."""

import httpx
import pytest

BASE_URL = "{base_url}"


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=10) as c:
        yield c

'''

TEST_TEMPLATE = '''
def test_api_{idx}_{method}(client):
    """Test {method} {path}"""
    resp = client.request("{method}", "{path}")
    assert resp.status_code < 500, f"Server error: {{resp.status_code}}"


def test_api_{idx}_{method}_invalid_payload(client):
    """Negative: send invalid payload to {method} {path}"""
    resp = client.request("{method}", "{path}", json={{"invalid_key": "invalid_value"}})
    assert resp.status_code < 500, f"Server error: {{resp.status_code}}"

'''


def generate_api_tests(analysis: SiteAnalysis, output_dir: Path) -> Path | None:
    all_endpoints: list[tuple[str, str]] = []
    for page in analysis.pages:
        for ep in page.api_endpoints:
            path = ep.replace(analysis.root_url, "")
            if not path.startswith("/"):
                path = "/" + path
            all_endpoints.append(("GET", path))
        for api_call in []:
            pass

    if not all_endpoints:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "test_api.py"

    lines = [HEADER.format(url=analysis.root_url, base_url=analysis.root_url)]
    seen = set()
    for idx, (method, endpoint) in enumerate(all_endpoints):
        key = f"{method}:{endpoint}"
        if key in seen:
            continue
        seen.add(key)
        lines.append(TEST_TEMPLATE.format(idx=idx, method=method, path=endpoint))

    path.write_text("".join(lines), encoding="utf-8")
    return path
