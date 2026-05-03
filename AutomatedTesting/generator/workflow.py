"""Workflow / E2E test generators — user journeys and navigation checks."""

from __future__ import annotations

import json
import logging

from openai import OpenAI

from analyzer.models import SiteAnalysis
from generator.models import Priority, Severity, TestCase, TestCategory

log = logging.getLogger("autotester")

_counter = 0


def _next_id() -> str:
    global _counter
    _counter += 1
    return f"TC-WF-{_counter:03d}"


JOURNEY_PROMPT = """\
You are a QA engineer. Given the following website structure, identify 3-5 key
user journeys (end-to-end scenarios). For each journey, provide:
- description: one-line summary
- steps: ordered list of user actions
- expected: what the user should see at the end

Website: {url}
Pages and their forms:
{pages_summary}

Return JSON: {{"journeys": [{{"description": "...", "steps": ["..."], "expected": "..."}}]}}
"""


def generate_workflow_tests(analysis: SiteAnalysis, api_key: str = "", model: str = "gpt-4o-mini") -> list[TestCase]:
    tests: list[TestCase] = []
    tests.extend(_navigation_tests(analysis))
    tests.extend(_broken_link_tests(analysis))
    tests.extend(_ai_journey_tests(analysis, api_key, model))
    return tests


def _navigation_tests(analysis: SiteAnalysis) -> list[TestCase]:
    tests = []
    all_links: set[str] = set()
    for page in analysis.pages:
        for link in page.internal_links:
            all_links.add(link)

    if all_links:
        tests.append(TestCase(
            id=_next_id(),
            category=TestCategory.WORKFLOW,
            description=f"Verify all {len(all_links)} internal links return HTTP 200",
            preconditions=["Site is accessible"],
            steps=[
                f"Navigate to {analysis.root_url}",
                f"Visit each of the {len(all_links)} discovered internal links",
                "Verify each returns a successful response (200 OK)",
            ],
            expected="All internal links resolve to valid pages",
            priority=Priority.HIGH,
            severity=Severity.MAJOR,
            page_url=analysis.root_url,
        ))
    return tests


def _broken_link_tests(analysis: SiteAnalysis) -> list[TestCase]:
    tests = []
    for link in analysis.broken_links:
        tests.append(TestCase(
            id=_next_id(),
            category=TestCategory.WORKFLOW,
            description=f"Broken link detected: {link}",
            preconditions=["Site is accessible"],
            steps=[f"Navigate to {link}"],
            expected="Page should load (currently returning error)",
            priority=Priority.MEDIUM,
            severity=Severity.MINOR,
            page_url=link,
        ))
    return tests


def _ai_journey_tests(analysis: SiteAnalysis, api_key: str, model: str) -> list[TestCase]:
    if not api_key:
        return _fallback_journeys(analysis)

    pages_summary = "\n".join(
        f"- {p.url}: title='{p.title}', forms={len(p.form_analyses)}, "
        f"links={len(p.internal_links)}, login={'yes' if any(fa.is_login_form for fa in p.form_analyses) else 'no'}"
        for p in analysis.pages
    )

    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a QA engineer. Return only valid JSON."},
                {"role": "user", "content": JOURNEY_PROMPT.format(
                    url=analysis.root_url, pages_summary=pages_summary
                )},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content)
        journeys = data.get("journeys", [])

        tests = []
        for j in journeys:
            tests.append(TestCase(
                id=_next_id(),
                category=TestCategory.WORKFLOW,
                description=j["description"],
                preconditions=["User starts from the home page"],
                steps=j["steps"],
                expected=j["expected"],
                priority=Priority.HIGH,
                severity=Severity.MAJOR,
                page_url=analysis.root_url,
            ))
        return tests
    except Exception as exc:
        log.warning("AI journey generation failed: %s", exc)
        return _fallback_journeys(analysis)


def _fallback_journeys(analysis: SiteAnalysis) -> list[TestCase]:
    tests = []
    has_login = any(fa.is_login_form for p in analysis.pages for fa in p.form_analyses)
    pages_with_forms = [p for p in analysis.pages if p.form_analyses]

    if has_login and len(analysis.pages) > 1:
        tests.append(TestCase(
            id=_next_id(),
            category=TestCategory.WORKFLOW,
            description="Login → navigate to inner pages → logout",
            preconditions=["Valid test credentials available"],
            steps=[
                f"Navigate to {analysis.root_url}",
                "Log in with valid credentials",
                "Navigate to at least 2 inner pages",
                "Verify page content loads correctly",
                "Log out",
            ],
            expected="User can complete full login → browse → logout flow",
            priority=Priority.CRITICAL,
            severity=Severity.BLOCKER,
            page_url=analysis.root_url,
        ))

    for p in pages_with_forms[:3]:
        for fa in p.form_analyses:
            if not fa.is_login_form:
                tests.append(TestCase(
                    id=_next_id(),
                    category=TestCategory.WORKFLOW,
                    description=f"Fill and submit form on {p.url}",
                    preconditions=["Page is accessible"],
                    steps=[
                        f"Navigate to {p.url}",
                        "Fill all fields with valid data",
                        "Submit the form",
                        "Verify success message or redirect",
                    ],
                    expected="Form processes successfully, user sees confirmation",
                    priority=Priority.HIGH,
                    severity=Severity.MAJOR,
                    page_url=p.url,
                    element_ref=fa.form.selector,
                ))
    return tests
