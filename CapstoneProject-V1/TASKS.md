# TASKS.md — Intelligent User Feedback Analysis & Action System
> **Capstone Project** · Agentic AI Certification
> **Tech Stack:** LangGraph · Python 3.11 · SQLite · ChromaDB · Streamlit · Docker · Azure
> **Agent Framework:** LangGraph (multi-node StateGraph)
> **LLM:** OpenAI `gpt-4o` via OpenAI SDK

---

## Business Context

Modern SaaS companies receive dozens of user reviews and support emails daily.
Manual triaging is slow, inconsistent, and doesn't scale — critical bugs get
missed, feature requests are delayed, and ticket quality is uneven.

This system automates the full triage pipeline: ingest → classify → analyse →
create ticket → quality-check, with a Streamlit UI for monitoring and overrides.

---

## Quick Reference

| Symbol | Meaning |
|--------|---------|
| 🔴 Critical | Blocks other work; must be done first |
| 🟠 High | Core deliverable; sprint priority |
| 🟡 Medium | Important but not blocking |
| 🟢 Low | Nice-to-have |

| Role | Code | Responsibility |
|------|------|----------------|
| Product Manager | `PM` | Architecture, planning, demo prep |
| Backend – DB & Infra | `BE-DB` | Database, ChromaDB, Docker, Azure |
| Backend – API & Agents | `BE-API` | LangGraph agents, pipeline logic |
| Frontend – Streamlit | `FE` | All Streamlit UI pages |
| Quality Assurance | `QA` | Automated tests, benchmarks |

**Story Points (Fibonacci):** 1 · 2 · 3 · 5 · 8 · 13

---

