# TESTTASKS — Implementation Plan for Automated Testing Solution

This document translates the technical stack and capabilities defined in
[TECHTESTSTACK.MD](TECHTESTSTACK.MD) into a concrete, step-by-step execution
plan. Each phase maps directly to a requirement section in the source document.

---

## Phase 1 — Project Scaffolding & Core Configuration

| # | Task | Details | Output |
|---|------|---------|--------|
| 1.1 | Initialize the Python project | Create a `pyproject.toml` (or `requirements.txt`) with initial dependencies: `playwright`, `beautifulsoup4`, `lxml`, `httpx`, `openai` / `langchain`, `pydantic`, `pandas`, `openpyxl`. | Runnable virtual-env with `pip install -e .` |
| 1.2 | Define directory structure | `crawler/`, `analyzer/`, `generator/`, `output/`, `scripts/`, `tests/`, `config/`. | Skeleton folders with `__init__.py` |
| 1.3 | Create configuration model | Pydantic `Settings` class: `target_url`, `max_depth`, `rate_limit_rps`, `respect_robots_txt`, `login_credentials` (optional), `output_format` (json/csv/excel), `ai_model` (gpt-4o / claude). | `config/settings.py` |
| 1.4 | Set up logging & rate-limiting | Python `logging` module + `asyncio.Semaphore` or `httpx` transport-level throttle. | `config/logging.py` |
| 1.5 | Add a CLI entry point | `click` or `argparse` CLI: `python -m autotester --url <URL> [--depth N] [--output json]`. | `__main__.py` |

---

## Phase 2 — Web Scraping & Crawling Engine

_Requirement: "Web Scraping Capability"_

| # | Task | Details | Output |
|---|------|---------|--------|
| 2.1 | Implement `robots.txt` parser | Fetch and parse `robots.txt` before crawling. Skip disallowed paths. | `crawler/robots.py` |
| 2.2 | Build Playwright-based page loader | Launch headless Chromium via Playwright. Navigate to URL, wait for `networkidle`, capture rendered HTML. Handle JS-rendered SPAs. | `crawler/browser.py` |
| 2.3 | Implement link discovery & crawl queue | BFS/DFS crawler: extract all `<a href>` links, normalize URLs, deduplicate, respect `max_depth`. Store visited set. | `crawler/crawler.py` |
| 2.4 | DOM element extraction | For each page, extract: forms (fields, actions, methods), buttons, inputs, dropdowns, textareas, links, headings, labels. Produce a structured `PageModel`. | `crawler/extractor.py` |
| 2.5 | Network traffic interception | Use Playwright's `page.on("request")` / `page.on("response")` to capture XHR/fetch API calls (URL, method, headers, payload shape). | `crawler/network.py` |
| 2.6 | Login / authentication handler | If credentials provided in config, detect login form (heuristic: `type=password` field), fill and submit, persist auth cookies/session for subsequent pages. | `crawler/auth.py` |
| 2.7 | Screenshot capture | Take a full-page screenshot per URL. Store as `output/screenshots/<slug>.png`. | `crawler/screenshot.py` |

### Phase 2 deliverable
A `SiteMap` data structure containing every crawled page with its URL,
extracted elements, detected API calls, and screenshot path.

---

## Phase 3 — Data Extraction & Semantic Understanding

_Requirement: "Data Extraction & Understanding"_

| # | Task | Details | Output |
|---|------|---------|--------|
| 3.1 | Metadata extraction | Page title, `<meta>` description, canonical URL, `<h1>`–`<h6>` hierarchy, Open Graph tags. | `analyzer/metadata.py` |
| 3.2 | Form field analysis | For each form: field name, type, `required` attribute, `pattern`/`minlength`/`maxlength` constraints, placeholder text, associated `<label>`. | `analyzer/forms.py` |
| 3.3 | Validation & message detection | Scan for error/success message containers (`.error`, `.alert`, `[role=alert]`, aria attributes). Record static text and dynamic patterns. | `analyzer/messages.py` |
| 3.4 | Element classification with AI | Send the page DOM summary to an LLM prompt that classifies each element into: **Input**, **Action** (submit, cancel, navigate), or **Output/Result**. Return structured JSON. | `analyzer/classifier.py` |
| 3.5 | Build `PageAnalysis` model | Pydantic model combining metadata, form analysis, detected messages, and element classifications per page. | `analyzer/models.py` |

