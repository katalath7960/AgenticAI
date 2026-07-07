# TECHTESTSTACK — Technical Implementation Plan
## AI-Powered Excel-Driven Automated Testing Framework

---

## 1. High-Level Objective

Build a production-ready, AI-powered test automation framework in Python that:

- Reads manual test cases from Excel workbooks stored in a folder.
- Interprets each test step using an AI/NLP engine (natural language understanding).
- Executes the interpreted steps against the target web application using Playwright.
- Handles complex UI interactions (AJAX, modals, tabs, uploads, downloads, date pickers).
- Captures evidence (screenshots, console errors, HTML snapshots) on failures.
- Writes execution results back into the original Excel file (new columns only — no new file).
- Generates HTML, PDF, and JSON execution reports with a full summary.
- Is modular, configurable, and extensible for future enhancements (parallel execution, CI/CD, multi-browser).

**Target Website:** `https://qafjdforum.courts.phila.gov/`  
**Credentials:** Provided separately via config file (never hardcoded).

---

## 2. Prerequisites and Assumptions

### 2.1 Environment Prerequisites

| Requirement | Version / Notes |
|---|---|
| Python | 3.10+ |
| pip | Latest |
| Node.js | 18+ (required by Playwright) |
| Git | For version control |
| VS Code / PyCharm | Recommended IDE |
| Internet access | Required for Playwright browser download |
| OpenAI / Anthropic API key | For AI step interpretation (Claude or GPT-4) |

### 2.2 Python Dependencies (requirements.txt)

```
playwright>=1.44.0
pandas>=2.2.0
openpyxl>=3.1.2
pytest>=8.2.0
pytest-asyncio>=0.23.0
anthropic>=0.28.0          # or openai>=1.30.0
Jinja2>=3.1.4              # HTML report templating
weasyprint>=62.0           # PDF report generation
python-dotenv>=1.0.0       # .env config loading
loguru>=0.7.2              # structured logging
aiofiles>=23.2.0           # async file I/O
Pillow>=10.3.0             # image handling for screenshots
tenacity>=8.3.0            # retry logic
```

### 2.3 Assumptions

- Excel files follow a consistent column structure with at minimum: `Test Case`, `Steps`, `Expected Result` columns.
- Each sheet within a workbook represents a logical test suite.
- The AI API key is stored securely in a `.env` file or `config/settings.yaml` — never committed to source control.
- Playwright runs against Chromium by default; Edge and Firefox are future enhancements.
- A single login session is reused per workbook execution (not per test case).
- Screenshots are stored in `screenshots/` with unique filenames per step.

---

## 3. Project Folder Structure

```
ExecuteTesting/
├── config/
│   ├── settings.yaml            # All configurable values
│   └── .env                     # API keys (git-ignored)
├── excel_reader/
│   ├── __init__.py
│   ├── reader.py                # Reads all .xlsx files from folder
│   └── formatter.py            # Preserves and writes back formatting
├── executor/
│   ├── __init__.py
│   ├── base_executor.py        # Abstract base class for step execution
│   └── step_dispatcher.py      # Routes parsed steps to handlers
├── playwright_engine/
│   ├── __init__.py
│   ├── browser_manager.py      # Browser/context lifecycle
│   ├── page_actions.py         # click, type, select, upload, download, etc.
│   ├── wait_strategy.py        # Smart waits, AJAX detection
│   ├── dialog_handler.py       # Modals, alerts, confirm dialogs
│   └── tab_manager.py          # Multi-tab management
├── ai_engine/
│   ├── __init__.py
│   ├── step_interpreter.py     # NLP parsing of test step strings
│   ├── locator_strategy.py     # AI-based element identification
│   ├── failure_analyzer.py     # Root-cause suggestion for failures
│   └── flaky_detector.py       # Flakiness scoring across runs
├── reports/
│   ├── __init__.py
│   ├── html_reporter.py        # Jinja2 HTML report
│   ├── pdf_reporter.py         # WeasyPrint PDF from HTML
│   ├── json_reporter.py        # Structured JSON output
│   └── templates/
│       └── report_template.html
├── screenshots/                 # Auto-created at runtime
├── logs/                        # Auto-created at runtime
├── excel_inputs/                # Source Excel files (configurable path)
├── utilities/
│   ├── __init__.py
│   ├── file_utils.py
│   └── time_utils.py
├── tests/                       # Framework self-tests
│   └── test_reader.py
├── main.py                      # Entry point
├── requirements.txt
├── README.md
├── INSTALLATION.md
├── TESTSTACK.MD                 # Original requirements
└── TECHTESTSTACK.md             # This document
```

