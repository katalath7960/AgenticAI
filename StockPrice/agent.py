"""
Stock Alert Agent — monitors stock prices and sends email alerts via Gmail SMTP.
Checks prices on a configurable interval and alerts when price rises above threshold.

Email setup (100% free, 500 emails/day):
  1. Use a Gmail account (create a dedicated one if preferred)
  2. Enable 2-Step Verification on the account
  3. Generate an App Password: myaccount.google.com → Security → App Passwords
  4. Set GMAIL_SENDER, GMAIL_APP_PASSWORD, ALERT_EMAIL in your .env
"""

import os
import json
import time
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional

import yfinance as yf
from apscheduler.schedulers.background import BackgroundScheduler

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("agent.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ── Config ─────────────────────────────────────────────────────────────────
WATCHLIST_FILE = os.getenv("WATCHLIST_FILE", "watchlist.json")

GMAIL_SENDER       = os.getenv("GMAIL_SENDER", "")        # your Gmail address
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")  # 16-char App Password
ALERT_EMAIL        = os.getenv("ALERT_EMAIL", "")         # where alerts are sent (can be same)


# ── Data model ─────────────────────────────────────────────────────────────
@dataclass
class StockWatch:
    ticker: str
    alert_threshold_pct: float   # alert if price rises by this % from last check
    last_price: Optional[float] = None
    alert_count: int = 0
    last_alert_at: Optional[str] = None
    added_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ── Persistence ────────────────────────────────────────────────────────────
def load_watchlist() -> dict[str, StockWatch]:
    if not os.path.exists(WATCHLIST_FILE):
        return {}
    with open(WATCHLIST_FILE) as f:
        raw = json.load(f)
    return {k: StockWatch(**v) for k, v in raw.items()}


def save_watchlist(watchlist: dict[str, StockWatch]) -> None:
    with open(WATCHLIST_FILE, "w") as f:
        json.dump({k: asdict(v) for k, v in watchlist.items()}, f, indent=2)


# ── Stock price fetch ──────────────────────────────────────────────────────
def get_current_price(ticker: str) -> Optional[float]:
    """Fetch real-time price from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        info  = stock.fast_info
        price = info.last_price
        if price and price > 0:
            return round(float(price), 4)
        # Fallback: latest 1-minute bar
        hist = stock.history(period="1d", interval="1m")
        if not hist.empty:
            return round(float(hist["Close"].iloc[-1]), 4)
    except Exception as e:
        log.warning(f"Failed to fetch price for {ticker}: {e}")
    return None


def get_stock_info(ticker: str) -> dict:
    """Return basic metadata for a ticker."""
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info
        return {
            "name":     info.get("longName", ticker),
            "exchange": info.get("exchange", ""),
            "currency": info.get("currency", "USD"),
            "sector":   info.get("sector", ""),
        }
    except Exception:
        return {"name": ticker, "exchange": "", "currency": "USD", "sector": ""}


# ── Email alert ────────────────────────────────────────────────────────────
def send_email_alert(watch: StockWatch, old_price: float, new_price: float) -> bool:
    """Send email alert via Gmail SMTP (free). Returns True on success."""
    pct = ((new_price - old_price) / old_price) * 100

    if not all([GMAIL_SENDER, GMAIL_APP_PASSWORD, ALERT_EMAIL]):
        log.warning("Gmail credentials not set — printing alert instead.")
        print(f"\n🚨 ALERT: {watch.ticker} ↑ {pct:.2f}%  ${old_price:.2f} → ${new_price:.2f}\n")
        return False

    try:
        subject = f"📈 Stock Alert: {watch.ticker} +{pct:.2f}%"

        # Plain-text body
        text_body = (
            f"Stock Alert: {watch.ticker}\n"
            f"{'─' * 35}\n"
            f"Previous price : ${old_price:.2f}\n"
            f"Current price  : ${new_price:.2f}\n"
            f"Change         : +{pct:.2f}%\n"
            f"Your threshold : +{watch.alert_threshold_pct}%\n"
            f"Time           : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Alerts sent    : {watch.alert_count + 1}\n"
        )

        # HTML body (renders nicely in Gmail / Outlook)
        html_body = f"""
        <html><body style="font-family:Arial,sans-serif;max-width:480px;margin:auto">
          <div style="background:#0f1117;border-radius:12px;padding:28px 32px;color:#fff">
            <h2 style="margin:0 0 4px;color:#00e5a0">📈 Stock Alert</h2>
            <p style="margin:0 0 20px;color:#888;font-size:13px">
              {datetime.now().strftime('%A, %B %d %Y · %H:%M:%S')}
            </p>
            <div style="font-size:2.2rem;font-weight:700;letter-spacing:-1px">
              {watch.ticker}
            </div>
            <div style="margin:12px 0;font-size:1.5rem;color:#00e5a0;font-weight:600">
              +{pct:.2f}%
            </div>
            <table style="width:100%;border-collapse:collapse;margin-top:16px;font-size:14px">
              <tr style="border-bottom:1px solid #2a2d3a">
                <td style="padding:8px 0;color:#888">Previous</td>
                <td style="padding:8px 0;text-align:right">${old_price:.2f}</td>
              </tr>
              <tr style="border-bottom:1px solid #2a2d3a">
                <td style="padding:8px 0;color:#888">Current</td>
                <td style="padding:8px 0;text-align:right;color:#00e5a0;font-weight:600">${new_price:.2f}</td>
              </tr>
              <tr>
                <td style="padding:8px 0;color:#888">Threshold</td>
                <td style="padding:8px 0;text-align:right">+{watch.alert_threshold_pct}%</td>
              </tr>
            </table>
          </div>
          <p style="color:#888;font-size:11px;text-align:center;margin-top:12px">
            Stock Alert Agent · alert #{watch.alert_count + 1} for {watch.ticker}
          </p>
        </body></html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"Stock Alert Agent <{GMAIL_SENDER}>"
        msg["To"]      = ALERT_EMAIL
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, ALERT_EMAIL, msg.as_string())

        log.info(f"Email sent for {watch.ticker} to {ALERT_EMAIL}")
        return True

    except Exception as e:
        log.error(f"Email failed for {watch.ticker}: {e}")
        return False


