# AI-Powered Test Automation Suite

A production-ready Streamlit web application that allows non-technical users to upload Excel test cases, execute them automatically against any web application using Playwright, and download the updated Excel file with full results — all through a browser-based interface with no command-line knowledge required.

---

## Overview

### Purpose

Manual test case execution is slow, error-prone, and does not scale. This application bridges the gap between manual test documentation (Excel) and automated browser execution, enabling QA engineers and business analysts to:

- Write test steps in plain English inside Excel.
- Upload the file to the Streamlit UI.
- Click "Start Testing" and watch the results appear in real-time.
- Download the updated Excel with PASS/FAIL results, screenshots, and error details.

### Problem it Solves

| Before | After |
|---|---|
| Manual testers execute steps one by one | Framework executes hundreds of steps automatically |
| Results recorded by hand | Results written back automatically into the original Excel |
| No screenshots for failures | Evidence captured automatically for every failure |
| Hours of regression testing | Minutes |
| Requires coding knowledge to automate | Simple Excel upload + button click |

### High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Streamlit Web Interface                     │
│   Upload → Configure → Execute → Monitor → Download           │
└───────────────────────────┬────────────────────────────────────┘
                            │
            ┌───────────────▼───────────────┐
            │       Test Executor           │
            │  Background Thread +          │
            │  asyncio event loop           │
            └───────┬───────────────────────┘
                    │
        ┌───────────▼──────────┐    ┌─────────────────────┐
        │   AI Step Interpreter│    │  Playwright Engine   │
        │  Claude API or       │───▶│  Browser + 25+       │
        │  Keyword Fallback    │    │  Action Handlers     │
        └──────────────────────┘    └──────────┬──────────┘
                                               │
                    ┌──────────────────────────▼───────────────┐
                    │           Evidence Capture               │
                    │  Screenshots · Console Errors · Timing   │
                    └──────────────────────────────────────────┘
                                               │
                    ┌──────────────────────────▼───────────────┐
                    │          Excel Writer                    │
                    │  Append result columns to original file  │
                    └──────────────────────────────────────────┘