---

## 4. Phased Implementation Approach

| Phase | Name | Focus | Estimated Effort |
|---|---|---|---|
| Phase 1 | Foundation | Environment, config, logging | 1 day |
| Phase 2 | Excel Reader | Read/write test cases and results | 1 day |
| Phase 3 | Playwright Core | Browser, login, all step handlers | 2–3 days |
| Phase 4 | AI Engine | NLP interpretation, smart locators, failure analysis | 2 days |
| Phase 5 | Evidence Capture | Screenshots, console errors, HTML | 0.5 day |
| Phase 6 | Excel Result Writer | Append result columns in-place | 0.5 day |
| Phase 7 | Report Generation | HTML, PDF, JSON | 1 day |
| Phase 8 | Integration & E2E | Wire everything together, smoke test | 1 day |
| Phase 9 | Docs & Deliverables | README, install guide, sample files | 0.5 day |

---

## 5. Sequential Task Breakdown

---

### PHASE 1 — Foundation

#### Task 1.1 — Initialize Project Structure

**Description:** Create all folders and placeholder `__init__.py` files.  
**Command:**
```powershell
$dirs = @("config","excel_reader","executor","playwright_engine","ai_engine","reports","reports/templates","screenshots","logs","excel_inputs","utilities","tests")
foreach ($d in $dirs) { New-Item -ItemType Directory -Force "ExecuteTesting/$d" }
```
**Dependency:** None.  
**Deliverable:** Full folder tree exists.

---

#### Task 1.2 — Create `requirements.txt`

**Description:** Pin all runtime dependencies. Include a `[dev]` section for test utilities.  
**Dependency:** Task 1.1  
**Deliverable:** `requirements.txt` committed to repo.

---

#### Task 1.3 — Create `config/settings.yaml`

**Description:** Define all runtime parameters. No hardcoded values anywhere else.

```yaml
app:
  url: "https://qafjdforum.courts.phila.gov/"
  username: "${APP_USERNAME}"       # resolved from .env
  password: "${APP_PASSWORD}"

browser:
  type: "chromium"                  # chromium | firefox | webkit
  headless: false
  timeout_ms: 30000
  slow_mo_ms: 0

paths:
  excel_folder: "excel_inputs/"
  screenshot_folder: "screenshots/"
  report_folder: "reports/output/"
  log_folder: "logs/"

ai:
  provider: "anthropic"             # anthropic | openai
  model: "claude-sonnet-4-6"
  api_key: "${AI_API_KEY}"
  max_tokens: 1024

execution:
  retry_count: 3
  retry_delay_ms: 1000
  screenshot_on_pass: false
  screenshot_on_fail: true
  continue_on_failure: true
```

**Dependency:** Task 1.1  
**Deliverable:** `config/settings.yaml` with all knobs externalized.

---

#### Task 1.4 — Create `config/.env` (git-ignored)

**Description:** Provide a `.env.example` template and add `.env` to `.gitignore`.

```
APP_USERNAME=your_username
APP_PASSWORD=your_password
AI_API_KEY=your_api_key_here
```

**Dependency:** Task 1.3  
**Deliverable:** `.env.example` committed; `.env` git-ignored.

---

#### Task 1.5 — Implement Centralized Logging (`utilities/`)

**Description:** Configure `loguru` with structured log output to both console and rotating file. Each run creates a timestamped log file. Log fields: timestamp, level, test name, step, result, error, stack trace.

```python
# utilities/logger.py
from loguru import logger
from pathlib import Path
from datetime import datetime

def setup_logger(log_folder: str) -> None:
    Path(log_folder).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.add(f"{log_folder}/run_{ts}.log", rotation="50 MB",
               format="{time} | {level} | {extra[test]} | {extra[step]} | {message}")
```

**Dependency:** Tasks 1.3, 1.4  
**Deliverable:** Logger active across all modules via `from utilities.logger import logger`.

---

### PHASE 2 — Excel Reader

#### Task 2.1 — Implement `excel_reader/reader.py`

**Description:** Scan the configured `excel_folder` for all `.xlsx` files. For each file, open every sheet, read all rows into a list of `TestCase` dataclass objects. Preserve raw cell formatting metadata for later write-back.

