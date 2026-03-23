"""
ui/pages/5_Analytics.py
Trend charts, classification accuracy, and feature demand analysis.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import src.config as config
from ui.utils import CATEGORY_COLORS, cold_start_banner, load_metrics, load_tickets, reload_all

st.set_page_config(page_title="Analytics · FIS", page_icon="📈", layout="wide")
st.title("📈 Analytics")

col_r, _ = st.columns([1, 9])
with col_r:
    if st.button("🔄 Refresh"):
        reload_all()
        st.rerun()

tickets = load_tickets()
metrics = load_metrics()

if tickets.empty and metrics.empty:
    cold_start_banner()
    st.stop()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_trends, tab_accuracy, tab_features, tab_latency = st.tabs(
    ["📉 Trends", "🎯 Accuracy", "⭐ Feature Demand", "⏱️ Latency"]
)

# ── Trends ────────────────────────────────────────────────────────────────────
with tab_trends:
    st.subheader("Tickets Created per Run")
    if not metrics.empty and "timestamp" in metrics.columns and "tickets_created" in metrics.columns:
        mdf = metrics.copy()
        mdf["tickets_created"] = pd.to_numeric(mdf["tickets_created"], errors="coerce").fillna(0)
        mdf["run_label"] = mdf["timestamp"].str[:16]
        fig = px.line(mdf, x="run_label", y="tickets_created", markers=True,
                      labels={"run_label": "Run Time", "tickets_created": "Tickets"})
        fig.update_layout(margin=dict(t=10, b=50))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Need at least one pipeline run.")

    st.subheader("Category Mix over Runs")
    if not metrics.empty:
        cat_cols = ["bugs", "features", "praise", "complaints", "spam"]
        avail = [c for c in cat_cols if c in metrics.columns]
        if avail:
            mdf2 = metrics.copy()
            mdf2["run_label"] = mdf2["timestamp"].str[:16]
            for c in avail:
                mdf2[c] = pd.to_numeric(mdf2[c], errors="coerce").fillna(0)
            melted = mdf2[["run_label"] + avail].melt(
                id_vars="run_label", var_name="category", value_name="count"
            )
            color_map = {
                "bugs": CATEGORY_COLORS["Bug"],
                "features": CATEGORY_COLORS["Feature Request"],
                "praise": CATEGORY_COLORS["Praise"],
                "complaints": CATEGORY_COLORS["Complaint"],
                "spam": CATEGORY_COLORS["Spam"],
            }
            fig2 = px.bar(melted, x="run_label", y="count", color="category",
                          barmode="stack", color_discrete_map=color_map,
                          labels={"run_label": "Run", "count": "Items"})
            fig2.update_layout(margin=dict(t=10, b=50))
            st.plotly_chart(fig2, use_container_width=True)

    st.subheader("QC Pass Rate over Runs")
    if not metrics.empty and "qc_pass_rate" in metrics.columns:
        mdf3 = metrics.copy()
        mdf3["qc_pass_rate"] = pd.to_numeric(mdf3["qc_pass_rate"], errors="coerce")
        mdf3["run_label"] = mdf3["timestamp"].str[:16]
        fig3 = px.line(mdf3, x="run_label", y="qc_pass_rate", markers=True,
                       labels={"run_label": "Run", "qc_pass_rate": "Pass Rate %"},
                       range_y=[0, 105])
        fig3.add_hline(y=95, line_dash="dash", line_color="green",
                       annotation_text="95% target")
        fig3.update_layout(margin=dict(t=10, b=50))
        st.plotly_chart(fig3, use_container_width=True)

# ── Accuracy vs expected classifications ─────────────────────────────────────
with tab_accuracy:
    st.subheader("Classification Accuracy vs Expected")
    import os
    expected_path = os.path.join(config.DATA_DIR, "expected_classifications.csv")
    if not os.path.exists(expected_path):
        st.info(
            "No `expected_classifications.csv` found in the data directory. "
            "This file is required for accuracy analysis.",
            icon="ℹ️",
        )
    elif tickets.empty:
        cold_start_banner("Run the pipeline to generate ticket data first.")
    else:
        try:
            expected = pd.read_csv(expected_path, dtype=str).fillna("")
            # Match on source_id / review_id
            if "review_id" in expected.columns and "category" in expected.columns:
                expected = expected.rename(columns={"review_id": "source_id",
                                                     "category": "expected_category"})
            merged = tickets.merge(
                expected[["source_id", "expected_category"]],
                on="source_id", how="inner"
            )
            if merged.empty:
                st.warning("No matching source IDs between tickets and expected classifications.")
            else:
                merged["correct"] = merged["category"] == merged["expected_category"]
                overall = merged["correct"].mean() * 100

                col_acc, col_n = st.columns(2)
                col_acc.metric("Overall Accuracy", f"{overall:.1f}%")
                col_n.metric("Matched Items", len(merged))

                per_cat = (
                    merged.groupby("expected_category")["correct"]
                    .mean()
                    .mul(100)
                    .reset_index()
                )
                per_cat.columns = ["category", "accuracy_pct"]
                fig_acc = px.bar(
                    per_cat, x="category", y="accuracy_pct",
                    color="category", color_discrete_map=CATEGORY_COLORS,
                    text=per_cat["accuracy_pct"].round(1).astype(str) + "%",
                    labels={"accuracy_pct": "Accuracy %"},
                    range_y=[0, 110],
                )
                fig_acc.add_hline(y=85, line_dash="dash", line_color="orange",
                                   annotation_text="85% target")
                fig_acc.update_traces(textposition="outside")
                fig_acc.update_layout(showlegend=False, margin=dict(t=10, b=10))
                st.plotly_chart(fig_acc, use_container_width=True)

                st.subheader("Confusion Details")
                confusion = (
                    merged.groupby(["expected_category", "category"])
                    .size()
                    .reset_index(name="count")
                )
                st.dataframe(confusion, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(f"Accuracy analysis failed: {exc}")

# ── Feature demand ─────────────────────────────────────────────────────────────
with tab_features:
    st.subheader("Top Feature Requests by Demand Score")
    if not tickets.empty:
        feat_df = tickets[tickets["category"] == "Feature Request"].copy()
        if feat_df.empty:
            st.info("No feature request tickets found.")
        else:
            feat_df["demand_score"] = pd.to_numeric(feat_df.get("demand_score", pd.Series(dtype=float)),
                                                      errors="coerce").fillna(0)
            if feat_df["demand_score"].sum() == 0:
                st.info("Demand score data not available in the tickets CSV.")
            else:
                top_feat = feat_df.nlargest(15, "demand_score")
                fig_feat = px.bar(
                    top_feat, x="demand_score", y="title",
                    orientation="h", text="demand_score",
                    labels={"demand_score": "Demand Score (1–5)", "title": "Feature"},
                    color="demand_score",
                    color_continuous_scale=["#93c5fd", "#1d4ed8"],
                )
                fig_feat.update_layout(yaxis={"autorange": "reversed"},
                                        margin=dict(t=10, b=10))
                st.plotly_chart(fig_feat, use_container_width=True)

        st.subheader("Duplicate Feature Requests")
        dup_feat = feat_df[feat_df.get("is_duplicate", pd.Series(["False"]*len(feat_df))) == "True"]
        if not dup_feat.empty:
            st.dataframe(
                dup_feat[["ticket_id", "title", "duplicate_of", "priority"]],
                use_container_width=True, hide_index=True,
            )
        else:
            st.info("No duplicate feature requests detected.")
    else:
        cold_start_banner()

# ── Latency ───────────────────────────────────────────────────────────────────
with tab_latency:
    st.subheader("Processing Latency per Run")
    if not metrics.empty and "avg_latency_ms" in metrics.columns:
        mdf_l = metrics.copy()
        mdf_l["avg_latency_ms"] = pd.to_numeric(mdf_l["avg_latency_ms"], errors="coerce")
        mdf_l = mdf_l.dropna(subset=["avg_latency_ms"])
        if mdf_l.empty:
            st.info("Latency data not yet populated (set by main.py after run).")
        else:
            mdf_l["run_label"] = mdf_l["timestamp"].str[:16]
            fig_lat = px.bar(mdf_l, x="run_label", y="avg_latency_ms",
                             labels={"run_label": "Run", "avg_latency_ms": "Avg Latency (ms)"},
                             text="avg_latency_ms")
            fig_lat.update_traces(textposition="outside")
            fig_lat.update_layout(margin=dict(t=10, b=50))
            st.plotly_chart(fig_lat, use_container_width=True)
    else:
        st.info("Latency data not yet available.")
