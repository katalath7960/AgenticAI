# WFH Event Scanner

End-to-end event check-in system for ~1,000-attendee events. A LangGraph agent reads an attendee CSV, generates unique barcodes + QR codes, emails them in bulk, and exposes a React scanner app for on-site check-in plus a Streamlit admin dashboard.

Built for the Edureka Applied-AI capstone. Designed to run offline on a single event laptop.

---

## Why this exists

Before: an Excel sheet of 1,000 guests, manual lookup at the door, slow lines, misdirected attendees, no visibility into who was sent what.

After: one agent run sends every invitee a personal barcode, staff scan it with a phone camera, the correct table color pops up in ~15 ms, and admin sees live attendance from Streamlit. All free/open-source: Gmail SMTP, `python-barcode`, `html5-qrcode`, SQLite.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   CSV ──► LangGraph Agent ──► Barcodes ──► Gmail SMTP ──► Attendees  │
│            (api, graph.py)      (PNGs)                               │
│                  │                                                   │
│                  ▼                                                   │
│            SQLite (attendees, scan_log)                              │
│                  ▲                                                   │
│   ┌──────────────┼──────────────────┐                                │
│   │              │                  │                                │
│   FastAPI (:8000) ──► React scanner (:5173)  ──► staff phones        │
│         │                                                            │
│         └──► Streamlit admin (:8501)  ──► event organisers           │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Tech stack:** FastAPI · SQLAlchemy + Alembic · SQLite · LangGraph · pandas · python-barcode + qrcode · React + Vite + Bootstrap · html5-qrcode · Streamlit · Docker Compose.

---

## Project layout

```
WFHEventScanner-Ver1/
├── agent/                     LangGraph agent + nodes
│   ├── graph.py               read_csv → generate_barcodes → send_emails → update_status
│   ├── state.py
│   └── nodes/
├── api/                       FastAPI backend
│   ├── main.py                app + CORS + middleware + /api/stats
│   ├── models.py              Attendee, ScanLog
│   ├── database.py            engine + SessionLocal + get_db
│   ├── schemas.py             Pydantic v2 schemas
│   ├── import_csv.py          idempotent CSV → DB upsert
│   └── routers/               attendees, scanner, agent
├── frontend/                  React + Vite + Bootstrap
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── components/        Navbar, Scanner, AttendeeCard, ScanLog
│       └── pages/             StatsPage
├── streamlit_app/app.py       Dashboard / Attendees / Run Agent / Scan Log
├── data/
│   ├── input/WFHAttendees.csv
│   ├── output/barcodes/
│   └── processed/
├── tests/                     pytest — 24 fast + 2 slow
├── docker/                    Dockerfile.api / .frontend / .streamlit + compose
├── docs/                      DEPLOYMENT.md, LOAD_REPORT.md, DEMO.md
├── alembic/                   migrations
├── run_api.py                 port-aware launcher (Windows-friendly)
├── .env.example
└── requirements.txt
```

---

## Local setup (bare metal, recommended for dev)

### 1. Clone and enter
```bash
cd WFHEventScanner-Ver1
```

### 2. Create the venv (Python 3.11)
**Windows:**
```bat
python -m venv .venv
.venv\Scripts\activate
```
**macOS / Linux:**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 3. Install
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env     # Windows: copy .env.example .env
```
Edit [.env](.env). Required for emailing:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_gmail@gmail.com
SMTP_PASSWORD=<16-char-app-password>   # NOT your login password
FROM_EMAIL=your_gmail@gmail.com
EVENT_NAME=WFH Annual Event
API_BASE_URL=http://localhost:8000
```
Generate a Gmail App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (requires 2-step verification).

### 5. Initialise the database
```bash
alembic upgrade head
```

### 6. Start the three services (three terminals)

**Terminal 1 — API**
```bash
python run_api.py               # picks a free port automatically
```
`run_api.py` probes a list of candidate ports (8000, 18000, 8080, …) and binds to the first one Windows allows. Watch the output — if it chooses anything other than 8000, update `API_BASE_URL` in `.env` and `VITE_API_BASE_URL` in `frontend/.env` to match, then restart Streamlit and Vite.

**Terminal 2 — Streamlit admin**
```bash
streamlit run streamlit_app/app.py
```
Opens http://localhost:8501.

**Terminal 3 — React scanner**
```bash
cd frontend
set NODE_ENV=development        # Windows; use `export` on POSIX
npm install                     # first time only
npm run dev
```
Opens http://localhost:5173. The camera requires HTTPS or `localhost` origin — don't use `127.0.0.1` or a LAN IP without TLS.

### 7. First-time data flow

1. Drop (or edit) `data/input/WFHAttendees.csv`. Columns: `Sno, FirstName, LastName, Color, EmailAddress, Status, EventName`.
2. Import + generate + email in one go:
   ```bash
   curl -X POST http://localhost:<api-port>/api/agent/run
   ```
   (Or click "Run Agent Now" in Streamlit.) Poll `GET /api/agent/runs/<id>` for progress.
3. Staff scan with the React app at `/`. Each scan flips `status → CheckedIn` and writes to `scan_log`.

---

## Docker setup (production-shaped)

```bash
cp .env.example .env            # edit SMTP creds
docker compose -f docker/docker-compose.yml up --build
```
Three services come up:

| Service | URL |
|---|---|
| API | http://localhost:8000 (OpenAPI at `/docs`) |
| Frontend | http://localhost:5173 |
| Streamlit | http://localhost:8501 |