```python
@dataclass
class TestCase:
    file_path: str
    sheet_name: str
    row_index: int          # 1-based row in sheet
    test_case_id: str
    test_case_name: str
    steps: str              # raw natural language step(s)
    expected_result: str
    preconditions: str = ""
    status: str = "NOT RUN"
    actual_result: str = ""
    error_message: str = ""
    screenshot_path: str = ""
    execution_time_ms: int = 0
```

**Key rules:**
- Skip rows where `steps` is blank.
- Handle merged cells gracefully.
- Do not load entire file into memory for large sheets — use `read_only=False` to allow write-back.

**Dependency:** Task 1.5  
**Deliverable:** `reader.py` returns `List[TestCase]` per file.

---

#### Task 2.2 — Implement `excel_reader/formatter.py`

**Description:** After execution, write result columns (`Status`, `Actual Result`, `Error`, `Screenshot`, `Execution Time`) back into the same workbook at the correct row. Use `openpyxl` with `keep_vba=True` and preserve cell styles in all existing columns.

**Key rules:**
- Check if result columns already exist; if so reuse them (idempotent re-runs).
- Style result cells: green fill for PASS, red fill for FAIL, yellow for SKIP.
- Save atomically (write to temp file, then rename).

**Dependency:** Task 2.1  
**Deliverable:** `formatter.py` updates original Excel in-place without losing data.

---

#### Task 2.3 — Create Sample Excel Template

**Description:** Provide `excel_inputs/sample_test_cases.xlsx` with:
- Columns: `TC_ID`, `Test Case Name`, `Preconditions`, `Steps`, `Expected Result`
- 3–5 sample test cases covering login, navigation, and form submission.

**Dependency:** Task 2.1  
**Deliverable:** Template file checked into repo as a reference artifact.

---

### PHASE 3 — Playwright Core Engine

#### Task 3.1 — Implement `playwright_engine/browser_manager.py`

**Description:** Manage the async Playwright browser lifecycle. Supports `async with BrowserManager() as bm:` context manager pattern. Reads browser type, headless mode, timeout from config.

```python
class BrowserManager:
    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright[config.browser.type].launch(
            headless=config.browser.headless,
            slow_mo=config.browser.slow_mo_ms
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True
        )
        self.page = await self.context.new_page()
        return self
```

**Dependency:** Tasks 1.3, 1.5  
**Deliverable:** Browser opens, closes, and handles context cleanly.

---

#### Task 3.2 — Implement `playwright_engine/wait_strategy.py`

**Description:** Centralize all wait logic so step handlers never use raw `sleep()`.

- `wait_for_navigation()` — waits for `networkidle` or `load` event.
- `wait_for_element(locator, state)` — waits for visible/attached/hidden.
- `wait_for_ajax()` — polls until no pending XHR/fetch requests.
- `wait_for_spinner_gone(spinner_selector)` — waits for loading overlay to disappear.
- Wrap all waits with configurable timeout from settings.

**Dependency:** Task 3.1  
**Deliverable:** Stable wait primitives used by all page_actions.

---

#### Task 3.3 — Implement Login Handler

**Description:** Dedicated login function in `playwright_engine/page_actions.py` that:
1. Navigates to the configured URL.
2. Fills username and password fields (using label-based locators first, fallback to common selectors).
3. Clicks the Login/Submit button.
4. Waits for the post-login page to load (verify by URL change or success element).
5. Validates login success; raises `LoginFailedError` if not.

**Dependency:** Tasks 3.1, 3.2  
**Deliverable:** `login(page, username, password)` function verified against target site.

---

#### Task 3.4 — Implement All Step Action Handlers

**Description:** One function per action type in `playwright_engine/page_actions.py`. Each function accepts `(page, target, value=None)` where `target` is a smart locator string.

