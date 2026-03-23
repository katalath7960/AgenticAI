# TASKS.md — Intelligent User Feedback Analysis & Action System
> **Capstone Project** · Agentic AI Certification
> **Tech Stack:** LangGraph · Python 3.11 · SQLite / Postgres · ChromaDB · Streamlit · Docker · Azure
> **Agent Framework:** LangGraph (multi-node StateGraph)
> **LLM:** Claude Opus 4.6 via Anthropic SDK

---

## Quick Reference

| Symbol | Meaning |
|--------|---------|
| 🔴 Critical | Blocks other work; must be done first |
| 🟠 High | Core deliverable; sprint priority |
| 🟡 Medium | Important but not blocking |
| 🟢 Low | Nice-to-have |

| Role | Code | Who |
|------|------|-----|
| Product Manager | `PM` | Product Manager |
| Backend – DB & Infra | `BE-DB` | Backend Dev focused on DB, Infra |
| Backend – API & Agents | `BE-API` | Backend Dev focused on API, Coding |
| Frontend – Streamlit | `FE` | Frontend Dev focused on Streamlit |
| Quality Assurance | `QA` | QA Eng for writing automated tests |

**Story Points (Fibonacci):** 1 · 2 · 3 · 5 · 8 · 13

---

## Proposed Project File Structure

```
capstone/
├── data/
│   ├── input/
│   │   ├── app_store_reviews.csv
│   │   ├── support_emails.csv
│   │   └── expected_classifications.csv
│   └── output/
│       ├── generated_tickets.csv
│       ├── processing_log.csv
│       └── metrics.csv
├── src/
│   ├── agents/
│   │   ├── csv_reader.py
│   │   ├── classifier.py
│   │   ├── bug_analyzer.py
│   │   ├── feature_extractor.py
│   │   ├── ticket_creator.py
│   │   └── quality_critic.py
│   ├── graph/
│   │   ├── state.py          # AgentState TypedDict
│   │   └── pipeline.py       # StateGraph wiring
│   ├── db/
│   │   ├── models.py         # SQLAlchemy ORM
│   │   ├── session.py
│   │   └── chroma_store.py
│   ├── config.py             # Loads config.json + .env
│   └── main.py               # CLI entry point
├── ui/
│   ├── app.py                # Streamlit entry point
│   └── pages/
│       ├── 1_Dashboard.py
│       ├── 2_Run_Pipeline.py
│       ├── 3_Tickets.py
│       ├── 4_Configuration.py
│       └── 5_Analytics.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/
├── config.json
├── .env.example
└── requirements.txt
```

---

## Sprint Plan (4 × 2-week sprints)

| Sprint | Focus | Phases |
|--------|-------|--------|
| Sprint 1 | Setup, mock data, graph skeleton | Phase 0 + Phase 1 (skeleton) |
| Sprint 2 | All 6 agents, DB, ChromaDB | Phase 1 (full) |
| Sprint 3 | Pipeline integration, Streamlit UI | Phase 2 + Phase 3 |
| Sprint 4 | QA, Docker, Azure, demo prep | Phase 4 |

---

## Phase 0 — Project Setup & Mock Data

### PM-001 · Project Kickoff & Architecture Sign-off
| Field | Value |
|-------|-------|
| **Assignee** | Product Manager |
| **Priority** | 🔴 Critical |
| **Story Points** | 3 |
| **Sprint** | 1 |
| **Status** | Todo |
| **Dependencies** | None |

**User Story:** As the team, we need a shared understanding of the architecture and conventions so every developer can work independently without blockers.

**Tasks:**
- [ ] Draw multi-agent architecture diagram (LangGraph nodes + edges)
- [ ] Confirm LangGraph as framework (over CrewAI/AutoGen per tech stack)
- [ ] Scaffold repo folder structure (`src/`, `data/`, `tests/`, `docker/`, `docs/`, `ui/`)
- [ ] Write `CONTRIBUTING.md`: branch naming (`feat/`, `fix/`, `chore/`), PR template, code style (black + ruff)
- [ ] Set up weekly sync (30-min standup) cadence

**Definition of Done:**
- Architecture diagram committed to `docs/architecture.png`
- Repo structure matches the file tree above
- All team members have cloned repo and can run `git log` successfully

---

### BE-DB-001 · Environment Setup & Dependency Management
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev - DB/Infra |
| **Priority** | 🔴 Critical |
| **Story Points** | 2 |
| **Sprint** | 1 |
| **Status** | Todo |
| **Dependencies** | PM-001 |

**User Story:** As a developer, I need a reproducible environment so I can install all dependencies with a single command.

**Tasks:**
- [ ] Populate `requirements.txt` with pinned versions (see below)
- [ ] Create `.env.example` documenting all required variables
- [ ] Configure `pre-commit` hooks: black, ruff, mypy
- [ ] Write `README.md` with local dev setup (venv, `pip install`, `streamlit run`)

**Key Dependencies:**
```
anthropic>=0.40.0
langgraph>=0.2.0
langchain-anthropic>=0.2.0
chromadb>=0.5.0
sqlalchemy>=2.0.0
alembic>=1.13.0
streamlit>=1.40.0
plotly>=5.24.0
pandas>=2.2.0
pydantic>=2.9.0
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-mock>=3.14.0
pytest-asyncio>=0.24.0
```

**`.env.example` variables:**
```
ANTHROPIC_API_KEY=
DATABASE_URL=sqlite:///./data/feedback.db
CHROMA_PATH=./data/chroma
DATA_DIR=./data/input
OUTPUT_DIR=./data/output
CLASSIFICATION_THRESHOLD=0.7
```

