"""
ui/pages/2_Run_Pipeline.py
Upload feedback CSVs (optional override), trigger the pipeline, and watch live logs.
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import src.config as config
from ui.utils import load_logs, reload_all

st.set_page_config(page_title="Run Pipeline · FIS", page_icon="▶️", layout="wide")
st.title("▶️ Run Pipeline")

# ── Session state init ────────────────────────────────────────────────────────
if "pipeline_running"    not in st.session_state:
    st.session_state.pipeline_running = False
if "pipeline_result"     not in st.session_state:
    st.session_state.pipeline_result = None
if "pipeline_error"      not in st.session_state:
    st.session_state.pipeline_error = None
if "tmp_data_dir"        not in st.session_state:
    st.session_state.tmp_data_dir = None


# ── File uploaders ────────────────────────────────────────────────────────────
st.subheader("1 · Upload Feedback Files (optional)")
st.markdown(
    "Upload your own CSV files to override the default data. "
    "Leave blank to use the files in `data/input/`."
)

col_r, col_e = st.columns(2)
with col_r:
    reviews_file = st.file_uploader(
        "App Store Reviews (`app_store_reviews.csv`)",
        type=["csv"],
        key="reviews_upload",
    )
with col_e:
    emails_file = st.file_uploader(
        "Support Emails (`support_emails.csv`)",
        type=["csv"],
        key="emails_upload",
    )

# ── Options ───────────────────────────────────────────────────────────────────
st.subheader("2 · Run Options")
dry_run = st.checkbox(
    "Dry-run mode — classify only, no ticket CSV writes",
    value=False,
    help="Useful for testing classification accuracy without creating output files.",
)

st.subheader("3 · Run")

if st.session_state.pipeline_running:
    st.warning("⏳ Pipeline is already running…", icon="⚠️")
    st.button("Run Pipeline", disabled=True)
else:
    run_btn = st.button("▶️ Run Pipeline", type="primary")

    if run_btn:
        # Save uploaded files to a temp directory if provided
        data_dir: str | None = None
        if reviews_file or emails_file:
            tmp_dir = tempfile.mkdtemp()
            st.session_state.tmp_data_dir = tmp_dir
            # Copy uploaded files; fall back to original for missing uploads
            src_dir = config.DATA_DIR
            for fname, fobj in [
                ("app_store_reviews.csv", reviews_file),
                ("support_emails.csv",    emails_file),
            ]:
                dest = os.path.join(tmp_dir, fname)
                if fobj:
                    with open(dest, "wb") as f:
                        f.write(fobj.read())
                else:
                    src_path = os.path.join(src_dir, fname)
                    if os.path.exists(src_path):
                        import shutil
                        shutil.copy(src_path, dest)
            data_dir = tmp_dir

        # Launch pipeline in background thread
        st.session_state.pipeline_running = True
        st.session_state.pipeline_result  = None
        st.session_state.pipeline_error   = None
        reload_all()

        def _run(data_dir=data_dir, dry=dry_run):
            try:
                from src.graph.pipeline import run_pipeline
                result = run_pipeline(data_dir=data_dir, dry_run=dry)
                st.session_state.pipeline_result = result
            except Exception as exc:
                st.session_state.pipeline_error = str(exc)
            finally:
                st.session_state.pipeline_running = False
                reload_all()

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        st.rerun()

# ── Live progress area ────────────────────────────────────────────────────────
progress_area = st.empty()
log_area      = st.empty()
result_area   = st.empty()

if st.session_state.pipeline_running:
    with progress_area.container():
        st.info("⏳ Pipeline running… (auto-refreshes every 5 min)")
        bar = st.progress(0, text="Processing…")
        # Animate progress bar while running
        for pct in range(0, 91, 5):
            if not st.session_state.pipeline_running:
                break
            bar.progress(pct, text=f"Processing… {pct}%")
            time.sleep(0.3)

    with log_area.container():
        st.subheader("Live Processing Log")
        logs = load_logs()
        if not logs.empty:
            st.dataframe(
                logs.tail(20).iloc[::-1][["source_id", "stage", "result", "details", "timestamp"]],
                use_container_width=True,
                hide_index=True,
            )
    time.sleep(300)
    reload_all()
    st.rerun()

elif st.session_state.pipeline_result is not None:
    progress_area.empty()
    with result_area.container():
        result = st.session_state.pipeline_result
        n_tickets = len(result.get("tickets", []))
        n_errors  = len(result.get("errors", []))
        st.success(f"✅ Pipeline complete — **{n_tickets} tickets created**, {n_errors} errors")
        if n_errors:
            with st.expander("Show errors"):
                for e in result.get("errors", []):
                    st.code(e)

        st.subheader("Processing Log")
        reload_all()
        logs = load_logs()
        if not logs.empty:
            st.dataframe(logs.iloc[::-1], use_container_width=True, hide_index=True)

elif st.session_state.pipeline_error:
    progress_area.empty()
    with result_area.container():
        st.error(f"❌ Pipeline failed: {st.session_state.pipeline_error}")

# ── Last run log (always show if exists and not currently running) ─────────────
if not st.session_state.pipeline_running and st.session_state.pipeline_result is None:
    logs = load_logs()
    if not logs.empty:
        st.subheader("Last Run — Processing Log")
        st.dataframe(
            logs.tail(30).iloc[::-1],
            use_container_width=True,
            hide_index=True,
        )
