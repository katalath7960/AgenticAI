"""
ui/utils.py
Shared data-loading helpers used by every page.
All functions return empty DataFrames on cold-start (no CSV yet).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# ── Make src importable when running from project root ───────────────────────
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import src.config as config


# ── Column schemas ────────────────────────────────────────────────────────────

TICKET_COLS = [
    "ticket_id", "source_id", "source_type", "title", "description",
    "category", "priority", "severity", "assignee_team", "tags",
    "created_at", "status", "is_duplicate", "duplicate_of",
]
LOG_COLS = ["log_id", "source_id", "stage", "result", "details", "timestamp"]
METRICS_COLS = [
    "run_id", "timestamp", "total_items", "bugs", "features",
    "praise", "complaints", "spam", "tickets_created", "qc_pass_rate", "avg_latency_ms",
]

PRIORITY_COLORS = {
    "Critical": "#ef4444",
    "High":     "#f97316",
    "Medium":   "#eab308",
    "Low":      "#22c55e",
}

CATEGORY_COLORS = {
    "Bug":             "#ef4444",
    "Feature Request": "#3b82f6",
    "Praise":          "#22c55e",
    "Complaint":       "#f97316",
    "Spam":            "#9ca3af",
}


def _safe_read(path: str, cols: list[str]) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, dtype=str).fillna("")
        for c in cols:
            if c not in df.columns:
                df[c] = ""
        return df[cols]
    except FileNotFoundError:
        return pd.DataFrame(columns=cols)
    except Exception as exc:
        st.warning(f"Could not read {Path(path).name}: {exc}")
        return pd.DataFrame(columns=cols)


@st.cache_data(ttl=5)
def load_tickets() -> pd.DataFrame:
    return _safe_read(os.path.join(config.OUTPUT_DIR, "generated_tickets.csv"), TICKET_COLS)


@st.cache_data(ttl=5)
def load_logs() -> pd.DataFrame:
    return _safe_read(os.path.join(config.OUTPUT_DIR, "processing_log.csv"), LOG_COLS)


@st.cache_data(ttl=5)
def load_metrics() -> pd.DataFrame:
    return _safe_read(os.path.join(config.OUTPUT_DIR, "metrics.csv"), METRICS_COLS)


def reload_all() -> None:
    """Invalidate all cached DataFrames so next access re-reads CSVs."""
    load_tickets.clear()
    load_logs.clear()
    load_metrics.clear()


def save_tickets(df: pd.DataFrame) -> None:
    """Persist ticket DataFrame back to CSV (used by edit form)."""
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    path = os.path.join(config.OUTPUT_DIR, "generated_tickets.csv")
    df.to_csv(path, index=False)
    load_tickets.clear()


def cold_start_banner(message: str = "No pipeline output yet. Go to **Run Pipeline** to generate data.") -> None:
    st.info(f"ℹ️ {message}", icon=None)


def priority_badge(priority: str) -> str:
    color = PRIORITY_COLORS.get(priority, "#6b7280")
    return f'<span style="background:{color};color:white;padding:2px 8px;border-radius:4px;font-size:0.8em">{priority}</span>'
