# WFHEventScanner — Implementation Plan (TASKS.md)

> Derived from [TECH_STACK.md](TECH_STACK.md). Covers the full scope: automation agent that emails barcodes to ~1,000 attendees, and a scanner web app for on-site check-in.

---

## Legend

| Field | Meaning |
|---|---|
| **Owner** | Team role responsible (PM / DB-Infra / API-Coding / Frontend / QA) |
| **Priority** | P0 (blocker) → P3 (nice-to-have) |
| **Depends** | Task IDs that must be complete first |
| **AC** | Acceptance criteria — how we know it's done |

---

## Execution Phases (high-level)

```
Phase 0  Bootstrap          TASK-001 → 003
Phase 1  Database           TASK-004 → 006
Phase 2  Barcode Engine     TASK-007 → 008
Phase 3  Email Engine       TASK-009 → 010
Phase 4  LangGraph Agent    TASK-011 → 014
Phase 5  FastAPI Backend    TASK-015 → 020
Phase 6  React Scanner UI   TASK-021 → 027
Phase 7  Streamlit Admin    TASK-028 → 031
Phase 8  Containerization   TASK-032 → 034
Phase 9  QA / Tests         TASK-035 → 038
Phase 10 Docs & Handover    TASK-039 → 040
```

---

# Phase 0 — Project Bootstrap

### TASK-001: Repo & Tooling Setup
**Owner:** PM · **Priority:** P0 · **Depends:** —

Steps:
1. Confirm working directory `WFHEventScanner-Ver1/` is a git-tracked folder.
2. Add `.gitignore` covering: `__pycache__/`, `*.pyc`, `.env`, `.venv/`, `node_modules/`, `dist/`, `build/`, `*.db`, `Data/Output/`, `Data/Processed/`, `.pytest_cache/`, `.streamlit/secrets.toml`.
3. Create `README.md` stub (project name, one-line description, link to TASKS.md).
4. Create Python 3.11 virtual environment: `python -m venv .venv`.
5. Document activation in README for Windows (`.venv\Scripts\activate`) and POSIX (`source .venv/bin/activate`).

**AC:** `git status` is clean of generated files; venv activates cleanly.

---

### TASK-002: Project Directory Structure
**Owner:** API-Coding · **Priority:** P0 · **Depends:** TASK-001