## Proposed File Structure

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
├── docs/
│   └── product/              ← markdown product docs indexed into ChromaDB
├── src/
│   ├── agents/
│   │   ├── rag_loader.py     ← indexes tech docs, primes RAG context
│   │   ├── csv_reader.py
│   │   ├── classifier.py
│   │   ├── bug_analyzer.py
│   │   ├── feature_extractor.py
│   │   ├── ticket_creator.py
│   │   └── quality_critic.py
│   ├── graph/
│   │   ├── state.py          ← AgentState TypedDict + all Pydantic models
│   │   └── pipeline.py       ← StateGraph wiring + run_pipeline()
│   ├── db/
│   │   ├── models.py         ← SQLAlchemy ORM
│   │   ├── session.py
│   │   └── chroma_store.py   ← 3 ChromaDB collections
│   ├── config.py             ← loads .env + config.json
│   └── main.py               ← CLI entry point (argparse)
├── ui/
│   ├── app.py
│   └── pages/
│       ├── 1_Dashboard.py
│       ├── 2_Run_Pipeline.py
│       ├── 3_Tickets.py
│       ├── 4_Configuration.py
│       └── 5_Analytics.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── ui/
│   └── fixtures/
├── scripts/
│   ├── generate_mock_data.py
│   ├── db_init.py
│   └── benchmark.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── pm_agent.py               ← PM agent that generates this TASKS.md
├── config.json
├── .env.example
└── requirements.txt
```

---

## Sprint Plan (4 × 2-week sprints)

| Sprint | Focus | Phases | Target Points |
|--------|-------|--------|--------------|
| Sprint 1 | Setup, mock data, graph skeleton | Phase 0 + Phase 1 skeleton | ~32 |
| Sprint 2 | All agents, DB, ChromaDB | Phase 1 full | ~32 |
| Sprint 3 | Pipeline integration, Streamlit UI | Phase 2 + Phase 3 | ~32 |
| Sprint 4 | QA, Docker, Azure, demo prep | Phase 4 | ~32 |

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
- [ ] Draw multi-agent architecture diagram (LangGraph nodes + edges + ChromaDB collections)
- [ ] Confirm LangGraph + OpenAI `gpt-4o` as the framework/LLM (replacing CrewAI/AutoGen/Anthropic from spec)
- [ ] Document the three ChromaDB collections: `feedback_reviews`, `generated_tickets`, `tech_documents`
- [ ] Scaffold repo folder structure matching the file tree above
- [ ] Write `CONTRIBUTING.md`: branch naming (`feat/`, `fix/`, `chore/`), PR template, code style (black + ruff)

**Definition of Done:**
- Architecture diagram committed to `docs/architecture.png`
- Repo structure matches the file tree above
- All team members have cloned repo and can run `git log` successfully

---

### BE-DB-001 · Environment Setup & Dependency Management
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev – DB/Infra |
| **Priority** | 🔴 Critical |
| **Story Points** | 2 |
| **Sprint** | 1 |
| **Status** | Done |
| **Dependencies** | PM-001 |

**User Story:** As a developer, I need a reproducible environment so I can install all dependencies with a single command.

**Tasks:**
- [ ] Populate `requirements.txt` with pinned versions:
  ```
  openai>=1.40.0
  langgraph>=0.2.0
  langchain-openai>=0.2.0
  chromadb>=0.5.0
  sqlalchemy>=2.0.0
  alembic>=1.13.0
  streamlit>=1.40.0
  plotly>=5.24.0
  pandas>=2.2.0
  pydantic>=2.9.0
  python-dotenv>=1.0.0
  scikit-learn>=1.5.0
  pytest>=8.0.0
  pytest-mock>=3.14.0
  pytest-asyncio>=0.24.0
  pytest-cov>=5.0.0
  ```
- [ ] Create `.env.example` with all required variables:
  ```
  OPENAI_API_KEY=
  OPENAI_MODEL=gpt-4o
  DATABASE_URL=sqlite:///./data/feedback.db
  CHROMA_PATH=./data/chroma
  DATA_DIR=./data/input
  OUTPUT_DIR=./data/output
  TECH_DOCS_DIR=./docs/product
  CLASSIFICATION_THRESHOLD=0.7
  DUPLICATE_SIMILARITY_THRESHOLD=0.85
  ```
- [ ] Write `src/config.py` — reads `.env` + `config.json`, exports typed constants
- [ ] Write `README.md` with local dev setup (venv, `pip install`, `streamlit run`)

**Definition of Done:**
- `pip install -r requirements.txt` succeeds in a fresh `python -m venv .venv`
- README reviewed by at least one other team member

---

### BE-DB-002 · Mock Data — app_store_reviews.csv
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev – DB/Infra |
| **Priority** | 🔴 Critical |
| **Story Points** | 3 |
| **Sprint** | 1 |
| **Status** | Done |
| **Dependencies** | BE-DB-001 |

**User Story:** As the pipeline, I need realistic app store review data so agents can be tested against representative inputs.

**Schema:** `review_id, platform, rating, review_text, user_name, date, app_version`

**Tasks:**
- [ ] Write `scripts/generate_mock_data.py` to produce all three CSVs programmatically
- [ ] Generate ≥ 50 rows distributed across categories:

| Category | Count | Typical Rating | Sample Pattern |
|----------|-------|----------------|----------------|
| Bug | 12 | 1–2 | "App crashes when I…", "Can't login since update" |
| Feature Request | 10 | 3–4 | "Please add dark mode", "Would love to see…" |
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
| **Assignee** | Backend Dev – DB/Infra |
| **Priority** | 🔴 Critical |
| **Story Points** | 3 |
| **Sprint** | 1 |
| **Status** | Done |
| **Dependencies** | BE-DB-001 |

**User Story:** As the pipeline, I need realistic support email data so agents can handle the second input channel.

**Schema:** `email_id, subject, body, sender_email, timestamp, priority`

**Tasks:**
- [ ] Generate ≥ 30 rows using `scripts/generate_mock_data.py`
- [ ] Include technical bug emails with: device model, OS version, steps to reproduce
- [ ] Mix formal business tone and casual user tone
- [ ] Leave `priority` blank for ~30% of rows; others: `"High"`, `"Medium"`, `"Low"`
- [ ] Include these subjects:
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
| **Assignee** | Backend Dev – DB/Infra |
| **Priority** | 🟠 High |
| **Story Points** | 2 |
| **Sprint** | 1 |
| **Status** | Done |
| **Dependencies** | BE-DB-002, BE-DB-003 |

**User Story:** As the QA Engineer, I need ground-truth labels for every input item so I can measure classification accuracy objectively.

**Schema:** `source_id, source_type, category, priority, technical_details, suggested_title`

**Tasks:**
- [ ] Create one row per review (`source_type="review"`) and one per email (`source_type="email"`)
- [ ] Manually assign correct `category` and `priority`
- [ ] For Bug rows: fill `technical_details` with device/OS/reproduction info
- [ ] Write `suggested_title` as a clear, ≤10-word actionable ticket title
- [ ] Valid values:
  - `category`: `Bug` | `Feature Request` | `Praise` | `Complaint` | `Spam`
  - `priority`: `Critical` | `High` | `Medium` | `Low`

**Definition of Done:**
- Row count equals `len(reviews) + len(emails)` = 80
- Zero missing `category` or `priority` values
- All Bug rows have non-empty `technical_details`

---

### BE-DB-005 · Product Tech Docs for RAG
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev – DB/Infra |
| **Priority** | 🟠 High |
| **Story Points** | 2 |
| **Sprint** | 1 |
| **Status** | Done |
| **Dependencies** | BE-DB-001 |

**User Story:** As the Bug Analyzer and Feature Extractor agents, I need product documentation in ChromaDB so I can ground my reasoning in the actual product knowledge base.

**Tasks:**
- [ ] Create `docs/product/` directory
- [ ] Write `docs/product/product_overview.md` — app description, key features, user personas
- [ ] Write `docs/product/feature_catalog.md` — all current features with descriptions (login, sync, search, notifications, etc.)
- [ ] Write `docs/product/known_issues.md` — documented bugs, workarounds, affected versions
- [ ] Write `docs/product/architecture.md` — system components, tech stack, data flow
- [ ] These files are auto-indexed by the `rag_loader` node at pipeline startup into the `tech_documents` ChromaDB collection

**Definition of Done:**
- At least 4 markdown files in `docs/product/`
- Each file is ≥ 300 words with realistic product content
- `chroma_store.index_tech_docs()` indexes them without errors

---

## Phase 1 — Core Agent Development

### BE-API-001 · LangGraph State Schema & Graph Skeleton
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev – API/Coding |
| **Priority** | 🔴 Critical |
| **Story Points** | 5 |
| **Sprint** | 1 |
| **Status** | Done |
| **Dependencies** | BE-DB-001 |

**User Story:** As a developer, I need a typed shared state and a wired graph skeleton so every agent node has a clear contract and the execution flow is defined before any node is implemented.

**Tasks:**
- [ ] Define all Pydantic models in `src/graph/state.py`:
  - `FeedbackItem(id, source_type, text, metadata, raw_row)`
  - `ClassificationResult(category, confidence, reasoning, needs_review)`
  - `ClassifiedItem` — extends `FeedbackItem` + `classification` + `similar_reviews`
  - `BugDetails(source_id, platform, device, os_version, app_version, steps_to_reproduce, severity, affected_feature, similar_bugs, product_context)`
  - `FeatureDetails(source_id, feature_summary, description, user_impact, demand_score, user_segment, is_duplicate, duplicate_of, similar_features, product_context)`
  - `Ticket(ticket_id, source_id, source_type, title, description, category, priority, severity, assignee_team, tags, created_at, status, is_duplicate, duplicate_of)`
  - `QCResult(ticket_id, passed, failed_rules, qc_notes, llm_completeness_score, priority_escalated)`
  - `LogEntry(log_id, source_id, stage, result, details, timestamp)`
- [ ] Define `AgentState` TypedDict with `Annotated[list, operator.add]` for `log_entries` and `errors`
- [ ] Wire `StateGraph` in `src/graph/pipeline.py` with stub nodes
- [ ] Add `rag_loader` as the first node (runs before `csv_reader`)
- [ ] Implement `route_after_classify` conditional edge → `"bug"` | `"feature"` | `"other"`
- [ ] Confirm `graph.compile()` runs without errors
- [ ] Write smoke tests in `tests/unit/test_graph_skeleton.py` (≥ 10 tests)

**Node execution order:**
```
START → rag_loader → csv_reader → classifier → [conditional]
  ├─ bug_analyzer       ─┐
  ├─ feature_extractor  ─┤  (fan-in)
  └─ passthrough        ─┘
         └─ ticket_creator → quality_critic → END
