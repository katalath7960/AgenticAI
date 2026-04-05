"""
MCP Client — Stock Price + Watchlist Demo
Connects to the MCP server via stdio and demonstrates all seven tools:

  Market data
    1. Listing available tools
    2. Fetching a single stock price
    3. Fetching company info
    4. Comparing multiple stocks

  Watchlist / agent
    5. Adding symbols to the watchlist
    6. Viewing the watchlist
    7. Viewing alert history

  Then drops into an interactive prompt loop.
"""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PATH = Path(__file__).parent / "server.py"


# ── Display helpers ────────────────────────────────────────────────────────────

def _header(title: str):
    print(f"\n{'─' * 55}")
    print(f"  {title}")
    print(f"{'─' * 55}")


def _print_price(data: dict):
    arrow = "▲" if data.get("change", 0) >= 0 else "▼"
    up    = "\033[92m" if data.get("change", 0) >= 0 else "\033[91m"
    rst   = "\033[0m"
    print(f"  Symbol    : {data.get('symbol')}")
    print(f"  Price     : {data.get('currency','USD')} {data.get('price')}")
    print(f"  Change    : {up}{arrow} {data.get('change'):+.2f} ({data.get('change_pct'):+.2f}%){rst}")
    print(f"  Day Range : {data.get('day_low')} – {data.get('day_high')}")
    if data.get("volume"):
        print(f"  Volume    : {data.get('volume'):,}")


def _print_info(data: dict):
    print(f"  Symbol      : {data.get('symbol')}")
    print(f"  Name        : {data.get('name')}")
    print(f"  Exchange    : {data.get('exchange')}")
    print(f"  Sector      : {data.get('sector')}")
    print(f"  Industry    : {data.get('industry')}")
    mc = data.get("market_cap")
    if mc:
        label = f"${mc/1e12:.2f}T" if mc >= 1e12 else f"${mc/1e9:.2f}B"
        print(f"  Market Cap  : {label}")
    if data.get("pe_ratio"):
        print(f"  P/E Ratio   : {data['pe_ratio']:.2f}")
    if data.get("52w_high"):
        print(f"  52W High    : {data['52w_high']}")
        print(f"  52W Low     : {data['52w_low']}")
    if data.get("description"):
        print(f"\n  About: {data['description']}...")


def _print_comparison(results: list):
    print(f"  {'Symbol':<8} {'Price':>10} {'Change':>10} {'Chg %':>8} {'Volume':>12}")
    print(f"  {'─'*8} {'─'*10} {'─'*10} {'─'*8} {'─'*12}")
    for r in results:
        if "error" in r:
            print(f"  {r['symbol']:<8}  ERROR: {r['error']}")
            continue
        arrow = "▲" if r.get("change", 0) >= 0 else "▼"
        vol   = f"{r['volume']:,}" if r.get("volume") else "N/A"
        print(
            f"  {r['symbol']:<8} {r['price']:>10.2f} "
            f"{arrow}{r['change']:>+9.2f} {r['change_pct']:>+7.2f}% {vol:>12}"
        )


def _print_watchlist(data: dict):
    wl     = data.get("watchlist", [])
    prices = data.get("last_prices", {})
    if not wl:
        print("  (watchlist is empty)")
        return
    print(f"  {'Symbol':<10} {'Last Price':>12}")
    print(f"  {'─'*10} {'─'*12}")
    for sym in wl:
        p = prices.get(sym)
        price_str = f"${p:.2f}" if p is not None else "—"
        print(f"  {sym:<10} {price_str:>12}")


def _print_alerts(data: dict):
    alerts = data.get("alerts", [])
    if not alerts:
        print("  (no alerts recorded yet)")
        return
    print(f"  {'Time':<20} {'Symbol':<8} {'Prev':>8} {'Now':>8} {'Change':>10} {'Email':>6}")
    print(f"  {'─'*20} {'─'*8} {'─'*8} {'─'*8} {'─'*10} {'─'*6}")
    for a in alerts:
        ts     = a.get("time", "")[:19].replace("T", " ")
        arrow  = "▲" if a.get("change", 0) >= 0 else "▼"
        email  = "✓" if a.get("email_sent") else ("✗" if a.get("email_error") else "—")
        print(
            f"  {ts:<20} {a['symbol']:<8} "
            f"${a['prev_price']:>7.2f} ${a['current_price']:>7.2f} "
            f"{arrow}{a['change']:>+9.2f} {email:>6}"
        )


# ── Core client logic ──────────────────────────────────────────────────────────

