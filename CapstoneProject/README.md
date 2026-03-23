# Intelligent User Feedback Analysis & Action System

Capstone Project — Agentic AI Certification

## Overview

A multi-agent LangGraph pipeline that ingests app store reviews and support emails, classifies them, extracts structured details, generates tickets, and surfaces everything through a Streamlit UI.

**Tech Stack:** LangGraph · Python 3.11 · SQLite / Postgres · ChromaDB · Streamlit · Docker · Azure
**LLM:** Claude Opus 4.6 via Anthropic SDK

## Local Dev Setup

### 1. Clone & create virtualenv

```bash
git clone <repo-url>
cd capstone
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY
```

### 4. Run the pipeline (CLI)

```bash
python -m src.main
```

### 5. Launch the Streamlit UI

```bash
streamlit run ui/app.py
```

## Project Structure

```
capstone/
├── data/
│   ├── input/          # CSV input files (reviews + emails)
│   └── output/         # Generated tickets, logs, metrics
├── src/
│   ├── agents/         # LangGraph agent nodes
│   ├── graph/          # StateGraph wiring + state schema
│   ├── db/             # SQLAlchemy ORM + ChromaDB store
│   ├── config.py
│   └── main.py
├── ui/                 # Streamlit app + pages
├── tests/              # unit / integration / ui tests
├── docker/             # Dockerfile + docker-compose.yml
├── scripts/            # generate_mock_data.py, db_init.py, benchmark.py
└── docs/               # Architecture diagram, deployment guide
```

## Running Tests

```bash
# Unit tests only (no API calls)
pytest tests/unit/ --cov=src/agents --cov-report=term-missing

# Integration tests (requires ANTHROPIC_API_KEY)
pytest -m integration tests/integration/
```
