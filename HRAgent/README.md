# HR Agent App

An agentic HR management system built with **LangGraph**, **LangChain**, **FastAPI**, and **Streamlit**. A ReAct agent backed by a **SQLite** database handles employee management, leave requests, recruitment, and HR policy Q&A — all through a conversational chat interface and a multi-tab dashboard.

---

## Project Structure

```
HRAgent/
├── hr_database.py     # SQLite schema, seed data, and all CRUD helpers
├── hr_tools.py        # 12 LangChain @tool functions used by the agent
├── hr_agent.py        # LangGraph ReAct agent (create_react_agent)
├── api.py             # FastAPI REST API (chat + CRUD endpoints)
├── app.py             # Streamlit multi-tab dashboard UI
├── requirements.txt   # Python dependencies
├── Dockerfile         # Single python:3.11-slim image for both services
├── docker-compose.yml # Orchestrates hr-api (8001) + hr-app (8502)
└── .dockerignore      # Excludes cache, secrets, and DB files from image
```

---

## Architecture

### LangGraph ReAct Agent Flow

```
User message
     │
     ▼
┌──────────────┐
│  hr_agent.py │  create_react_agent(llm, tools=ALL_TOOLS)
└──────┬───────┘
       │
       ▼
┌──────────────┐      ┌─────────────────────────────────────────┐
│  Agent node  │─────►│  Tool call? (one or more of 12 tools)   │
│  (LLM)       │◄─────│  lookup_employee, apply_for_leave, etc. │
└──────┬───────┘      └────────────────────┬────────────────────┘
       │                                   │
       │  No more tool calls               │  Tool result
       ▼                                   └──────────────► Agent node (loop)
    Final answer
```

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        User                             │
└──────────────┬──────────────────┬───────────────────────┘
               │                  │
               ▼                  ▼
  ┌────────────────────┐  ┌──────────────────────┐
  │  Streamlit UI      │  │  FastAPI (api.py)     │
  │  app.py            │  │  POST /chat           │
  │  port 8502         │  │  GET/POST CRUD        │
  └──────────┬─────────┘  └──────────┬───────────┘
             │ HTTP /chat             │
             └────────────┬──────────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │  LangGraph ReAct Agent  │
             │  hr_agent.py            │
             └──────────┬──────────────┘
                        │  calls tools
                        ▼
             ┌─────────────────────────┐
             │  hr_tools.py (12 tools) │
             └──────────┬──────────────┘
                        │
                        ▼
             ┌─────────────────────────┐    ┌─────────────────┐
             │  SQLite (hr_data.db)    │    │  OpenAI API     │
             │  hr_database.py         │    │  gpt-4o-mini    │
             └─────────────────────────┘    └─────────────────┘
```

---

## File Descriptions

### `hr_database.py`
SQLite data layer — owns the connection, schema, seed data, and all CRUD functions.

**Tables:**

| Table | Description |
|---|---|
| `employees` | Employee directory (8 seed records across 3 departments) |
| `leave_requests` | Leave applications with status tracking |
| `jobs` | Job postings (3 seed open positions) |
| `applicants` | Job applicants with pipeline status |
| `hr_policies` | Policy documents (6 seed policies) |
| `hr_policies_fts` | SQLite FTS5 virtual table for full-text policy search |

**Key functions:** `init_db()`, `get_db()`, `search_employees()`, `get_employee()`, `create_leave_request()`, `update_leave_status()`, `search_policies()`, `create_job()`, `create_applicant()`, `update_applicant_status()`

---

### `hr_tools.py`
12 LangChain `@tool` functions registered with the ReAct agent.

| Tool | Purpose |
|---|---|
| `lookup_employee` | Search employees by name, dept, or role |
| `get_employee_details` | Full employee profile + manager name |
| `check_leave_balance` | Remaining leave days for an employee |
| `apply_for_leave` | Submit a leave request |
| `get_leave_requests` | Leave history (filterable by status) |
| `approve_leave` | Approve or reject a leave request |
| `search_hr_policy` | FTS5 policy search — returns top 3 matches |
| `list_job_openings` | Open positions (filterable by department) |
| `post_job` | Create a new job posting |
| `submit_application` | Apply for a job |
| `list_applicants` | Applicants for a job |
| `update_applicant_status` | Move applicant through pipeline |

---

### `hr_agent.py`
LangGraph ReAct agent powered by `create_react_agent`.

- **LLM:** `gpt-4o-mini` (configurable via `OPENAI_MODEL` env var)
- **Temperature:** 0 for consistent, deterministic HR responses
- **System prompt:** Defines HR assistant persona, today's date, and guidelines
- **`run(message, history)`** — main entry point called by the API

---

### `api.py`
FastAPI REST API with 12 endpoints.

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/chat` | HR agent chat (accepts history) |
| `GET` | `/employees` | List employees (`?department=` filter) |
| `GET` | `/employees/{id}` | Employee detail |
| `GET` | `/leave/{employee_id}` | Leave history (`?status=` filter) |
| `POST` | `/leave` | Submit leave request |
| `PUT` | `/leave/{id}/approve` | Approve or reject leave |
| `GET` | `/jobs` | List open jobs (`?department=` filter) |
| `POST` | `/jobs` | Post new job |
| `GET` | `/jobs/{id}/applicants` | List applicants |
| `POST` | `/jobs/{id}/apply` | Submit application |
| `PUT` | `/applicants/{id}/status` | Update applicant status |

