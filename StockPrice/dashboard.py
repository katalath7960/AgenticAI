"""
Streamlit dashboard — manage watchlist and monitor alerts visually.
Run with:  streamlit run dashboard.py
"""

import json
import os
import time
from datetime import datetime

import streamlit as st
import yfinance as yf
import pandas as pd

from agent import (
    load_watchlist, save_watchlist, add_stock, remove_stock,
    get_current_price, get_stock_info, check_stocks, StockWatch,
    GMAIL_SENDER, ALERT_EMAIL,
)

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Alert Agent",
    page_icon="📈",
    layout="wide",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .metric-card {
        background: #0f1117;
        border: 1px solid #2a2d3a;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 0.75rem;
    }
    .ticker-label {
        font-family: 'Space Mono', monospace;
        font-size: 1.1rem;
        font-weight: 700;
        color: #00e5a0;
    }
    .price-label {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
    }
    .up   { color: #00e5a0; }
    .down { color: #ff4f5a; }
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns([4, 1])
with col1:
    st.title("📈 Stock Alert Agent")
    st.caption("Real-time monitoring · SMS notifications via Twilio")
with col2:
    st.metric("Gmail", "✅ Connected" if GMAIL_SENDER else "⚠️ Not set")
    st.metric("Alert to", ALERT_EMAIL if ALERT_EMAIL else "Not set")

st.divider()

# ── Sidebar: Add / Remove ────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Manage Watchlist")

    with st.form("add_form"):
        st.subheader("Add Stock")
        ticker    = st.text_input("Ticker Symbol", placeholder="AAPL").upper()
        threshold = st.slider("Alert threshold (%)", 0.1, 10.0, 1.0, 0.1,
                              help="Send SMS when price rises by this %")
        submitted = st.form_submit_button("➕ Add to Watchlist", use_container_width=True)
        if submitted and ticker:
            add_stock(ticker, threshold)
            st.success(f"Added {ticker}")
            time.sleep(0.5)
            st.rerun()

    st.divider()

    watchlist = load_watchlist()
    if watchlist:
        st.subheader("Remove Stock")
        to_remove = st.selectbox("Select ticker", list(watchlist.keys()))
        if st.button("🗑 Remove", use_container_width=True):
            remove_stock(to_remove)
            st.warning(f"Removed {to_remove}")
            time.sleep(0.5)
            st.rerun()

    st.divider()
    st.subheader("Manual Check")
    if st.button("🔍 Run Check Now", use_container_width=True):
        with st.spinner("Fetching prices…"):
            check_stocks()
        st.success("Check complete!")
        st.rerun()

    st.divider()
    st.caption("Auto-refresh every 60s when agent is running.")

# ── Main: Live Price Cards ───────────────────────────────────────────────────
watchlist = load_watchlist()

if not watchlist:
    st.info("Your watchlist is empty. Add stocks in the sidebar →")
else:
    st.subheader("Live Prices")
    cols = st.columns(min(len(watchlist), 4))

    for i, (ticker, watch) in enumerate(watchlist.items()):
        price    = get_current_price(ticker)
        old      = watch.last_price
        pct      = ((price - old) / old * 100) if (price and old) else 0
        sign     = "+" if pct >= 0 else ""
        css_cls  = "up" if pct >= 0 else "down"
        arrow    = "▲" if pct >= 0 else "▼"

        with cols[i % 4]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="ticker-label">{ticker}</div>
                <div class="price-label">${f"{price:.2f}" if price else "—"}</div>
                <div class="{css_cls}">{arrow} {sign}{pct:.2f}% from baseline</div>
                <small style="color:#888">Alert at +{watch.alert_threshold_pct}% &nbsp;|&nbsp; 
                {watch.alert_count} alerts sent</small>
            </div>
            """, unsafe_allow_html=True)

    # ── Alert history table ──────────────────────────────────────────────────
    st.divider()
    st.subheader("Watchlist Summary")
    rows = []
    for ticker, w in watchlist.items():
        price = get_current_price(ticker)
        rows.append({
            "Ticker":      ticker,
            "Current Price": f"${price:.2f}" if price else "—",
            "Baseline":    f"${w.last_price:.2f}" if w.last_price else "—",
            "Threshold":   f"+{w.alert_threshold_pct}%",
            "Alerts Sent": w.alert_count,
            "Last Alert":  w.last_alert_at[:16] if w.last_alert_at else "None",
            "Added":       w.added_at[:10],
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Sparkline chart ──────────────────────────────────────────────────────
    st.divider()
    st.subheader("📊 1-Day Price Chart")
    selected = st.selectbox("Select stock", list(watchlist.keys()))
    try:
        hist = yf.Ticker(selected).history(period="1d", interval="5m")
        if not hist.empty:
            chart_df = hist[["Close"]].rename(columns={"Close": selected})
            st.line_chart(chart_df, height=300)
        else:
            st.info("No intraday data available (market may be closed).")
    except Exception as e:
        st.error(f"Could not load chart: {e}")
