"""
Streamlit UI — StockMCP Dashboard
Tabs: Stock Price | Company Info | Compare | Watchlist & Agent | Alerts

The background StockAgent is a module-level singleton kept alive across
Streamlit reruns via @st.cache_resource.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from agent import StockAgent, STATE_FILE

SERVER_PATH = Path(__file__).parent / "server.py"


# ── MCP helpers ────────────────────────────────────────────────────────────────

async def _call_tool_async(tool_name: str, arguments: dict):
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        env=None,
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return json.loads(result.content[0].text)


def call_tool(tool_name: str, arguments: dict):
    """Sync wrapper — safe to call from any Streamlit thread on Windows."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_call_tool_async(tool_name, arguments))
    finally:
        loop.close()


# ── Singleton agent (survives Streamlit reruns) ────────────────────────────────

@st.cache_resource
def get_agent() -> StockAgent:
    return StockAgent()


# ── Page layout ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="StockMCP Dashboard", page_icon="📈", layout="wide")
st.title("📈 StockMCP Dashboard")
st.caption("Real-time stock data via Yahoo Finance · Background price-alert agent")

agent = get_agent()

tab_price, tab_info, tab_compare, tab_watch, tab_alerts = st.tabs(
    ["Stock Price", "Company Info", "Compare Stocks", "Watchlist & Agent", "Alerts"]
)


# ══════════════════════════════════════════════════════════════════════════════
# Tab 1 — Stock Price
# ══════════════════════════════════════════════════════════════════════════════
with tab_price:
    st.subheader("Real-Time Stock Price")
    col1, col2 = st.columns([3, 1])
    with col1:
        price_sym = st.text_input(
            "Ticker Symbol", value="AAPL", placeholder="e.g. AAPL", key="price_sym"
        ).upper().strip()
    with col2:
        st.write(""); st.write("")
        price_go = st.button("Get Price", key="price_btn", use_container_width=True)

    if price_go and price_sym:
        with st.spinner(f"Fetching {price_sym}…"):
            try:
                d = call_tool("get_stock_price", {"symbol": price_sym})
                if "error" in d:
                    st.error(d["error"])
                else:
                    c1, c2, c3, c4 = st.columns(4)
                    sign = "+" if d["change"] >= 0 else ""
                    c1.metric(
                        f"{d['symbol']} ({d.get('currency','USD')})",
                        f"{d['price']:.2f}",
                        f"{sign}{d['change']:.2f} ({sign}{d['change_pct']:.2f}%)",
                    )
                    c2.metric("Prev Close", f"{d['previous_close']:.2f}")
                    c3.metric("Day High",   f"{d['day_high']:.2f}")
                    c4.metric("Day Low",    f"{d['day_low']:.2f}")
                    if d.get("volume"):
                        st.caption(f"Volume: {d['volume']:,}")
            except Exception as e:
                st.error(str(e))


# ══════════════════════════════════════════════════════════════════════════════
# Tab 2 — Company Info
# ══════════════════════════════════════════════════════════════════════════════
with tab_info:
    st.subheader("Company Information")
    col1, col2 = st.columns([3, 1])
    with col1:
        info_sym = st.text_input(
            "Ticker Symbol", value="TSLA", placeholder="e.g. TSLA", key="info_sym"
        ).upper().strip()
    with col2:
        st.write(""); st.write("")
        info_go = st.button("Get Info", key="info_btn", use_container_width=True)

    if info_go and info_sym:
        with st.spinner(f"Fetching {info_sym}…"):
            try:
                d = call_tool("get_stock_info", {"symbol": info_sym})
                if "error" in d:
                    st.error(d["error"])
                else:
                    st.write(f"### {d.get('name', info_sym)}  ({d['symbol']})")
                    st.caption(
                        f"Exchange: **{d.get('exchange','N/A')}**  ·  "
                        f"Currency: **{d.get('currency','USD')}**"
                    )
                    ca, cb = st.columns(2)
                    with ca:
                        st.write(f"**Sector:** {d.get('sector','N/A')}")
                        st.write(f"**Industry:** {d.get('industry','N/A')}")
                        mc = d.get("market_cap")
                        if mc:
                            st.write(
                                f"**Market Cap:** "
                                f"{'${:.2f}T'.format(mc/1e12) if mc>=1e12 else '${:.2f}B'.format(mc/1e9)}"
                            )
                    with cb:
                        if d.get("pe_ratio"):
                            st.write(f"**P/E Ratio:** {d['pe_ratio']:.2f}")
                        if d.get("52w_high"):
                            st.write(f"**52W High:** {d['52w_high']}")
                            st.write(f"**52W Low:** {d['52w_low']}")
                        if d.get("dividend_yield"):
                            st.write(f"**Dividend Yield:** {d['dividend_yield']:.2%}")
                    if d.get("description"):
                        with st.expander("About"):
                            st.write(d["description"] + "…")
            except Exception as e:
                st.error(str(e))


