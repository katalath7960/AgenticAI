"""Functional test case generators — valid, invalid, boundary, required."""

from __future__ import annotations

from analyzer.models import FormAnalysis, PageAnalysis
from generator.models import Priority, Severity, TestCase, TestCategory

_counter = 0


def _next_id() -> str:
    global _counter
    _counter += 1
    return f"TC-FUNC-{_counter:03d}"


def generate_functional_tests(analysis: PageAnalysis) -> list[TestCase]:
    tests: list[TestCase] = []
    for fa in analysis.form_analyses:
        tests.extend(_valid_input_tests(fa, analysis.url))
        tests.extend(_invalid_input_tests(fa, analysis.url))
        tests.extend(_boundary_tests(fa, analysis.url))
        tests.extend(_required_field_tests(fa, analysis.url))
    return tests


def _valid_input_tests(fa: FormAnalysis, url: str) -> list[TestCase]:
    if not fa.form.fields:
        return []
    steps = [f"Navigate to {url}"]
    for f in fa.form.fields:
        sample = _sample_valid(f.field_type, f.name)
        steps.append(f"Enter '{sample}' in field '{f.name}' ({f.field_type})")
    steps.append("Click submit")

    return [TestCase(
        id=_next_id(),
        category=TestCategory.FUNCTIONAL,
        description=f"Submit form with all valid inputs on {url}",
        preconditions=["Page is loaded", "User is on the correct page"],
        steps=steps,
        expected="Form submits successfully without errors",
        priority=Priority.HIGH,
        severity=Severity.MAJOR,
        page_url=url,
        element_ref=fa.form.selector,
    )]


def _invalid_input_tests(fa: FormAnalysis, url: str) -> list[TestCase]:
    tests = []
    for f in fa.form.fields:
        if f.field_type in ("hidden", "submit", "button"):
            continue
        invalid_val = _sample_invalid(f.field_type)
        tests.append(TestCase(
            id=_next_id(),
            category=TestCategory.FUNCTIONAL,
            description=f"Enter invalid value in '{f.name}' ({f.field_type})",
            preconditions=["Page is loaded"],
            steps=[
                f"Navigate to {url}",
                f"Enter '{invalid_val}' in field '{f.name}'",
                "Click submit",
            ],
            expected=f"Validation error shown for field '{f.name}'",
            priority=Priority.MEDIUM,
            severity=Severity.MINOR,
            page_url=url,
            element_ref=f.selector,
        ))
    return tests


def _boundary_tests(fa: FormAnalysis, url: str) -> list[TestCase]:
    tests = []
    for f in fa.form.fields:
        if f.min_length is not None:
            tests.append(TestCase(
                id=_next_id(),
                category=TestCategory.FUNCTIONAL,
                description=f"Boundary: enter {f.min_length - 1} chars in '{f.name}' (below min)",
                preconditions=["Page is loaded"],
                steps=[
                    f"Navigate to {url}",
                    f"Enter {'x' * max(f.min_length - 1, 0)} in field '{f.name}'",
                    "Click submit",
                ],
                expected="Validation error for minimum length",
                priority=Priority.MEDIUM,
                severity=Severity.MINOR,
                page_url=url,
                element_ref=f.selector,
            ))
            tests.append(TestCase(
                id=_next_id(),
                category=TestCategory.FUNCTIONAL,
                description=f"Boundary: enter exactly {f.min_length} chars in '{f.name}' (at min)",
                preconditions=["Page is loaded"],
                steps=[
                    f"Navigate to {url}",
                    f"Enter {'x' * f.min_length} in field '{f.name}'",
                    "Click submit",
                ],
                expected="Field accepts the value (at minimum length)",
                priority=Priority.LOW,
                severity=Severity.TRIVIAL,
                page_url=url,
                element_ref=f.selector,
            ))
        if f.max_length is not None:
            tests.append(TestCase(
                id=_next_id(),
                category=TestCategory.FUNCTIONAL,
                description=f"Boundary: enter {f.max_length + 1} chars in '{f.name}' (above max)",
                preconditions=["Page is loaded"],
                steps=[
                    f"Navigate to {url}",
                    f"Enter {'x' * (f.max_length + 1)} in field '{f.name}'",
                    "Click submit",
                ],
                expected="Input truncated or validation error for maximum length",
                priority=Priority.MEDIUM,
                severity=Severity.MINOR,
                page_url=url,
                element_ref=f.selector,
            ))
    return tests


def _required_field_tests(fa: FormAnalysis, url: str) -> list[TestCase]:
    tests = []
    required_fields = [f for f in fa.form.fields if f.required]
    for f in required_fields:
        tests.append(TestCase(
            id=_next_id(),
            category=TestCategory.FUNCTIONAL,
            description=f"Leave required field '{f.name}' empty and submit",
            preconditions=["Page is loaded"],
            steps=[
                f"Navigate to {url}",
                f"Leave field '{f.name}' empty",
                "Fill all other required fields with valid data",
                "Click submit",
            ],
            expected=f"Validation error displayed for required field '{f.name}'",
            priority=Priority.HIGH,
            severity=Severity.MAJOR,
            page_url=url,
            element_ref=f.selector,
        ))
    return tests


def _sample_valid(field_type: str, name: str) -> str:
    name_lower = name.lower()
    if field_type == "email" or "email" in name_lower:
        return "test@example.com"
    if field_type == "password" or "password" in name_lower:
        return "P@ssw0rd123"
    if field_type == "tel" or "phone" in name_lower:
        return "+1-555-0100"
    if field_type == "number":
        return "42"
    if field_type == "url":
        return "https://example.com"
    if field_type == "date":
        return "2025-01-15"
    return "Test Value"


def _sample_invalid(field_type: str) -> str:
    mapping = {
        "email": "not-an-email",
        "number": "abc",
        "tel": "not-a-phone",
        "url": "not-a-url",
        "date": "99-99-9999",
    }
    return mapping.get(field_type, "")