| Handler | Playwright API used |
|---|---|
| `click(page, target)` | `page.get_by_role`, `page.get_by_text`, `page.locator` |
| `enter_text(page, target, value)` | `locator.fill()` |
| `select_dropdown(page, target, value)` | `locator.select_option()` |
| `select_radio(page, target, value)` | `locator.check()` |
| `check_checkbox(page, target)` | `locator.check()` |
| `upload_file(page, target, file_path)` | `locator.set_input_files()` |
| `download_file(page, target)` | `context.expect_download()` |
| `validate_text(page, target, expected)` | `locator.inner_text()` assertion |
| `validate_url(page, expected_url)` | `page.url` assertion |
| `validate_title(page, expected_title)` | `page.title()` assertion |
| `validate_field_value(page, target, expected)` | `locator.input_value()` |
| `validate_table(page, target, expected_rows)` | Parse table HTML |
| `validate_error_message(page, expected_msg)` | Scan common error selectors |
| `logout(page)` | Click logout link/button |

All handlers must:
- Use `tenacity` for automatic retry (up to `config.execution.retry_count` times).
- Log every attempt with result.
- Return `(success: bool, actual_result: str, error: str)`.

**Dependency:** Tasks 3.2, 3.3  
**Deliverable:** All 25+ action types from TESTSTACK.MD functional.

---

#### Task 3.5 — Implement Complex UI Handlers

**Description:** Separate handlers for advanced interactions.

**`playwright_engine/dialog_handler.py`:**
- Listen for `page.on("dialog")` to auto-accept or auto-dismiss alerts/confirms.
- Handle Bootstrap/custom modals by waiting for the modal backdrop and then interacting with modal body elements.

**`playwright_engine/tab_manager.py`:**
- Track new pages opened via `context.on("page")`.
- `switch_to_tab(index)` — switches focus to a specific tab.
- `close_tab(index)` — closes a tab and returns to previous.

**Additional complex handlers in `page_actions.py`:**
- `handle_date_picker(page, target, date_value)` — fills date input or interacts with calendar widget.
- `handle_rich_text_editor(page, target, content)` — types into contenteditable / TinyMCE / CKEditor.

**Dependency:** Task 3.4  
**Deliverable:** All complex UI scenario handlers verified manually.

---

### PHASE 4 — AI Engine

#### Task 4.1 — Implement `ai_engine/step_interpreter.py`

**Description:** Use the Claude API (Anthropic SDK) to parse a raw natural language test step string and return a structured action object.

**Input:** `"Click the Save button on the Add Case form"`  
**Output:**
```json
{
  "action": "click",
  "target": "Save",
  "target_type": "button",
  "context": "Add Case form",
  "value": null
}
```

**Implementation approach:**
- Build a system prompt that lists all supported action types with examples.
- Send the raw step string as the user message.
- Parse the JSON response.
- Cache results by step string hash to avoid repeated API calls for the same step.

**System prompt skeleton:**
```
You are a test automation interpreter. Given a natural language test step,
return a JSON object with:
- action: one of [click, enter_text, select_dropdown, select_radio, check_checkbox,
  upload_file, download_file, validate_text, validate_url, validate_title,
  validate_field_value, validate_table, validate_error, login, logout, navigate, save, cancel]
- target: the UI element label or identifier
- target_type: button | link | field | dropdown | checkbox | radio | table | page | message
- context: parent container or form name if mentioned
- value: the value to enter or select (null if not applicable)
Return ONLY valid JSON. No explanation.
```

**Dependency:** Tasks 1.3, 1.5  
**Deliverable:** `interpret_step(step_text) -> ActionSpec` with 90%+ accuracy on sample steps.

---

#### Task 4.2 — Implement `ai_engine/locator_strategy.py`

**Description:** Given an `ActionSpec`, generate a ranked list of Playwright locators to try.

**Strategy (in priority order):**
1. `page.get_by_role(target_type, name=target)` — ARIA role + accessible name.
2. `page.get_by_label(target)` — form label association.
3. `page.get_by_text(target)` — visible text.
4. `page.get_by_placeholder(target)` — placeholder text.
5. CSS attribute: `[data-testid]`, `[id]`, `[name]` containing target (case-insensitive).
6. AI fallback: if above fail, query the DOM snapshot via AI to suggest a specific CSS/XPath selector.

**Key principle:** Never use absolute XPath. Use relative, semantic locators that survive minor UI changes.

**Dependency:** Task 4.1  
**Deliverable:** `get_locators(page, action_spec) -> List[Locator]` tried in order until one resolves.

---

#### Task 4.3 — Implement `ai_engine/failure_analyzer.py`

**Description:** When a step fails, use AI to analyze the failure context and return a probable cause + suggested fix.

**Inputs to AI:**
- Failed step text.
- Exception message + stack trace.
- Page title and URL at time of failure.
- List of visible elements on page (DOM snapshot summary).