# ══════════════════════════════════════════════════════════════════════════════
# Tab 3 — Compare Stocks
# ══════════════════════════════════════════════════════════════════════════════
with tab_compare:
    st.subheader("Compare Multiple Stocks")
    col1, col2 = st.columns([3, 1])
    with col1:
        cmp_syms = st.text_input(
            "Comma-separated symbols", value="AAPL,MSFT,NVDA,TSLA", key="cmp_syms"
        ).upper().strip()
    with col2:
        st.write(""); st.write("")
        cmp_go = st.button("Compare", key="cmp_btn", use_container_width=True)

    if cmp_go and cmp_syms:
        with st.spinner("Fetching…"):
            try:
                results = call_tool("compare_stocks", {"symbols": cmp_syms})
                rows = []
                for r in results:
                    rows.append({
                        "Symbol":   r["symbol"],
                        "Price":    r.get("price"),
                        "Change":   r.get("change"),
                        "Change %": r.get("change_pct"),
                        "Day High": r.get("day_high"),
                        "Day Low":  r.get("day_low"),
                        "Volume":   r.get("volume"),
                        "Error":    r.get("error", ""),
                    })
                df = pd.DataFrame(rows)

                def _color_change(val):
                    if val is None or not isinstance(val, (int, float)):
                        return ""
                    return "color: green" if val >= 0 else "color: red"

                styled = df.style.applymap(_color_change, subset=["Change", "Change %"])
                st.dataframe(styled, use_container_width=True, hide_index=True)

                price_data = {r["Symbol"]: r["Price"] for r in rows if r.get("Price")}
                if price_data:
                    st.bar_chart(price_data)
            except Exception as e:
                st.error(str(e))