```

---

## Features Implemented

### Streamlit User Interface
- Clean, dark-sidebar layout with clear navigation phases (Upload → Configure → Execute → Results).
- Drag-and-drop Excel file upload component.
- Test case preview table (up to 50 rows shown before execution).
- Real-time execution log with color-coded output (green=pass, red=fail, purple=step, blue=info).
- Auto-refreshing progress bar during execution.
- Stop button to terminate execution mid-run.
- Password masking for secure credential entry.

### Excel Upload Capability
- Reads all sheets in a workbook automatically.
- Column name detection is flexible — accepts common aliases (e.g. "TC_ID", "Test ID", "No").
- Handles merged cells and blank rows gracefully.
- Multi-step test cases supported (one step per line within a single cell).

### Test Execution Workflow
- Background threading — Streamlit UI stays responsive during execution.
- Asyncio event loop runs inside the thread (no event loop conflicts).
- Login once per run; session reused across all test cases.
- Per-test-case step interpretation using keyword matching or Claude AI.
- Retry logic for element resolution (up to 3 attempts before failing a step).
- Configurable timeout, continue-on-failure, and screenshot settings.

### Browser Automation (25+ Actions)
| Category | Actions |
|---|---|
| Auth | login, logout |
| Navigation | navigate, click (menu/link/button) |
| Forms | enter_text, select_dropdown, select_radio, check_checkbox |
| Files | upload_file, download_file |
| Records | add_record, edit_record, delete_record, search_records, save, cancel |
| Validation | validate_text, validate_url, validate_title, validate_error_message, validate_navigation |
| Special | date_picker, rich text editor, modal dialogs, multi-tab |

### Smart Element Location (locator_manager.py)
Tries locators in this priority order (never uses fragile absolute XPath):
1. ARIA role + accessible name
2. Label association
3. Placeholder text
4. Visible text
5. `name`, `id`, `aria-label`, `data-testid`, `title` attributes

### Excel Result Updates
- Appends 6 new columns: `Execution Status`, `Actual Result`, `Error Details`, `Screenshot`, `Execution Time`, `Executed Date`.
- Color-coded: green (PASS), red (FAIL), yellow (SKIP/NOT RUN).
- Idempotent: re-running overwrites result columns without duplicating them.
- Backup created before write; backup deleted on success.

### Reporting
- **Execution Dashboard**: Total / Passed / Failed / Skipped / Pass% / Duration — displayed as metric cards.
- **Results Table**: Sortable, filterable Pandas DataFrame rendered in Streamlit.
- **Failure Expanders**: Per-failed-test accordion showing steps, error, and screenshot.
- **Download Updated Excel**: One-click download of the annotated workbook.
- **Download JSON Report**: Machine-readable summary for CI/CD integration.

### Error Handling
- `continue_on_failure = true` (configurable): never stops after a single test failure.
- Screenshots captured automatically for every failed step.
- Browser console errors collected via `page.on("console")` listener.
- Exception details stored in `Error Details` column.
- Thread-safe architecture: executor thread crashes don't affect the Streamlit UI.

### Screenshot Capture
- Saved to `screenshots/<timestamp>/` folder.
- Named: `{TC_ID}_step{N}_{PASS|FAIL}_{timestamp}.png`.
- Displayed inline in the failure expander in the results dashboard.
- Path stored in `Screenshot` column of the updated Excel.

### Logging
- All execution messages timestamped and streamed to the UI log panel.
- Color coding: INFO (blue), SUCCESS (green), ERROR (red), WARNING (yellow), STEP (purple).
- Log replay available after execution completes (collapsible panel).

---

## Technology Stack

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Runtime |
| Streamlit | ≥ 1.35 | Web UI framework |
| Playwright (async) | ≥ 1.44 | Browser automation |
| anthropic | ≥ 0.28 | AI step interpretation (Claude) |
| pandas | ≥ 2.2 | DataFrame rendering in UI |
| openpyxl | ≥ 3.1 | Excel read/write |
| PyYAML | ≥ 6.0 | Configuration loading |
| tenacity | ≥ 8.3 | Retry logic |
| Pillow | ≥ 10.3 | Screenshot image handling |

---

## Installation Instructions

### Prerequisites
- Python 3.10 or higher
- pip (latest)
- Node.js 18+ (required internally by Playwright)

### 1. Clone / Download

```bash
cd c:\Damu\AppliedAI\Edureka-AgenticAI\Python\TestAutomationApp
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright browser

```bash
playwright install chromium
# Or install all browsers:
playwright install
```

### 5. Generate sample test case file (optional)

```bash
python create_sample.py
```

---

## How to Run

```bash
streamlit run app.py
```

The application opens in your browser at `http://localhost:8501`.

---

## Application Workflow — Step by Step

### Step 1 — Prepare Your Excel File

Create or use the provided `sample_test_cases.xlsx`. Required columns:

| Column | Accepted Names | Example |
|---|---|---|
| TC ID | TC_ID, ID, Test ID, No | TC_001 |
| Test Case Name | Test Case Name, Scenario, Title | Verify Login |
| Preconditions | Preconditions, Prerequisites | App is accessible |
| Steps | Steps, Action, Test Steps | Login with valid credentials |
| Expected Result | Expected Result, Expected | User is logged in |

**Multi-step cells:** Put each step on a new line within the Steps cell.

### Step 2 — Configure in Sidebar

| Field | Description |
|---|---|
| Application URL | Full URL including https:// |
| Username | Login username (stored only in memory, never on disk) |
| Password | Masked input; stored only in session memory |
| Browser | Chrome (Chromium), Firefox, or WebKit |
| Headless Mode | Run without visible browser window |
| Element Timeout | Seconds to wait for elements (default 30s) |
| Screenshot on Failure | Capture PNG for failed steps |
| Continue on Failure | Don't stop suite after a single failure |
| Anthropic API Key | Optional — enables Claude AI step interpretation |

### Step 3 — Upload Excel

Drag and drop or click "Browse files" to upload your `.xlsx` file. A preview of the test cases appears immediately.

### Step 4 — Start Testing

Click **▶ Start Testing**. The browser launches (or runs headlessly), logs in, and executes every test case. A live log streams to the screen with color-coded status messages.

### Step 5 — Monitor Progress

Watch the real-time log and progress bar. The current test case ID is shown at the top of the log area. Click **⏹ Stop Execution** at any time to halt the run.

