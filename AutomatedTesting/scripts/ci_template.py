"""Generate CI/CD workflow files."""

from __future__ import annotations

from pathlib import Path

GITHUB_ACTIONS_YAML = """\
name: Automated Tests
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r AutomatedTesting/requirements.txt
          playwright install chromium --with-deps

      - name: Run generated Playwright tests
        run: pytest AutomatedTesting/output/generated_tests/ -v --tb=short

      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-report
          path: AutomatedTesting/output/report.html
"""


def generate_ci_config(output_dir: Path) -> Path:
    ci_dir = output_dir / ".github" / "workflows"
    ci_dir.mkdir(parents=True, exist_ok=True)
    path = ci_dir / "test.yml"
    path.write_text(GITHUB_ACTIONS_YAML, encoding="utf-8")
    return path