# ══════════════════════════════════════════════════════════════════════════════
# Tab 4 — Watchlist & Agent
# ══════════════════════════════════════════════════════════════════════════════
with tab_watch:
    st.subheader("Watchlist & Background Agent")

    # ── Agent control ──────────────────────────────────────────────────────────
    st.markdown("#### Agent Control")
    is_running = agent.is_running()

    # Fetch live threshold from state via MCP
    try:
        _tdata = call_tool("get_threshold", {})
        _current_threshold = float(_tdata.get("threshold", 1.0))
    except Exception:
        _current_threshold = 1.0

    status_col, btn_col = st.columns([2, 1])
    with status_col:
        if is_running:
            st.success(
                f"Agent is RUNNING — checking every 60 s  |  "
                f"Alert threshold: **${_current_threshold:.2f}**"
            )
        else:
            st.warning("Agent is STOPPED")
    with btn_col:
        if is_running:
            if st.button("Stop Agent", key="stop_agent", use_container_width=True):
                agent.stop()
                st.rerun()
        else:
            if st.button("Start Agent", key="start_agent", use_container_width=True, type="primary"):
                agent.start()
                st.rerun()

    # ── Threshold configuration ────────────────────────────────────────────────
    st.markdown("#### Alert Threshold")
    st.caption("An email alert fires when a stock price moves by at least this amount.")
    thr_col, thr_btn_col = st.columns([2, 1])
    with thr_col:
        new_threshold = st.number_input(
            "Price change threshold ($)",
            min_value=0.01,
            max_value=1000.0,
            value=_current_threshold,
            step=0.25,
            format="%.2f",
            key="threshold_input",
            help="Agent reads this value fresh every cycle — no restart needed.",
        )
    with thr_btn_col:
        st.write(""); st.write("")
        if st.button("Set Threshold", key="set_thr_btn", use_container_width=True):
            try:
                r = call_tool("set_threshold", {"threshold": new_threshold})
                if "error" in r:
                    st.error(r["error"])
                else:
                    st.success(f"Threshold updated to ${r['threshold']:.2f}")
                    st.rerun()
            except Exception as e:
                st.error(str(e))

    st.divider()

    # ── Alert recipients ───────────────────────────────────────────────────────
    st.markdown("#### Alert Recipients")
    st.caption("Alerts are sent to all addresses in this list when a price threshold is crossed.")

    # Fetch current recipients
    try:
        _rdata      = call_tool("get_recipients", {})
        _recipients = _rdata.get("recipients", [])
    except Exception:
        _recipients = []

    # Add new recipient
    add_rec_col, add_rec_btn_col = st.columns([3, 1])
    with add_rec_col:
        new_email = st.text_input(
            "Add email address",
            placeholder="e.g. colleague@example.com",
            key="new_recipient_input",
        ).strip().lower()
    with add_rec_btn_col:
        st.write(""); st.write("")
        if st.button("Add Recipient", key="add_rec_btn", use_container_width=True):
            if new_email:
                try:
                    r = call_tool("add_recipient", {"email": new_email})
                    if "error" in r:
                        st.error(r["error"])
                    else:
                        st.success(f"{r['email']}: {r['status']}")
                        st.rerun()
                except Exception as e:
                    st.error(str(e))
            else:
                st.warning("Enter an email address first.")

    # Current recipients table with per-row Remove buttons
    if not _recipients:
        st.info("No recipients configured. Add at least one address above.")
    else:
        st.write(f"**{len(_recipients)} recipient(s) configured:**")
        for addr in _recipients:
            rec_col, rm_col = st.columns([4, 1])
            with rec_col:
                st.write(f"✉ {addr}")
            with rm_col:
                # Use a sanitised key so special chars in emails don't break Streamlit
                safe_key = f"rm_rec_{addr.replace('@','_at_').replace('.','_')}"
                if st.button("Remove", key=safe_key, use_container_width=True):
                    try:
                        r = call_tool("remove_recipient", {"email": addr})
                        st.info(f"{r['email']}: {r['status']}")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    st.divider()

    # ── Watchlist management ───────────────────────────────────────────────────
    st.markdown("#### Manage Watchlist")
    wa_col, wr_col = st.columns(2)

    with wa_col:
        add_sym = st.text_input(
            "Add symbol", placeholder="e.g. AAPL", key="add_sym"
        ).upper().strip()
        if st.button("Add to Watchlist", key="add_btn", use_container_width=True):
            if add_sym:
                with st.spinner(f"Adding {add_sym}…"):
                    try:
                        r = call_tool("add_to_watchlist", {"symbol": add_sym})
                        st.success(f"{r['symbol']}: {r['status']}")
                    except Exception as e:
                        st.error(str(e))
            else:
                st.warning("Enter a symbol first.")

    with wr_col:
        rm_sym = st.text_input(
            "Remove symbol", placeholder="e.g. TSLA", key="rm_sym"
        ).upper().strip()
        if st.button("Remove from Watchlist", key="rm_btn", use_container_width=True):
            if rm_sym:
                with st.spinner(f"Removing {rm_sym}…"):
                    try:
                        r = call_tool("remove_from_watchlist", {"symbol": rm_sym})
                        st.info(f"{r['symbol']}: {r['status']}")
                    except Exception as e:
                        st.error(str(e))
            else:
                st.warning("Enter a symbol first.")

    st.divider()

    # ── Current watchlist table ────────────────────────────────────────────────
    st.markdown("#### Current Watchlist")
    if st.button("Refresh Watchlist", key="refresh_wl"):
        st.rerun()

    try:
        wl_data   = call_tool("get_watchlist", {})
        watchlist = wl_data.get("watchlist", [])
        prices    = wl_data.get("last_prices", {})

        if not watchlist:
            st.info("Watchlist is empty. Add symbols above.")
        else:
            rows = [
                {
                    "Symbol":     sym,
                    "Last Price": f"${prices[sym]:.2f}" if sym in prices else "—",
                }
                for sym in watchlist
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Could not load watchlist: {e}")

    st.divider()

    # ── Agent logs ─────────────────────────────────────────────────────────────
    st.markdown("#### Agent Logs")
    logs = agent.get_logs()
    if logs:
        log_text = "\n".join(reversed(logs[-50:]))   # newest first, last 50
        st.text_area("Recent log entries (newest first)", log_text, height=250, key="log_area")
    else:
        st.caption("No log entries yet. Start the agent and add symbols to the watchlist.")

    # ── Email config hint ──────────────────────────────────────────────────────
    with st.expander("Email sender configuration (.env)"):
        st.markdown("""
Set the following in a `.env` file in the project directory
(or as environment variables before launching Streamlit):

| Variable | Description |
|---|---|
| `GMAIL_SENDER` | Your Gmail address — used as the **From** address |
| `GMAIL_APP_PASSWORD` | 16-char Gmail App Password — spaces are OK |
| `ALERT_EMAIL` | Fallback recipient if no recipients are configured above |

**Recipients are managed above** — add or remove addresses any time.
Changes take effect on the next agent check cycle (no restart needed).

**Gmail App Password quick-start:**
1. Enable 2-Factor Authentication on your Google Account
2. Go to **Google Account → Security → App Passwords**
3. Generate an app password for "Mail"
4. Paste the 16-character code as `GMAIL_APP_PASSWORD` (spaces are fine)
""")


# ══════════════════════════════════════════════════════════════════════════════
# Tab 5 — Alerts
# ══════════════════════════════════════════════════════════════════════════════
with tab_alerts:
    st.subheader("Price-Change Alert History")

    col_lim, col_ref = st.columns([2, 1])
    with col_lim:
        limit = st.slider("Max alerts to show", 5, 100, 20, key="alert_limit")
    with col_ref:
        st.write("")
        if st.button("Refresh Alerts", key="refresh_alerts", use_container_width=True):
            st.rerun()

    try:
        alert_data = call_tool("get_alert_history", {"limit": limit})
        alerts     = alert_data.get("alerts", [])

        if not alerts:
            st.info("No alerts recorded yet. Start the agent and add symbols to the watchlist.")
        else:
            st.caption(f"Showing {len(alerts)} most recent alert(s)")

            rows = []
            for a in alerts:
                ts     = a.get("time", "")[:19].replace("T", " ")
                change = a.get("change", 0)
                arrow  = "▲" if change >= 0 else "▼"

                ok_list  = a.get("emails_ok", [])
                fail_map = a.get("emails_failed", {})
                err      = a.get("email_error")

                if err:
                    delivery = f"❌ Error: {err[:50]}"
                elif ok_list or fail_map:
                    parts = []
                    if ok_list:
                        parts.append(f"✅ {len(ok_list)} sent")
                    if fail_map:
                        parts.append(f"❌ {len(fail_map)} failed")
                    delivery = " · ".join(parts)
                elif a.get("email_sent"):
                    # legacy record without ok/fail detail
                    delivery = "✅ Sent"
                else:
                    delivery = "—"

                rows.append({
                    "Time":       ts,
                    "Symbol":     a["symbol"],
                    "Prev ($)":   a["prev_price"],
                    "Now ($)":    a["current_price"],
                    "Change ($)": a["change"],
                    "Change (%)": a["change_pct"],
                    "Direction":  f"{arrow} {'UP' if change >= 0 else 'DOWN'}",
                    "Threshold":  f"${a.get('threshold', 1.0):.2f}",
                    "Delivery":   delivery,
                })

            df = pd.DataFrame(rows)

            def _color(val):
                if not isinstance(val, (int, float)):
                    return ""
                return "color: green" if val >= 0 else "color: red"

            styled = df.style.applymap(_color, subset=["Change ($)", "Change (%)"])
            st.dataframe(styled, use_container_width=True, hide_index=True)

            # Per-alert delivery detail (expandable)
            with st.expander("Delivery detail per alert"):
                for i, a in enumerate(alerts):
                    ok_list  = a.get("emails_ok", [])
                    fail_map = a.get("emails_failed", {})
                    err      = a.get("email_error")
                    ts       = a.get("time", "")[:19].replace("T", " ")
                    st.markdown(
                        f"**{i+1}. {a['symbol']} @ {ts}**  "
                        f"— threshold ${a.get('threshold', 1.0):.2f}"
                    )
                    if err:
                        st.error(f"Send error: {err}")
                    else:
                        for addr in ok_list:
                            st.write(f"  ✅ {addr}")
                        for addr, reason in fail_map.items():
                            st.write(f"  ❌ {addr} — {reason}")
                        if not ok_list and not fail_map:
                            st.write("  — no delivery info")

            # Summary metrics
            total          = len(alerts)
            total_ok       = sum(len(a.get("emails_ok", [])) for a in alerts)
            total_failed   = sum(len(a.get("emails_failed", {})) for a in alerts)
            total_err      = sum(1 for a in alerts if a.get("email_error"))
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Alerts",      total)
            m2.metric("Emails Delivered",  total_ok)
            m3.metric("Emails Failed",     total_failed)
            m4.metric("Send Errors",       total_err)

    except Exception as e:
        st.error(f"Could not load alerts: {e}")
