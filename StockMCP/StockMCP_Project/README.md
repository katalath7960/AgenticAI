# StockMCP — Stock Price MCP Server, Agent & Dashboard

A **Model Context Protocol (MCP)** implementation that exposes real-time stock price data as tools, a **background monitoring agent** that fires email alerts when a price moves by $1 or more, and a **Streamlit web dashboard**.

---

## Project Structure

```
StockMCP_Project/
├── server.py          # MCP Server — 7 tools (market data + watchlist)
├── client.py          # MCP Client — CLI demo + interactive loop
├── agent.py           # Background agent — monitors watchlist, fires alerts
├── notifier.py        # Email sender (SMTP/Gmail)
├── app.py             # Streamlit Web UI — 5-tab dashboard
├── state.json         # Auto-created — watchlist, prices, alert history
├── .env               # Your email credentials (create from .env.example)
├── .env.example       # Template for email config
├── requirements.txt   # All dependencies
└── README.md
```

---

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│  Streamlit  app.py                                        │
│  ┌─────────────┬──────────────┬────────────┬──────────┐   │
│  │ Stock Price │ Company Info │  Compare   │Watchlist │   │
│  │             │              │            │& Agent   │   │
│  └─────────────┴──────────────┴────────────┴──────────┘   │
│                                                           │
│  @st.cache_resource ──► StockAgent (background thread)   │
│                          └─ every 60 s: fetch → compare  │
│                                         └─ Δ ≥ $1 → email│
└───────────────────────────────────────────────────────────┘
          │  stdio MCP per query (subprocess)
┌───────────────────────────────────────────────────────────┐
│  server.py  (MCP Server subprocess)                       │
│  Tools: get_stock_price · get_stock_info · compare_stocks │
│          add_to_watchlist · remove_from_watchlist         │
│          get_watchlist · get_alert_history                │
└───────────────────────────────────────────────────────────┘
          │  reads / atomic writes
┌───────────────────────────────────────────────────────────┐
│  state.json  { watchlist, prices, alerts }                │
└───────────────────────────────────────────────────────────┘
          │
┌───────────────────────────────────────────────────────────┐
│  notifier.py  →  Gmail / SMTP email alert                 │
└───────────────────────────────────────────────────────────┘
```

---

## MCP Tools

| Tool | Input | Output |
|---|---|---|
| `get_stock_price` | `symbol` | Price, prev close, change, % change, day high/low, volume |
| `get_stock_info` | `symbol` | Name, exchange, sector, market cap, P/E, 52W high/low, description |
| `compare_stocks` | `symbols` (comma-sep) | Side-by-side price snapshot for all symbols |
| `add_to_watchlist` | `symbol` | Adds symbol; returns updated watchlist |
| `remove_from_watchlist` | `symbol` | Removes symbol; returns updated watchlist |
| `get_watchlist` | — | Watchlist + last-known prices |
| `get_alert_history` | `limit` (optional) | Most recent N alert records |

---

## Setup

### 1. Install dependencies

```bash
cd StockMCP/StockMCP_Project
pip install -r requirements.txt
```

### 2. Configure email alerts

```bash
cp .env.example .env
```

Edit `.env` and fill in your Gmail credentials:

```env
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
ALERT_EMAIL=your-email@gmail.com
```

**Gmail App Password quick-start:**
1. Enable 2-Factor Authentication on your Google Account
2. Go to: Google Account → Security → App Passwords
3. Generate an app password for "Mail"
4. Paste the 16-character password as `SMTP_PASSWORD`

> Email is optional — the agent still monitors prices and logs alerts even without email configured. You will just see `Email failed: …` in the logs.

---

## Running the Streamlit Dashboard (Recommended)

```bash
streamlit run app.py
```

Opens in your browser at **http://localhost:8501**

### Dashboard Tabs

| Tab | What it does |
|---|---|
| **Stock Price** | Enter a symbol → live price, change, day range, volume |
| **Company Info** | Enter a symbol → sector, market cap, P/E, 52W range, description |
| **Compare Stocks** | Comma-separated symbols → color-coded table + bar chart |
| **Watchlist & Agent** | Add/remove symbols · Start/Stop agent · View live logs · Email config help |
| **Alerts** | Full alert history with email delivery status |

### Using the agent from the UI

1. Open the **Watchlist & Agent** tab
2. Add stock symbols (e.g. `AAPL`, `TSLA`)
3. Click **Start Agent**
4. The agent checks prices every 60 seconds — when any price moves ≥ $1 it sends an email and records the alert
5. View logs in real time on the same tab; view the alert history on the **Alerts** tab

---

## Running the Agent Standalone

Useful for running the monitor as a headless background service:

```bash
python agent.py
```

Output:
```
StockMCP Agent — standalone mode
State file : .../state.json
Threshold  : $1.00
Interval   : 60s
Press Ctrl+C to stop.

[10:00:00] Agent started — monitoring every 60 s
[10:00:00] Checking: AAPL, TSLA
[10:00:01]   AAPL: $213.49  (baseline set)
[10:00:01]   TSLA: $178.90  (baseline set)
[10:01:00] Checking: AAPL, TSLA
[10:01:01]   AAPL: $213.49  (prev $213.49, ▲+0.00)
[10:01:01]   TSLA: $176.50  (prev $178.90, ▼-2.40)
[10:01:01]   *** ALERT: TSLA ▼ $2.40 (-1.34%) — was $178.90, now $176.50 ***
[10:01:02]   Email sent: [StockMCP Alert] TSLA ▼ $2.40 ...
```

---

## Running the CLI Client

```bash
python client.py
```

Runs a full demo sequence then drops into an interactive prompt:

```
> price AAPL
> info MSFT
> compare AAPL,TSLA,NVDA
> watch AAPL
> watch TSLA
> watchlist
> alerts 10
> unwatch TSLA
> exit
```

---

## Running the MCP Server Standalone (debugging only)

```bash
python server.py
```

The server waits on stdin for MCP JSON-RPC messages. The client and Streamlit app spawn it automatically as a subprocess.

---

## Example Alert Email

**Subject:** `[StockMCP Alert] TSLA ▼ $2.40 (-1.34%) — Price is now $176.50`

```
Stock Price Alert — TSLA
========================================
Time           : 2025-10-01 10:01:01
Symbol         : TSLA
Previous Price : $178.90
Current Price  : $176.50
Change         : ▼  $2.40  (-1.34%)
Direction      : DOWN

This alert was triggered because the price moved by $1.00 or more.
```

---

## Architecture Notes

- **Transport:** `stdio` — server runs as a subprocess; client and Streamlit app communicate over stdin/stdout pipes
- **Protocol:** JSON-RPC 2.0 wrapped in MCP envelope (handled by the `mcp` SDK)
- **Data source:** Yahoo Finance via `yfinance` — free, no API key required
- **State:** `state.json` shared between the server (watchlist CRUD) and the agent (price tracking + alert log). Writes are atomic (temp-file + rename).
- **Agent threading:** `StockAgent` runs in a daemon thread. In Streamlit it is kept alive across page reruns via `@st.cache_resource`.
- **Async/Windows:** each MCP call creates a fresh `asyncio` event loop (`new_event_loop()` + `run_until_complete()`) to avoid Windows ProactorEventLoop conflicts in non-main threads.