```

**Definition of Done:**
- `graph.compile()` succeeds
- All state fields typed (no `Any` except in `metadata` dicts)
- All 10+ smoke tests pass with zero API calls

---

### BE-DB-006 · ChromaDB Vector Store — 3 Collections
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev – DB/Infra |
| **Priority** | 🔴 Critical |
| **Story Points** | 5 |
| **Sprint** | 1 |
| **Status** | Done |
| **Dependencies** | BE-DB-001 |

**User Story:** As the pipeline, I need three ChromaDB collections so agents can retrieve past feedback, detect duplicate tickets, and query product documentation as RAG context.

**Collections and purposes:**

| Collection | Name constant | Populated by | Queried by |
|------------|--------------|--------------|------------|
| Raw feedback | `feedback_reviews` | CSV Reader (every item) | Classifier, Bug Analyzer |
| Generated tickets | `generated_tickets` | Ticket Creator | Ticket Creator (dedup) |
| Product docs | `tech_documents` | RAG Loader (startup) | Bug Analyzer, Feature Extractor |

**Tasks:**
- [ ] Implement `src/db/chroma_store.py` with `ChromaStore` class:
  - `init() → ChromaStore` — creates/loads all 3 collections with cosine distance
  - `upsert_review(id, text, metadata)` — stores raw feedback
  - `find_similar_reviews(text, k, threshold, source_type)` — finds past similar items
  - `upsert_ticket(ticket_id, title, description, metadata)` — stores generated ticket
  - `find_similar_tickets(text, k, threshold, category)` — detects duplicate tickets
  - `index_tech_docs(docs_dir)` — walks directory, chunks by paragraph, upserts
  - `upsert_tech_doc(doc_id, text, metadata)` — single-chunk upsert
  - `query_tech_docs(query, k)` — retrieves relevant product context
  - `get_store() → ChromaStore` — module-level singleton
- [ ] Use `OpenAIEmbeddingFunction` with `text-embedding-3-small`
- [ ] Return `SimilarResult(id, text, metadata, similarity_score)` from all query methods
- [ ] All paths read from `config.CHROMA_PATH` — no hardcoded paths

**Definition of Done:**
- Integration test: upsert 5 texts → query → correct top-1 returned for each collection
- `find_similar_*` returns empty list (not error) when collection is empty
- `index_tech_docs` on missing directory logs warning and returns 0 (no crash)

---

### BE-API-002 · RAG Loader Agent Node
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev – API/Coding |
| **Priority** | 🔴 Critical |
| **Story Points** | 3 |
| **Sprint** | 2 |
| **Status** | Done |
| **Dependencies** | BE-API-001, BE-DB-006, BE-DB-005 |

**User Story:** As the pipeline, I need a RAG Loader node that runs first so all downstream agents have product context available in state before they start processing feedback.

**Tasks:**
- [ ] Implement `rag_loader_node(state)` in `src/agents/rag_loader.py`
- [ ] Call `chroma_store.index_tech_docs(config.TECH_DOCS_DIR)` — idempotent (upsert)
- [ ] Run a broad warm-up query `"product overview features architecture"` with `k=5`
- [ ] Write results into `state["tech_doc_context"]` as `[{id, text, source}]`
- [ ] Set `state["run_id"]` to a new `uuid.uuid4()` string
- [ ] Initialize `state["metrics"]` with `run_start` ISO timestamp
- [ ] Log a warning (not crash) if `TECH_DOCS_DIR` does not exist

**Definition of Done:**
- Unit test: `tech_doc_context` is a list (may be empty) after node runs
- Unit test: `run_id` is a valid UUID string
- Node never raises — all ChromaDB errors caught and logged

---

### BE-API-003 · CSV Reader Agent Node
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev – API/Coding |
| **Priority** | 🔴 Critical |
| **Story Points** | 3 |
| **Sprint** | 2 |
| **Status** | Done |
| **Dependencies** | BE-API-001, BE-DB-002, BE-DB-003, BE-DB-006 |

**User Story:** As the pipeline, I need to ingest both CSV files into a unified list of `FeedbackItem` objects and store them in ChromaDB so downstream agents work with a consistent schema and can retrieve similar past feedback.

**Tasks:**
- [ ] Implement `csv_reader_node(state)` in `src/agents/csv_reader.py`
- [ ] Normalize `app_store_reviews` → `FeedbackItem(id=review_id, source_type="review", text=review_text, metadata={platform, rating, date, app_version, user_name}, raw_row=...)`
- [ ] Normalize `support_emails` → `FeedbackItem(id=email_id, source_type="email", text=f"{subject}\n\n{body}", metadata={subject, sender_email, timestamp, priority}, raw_row=...)`
- [ ] After normalising each item, call `chroma_store.upsert_review(id, text, metadata)` — stores in `feedback_reviews` collection
- [ ] Log warning and skip malformed rows (do not raise)
- [ ] Read paths from `config.DATA_DIR`
- [ ] Append a `LogEntry` per item to `state["log_entries"]`

**Definition of Done:**
- Unit test: 50 reviews + 30 emails → 80 `FeedbackItem` objects in state
- Unit test: each item is upserted into the reviews ChromaDB collection (mock asserts called)
- Unit test: 2 malformed rows → 2 skipped, rest processed, 2 warnings logged
- No `KeyError` or `AttributeError` on any mock data row

---

### BE-API-004 · Feedback Classifier Agent Node
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev – API/Coding |
| **Priority** | 🔴 Critical |
| **Story Points** | 8 |
| **Sprint** | 2 |
| **Status** | Done |
| **Dependencies** | BE-API-003 |

**User Story:** As the system, I need every feedback item categorized with a confidence score and relevant past-feedback context so downstream routing and prioritization are accurate.

**Tasks:**
- [ ] Implement `classifier_node(state)` in `src/agents/classifier.py`
- [ ] Before classifying each item, call `chroma_store.find_similar_reviews(text, k=3)` to retrieve similar past feedback as RAG context — include summaries in the prompt
- [ ] Use OpenAI `gpt-4o` with structured output (`client.beta.chat.completions.parse()`) and `ClassificationResult` as the response model
- [ ] Define `ClassificationResult` Pydantic model:
  ```python
  class ClassificationResult(BaseModel):
      category: Literal["Bug", "Feature Request", "Praise", "Complaint", "Spam"]
      confidence: float          # 0.0 – 1.0 (clamped by validator)
      reasoning: str             # one-sentence justification
      needs_review: bool         # True if confidence < CLASSIFICATION_THRESHOLD
  ```
- [ ] System prompt: senior product triage analyst persona with one-shot examples for all 5 categories
- [ ] Process items in batches of 10 (`config.CLASSIFIER_BATCH_SIZE`) to limit API calls
- [ ] Write `ClassifiedItem` (extends `FeedbackItem` + `classification` + `similar_reviews`) back to state
- [ ] Read `CLASSIFICATION_THRESHOLD` from config (default `0.7`)

**Definition of Done:**
- Accuracy ≥ 85% against `expected_classifications.csv` (80 items)
- `confidence` always in [0.0, 1.0] (validator clamps out-of-range LLM output)
- Items with `confidence < threshold` have `needs_review=True`
- Unit tests mock all API responses — zero real API calls in unit suite

---

### BE-API-005 · Bug Analyzer Agent Node
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev – API/Coding |
| **Priority** | 🟠 High |
| **Story Points** | 5 |
| **Sprint** | 2 |
| **Status** | Done |
| **Dependencies** | BE-API-004, BE-DB-006 |

**User Story:** As an engineer receiving a bug ticket, I need structured technical details extracted from the raw text — grounded in product documentation and similar past bugs — so I can reproduce the issue without reading the original feedback.

**Tasks:**
- [ ] Implement `bug_analyzer_node(state)` in `src/agents/bug_analyzer.py`
- [ ] Only processes items where `classified.classification.category == "Bug"`
- [ ] For each bug item, before calling the LLM:
  - Query `chroma_store.find_similar_reviews(text, k=3)` → similar past bug reports
  - Query `chroma_store.query_tech_docs(f"bug {affected_feature}", k=3)` → relevant product docs
  - Include both in the prompt as context sections
- [ ] Use OpenAI `gpt-4o` with `BugDetails` as structured response model
- [ ] Auto-assign severity rules (applied before LLM, can be overridden):
  - `Critical`: keywords crash, data loss, unable to open, frozen, urgent
  - `High`: login failure, feature completely broken, sync failure
  - `Medium`: degraded performance, intermittent issue, notification not working
  - `Low`: cosmetic, minor UI glitch, slow loading
- [ ] Mark all unknown fields as `"Unknown"` (never `None`)
- [ ] Store `similar_bugs` and `product_context` on `BugDetails` for traceability

**Definition of Done:**
- Unit tests cover 5 scenarios: crash, login failure, sync bug, cosmetic, sparse (no technical detail)
- `severity` always one of 4 valid values
- `steps_to_reproduce` always a list (validator ensures `["Not provided"]` if empty)
- `similar_bugs` and `product_context` populated (may be empty lists) on every `BugDetails`

---

### BE-API-006 · Feature Extractor Agent Node
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev – API/Coding |
| **Priority** | 🟠 High |
| **Story Points** | 5 |
| **Sprint** | 2 |
| **Status** | Done |
| **Dependencies** | BE-API-004, BE-DB-006 |

**User Story:** As a product manager, I need feature requests scored by user demand and checked against existing tickets so duplicates are flagged and the roadmap reflects real user signal.

**Tasks:**
- [ ] Implement `feature_extractor_node(state)` in `src/agents/feature_extractor.py`
- [ ] Only processes items where `classified.classification.category == "Feature Request"`
- [ ] For each feature item, before calling the LLM:
  - Query `chroma_store.query_tech_docs(text, k=3)` → understand existing product features
  - Query `chroma_store.find_similar_reviews(text, k=5)` → measure demand signal (similar requests)
  - Query `chroma_store.find_similar_tickets(text, k=3, category="Feature Request")` → detect duplicate tickets
- [ ] Use OpenAI `gpt-4o` with `FeatureDetails` as structured response model
- [ ] Set `is_duplicate=True` and `duplicate_of=<ticket_id>` when similarity score ≥ `config.DUPLICATE_SIMILARITY_THRESHOLD`
- [ ] After extraction, upsert non-duplicate features into the `feedback_reviews` collection

**Definition of Done:**
- Unit test: 3 near-duplicate "dark mode" requests → 1 original, 2 marked `is_duplicate=True`
- `demand_score` always 1–5 (Pydantic `ge=1, le=5` constraint)
- `product_context` and `similar_features` stored on `FeatureDetails` for traceability

---

### BE-API-007 · Ticket Creator Agent Node
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev – API/Coding |
| **Priority** | 🔴 Critical |
| **Story Points** | 5 |
| **Sprint** | 2 |
| **Status** | Done |
| **Dependencies** | BE-API-005, BE-API-006 |

**User Story:** As an engineer, I need every actionable item converted to a consistently formatted ticket that is checked for cross-run duplicates before being written to CSV and ChromaDB.

**Tasks:**
- [ ] Implement `ticket_creator_node(state)` in `src/agents/ticket_creator.py`
- [ ] Generate tickets for: `Bug`, `Feature Request`, `Complaint`
- [ ] Skip ticket creation for: `Praise` (log as positive signal), `Spam` (log and discard)
- [ ] Before creating each ticket, call `chroma_store.find_similar_tickets(title + description, k=3, category=category)` — if match ≥ threshold set `is_duplicate=True`, `duplicate_of=<ticket_id>`
- [ ] After creating each ticket, call `chroma_store.upsert_ticket(ticket_id, title, description, metadata)` — stores in `generated_tickets` collection
- [ ] Write `generated_tickets.csv` with columns:
  `ticket_id | source_id | source_type | title | description | category | priority | severity | assignee_team | tags | created_at | status`
- [ ] `ticket_id` format: `TKT-YYYYMMDD-XXXX` (zero-padded sequence)
- [ ] `description` format: Markdown with **Summary**, **Steps/Details**, **Expected Behavior**
- [ ] Write `processing_log.csv` with one row per item (including skipped):
  `log_id | source_id | stage | result | details | timestamp`
- [ ] Append (do not truncate) existing CSV files — run-safe

**Definition of Done:**
- Unit test verifies all 12 columns present in output CSV
- `ticket_id` uniqueness guaranteed within a single run
- Praise and Spam have `processing_log` entries but no ticket rows
- `upsert_ticket` called for every non-duplicate ticket created (mock assertion)

---

### BE-API-008 · Quality Critic Agent Node
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev – API/Coding |
| **Priority** | 🟠 High |
| **Story Points** | 5 |
| **Sprint** | 2 |
| **Status** | Done |
| **Dependencies** | BE-API-007 |

**User Story:** As a product manager, I need every generated ticket reviewed for completeness and correct prioritization so low-quality tickets are flagged before they reach the engineering backlog.

**Tasks:**
- [ ] Implement `quality_critic_node(state)` in `src/agents/quality_critic.py`
- [ ] Run rule-based validation checks:

| Rule | Check | Action on Fail |
|------|-------|----------------|
| Title length | ≤ 80 chars | Flag `needs_review` |
| Description length | ≥ 50 chars | Flag `needs_review` |
| Priority assigned | Not blank | Flag `needs_review` |
| Category valid | One of 5 values | Flag `needs_review` |
| Bug has severity | Non-empty for Bug | Flag `needs_review` |

- [ ] Auto-escalate priority: description contains `crash` or `data loss` → set `priority = "Critical"`
- [ ] Optional LLM review (configurable via `config.json`): ask `gpt-4o` to rate completeness 1–5 and suggest improvements
- [ ] Write `metrics.csv` with run-level summary:
  `run_id | timestamp | total_items | bugs | features | praise | complaints | spam | tickets_created | qc_pass_rate | accuracy | avg_latency_ms`

**Definition of Done:**
- ≥ 95% of well-formed tickets pass QC automatically in unit tests
- Priority auto-escalation unit-tested with 3 crash/data-loss scenarios
- `metrics.csv` written after every run with correct column count

---

### BE-DB-007 · SQLAlchemy ORM & Alembic Migrations
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev – DB/Infra |
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
- [ ] Configure `src/db/session.py` to read `DATABASE_URL` from env (default: `sqlite:///./data/feedback.db`)
- [ ] Write Alembic migration: `alembic revision --autogenerate -m "initial schema"`
- [ ] Write `scripts/db_init.py`: creates tables, optionally imports existing CSVs

