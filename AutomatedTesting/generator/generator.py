"""Master test generator — orchestrates all category generators."""

from __future__ import annotations

import logging

from analyzer.models import SiteAnalysis
from generator.functional import generate_functional_tests
from generator.models import TestSuite
from generator.negative import generate_negative_tests, generate_route_tests
from generator.security import generate_security_tests
from generator.workflow import generate_workflow_tests

log = logging.getLogger("autotester")


def generate_test_suite(
    analysis: SiteAnalysis,
    api_key: str = "",
    ai_model: str = "gpt-4o-mini",
    include_security: bool = False,
) -> TestSuite:
    suite = TestSuite(site_url=analysis.root_url)

    for page in analysis.pages:
        suite.test_cases.extend(generate_functional_tests(page))
        suite.test_cases.extend(generate_negative_tests(page))
        if include_security:
            suite.test_cases.extend(generate_security_tests(page))

    suite.test_cases.extend(generate_workflow_tests(analysis, api_key=api_key, model=ai_model))
    suite.test_cases.extend(generate_route_tests(analysis))

    log.info(
        "Generated %d test cases: %s",
        len(suite.test_cases),
        suite.summary,
    )
    return suite