**Definition of Done:**
- `pip install -r requirements.txt` succeeds in a fresh `python -m venv .venv`
- `pre-commit run --all-files` passes with no errors
- README reviewed by at least one other team member

---

### BE-DB-002 · Mock Data — app_store_reviews.csv
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev - DB/Infra |
| **Priority** | 🔴 Critical |
| **Story Points** | 3 |
| **Sprint** | 1 |
| **Status** | Todo |
| **Dependencies** | BE-DB-001 |

**User Story:** As the pipeline, I need realistic app store review data so agents can be tested against representative inputs.

**Schema:** `review_id, platform, rating, review_text, user_name, date, app_version`

**Tasks:**
- [ ] Write Python script `scripts/generate_mock_data.py` to produce the CSV programmatically
- [ ] Generate ≥ 50 rows distributed across categories:

| Category | Count | Typical Rating | Sample Text Pattern |
|----------|-------|----------------|---------------------|
| Bug | 12 | 1–2 | "App crashes when I...", "Can't login since update" |
| Feature Request | 10 | 3–4 | "Please add dark mode", "Would love to see..." |
| Praise | 10 | 4–5 | "Amazing app!", "Love the new feature" |
| Complaint | 10 | 1–3 | "Too expensive", "App is very slow" |
| Spam | 8 | any | Promotional text, random chars, unrelated content |

- [ ] Include both `"Google Play"` and `"App Store"` platforms (~50/50 split)
- [ ] Use realistic versions: `"2.1.3"`, `"3.0.1"`, `"3.1.0"`, `"3.0.5"`
- [ ] Use ISO 8601 dates spanning the last 90 days

**Definition of Done:**
- File at `data/input/app_store_reviews.csv`
- `pandas.read_csv()` loads without errors
- No duplicate `review_id` values
- At least one bug review with detailed crash steps

---

### BE-DB-003 · Mock Data — support_emails.csv
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev - DB/Infra |
| **Priority** | 🔴 Critical |
| **Story Points** | 3 |
| **Sprint** | 1 |
| **Status** | Todo |
| **Dependencies** | BE-DB-001 |

**User Story:** As the pipeline, I need realistic support email data so agents can handle the second input channel.

**Schema:** `email_id, subject, body, sender_email, timestamp, priority`

**Tasks:**
- [ ] Generate ≥ 30 rows using `scripts/generate_mock_data.py`
- [ ] Include technical bug emails with: device model, OS version, steps to reproduce
- [ ] Mix formal business tone and casual user tone
- [ ] Leave `priority` blank for ~30% of rows; others: `"High"`, `"Medium"`, `"Low"`

**Sample subjects to include:**
- `"App Crash Report — iPhone 15 iOS 17.4"`
- `"Feature Request: Dark Mode Support"`
- `"Login Issue Since v3.0.1 Update"`
- `"Data Loss Problem — Urgent"`
- `"Suggestion for Improvement"`

**Definition of Done:**
- File at `data/input/support_emails.csv`
- `pandas.read_csv()` loads without errors
- No duplicate `email_id` values
- At least 5 bug emails with full technical details in `body`

---

### BE-DB-004 · Mock Data — expected_classifications.csv
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev - DB/Infra |
| **Priority** | 🟠 High |
| **Story Points** | 3 |
| **Sprint** | 1 |
| **Status** | Todo |
| **Dependencies** | BE-DB-002, BE-DB-003 |

**User Story:** As the QA Engineer, I need ground-truth labels for every input item so I can measure classification accuracy objectively.

**Schema:** `source_id, source_type, category, priority, technical_details, suggested_title`

**Tasks:**
- [ ] Create one row per review (`source_type="review"`) and one per email (`source_type="email"`)
- [ ] Manually assign correct `category` and `priority`
- [ ] For Bug rows: fill `technical_details` with device/OS/reproduction info
- [ ] Write `suggested_title` as a clear, ≤10-word actionable ticket title

**Valid values:**
- `category`: `Bug` | `Feature Request` | `Praise` | `Complaint` | `Spam`
- `priority`: `Critical` | `High` | `Medium` | `Low`

**Definition of Done:**
- Row count equals `len(reviews) + len(emails)`
- Zero missing `category` or `priority` values
- All Bug rows have non-empty `technical_details`
- Reviewed by PM for labelling consistency

---

## Phase 1 — Core Agent Development

### BE-API-001 · LangGraph State Schema & Graph Skeleton
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev - API/Coding |
| **Priority** | 🔴 Critical |
| **Story Points** | 5 |
| **Sprint** | 1 |
| **Status** | Todo |
| **Dependencies** | BE-DB-001 |

**User Story:** As a developer, I need a typed shared state and a wired graph skeleton so every agent node has a clear contract and the execution flow is defined before any node is implemented.

**Tasks:**
- [ ] Define `AgentState` TypedDict in `src/graph/state.py`:
```python
class AgentState(TypedDict):
    feedback_items: list[FeedbackItem]       # raw normalized input
    classified_items: list[ClassifiedItem]   # after Classifier
    bug_details: list[BugDetails]            # after Bug Analyzer
    feature_details: list[FeatureDetails]    # after Feature Extractor
    tickets: list[Ticket]                    # after Ticket Creator
    qc_results: list[QCResult]               # after Quality Critic
    errors: list[str]                        # item-level errors
    metrics: dict                            # run-level metrics
```
- [ ] Wire `StateGraph` in `src/graph/pipeline.py` with stub nodes
- [ ] Implement conditional edge: `route_after_classify` → Bug path | Feature path | Other
- [ ] Confirm `graph.compile()` runs without errors
- [ ] Write one smoke test that traverses the full graph with stub nodes