**Output:**
```json
{
  "probable_cause": "The Save button is disabled because mandatory field 'Case Type' is not filled.",
  "suggested_fix": "Ensure 'Case Type' dropdown is selected before clicking Save.",
  "retry_recommended": false
}
```

**Dependency:** Task 4.1  
**Deliverable:** `analyze_failure(context) -> FailureAnalysis` included in report.

---

#### Task 4.4 — Implement `ai_engine/flaky_detector.py`

**Description:** Track step-level pass/fail history across runs (stored in `logs/flaky_history.json`). A step is flagged as flaky if it has both PASS and FAIL results across the last N runs. Flaky steps are highlighted in the report.

**Dependency:** Tasks 4.1, 4.3  
**Deliverable:** `flaky_history.json` updated after each run; flaky flags surfaced in report.

---

### PHASE 5 — Evidence Capture

#### Task 5.1 — Implement Screenshot Capture

**Description:** In `playwright_engine/page_actions.py`, after every step:
- On FAIL: always capture screenshot. Filename: `{tc_id}_{step_index}_{action}_FAIL_{timestamp}.png`.
- On PASS: capture only if `config.execution.screenshot_on_pass` is `true`.
- Store path relative to project root; write relative path into `TestCase.screenshot_path`.

**Dependency:** Task 3.4  
**Deliverable:** Screenshots saved with consistent naming; path stored in test case object.

---

#### Task 5.2 — Capture Browser Console Errors

**Description:** Register a `page.on("console")` listener at browser start. Collect all `error` and `warning` level messages. Attach the log to the failed test case in the result.

**Dependency:** Task 3.1  
**Deliverable:** `console_errors: List[str]` field populated in `TestCase` on failure.

---

#### Task 5.3 — Capture Page HTML Snapshot (Optional)

**Description:** On critical failures (unhandled exceptions, page crashes), capture `page.content()` to `logs/html_snapshots/{tc_id}_{timestamp}.html`. Reference path in the test case error field.

**Dependency:** Task 5.1  
**Deliverable:** HTML snapshots captured for severe failures.

---

### PHASE 6 — Excel Result Writer

#### Task 6.1 — Wire `formatter.py` Write-Back

**Description:** After all test cases in a workbook are executed, call `write_results(workbook_path, test_cases)`. This function:
1. Opens the workbook with `openpyxl`.
2. Locates or creates result columns: `Status`, `Actual Result`, `Error`, `Screenshot`, `Execution Time (ms)`.
3. For each `TestCase`, writes values at the correct `row_index`.
4. Applies conditional formatting (green/red/yellow fill).
5. Saves the workbook.

**Idempotency rule:** If columns already exist from a previous run, overwrite only the result cells — do not duplicate columns.

**Dependency:** Tasks 2.1, 2.2, 3.4, 5.1  
**Deliverable:** Original Excel updated in-place with results after each run.

---

### PHASE 7 — Report Generation

#### Task 7.1 — Implement `reports/html_reporter.py`

**Description:** Use Jinja2 to render `reports/templates/report_template.html` with the execution summary and per-test details.

**Template sections:**
- Header: Run date, total time, target URL, browser.
- Summary table: Total, Passed, Failed, Skipped, Pass%.
- Per-test table: TC ID, Name, Status (color-coded), Actual Result, Error, Screenshot (clickable thumbnail), Execution Time.
- Failure analysis: AI probable cause per failed test.
- Flaky test flags.

**Output:** `reports/output/report_{timestamp}.html`

**Dependency:** Phase 3, Phase 4, Phase 5  
**Deliverable:** Self-contained HTML report (inline CSS, base64 screenshots).

---

#### Task 7.2 — Implement `reports/pdf_reporter.py`

**Description:** Use WeasyPrint to convert the generated HTML report to PDF.

```python
from weasyprint import HTML
HTML(filename=html_path).write_pdf(pdf_path)
```

**Output:** `reports/output/report_{timestamp}.pdf`

**Dependency:** Task 7.1  
**Deliverable:** PDF report matching HTML content.

---

#### Task 7.3 — Implement `reports/json_reporter.py`

**Description:** Serialize the full execution run (summary + all `TestCase` objects) to JSON.