# ── Core check loop ────────────────────────────────────────────────────────
def check_stocks() -> None:
    """Called by the scheduler every interval."""
    watchlist = load_watchlist()
    if not watchlist:
        log.info("Watchlist is empty — nothing to check.")
        return

    log.info(f"Checking {len(watchlist)} stocks…")
    changed = False

    for ticker, watch in watchlist.items():
        price = get_current_price(ticker)
        if price is None:
            log.warning(f"Could not fetch price for {ticker}")
            continue

        log.info(f"{ticker}: ${price:.2f}  (last=${watch.last_price})")

        if watch.last_price is None:
            # First run — just record the baseline
            watch.last_price = price
            changed = True
            log.info(f"{ticker}: baseline set at ${price:.2f}")
            continue

        pct_change = ((price - watch.last_price) / watch.last_price) * 100

        if pct_change >= watch.alert_threshold_pct:
            log.info(f"🚨 {ticker} rose {pct_change:.2f}% — triggering alert")
            send_email_alert(watch, watch.last_price, price)
            watch.alert_count += 1
            watch.last_alert_at = datetime.now().isoformat()
            watch.last_price = price   # reset baseline after alert
            changed = True
        elif pct_change < 0:
            # Price dropped — silently update baseline (no alert for drops)
            watch.last_price = price
            changed = True

    if changed:
        save_watchlist(watchlist)


# ── CLI helpers ────────────────────────────────────────────────────────────
def add_stock(ticker: str, threshold_pct: float = 1.0) -> None:
    ticker    = ticker.upper()
    watchlist = load_watchlist()
    if ticker in watchlist:
        print(f"{ticker} is already in the watchlist.")
        return
    info = get_stock_info(ticker)
    watchlist[ticker] = StockWatch(ticker=ticker, alert_threshold_pct=threshold_pct)
    save_watchlist(watchlist)
    print(f"✅ Added {ticker} ({info['name']}) — alert at +{threshold_pct}%")


def remove_stock(ticker: str) -> None:
    ticker    = ticker.upper()
    watchlist = load_watchlist()
    if ticker not in watchlist:
        print(f"{ticker} not found in watchlist.")
        return
    del watchlist[ticker]
    save_watchlist(watchlist)
    print(f"🗑  Removed {ticker}")


def list_stocks() -> None:
    watchlist = load_watchlist()
    if not watchlist:
        print("Watchlist is empty.")
        return
    print(f"\n{'Ticker':<8} {'Last Price':>12} {'Threshold':>10} {'Alerts':>7} {'Last Alert'}")
    print("-" * 65)
    for ticker, w in watchlist.items():
        price      = f"${w.last_price:.2f}" if w.last_price else "—"
        last_alert = w.last_alert_at[:16] if w.last_alert_at else "never"
        print(f"{ticker:<8} {price:>12} {w.alert_threshold_pct:>9}% {w.alert_count:>7}  {last_alert}")
    print()


# ── Entry point ────────────────────────────────────────────────────────────
def run_agent(interval_seconds: int = 60) -> None:
    log.info(f"Agent starting — checking every {interval_seconds}s")
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_stocks, "interval", seconds=interval_seconds, id="stock_check")
    scheduler.start()

    # Run once immediately
    check_stocks()

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        log.info("Agent stopped.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stock Alert Agent")
    sub    = parser.add_subparsers(dest="cmd")

    p_add = sub.add_parser("add", help="Add a stock to watch")
    p_add.add_argument("ticker")
    p_add.add_argument("--threshold", type=float, default=1.0,
                       help="Alert when price rises by this %% (default: 1.0)")

    p_rm  = sub.add_parser("remove", help="Remove a stock")
    p_rm.add_argument("ticker")

    sub.add_parser("list",  help="List watched stocks")
    sub.add_parser("check", help="Run one price check now")

    p_run = sub.add_parser("run", help="Start the agent loop")
    p_run.add_argument("--interval", type=int, default=60,
                       help="Check interval in seconds (default: 60)")

    args = parser.parse_args()

    if   args.cmd == "add":    add_stock(args.ticker, args.threshold)
    elif args.cmd == "remove": remove_stock(args.ticker)
    elif args.cmd == "list":   list_stocks()
    elif args.cmd == "check":  check_stocks()
    elif args.cmd == "run":    run_agent(args.interval)
    else:
        parser.print_help()
