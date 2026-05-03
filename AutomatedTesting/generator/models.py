"""Test case data models."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TestCategory(str, Enum):
    FUNCTIONAL = "Functional"
    SECURITY = "Security"
    WORKFLOW = "Workflow"
    NEGATIVE = "Negative"


class Priority(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class Severity(str, Enum):
    BLOCKER = "Blocker"
    MAJOR = "Major"
    MINOR = "Minor"
    TRIVIAL = "Trivial"


class TestCase(BaseModel):
    id: str
    category: TestCategory
    description: str
    preconditions: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    expected: str
    priority: Priority = Priority.MEDIUM
    severity: Severity = Severity.MINOR
    page_url: str = ""
    element_ref: str = ""


class TestSuite(BaseModel):
    site_url: str
    test_cases: list[TestCase] = Field(default_factory=list)

    @property
    def by_category(self) -> dict[str, list[TestCase]]:
        result: dict[str, list[TestCase]] = {}
        for tc in self.test_cases:
            result.setdefault(tc.category.value, []).append(tc)
        return result

    @property
    def summary(self) -> dict[str, int]:
        counts = {}
        for tc in self.test_cases:
            counts[tc.category.value] = counts.get(tc.category.value, 0) + 1
        return counts
