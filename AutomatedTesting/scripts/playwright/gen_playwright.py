"""Generate Playwright (Python + pytest) test scripts from test cases."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from generator.models import TestCase, TestCategory, TestSuite

HEADER = '''\
"""Auto-generated Playwright tests — {category} for {url}."""

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="module")
def browser_page(browser):
    page = browser.new_page()
    yield page
    page.close()

'''

FUNC_TEMPLATE = '''
def test_{safe_id}(browser_page: Page):
    """{description}"""
    page = browser_page
{steps}
'''


def generate_playwright_scripts(suite: TestSuite, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []

    by_cat = suite.by_category
    for cat_name, tests in by_cat.items():
        filename = f"test_{cat_name.lower()}.py"
        path = output_dir / filename
        url = suite.site_url

        lines = [HEADER.format(category=cat_name, url=url)]

        for tc in tests:
            safe_id = tc.id.lower().replace("-", "_")
            step_lines = _tc_to_steps(tc)
            lines.append(FUNC_TEMPLATE.format(
                safe_id=safe_id,
                description=tc.description.replace('"', '\\"'),
                steps=step_lines,
            ))

        path.write_text("".join(lines), encoding="utf-8")
        files.append(path)

    return files


def _tc_to_steps(tc: TestCase) -> str:
    lines = []
    for step in tc.steps:
        sl = step.lower()
        if "navigate to" in sl:
            url = step.split("Navigate to")[-1].split("navigate to")[-1].strip()
            lines.append(f'    page.goto("{url}")')
        elif "enter" in sl and "field" in sl:
            parts = step.split("'")
            value = parts[1] if len(parts) > 1 else "test"
            field = parts[3] if len(parts) > 3 else "input"
            lines.append(f'    page.fill("[name=\\"{field}\\"]", "{value}")')
        elif "click submit" in sl or "submit" in sl:
            selector = tc.element_ref or "button[type='submit']"
            lines.append(f'    page.click("{selector}")')
        elif "leave" in sl and "empty" in sl:
            lines.append("    # Leave field empty (no action needed)")
        else:
            lines.append(f"    # {step}")

    if not lines:
        lines.append(f'    page.goto("{tc.page_url}")')
        lines.append("    pass  # manual verification needed")

    return "\n".join(lines)