**Definition of Done:**
- `alembic upgrade head` runs against SQLite without errors
- Unit tests use `sqlite:///:memory:` — no file system writes
- `db_init.py` imports 80-row mock dataset without errors

---

## Phase 2 — Pipeline Integration

### BE-API-009 · End-to-End Pipeline Integration
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev – API/Coding |
| **Priority** | 🔴 Critical |
| **Story Points** | 8 |
| **Sprint** | 3 |
| **Status** | Done |
| **Dependencies** | BE-API-002, BE-API-003, BE-API-004, BE-API-005, BE-API-006, BE-API-007, BE-API-008, BE-DB-006, BE-DB-007 |

**User Story:** As a user, I need to run `python -m src.main` and have the system automatically process all CSVs and produce all output files with no manual intervention.

**Tasks:**
- [ ] Replace all stub nodes with real implementations in `src/graph/pipeline.py`
- [ ] Implement `run_pipeline(data_dir, output_dir, config)` in `src/graph/pipeline.py`
- [ ] Implement CLI entry point `src/main.py` with argparse:
  - `--data-dir` (default from `.env`)
  - `--output-dir` (default from `.env`)
  - `--dry-run` (classify only, no ticket creation or CSV writes)
- [ ] Write output CSVs atomically (write to `.tmp` file, then `os.rename`)
- [ ] Item-level error handling: one bad item logs error and continues; never aborts pipeline
- [ ] Print run summary table to stdout on completion
- [ ] Initialize ChromaDB singleton once at pipeline start via `get_store()`