**Node execution order:**
```
csv_reader → classifier → [conditional]
  ├─ bug_analyzer   ─┐
  ├─ feature_extractor ─┤
  └─ (pass-through) ─┘
         └─ ticket_creator → quality_critic → END
```

**Definition of Done:**
- `graph.compile()` succeeds
- All state fields are typed (no `Any`)
- Smoke test passes: stub graph processes 1 item end-to-end

---

### BE-API-002 · CSV Reader Agent Node
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev - API/Coding |
| **Priority** | 🔴 Critical |
| **Story Points** | 3 |
| **Sprint** | 1 |
| **Status** | Todo |
| **Dependencies** | BE-API-001, BE-DB-002, BE-DB-003 |

**User Story:** As the pipeline, I need to ingest both CSV files into a unified list of `FeedbackItem` objects so downstream agents work with a consistent schema regardless of source.

**Tasks:**
- [ ] Implement `csv_reader_node(state: AgentState) -> AgentState` in `src/agents/csv_reader.py`
- [ ] Normalize `app_store_reviews` columns → `FeedbackItem(id, source_type="review", text, metadata)`
- [ ] Normalize `support_emails` columns → `FeedbackItem(id, source_type="email", text, metadata)`
- [ ] Log warning and skip malformed rows (do not raise)
- [ ] Read paths from `config.DATA_DIR`

**`FeedbackItem` Pydantic model:**
```python
class FeedbackItem(BaseModel):
    id: str
    source_type: Literal["review", "email"]
    text: str
    metadata: dict  # platform/rating or subject/priority
    raw_row: dict
```

**Definition of Done:**
- Unit test: 50 reviews + 30 emails → 80 `FeedbackItem` objects in state
- Unit test: file with 2 malformed rows → 2 skipped, rest processed, 2 warnings logged
- No `KeyError` or `AttributeError` on any mock data row

---

### BE-API-003 · Feedback Classifier Agent Node
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev - API/Coding |
| **Priority** | 🔴 Critical |
| **Story Points** | 8 |
| **Sprint** | 2 |
| **Status** | Todo |
| **Dependencies** | BE-API-001 |

**User Story:** As the system, I need every feedback item categorized into exactly one of five categories with a confidence score so downstream routing and prioritization are accurate and consistent.

**Tasks:**
- [ ] Implement `classifier_node` in `src/agents/classifier.py`
- [ ] Use `claude-opus-4-6` with structured output (`client.messages.parse()`)
- [ ] Define `ClassificationResult` Pydantic model:
```python
class ClassificationResult(BaseModel):
    category: Literal["Bug", "Feature Request", "Praise", "Complaint", "Spam"]
    confidence: float          # 0.0 – 1.0
    reasoning: str             # one-sentence justification
    needs_review: bool         # True if confidence < threshold
```
- [ ] Process items in batches of 10 to reduce API calls
- [ ] Read `CLASSIFICATION_THRESHOLD` from config (default `0.7`)
- [ ] Write `ClassifiedItem` (extends `FeedbackItem`) back to state

**Prompt design notes:**
- System prompt: senior product triage analyst persona
- Include one-shot examples for each of the 5 categories
- Instruct model to return JSON matching the Pydantic schema

**Definition of Done:**
- Accuracy ≥ 85% on `expected_classifications.csv` (80 items)
- `confidence` always in [0, 1]
- Items with `confidence < threshold` have `needs_review=True`
- Unit tests mock API responses — zero real API calls in unit suite

---

### BE-API-004 · Bug Analysis Agent Node
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev - API/Coding |
| **Priority** | 🟠 High |
| **Story Points** | 5 |
| **Sprint** | 2 |
| **Status** | Todo |
| **Dependencies** | BE-API-003 |

**User Story:** As an engineer receiving a bug ticket, I need structured technical details extracted from the raw text so I can reproduce the issue without reading the original feedback.

**Tasks:**
- [ ] Implement `bug_analyzer_node` in `src/agents/bug_analyzer.py`
- [ ] Only processes items where `classified.category == "Bug"`
- [ ] Define `BugDetails` Pydantic model:
```python
class BugDetails(BaseModel):
    platform: str           # "iOS" | "Android" | "Unknown"
    device: str             # e.g. "iPhone 15" | "Unknown"
    os_version: str         # e.g. "iOS 17.4" | "Unknown"
    app_version: str        # e.g. "3.0.1" | "Unknown"
    steps_to_reproduce: list[str]   # numbered steps or ["Not provided"]
    severity: Literal["Critical", "High", "Medium", "Low"]
    affected_feature: str   # e.g. "Login", "Data Sync"
```
- [ ] Auto-assign severity rules:
  - `Critical`: keywords crash, data loss, unable to open, frozen
  - `High`: feature completely broken, login failure
  - `Medium`: degraded performance, intermittent issue
  - `Low`: cosmetic, minor UI glitch
- [ ] Mark all unknown fields as `"Unknown"` (never `None`)

**Definition of Done:**
- Unit tests cover 5 scenarios: crash bug, login bug, sync bug, cosmetic bug, sparse bug (no technical detail)
- `severity` always one of the 4 valid values
- `steps_to_reproduce` always a list (never empty string)