### Phase 3 deliverable
An enriched `PageAnalysis` per page — the semantic input for test generation.

---

## Phase 4 — Test Case Generation

_Requirement: "Test Case Generation" — functional, security, workflow, negative_

### 4A — Functional Test Cases

| # | Task | Details | Output |
|---|------|---------|--------|
| 4A.1 | Valid-input scenario generator | For each form: generate a test case with valid values respecting detected constraints (type, pattern, min/max). Use AI to produce realistic sample data. | List of `TestCase` |
| 4A.2 | Invalid-input scenario generator | For each constrained field: empty when required, too-short, too-long, wrong type, wrong format (e.g., `abc` in email field). | List of `TestCase` |
| 4A.3 | Boundary-condition generator | `minlength - 1`, `minlength`, `maxlength`, `maxlength + 1`, zero, negative, Unicode edge cases. | List of `TestCase` |
| 4A.4 | Required-field validation generator | Submit form with each required field individually blanked. Expected result: field-level error message. | List of `TestCase` |

### 4B — Security Test Cases

| # | Task | Details | Output |
|---|------|---------|--------|
| 4B.1 | SQL injection payloads | For each text input: inject common SQLi payloads (`' OR 1=1 --`, `"; DROP TABLE`, UNION-based). Expected: no server error / no data leak. | List of `TestCase` |
| 4B.2 | XSS payloads | Inject `<script>alert(1)</script>`, event-handler payloads, encoded variants. Expected: sanitized output. | List of `TestCase` |
| 4B.3 | Auth/authz checks | Access protected pages without login; access admin routes as regular user; test session expiry. | List of `TestCase` |

### 4C — Workflow / E2E Scenarios

| # | Task | Details | Output |
|---|------|---------|--------|
| 4C.1 | AI-driven journey generation | Provide the `SiteMap` (pages + links + forms) to an LLM. Prompt it to identify logical user journeys (e.g., home → login → dashboard → profile edit → logout). | List of `WorkflowTestCase` |
| 4C.2 | Navigation & link validation | For every internal link: verify it returns 200 and lands on the expected page. Flag broken links (404/5xx). | List of `TestCase` |

### 4D — Negative Test Cases

| # | Task | Details | Output |
|---|------|---------|--------|
| 4D.1 | Missing-input tests | Submit each form completely empty. | List of `TestCase` |
| 4D.2 | Malformed-input tests | Incorrect email formats, future dates in past-only fields, special characters in numeric fields. | List of `TestCase` |
| 4D.3 | Broken route tests | Append random paths, query-string fuzz, test 404 page rendering. | List of `TestCase` |

### Test Case data model

```
TestCase:
  id:            str          # e.g., "TC-FUNC-001"
  category:      enum         # Functional | Security | Workflow | Negative
  description:   str
  preconditions: list[str]
  steps:         list[str]
  expected:      str
  priority:      enum         # Critical | High | Medium | Low
  severity:      enum         # Blocker | Major | Minor | Trivial
  page_url:      str
  element_ref:   str | None   # CSS selector or XPath of the element under test
```

File: `generator/models.py`

### Phase 4 deliverable
A complete `TestSuite` (list of `TestCase`) covering all four categories.

---

## Phase 5 — Output Formatting & Export

_Requirement: "Output Format"_

| # | Task | Details | Output |
|---|------|---------|--------|
| 5.1 | JSON exporter | Serialize `TestSuite` to pretty-printed JSON. | `output/exporters/json_export.py` |
| 5.2 | CSV / Excel exporter | Use `pandas` + `openpyxl` to write one sheet per category. Columns match the `TestCase` fields. | `output/exporters/excel_export.py` |
| 5.3 | Test-management exporter | Format for Jira (CSV import) or TestRail (XML). Map priority/severity to platform values. | `output/exporters/jira_export.py` |
| 5.4 | HTML report | Jinja2 template rendering a browsable report with screenshots inline, grouped by page and category. | `output/exporters/html_report.py` |

---

## Phase 6 — Automation Script Generation

_Requirement: "Automation Support"_