**Definition of Done:**
- `python -m src.main` with mock data produces all 3 output files
- Pipeline processes 80 items in under 5 minutes
- Killing mid-run and rerunning does not produce duplicate ticket IDs
- `--dry-run` mode produces no ticket CSV writes
- `generated_tickets`, `processing_log`, and `metrics` CSVs all have correct schema

---

## Phase 3 — Streamlit UI

### FE-001 · Streamlit App Shell & Navigation
| Field | Value |
|-------|-------|
| **Assignee** | Frontend Dev – Streamlit |
| **Priority** | 🔴 Critical |
| **Story Points** | 3 |
| **Sprint** | 3 |
| **Status** | Done |
| **Dependencies** | BE-DB-001 |

**User Story:** As a product manager, I need a web UI with clear navigation so I can monitor, control, and review the feedback pipeline without using the command line.

**Tasks:**
- [ ] Create `ui/app.py` as Streamlit entry point with sidebar navigation
- [ ] Implement shared helpers in `ui/utils.py`: `load_tickets()`, `load_metrics()`, `load_logs()`
- [ ] Create 5 page files under `ui/pages/`
- [ ] App title: "Feedback Intelligence System"
- [ ] Handle cold-start gracefully: no output files → show "Run pipeline first" banner, not traceback
- [ ] Store pipeline run state in `st.session_state`

