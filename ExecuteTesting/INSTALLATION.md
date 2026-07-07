# Installation Guide

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10+ |
| pip | Latest |
| Node.js | 18+ (required internally by Playwright) |

---

## Step 1 — Clone / Download the Project

```bash
cd c:\Damu\AppliedAI\Edureka-AgenticAI\Python\ExecuteTesting
```

---

## Step 2 — Create a Virtual Environment

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

---

## Step 3 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## Step 4 — Install Playwright Browser

```bash
playwright install chromium
```

To install all browsers:
```bash
playwright install
```

---

## Step 5 — Configure Credentials

Copy the example env file:
```bash
cp .env.example .env
```

Edit `.env` and fill in:
```
APP_USERNAME=your_actual_username
APP_PASSWORD=your_actual_password
AI_API_KEY=your_anthropic_api_key
```

> **Note:** The `.env` file is git-ignored and must never be committed.

---

## Step 6 — Add Test Case Excel Files

Place your `.xlsx` test case files in the `excel_inputs/` folder.

To generate the bundled sample file:
```bash
python excel_inputs/create_sample.py
```

---

## Step 7 — Run the Framework

```bash
python main.py
```

The framework will:
1. Read all `.xlsx` files from `excel_inputs/`
2. Launch the browser and login
3. Execute every test case
4. Write results back into the original Excel files
5. Generate HTML, PDF, and JSON reports in `reports/output/`

---

## Optional — Adjust Configuration

Edit `config/settings.yaml` to change:
- `browser.headless: true` — run without a visible browser window
- `execution.screenshot_on_pass: true` — capture screenshots for passing steps
- `execution.continue_on_failure: false` — stop suite on first failure
- `browser.type` — switch to `firefox` or `webkit`

---

## Output Locations

| Artifact | Location |
|---|---|
| Updated Excel files | `excel_inputs/` (in-place) |
| HTML Report | `reports/output/report_<timestamp>.html` |
| PDF Report | `reports/output/report_<timestamp>.pdf` |
| JSON Report | `reports/output/report_<timestamp>.json` |
| Screenshots | `screenshots/` |
| Logs | `logs/run_<timestamp>.log` |

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'playwright'`**
→ Run `pip install -r requirements.txt` inside the activated virtualenv.

**`playwright install` fails**
→ Ensure Node.js 18+ is installed: `node --version`

**Login fails**
→ Verify `APP_USERNAME` and `APP_PASSWORD` in `.env`; test manually in a browser.

**WeasyPrint PDF not generated on Windows**
→ Install GTK runtime from the WeasyPrint Windows docs, or the PDF step will be skipped (HTML report still generated).