---

### BE-API-005 · Feature Extractor Agent Node
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev - API/Coding |
| **Priority** | 🟠 High |
| **Story Points** | 5 |
| **Sprint** | 2 |
| **Status** | Todo |
| **Dependencies** | BE-API-003, BE-DB-006 |

**User Story:** As a product manager, I need feature requests deduplicated and scored by user demand so I can prioritize the roadmap based on signal, not noise.

**Tasks:**
- [ ] Implement `feature_extractor_node` in `src/agents/feature_extractor.py`
- [ ] Only processes items where `classified.category == "Feature Request"`
- [ ] Define `FeatureDetails` Pydantic model:
```python
class FeatureDetails(BaseModel):
    feature_summary: str       # ≤ 15-word title of the feature
    description: str           # expanded description
    user_impact: str           # why users need it
    demand_score: int          # 1 (niche) – 5 (widely requested)
    user_segment: str          # e.g. "power users", "all users", "enterprise"
    is_duplicate: bool
    duplicate_of: str | None   # ID of the original feature request
```
- [ ] After extraction, call `chroma_store.find_similar(text, k=3, threshold=0.85)`
- [ ] If similarity match found: set `is_duplicate=True`, `duplicate_of=<matched_id>`
- [ ] Upsert non-duplicate features into ChromaDB for future deduplication

**Definition of Done:**
- Unit test: 3 near-duplicate "dark mode" requests → 1 original, 2 marked duplicate
- `demand_score` always 1–5 (validated by Pydantic)
- ChromaDB upsert called for non-duplicate features

---

### BE-API-006 · Ticket Creator Agent Node
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev - API/Coding |
| **Priority** | 🔴 Critical |
| **Story Points** | 5 |
| **Sprint** | 2 |
| **Status** | Todo |
| **Dependencies** | BE-API-004, BE-API-005 |

**User Story:** As an engineer, I need every actionable feedback item converted to a consistently formatted ticket in CSV so I have a traceable record from raw feedback to engineering action.

**Tasks:**
- [ ] Implement `ticket_creator_node` in `src/agents/ticket_creator.py`
- [ ] Generate tickets for: `Bug`, `Feature Request`, `Complaint`
- [ ] Skip ticket creation for: `Praise` (log as positive signal), `Spam` (log and discard)
- [ ] Write `generated_tickets.csv`:

| Column | Description |
|--------|-------------|
| `ticket_id` | Format: `TKT-YYYYMMDD-XXXX` (zero-padded sequence) |
| `source_id` | ID from original review/email |
| `source_type` | `review` or `email` |
| `title` | Concise action title (≤ 80 chars) |
| `description` | Structured markdown: **Summary**, **Steps/Details**, **Expected Behavior** |
| `category` | Bug / Feature Request / Complaint |
| `priority` | Critical / High / Medium / Low |
| `severity` | For bugs only; blank for others |
| `assignee_team` | Engineering / Product / Support |
| `tags` | Comma-separated: platform, feature area |
| `created_at` | ISO 8601 timestamp |
| `status` | `open` or `needs_review` |

- [ ] Write `processing_log.csv` with one row per item (including skipped):

| Column | Description |
|--------|-------------|
| `log_id` | Sequence ID |
| `source_id` | Original item ID |
| `stage` | Node name where log entry was created |
| `result` | `success` / `skipped` / `error` |
| `details` | Human-readable note |
| `timestamp` | ISO 8601 |

**Definition of Done:**
- Unit test verifies all 12 columns present in output CSV
- `ticket_id` uniqueness guaranteed within a single run
- Praise and Spam have `processing_log` entries but no ticket rows
- CSV appends without truncating existing rows (run-safe)

---

### BE-API-007 · Quality Critic Agent Node
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev - API/Coding |
| **Priority** | 🟠 High |
| **Story Points** | 5 |
| **Sprint** | 2 |
| **Status** | Todo |
| **Dependencies** | BE-API-006 |

**User Story:** As a product manager, I need every generated ticket reviewed for completeness and correct prioritization so inconsistent or incomplete tickets are flagged before they reach the engineering backlog.

**Tasks:**
- [ ] Implement `quality_critic_node` in `src/agents/quality_critic.py`
- [ ] Run rule-based validation checks:

| Rule | Check | Action on Fail |
|------|-------|----------------|
| Title length | ≤ 80 chars | Flag `needs_review` |
| Description | ≥ 50 chars | Flag `needs_review` |
| Priority assigned | Not blank | Flag `needs_review` |
| Category valid | One of 5 valid values | Flag `needs_review` |
| Bug has severity | Non-empty for Bug tickets | Flag `needs_review` |

- [ ] Run LLM-based completeness review (optional, configurable): asks Claude to rate completeness 1–5 and suggest missing information
- [ ] Auto-escalate priority: if description contains `crash` or `data loss` → set `priority = "Critical"`
- [ ] Write `QCResult` per ticket; merge `qc_notes` and updated `status` back into ticket CSV
- [ ] Write `metrics.csv` with run-level summary:

| Column | Description |
|--------|-------------|
| `run_id` | UUID of this pipeline run |
| `timestamp` | Run start time |
| `total_items` | Total feedback items processed |
| `bugs` / `features` / `praise` / `complaints` / `spam` | Count per category |
| `tickets_created` | Total tickets written |
| `qc_pass_rate` | % tickets passing QC without manual review |
| `accuracy` | vs expected_classifications (if available) |
| `avg_latency_ms` | Average per-item processing time |

