"""
StockMCP Background Agent
=========================
Monitors a watchlist of stock symbols every CHECK_INTERVAL seconds.
When a price moves by ALERT_THRESHOLD dollars or more, fires an email alert
via notifier.py and records the event in state.json.

Can be used in two ways:
  1. Embedded in the Streamlit app — import StockAgent and call .start()/.stop()
  2. Standalone — run: python agent.py
"""

import asyncio
import json
import logging
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

# Load .env if present (no-op if python-dotenv is absent)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from notifier import send_price_alert

# ── Constants ──────────────────────────────────────────────────────────────────
STATE_FILE          = Path(__file__).parent / "state.json"
SERVER_PATH         = Path(__file__).parent / "server.py"
DEFAULT_THRESHOLD   = 1.0   # fallback if not set in state.json
CHECK_INTERVAL      = 60    # seconds between checks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [AGENT] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("agent")


# ── State helpers ──────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"watchlist": [], "prices": {}, "alerts": []}


def save_state(state: dict) -> None:
    """Atomic write: write to a temp file then rename to avoid corruption."""
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    tmp.replace(STATE_FILE)


# ── MCP fetch helper ───────────────────────────────────────────────────────────

async def _fetch_price_async(symbol: str) -> dict:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        env=None,
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("get_stock_price", {"symbol": symbol})
            return json.loads(result.content[0].text)


def _fetch_price(symbol: str) -> dict:
    """Sync wrapper — safe to call from any thread on Windows."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_fetch_price_async(symbol))
    finally:
        loop.close()


# ── Agent class ────────────────────────────────────────────────────────────────

class StockAgent:
    """
    Background thread that polls watchlisted stock prices every CHECK_INTERVAL
    seconds and fires email alerts when a price moves >= ALERT_THRESHOLD.
    """

    def __init__(self):
        self._stop_event  = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock        = threading.Lock()
        self._logs: list[str] = []
        self._running     = False

    # ── Public API ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop, name="stock-agent", daemon=True
        )
        self._thread.start()
        self._running = True
        self._log("Agent started — monitoring every 60 s")

    def stop(self) -> None:
        if not self._running:
            return
        self._stop_event.set()
        self._running = False
        self._log("Agent stopped")

    def is_running(self) -> bool:
        return self._running

    def get_logs(self) -> list[str]:
        with self._lock:
            return list(self._logs)

    # ── Internal ───────────────────────────────────────────────────────────────

    def _log(self, msg: str) -> None:
        ts    = datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        logger.info(msg)
        with self._lock:
            self._logs.append(entry)
            if len(self._logs) > 500:
                self._logs = self._logs[-500:]

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._check_prices()
            except Exception as exc:
                self._log(f"Unexpected error in check cycle: {exc}")
            # wait CHECK_INTERVAL, but wake immediately if stopped
            self._stop_event.wait(CHECK_INTERVAL)

    def _check_prices(self) -> None:
        state     = load_state()
        watchlist = state.get("watchlist", [])

        if not watchlist:
            self._log("Watchlist empty — nothing to monitor")
            return

        # Read threshold and recipients fresh every cycle — UI changes take effect immediately
        threshold   = float(state.get("threshold", DEFAULT_THRESHOLD))
        recipients  = list(state.get("recipients", []))
        prev_prices = state.get("prices", {})
        alerts      = state.get("alerts", [])

        self._log(
            f"Checking: {', '.join(watchlist)}  "
            f"(threshold: ${threshold:.2f}, recipients: {len(recipients)})"
        )

        for symbol in watchlist:
            try:
                data = _fetch_price(symbol)

                if "error" in data:
                    self._log(f"  {symbol}: ERROR — {data['error']}")
                    continue

                current = data["price"]
                prev    = prev_prices.get(symbol)

                if prev is not None:
                    change     = current - prev
                    change_pct = (change / prev * 100) if prev else 0.0
                    arrow      = "▲" if change >= 0 else "▼"
                    self._log(
                        f"  {symbol}: ${current:.2f}  "
                        f"(prev ${prev:.2f}, {arrow}{change:+.2f})"
                    )

                    if abs(change) >= threshold:
                        self._fire_alert(
                            alerts, symbol, prev, current, change, change_pct, threshold, recipients
                        )
                else:
                    self._log(f"  {symbol}: ${current:.2f}  (baseline set)")

                prev_prices[symbol] = current

            except Exception as exc:
                self._log(f"  {symbol}: exception — {exc}")

        state["prices"] = prev_prices
        state["alerts"] = alerts[-100:]   # keep last 100
        save_state(state)

    def _fire_alert(
        self,
        alerts: list,
        symbol: str,
        old: float,
        new: float,
        change: float,
        change_pct: float,
        threshold: float,
        recipients: list[str],
    ) -> None:
        arrow = "▲" if change >= 0 else "▼"
        self._log(
            f"  *** ALERT: {symbol} {arrow} ${abs(change):.2f} "
            f"({change_pct:+.2f}%) — was ${old:.2f}, now ${new:.2f} ***"
        )
        self._log(f"  Sending to {len(recipients)} recipient(s): {', '.join(recipients)}")

        record: dict = {
            "symbol":        symbol,
            "time":          datetime.now().isoformat(),
            "prev_price":    old,
            "current_price": new,
            "change":        round(change, 2),
            "change_pct":    round(change_pct, 2),
            "threshold":     threshold,
            "recipients":    recipients,
            "email_sent":    False,
            "emails_ok":     [],
            "emails_failed": {},
            "email_error":   None,
        }

        try:
            result = send_price_alert(symbol, old, new, change, change_pct, threshold, recipients)
            record["email_sent"]    = len(result["sent_to"]) > 0
            record["emails_ok"]     = result["sent_to"]
            record["emails_failed"] = result["failed"]
            self._log(f"  Email sent — subject: {result['subject']}")
            if result["sent_to"]:
                self._log(f"  Delivered to: {', '.join(result['sent_to'])}")
            if result["failed"]:
                self._log(f"  Failed for:   {', '.join(result['failed'].keys())}")
        except Exception as exc:
            record["email_error"] = str(exc)
            self._log(f"  Email failed: {exc}")

        alerts.append(record)


# ── Standalone entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    _state = load_state()
    print("StockMCP Agent — standalone mode")
    print(f"State file : {STATE_FILE}")
    print(f"Threshold  : ${float(_state.get('threshold', DEFAULT_THRESHOLD)):.2f}  (configurable via UI or set_threshold MCP tool)")
    print(f"Interval   : {CHECK_INTERVAL}s")
    print("Press Ctrl+C to stop.\n")

    agent = StockAgent()
    agent.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping agent...")
        agent.stop()
        print("Done.")
