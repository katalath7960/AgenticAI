"""
src/config.py
Central configuration — reads .env then config.json.
All modules import constants from here; never read os.environ directly.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env", override=False)

_CONFIG_FILE = _ROOT / "config.json"


def _load_json() -> dict:
    if _CONFIG_FILE.exists():
        with open(_CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


_json = _load_json()


def _get(key: str, default: str = "") -> str:
    """JSON config overrides env; env overrides default."""
    return str(_json.get(key, os.getenv(key, default)))


# ── LLM ──────────────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = _get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    import warnings
    warnings.warn(
        "OPENAI_API_KEY is not set. Set it in .env or config.json before running the pipeline.",
        stacklevel=2,
    )
OPENAI_MODEL: str = _get("OPENAI_MODEL", "gpt-4o")
OPENAI_TEMPERATURE: float = float(_get("OPENAI_TEMPERATURE", "0.0"))

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL: str = _get("DATABASE_URL", f"sqlite:///{_ROOT / 'data' / 'feedback.db'}")

# ── ChromaDB ─────────────────────────────────────────────────────────────────
CHROMA_PATH: str = _get("CHROMA_PATH", str(_ROOT / "data" / "chroma"))
CHROMA_COLLECTION_REVIEWS: str = "feedback_reviews"
CHROMA_COLLECTION_TICKETS: str = "generated_tickets"
CHROMA_COLLECTION_TECH_DOCS: str = "tech_documents"

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR: str = _get("DATA_DIR", str(_ROOT / "data" / "input"))
OUTPUT_DIR: str = _get("OUTPUT_DIR", str(_ROOT / "data" / "output"))
TECH_DOCS_DIR: str = _get("TECH_DOCS_DIR", str(_ROOT / "docs" / "product"))

# ── Pipeline ──────────────────────────────────────────────────────────────────
CLASSIFICATION_THRESHOLD: float = float(_get("CLASSIFICATION_THRESHOLD", "0.7"))
DUPLICATE_SIMILARITY_THRESHOLD: float = float(_get("DUPLICATE_SIMILARITY_THRESHOLD", "0.85"))
CLASSIFIER_BATCH_SIZE: int = int(_get("CLASSIFIER_BATCH_SIZE", "10"))


def save_json_config(updates: dict) -> None:
    """Persist updates to config.json (called by Streamlit config panel)."""
    current = _load_json()
    current.update(updates)
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)


def as_dict() -> dict:
    return {
        "OPENAI_MODEL": OPENAI_MODEL,
        "DATABASE_URL": DATABASE_URL,
        "CHROMA_PATH": CHROMA_PATH,
        "DATA_DIR": DATA_DIR,
        "OUTPUT_DIR": OUTPUT_DIR,
        "TECH_DOCS_DIR": TECH_DOCS_DIR,
        "CLASSIFICATION_THRESHOLD": CLASSIFICATION_THRESHOLD,
        "DUPLICATE_SIMILARITY_THRESHOLD": DUPLICATE_SIMILARITY_THRESHOLD,
        "CLASSIFIER_BATCH_SIZE": CLASSIFIER_BATCH_SIZE,
    }