**Definition of Done:**
- ≥ 95% of well-formed tickets pass QC automatically in unit tests
- Priority auto-escalation unit-tested with 3 crash/data-loss scenarios
- `metrics.csv` written after every run with correct column count

---

### BE-DB-005 · Database Schema & ORM Models
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev - DB/Infra |
| **Priority** | 🟠 High |
| **Story Points** | 5 |
| **Sprint** | 2 |
| **Status** | Todo |
| **Dependencies** | BE-DB-001 |

**User Story:** As the system, I need a relational database to persist tickets and processing history so the UI can query and display data without re-reading CSVs on every request.

**Tasks:**
- [ ] Define SQLAlchemy ORM models in `src/db/models.py`:
  - `FeedbackItemModel` — mirrors `FeedbackItem` + FK to Ticket
  - `TicketModel` — mirrors `generated_tickets.csv` columns
  - `ProcessingLogModel` — mirrors `processing_log.csv` columns
  - `MetricsModel` — mirrors `metrics.csv` columns
- [ ] Configure `src/db/session.py` to read `DATABASE_URL` from env
- [ ] Write Alembic migration: `alembic revision --autogenerate -m "initial schema"`
- [ ] Write `scripts/db_init.py`: creates tables, optionally imports existing CSVs
- [ ] Support SQLite (`sqlite:///./data/feedback.db`) for local dev
- [ ] Support Postgres (`postgresql://...`) for production

**Definition of Done:**
- `alembic upgrade head` runs against both SQLite and Postgres
- Unit tests use `sqlite:///:memory:` — no file system writes
- `db_init.py` imports 80-row mock dataset without errors

---

### BE-DB-006 · ChromaDB Vector Store
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev - DB/Infra |
| **Priority** | 🟠 High |
| **Story Points** | 3 |
| **Sprint** | 2 |
| **Status** | Todo |
| **Dependencies** | BE-DB-001 |

**User Story:** As the Feature Extractor, I need a vector similarity search so duplicate feature requests are detected automatically without manual comparison.

**Tasks:**
- [ ] Implement `src/db/chroma_store.py` with:
  - `init_chroma(path: str) -> chromadb.Client`
  - `upsert_feedback(id: str, text: str, metadata: dict) -> None`
  - `find_similar(text: str, k: int = 5, threshold: float = 0.85) -> list[SimilarResult]`
- [ ] Use ChromaDB's default embedding function (or `sentence-transformers/all-MiniLM-L6-v2`)
- [ ] Persist collection to `CHROMA_PATH` from env
- [ ] Return `SimilarResult(id, text, similarity_score)` from `find_similar`

**Definition of Done:**
- Integration test: upsert 5 feature texts → query similar → correct top-1 returned
- `find_similar` returns empty list (not error) when collection is empty
- ChromaDB path configurable (no hardcoded paths)

---

## Phase 2 — Pipeline Integration & Output

### BE-API-008 · End-to-End Pipeline Integration
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev - API/Coding |
| **Priority** | 🔴 Critical |
| **Story Points** | 8 |
| **Sprint** | 3 |
| **Status** | Todo |
| **Dependencies** | BE-API-002, BE-API-003, BE-API-004, BE-API-005, BE-API-006, BE-API-007, BE-DB-005, BE-DB-006 |

**User Story:** As a user, I need to run `python -m src.main` and have the system automatically process all CSVs and produce output files so there is no manual intervention required.

**Tasks:**
- [ ] Compile `StateGraph` with all real nodes (replace stubs)
- [ ] Implement `run_pipeline(data_dir, output_dir, config)` in `src/graph/pipeline.py`
- [ ] Implement CLI entry point `src/main.py` with `argparse`:
  - `--data-dir` (default from `.env`)
  - `--output-dir` (default from `.env`)
  - `--dry-run` (classify only, no ticket creation)
- [ ] Write output CSVs atomically (write to temp file, then rename)
- [ ] Item-level error handling: one bad item logs error and continues; does not abort pipeline
- [ ] Print run summary table to stdout on completion

**Definition of Done:**
- `python -m src.main` with mock data produces all 3 output files
- Pipeline processes 80 items in under 5 minutes
- Killing mid-run and rerunning does not produce duplicate ticket IDs
- `--dry-run` mode produces no ticket CSV writes

---

## Phase 3 — Streamlit UI

### FE-001 · Streamlit App Shell & Navigation
| Field | Value |
|-------|-------|
| **Assignee** | Frontend Dev - Streamlit |
| **Priority** | 🔴 Critical |
| **Story Points** | 3 |
| **Sprint** | 3 |
| **Status** | Todo |
| **Dependencies** | BE-DB-001 |

**User Story:** As a product manager, I need a web UI with clear navigation so I can monitor, control, and review the feedback pipeline without using the command line.

**Tasks:**
- [ ] Create `ui/app.py` as Streamlit entry point with sidebar navigation
- [ ] Implement shared helpers in `ui/utils.py`: `load_tickets()`, `load_metrics()`, `load_logs()`
- [ ] Create 5 page files under `ui/pages/`
- [ ] Apply consistent styling: app title "Feedback Intelligence System", team color palette
- [ ] Handle cold-start gracefully (no output files yet → show "Run pipeline first" message)
- [ ] Store pipeline run state in `st.session_state`

**Definition of Done:**
- `streamlit run ui/app.py` launches with no errors
- All 5 pages accessible from sidebar with no `FileNotFoundError`
- Cold-start state (no output CSVs) shows placeholder, not traceback

