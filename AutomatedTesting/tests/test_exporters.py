"""Tests for export modules."""

import json
from pathlib import Path

from generator.models import Priority, Severity, TestCase, TestCategory, TestSuite
from output.exporters.json_export import export_json
from output.exporters.excel_export import export_csv, export_excel
from output.exporters.html_report import export_html


def _make_suite() -> TestSuite:
    return TestSuite(
        site_url="http://test.com",
        test_cases=[
            TestCase(
                id="TC-001",
                category=TestCategory.FUNCTIONAL,
                description="Test something",
                steps=["Step 1", "Step 2"],
                expected="It works",
                priority=Priority.HIGH,
                severity=Severity.MAJOR,
                page_url="http://test.com",
            ),
            TestCase(
                id="TC-002",
                category=TestCategory.NEGATIVE,
                description="Test negative",
                steps=["Break it"],
                expected="Error shown",
            ),
        ],
    )


def test_json_export(tmp_path: Path):
    suite = _make_suite()
    path = export_json(suite, tmp_path)
    assert path.exists()
    data = json.loads(path.read_text())
    assert len(data["test_cases"]) == 2


def test_csv_export(tmp_path: Path):
    suite = _make_suite()
    path = export_csv(suite, tmp_path)
    assert path.exists()
    content = path.read_text()
    assert "TC-001" in content
    assert "TC-002" in content


def test_excel_export(tmp_path: Path):
    suite = _make_suite()
    path = export_excel(suite, tmp_path)
    assert path.exists()
    assert path.suffix == ".xlsx"


def test_html_export(tmp_path: Path):
    suite = _make_suite()
    path = export_html(suite, tmp_path)
    assert path.exists()
    html = path.read_text()
    assert "Test something" in html
    assert "TC-001" in html
