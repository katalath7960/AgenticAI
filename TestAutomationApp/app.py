"""
AI-Powered Test Automation Suite — Streamlit Application
Run: streamlit run app.py
"""
import html
import queue
import shutil
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

# ─── Page configuration ───────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Test Automation Suite",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* Global */
[data-testid="stAppViewContainer"] { background: #F0F4F8; }
[data-testid="stSidebar"] { background: #1A2E4A; }
[data-testid="stSidebar"] * { color: #E8EEF4 !important; }
[data-testid="stSidebar"] input { background: #253B56 !important; border: 1px solid #3A5472 !important; color: #FFF !important; }
[data-testid="stSidebar"] select { background: #253B56 !important; color: #FFF !important; }
[data-testid="stSidebar"] label { color: #A8C0D6 !important; font-size: 12px !important; }

/* Header */
.app-header {
    background: linear-gradient(135deg, #1A2E4A 0%, #2E6DA4 100%);
    color: white; padding: 24px 32px; border-radius: 12px;
    margin-bottom: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.app-header h1 { font-size: 28px; font-weight: 700; margin: 0; letter-spacing: -0.5px; }
.app-header p  { margin: 6px 0 0; opacity: 0.8; font-size: 14px; }

/* Cards */
.card {
    background: white; border-radius: 10px; padding: 20px 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 16px;
    border-left: 4px solid #2E6DA4;
}
.card h3 { font-size: 14px; color: #666; margin: 0 0 4px; font-weight: 600; text-transform: uppercase; letter-spacing: .4px; }
.card .value { font-size: 36px; font-weight: 700; color: #1A2E4A; }

/* Metric cards */
.metric-pass  { border-left-color: #1E8A44 !important; }
.metric-fail  { border-left-color: #C0392B !important; }
.metric-skip  { border-left-color: #D68910 !important; }
.metric-total { border-left-color: #2E6DA4 !important; }
.metric-pass .value  { color: #1E8A44; }
.metric-fail .value  { color: #C0392B; }
.metric-skip .value  { color: #D68910; }

/* Badges */
.badge { display: inline-block; padding: 3px 12px; border-radius: 12px; font-size: 12px; font-weight: 700; }
.badge-pass { background: #D5F5E3; color: #1E8A44; }
.badge-fail { background: #FDE8E8; color: #C0392B; }
.badge-skip { background: #FEF9E7; color: #D68910; }
.badge-notrun { background: #EEE; color: #666; }

/* Step log */
.log-container {
    background: #0D1117; color: #E6EDF3; border-radius: 8px;
    padding: 14px 16px; font-family: 'Consolas','Courier New',monospace;
    font-size: 12px; height: 320px; overflow-y: auto;
    border: 1px solid #30363D;
}
.log-info    { color: #79C0FF; }
.log-success { color: #56D364; }
.log-error   { color: #F85149; }
.log-warning { color: #E3B341; }
.log-step    { color: #D2A8FF; }
.log-done    { color: #56D364; font-weight: bold; }

/* Upload area */
.upload-hint {
    text-align: center; padding: 32px; border: 2px dashed #BCC8D8;
    border-radius: 10px; color: #7A90A4; background: #F8FAFC;
}

/* Section label */
.section-label {
    font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1px; color: #7A90A4; margin-bottom: 8px;
}

/* Table tweaks */
[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }

/* Progress bar */
.stProgress > div > div { background: #2E6DA4; border-radius: 4px; }

/* Sidebar section labels */
.sidebar-section {
    font-size: 10px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1px; color: #5A7A96 !important; margin: 16px 0 4px;
    border-bottom: 1px solid #2A3F58; padding-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)


# ─── Session state initialization ─────────────────────────────────────────────

def _init_state():
    defaults = {
        "phase": "upload",           # upload | running | complete
        "test_cases": None,
        "excel_path": None,          # path to temp Excel file
        "original_filename": "",
        "progress_q": None,
        "result_holder": {},
        "thread": None,
        "log_messages": [],
        "progress_pct": 0.0,
        "current_tc": "",
        "results": None,
        "exec_error": None,
        "run_start": None,
        "run_end": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ─── Sidebar — configuration ──────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("## 🤖 Test Automation")
        st.markdown("---")

        st.markdown('<p class="sidebar-section">Target Application</p>', unsafe_allow_html=True)
        url = st.text_input("Application URL", value="https://qafjdforum.courts.phila.gov/",
                            placeholder="https://your-app.com")

        st.markdown('<p class="sidebar-section">Credentials</p>', unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")

        st.markdown('<p class="sidebar-section">Browser Settings</p>', unsafe_allow_html=True)
        browser_label = st.selectbox(
            "Browser", ["Chrome (Chromium)", "Firefox", "WebKit (Safari-engine)"]
        )
        browser_map = {
            "Chrome (Chromium)": "chromium",
            "Firefox": "firefox",
            "WebKit (Safari-engine)": "webkit",
        }
        browser_type = browser_map[browser_label]
        headless = st.checkbox("Headless Mode", value=False,
                               help="Run browser without visible window")
        timeout = st.slider("Element Timeout (s)", 10, 60, 30)

        st.markdown('<p class="sidebar-section">Execution Options</p>', unsafe_allow_html=True)
        ss_on_fail = st.checkbox("Screenshot on Failure", value=True)
        ss_on_pass = st.checkbox("Screenshot on Pass", value=False)
        continue_on_fail = st.checkbox("Continue on Failure", value=True,
                                       help="Don't stop after a single test failure")

        st.markdown('<p class="sidebar-section">AI Settings (Optional)</p>', unsafe_allow_html=True)
        ai_key = st.text_input("Anthropic API Key", type="password",
                               placeholder="sk-ant-... (optional)")
        if ai_key:
            st.success("AI step interpretation enabled", icon="🧠")

        st.markdown("---")
        st.markdown(
            '<p style="font-size:10px;color:#4A6A86;text-align:center">'
            'AI-Powered Test Automation Suite<br/>Powered by Playwright + Claude</p>',
            unsafe_allow_html=True,
        )

    return {
        "url": url, "username": username, "password": password,
        "browser_type": browser_type, "headless": headless,
        "timeout_ms": timeout * 1000,
        "ss_on_fail": ss_on_fail, "ss_on_pass": ss_on_pass,
        "continue_on_failure": continue_on_fail,
        "ai_api_key": ai_key,
    }


# ─── Header ───────────────────────────────────────────────────────────────────

def render_header():
    st.markdown("""
    <div class="app-header">
        <h1>🤖 AI-Powered Test Automation Suite</h1>
        <p>Upload an Excel test case file → Configure → Execute → Download results</p>
    </div>
    """, unsafe_allow_html=True)


# ─── Upload phase ─────────────────────────────────────────────────────────────

def render_upload(cfg: dict):
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<p class="section-label">📂 Step 1 — Upload Test Cases</p>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Upload Excel file (.xlsx)",
            type=["xlsx"],
            help="Your Excel file should have columns: TC_ID, Test Case Name, Steps, Expected Result",
        )

        if uploaded:
            _handle_upload(uploaded)

        if st.session_state.test_cases is None:
            st.markdown("""
            <div class="upload-hint">
                <p style="font-size:32px;margin:0">📊</p>
                <p style="font-size:16px;font-weight:600;margin:8px 0 4px">Drop your Excel file here</p>
                <p style="font-size:13px">Columns needed: TC_ID · Test Case Name · Steps · Expected Result</p>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown('<p class="section-label">⚙️ Step 2 — Configuration Preview</p>', unsafe_allow_html=True)
        if cfg["url"]:
            st.info(f"🌐 **URL:** {cfg['url']}")
        st.info(f"🖥️ **Browser:** {cfg['browser_type'].title()} ({'Headless' if cfg['headless'] else 'Visible'})")
        st.info(f"⏱️ **Timeout:** {cfg['timeout_ms'] // 1000}s")
        if cfg["username"]:
            st.success(f"👤 **Credentials:** {cfg['username']} / {'●' * len(cfg['password'])}")
        else:
            st.warning("⚠️ Username not configured — set in sidebar")
        if cfg["ai_api_key"]:
            st.success("🧠 **AI Step Interpreter:** Enabled")

    # Test case preview
    if st.session_state.test_cases:
        tcs = st.session_state.test_cases
        st.markdown("---")
        st.markdown(f'<p class="section-label">📋 Test Cases Loaded — {len(tcs)} total</p>', unsafe_allow_html=True)
        preview_data = [{
            "TC ID": tc.tc_id,
            "Test Case Name": tc.test_case_name,
            "Steps": tc.steps[:80] + ("…" if len(tc.steps) > 80 else ""),
            "Expected Result": tc.expected_result[:60] + ("…" if len(tc.expected_result) > 60 else ""),
        } for tc in tcs[:50]]
        st.dataframe(pd.DataFrame(preview_data), use_container_width=True, height=260)
        if len(tcs) > 50:
            st.caption(f"Showing first 50 of {len(tcs)} test cases")

        st.markdown("---")
        st.markdown('<p class="section-label">🚀 Step 3 — Start Execution</p>', unsafe_allow_html=True)

        col_btn, col_warn = st.columns([1, 2])
        with col_btn:
            ready = bool(cfg["url"] and cfg["username"] and cfg["password"])
            if st.button(
                "▶ Start Testing",
                type="primary",
                disabled=not ready,
                use_container_width=True,
            ):
                _start_execution(cfg)

        with col_warn:
            if not ready:
                st.warning("Fill in URL, Username and Password in the sidebar to begin.")


def _handle_upload(uploaded):
    """Save uploaded file to a temp path and parse test cases."""
    try:
        # Clean up previous temp file
        if st.session_state.excel_path and Path(st.session_state.excel_path).exists():
            try:
                Path(st.session_state.excel_path).unlink()
            except Exception:
                pass

        # Write to temp file
        suffix = Path(uploaded.name).suffix
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(uploaded.read())
        tmp.flush()
        tmp.close()

        st.session_state.excel_path = tmp.name
        st.session_state.original_filename = uploaded.name

        from excel.excel_reader import read_workbook
        tcs = read_workbook(tmp.name)
        st.session_state.test_cases = tcs
        st.session_state.phase = "upload"
        st.session_state.results = None

        st.success(f"✅ Loaded **{len(tcs)}** test cases from **{uploaded.name}**")
    except Exception as e:
        st.error(f"Failed to read Excel file: {e}")


def _start_execution(cfg: dict):
    """Kick off the background test execution thread."""
    import copy
    from automation.test_executor import run_in_thread

    test_cases = copy.deepcopy(st.session_state.test_cases)
    excel_path = st.session_state.excel_path
    ss_folder = str(Path("screenshots") / datetime.now().strftime("%Y%m%d_%H%M%S"))

    progress_q: queue.Queue = queue.Queue()
    result_holder: dict = {}

    thread = threading.Thread(
        target=run_in_thread,
        kwargs=dict(
            test_cases=test_cases,
            url=cfg["url"],
            username=cfg["username"],
            password=cfg["password"],
            browser_type=cfg["browser_type"],
            headless=cfg["headless"],
            timeout_ms=cfg["timeout_ms"],
            screenshot_on_fail=cfg["ss_on_fail"],
            screenshot_on_pass=cfg["ss_on_pass"],
            continue_on_failure=cfg["continue_on_failure"],
            ai_api_key=cfg["ai_api_key"],
            screenshot_folder=ss_folder,
            progress_q=progress_q,
            result_holder=result_holder,
        ),
        daemon=True,
    )

    st.session_state.progress_q = progress_q
    st.session_state.result_holder = result_holder
    st.session_state.thread = thread
    st.session_state.log_messages = []
    st.session_state.progress_pct = 0.0
    st.session_state.current_tc = ""
    st.session_state.run_start = datetime.now()
    st.session_state.phase = "running"

    thread.start()
    st.rerun()


# ─── Running phase ────────────────────────────────────────────────────────────

def render_running():
    st.markdown('<p class="section-label">⚡ Execution in Progress</p>', unsafe_allow_html=True)

    # Drain queue
    pq: queue.Queue = st.session_state.progress_q
    while not pq.empty():
        try:
            msg = pq.get_nowait()
        except queue.Empty:
            break

        mtype = msg.get("type", "log")
        ts = msg.get("ts", "")
        text = msg.get("message", "")

        if mtype == "done":
            st.session_state.phase = "complete"
            st.session_state.run_end = datetime.now()
            # Get results from holder
            rh = st.session_state.result_holder
            st.session_state.results = rh.get("results", st.session_state.test_cases)
            st.session_state.exec_error = rh.get("error")
            # Write results to Excel
            _write_excel_results()
            st.rerun()
            return

        level = msg.get("level", "INFO")
        if mtype in ("tc_start", "tc_done"):
            css = "log-step"
            st.session_state.current_tc = text
            st.session_state.progress_pct = msg.get("progress", st.session_state.progress_pct)
        elif mtype == "step_result":
            css = "log-success" if level == "SUCCESS" else "log-error"
        elif level == "ERROR":
            css = "log-error"
        elif level == "SUCCESS":
            css = "log-success"
        elif level == "WARNING":
            css = "log-warning"
        else:
            css = "log-info"

        # html.escape prevents Playwright's multiline error output (with < > & box chars)
        # from breaking the log panel. Newlines become <br/> so each traceback line shows.
        safe_text = html.escape(text).replace("\n", "<br/>")
        st.session_state.log_messages.append(
            f'<span class="{css}">[{ts}] {safe_text}</span>'
        )

    # Check if thread died unexpectedly
    thread: threading.Thread = st.session_state.thread
    if thread and not thread.is_alive() and st.session_state.phase == "running":
        st.session_state.phase = "complete"
        st.session_state.run_end = datetime.now()
        rh = st.session_state.result_holder
        st.session_state.results = rh.get("results", st.session_state.test_cases)
        st.session_state.exec_error = rh.get("error")
        _write_excel_results()
        st.rerun()
        return

    # Render progress UI
    pct = st.session_state.progress_pct
    st.progress(pct, text=f"Progress: {int(pct * 100)}%")

    if st.session_state.current_tc:
        st.info(f"⚡ {st.session_state.current_tc}")

    # Log area
    log_html = "<br/>".join(st.session_state.log_messages[-80:])
    placeholder = '<span class="log-info">Waiting for browser to launch...</span>'
    st.markdown(
        f'<div class="log-container">{log_html or placeholder}</div>',
        unsafe_allow_html=True,
    )

    # Stop button
    if st.button("⏹ Stop Execution", type="secondary"):
        st.session_state.phase = "complete"
        st.session_state.run_end = datetime.now()
        rh = st.session_state.result_holder
        st.session_state.results = rh.get("results", st.session_state.test_cases)
        _write_excel_results()
        st.rerun()
        return

    # Auto-refresh
    time.sleep(0.4)
    st.rerun()


def _write_excel_results():
    """Write execution results back into the Excel file."""
    results = st.session_state.results
    excel_path = st.session_state.excel_path
    if not results or not excel_path:
        return
    try:
        from excel.excel_writer import write_results
        write_results(excel_path, results)
    except Exception as e:
        st.session_state.exec_error = (st.session_state.exec_error or "") + f"\nExcel write error: {e}"


# ─── Complete phase — Dashboard ───────────────────────────────────────────────

def render_complete():
    results = st.session_state.results or []
    error = st.session_state.exec_error

    if error:
        st.error(f"⚠️ Execution error: {error}")

    total   = len(results)
    passed  = sum(1 for t in results if t.status == "PASS")
    failed  = sum(1 for t in results if t.status == "FAIL")
    skipped = sum(1 for t in results if t.status in ("SKIP", "NOT RUN"))
    pass_pct = round(passed / total * 100, 1) if total else 0.0

    elapsed = ""
    if st.session_state.run_start and st.session_state.run_end:
        delta = st.session_state.run_end - st.session_state.run_start
        secs = int(delta.total_seconds())
        elapsed = f"{secs // 60}m {secs % 60}s"

    # ── Summary cards ──
    st.markdown('<p class="section-label">📊 Execution Summary</p>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    for col, label, value, css in [
        (c1, "Total",    total,    "metric-total"),
        (c2, "Passed",   passed,   "metric-pass"),
        (c3, "Failed",   failed,   "metric-fail"),
        (c4, "Skipped",  skipped,  "metric-skip"),
        (c5, "Pass Rate", f"{pass_pct}%", "metric-total"),
        (c6, "Duration", elapsed or "—", "metric-total"),
    ]:
        col.markdown(
            f'<div class="card {css}"><h3>{label}</h3><div class="value">{value}</div></div>',
            unsafe_allow_html=True,
        )

    # ── Progress bar ──
    if total > 0:
        st.progress(passed / total, text=f"Pass rate: {pass_pct}%")

    st.markdown("---")

    # ── Results table ──
    st.markdown('<p class="section-label">📋 Detailed Results</p>', unsafe_allow_html=True)

    if results:
        df = pd.DataFrame([{
            "TC ID": t.tc_id,
            "Test Case": t.test_case_name,
            "Status": t.status,
            "Actual Result": (t.actual_result or "")[:120],
            "Error": (t.error_details or "")[:100],
            "Screenshot": "📷" if t.screenshot else "",
            "Time": t.execution_time,
            "Executed": t.executed_date,
        } for t in results])

        def _style_status(val):
            colors = {"PASS": "#D5F5E3", "FAIL": "#FDE8E8", "SKIP": "#FEF9E7"}
            return f"background-color: {colors.get(val, '#EEE')}"

        styled = df.style.applymap(_style_status, subset=["Status"])
        st.dataframe(styled, use_container_width=True, height=400)

    # ── Failed test details ──
    failed_cases = [t for t in results if t.status == "FAIL"]
    if failed_cases:
        st.markdown("---")
        st.markdown(f'<p class="section-label">❌ Failed Tests ({len(failed_cases)})</p>', unsafe_allow_html=True)
        for tc in failed_cases:
            with st.expander(f"❌ {tc.tc_id} — {tc.test_case_name}", expanded=False):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**Steps:**")
                    st.text(tc.steps)
                    st.markdown("**Expected:**")
                    st.text(tc.expected_result)
                with col_b:
                    st.markdown("**Error Details:**")
                    st.error(tc.error_details or "No error details captured")
                    if tc.screenshot and Path(tc.screenshot).exists():
                        st.image(tc.screenshot, caption="Failure Screenshot", use_column_width=True)

    # ── Log replay ──
    if st.session_state.log_messages:
        with st.expander("📜 Execution Log", expanded=False):
            log_html = "<br/>".join(st.session_state.log_messages)
            st.markdown(
                f'<div class="log-container" style="height:400px">{log_html}</div>',
                unsafe_allow_html=True,
            )

    # ── Download section ──
    st.markdown("---")
    st.markdown('<p class="section-label">⬇️ Download Results</p>', unsafe_allow_html=True)
    _render_download()

    # ── Run again ──
    st.markdown("---")
    if st.button("🔄 Run Again with New File", use_container_width=True):
        _reset_session()
        st.rerun()


def _render_download():
    excel_path = st.session_state.excel_path
    orig_name = st.session_state.original_filename or "test_results.xlsx"
    out_name = Path(orig_name).stem + "_results.xlsx"

    col1, col2 = st.columns(2)

    with col1:
        if excel_path and Path(excel_path).exists():
            with open(excel_path, "rb") as f:
                data = f.read()
            st.download_button(
                label="📥 Download Updated Excel",
                data=data,
                file_name=out_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )
            st.caption("Updated Excel with Execution Status, Actual Results, Error Details, Screenshots, and Timestamps")
        else:
            st.warning("Updated Excel file not available")

    with col2:
        # JSON summary download
        if st.session_state.results:
            import json
            summary = {
                "run_date": st.session_state.run_start.isoformat() if st.session_state.run_start else "",
                "total": len(st.session_state.results),
                "passed": sum(1 for t in st.session_state.results if t.status == "PASS"),
                "failed": sum(1 for t in st.session_state.results if t.status == "FAIL"),
                "results": [
                    {
                        "tc_id": t.tc_id,
                        "name": t.test_case_name,
                        "status": t.status,
                        "actual": t.actual_result,
                        "error": t.error_details,
                        "time": t.execution_time,
                        "date": t.executed_date,
                    }
                    for t in st.session_state.results
                ],
            }
            st.download_button(
                label="📄 Download JSON Report",
                data=json.dumps(summary, indent=2),
                file_name=f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )


def _reset_session():
    """Reset to initial state for a new run."""
    # Clean up temp file
    if st.session_state.excel_path:
        try:
            Path(st.session_state.excel_path).unlink(missing_ok=True)
        except Exception:
            pass
    # Reset all keys
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    _init_state()


# ─── About tab / helper ───────────────────────────────────────────────────────

def render_about():
    with st.expander("ℹ️ About & Supported Step Formats", expanded=False):
        st.markdown("""
**Supported Natural Language Test Steps:**

| Category | Example Steps |
|---|---|
| Authentication | `Login with valid username and password` · `Logout from the application` |
| Navigation | `Click menu Case Search` · `Click the Dashboard link` |
| Text Entry | `Enter text 'John' in the First Name field` |
| Dropdown | `Select 'Active' from the Status dropdown` |
| Checkbox | `Check the Terms and Conditions checkbox` |
| Validation | `Validate page title contains 'Dashboard'` |
| Validation | `Validate error message is displayed` |
| Validation | `Validate URL contains 'dashboard'` |
| Search | `Search for 'TEST-001'` |
| CRUD | `Add new record` · `Edit record` · `Delete record` · `Save` · `Cancel` |

**Excel Column Names (flexible — any of these are accepted):**
- TC ID: `TC_ID`, `ID`, `Test ID`, `No`
- Test Case Name: `Test Case Name`, `Test Case`, `Scenario`, `Title`
- Steps: `Steps`, `Action`, `Test Steps`, `Procedure`
- Expected Result: `Expected Result`, `Expected`, `Expected Outcome`

**Multi-step test cases:** Put each step on a new line within the Steps cell.
        """)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    cfg = render_sidebar()
    render_header()
    render_about()

    phase = st.session_state.phase

    if phase == "upload":
        render_upload(cfg)

    elif phase == "running":
        render_running()

    elif phase == "complete":
        render_complete()


if __name__ == "__main__":
    main()
