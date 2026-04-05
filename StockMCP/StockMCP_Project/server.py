"""
MCP Server — Stock Price Service
Exposes seven tools over stdio transport:

  Market data
  ───────────
  • get_stock_price      — real-time price + change for one symbol
  • get_stock_info       — company metadata (sector, market cap, P/E, etc.)
  • compare_stocks       — side-by-side comparison of multiple symbols

  Watchlist / agent
  ─────────────────
  • add_to_watchlist     — add a symbol to the monitoring watchlist
  • remove_from_watchlist— remove a symbol from the watchlist
  • get_watchlist        — return current watchlist + last-known prices
  • get_alert_history    — return the last N price-change alerts
"""

import asyncio
import json
import logging
import tempfile
from pathlib import Path

import yfinance as yf
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SERVER] %(message)s")
logger = logging.getLogger(__name__)

# Shared state file (same path used by agent.py)
STATE_FILE = Path(__file__).parent / "state.json"

# ── Server instance ────────────────────────────────────────────────────────────
app = Server("stock-price-server")


# ── State helpers ──────────────────────────────────────────────────────────────

def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"watchlist": [], "prices": {}, "alerts": []}


def _save_state(state: dict) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    tmp.replace(STATE_FILE)


# ── Market-data helpers ────────────────────────────────────────────────────────

def _fetch_price(symbol: str) -> dict:
    ticker = yf.Ticker(symbol)
    info   = ticker.fast_info
    price  = info.last_price
    prev   = info.previous_close or price
    change = price - prev
    pct    = (change / prev * 100) if prev else 0.0
    return {
        "symbol":         symbol.upper(),
        "price":          round(price,  2),
        "previous_close": round(prev,   2),
        "change":         round(change, 2),
        "change_pct":     round(pct,    2),
        "day_high":       round(info.day_high  or 0, 2),
        "day_low":        round(info.day_low   or 0, 2),
        "volume":         info.last_volume,
        "currency":       info.currency or "USD",
    }


def _fetch_info(symbol: str) -> dict:
    raw = yf.Ticker(symbol).info
    return {
        "symbol":         symbol.upper(),
        "name":           raw.get("longName") or raw.get("shortName", symbol),
        "exchange":       raw.get("exchange",            "N/A"),
        "sector":         raw.get("sector",              "N/A"),
        "industry":       raw.get("industry",            "N/A"),
        "currency":       raw.get("currency",            "USD"),
        "market_cap":     raw.get("marketCap"),
        "pe_ratio":       raw.get("trailingPE"),
        "52w_high":       raw.get("fiftyTwoWeekHigh"),
        "52w_low":        raw.get("fiftyTwoWeekLow"),
        "dividend_yield": raw.get("dividendYield"),
        "description":    (raw.get("longBusinessSummary") or "")[:300],
    }