---

### FE-002 · Dashboard Page
| Field | Value |
|-------|-------|
| **Assignee** | Frontend Dev - Streamlit |
| **Priority** | 🟠 High |
| **Story Points** | 5 |
| **Sprint** | 3 |
| **Status** | Todo |
| **Dependencies** | FE-001, BE-API-008 |

**User Story:** As a product manager, I need a dashboard with KPIs and charts so I can assess the pipeline's output at a glance without reading raw CSV files.

**Tasks:**
- [ ] KPI row (4 `st.metric` cards): Total Feedback · Tickets Created · QC Pass Rate · Avg Latency
- [ ] Category breakdown: Plotly donut chart (Bug / Feature / Praise / Complaint / Spam)
- [ ] Source breakdown: Plotly grouped bar (App Store vs Support Email per category)
- [ ] Recent tickets table: last 20 tickets, `st.dataframe` with priority colour-coding
- [ ] "Refresh" button: re-reads CSVs from disk without full page reload

**Definition of Done:**
- KPI cards populated from `metrics.csv`
- Charts render with Plotly (not matplotlib)
- Table shows priority column with colour: Critical=red, High=orange, Medium=yellow, Low=green
- Empty state (no data) shows info banner, not Python traceback

---

### FE-003 · Run Pipeline Page
| Field | Value |
|-------|-------|
| **Assignee** | Frontend Dev - Streamlit |
| **Priority** | 🔴 Critical |
| **Story Points** | 5 |
| **Sprint** | 3 |
| **Status** | Todo |
| **Dependencies** | FE-001, BE-API-008 |

**User Story:** As a product manager, I need to trigger the feedback pipeline from the UI and monitor its progress in real time so I do not need terminal access.

**Tasks:**
- [ ] File uploader: accept custom `app_store_reviews.csv` and `support_emails.csv` (optional override)
- [ ] "Run Pipeline" button: triggers `run_pipeline()` in a `threading.Thread`
- [ ] Progress bar: updates as each item is processed (use `st.progress` + queue)
- [ ] Live log table: reads `processing_log.csv` every 2 seconds during run (`st.empty`)
- [ ] Toast notification on completion: success (green) or error (red)
- [ ] Disable "Run Pipeline" button while pipeline is running

**Definition of Done:**
- UI remains responsive (no freezing) while pipeline runs
- Progress bar reaches 100% on successful run completion
- Log table shows real entries (not placeholder text)
- Running pipeline twice without waiting shows appropriate "already running" warning

---

### FE-004 · Tickets Page — View & Manual Override
| Field | Value |
|-------|-------|
| **Assignee** | Frontend Dev - Streamlit |
| **Priority** | 🟠 High |
| **Story Points** | 8 |
| **Sprint** | 3 |
| **Status** | Todo |
| **Dependencies** | FE-001, BE-API-006, BE-API-007 |

**User Story:** As an engineer, I need to view all generated tickets and override fields like priority or status so I can correct any misclassifications before they enter the backlog.

**Tasks:**
- [ ] Filterable ticket table with sidebar filters: category, priority, status, date range
- [ ] Keyword search bar: filters `title` and `description` columns
- [ ] Row click → opens edit form (`st.form`) with editable fields: title, description, priority, status
- [ ] "Save Changes" button: writes edits to `generated_tickets.csv` and DB; appends edit record to `processing_log.csv`
- [ ] "Approve All" button: sets all `needs_review` tickets to `open` in bulk
- [ ] "Export CSV" button: downloads current filtered view as CSV

**Definition of Done:**
- Edits persist to CSV after page refresh
- Filter and search work independently and in combination
- "Approve All" changes status of all `needs_review` rows only
- Edit audit trail visible in processing log

---

### FE-005 · Configuration Panel
| Field | Value |
|-------|-------|
| **Assignee** | Frontend Dev - Streamlit |
| **Priority** | 🟡 Medium |
| **Story Points** | 3 |
| **Sprint** | 3 |
| **Status** | Todo |
| **Dependencies** | FE-001 |

**User Story:** As a power user, I need to adjust classification thresholds and priority mappings from the UI so I can tune the pipeline without editing code or config files directly.

**Tasks:**
- [ ] Confidence threshold slider: range 0.5–1.0, step 0.05, default 0.7
- [ ] Default priority dropdowns: one per category (Bug / Feature Request / Complaint)
- [ ] Data directory path inputs (text fields with validation)
- [ ] "Save Configuration" button: writes to `config.json`
- [ ] "Reset to Defaults" button
- [ ] Show current config values on load from `config.json`

**Definition of Done:**
- Saving config writes valid JSON to `config.json`
- Pipeline reads updated config on next run (no restart required)
- Invalid paths show an inline error, not a Python exception

---

### FE-006 · Analytics Page
| Field | Value |
|-------|-------|
| **Assignee** | Frontend Dev - Streamlit |
| **Priority** | 🟡 Medium |
| **Story Points** | 5 |
| **Sprint** | 4 |
| **Status** | Todo |
| **Dependencies** | FE-002, BE-API-008 |

**User Story:** As a product manager, I need trend charts and accuracy metrics so I can demonstrate the system's performance and value during the capstone demo.

**Tasks:**
- [ ] Trend line chart: tickets created per run over time (x = run timestamp, y = count)
- [ ] Category breakdown stacked bar: App Store vs Email per category
- [ ] Classification accuracy bar chart (per category vs `expected_classifications.csv`)
- [ ] Top feature requests table: sorted by `demand_score` desc
- [ ] Processing latency histogram: distribution of per-item latency in ms
- [ ] Date range filter applied to all charts

