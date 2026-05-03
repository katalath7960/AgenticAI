"""Streamlit UI for the Automated Testing pipeline."""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import threading

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.logging import setup_logging
from config.settings import OutputFormat, Settings
from pipeline import run_pipeline

setup_logging()

st.set_page_config(page_title="AutoTester", layout="wide")
st.title("AutoTester — Automated Test Case Generator")

def _run_in_proactor(coro_factory):
    """Run an async coroutine in a dedicated thread with a ProactorEventLoop."""
    result_box = {}

    def runner():
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        try:
            result_box["value"] = loop.run_until_complete(coro_factory())
        except BaseException as e:
            result_box["error"] = e
        finally:
            loop.close()

    t = threading.Thread(target=runner)
    t.start()
    t.join()

    if "error" in result_box:
        raise result_box["error"]
    return result_box["value"]

with st.sidebar:
    st.header("Configuration")
    url = st.text_input("Target URL", placeholder="https://example.com")
    depth = st.slider("Max crawl depth", 1, 10, 3)
    rate_limit = st.slider("Rate limit (req/s)", 0.5, 10.0, 2.0, 0.5)
    headless = st.checkbox("Headless browser", value=True)
    security = st.checkbox("Include security tests", value=False)
    gen_scripts = st.checkbox("Generate automation scripts", value=True)
    fmt = st.selectbox("Output format", ["json", "csv", "excel", "html"])
    output_dir = st.text_input("Output directory", value="output")

    run_btn = st.button("Run Pipeline", type="primary", disabled=not url.strip())

if run_btn and url.strip():
    settings = Settings(
        target_url=url.strip(),
        max_depth=depth,
        rate_limit_rps=rate_limit,
        headless=headless,
        run_security_tests=security,
        generate_scripts=gen_scripts,
        output_format=OutputFormat(fmt),
        output_dir=output_dir,
    )

    with st.status("Running pipeline...", expanded=True) as status:
        st.write("Crawling website...")
        results = _run_in_proactor(lambda: run_pipeline(settings))

        status.update(label="Pipeline complete!", state="complete")

    st.success(f"Generated **{results['test_cases']}** test cases across **{results['pages_crawled']}** pages")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pages", results["pages_crawled"])
    c2.metric("Forms", results["total_forms"])
    c3.metric("API Endpoints", results["total_api_endpoints"])
    c4.metric("Broken Links", results["broken_links"])

    st.subheader("Test Case Breakdown")
    summary = results["summary"]
    cols = st.columns(len(summary))
    for col, (cat, count) in zip(cols, summary.items()):
        col.metric(cat, count)

    json_path = Path(output_dir) / "test_cases.json"
    if json_path.exists():
        data = json.loads(json_path.read_text(encoding="utf-8"))
        df = pd.json_normalize(data["test_cases"])
        st.subheader("Test Cases")

        cat_filter = st.multiselect("Filter by category", options=list(summary.keys()), default=list(summary.keys()))
        filtered = df[df["category"].isin(cat_filter)]
        st.dataframe(filtered, use_container_width=True, hide_index=True)

        csv_data = filtered.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv_data, "test_cases.csv", "text/csv")

    report_path = Path(output_dir) / "report.html"
    if report_path.exists():
        st.subheader("HTML Report")
        st.download_button(
            "Download HTML Report",
            report_path.read_bytes(),
            "report.html",
            "text/html",
        )

    if results.get("ui_changes"):
        st.subheader("UI Changes Detected")
        st.json(results["ui_changes"])

    st.subheader("Output Files")
    for o in results["outputs"]:
        st.text(f"  {o}")
elif not url.strip():
    st.info("Enter a target URL in the sidebar and click **Run Pipeline** to begin.")

