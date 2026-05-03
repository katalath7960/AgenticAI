"""Security test case generators — SQLi, XSS, auth/authz."""

from __future__ import annotations

from analyzer.models import PageAnalysis
from generator.models import Priority, Severity, TestCase, TestCategory

_counter = 0

SQLI_PAYLOADS = [
    "' OR 1=1 --",
    '"; DROP TABLE users; --',
    "' UNION SELECT NULL,NULL--",
    "1' AND '1'='1",
    "admin'--",
]

XSS_PAYLOADS = [
    "<script>alert('XSS')</script>",
    '<img src=x onerror="alert(1)">',
    "javascript:alert(1)",
    '"><script>alert(document.cookie)</script>',
    "<svg/onload=alert(1)>",
]


def _next_id() -> str:
    global _counter
    _counter += 1
    return f"TC-SEC-{_counter:03d}"


def generate_security_tests(analysis: PageAnalysis) -> list[TestCase]:
    tests: list[TestCase] = []
    for fa in analysis.form_analyses:
        tests.extend(_sqli_tests(fa, analysis.url))
        tests.extend(_xss_tests(fa, analysis.url))
    tests.extend(_auth_tests(analysis))
    return tests


def _sqli_tests(fa, url: str) -> list[TestCase]:
    tests = []
    text_fields = [f for f in fa.form.fields if f.field_type in ("text", "email", "search", "textarea", "password")]
    for field in text_fields:
        for payload in SQLI_PAYLOADS[:3]:
            tests.append(TestCase(
                id=_next_id(),
                category=TestCategory.SECURITY,
                description=f"SQL injection in '{field.name}': {payload[:30]}",
                preconditions=["Page is loaded", "Security testing is authorized"],
                steps=[
                    f"Navigate to {url}",
                    f"Enter '{payload}' in field '{field.name}'",
                    "Submit the form",
                ],
                expected="No SQL error exposed, input sanitized, no data leak",
                priority=Priority.CRITICAL,
                severity=Severity.BLOCKER,
                page_url=url,
                element_ref=field.selector,
            ))
    return tests


def _xss_tests(fa, url: str) -> list[TestCase]:
    tests = []
    text_fields = [f for f in fa.form.fields if f.field_type in ("text", "textarea", "search")]
    for field in text_fields:
        for payload in XSS_PAYLOADS[:3]:
            tests.append(TestCase(
                id=_next_id(),
                category=TestCategory.SECURITY,
                description=f"XSS injection in '{field.name}': {payload[:30]}",
                preconditions=["Page is loaded", "Security testing is authorized"],
                steps=[
                    f"Navigate to {url}",
                    f"Enter '{payload}' in field '{field.name}'",
                    "Submit the form",
                    "Check the response/rendered page for unescaped script execution",
                ],
                expected="Input is sanitized, no script execution in browser",
                priority=Priority.CRITICAL,
                severity=Severity.BLOCKER,
                page_url=url,
                element_ref=field.selector,
            ))
    return tests


def _auth_tests(analysis: PageAnalysis) -> list[TestCase]:
    tests = []
    has_login = any(fa.is_login_form for fa in analysis.form_analyses)

    if has_login:
        tests.append(TestCase(
            id=_next_id(),
            category=TestCategory.SECURITY,
            description="Access protected pages without authentication",
            preconditions=["User is NOT logged in"],
            steps=[
                "Clear all cookies and session data",
                f"Navigate directly to {analysis.url}",
                "Attempt to access pages that require authentication",
            ],
            expected="Redirected to login page or shown 401/403 error",
            priority=Priority.CRITICAL,
            severity=Severity.BLOCKER,
            page_url=analysis.url,
        ))
        tests.append(TestCase(
            id=_next_id(),
            category=TestCategory.SECURITY,
            description="Test session expiry after logout",
            preconditions=["User was logged in and then logged out"],
            steps=[
                "Log in with valid credentials",
                "Log out",
                "Press browser back button",
                "Try to access a protected resource",
            ],
            expected="Session is invalidated, access denied",
            priority=Priority.HIGH,
            severity=Severity.MAJOR,
            page_url=analysis.url,
        ))

    return tests
