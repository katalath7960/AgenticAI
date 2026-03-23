"""
ui/pages/3_Tickets.py
Browse, filter, search and edit generated tickets.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ui.utils import (
    PRIORITY_COLORS,
    cold_start_banner, load_logs, load_tickets, reload_all, save_tickets,
)

st.set_page_config(page_title="Tickets · FIS", page_icon="🎫", layout="wide")
st.title("🎫 Tickets")

col_r, _ = st.columns([1, 9])
with col_r:
    if st.button("🔄 Refresh"):
        reload_all()
        st.rerun()

tickets = load_tickets()
if tickets.empty:
    cold_start_banner()
    st.stop()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")

    all_cats = ["(All)"] + sorted(tickets["category"].unique().tolist())
    sel_cat  = st.selectbox("Category", all_cats)

    all_prio = ["(All)"] + ["Critical", "High", "Medium", "Low"]
    sel_prio = st.selectbox("Priority", all_prio)

    all_stat = ["(All)"] + sorted(tickets["status"].unique().tolist())
    sel_stat = st.selectbox("Status", all_stat)

    show_dups = st.checkbox("Hide duplicates", value=False)

    keyword = st.text_input("Keyword search (title / description)")

    st.divider()
    if st.button("✅ Approve All Under Review"):
        df = load_tickets()
        df.loc[df["status"] == "needs_review", "status"] = "open"
        save_tickets(df)
        st.success("All 'needs_review' tickets set to 'open'.")
        reload_all()
        st.rerun()

# ── Apply filters ─────────────────────────────────────────────────────────────
df = tickets.copy()
if sel_cat  != "(All)": df = df[df["category"] == sel_cat]
if sel_prio != "(All)": df = df[df["priority"] == sel_prio]
if sel_stat != "(All)": df = df[df["status"]   == sel_stat]
if show_dups:           df = df[df["is_duplicate"] != "True"]
if keyword:
    mask = (
        df["title"].str.contains(keyword, case=False, na=False) |
        df["description"].str.contains(keyword, case=False, na=False)
    )
    df = df[mask]

st.markdown(f"Showing **{len(df)}** of {len(tickets)} tickets")

# ── Export ────────────────────────────────────────────────────────────────────
st.download_button(
    "⬇️ Export filtered CSV",
    data=df.to_csv(index=False).encode(),
    file_name="filtered_tickets.csv",
    mime="text/csv",
)

# ── Ticket table ──────────────────────────────────────────────────────────────
display_cols = ["ticket_id", "title", "category", "priority", "status",
                "assignee_team", "is_duplicate", "created_at"]
display_cols = [c for c in display_cols if c in df.columns]

def _color_priority(val):
    return f"color:{PRIORITY_COLORS.get(val,'')};font-weight:bold"

styled_df = (
    df[display_cols]
    .style.map(_color_priority, subset=["priority"])
    if "priority" in display_cols else df[display_cols].style
)

st.dataframe(styled_df, use_container_width=True, hide_index=True, height=400)

# ── Edit form ─────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Edit Ticket")

ticket_ids = df["ticket_id"].tolist()
if not ticket_ids:
    st.info("No tickets match the current filters.")
else:
    sel_id = st.selectbox("Select ticket to edit", ticket_ids)
    row    = tickets[tickets["ticket_id"] == sel_id].iloc[0].to_dict()

    with st.form("edit_ticket_form"):
        new_title       = st.text_input("Title",       value=row.get("title", ""),       max_chars=80)
        new_description = st.text_area("Description",  value=row.get("description", ""), height=200)
        new_priority    = st.selectbox("Priority",
                                       ["Critical", "High", "Medium", "Low"],
                                       index=["Critical","High","Medium","Low"].index(
                                           row.get("priority","Medium")) if row.get("priority") in
                                           ["Critical","High","Medium","Low"] else 1)
        new_status      = st.selectbox("Status",
                                       ["open", "in_progress", "resolved", "needs_review", "closed"],
                                       index=["open","in_progress","resolved","needs_review","closed"].index(
                                           row.get("status","open")) if row.get("status") in
                                           ["open","in_progress","resolved","needs_review","closed"] else 0)
        submitted = st.form_submit_button("💾 Save Changes")

    if submitted:
        all_df = load_tickets()
        idx = all_df.index[all_df["ticket_id"] == sel_id]
        if len(idx):
            all_df.loc[idx, "title"]       = new_title
            all_df.loc[idx, "description"] = new_description
            all_df.loc[idx, "priority"]    = new_priority
            all_df.loc[idx, "status"]      = new_status
            save_tickets(all_df)
            st.success(f"✅ Ticket {sel_id} updated.")
            reload_all()
            st.rerun()

    # ── Duplicate badge ───────────────────────────────────────────────────────
    if row.get("is_duplicate") == "True":
        dup_of = row.get("duplicate_of", "")
        st.warning(
            f"⚠️ This ticket is marked as a **duplicate** of `{dup_of}`.",
            icon="🔁",
        )