# ── Tool definitions ───────────────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        # ── Market data ──────────────────────────────────────────────────────
        types.Tool(
            name="get_stock_price",
            description=(
                "Get the current real-time stock price for a given ticker symbol. "
                "Returns price, previous close, change, % change, day high/low, volume."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "e.g. AAPL, TSLA"}
                },
                "required": ["symbol"],
            },
        ),
        types.Tool(
            name="get_stock_info",
            description=(
                "Get detailed company information: name, sector, industry, "
                "market cap, P/E ratio, 52-week high/low, dividend yield."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "e.g. AAPL, TSLA"}
                },
                "required": ["symbol"],
            },
        ),
        types.Tool(
            name="compare_stocks",
            description=(
                "Compare current prices and daily changes for multiple symbols "
                "side-by-side. Pass a comma-separated list."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "string",
                        "description": "Comma-separated symbols, e.g. AAPL,TSLA,MSFT",
                    }
                },
                "required": ["symbols"],
            },
        ),
        # ── Watchlist ────────────────────────────────────────────────────────
        types.Tool(
            name="add_to_watchlist",
            description="Add a stock symbol to the monitoring watchlist.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Ticker symbol to add"}
                },
                "required": ["symbol"],
            },
        ),
        types.Tool(
            name="remove_from_watchlist",
            description="Remove a stock symbol from the monitoring watchlist.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Ticker symbol to remove"}
                },
                "required": ["symbol"],
            },
        ),
        types.Tool(
            name="get_watchlist",
            description=(
                "Return the current watchlist with the last-known price for each symbol."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_alert_history",
            description="Return the most recent price-change alert records.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max number of alerts to return (default 20)",
                    }
                },
            },
        ),
        types.Tool(
            name="set_threshold",
            description=(
                "Set the price-change threshold (in dollars) that triggers an alert. "
                "The background agent reads this value fresh every cycle, so changes "
                "take effect immediately without restarting the agent."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "threshold": {
                        "type": "number",
                        "description": "Dollar amount (e.g. 1.0, 0.5, 2.5). Must be > 0.",
                    }
                },
                "required": ["threshold"],
            },
        ),
        types.Tool(
            name="get_threshold",
            description="Return the current price-change alert threshold in dollars.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="add_recipient",
            description="Add an email address to the alert recipient list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Email address to add, e.g. user@example.com",
                    }
                },
                "required": ["email"],
            },
        ),
        types.Tool(
            name="remove_recipient",
            description="Remove an email address from the alert recipient list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Email address to remove",
                    }
                },
                "required": ["email"],
            },
        ),
        types.Tool(
            name="get_recipients",
            description="Return the current list of alert email recipients.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


# ── Tool execution ─────────────────────────────────────────────────────────────

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    def _ok(payload) -> list[types.TextContent]:
        return [types.TextContent(type="text", text=json.dumps(payload, indent=2))]

    try:
        # ── Market data ──────────────────────────────────────────────────────
        if name == "get_stock_price":
            symbol = arguments["symbol"].upper().strip()
            logger.info("get_stock_price: %s", symbol)
            return _ok(_fetch_price(symbol))

        elif name == "get_stock_info":
            symbol = arguments["symbol"].upper().strip()
            logger.info("get_stock_info: %s", symbol)
            return _ok(_fetch_info(symbol))

        elif name == "compare_stocks":
            symbols = [s.strip().upper() for s in arguments["symbols"].split(",") if s.strip()]
            logger.info("compare_stocks: %s", symbols)
            results = []
            for sym in symbols:
                try:
                    results.append(_fetch_price(sym))
                except Exception as exc:
                    results.append({"symbol": sym, "error": str(exc)})
            return _ok(results)

        # ── Watchlist ────────────────────────────────────────────────────────
        elif name == "add_to_watchlist":
            symbol = arguments["symbol"].upper().strip()
            state  = _load_state()
            if symbol not in state["watchlist"]:
                state["watchlist"].append(symbol)
                _save_state(state)
                logger.info("add_to_watchlist: %s", symbol)
                return _ok({"status": "added", "symbol": symbol, "watchlist": state["watchlist"]})
            return _ok({"status": "already_present", "symbol": symbol, "watchlist": state["watchlist"]})

        elif name == "remove_from_watchlist":
            symbol = arguments["symbol"].upper().strip()
            state  = _load_state()
            if symbol in state["watchlist"]:
                state["watchlist"].remove(symbol)
                state["prices"].pop(symbol, None)
                _save_state(state)
                logger.info("remove_from_watchlist: %s", symbol)
                return _ok({"status": "removed", "symbol": symbol, "watchlist": state["watchlist"]})
            return _ok({"status": "not_found", "symbol": symbol, "watchlist": state["watchlist"]})

        elif name == "get_watchlist":
            state  = _load_state()
            result = {
                "watchlist": state.get("watchlist", []),
                "last_prices": state.get("prices", {}),
            }
            return _ok(result)

        elif name == "get_alert_history":
            limit  = int(arguments.get("limit", 20))
            state  = _load_state()
            alerts = state.get("alerts", [])[-limit:]
            return _ok({"count": len(alerts), "alerts": list(reversed(alerts))})

        elif name == "set_threshold":
            value = float(arguments["threshold"])
            if value <= 0:
                return _ok({"error": "threshold must be greater than 0"})
            state = _load_state()
            state["threshold"] = round(value, 2)
            _save_state(state)
            logger.info("set_threshold: $%.2f", value)
            return _ok({"status": "updated", "threshold": state["threshold"]})

        elif name == "get_threshold":
            state = _load_state()
            return _ok({"threshold": state.get("threshold", 1.0)})

        elif name == "add_recipient":
            email = arguments["email"].strip().lower()
            if "@" not in email or "." not in email.split("@")[-1]:
                return _ok({"error": f"Invalid email address: {email}"})
            state = _load_state()
            if "recipients" not in state:
                state["recipients"] = []
            if email not in state["recipients"]:
                state["recipients"].append(email)
                _save_state(state)
                logger.info("add_recipient: %s", email)
                return _ok({"status": "added", "email": email, "recipients": state["recipients"]})
            return _ok({"status": "already_present", "email": email, "recipients": state["recipients"]})

        elif name == "remove_recipient":
            email = arguments["email"].strip().lower()
            state = _load_state()
            if "recipients" not in state:
                state["recipients"] = []
            if email in state["recipients"]:
                state["recipients"].remove(email)
                _save_state(state)
                logger.info("remove_recipient: %s", email)
                return _ok({"status": "removed", "email": email, "recipients": state["recipients"]})
            return _ok({"status": "not_found", "email": email, "recipients": state.get("recipients", [])})

        elif name == "get_recipients":
            state = _load_state()
            return _ok({"recipients": state.get("recipients", [])})

        else:
            return _ok({"error": f"Unknown tool: {name}"})

    except Exception as exc:
        logger.error("Tool %s failed: %s", name, exc)
        return [types.TextContent(type="text", text=json.dumps({"error": str(exc)}))]


# ── Entry point ────────────────────────────────────────────────────────────────

async def main():
    logger.info("Stock Price MCP Server starting (stdio transport)...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