async def run_demo(session: ClientSession):
    # 1. List tools
    _header("1. Available Tools on Server")
    tools_result = await session.list_tools()
    for t in tools_result.tools:
        print(f"  🔧 {t.name}")
        print(f"     {t.description[:80]}...")

    # 2. Single stock price
    _header("2. Get Stock Price — AAPL")
    res  = await session.call_tool("get_stock_price", {"symbol": "AAPL"})
    _print_price(json.loads(res.content[0].text))

    # 3. Company info
    _header("3. Get Stock Info — TSLA")
    res = await session.call_tool("get_stock_info", {"symbol": "TSLA"})
    _print_info(json.loads(res.content[0].text))

    # 4. Compare stocks
    _header("4. Compare Stocks — AAPL, MSFT, NVDA, TSLA")
    res = await session.call_tool("compare_stocks", {"symbols": "AAPL,MSFT,NVDA,TSLA"})
    _print_comparison(json.loads(res.content[0].text))

    # 5. Add to watchlist
    _header("5. Add AAPL and TSLA to Watchlist")
    for sym in ("AAPL", "TSLA"):
        res = await session.call_tool("add_to_watchlist", {"symbol": sym})
        d   = json.loads(res.content[0].text)
        print(f"  {sym}: {d['status']}  →  watchlist = {d['watchlist']}")

    # 6. View watchlist
    _header("6. Current Watchlist")
    res = await session.call_tool("get_watchlist", {})
    _print_watchlist(json.loads(res.content[0].text))

    # 7. Alert history
    _header("7. Alert History (last 5)")
    res = await session.call_tool("get_alert_history", {"limit": 5})
    _print_alerts(json.loads(res.content[0].text))


async def interactive_loop(session: ClientSession):
    _header("Interactive Mode  (type 'help' for commands, 'exit' to quit)")
    print("""
  Market data
    price <SYMBOL>                e.g.  price AAPL
    info  <SYMBOL>                e.g.  info  MSFT
    compare <SYM1,SYM2,...>       e.g.  compare AAPL,TSLA,NVDA

  Watchlist
    watch   <SYMBOL>              e.g.  watch AAPL
    unwatch <SYMBOL>              e.g.  unwatch AAPL
    watchlist
    alerts  [limit]               e.g.  alerts 10

  exit
""")

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not line:
            continue
        if line.lower() in ("exit", "quit"):
            break

        parts = line.split(maxsplit=1)
        cmd   = parts[0].lower()
        arg   = parts[1].strip() if len(parts) > 1 else ""

        try:
            if cmd == "price" and arg:
                res  = await session.call_tool("get_stock_price", {"symbol": arg})
                data = json.loads(res.content[0].text)
                _print_price(data) if "error" not in data else print(f"  Error: {data['error']}")

            elif cmd == "info" and arg:
                res  = await session.call_tool("get_stock_info", {"symbol": arg})
                data = json.loads(res.content[0].text)
                _print_info(data) if "error" not in data else print(f"  Error: {data['error']}")

            elif cmd == "compare" and arg:
                res  = await session.call_tool("compare_stocks", {"symbols": arg})
                _print_comparison(json.loads(res.content[0].text))

            elif cmd == "watch" and arg:
                res  = await session.call_tool("add_to_watchlist", {"symbol": arg})
                data = json.loads(res.content[0].text)
                print(f"  {data['symbol']}: {data['status']}  →  {data['watchlist']}")

            elif cmd == "unwatch" and arg:
                res  = await session.call_tool("remove_from_watchlist", {"symbol": arg})
                data = json.loads(res.content[0].text)
                print(f"  {data['symbol']}: {data['status']}  →  {data['watchlist']}")

            elif cmd == "watchlist":
                res  = await session.call_tool("get_watchlist", {})
                _print_watchlist(json.loads(res.content[0].text))

            elif cmd == "alerts":
                limit = int(arg) if arg.isdigit() else 20
                res   = await session.call_tool("get_alert_history", {"limit": limit})
                _print_alerts(json.loads(res.content[0].text))

            elif cmd == "help":
                print("""
  price <SYM>  |  info <SYM>  |  compare <SYM,...>
  watch <SYM>  |  unwatch <SYM>  |  watchlist  |  alerts [N]  |  exit
""")
            else:
                print("  Unknown command. Type 'help'.")

        except Exception as exc:
            print(f"  Error: {exc}")


# ── Entry point ────────────────────────────────────────────────────────────────

async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        env=None,
    )
    print("Connecting to Stock Price MCP Server...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected!\n")
            await run_demo(session)
            await interactive_loop(session)


if __name__ == "__main__":
    asyncio.run(main())