Shared volume `./data` → `/app/data` so API + Streamlit see the same SQLite file and barcode PNGs. Streamlit reaches the API via the internal Docker DNS name `http://api:8000`.

For cloud deployment (Azure Container Apps, Render, Fly), see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

---

## Running the test suite

```bash
pytest                           # 24 fast tests, ~5 s
pytest -m slow -s                # + 1,000-row load test with timing, ~30 s
```
Coverage: CSV importer, barcode generation, SMTP send (mocked), LangGraph nodes, every API endpoint, E2E run, p95 scan latency.

Load numbers from the current host: see [docs/LOAD_REPORT.md](docs/LOAD_REPORT.md).

---

## Day-of-event runbook

**Day -3**
- [ ] Finalise `data/input/WFHAttendees.csv` (no blank emails, unique emails, valid color codes).
- [ ] Generate a fresh Gmail App Password — rotate any that have been shared.
- [ ] Run the agent on a test CSV of 3 attendees; confirm emails arrive with barcodes rendered.

**Day -1**
- [ ] Run the full agent: `POST /api/agent/run`. Confirm all 1,000 emails go out (SMTP throttle → ~8 min).
- [ ] Sanity-check `data/processed/WFHAttendees_processed.xlsx` in Excel.
- [ ] Back up `wfh_event.db` and the `data/` folder.

**Day 0 — morning**
- [ ] Boot the event laptop on venue WiFi. Disable Windows auto-updates / sleep.
- [ ] Start: `python run_api.py`, `streamlit run …`, `npm run dev`.
- [ ] From each staff phone, open `http://<laptop-ip>:5173`, grant camera permission, scan a printed test barcode. Confirm check-in.
- [ ] Open Streamlit dashboard on an event-info monitor.

**During event**
- [ ] Watch Streamlit for stuck scans (e.g., duplicate bursts).
- [ ] If a guest's email never arrived: look them up in the Attendees page → "Resend now".
- [ ] If the API hangs: Ctrl+C the uvicorn window, `python run_api.py` again. State persists in SQLite.

**Day +1**
- [ ] Export the scan log (CSV button on the log page) for post-event analytics.
- [ ] Archive the `data/` folder, commit the processed CSV/XLSX.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `uvicorn` → `WinError 10013` | Windows reserved port range | Use `python run_api.py` — it auto-picks a free port |
| Frontend can't reach API | Port mismatch | Edit `frontend/.env` `VITE_API_BASE_URL`, **restart `npm run dev`** (Vite reads env at start only) |
| CORS error in browser console | Frontend origin not in allowlist | Add the origin to `cors_origins` in [api/main.py](api/main.py) and restart |
| Camera preview blank | Not on `localhost` / HTTPS | Use `http://localhost:5173`; on a LAN, terminate TLS (mkcert/Caddy) |
| Gmail "Username and Password not accepted" | Using login password, not App Password | Regenerate at myaccount.google.com/apppasswords |
| `502 email send failed` on resend | Any SMTP exception | Real traceback is in the API terminal — read the last block |
| SQLite `database is locked` | Multiple writers | For >10 concurrent users, switch `DATABASE_URL` to Postgres |
| `ModuleNotFoundError` on startup | Wrong venv active | `.venv\Scripts\activate` *inside* the project dir; `where python` should show `WFHEventScanner-Ver1\.venv\…` |
| Frontend `npm install` finishes fast but `vite` is missing | `NODE_ENV=production` is set | `set NODE_ENV=development` then reinstall |

---

## Security

- **Never commit `.env`.** It's in `.gitignore` by default.
- Use Gmail **App Passwords**, not your account password. Rotate if shared.
- Barcode payloads encode only `sno` + color + 8-char email hash — no raw PII.
- The API trusts the local network. Before exposing publicly, add auth and TLS (see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)).

---

## Quick start — exact commands

Once everything is installed (steps 1–5 above), these are the three commands to boot the full stack. Run each in its own terminal and leave it running.

### Terminal 1 — API

```bash
cd c:\Damu\AppliedAI\Edureka-AgenticAI\Python\WFHEventScanner-ver1
.venv\Scripts\python.exe run_api.py
```

Watch the output for the port it picked (e.g. `bound: http://127.0.0.1:18000`). If it's not `8000`, update `API_BASE_URL` in [.env](.env) and `VITE_API_BASE_URL` in [frontend/.env](frontend/.env) to match — then restart Streamlit and the React dev server so they pick up the new values.

Sanity check: open `http://localhost:<port>/docs` — Swagger UI should load.

### Terminal 2 — Streamlit admin dashboard

```bash
cd c:\Damu\AppliedAI\Edureka-AgenticAI\Python\WFHEventScanner-ver1
streamlit run streamlit_app/app.py
```

Opens `http://localhost:8501` in your browser automatically.

### Terminal 3 — React scanner

```bash
cd c:\Damu\AppliedAI\Edureka-AgenticAI\Python\wfheventscanner-ver1\frontend
npm run dev
```

Opens `http://localhost:5173`. Use **this** URL (not `127.0.0.1` or a LAN IP) so the browser grants camera access.

### Stopping

Press `Ctrl+C` in each terminal. No cleanup needed — state persists in `wfh_event.db`.

---

## Status & links

- Implementation plan: [TASKS.md](TASKS.md) · tech scope: [TECH_STACK.md](TECH_STACK.md)
- Deployment: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- Load numbers: [docs/LOAD_REPORT.md](docs/LOAD_REPORT.md)
- Demo script: [docs/DEMO.md](docs/DEMO.md)