**Definition of Done:**
- `streamlit run ui/app.py` launches with no errors
- All 5 pages accessible from sidebar
- Cold-start state shows placeholder, not Python traceback

---

### FE-002 · Dashboard Page
| Field | Value |
|-------|-------|
| **Assignee** | Frontend Dev – Streamlit |
| **Priority** | 🟠 High |
| **Story Points** | 5 |
| **Sprint** | 3 |
| **Status** | Done |
| **Dependencies** | FE-001, BE-API-009 |

**User Story:** As a product manager, I need a dashboard with KPIs and charts so I can assess the pipeline's output at a glance without reading raw CSV files.

**Tasks:**
- [ ] KPI row (4 `st.metric` cards): Total Feedback · Tickets Created · QC Pass Rate · Avg Latency
- [ ] Category breakdown: Plotly donut chart (Bug / Feature / Praise / Complaint / Spam)
- [ ] Source breakdown: Plotly grouped bar (App Store vs Support Email per category)
- [ ] Recent tickets table: last 20 tickets, `st.dataframe` with priority colour-coding
- [ ] "Refresh" button: re-reads CSVs without full page reload

**Definition of Done:**
- KPI cards populated from `metrics.csv`
- Charts render with Plotly (not matplotlib)
- Priority colour: Critical=red, High=orange, Medium=yellow, Low=green
- Empty state shows info banner, not traceback

---

### FE-003 · Run Pipeline Page
| Field | Value |
|-------|-------|
| **Assignee** | Frontend Dev – Streamlit |
| **Priority** | 🔴 Critical |
| **Story Points** | 5 |
| **Sprint** | 3 |
| **Status** | Done |
| **Dependencies** | FE-001, BE-API-009 |

**User Story:** As a product manager, I need to trigger the feedback pipeline from the UI and monitor its progress so I do not need terminal access.

**Tasks:**
- [ ] File uploader: accept custom `app_store_reviews.csv` and `support_emails.csv` (optional override)
- [ ] "Run Pipeline" button: triggers `run_pipeline()` in a `threading.Thread`
- [ ] Progress bar: `st.progress` updated as each item is processed
- [ ] Live log table: reads `processing_log.csv` every 2 seconds during run (`st.empty`)
- [ ] Toast notification on completion: success (green) or error (red)
- [ ] "Run Pipeline" button disabled while pipeline is running

**Definition of Done:**
- UI remains responsive (no freezing) while pipeline runs
- Progress bar reaches 100% on successful run completion
- Running pipeline twice without waiting shows "already running" warning

---

### FE-004 · Tickets Page — View & Manual Override
| Field | Value |
|-------|-------|
| **Assignee** | Frontend Dev – Streamlit |
| **Priority** | 🟠 High |
| **Story Points** | 8 |
| **Sprint** | 3 |
| **Status** | Done |
| **Dependencies** | FE-001, BE-API-007, BE-API-008 |

**User Story:** As an engineer, I need to view all generated tickets and override fields like priority or status so I can correct misclassifications before they enter the engineering backlog.

**Tasks:**
- [ ] Filterable ticket table with sidebar filters: category, priority, status, date range
- [ ] Keyword search bar filtering `title` and `description`
- [ ] Row click → opens edit form (`st.form`) with editable: title, description, priority, status
- [ ] "Save Changes" button: writes edits to `generated_tickets.csv` and DB; appends to `processing_log.csv`
- [ ] "Approve All" button: sets all `needs_review` tickets to `open` in bulk
- [ ] "Export CSV" button: downloads current filtered view as CSV
- [ ] Show `is_duplicate` badge on duplicate tickets with link to `duplicate_of` ticket

**Definition of Done:**
- Edits persist to CSV after page refresh
- Filter and search work independently and in combination
- "Approve All" only changes `needs_review` rows
- Duplicate tickets visually distinguished

---

### FE-005 · Configuration Panel
| Field | Value |
|-------|-------|
| **Assignee** | Frontend Dev – Streamlit |
| **Priority** | 🟡 Medium |
| **Story Points** | 3 |
| **Sprint** | 3 |
| **Status** | Done |
| **Dependencies** | FE-001 |

**User Story:** As a power user, I need to adjust classification thresholds from the UI so I can tune the pipeline without editing config files directly.

