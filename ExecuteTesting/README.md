# AI-Powered Excel-Driven Test Automation Framework

An intelligent, production-ready test automation framework that reads manual test cases from Excel, interprets them using AI (Claude), executes them against a web application using Playwright, and produces comprehensive reports.

---

## Architecture

```
ExecuteTesting/
├── config/               # settings.yaml + .env
├── excel_reader/         # Read .xlsx files, write results back
├── executor/             # Orchestrate test execution
├── playwright_engine/    # Browser, page actions, waits, dialogs
├── ai_engine/            # NLP step interpretation, failure analysis
├── reports/              # HTML / PDF / JSON report generation
├── screenshots/          # Captured on failure (auto-created)
├── logs/                 # Run logs + flaky history (auto-created)
├── excel_inputs/         # Place your .xlsx test files here
├── utilities/            # Config loader, logger, helpers
└── main.py               # Entry point
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 2. Configure credentials
cp .env.example .env
# Edit .env with your credentials and Anthropic API key

# 3. Add test Excel files to excel_inputs/
python excel_inputs/create_sample.py   # generates sample file

# 4. Run
python main.py
```

---

## Excel Test Case Format

Your `.xlsx` files must contain these columns (names are flexible — see aliases in reader.py):

| TC_ID | Test Case Name | Preconditions | Steps | Expected Result |
|---|---|---|---|---|
| TC_001 | Login Test | App accessible | Login with valid username and password | User logged in |

**Steps** supports natural language and can contain multiple lines (one step per line).

---

## Supported Actions (AI-interpreted)

| Category | Actions |
|---|---|
| Authentication | login, logout |
| Navigation | navigate, click menu, click link |
| Form interaction | enter text, select dropdown, select radio, check checkbox |
| File operations | upload file, download file |
| Record management | add record, edit record, delete record, search records, save, cancel |
| Validation | validate text, validate URL, validate title, validate field value, validate table, validate error message, validate mandatory fields, validate navigation |
| Special | handle date picker, handle rich text editor |

---

## Configuration Reference (`config/settings.yaml`)

```yaml
app:
  url: "https://..."        # Target URL
  username: ...             # From .env
  password: ...             # From .env

browser:
  type: chromium            # chromium | firefox | webkit
  headless: false           # true = no visible window
  timeout_ms: 30000         # Element wait timeout

execution:
  retry_count: 3            # Retries per step
  screenshot_on_pass: false
  screenshot_on_fail: true
  continue_on_failure: true # Don't stop on first failure

ai:
  provider: anthropic
  model: claude-sonnet-4-6
```

---

## Output

After each run:

- **Excel files** updated in-place with `Status`, `Actual Result`, `Error`, `Screenshot`, `Execution Time`, `Failure Analysis` columns (color-coded: green=PASS, red=FAIL, yellow=SKIP).
- **HTML report** — fully self-contained report with summary, per-test details, AI failure analysis, flaky test flags.
- **PDF report** — identical to HTML, rendered by WeasyPrint.
- **JSON report** — machine-readable, suitable for CI/CD integration.

---

## AI Features

- **Natural language interpretation** — steps like "Click the Save button on the Add Case form" are parsed into structured actions automatically.
- **Caching** — interpreted steps are cached by hash; repeated steps don't consume AI API quota.
- **Failure analysis** — AI explains probable cause and suggests fixes for each failed step.
- **Flaky detection** — steps with mixed PASS/FAIL history across runs are flagged as flaky.
- **Fallback** — if the AI API is unavailable, keyword-based rule matching is used.

---

## Future Enhancements

- Parallel execution across multiple browsers
- CI/CD integration (GitHub Actions, Azure DevOps)
- BrowserStack / Sauce Labs remote execution
- Visual regression testing
- Accessibility testing (axe-core)
- API testing module
- Email / Slack report delivery
- Self-healing locators using DOM diffing

---

## Dependencies

See [requirements.txt](requirements.txt) for the full list. Key packages:

| Package | Purpose |
|---|---|
| playwright | Browser automation |
| anthropic | AI step interpretation |
| pandas / openpyxl | Excel read/write |
| Jinja2 | HTML report templating |
| weasyprint | PDF generation |
| loguru | Structured logging |
| tenacity | Retry logic |
