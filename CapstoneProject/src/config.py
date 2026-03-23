"""
src/config.py
Loads configuration from .env and config.json.
All other modules import from here — never read os.environ directly.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from dotenv import load_dotenv

# ── Locate project root (parent of src/) ──────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env", override=False)

# ── config.json (optional — UI writes updates here) ──────────────────────────
_CONFIG_FILE = _ROOT / "config.json"

def _load_json_config() -> dict:
    if _CONFIG_FILE.exists():
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

_json = _load_json_config()


def _get(key: str, default: str = "") -> str:
    """Read from JSON config first, then env, then default."""
    return str(_json.get(key, os.getenv(key, default)))


# ── LLM ──────────────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = _get("OPENAI_API_KEY")
OPENAI_MODEL: str = _get("OPENAI_MODEL", "gpt-4o")
OPENAI_TEMPERATURE: float = float(_get("OPENAI_TEMPERATURE", "0.0"))

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL: str = _get("DATABASE_URL", f"sqlite:///{_ROOT / 'data' / 'feedback.db'}")

# ── ChromaDB ─────────────────────────────────────────────────────────────────
CHROMA_PATH: str = _get("CHROMA_PATH", str(_ROOT / "data" / "chroma"))

# Collections
CHROMA_COLLECTION_REVIEWS: str = "feedback_reviews"     # all raw reviews + emails
CHROMA_COLLECTION_TICKETS: str = "generated_tickets"    # deduplicate tickets
CHROMA_COLLECTION_TECH_DOCS: str = "tech_documents"     # product/architecture docs

# ── Data dirs ─────────────────────────────────────────────────────────────────
DATA_DIR: str = _get("DATA_DIR", str(_ROOT / "data" / "input"))
OUTPUT_DIR: str = _get("OUTPUT_DIR", str(_ROOT / "data" / "output"))
TECH_DOCS_DIR: str = _get("TECH_DOCS_DIR", str(_ROOT / "docs" / "product"))

# ── Pipeline settings ─────────────────────────────────────────────────────────
CLASSIFICATION_THRESHOLD: float = float(_get("CLASSIFICATION_THRESHOLD", "0.7"))
DUPLICATE_SIMILARITY_THRESHOLD: float = float(_get("DUPLICATE_SIMILARITY_THRESHOLD", "0.85"))
CLASSIFIER_BATCH_SIZE: int = int(_get("CLASSIFIER_BATCH_SIZE", "10"))


def save_json_config(updates: dict) -> None:
    """Write updated key/value pairs back to config.json (used by UI)."""
    current = _load_json_config()
    current.update(updates)
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)


def as_dict() -> dict:
    """Return the full resolved config as a plain dict (for display in UI)."""
    return {
        "OPENAI_MODEL": OPENAI_MODEL,
        "OPENAI_TEMPERATURE": OPENAI_TEMPERATURE,
        "DATABASE_URL": DATABASE_URL,
        "CHROMA_PATH": CHROMA_PATH,
        "DATA_DIR": DATA_DIR,
        "OUTPUT_DIR": OUTPUT_DIR,
        "TECH_DOCS_DIR": TECH_DOCS_DIR,
        "CLASSIFICATION_THRESHOLD": CLASSIFICATION_THRESHOLD,
        "DUPLICATE_SIMILARITY_THRESHOLD": DUPLICATE_SIMILARITY_THRESHOLD,
        "CLASSIFIER_BATCH_SIZE": CLASSIFIER_BATCH_SIZE,
    }