**Tasks:**
- [ ] Confidence threshold slider: range 0.5–1.0, step 0.05, default 0.7
- [ ] Duplicate similarity threshold slider: range 0.5–1.0, step 0.05, default 0.85
- [ ] Default priority dropdowns: one per category (Bug / Feature Request / Complaint)
- [ ] Data directory path inputs with validation
- [ ] "Save Configuration" button: writes to `config.json` via `config.save_json_config()`
- [ ] "Reset to Defaults" button
- [ ] Show current values on load from `config.json`

**Definition of Done:**
- Saving config writes valid JSON to `config.json`
- Pipeline reads updated config on next run (no restart required)
- Invalid paths show inline error, not Python exception

---

### FE-006 · Analytics Page
| Field | Value |
|-------|-------|
| **Assignee** | Frontend Dev – Streamlit |
| **Priority** | 🟡 Medium |
| **Story Points** | 5 |
| **Sprint** | 4 |
| **Status** | Done |
| **Dependencies** | FE-002, BE-API-009 |

**User Story:** As a product manager, I need trend charts and accuracy metrics so I can demonstrate the system's performance during the capstone demo.

**Tasks:**
- [ ] Trend line chart: tickets created per run over time
- [ ] Category stacked bar: App Store vs Email per category
- [ ] Classification accuracy bar chart (per category vs `expected_classifications.csv`)
- [ ] Top feature requests table: sorted by `demand_score` desc
- [ ] Processing latency histogram
- [ ] Date range filter applied to all charts

**Definition of Done:**
- All 5 charts render with Plotly
- Accuracy chart hidden (not error) when `expected_classifications.csv` absent
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
| **Dependencies** | BE-API-002 through BE-API-008 |

**User Story:** As the team, we need comprehensive unit tests for every agent node so regressions are caught in CI before they reach integration testing.

**Tasks:**
- [ ] Write `tests/unit/test_<agent_name>.py` for each of 7 nodes (including rag_loader)
- [ ] Mock all OpenAI API calls with `pytest-mock` (zero real API calls)
- [ ] Mock all ChromaDB calls — test that correct collections are queried
- [ ] Cover per node: happy path, empty input, malformed input, edge cases
- [ ] Use `pytest.fixture` for reusable `FeedbackItem` and `ClassifiedItem` factories
- [ ] Run with `pytest tests/unit/ --cov=src/agents --cov-report=term-missing`

**Coverage targets:**

| Agent | Min Coverage |
|-------|-------------|
| rag_loader | 90% |
| csv_reader | 95% |
| classifier | 90% |
| bug_analyzer | 90% |
| feature_extractor | 90% |
| ticket_creator | 95% |
| quality_critic | 90% |

**Definition of Done:**
- `pytest tests/unit/` passes with 0 failures
- All coverage targets met
- No real API or ChromaDB calls (verified via mock assertion)

---

### QA-002 · Integration Tests — Full Pipeline
| Field | Value |
|-------|-------|
| **Assignee** | QA Engineer |
| **Priority** | 🟠 High |
| **Story Points** | 5 |
| **Sprint** | 4 |
| **Status** | Todo |
| **Dependencies** | BE-API-009 |

**User Story:** As the team, we need an integration test that runs the full pipeline end-to-end so we know the system works correctly as a whole.

**Tasks:**
- [ ] Create `tests/fixtures/` with 10-item versions of all 3 CSVs (hand-labelled)
- [ ] Write `tests/integration/test_pipeline.py`:
  - Test: pipeline runs without exception on 10-item fixture
  - Test: `generated_tickets.csv` has correct schema
  - Test: ticket count matches expected (non-Praise, non-Spam items)
  - Test: classification accuracy ≥ 80% on fixture
  - Test: ChromaDB collections populated after run (reviews + tickets collections non-empty)
- [ ] Mark with `@pytest.mark.integration`
- [ ] Add `pytest.ini` to exclude integration from default run: `-m "not integration"`

**Definition of Done:**
- `pytest -m integration tests/integration/` passes
- Uses real OpenAI API and real ChromaDB
- Accuracy assertion only runs when fixture `expected_classifications.csv` exists

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

**User Story:** As the capstone evaluator, I need a benchmark report with precision, recall, and F1 per category so I can objectively assess classification quality.

**Tasks:**
- [ ] Run full pipeline against complete 80-item mock dataset
- [ ] Compute per-category: Precision, Recall, F1 using scikit-learn
- [ ] Write `docs/benchmark_report.md` with confusion matrix, per-category table, overall weighted F1, top-5 misclassified examples

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

**User Story:** As the team, we need automated UI tests so we catch page load errors before the demo.

**Tasks:**
- [ ] Write `tests/ui/test_smoke.py` using pytest + subprocess to launch Streamlit
- [ ] Test: all 5 pages load without HTTP errors
- [ ] Test: Dashboard shows "Run pipeline first" when no data present
- [ ] Test: Configuration page saves `config.json` after form submit
- [ ] Test: Tickets page shows filter controls
- [ ] Run against `localhost:8501` with fixture output files pre-loaded

**Definition of Done:**
- All smoke tests pass when Streamlit is running
- Tests use fixture data (not real pipeline run)

---

### BE-DB-008 · Docker Compose Setup
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev – DB/Infra |
| **Priority** | 🟠 High |
| **Story Points** | 5 |
| **Sprint** | 4 |
| **Status** | Todo |
| **Dependencies** | BE-DB-001, FE-001 |

**User Story:** As a developer or evaluator, I need to run the entire system with `docker compose up` so I don't need to manually install Python or ChromaDB.

**Tasks:**
- [ ] Write `docker/Dockerfile` — multi-stage: builder installs deps, runner copies app (`python:3.11-slim`)
- [ ] Write `docker/docker-compose.yml` with services:
  - `app`: Streamlit on port 8501 (SQLite DB file mounted via volume)
  - `chroma`: ChromaDB server on port 8000 (optional embedded mode)