```json
{
  "run_id": "20260706_143022",
  "start_time": "...",
  "end_time": "...",
  "total": 25,
  "passed": 20,
  "failed": 4,
  "skipped": 1,
  "pass_percentage": 80.0,
  "total_execution_time_ms": 145200,
  "test_cases": [...]
}
```

**Output:** `reports/output/report_{timestamp}.json`

**Dependency:** Phase 3, Phase 4  
**Deliverable:** Machine-readable JSON for downstream CI/CD integration.

---

### PHASE 8 — Integration and End-to-End Wiring

#### Task 8.1 — Implement `executor/step_dispatcher.py`

**Description:** Routes a parsed `ActionSpec` to the correct handler in `playwright_engine/page_actions.py`. Acts as the bridge between AI interpretation and Playwright execution.

```python
async def dispatch(page, action_spec: ActionSpec) -> StepResult:
    handler_map = {
        "click": page_actions.click,
        "enter_text": page_actions.enter_text,
        "select_dropdown": page_actions.select_dropdown,
        ...
    }
    handler = handler_map.get(action_spec.action)
    if not handler:
        return StepResult(success=False, error=f"Unknown action: {action_spec.action}")
    return await handler(page, action_spec.target, action_spec.value)
```

**Dependency:** Tasks 3.4, 4.1  
**Deliverable:** All action types routable without conditional chains in `main.py`.

---

#### Task 8.2 — Implement `main.py` Orchestrator

**Description:** The top-level entry point that ties all phases together.

```
main.py flow:
1. Load config from settings.yaml + .env
2. Setup logger
3. Read all Excel files → List[TestCase]
4. For each workbook:
   a. Open browser, login
   b. For each TestCase in workbook:
      i.  Interpret step via AI engine
      ii. Dispatch to step handler
      iii.Capture evidence on failure
      iv. Record result in TestCase object
   c. Write results back to Excel
   d. Close browser
5. Generate HTML, PDF, JSON reports
6. Print summary to console
```

**Error handling:** Any unhandled exception on a test case logs the error, marks it FAIL, and continues to the next test case (`continue_on_failure = true`).

**Dependency:** All previous tasks.  
**Deliverable:** `python main.py` executes full suite end-to-end.

---

#### Task 8.3 — Smoke Test Against Target Website

**Description:** Before full suite execution, run a minimal smoke test:
1. Open browser.
2. Navigate to `https://qafjdforum.courts.phila.gov/`.
3. Verify page title loads.
4. Attempt login with provided credentials.
5. Verify successful login (URL change or dashboard element visible).
6. Logout.
7. Verify logout.

**Dependency:** Task 8.2  
**Deliverable:** Smoke test passes; credentials confirmed valid; login/logout flow documented.

---

### PHASE 9 — Documentation and Deliverables

#### Task 9.1 — Write `INSTALLATION.md`

**Description:** Step-by-step guide:
```
1. Clone repository
2. Create virtualenv: python -m venv .venv
3. Activate: .venv\Scripts\activate (Windows) / source .venv/bin/activate (Linux/Mac)
4. Install dependencies: pip install -r requirements.txt
5. Install Playwright browsers: playwright install chromium
6. Copy .env.example to .env and fill in credentials
7. Place Excel test files in excel_inputs/
8. Run: python main.py
```

**Dependency:** Task 8.2  
**Deliverable:** `INSTALLATION.md` committed.

---

#### Task 9.2 — Write `README.md`

**Description:** Project overview, architecture diagram (ASCII), quick start, configuration reference, output description, and future enhancement roadmap.

**Dependency:** Task 9.1  
**Deliverable:** `README.md` committed.

---

## 6. Task Dependencies — Visual Map

```
Task 1.1 (folders)
  └── Task 1.2 (requirements)
  └── Task 1.3 (settings.yaml)
        └── Task 1.4 (.env)
        └── Task 1.5 (logging)
              └── Task 2.1 (excel reader)
                    └── Task 2.2 (excel formatter)
                    └── Task 2.3 (sample template)
              └── Task 3.1 (browser manager)
                    └── Task 3.2 (wait strategy)
                          └── Task 3.3 (login)
                                └── Task 3.4 (step handlers)
                                      └── Task 3.5 (complex handlers)
                                      └── Task 5.1 (screenshots)
                                      └── Task 5.2 (console errors)
                                      └── Task 5.3 (HTML snapshots)
              └── Task 4.1 (step interpreter)
                    └── Task 4.2 (locator strategy)
                    └── Task 4.3 (failure analyzer)
                    └── Task 4.4 (flaky detector)

Task 3.4 + Task 4.1 → Task 8.1 (dispatcher)
Task 2.2 + Task 5.1 → Task 6.1 (excel write-back)
All Phase 3-5 → Task 7.1 (HTML report)
Task 7.1 → Task 7.2 (PDF report)
Task 7.1 → Task 7.3 (JSON report)
All previous → Task 8.2 (main.py)
Task 8.2 → Task 8.3 (smoke test)
Task 8.3 → Task 9.1, 9.2
```