**Definition of Done:**
- All 5 charts render with Plotly
- Accuracy chart hidden (not error) when `expected_classifications.csv` is absent
- Single-run data renders without division-by-zero errors

---

## Phase 4 — Quality, Testing & Deployment

### QA-001 · Unit Tests — All Agent Nodes
| Field | Value |
|-------|-------|
| **Assignee** | QA Engineer |
| **Priority** | 🟠 High |
| **Story Points** | 8 |
| **Sprint** | 3 |
| **Status** | Todo |
| **Dependencies** | BE-API-002 through BE-API-007 |

**User Story:** As the team, we need comprehensive unit tests for every agent node so regressions are caught in CI before they reach integration testing.

**Tasks:**
- [ ] Write unit tests in `tests/unit/test_<agent_name>.py` for each of 6 nodes
- [ ] Mock all Anthropic API calls with `pytest-mock` (zero real API calls)
- [ ] Cover per node:
  - Happy path (typical input)
  - Empty input (empty list / empty string)
  - Malformed input (missing columns, wrong types)
  - Edge cases (very long text, non-ASCII characters, all-caps text)
- [ ] Use `pytest.fixture` for reusable `FeedbackItem` and `ClassifiedItem` factories
- [ ] Run with `pytest tests/unit/ --cov=src/agents --cov-report=term-missing`

**Coverage targets:**

| Agent | Min Coverage |
|-------|-------------|
| csv_reader | 95% |
| classifier | 90% |
| bug_analyzer | 90% |
| feature_extractor | 90% |
| ticket_creator | 95% |
| quality_critic | 90% |

**Definition of Done:**
- `pytest tests/unit/` passes with 0 failures
- All coverage targets met
- No real API calls (verified via mock assertion)

---

### QA-002 · Integration Tests — Full Pipeline
| Field | Value |
|-------|-------|
| **Assignee** | QA Engineer |
| **Priority** | 🟠 High |
| **Story Points** | 5 |
| **Sprint** | 4 |
| **Status** | Todo |
| **Dependencies** | BE-API-008 |

**User Story:** As the team, we need an integration test that runs the full pipeline end-to-end so we know the system works correctly as a whole, not just node-by-node.

**Tasks:**
- [ ] Create `tests/fixtures/` with 10-item versions of all 3 CSVs (hand-labelled)
- [ ] Write `tests/integration/test_pipeline.py`:
  - Test: pipeline runs without exception on 10-item fixture
  - Test: `generated_tickets.csv` exists and has correct schema after run
  - Test: ticket count matches expected (non-Praise, non-Spam items)
  - Test: classification accuracy ≥ 80% on 10-item fixture
- [ ] Mark with `@pytest.mark.integration`
- [ ] Add `pytest.ini` section to exclude integration from default run: `-m "not integration"`

**Definition of Done:**
- `pytest -m integration tests/integration/` passes
- Uses real Claude API (key from `ANTHROPIC_API_KEY` env var)
- Accuracy assertion runs only when fixture `expected_classifications.csv` exists

---

### QA-003 · Accuracy Benchmarking Report
| Field | Value |
|-------|-------|
| **Assignee** | QA Engineer |
| **Priority** | 🟡 Medium |
| **Story Points** | 3 |
| **Sprint** | 4 |
| **Status** | Todo |
| **Dependencies** | QA-002, BE-DB-004 |

**User Story:** As the capstone evaluator, I need a benchmark report with precision, recall, and F1 per category so I can objectively assess the system's classification quality.

**Tasks:**
- [ ] Run full pipeline against complete 80-item mock dataset
- [ ] Compute per-category: Precision, Recall, F1-score using scikit-learn
- [ ] Write `docs/benchmark_report.md` with:
  - Confusion matrix
  - Per-category table (Precision / Recall / F1)
  - Overall weighted F1
  - Misclassified examples (top 5)
  - Improvement notes for any category below F1 0.70

**Targets:**

| Metric | Minimum |
|--------|---------|
| Overall weighted F1 | ≥ 0.80 |
| Bug F1 | ≥ 0.85 |
| Feature Request F1 | ≥ 0.80 |
| Spam F1 | ≥ 0.90 |

**Definition of Done:**
- `docs/benchmark_report.md` committed
- All targets met or improvement tasks filed
- Benchmark re-runnable with `python scripts/benchmark.py`

---

### QA-004 · UI Smoke Tests
| Field | Value |
|-------|-------|
| **Assignee** | QA Engineer |
| **Priority** | 🟡 Medium |
| **Story Points** | 3 |
| **Sprint** | 4 |
| **Status** | Todo |
| **Dependencies** | FE-001 through FE-006 |

**User Story:** As the team, we need automated UI tests so we catch page load errors and broken interactions before the demo.

**Tasks:**
- [ ] Write `tests/ui/test_smoke.py` using `pytest` + `subprocess` to launch Streamlit
- [ ] OR use Playwright (`playwright install chromium`) for browser-level tests
- [ ] Test cases:
  - All 5 pages load returning HTTP 200
  - Dashboard shows "Run pipeline first" when no data present
  - Configuration page saves `config.json` after form submit
  - Tickets page shows filter controls
- [ ] Run against `localhost:8501` with fixture output files pre-loaded

**Definition of Done:**
- All smoke tests pass when Streamlit is running
- Tests use fixture data (not real pipeline run)
- CI step documented in `docs/testing.md`

