"""Negative test case generators — missing inputs, malformed data, broken routes."""

from __future__ import annotations

from analyzer.models import PageAnalysis, SiteAnalysis
from generator.models import Priority, Severity, TestCase, TestCategory

_counter = 0


def _next_id() -> str:
    global _counter
    _counter += 1
    return f"TC-NEG-{_counter:03d}"


def generate_negative_tests(analysis: PageAnalysis) -> list[TestCase]:
    tests: list[TestCase] = []
    tests.extend(_missing_input_tests(analysis))
    tests.extend(_malformed_input_tests(analysis))
    return tests


def generate_route_tests(site_analysis: SiteAnalysis) -> list[TestCase]:
    tests: list[TestCase] = []
    tests.extend(_broken_route_tests(site_analysis))
    return tests


def _missing_input_tests(analysis: PageAnalysis) -> list[TestCase]:
    tests = []
    for fa in analysis.form_analyses:
        if fa.form.fields:
            tests.append(TestCase(
                id=_next_id(),
                category=TestCategory.NEGATIVE,
                description=f"Submit form completely empty on {analysis.url}",
                preconditions=["Page is loaded"],
                steps=[
                    f"Navigate to {analysis.url}",
                    "Leave all fields empty",
                    "Click submit",
                ],
                expected="Validation errors shown for required fields, form does not submit",
                priority=Priority.HIGH,
                severity=Severity.MAJOR,
                page_url=analysis.url,
                element_ref=fa.form.selector,
            ))
    return tests


def _malformed_input_tests(analysis: PageAnalysis) -> list[TestCase]:
    tests = []
    malformed = {
        "email": ("invalid-email", "abc@", "@domain.com", "user@.com"),
        "number": ("abc", "-999999", "1e999", "NaN"),
        "tel": ("abc", "12345678901234567890"),
        "url": ("not-a-url", "://missing-scheme"),
        "date": ("99-99-9999", "not-a-date", "2025-13-32"),
    }

    for fa in analysis.form_analyses:
        for field in fa.form.fields:
            values = malformed.get(field.field_type, ())
            for val in values[:2]:
                tests.append(TestCase(
                    id=_next_id(),
                    category=TestCategory.NEGATIVE,
                    description=f"Malformed '{field.field_type}' in '{field.name}': {val}",
                    preconditions=["Page is loaded"],
                    steps=[
                        f"Navigate to {analysis.url}",
                        f"Enter '{val}' in field '{field.name}'",
                        "Submit the form",
                    ],
                    expected="Validation error displayed, form not submitted",
                    priority=Priority.MEDIUM,
                    severity=Severity.MINOR,
                    page_url=analysis.url,
                    element_ref=field.selector,
                ))
    return tests


FUZZ_PATHS = [
    "/admin", "/wp-admin", "/api/v1/debug", "/.env",
    "/nonexistent-page-xyz", "/../../etc/passwd",
]


def _broken_route_tests(site_analysis: SiteAnalysis) -> list[TestCase]:
    tests = []
    for fuzz in FUZZ_PATHS:
        tests.append(TestCase(
            id=_next_id(),
            category=TestCategory.NEGATIVE,
            description=f"Access invalid/fuzz route: {fuzz}",
            preconditions=["Site is accessible"],
            steps=[f"Navigate to {site_analysis.root_url}{fuzz}"],
            expected="404 page displayed, no server errors or sensitive info exposed",
            priority=Priority.MEDIUM,
            severity=Severity.MINOR,
            page_url=f"{site_analysis.root_url}{fuzz}",
        ))
    return tests