- [ ] Mount `./data` as a Docker volume so the SQLite file persists across container restarts
- [ ] Pass all config via environment variables — no hardcoded values
- [ ] Add `.dockerignore`: excludes `__pycache__`, `.venv`, `.env`
- [ ] Validate: `docker compose up --build` → app healthy at `http://localhost:8501`

**Definition of Done:**
- `docker compose up` starts all services from a cold pull
- Image size ≤ 1 GB
- SQLite data persists across container restarts via the mounted `./data` volume

---

### BE-DB-009 · Azure Deployment
| Field | Value |
|-------|-------|
| **Assignee** | Backend Dev – DB/Infra |
| **Priority** | 🟡 Medium |
| **Story Points** | 5 |
| **Sprint** | 4 |
| **Status** | Todo |
| **Dependencies** | BE-DB-008 |

**User Story:** As the capstone evaluator, I need the app accessible at a public URL so I can review the live system without running it locally.

**Tasks:**
- [ ] Push Docker image to Azure Container Registry (ACR)
- [ ] Deploy to Azure Container Apps (or Azure App Service)
- [ ] Mount an Azure File Share or persistent volume for the SQLite `data/` directory
- [ ] Store secrets (`OPENAI_API_KEY`, DB password) in Azure Key Vault
- [ ] Configure health check: `GET /healthz` → 200 OK
- [ ] Document full deployment steps in `docs/azure_deployment.md`

**Definition of Done:**
- App accessible at a public `*.azurecontainerapps.io` URL
- No secrets in container image or env variable literals
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
| **Dependencies** | BE-API-009, FE-003, QA-003 |

**User Story:** As the presenting team, we need a polished demo script and slide deck so the capstone evaluation is smooth and covers all required demonstration points.

**Tasks:**
- [ ] Write demo script (`docs/demo_script.md`) covering all 6 required steps:
  1. Data ingestion from mock CSV files
  2. Real-time processing with agent interactions
  3. Classification accuracy vs expected results
  4. Ticket generation with proper formatting
  5. User interface functionality and monitoring
  6. Error handling and edge case management
- [ ] Create slide deck (≤ 10 slides): problem, architecture, RAG design, demo flow, metrics, learnings
- [ ] Set up demo environment with pre-loaded mock data
- [ ] Conduct at least 1 full rehearsal

**Definition of Done:**
- Demo walkthrough ≤ 15 minutes
- All 6 required demo steps covered
- Rehearsal completed and feedback incorporated

---

## Task Summary

| Phase | Tasks | 🔴 Critical | 🟠 High | 🟡 Medium | Story Points |
|-------|-------|------------|--------|----------|-------------|
| 0 – Setup & Mock Data | 6 | 3 | 2 | 1 | 18 |
| 1 – Core Agents | 9 | 5 | 4 | 0 | 44 |
| 2 – Pipeline | 1 | 1 | 0 | 0 | 8 |
| 3 – Streamlit UI | 6 | 2 | 2 | 2 | 29 |
| 4 – QA & Deployment | 7 | 0 | 3 | 4 | 32 |
| **Total** | **29** | **11** | **11** | **7** | **131** |

**Sprint Velocity Target:** ~33 story points / sprint × 4 sprints = 131 points ✓

---

## Dependency Graph

```
PM-001
└── BE-DB-001
    ├── BE-DB-002 ──┐
    ├── BE-DB-003 ──┼── BE-DB-004
    ├── BE-DB-005 (tech docs)
    ├── BE-DB-006 (ChromaDB — 3 collections)
    ├── BE-DB-007 (SQLAlchemy ORM)
    ├── BE-API-001 (state + graph skeleton)
    │   ├── BE-API-002 (rag_loader) ← needs BE-DB-005, BE-DB-006
    │   │   └── BE-API-003 (csv_reader) ← needs BE-DB-002, BE-DB-003, BE-DB-006
    │   │       └── BE-API-004 (classifier) ← queries feedback_reviews
    │   │           ├── BE-API-005 (bug_analyzer) ← queries tech_docs + feedback_reviews
    │   │           └── BE-API-006 (feature_extractor) ← queries all 3 collections
    │   │               └── BE-API-007 (ticket_creator) ← queries + upserts generated_tickets
    │   │                   └── BE-API-008 (quality_critic)
    │   │                       └── BE-API-009 (end-to-end) ── QA-002
    │   └── BE-DB-006
    └── FE-001
        ├── FE-002 (needs BE-API-009)
        ├── FE-003 (needs BE-API-009)
        ├── FE-004 (needs BE-API-007, BE-API-008)
        ├── FE-005
        └── FE-006 (needs BE-API-009)

BE-DB-001 ── BE-DB-008 (Docker)
    └── BE-DB-009 (Azure)

QA-002 + BE-DB-004 ── QA-003
BE-API-009 + FE-003 + QA-003 ── PM-002
```

---

## RAG Architecture Summary

The system uses ChromaDB with OpenAI `text-embedding-3-small` across three collections:

| Collection | Contents | Written by | Read by |
|------------|---------|------------|---------|
| `feedback_reviews` | Every normalised review + email | CSV Reader | Classifier, Bug Analyzer |
| `generated_tickets` | Every created ticket (title + desc) | Ticket Creator | Ticket Creator (dedup check) |
| `tech_documents` | Product docs from `docs/product/*.md` | RAG Loader (startup) | Bug Analyzer, Feature Extractor |

The **RAG Loader** node runs first in the pipeline and populates `state["tech_doc_context"]`
so all downstream nodes have product knowledge available without re-querying ChromaDB per item.