---

## 7. Expected Deliverables per Phase

| Phase | Deliverables |
|---|---|
| Phase 1 | Folder structure, `requirements.txt`, `settings.yaml`, `.env.example`, logger |
| Phase 2 | `reader.py`, `formatter.py`, sample Excel template |
| Phase 3 | Browser manager, all step handlers, dialog/tab handlers, login flow |
| Phase 4 | Step interpreter, locator strategy, failure analyzer, flaky detector |
| Phase 5 | Screenshots, console error capture, HTML snapshots |
| Phase 6 | In-place Excel result write-back with conditional formatting |
| Phase 7 | HTML report, PDF report, JSON report, Jinja2 template |
| Phase 8 | Wired `main.py`, smoke test passing, end-to-end execution verified |
| Phase 9 | `INSTALLATION.md`, `README.md`, all deliverables listed in TESTSTACK.MD |

---

## 8. Validation and Testing Checkpoints

### Checkpoint 1 — After Phase 1
- [ ] `python -c "import playwright, pandas, openpyxl, anthropic, loguru"` succeeds.
- [ ] `playwright install chromium` completes without errors.
- [ ] Logger writes to `logs/` folder.

### Checkpoint 2 — After Phase 2
- [ ] `reader.py` correctly reads all rows from sample Excel template.
- [ ] `formatter.py` writes result columns back without corrupting existing data.
- [ ] Idempotent re-run does not duplicate result columns.

### Checkpoint 3 — After Phase 3 (Login + Basic Actions)
- [ ] Browser opens and navigates to target URL.
- [ ] Login succeeds with provided credentials.
- [ ] `click`, `enter_text`, `select_dropdown` handlers work on at least one live form.
- [ ] Wait strategies do not produce false timeouts on the target site.

### Checkpoint 4 — After Phase 4 (AI Engine)
- [ ] 10 sample steps interpreted correctly by `step_interpreter.py`.
- [ ] Locator strategy finds elements for at least 80% of test steps without XPath fallback.
- [ ] Failure analyzer returns non-empty probable cause for a deliberate failure.

### Checkpoint 5 — After Phase 5 (Evidence)
- [ ] Failed step produces a screenshot in `screenshots/`.
- [ ] Console errors are captured in the test result.
- [ ] Screenshot filename matches expected naming convention.

### Checkpoint 6 — After Phase 6 (Excel Write-Back)
- [ ] Original Excel file has new result columns after execution.
- [ ] PASS rows have green fill; FAIL rows have red fill.
- [ ] All other columns and formatting are untouched.

### Checkpoint 7 — After Phase 7 (Reports)
- [ ] HTML report renders correctly in Chrome.
- [ ] PDF report is generated from HTML without layout errors.
- [ ] JSON report parses cleanly with `json.loads()`.
- [ ] Summary counts in reports match actual executed test cases.

### Checkpoint 8 — After Phase 8 (End-to-End)
- [ ] `python main.py` executes full sample suite without crashing.
- [ ] All 3 reports generated in `reports/output/`.
- [ ] Excel updated in-place.
- [ ] One deliberate failure is correctly captured with screenshot and AI analysis.
- [ ] `continue_on_failure = true` — framework does not halt on a failed step.

### Checkpoint 9 — After Phase 9 (Docs)
- [ ] A fresh environment can run the framework by following `INSTALLATION.md` alone.
- [ ] `README.md` accurately describes all outputs and configuration options.

---

## 9. Risks, Considerations, and Rollback Strategy

### Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Target website login credentials expire or change | Medium | High | Externalize in `.env`; fail fast with clear error if login fails |
| Target site blocks Playwright user-agent | Low | High | Set realistic `user_agent` in browser context; add `slow_mo` |
| AI API rate limits during large test runs | Medium | Medium | Cache interpreted steps by hash; add exponential backoff |
| WeasyPrint PDF rendering differences on Windows vs Linux | Medium | Low | Test on target OS; fall back to ReportLab if WeasyPrint fails |
| Excel file locked by another process during write-back | Low | Medium | Detect IOError, retry 3x with delay, log warning |
| Flaky locators on dynamic content | High | Medium | Use robust semantic locators; implement retry with `tenacity` |
| AI misinterprets ambiguous step text | Medium | Medium | Log interpreted action; allow manual override via `action_override` column in Excel |

### Considerations

- **Security:** Credentials must never appear in logs, screenshots, or reports. Mask password fields before logging.
- **Performance:** For large test suites (100+ cases), consider async batch execution per sheet.
- **Extensibility:** All action handlers are registered in a dict (`handler_map`) — adding new action types requires only adding a new function and one dict entry.
- **Re-runs:** The framework is idempotent — re-running against the same Excel file overwrites only result columns.

### Rollback Strategy

| Scenario | Rollback Action |
|---|---|
| Excel file corrupted during write-back | Framework creates a backup `{filename}_backup_{timestamp}.xlsx` before writing |
| AI model API unavailable | Fallback to a local rule-based interpreter using keyword matching (no API call) |
| Playwright browser fails to install | Pin known-good Playwright version in `requirements.txt`; document manual install steps |
| Report generation fails | Execution results already saved in Excel and JSON; HTML/PDF failure is non-blocking |

---

## 10. Final Implementation Checklist

Use this checklist to confirm the full implementation is complete and production-ready.

### Infrastructure
- [ ] All folders created per project structure.
- [ ] `requirements.txt` complete and all packages installable.
- [ ] `settings.yaml` covers all configurable parameters.
- [ ] `.env.example` documented; `.env` git-ignored.
- [ ] Logging writes to rotating file in `logs/`.

### Excel Reader
- [ ] Reads all `.xlsx` files from `excel_inputs/` folder.
- [ ] Reads all sheets per workbook.
- [ ] All required columns mapped to `TestCase` dataclass.
- [ ] Blank rows skipped gracefully.

### Playwright Execution
- [ ] Browser launch and context initialization working.
- [ ] Login handler verified on target site.
- [ ] All 25+ action types implemented.
- [ ] Smart wait strategies in place (no raw `sleep()`).
- [ ] Dialog/alert/modal handler registered.
- [ ] Multi-tab handler implemented.
- [ ] File upload and download handlers working.
- [ ] Date picker handler implemented.
- [ ] Rich text editor handler implemented.
- [ ] Retry logic via `tenacity` active on all handlers.

### AI Engine
- [ ] Step interpreter returns valid `ActionSpec` for all sample steps.
- [ ] Result caching by step hash active.
- [ ] Locator strategy tries semantic locators in priority order.
- [ ] Failure analyzer returns probable cause on failure.
- [ ] Flaky detector updates history file after each run.
- [ ] Fallback rule-based interpreter available if API is down.

### Evidence Capture
- [ ] Screenshots taken on every FAIL.
- [ ] Screenshot filenames follow naming convention.
- [ ] Console errors captured and stored in `TestCase`.
- [ ] HTML snapshot captured for critical failures.

### Excel Write-Back
- [ ] Result columns appended to original file.
- [ ] Conditional color formatting applied.
- [ ] No existing columns or data altered.
- [ ] Backup file created before write.

### Reports
- [ ] HTML report generated with summary and per-test table.
- [ ] Clickable screenshot thumbnails in HTML report.
- [ ] AI failure analysis included per failed test.
- [ ] Flaky test flags visible in report.
- [ ] PDF report generated from HTML.
- [ ] JSON report parseable and complete.

### Main Orchestrator
- [ ] Executes full flow from Excel read to report generation.
- [ ] Continues after any single test case failure.
- [ ] All errors logged with stack trace.
- [ ] Console summary printed at end.

### Documentation and Deliverables
- [ ] `INSTALLATION.md` complete and verified on a clean environment.
- [ ] `README.md` describes architecture, usage, and output.
- [ ] Sample Excel template committed.
- [ ] Sample `settings.yaml` committed.
- [ ] `requirements.txt` committed with pinned versions.
- [ ] All source code modular, no hardcoded values.

---

*Document version: 1.0 | Created: 2026-07-06 | Author: Implementation Planning*