Create this layout:
```
WFHEventScanner-Ver1/
├── agent/                       # LangGraph automation agent
│   ├── __init__.py
│   ├── graph.py                 # graph wiring
│   ├── state.py                 # typed state object
│   └── nodes/
│       ├── __init__.py
│       ├── read_csv.py
│       ├── generate_barcode.py
│       ├── send_email.py
│       └── update_status.py
├── api/                         # FastAPI backend
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── routers/
│       ├── __init__.py
│       ├── attendees.py
│       ├── scanner.py
│       └── agent.py
├── frontend/                    # React + Bootstrap scanner
│   ├── public/
│   └── src/
│       ├── components/
│       │   ├── Navbar.jsx
│       │   ├── Scanner.jsx
│       │   ├── AttendeeCard.jsx
│       │   └── ScanLog.jsx
│       ├── App.jsx
│       └── index.js
├── streamlit_app/               # Admin dashboard
│   └── app.py
├── data/
│   ├── input/
│   │   └── WFHAttendees.csv
│   ├── output/
│   │   └── barcodes/
│   └── processed/
├── tests/
│   ├── test_agent.py
│   ├── test_api.py
│   └── test_email.py
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.frontend
│   ├── Dockerfile.streamlit
│   └── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

Steps:
1. `mkdir` each directory.
2. Drop `.gitkeep` in empty leaf folders (`data/output/barcodes/`, `data/processed/`, `frontend/public/`).
3. Create empty `__init__.py` in every Python package.

**AC:** Directory tree matches spec; `pytest --collect-only` discovers the `tests/` package without error.

---

### TASK-003: Dependencies & Environment Config
**Owner:** API-Coding · **Priority:** P0 · **Depends:** TASK-002

Steps:
1. Author `requirements.txt`:
   ```
   # Core
   fastapi==0.111.*
   uvicorn[standard]==0.29.*
   python-dotenv==1.0.*
   pydantic==2.7.*

   # Data
   pandas==2.2.*
   openpyxl==3.1.*
   xlsxwriter==3.2.*

   # Database
   sqlalchemy==2.0.*
   alembic==1.13.*

   # LangGraph
   langgraph==0.1.*
   langchain-core==0.2.*

   # Barcode / QR
   python-barcode==0.15.*
   qrcode[pil]==7.4.*
   Pillow==10.*

   # Streamlit
   streamlit==1.35.*

   # Testing
   pytest==8.2.*
   pytest-asyncio==0.23.*
   httpx==0.27.*
   ```
2. Author `.env.example`:
   ```
   DATABASE_URL=sqlite:///./wfh_event.db
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_gmail@gmail.com
   SMTP_PASSWORD=your_app_password
   FROM_EMAIL=your_gmail@gmail.com
   EVENT_NAME=WFH Annual Event
   API_BASE_URL=http://localhost:8000
   BARCODE_OUTPUT_DIR=./data/output/barcodes
   INPUT_CSV=./data/input/WFHAttendees.csv
   ```
3. Copy `.env.example` → `.env` locally and populate SMTP credentials (Gmail App Password, not account password).
4. Run `pip install -r requirements.txt` inside the venv.

**AC:** Clean install succeeds; `python -c "import fastapi, sqlalchemy, langgraph, barcode, qrcode, streamlit"` returns no error.

---

# Phase 1 — Database Layer

### TASK-004: Database Schema & ORM Models
**Owner:** DB-Infra · **Priority:** P1 · **Depends:** TASK-003

Tables:

**`attendees`**
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | |
| sno | INTEGER UNIQUE | original CSV row number |
| first_name | VARCHAR(100) | |
| last_name | VARCHAR(100) | |
| email | VARCHAR(200) UNIQUE | |
| color | VARCHAR(50) | table color code |
| event_name | VARCHAR(200) | |
| status | VARCHAR(50) DEFAULT 'Pending' | Pending / Sent / CheckedIn |
| barcode_path | VARCHAR(500) NULLABLE | |
| email_sent_at | DATETIME NULLABLE | |
| checked_in_at | DATETIME NULLABLE | |
| created_at | DATETIME DEFAULT NOW | |

**`scan_log`**
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | |
| attendee_id | INTEGER FK → attendees.id | |
| scanned_at | DATETIME DEFAULT NOW | |
| scanned_by | VARCHAR(100) | staff id/name |
| is_duplicate | BOOLEAN DEFAULT FALSE | |

Steps:
1. Implement `api/database.py` — engine from `DATABASE_URL`, `SessionLocal`, `Base`, `get_db()` FastAPI dependency.
2. Implement `api/models.py` — `Attendee` and `ScanLog` ORM classes with a bidirectional `relationship`.
3. Implement `api/schemas.py` — Pydantic v2 schemas: `AttendeeCreate`, `AttendeeRead`, `ScanResult`, `ImportSummary`.

**AC:** `python -c "from api.database import Base; from api import models; Base.metadata.create_all(bind=__import__('api.database', fromlist=['engine']).engine)"` creates both tables in SQLite.

---

### TASK-005: Alembic Migrations
**Owner:** DB-Infra · **Priority:** P1 · **Depends:** TASK-004

Steps:
1. `alembic init alembic` at project root.
2. Edit `alembic/env.py`:
   - Load `.env` via `python-dotenv`.
   - Set `sqlalchemy.url` from `os.getenv("DATABASE_URL")`.
   - Set `target_metadata = Base.metadata` (import from `api.database`).
3. `alembic revision --autogenerate -m "initial schema"`.
4. `alembic upgrade head`.

**AC:** Both tables exist in the SQLite file; `alembic downgrade base` and re-upgrade are clean.

---

### TASK-006: CSV Importer
**Owner:** DB-Infra · **Priority:** P1 · **Depends:** TASK-005

Steps:
1. Implement `api/import_csv.py` with `import_attendees(csv_path: str) -> ImportSummary`:
   - Read `data/input/WFHAttendees.csv` with `pandas.read_csv`.
   - Normalize columns (strip/title-case names, lowercase emails).
   - Split `InviteeName` into `first_name` / `last_name` (split on last space).
   - Upsert by `email`: update existing row's mutable fields, insert if missing.
   - Count `imported`, `updated`, `skipped`, collect `errors` (malformed rows).
2. Expose a CLI: `python -m api.import_csv --csv data/input/WFHAttendees.csv`.

**AC:** Running twice in a row produces no duplicates; `SELECT COUNT(*) FROM attendees` equals distinct emails in the CSV.

---

# Phase 2 — Barcode Generation

### TASK-007: Barcode Generator Module
**Owner:** API-Coding · **Priority:** P1 · **Depends:** TASK-006

Steps:
1. Implement `agent/nodes/generate_barcode.py` with `generate_barcode(attendee: dict, output_dir: Path) -> dict`.
2. Encoded payload: `WFH-{sno:04d}-{color}-{email_hash8}` (hash keeps it short but unique; avoids PII in the barcode).
3. Produce two artifacts per attendee:
   - Code128 PNG via `python-barcode` → `data/output/barcodes/barcode_{sno:04d}.png`.
   - QR PNG via `qrcode` → `data/output/barcodes/qr_{sno:04d}.png` (for phone cameras).
4. Return `{ "barcode_path": ..., "qr_path": ..., "payload": ... }`.
5. Wrap each attendee in try/except — log failures, continue.

**AC:** Given 3 sample rows, 6 PNGs are produced and open as valid images; re-run is idempotent (overwrites cleanly).

---

### TASK-008: Bulk Barcode Job
**Owner:** API-Coding · **Priority:** P1 · **Depends:** TASK-007

Steps:
1. Add `generate_all_barcodes(db: Session) -> dict` helper in `agent/nodes/generate_barcode.py`.
2. Iterate attendees with `status='Pending'` and no `barcode_path`; generate + persist path to DB.
3. Return `{ "generated": N, "failed": [sno,...] }`.

**AC:** After run, every Pending attendee has `barcode_path` populated; failed rows are reported.

---

# Phase 3 — Email Module

### TASK-009: SMTP Email Sender
**Owner:** API-Coding · **Priority:** P1 · **Depends:** TASK-008

Steps:
1. Implement `agent/nodes/send_email.py::send_invite(attendee, barcode_path, qr_path) -> bool`.
2. Use stdlib `smtplib.SMTP` + `email.message.EmailMessage`.
3. Load SMTP creds from env.
4. Build multipart message:
   - Plain text fallback + HTML body with event name, attendee first name, color-coded table, instructions.
   - Attach `barcode_{sno}.png` and `qr_{sno}.png` (inline `cid:` references in HTML).
5. On success, set `status='Sent'` and `email_sent_at=NOW()`.
6. On failure, leave status as-is and log the exception with `sno`.
7. Throttle: `time.sleep(0.5)` between sends to stay under Gmail's burst limits.

**AC:** Sending to a personal test address yields an email with embedded barcode + QR that scans correctly on a phone.

---

### TASK-010: Bulk Email Job with Resume
**Owner:** API-Coding · **Priority:** P2 · **Depends:** TASK-009

Steps:
1. `send_all_invites(db)` iterates attendees where `status='Pending'` AND `barcode_path IS NOT NULL`.
2. Commit after each successful send so a crash is resumable.
3. Return `{ "sent": N, "failed": [...] }`.

**AC:** Killing the process mid-run and restarting it resumes without re-sending to already-Sent attendees.

---

# Phase 4 — LangGraph Automation Agent

### TASK-011: Agent State & Graph Skeleton
**Owner:** API-Coding · **Priority:** P1 · **Depends:** TASK-010

Steps:
1. Define `agent/state.py`:
   ```python
   class AgentState(TypedDict):
       csv_path: str
       imported: int
       barcodes_generated: int
       emails_sent: int
       errors: list[str]
   ```
2. Author `agent/graph.py` — `StateGraph(AgentState)` with nodes wired:
   `START → read_csv → generate_barcodes → send_emails → update_status → END`.
3. Each node is a thin adapter calling the concrete functions from `agent/nodes/*.py` and returning a partial state update.

**AC:** `python -c "from agent.graph import build_graph; build_graph().invoke({'csv_path':'data/input/WFHAttendees.csv'})"` runs end-to-end on a 3-row sample CSV.

---

### TASK-012: Node — read_csv
**Owner:** API-Coding · **Priority:** P1 · **Depends:** TASK-011

Steps:
1. Call `import_attendees()` from TASK-006.
2. Return `{"imported": summary.imported}` and append any errors to `state["errors"]`.

**AC:** After node runs, DB reflects CSV contents; state carries correct count.

---

### TASK-013: Node — generate_barcodes + send_emails
**Owner:** API-Coding · **Priority:** P1 · **Depends:** TASK-012

Steps:
1. `generate_barcodes` node calls `generate_all_barcodes`; writes counts to state.
2. `send_emails` node calls `send_all_invites`; writes counts to state.
3. Both nodes must be *retryable* — re-invoking the graph re-processes only Pending items.

**AC:** Second invocation on the same DB is a no-op (nothing to do).

---

### TASK-014: Node — update_status & Excel/CSV Writeback
**Owner:** API-Coding · **Priority:** P2 · **Depends:** TASK-013

Steps:
1. Export processed roster to `data/processed/WFHAttendees_processed.csv` using pandas.
2. Columns: original CSV + `Status` (Sent/Pending) + `BarcodePath` + `EmailSentAt`.
3. Also emit `.xlsx` copy via `openpyxl` so the PM can open it in Excel.

**AC:** Processed files exist and match DB state row-for-row.

---

# Phase 5 — FastAPI Backend

### TASK-015: FastAPI App Shell
**Owner:** API-Coding · **Priority:** P1 · **Depends:** TASK-005

Steps:
1. `api/main.py`: create `FastAPI(title="WFH Event Scanner API")`, mount CORS for `http://localhost:5173` and `http://localhost:8501`.
2. Register routers: `attendees`, `scanner`, `agent`.
3. Health endpoint `GET /health` → `{"status":"ok"}`.

**AC:** `uvicorn api.main:app --reload` serves `GET /health` → 200.

---

### TASK-016: Attendees Endpoints
**Owner:** API-Coding · **Priority:** P1 · **Depends:** TASK-015, TASK-006

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/attendees/import` | Trigger CSV import |
| GET | `/api/attendees` | List (filter by `status`, paginate) |
| GET | `/api/attendees/{id}` | Detail |
| GET | `/api/attendees/{id}/barcode` | Return the barcode PNG |

**AC:** OpenAPI docs at `/docs` list all four; manual requests return correct JSON/PNG.

---

### TASK-017: Scanner Endpoint
**Owner:** API-Coding · **Priority:** P1 · **Depends:** TASK-016

`POST /api/scan` with body `{ "payload": "WFH-0001-Blue-abc12345", "scanned_by": "staff1" }`.

Logic:
1. Parse payload → extract `sno`.
2. Look up attendee; if missing → 404.
3. Check for prior successful scan today; if found → insert `scan_log` with `is_duplicate=true` and return `{ "duplicate": true, ... }`.
4. Otherwise insert scan_log, set `attendees.status='CheckedIn'`, `checked_in_at=NOW()`.
5. Return `{ attendee: {...}, duplicate: false, already_checked_in: bool }`.

**AC:** First scan succeeds and flips status; second scan returns `duplicate: true` without changing `checked_in_at`.

---

### TASK-018: Agent Trigger Endpoint
**Owner:** API-Coding · **Priority:** P2 · **Depends:** TASK-017, TASK-014

`POST /api/agent/run` — kicks off the LangGraph agent asynchronously (BackgroundTasks) and returns `{ "run_id": "...", "status": "started" }`.

`GET /api/agent/runs/{run_id}` — returns last state snapshot.

**AC:** Endpoint starts the graph; polling endpoint reflects progress (imported → generated → sent).

---

### TASK-019: Stats Endpoint
**Owner:** API-Coding · **Priority:** P2 · **Depends:** TASK-017

`GET /api/stats` → `{ total, pending, sent, checked_in, scans_today }`.

**AC:** Numbers match hand-counted DB queries.

---

### TASK-020: Error Handling & Logging
**Owner:** API-Coding · **Priority:** P2 · **Depends:** TASK-019

Steps:
1. Global exception handler for `HTTPException` + `SQLAlchemyError` → uniform JSON.
2. Structured logging (`logging.basicConfig`, JSON format optional).
3. Request ID middleware (`X-Request-ID` header passthrough / generate).

**AC:** 500s return JSON (not HTML); logs include request IDs.

---

# Phase 6 — React Scanner Web App

### TASK-021: React Project Scaffold
**Owner:** Frontend · **Priority:** P1 · **Depends:** TASK-015

Steps:
1. `npm create vite@latest frontend -- --template react`.
2. `npm install bootstrap react-bootstrap html5-qrcode axios react-router-dom`.
3. Import Bootstrap CSS in `src/main.jsx`.
4. Set `VITE_API_BASE_URL=http://localhost:8000` in `frontend/.env`.

**AC:** `npm run dev` serves a blank Bootstrap-themed page on :5173.

---

### TASK-022: App Shell & Routing
**Owner:** Frontend · **Priority:** P1 · **Depends:** TASK-021

Routes:
- `/` → Scanner page
- `/log` → Scan log
- `/stats` → Stats dashboard

Shared `<Navbar />` with event name + nav links.

**AC:** Navigation works; unknown routes show a 404 component.

---

### TASK-023: Scanner Component
**Owner:** Frontend · **Priority:** P1 · **Depends:** TASK-022

Steps:
1. `Scanner.jsx` uses `html5-qrcode`'s `Html5QrcodeScanner`.
2. Prefers rear camera (`facingMode: "environment"`).
3. On successful scan → call `POST /api/scan` via axios.
4. Pause scanner for 2 s after each scan to prevent rapid duplicates.
5. Button to toggle camera on/off and switch cameras.

**AC:** Scanning a barcode PNG on screen produces a real API call and surfaces the response.

---

### TASK-024: AttendeeCard Component
**Owner:** Frontend · **Priority:** P1 · **Depends:** TASK-023

Steps:
1. Large, readable card showing: full name, color swatch (background matching `color` field), event name, check-in time.
2. Prominent green ✓ for success, red ✗ for not-found, yellow ⚠ for duplicate.
3. Auto-dismiss after 5 s, or "Next" button.

**AC:** Designer review passes at 2 m viewing distance (event staff use case).

---

### TASK-025: Scan Log Page
**Owner:** Frontend · **Priority:** P2 · **Depends:** TASK-024

Steps:
1. Table of recent scans: time, name, color, staff, duplicate flag.
2. Auto-refresh every 5 s (polling; can swap for SSE later).
3. "Export CSV" button.

**AC:** Log updates within 5 s of a scan happening.

---

### TASK-026: Stats Page
**Owner:** Frontend · **Priority:** P2 · **Depends:** TASK-025

Steps:
1. Cards for: Total attendees, Sent, Checked in, % attendance.
2. Color-breakdown bar chart (use react-bootstrap + simple CSS bars; no heavy chart lib).

**AC:** Numbers match `/api/stats`.

---

### TASK-027: Frontend Polish
**Owner:** Frontend · **Priority:** P3 · **Depends:** TASK-026

Steps:
1. Loading spinners, error toasts.
2. Responsive layout: works on tablet and phone.
3. Dark-mode toggle via Bootstrap data-bs-theme.

**AC:** Lighthouse mobile score ≥ 85.

---

# Phase 7 — Streamlit Admin App

### TASK-028: Streamlit Scaffold
**Owner:** Frontend (Streamlit) · **Priority:** P2 · **Depends:** TASK-019

Steps:
1. `streamlit_app/app.py` with sidebar navigation (Dashboard, Attendees, Run Agent, Scan Log).
2. Shared helper `call_api(path)` reading `API_BASE_URL` from env.

**AC:** `streamlit run streamlit_app/app.py` serves on :8501.

---

### TASK-029: Admin Dashboard Page
**Owner:** Frontend (Streamlit) · **Priority:** P2 · **Depends:** TASK-028

Steps:
1. Summary metrics (`st.metric`) from `/api/stats`.
2. Bar chart by color code.
3. Last 10 scans table.

**AC:** Data matches DB; refreshes on rerun.

---

### TASK-030: Attendees Table Page
**Owner:** Frontend (Streamlit) · **Priority:** P2 · **Depends:** TASK-029

Steps:
1. `st.dataframe` with status filter + email search.
2. Row-level action to re-send invite (calls a yet-to-add `POST /api/attendees/{id}/resend`).

**AC:** Filtering/searching works; resend flips status and triggers new email.

---

### TASK-031: Run Agent Page
**Owner:** Frontend (Streamlit) · **Priority:** P2 · **Depends:** TASK-018

Steps:
1. Button: "Run Agent Now" → `POST /api/agent/run`.
2. Poll `/api/agent/runs/{run_id}` every 2 s; render progress (imported / generated / sent).

**AC:** Button end-to-end triggers real agent and UI reflects progress.

---

# Phase 8 — Containerization & Deployment

### TASK-032: Dockerfiles
**Owner:** DB-Infra · **Priority:** P2 · **Depends:** TASK-020, TASK-027, TASK-031

Steps:
1. `docker/Dockerfile.api` — python:3.11-slim, install requirements, `uvicorn api.main:app`.
2. `docker/Dockerfile.frontend` — node:20-alpine build → nginx:alpine serve.
3. `docker/Dockerfile.streamlit` — python:3.11-slim, `streamlit run streamlit_app/app.py`.
4. Each image uses a non-root user.

**AC:** Each image builds cleanly and runs standalone.

---

### TASK-033: docker-compose
**Owner:** DB-Infra · **Priority:** P2 · **Depends:** TASK-032

Services: `api` (8000), `frontend` (5173/80), `streamlit` (8501). Shared named volume for `./data` and the SQLite file. Env var wiring to `.env`.

**AC:** `docker compose up` boots all three; scanning from frontend hits API and persists to the shared DB.

---

### TASK-034: Deployment Notes (Optional)
**Owner:** DB-Infra · **Priority:** P3 · **Depends:** TASK-033

Steps:
1. Document deploy options (Azure Container Apps / Render / local LAN).
2. For production, recommend swapping SQLite → Postgres (DB driver only).
3. SMTP hardening: use a dedicated service account + App Password.

**AC:** `docs/DEPLOYMENT.md` written; at least one path is verified.

---

# Phase 9 — QA & Testing

### TASK-035: Unit Tests — Agent Nodes
**Owner:** QA · **Priority:** P2 · **Depends:** TASK-014

Coverage:
- `read_csv` with good/bad CSVs (missing columns, blank emails, duplicates).
- `generate_barcode` — payload format, file written, idempotency.
- `send_email` — mock `smtplib.SMTP`, assert call args and status update.

**AC:** `pytest tests/test_agent.py` passes; ≥80% line coverage for `agent/nodes/`.

---

### TASK-036: Integration Tests — API
**Owner:** QA · **Priority:** P2 · **Depends:** TASK-020

Using `httpx.AsyncClient` + `pytest-asyncio`:
- `/api/attendees/import` populates DB.
- `/api/scan` happy path, not-found, duplicate.
- `/api/stats` numbers after a sequence of scans.

**AC:** All endpoint tests green in CI.

---

### TASK-037: End-to-End Smoke Test
**Owner:** QA · **Priority:** P3 · **Depends:** TASK-033

Steps:
1. `docker compose up` in CI.
2. Seed test CSV (5 rows).
3. Trigger agent, assert 5 "emails" sent (capture via SMTP mock server like `aiosmtpd`).
4. Simulate scans via API; verify status transitions.

**AC:** Script exits 0 on green path.

---

### TASK-038: Load Check
**Owner:** QA · **Priority:** P3 · **Depends:** TASK-037

Steps:
1. Generate 1,000-row synthetic CSV.
2. Time the full agent run; target < 15 min with 0.5 s SMTP throttle.
3. Hit `/api/scan` at 5 req/s for 60 s; p95 latency target < 200 ms.

**AC:** Timings recorded in `docs/LOAD_REPORT.md`.

---

# Phase 10 — Documentation & Handover

### TASK-039: README
**Owner:** PM · **Priority:** P2 · **Depends:** TASK-033

Sections:
1. What & Why (1 paragraph).
2. Architecture diagram (ASCII or image).
3. Local setup — venv, `.env`, `alembic upgrade head`, `uvicorn`, `npm run dev`, `streamlit run`.
4. Docker setup — `docker compose up`.
5. Operating runbook — "Day of Event" checklist.
6. Troubleshooting — Gmail App Password, camera permissions, duplicate scans.

**AC:** A new engineer can go from zero to running system in under 30 minutes following the README.

---

### TASK-040: Demo & Handover
**Owner:** PM · **Priority:** P2 · **Depends:** TASK-039

Steps:
1. Record a 5-minute walkthrough: agent run → email received → scan at venue → stats update.
2. Ship slide deck summarizing architecture, metrics, and next-steps.

**AC:** Recording + deck delivered; stakeholder sign-off captured.

---

## Task Index

| ID | Title | Category | Priority | Depends |
|---|---|---|---|---|
| TASK-001 | Repo & Tooling Setup | PM | P0 | — |
| TASK-002 | Project Directory Structure | Backend | P0 | 001 |
| TASK-003 | Dependencies & Env Config | Backend | P0 | 002 |
| TASK-004 | DB Schema & ORM | Database | P1 | 003 |
| TASK-005 | Alembic Migrations | Database | P1 | 004 |
| TASK-006 | CSV Importer | Database | P1 | 005 |
| TASK-007 | Barcode Generator | Backend | P1 | 006 |
| TASK-008 | Bulk Barcode Job | Backend | P1 | 007 |
| TASK-009 | SMTP Email Sender | Backend | P1 | 008 |
| TASK-010 | Bulk Email w/ Resume | Backend | P2 | 009 |
| TASK-011 | LangGraph Skeleton | Agent | P1 | 010 |
| TASK-012 | Node — read_csv | Agent | P1 | 011 |
| TASK-013 | Nodes — barcode + email | Agent | P1 | 012 |
| TASK-014 | Node — update_status/export | Agent | P2 | 013 |
| TASK-015 | FastAPI Shell | API | P1 | 005 |
| TASK-016 | Attendees Endpoints | API | P1 | 015 |
| TASK-017 | Scanner Endpoint | API | P1 | 016 |
| TASK-018 | Agent Trigger Endpoint | API | P2 | 017 |
| TASK-019 | Stats Endpoint | API | P2 | 017 |
| TASK-020 | Error Handling & Logging | API | P2 | 019 |
| TASK-021 | React Scaffold | Frontend | P1 | 015 |
| TASK-022 | App Shell & Routing | Frontend | P1 | 021 |
| TASK-023 | Scanner Component | Frontend | P1 | 022 |
| TASK-024 | AttendeeCard Component | Frontend | P1 | 023 |
| TASK-025 | Scan Log Page | Frontend | P2 | 024 |
| TASK-026 | Stats Page | Frontend | P2 | 025 |
| TASK-027 | Frontend Polish | Frontend | P3 | 026 |
| TASK-028 | Streamlit Scaffold | Streamlit | P2 | 019 |
| TASK-029 | Admin Dashboard | Streamlit | P2 | 028 |
| TASK-030 | Attendees Table Page | Streamlit | P2 | 029 |
| TASK-031 | Run Agent Page | Streamlit | P2 | 018 |
| TASK-032 | Dockerfiles | DevOps | P2 | 020,027,031 |
| TASK-033 | docker-compose | DevOps | P2 | 032 |
| TASK-034 | Deployment Notes | DevOps | P3 | 033 |
| TASK-035 | Unit Tests — Agent | QA | P2 | 014 |
| TASK-036 | Integration Tests — API | QA | P2 | 020 |
| TASK-037 | E2E Smoke Test | QA | P3 | 033 |
| TASK-038 | Load Check | QA | P3 | 037 |
| TASK-039 | README | Docs | P2 | 033 |
| TASK-040 | Demo & Handover | Docs | P2 | 039 |

---

## Team & Ownership Map

| Role | Primary Tasks |
|---|---|
| **Product Manager** | TASK-001, 039, 040 |
| **Backend — DB/Infra** | TASK-004 → 006, 032 → 034 |
| **Backend — API/Coding** | TASK-002, 003, 007 → 020 |
| **Frontend — React** | TASK-021 → 027 |
| **Frontend — Streamlit** | TASK-028 → 031 |
| **QA Engineer** | TASK-035 → 038 |

---

## Open Questions for PM

1. Final color palette — what are the allowed `color` values?
2. SMTP provider — Gmail is planned, but volume (~1,000 emails) may brush Gmail's 500/day soft limit. Should we plan a SendGrid / Mailgun free-tier fallback?
3. Should we support Excel (`.xlsx`) input in addition to CSV, or is CSV final?
4. Who owns the Gmail App Password / shared mailbox for production sends?
5. Is there a network in the venue, or do we need an offline-capable scanner mode?