**Interactive docs:** http://localhost:8001/docs

---

### `app.py`
Streamlit dashboard with 5 pages (sidebar navigation):

| Page | Features |
|---|---|
| **Chat** | Conversational HR assistant, message history, example questions |
| **Employees** | Department filter, sortable table, employee detail metrics |
| **Leave** | Apply form, history table with status filter, approve/reject panel |
| **Recruitment** | Job cards, apply form, applicant pipeline table, post new job |
| **Policies** | Full-text policy search powered by the HR agent |

---

## Seed Data

### Employees (8)
| ID | Name | Department | Role |
|---|---|---|---|
| 1 | Alice Johnson | Engineering | VP of Engineering |
| 2 | Bob Smith | Engineering | Senior Engineer |
| 3 | Carol White | Engineering | Software Engineer |
| 4 | David Lee | HR | HR Manager |
| 5 | Eva Martinez | HR | HR Coordinator |
| 6 | Frank Brown | Marketing | Marketing Director |
| 7 | Grace Kim | Marketing | Content Strategist |
| 8 | Henry Wilson | Engineering | DevOps Engineer |

### Job Openings (3)
- Senior Python Developer — Engineering
- HR Business Partner — HR
- Growth Marketing Manager — Marketing

### HR Policies (6)
Annual Leave · Sick Leave · Personal Leave · Code of Conduct · Benefits Overview · Internal Referral Policy

---

## Environment Variables

Only one variable is **required**:

```env
OPENAI_API_KEY=your_openai_api_key
```

Optional overrides:

```env
OPENAI_MODEL=gpt-4o-mini    # default: gpt-4o-mini
HR_DB_PATH=hr_data.db       # default: hr_data.db (relative to CWD)
HR_API_URL=http://localhost:8001  # used by Streamlit app to reach the API
```

---

## Docker Deployment

### Build and run

```bash
cd HRAgent
docker compose up --build
```

| Service | URL |
|---|---|
| FastAPI (HR API) | http://localhost:8001 |
| Swagger UI | http://localhost:8001/docs |
| Streamlit Dashboard | http://localhost:8502 |

### Deployment diagram

```
Docker Desktop
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  ┌────────────────────────┐  ┌────────────────────────┐  │
│  │   hr-api               │  │   hr-app               │  │
│  │   FastAPI + uvicorn    │  │   Streamlit            │  │
│  │   localhost:8001       │  │   localhost:8502       │  │
│  └───────────┬────────────┘  └───────────┬────────────┘  │
│              │   depends_on (healthy)     │               │
│              └──────────┬─────────────────┘               │
│                         │  (same Docker image)            │
│              ┌──────────▼──────────┐                      │
│              │   python:3.11-slim  │                      │
│              │   + curl + deps     │                      │
│              │   + hr_data.db      │  (seeded at build)   │
│              └─────────────────────┘                      │
└──────────────────────────────────────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │   OpenAI API        │
              │   (external)        │
              └─────────────────────┘
```

> Note: `hr-app` waits for `hr-api` to be healthy before starting (via `depends_on`).
> The SQLite database is seeded at image build time inside the container.

### Useful commands

```bash
# View container status
docker compose ps

# Live logs
docker compose logs -f

# Logs for one service
docker compose logs -f hr-api
docker compose logs -f hr-app

# Stop
docker compose down

# Rebuild after code changes
docker compose up --build -d
```

---

## Quick Start (local, no Docker)

```bash
# 1. Install dependencies
pip install -r HRAgent/requirements.txt

# 2. Set OPENAI_API_KEY in Python/.env

# 3. Initialise the database
cd HRAgent
python hr_database.py

# 4. Start the API (terminal 1)
uvicorn api:app --port 8001 --reload

# 5. Start the UI (terminal 2)
streamlit run app.py --server.port 8502

# 6. Or use the CLI agent directly
python hr_agent.py
```

---

## Example Chat Queries

```
Who is in the Engineering department?
What is Bob Smith's leave balance?
Apply for 3 days annual leave for employee 2 from 2026-03-10 to 2026-03-12 — family vacation.
Approve leave request 1.
What are the rules around carrying over annual leave?
Show me open positions in Marketing.
Submit an application for job 1: name=Jane Doe, email=jane@test.com, summary=5 years Python.
Move applicant 2 to interview stage.
What is the employee referral bonus?
```
