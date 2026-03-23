"""
ui/pages/1_Dashboard.py
KPI metrics, category donut, source bar chart, and recent tickets table.
"""
from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ui.utils import (
    CATEGORY_COLORS, PRIORITY_COLORS,
    cold_start_banner, load_logs, load_metrics, load_tickets, reload_all,
)

st.set_page_config(page_title="Dashboard · FIS", page_icon="📊", layout="wide")
st.title("📊 Dashboard")

col_refresh, _ = st.columns([1, 8])
with col_refresh:
    if st.button("🔄 Refresh"):
        reload_all()
        st.rerun()

tickets = load_tickets()
metrics = load_metrics()
logs    = load_logs()

# ── Cold-start guard ──────────────────────────────────────────────────────────
if tickets.empty and metrics.empty:
    cold_start_banner()
    st.stop()

# ── KPI row ───────────────────────────────────────────────────────────────────
st.subheader("Key Metrics")
latest = metrics.tail(1).to_dict("records")[0] if not metrics.empty else {}

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Feedback",   latest.get("total_items",    "—"))
k2.metric("Tickets Created",  latest.get("tickets_created","—"))
k3.metric("QC Pass Rate",
          f"{latest.get('qc_pass_rate', '—')}%" if latest.get("qc_pass_rate") else "—")
k4.metric("Avg Latency (ms)", latest.get("avg_latency_ms", "—") or "—")

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
chart_left, chart_right = st.columns(2)

with chart_left:
    st.subheader("Category Breakdown")
    if not tickets.empty and "category" in tickets.columns:
        cat_counts = tickets["category"].value_counts().reset_index()
        cat_counts.columns = ["category", "count"]
        fig = px.pie(
            cat_counts, names="category", values="count", hole=0.45,
            color="category",
            color_discrete_map=CATEGORY_COLORS,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=True,
                          legend=dict(orientation="h"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No ticket data yet.")

with chart_right:
    st.subheader("Source × Category")
    if not tickets.empty and {"source_type", "category"} <= set(tickets.columns):
        cross = (
            tickets.groupby(["source_type", "category"])
            .size()
            .reset_index(name="count")
        )
        fig2 = px.bar(
            cross, x="category", y="count", color="source_type", barmode="group",
            labels={"source_type": "Source", "count": "Items"},
            color_discrete_map={"review": "#3b82f6", "email": "#f97316"},
        )
        fig2.update_layout(margin=dict(t=10, b=10, l=10, r=10),
                           legend=dict(orientation="h"))
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No ticket data yet.")

st.divider()

# ── Priority distribution bar ─────────────────────────────────────────────────
st.subheader("Priority Distribution")
if not tickets.empty and "priority" in tickets.columns:
    prio_order = ["Critical", "High", "Medium", "Low"]
    prio_counts = (
        tickets["priority"]
        .value_counts()
        .reindex(prio_order, fill_value=0)
        .reset_index()
    )
    prio_counts.columns = ["priority", "count"]
    fig3 = px.bar(
        prio_counts, x="priority", y="count",
        color="priority",
        color_discrete_map=PRIORITY_COLORS,
        text="count",
    )
    fig3.update_traces(textposition="outside")
    fig3.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("No ticket data yet.")

st.divider()

# ── Recent tickets ────────────────────────────────────────────────────────────
st.subheader("Recent Tickets (last 20)")
if not tickets.empty:
    display_cols = ["ticket_id", "title", "category", "priority", "status", "created_at"]
    display_cols = [c for c in display_cols if c in tickets.columns]
    recent = tickets.tail(20)[display_cols].iloc[::-1]

    def _style_priority(val):
        color = PRIORITY_COLORS.get(val, "")
        return f"color: {color}; font-weight: bold" if color else ""

    styled = recent.style.map(_style_priority, subset=["priority"]) \
        if "priority" in recent.columns else recent.style
    st.dataframe(styled, use_container_width=True, hide_index=True)
else:
    cold_start_banner("No tickets found. Run the pipeline first.")

# ── Run history ───────────────────────────────────────────────────────────────
if not metrics.empty and len(metrics) > 1:
    st.divider()
    st.subheader("Run History")
    display_m = metrics[["run_id", "timestamp", "total_items", "tickets_created", "qc_pass_rate"]].copy()
    st.dataframe(display_m.iloc[::-1], use_container_width=True, hide_index=True)
