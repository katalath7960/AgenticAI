# AutoTester — AI-Powered Automated Test Case Generator

AutoTester crawls a website, understands its structure using AI, and generates
comprehensive test cases (functional, security, negative, workflow) along with
runnable Playwright/API automation scripts.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Pipeline](#running-the-pipeline)
  - [CLI](#cli)
  - [Streamlit UI](#streamlit-ui)
- [CLI Options Reference](#cli-options-reference)
- [Output Files](#output-files)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [How It Works](#how-it-works)
- [CI/CD Integration](#cicd-integration)

---

## Prerequisites

- **Python 3.11+**
- **Git**
- (Optional) An **OpenAI API key** for AI-powered element classification and
  user-journey generation. Without it the pipeline falls back to heuristic
  rules — everything still works.

---

## Installation

```bash
# 1. Clone the repo and navigate to the project
cd AutomatedTesting

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install the Playwright browser (Chromium)
playwright install chromium
```

---

## Configuration

Copy the example env file and add your key (optional):

```bash
cp .env.example .env
```

Edit `.env`:

```
OPENAI_API_KEY=sk-your-key-here
```

If you skip this step the pipeline will use heuristic classification instead of
AI — no functionality is lost.

---

## Running the Pipeline

### CLI

Run from the **parent directory** of `AutomatedTesting` (i.e. the `Python/`
folder), or from inside `AutomatedTesting/` itself:

```bash
# Basic run — crawl a site and generate test cases as JSON
python -m AutomatedTesting --url https://example.com

# Full run with security tests, Excel output, depth 5
python -m AutomatedTesting \
  --url https://example.com \
  --depth 5 \
  --output excel \
  --security

# Show all options
python -m AutomatedTesting --help
```

### Streamlit UI

```bash
streamlit run AutomatedTesting/streamlit_app.py
```

This opens a browser UI where you can:

1. Enter a target URL and tweak settings in the sidebar.
2. Click **Run Pipeline**.
3. View results, filter test cases, and download reports.

---

## CLI Options Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--url` | *(required)* | Target website URL |
| `--depth` | `3` | Max crawl depth (1–10) |
| `--output` | `json` | Output format: `json`, `csv`, `excel`, `html` |
| `--output-dir` | `output` | Directory for all generated files |
| `--security / --no-security` | `--no-security` | Include SQL injection and XSS test cases |
| `--headless / --no-headless` | `--headless` | Run browser visibly for debugging |
| `--scripts / --no-scripts` | `--scripts` | Generate Playwright and API test scripts |
| `--rate-limit` | `2.0` | Max requests per second (respects target server) |

---

## Output Files

After a run, the `output/` directory contains:

```
output/
├── test_cases.json             # Full test suite (JSON)
├── test_cases.csv              # CSV export
├── test_cases.xlsx             # Excel workbook (one sheet per category)
├── test_cases_jira.csv         # Jira-importable CSV
├── test_cases_testrail.xml     # TestRail-importable XML
├── report.html                 # Browsable HTML report
├── baseline.json               # DOM fingerprint for change detection
├── screenshots/                # Full-page screenshots per crawled URL
│   ├── index.png
│   └── about.png
├── generated_tests/
│   ├── playwright/             # Runnable pytest + Playwright scripts
│   │   ├── test_functional.py
│   │   ├── test_negative.py
│   │   ├── test_security.py
│   │   └── test_workflow.py
│   └── api/
│       └── test_api.py         # API endpoint tests (if APIs detected)
└── .github/
    └── workflows/
        └── test.yml            # GitHub Actions CI template
```

### Running Generated Playwright Tests

```bash
pytest output/generated_tests/playwright/ -v
```

### Running Generated API Tests

```bash
pytest output/generated_tests/api/ -v
```

---

## Project Structure

```
AutomatedTesting/
├── __main__.py                 # CLI entry point
├── pipeline.py                 # Orchestrator (crawl → analyze → generate → export)
├── streamlit_app.py            # Streamlit UI
├── requirements.txt
├── .env.example
│
├── config/
│   ├── settings.py             # Pydantic settings model
│   └── logging.py              # Logging setup
│
├── crawler/                    # Phase 2 — Web scraping engine
│   ├── crawler.py              # BFS crawl loop
│   ├── browser.py              # Playwright page loader
│   ├── extractor.py            # DOM element extraction (BeautifulSoup)
│   ├── network.py              # XHR/fetch API interception
│   ├── auth.py                 # Login form handler
│   ├── robots.py               # robots.txt parser
│   └── models.py               # PageData, SiteMap, FormField, etc.
│
├── analyzer/                   # Phase 3 — Semantic analysis
│   ├── analyzer.py             # Main analysis pipeline
│   ├── forms.py                # Form field analysis
│   ├── classifier.py           # AI + heuristic element classification
│   ├── diff.py                 # UI change detection (baseline diffing)
│   └── models.py               # PageAnalysis, SiteAnalysis
│
├── generator/                  # Phase 4 — Test case generation
│   ├── generator.py            # Master generator
│   ├── functional.py           # Valid/invalid/boundary/required tests
│   ├── security.py             # SQLi, XSS, auth checks
│   ├── workflow.py             # E2E journeys, navigation, broken links
│   ├── negative.py             # Missing input, malformed data, fuzz routes
│   └── models.py               # TestCase, TestSuite
│
├── output/exporters/           # Phase 5 — Export formats
│   ├── json_export.py
│   ├── excel_export.py         # CSV + Excel
│   ├── jira_export.py          # Jira CSV + TestRail XML
│   └── html_report.py
│
├── scripts/                    # Phase 6 — Automation script generation
│   ├── playwright/gen_playwright.py
│   ├── api/gen_api_tests.py
│   ├── ci_template.py          # GitHub Actions YAML generator
│   └── selectors.py            # Self-healing selector strategies
│
├── templates/
│   └── report.html             # Jinja2 HTML report template
│
└── tests/                      # Phase 8 — Unit tests
    ├── test_extractor.py
    ├── test_generator.py
    └── test_exporters.py
```

---

## Running Tests

```bash
# From the AutomatedTesting directory
python -m pytest tests/ -v
```

All 16 unit tests cover the extractor, generator, and exporter modules without
needing a browser or network.

---

## How It Works

The pipeline runs in five stages:

1. **Crawl** — Playwright loads each page (JS rendered), extracts DOM elements
   (forms, buttons, inputs, links), intercepts XHR/fetch API calls, and takes
   screenshots. A BFS queue respects `robots.txt`, rate limits, and max depth.

2. **Analyze** — Forms are classified (login, search, general). Fields are
   checked for validation constraints (required, minlength, pattern). An
   optional OpenAI call classifies every element into Input / Action / Output /
   Navigation. A risk score is computed per page.

3. **Generate** — Four generators produce test cases:
   - **Functional**: valid input, invalid input, boundary conditions, required
     field validation.
   - **Security**: SQL injection, XSS, authentication/authorization (only with
     `--security` flag).
   - **Workflow**: AI-generated user journeys, internal link validation, broken
     link checks.
   - **Negative**: empty submissions, malformed data, route fuzzing.

4. **Export** — The test suite is written to JSON, CSV, Excel, HTML, Jira CSV,
   and TestRail XML.

5. **Script generation** — Runnable `pytest` + Playwright test files and API
   test files are generated from the test cases. A GitHub Actions workflow
   template is included.

### UI Change Detection

On each run the pipeline saves a DOM fingerprint (`baseline.json`). On
subsequent runs it diffs against the baseline and flags pages where forms,
headings, or links changed — so you know which test cases may need
regeneration.

---

## CI/CD Integration

The pipeline auto-generates `.github/workflows/test.yml`. To use it:

1. Copy `output/.github/` to your repo root.
2. Push to GitHub — the workflow installs dependencies, runs the generated
   Playwright tests, and uploads the HTML report as a build artifact.

---

## Examples

```bash
# Crawl a site with visible browser (for debugging)
python -m AutomatedTesting --url https://example.com --no-headless --depth 2

# Generate everything including security tests, output to Excel
python -m AutomatedTesting --url https://myapp.com --security --output excel

# Slow crawl (0.5 req/s) to avoid overloading a staging server
python -m AutomatedTesting --url https://staging.myapp.com --rate-limit 0.5

# Skip script generation, just produce test case documents
python -m AutomatedTesting --url https://example.com --no-scripts
```