| # | Task | Details | Output |
|---|------|---------|--------|
| 6.1 | Playwright script generator | For each `TestCase`, produce a self-contained Playwright (Python) test function. Use selectors from `element_ref`. Group into `test_<page>.py` files. | `scripts/playwright/` |
| 6.2 | Selenium script generator (optional) | Same as above but targeting Selenium WebDriver + pytest. | `scripts/selenium/` |
| 6.3 | API test script generator | For detected API endpoints (from Phase 2.5), generate `httpx`/`requests`-based tests: valid call, invalid payload, auth required, rate-limit. | `scripts/api/` |
| 6.4 | CI/CD integration template | Provide GitHub Actions workflow YAML (and optionally GitLab CI) that installs deps, runs Playwright tests, and uploads the HTML report as an artifact. | `.github/workflows/test.yml` |

---

## Phase 7 — AI-Powered Enhancements

_Requirement: "Advanced Enhancements (Optional)"_

| # | Task | Details | Output |
|---|------|---------|--------|
| 7.1 | Risk-based test prioritization | Feed test cases + page analytics to an LLM. Score each test by risk (form complexity, user traffic heuristic, security surface). Re-sort suite by priority. | Updated `TestSuite` ordering |
| 7.2 | UI change detection & re-generation | Store a baseline DOM fingerprint per page. On re-run, diff against baseline. If elements changed, regenerate affected test cases and flag deltas. | `analyzer/diff.py` |
| 7.3 | Visual test cases | Annotate screenshots with bounding boxes around test-relevant elements + overlay test descriptions. Use Pillow or Playwright's `element.screenshot()`. | Annotated PNGs in `output/visual/` |
| 7.4 | Self-healing selectors | Generate multiple selector strategies per element (CSS, XPath, text content, `data-testid`). At test runtime, try in order until one resolves. | `scripts/selectors.py` |

---

## Phase 8 — Integration, Testing & Packaging

| # | Task | Details | Output |
|---|------|---------|--------|
| 8.1 | Unit tests for each module | pytest tests for crawler, analyzer, generator, exporters. Mock Playwright for CI. | `tests/` |
| 8.2 | Integration test on a sample site | Run the full pipeline against a known test site (e.g., `the-internet.herokuapp.com` or a local Flask app). Validate output completeness. | `tests/integration/` |
| 8.3 | Streamlit admin UI (optional) | Single-page Streamlit app: enter URL, configure options, trigger run, view/download results. | `streamlit_app/app.py` |
| 8.4 | Docker packaging | `Dockerfile` with Playwright browsers pre-installed. `docker-compose.yml` if a DB is used. | `docker/` |
| 8.5 | Documentation | `README.md` with quickstart, architecture diagram, configuration reference, and example output. | `README.md` |

---

## Dependency Summary

| Category | Libraries |
|----------|-----------|
| Scraping / Browser | `playwright`, `beautifulsoup4`, `lxml` |
| HTTP | `httpx` |
| AI / LLM | `openai` or `langchain` + `langchain-openai` |
| Data modeling | `pydantic` |
| Data export | `pandas`, `openpyxl`, `jinja2` |
| CLI | `click` |
| Image annotation | `Pillow` |
| Testing | `pytest`, `pytest-asyncio`, `pytest-playwright` |
| CI/CD | GitHub Actions |
| UI (optional) | `streamlit` |
| Containerization | Docker + Playwright base image |

---

## Execution Timeline (suggested)

| Week | Phases | Milestone |
|------|--------|-----------|
| 1 | 1 + 2 | Crawler produces a complete `SiteMap` for a target URL |
| 2 | 3 + 4A/4D | Semantic analysis + functional & negative test cases generated |
| 3 | 4B + 4C + 5 | Security & workflow tests + all export formats working |
| 4 | 6 + 7 | Automation scripts generated + AI enhancements integrated |
| 5 | 8 | Testing, Docker packaging, documentation, demo |

---

## Constraints & Guardrails

- **Legal**: Always check and respect `robots.txt`. Only test sites you own or
  have explicit permission to test.
- **Rate limiting**: Default to 2 requests/second with configurable override.
- **Credentials**: Never log or export credentials. Store in environment
  variables or a `.env` file (gitignored).
- **Data privacy**: Do not persist PII scraped from pages. Redact in exports.
- **Security payloads**: Only execute injection tests against sites you are
  authorized to test. Include a confirmation prompt before running security
  test cases.
