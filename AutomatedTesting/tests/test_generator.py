"""Tests for test case generators."""

from analyzer.forms import analyze_form
from analyzer.models import FormAnalysis, PageAnalysis
from crawler.models import FormField, FormInfo
from generator.functional import generate_functional_tests
from generator.negative import generate_negative_tests
from generator.security import generate_security_tests
from generator.models import TestCategory


def _make_page_analysis() -> PageAnalysis:
    form = FormInfo(
        action="/login",
        method="POST",
        fields=[
            FormField(name="email", field_type="email", required=True, min_length=5, max_length=100, selector="input[name='email']"),
            FormField(name="password", field_type="password", required=True, selector="input[name='password']"),
        ],
        submit_selector="button[type='submit']",
        selector="form",
    )
    fa = analyze_form(form)
    return PageAnalysis(
        url="http://test.com/login",
        title="Login",
        form_analyses=[fa],
    )


def test_functional_tests_generated():
    page = _make_page_analysis()
    tests = generate_functional_tests(page)
    assert len(tests) > 0
    assert all(tc.category == TestCategory.FUNCTIONAL for tc in tests)


def test_valid_input_test_created():
    page = _make_page_analysis()
    tests = generate_functional_tests(page)
    valid_tests = [t for t in tests if "valid" in t.description.lower()]
    assert len(valid_tests) >= 1


def test_boundary_tests_for_minmax():
    page = _make_page_analysis()
    tests = generate_functional_tests(page)
    boundary = [t for t in tests if "boundary" in t.description.lower()]
    assert len(boundary) >= 2


def test_required_field_tests():
    page = _make_page_analysis()
    tests = generate_functional_tests(page)
    required = [t for t in tests if "required" in t.description.lower()]
    assert len(required) == 2


def test_negative_tests_generated():
    page = _make_page_analysis()
    tests = generate_negative_tests(page)
    assert len(tests) > 0
    assert all(tc.category == TestCategory.NEGATIVE for tc in tests)


def test_security_tests_generated():
    page = _make_page_analysis()
    tests = generate_security_tests(page)
    assert len(tests) > 0
    sqli = [t for t in tests if "SQL" in t.description]
    assert len(sqli) > 0