### Step 6 — Review Results

After execution completes:
- **Summary cards** show totals and pass rate.
- **Results table** shows per-test-case status with color coding.
- **Failure expanders** show error details and failure screenshots inline.

### Step 7 — Download Results

Click **📥 Download Updated Excel** to get the original file annotated with 6 new result columns. Click **📄 Download JSON Report** for a machine-readable summary.

---

## Configuration Details (`config/config.yaml`)

```yaml
browser:
  default_type: "chromium"    # chromium | firefox | webkit
  headless: false             # overridden by UI selection
  timeout_ms: 30000           # element wait timeout
  slow_mo_ms: 0               # delay between actions (debug)

execution:
  retry_count: 3              # retries per failed element resolution
  retry_delay_ms: 1000        # delay between retries
  screenshot_on_fail: true    # overridden by UI
  continue_on_failure: true   # overridden by UI

ai:
  model: "claude-sonnet-4-6"  # Claude model for step interpretation
  max_tokens: 512
```

---

## Troubleshooting

### Browser fails to launch
- Run `playwright install chromium` inside the activated virtualenv.
- Ensure Node.js 18+ is installed: `node --version`.

### Login fails
- Verify credentials manually in a browser first.
- Ensure `headless: false` to see what's happening on screen.
- Increase timeout if the login page loads slowly.

### Element not found / FAIL on valid steps
- Enable **Headless Mode: OFF** and slow down using `slow_mo_ms: 200` in config.yaml.
- Rephrase the step to match visible text exactly (e.g. "Click Save" not "Click the save button").
- Check for iframes — elements inside iframes require a `switch_to_frame` step.

### Excel not updating
- Ensure the file isn't open in Excel while the app is writing to it.
- Check `logs/` for write error details.

### Missing dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Streamlit port already in use
```bash
streamlit run app.py --server.port 8502
```

### WeasyPrint / PDF issues on Windows
- PDF generation is not included in this Streamlit version (JSON + Excel are the download formats).

---

## Future Enhancements

| Enhancement | Description |
|---|---|
| AI-generated test cases | Generate test cases from screenshots or requirements documents |
| Self-healing locators | Detect DOM changes and auto-update locators |
| Parallel execution | Run multiple test suites simultaneously across browser instances |
| CI/CD integration | GitHub Actions / Azure DevOps / Jenkins pipeline support |
| BrowserStack integration | Run on real devices in the cloud |
| API testing | Validate REST API endpoints alongside UI steps |
| Database validation | Query databases to verify backend data after UI operations |
| Email report delivery | Send HTML report to stakeholders automatically |
| Slack / Teams notifications | Post results summary to collaboration channels |
| Visual regression | Compare screenshots against baselines |
| Accessibility testing | Run axe-core accessibility checks as test steps |
| Test scheduling | Run suites on a cron schedule |
| Multi-user support | User accounts and run history |

---

## Security Notes

- Passwords are entered via `type="password"` masked Streamlit inputs.
- Credentials are stored only in `st.session_state` (in-memory, per-session).
- No credentials are written to disk, logs, Excel, or screenshots.
- Uploaded Excel files are written to a system temp directory and deleted when a new file is uploaded or the session resets.
- The `.env.example` shows what environment variables to set; the actual `.env` is never committed.

---

## Project Structure

```
TestAutomationApp/
├── app.py                    # Streamlit application (entry point)
├── config/
│   └── config.yaml           # Default configuration
├── excel/
│   ├── __init__.py
│   ├── excel_reader.py       # Read test cases from .xlsx workbooks
│   └── excel_writer.py       # Write results back to original workbook
├── automation/
│   ├── __init__.py
│   ├── playwright_engine.py  # All browser action handlers
│   ├── test_executor.py      # Orchestration, step interpretation, threading
│   └── locator_manager.py    # Smart element resolution (no XPath)
├── reports/                  # Reserved for future HTML report output
├── screenshots/              # Failure evidence (auto-created per run)
├── logs/                     # Reserved for structured log files
├── requirements.txt
├── create_sample.py          # Script to generate sample_test_cases.xlsx
├── sample_test_cases.xlsx    # Sample test case file (generated)
└── README.md
```
