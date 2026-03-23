"""
ui/pages/6_Configuration.py
Tune pipeline thresholds and paths; persisted to config.json.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import src.config as config

st.set_page_config(page_title="Configuration · FIS", page_icon="⚙️", layout="wide")
st.title("⚙️ Configuration")
st.markdown(
    "Changes are saved to `config.json` and take effect on the next pipeline run "
    "(no restart required)."
)

# ── Load current values ───────────────────────────────────────────────────────
cur = config.as_dict()

with st.form("config_form"):
    st.subheader("🤖 LLM Settings")
    col_m, col_t = st.columns(2)
    with col_m:
        openai_model = st.selectbox(
            "OpenAI Model",
            ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            index=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"].index(
                cur.get("OPENAI_MODEL", "gpt-4o")
            ) if cur.get("OPENAI_MODEL") in ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"] else 0,
            help="Model used for classification, bug analysis, and feature extraction.",
        )
    with col_t:
        temperature = st.slider(
            "Temperature", min_value=0.0, max_value=1.0, step=0.05,
            value=float(cur.get("OPENAI_TEMPERATURE", 0.0)),
            help="Higher = more creative, lower = more deterministic.",
        )

    st.divider()
    st.subheader("🎯 Classification Settings")
    col_c, col_d, col_b = st.columns(3)
    with col_c:
        class_threshold = st.slider(
            "Classification Confidence Threshold",
            min_value=0.5, max_value=1.0, step=0.05,
            value=float(cur.get("CLASSIFICATION_THRESHOLD", 0.7)),
            help="Items below this confidence are flagged as needs_review.",
        )
    with col_d:
        dup_threshold = st.slider(
            "Duplicate Similarity Threshold",
            min_value=0.5, max_value=1.0, step=0.05,
            value=float(cur.get("DUPLICATE_SIMILARITY_THRESHOLD", 0.85)),
            help="ChromaDB cosine similarity above which a ticket is flagged as duplicate.",
        )
    with col_b:
        batch_size = st.number_input(
            "Classifier Batch Size",
            min_value=1, max_value=50, step=1,
            value=int(cur.get("CLASSIFIER_BATCH_SIZE", 10)),
            help="Number of feedback items sent to the LLM per API call.",
        )

    st.divider()
    st.subheader("📁 Directory Paths")
    col_data, col_out = st.columns(2)
    with col_data:
        data_dir = st.text_input(
            "Data Directory (input CSVs)",
            value=cur.get("DATA_DIR", ""),
            help="Path to app_store_reviews.csv and support_emails.csv",
        )
    with col_out:
        output_dir = st.text_input(
            "Output Directory",
            value=cur.get("OUTPUT_DIR", ""),
            help="Where generated_tickets.csv, metrics.csv, and processing_log.csv are written.",
        )

    tech_docs_dir = st.text_input(
        "Tech Docs Directory",
        value=cur.get("TECH_DOCS_DIR", ""),
        help="Root directory scanned for .md/.txt/.rst files to index into ChromaDB.",
    )

    st.divider()
    st.subheader("🗄️ Database")
    chroma_path = st.text_input(
        "ChromaDB Path",
        value=cur.get("CHROMA_PATH", ""),
        help="Directory where ChromaDB stores its SQLite files.",
    )

    st.divider()
    col_save, col_reset = st.columns([1, 1])
    with col_save:
        save_btn = st.form_submit_button("💾 Save Configuration", type="primary")
    with col_reset:
        reset_btn = st.form_submit_button("↩️ Reset to Defaults")

# ── Validate paths ────────────────────────────────────────────────────────────
def _validate(label: str, path: str) -> bool:
    if path and not Path(path).exists():
        st.error(f"⚠️ {label}: path does not exist — `{path}`")
        return False
    return True

# ── Save ──────────────────────────────────────────────────────────────────────
if save_btn:
    valid = all([
        _validate("Data Directory",     data_dir),
        _validate("Output Directory",   output_dir) or not output_dir,
        _validate("Tech Docs Directory",tech_docs_dir) or not tech_docs_dir,
        _validate("ChromaDB Path",      chroma_path) or not chroma_path,
    ])
    if valid:
        updates = {
            "OPENAI_MODEL":                   openai_model,
            "OPENAI_TEMPERATURE":             temperature,
            "CLASSIFICATION_THRESHOLD":       class_threshold,
            "DUPLICATE_SIMILARITY_THRESHOLD": dup_threshold,
            "CLASSIFIER_BATCH_SIZE":          batch_size,
        }
        if data_dir:     updates["DATA_DIR"]     = data_dir
        if output_dir:   updates["OUTPUT_DIR"]   = output_dir
        if tech_docs_dir:updates["TECH_DOCS_DIR"]= tech_docs_dir
        if chroma_path:  updates["CHROMA_PATH"]  = chroma_path

        try:
            config.save_json_config(updates)
            st.success("✅ Configuration saved to `config.json`. Takes effect on next pipeline run.")
        except Exception as exc:
            st.error(f"Failed to save: {exc}")

# ── Reset ─────────────────────────────────────────────────────────────────────
if reset_btn:
    defaults = {
        "OPENAI_MODEL":                   "gpt-4o",
        "OPENAI_TEMPERATURE":             0.0,
        "CLASSIFICATION_THRESHOLD":       0.7,
        "DUPLICATE_SIMILARITY_THRESHOLD": 0.85,
        "CLASSIFIER_BATCH_SIZE":          10,
    }
    try:
        config.save_json_config(defaults)
        st.success("↩️ Configuration reset to defaults.")
        st.rerun()
    except Exception as exc:
        st.error(f"Reset failed: {exc}")

# ── Current config display ────────────────────────────────────────────────────
st.divider()
st.subheader("Current Configuration")
import json
try:
    cfg_file = _ROOT / "config.json"
    if cfg_file.exists():
        with open(cfg_file) as f:
            st.json(json.load(f))
    else:
        st.info("No `config.json` yet — defaults are used from `.env` and code.")
except Exception as exc:
    st.warning(f"Could not read config.json: {exc}")