---

### BE-DB-007 · Docker Compose Setup
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev - DB/Infra |
| **Priority** | 🟠 High |
| **Story Points** | 5 |
| **Sprint** | 4 |
| **Status** | Todo |
| **Dependencies** | BE-DB-001, FE-001 |

**User Story:** As a developer or evaluator, I need to run the entire system with `docker compose up` so I don't need to manually install Python, Postgres, or ChromaDB.

**Tasks:**
- [ ] Write `docker/Dockerfile` — multi-stage: builder installs deps, runner copies app
- [ ] Write `docker/docker-compose.yml` with services:
  - `app`: Streamlit on port 8501
  - `db`: Postgres 16 with named volume
  - `chroma`: ChromaDB server on port 8000 (optional, can use embedded mode)
- [ ] Pass all config via environment variables (no hardcoded values in Dockerfile)
- [ ] Add `.dockerignore` to exclude `__pycache__`, `.venv`, `data/`, `.env`
- [ ] Validate: `docker compose up --build` → app healthy at `http://localhost:8501`

**Image size target:** ≤ 1 GB (use `python:3.11-slim`)

**Definition of Done:**
- `docker compose up` starts all services from a cold pull
- Postgres data persists across container restarts
- `docker compose down -v` cleans up all volumes cleanly

---

### BE-DB-008 · Azure Deployment
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev - DB/Infra |
| **Priority** | 🟡 Medium |
| **Story Points** | 5 |
| **Sprint** | 4 |
| **Status** | Todo |
| **Dependencies** | BE-DB-007 |

**User Story:** As the capstone evaluator, I need the app accessible at a public URL so I can review the live system without running it locally.

**Tasks:**
- [ ] Push Docker image to Azure Container Registry (ACR)
- [ ] Deploy to Azure Container Apps (or Azure App Service)
- [ ] Provision Azure Database for PostgreSQL (Flexible Server)
- [ ] Store secrets (`ANTHROPIC_API_KEY`, DB password) in Azure Key Vault
- [ ] Reference secrets from Key Vault in Container App environment variables
- [ ] Configure health check: `GET /healthz` → 200 OK
- [ ] Document full deployment steps in `docs/azure_deployment.md`

**Definition of Done:**
- App accessible at a public `*.azurecontainerapps.io` URL
- No secrets in container image or environment variable literals
- `docs/azure_deployment.md` allows a new team member to deploy from scratch

---

### PM-002 · Capstone Demo Preparation
| Field | Value |
|-------|-------|
| **Assignee** | Product Manager |
| **Priority** | 🟠 High |
| **Story Points** | 3 |
| **Sprint** | 4 |
| **Status** | Todo |
| **Dependencies** | BE-API-008, FE-003, QA-003 |

**User Story:** As the presenting team, we need a polished demo script and slide deck so the capstone evaluation is smooth and covers all required demonstration points.

**Tasks:**
- [ ] Write demo script (`docs/demo_script.md`) covering all 6 required steps:
  1. Data ingestion from mock CSV files
  2. Real-time processing with agent interactions
  3. Classification accuracy vs expected results
  4. Ticket generation with proper formatting
  5. User interface functionality and monitoring
  6. Error handling and edge case management
- [ ] Create slide deck (≤ 10 slides): problem, architecture, demo flow, metrics, learnings
- [ ] Set up demo environment with pre-loaded mock data
- [ ] Conduct at least 1 full rehearsal with team

**Definition of Done:**
- Demo walkthrough ≤ 15 minutes
- All 6 required demo steps covered
- Slide deck reviewed by whole team
- Rehearsal completed and feedback incorporated

---

## Task Summary

| Phase | Tasks | 🔴 Critical | 🟠 High | 🟡 Medium | Story Points |
|-------|-------|------------|--------|----------|-------------|
| 0 – Setup & Mock Data | 5 | 3 | 2 | 0 | 14 |
| 1 – Core Agents | 9 | 4 | 5 | 0 | 44 |
| 2 – Pipeline | 1 | 1 | 0 | 0 | 8 |
| 3 – Streamlit UI | 6 | 2 | 2 | 2 | 29 |
| 4 – QA & Deployment | 8 | 0 | 4 | 4 | 32 |
| **Total** | **29** | **10** | **13** | **6** | **127** |

**Sprint Velocity Target:** ~32 story points / sprint × 4 sprints = 128 points ✓

---

## Dependency Graph

```
PM-001
└── BE-DB-001
    ├── BE-DB-002 ──┐
    ├── BE-DB-003 ──┼── BE-DB-004
    ├── BE-API-001
    │   ├── BE-API-002 (needs BE-DB-002, BE-DB-003)
    │   └── BE-API-003
    │       ├── BE-API-004
    │       └── BE-API-005 ── (needs BE-DB-006)
    │           └── BE-API-006
    │               └── BE-API-007
    │                   └── BE-API-008 ─── QA-002
    ├── BE-DB-005
    ├── BE-DB-006
    └── FE-001
        ├── FE-002 (needs BE-API-008)
        ├── FE-003 (needs BE-API-008)
        ├── FE-004 (needs BE-API-006, BE-API-007)
        ├── FE-005
        └── FE-006 (needs BE-API-008)
            └── QA-004

BE-DB-001 ── BE-DB-007 (Docker)
    └── BE-DB-008 (Azure)

QA-002 + BE-DB-004 ── QA-003
BE-API-008 + FE-003 + QA-003 ── PM-002
```
