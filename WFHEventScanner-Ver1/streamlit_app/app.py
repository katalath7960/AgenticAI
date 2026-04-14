"""Streamlit admin dashboard — talks to the FastAPI backend."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")


def call_api(path: str, method: str = "GET", **kwargs):
    url = f"{API_BASE}{path}"
    r = requests.request(method, url, timeout=10, **kwargs)
    r.raise_for_status()
    if r.headers.get("content-type", "").startswith("application/json"):
        return r.json()
    return r.content


st.set_page_config(page_title="WFH Event Admin", layout="wide")

page = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Attendees", "Run Agent", "Scan Log"],
)

st.sidebar.caption(f"API: {API_BASE}")


# ------------------------------------------------------------------ Dashboard
def dashboard():
    st.title("Dashboard")
    try:
        stats = call_api("/api/stats")
    except Exception as exc:
        st.error(f"API unreachable: {exc}")
        return

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total", stats["total"])
    c2.metric("Pending", stats["pending"])
    c3.metric("Sent", stats["sent"])
    c4.metric("Checked in", stats["checked_in"])
    c5.metric("Scans today", stats["scans_today"])

    st.subheader("By color")
    try:
        attendees = call_api("/api/attendees", params={"limit": 1000})
        if attendees:
            df = pd.DataFrame(attendees)
            counts = df.groupby("color").size().rename("count")
            st.bar_chart(counts)
    except Exception as exc:
        st.warning(f"couldn't load attendees: {exc}")

    st.subheader("Recent scans")
    try:
        scans = call_api("/api/scans", params={"limit": 10})
        if scans:
            st.dataframe(pd.DataFrame(scans), use_container_width=True)
        else:
            st.info("no scans yet")
    except Exception as exc:
        st.warning(f"couldn't load scans: {exc}")


# ------------------------------------------------------------------- Attendees
def attendees_page():
    st.title("Attendees")
    col_status, col_search = st.columns([1, 3])
    status_filter = col_status.selectbox("Status", ["All", "Pending", "Sent", "CheckedIn"])
    search = col_search.text_input("Search email / name")

    try:
        params = {"limit": 1000}
        if status_filter != "All":
            params["status"] = status_filter
        data = call_api("/api/attendees", params=params)
    except Exception as exc:
        st.error(f"load failed: {exc}"); return

    df = pd.DataFrame(data)
    if search:
        mask = df.apply(lambda r: search.lower() in str(r.get("email", "")).lower()
                                  or search.lower() in f"{r.get('first_name','')} {r.get('last_name','')}".lower(),
                         axis=1)
        df = df[mask]

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Resend invite")
    if len(df):
        target = st.selectbox("Attendee", df.apply(lambda r: f"{r['id']} — {r['email']}", axis=1).tolist())
        if st.button("Resend now"):
            att_id = int(target.split(" — ")[0])
            try:
                res = call_api(f"/api/attendees/{att_id}/resend", method="POST")
                st.success(f"sent: {res}")
            except Exception as exc:
                st.error(f"resend failed: {exc}")


# ------------------------------------------------------------------- Run Agent
def run_agent_page():
    st.title("Run Agent")
    st.caption("Kicks off the full pipeline: CSV import → barcodes → emails → processed roster export.")

    if "run_id" not in st.session_state:
        st.session_state.run_id = None

    if st.button("Run Agent Now", type="primary", disabled=st.session_state.run_id is not None):
        try:
            res = call_api("/api/agent/run", method="POST")
            st.session_state.run_id = res["run_id"]
            st.rerun()
        except Exception as exc:
            st.error(f"failed to start: {exc}")

    if st.session_state.run_id:
        st.info(f"run_id: {st.session_state.run_id}")
        progress = st.progress(0, text="running…")
        status_area = st.empty()
        for i in range(120):
            try:
                run = call_api(f"/api/agent/runs/{st.session_state.run_id}")
            except Exception as exc:
                status_area.error(f"poll failed: {exc}"); break
            status_area.json(run)
            if run["status"] in ("completed", "failed"):
                progress.progress(100, text=run["status"])
                break
            state = run.get("state") or {}
            approx = min(
                95,
                (state.get("imported", 0) > 0) * 30
                + (state.get("barcodes_generated", 0) > 0) * 30
                + (state.get("emails_sent", 0) > 0) * 30,
            )
            progress.progress(approx, text=run["status"])
            time.sleep(2)

        if st.button("Clear"):
            st.session_state.run_id = None
            st.rerun()


# -------------------------------------------------------------------- Scan Log
def scan_log_page():
    st.title("Scan Log")
    limit = st.slider("Rows", 20, 500, 100, 20)
    try:
        scans = call_api("/api/scans", params={"limit": limit})
    except Exception as exc:
        st.error(f"load failed: {exc}"); return
    if not scans:
        st.info("no scans yet"); return
    st.dataframe(pd.DataFrame(scans), use_container_width=True, hide_index=True)


pages = {
    "Dashboard": dashboard,
    "Attendees": attendees_page,
    "Run Agent": run_agent_page,
    "Scan Log": scan_log_page,
}
pages[page]()
