"""
Email Notifier — sends stock price alerts via Gmail SMTP.

Configure via a .env file (or environment variables):
    GMAIL_SENDER       Sender Gmail address   (required)
    GMAIL_APP_PASSWORD 16-char Gmail App Password — spaces are stripped (required)
    ALERT_EMAIL        Fallback recipient     (used only if no recipients are stored in state.json)
"""

import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_price_alert(
    symbol: str,
    old_price: float,
    new_price: float,
    change: float,
    change_pct: float,
    threshold: float = 1.0,
    recipients: list[str] | None = None,
) -> dict:
    """
    Send a price-change alert to one or more recipients via a single Gmail SMTP session.

    Parameters
    ----------
    recipients : list of email addresses to send to.
                 Falls back to ALERT_EMAIL env var (or GMAIL_SENDER) if empty/None.

    Returns
    -------
    dict with keys:
        subject   : the email subject line
        sent_to   : list of addresses the message was delivered to
        failed    : dict of {address: error_message} for any that failed
    """
    smtp_host     = "smtp.gmail.com"
    smtp_port     = 587

    # Prefer st.secrets (Streamlit Cloud), fall back to env vars (local .env)
    try:
        import streamlit as st
        smtp_user     = st.secrets.get("GMAIL_SENDER", os.getenv("GMAIL_SENDER", "")).strip()
        smtp_password = st.secrets.get("GMAIL_APP_PASSWORD", os.getenv("GMAIL_APP_PASSWORD", "")).replace(" ", "").strip()
    except Exception:
        smtp_user     = os.getenv("GMAIL_SENDER", "").strip()
        smtp_password = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()

    if not smtp_user or not smtp_password:
        raise ValueError(
            "Email not configured. Set GMAIL_SENDER and GMAIL_APP_PASSWORD in your .env file."
        )

    # Resolve recipient list — fall back to env/secrets if nothing passed in
    if not recipients:
        try:
            import streamlit as st
            fallback = st.secrets.get("ALERT_EMAIL", os.getenv("ALERT_EMAIL", smtp_user)).strip()
        except Exception:
            fallback = os.getenv("ALERT_EMAIL", smtp_user).strip()
        recipients = [fallback] if fallback else [smtp_user]

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_recipients: list[str] = []
    for addr in recipients:
        addr = addr.strip().lower()
        if addr and addr not in seen:
            seen.add(addr)
            unique_recipients.append(addr)

    if not unique_recipients:
        raise ValueError("No valid recipients — cannot send alert.")

    arrow     = "▲" if change >= 0 else "▼"
    direction = "UP" if change >= 0 else "DOWN"
    subject   = (
        f"[StockMCP Alert] {symbol} {arrow} ${abs(change):.2f} "
        f"({change_pct:+.2f}%) — Price is now ${new_price:.2f}"
    )

    body_plain = f"""\
Stock Price Alert — {symbol}
{'=' * 40}
Time           : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Symbol         : {symbol}
Previous Price : ${old_price:.2f}
Current Price  : ${new_price:.2f}
Change         : {arrow}  ${abs(change):.2f}  ({change_pct:+.2f}%)
Direction      : {direction}

This alert was triggered because the price moved by ${threshold:.2f} or more.

-- StockMCP Background Agent
"""

    body_html = f"""\
<html><body>
<h2 style="color:{'#16a34a' if change >= 0 else '#dc2626'}">
  {arrow} Stock Alert: {symbol}
</h2>
<table style="border-collapse:collapse;font-family:monospace">
  <tr><td style="padding:4px 12px"><b>Time</b></td>
      <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
  <tr><td style="padding:4px 12px"><b>Symbol</b></td>
      <td>{symbol}</td></tr>
  <tr><td style="padding:4px 12px"><b>Previous Price</b></td>
      <td>${old_price:.2f}</td></tr>
  <tr><td style="padding:4px 12px"><b>Current Price</b></td>
      <td><b>${new_price:.2f}</b></td></tr>
  <tr><td style="padding:4px 12px"><b>Change</b></td>
      <td style="color:{'#16a34a' if change >= 0 else '#dc2626'}">
        {arrow} ${abs(change):.2f} ({change_pct:+.2f}%)
      </td></tr>
</table>
<p style="color:#6b7280;font-size:12px">
  Triggered because the price moved ≥ ${threshold:.2f} — StockMCP Background Agent
</p>
</body></html>
"""

    msg = MIMEMultipart("alternative")
    msg["From"]    = smtp_user
    msg["To"]      = ", ".join(unique_recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body_plain, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    sent_to: list[str] = []
    failed:  dict[str, str] = {}

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_password)
        # sendmail returns a dict of {addr: (code, msg)} for addresses that were REFUSED
        refused = server.sendmail(smtp_user, unique_recipients, msg.as_string())
        for addr in unique_recipients:
            if addr in refused:
                failed[addr] = str(refused[addr])
            else:
                sent_to.append(addr)

    return {"subject": subject, "sent_to": sent_to, "failed": failed}
