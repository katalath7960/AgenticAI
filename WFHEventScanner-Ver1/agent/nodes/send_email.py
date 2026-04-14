"""SMTP email sender. Sends each attendee their barcode + QR invite."""

from __future__ import annotations

import logging
import os
import smtplib
import time
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from sqlalchemy import and_
from sqlalchemy.orm import Session

from api.database import SessionLocal
from api.models import Attendee
from agent.state import AgentState

logger = logging.getLogger(__name__)

SEND_THROTTLE_SECONDS = 0.5


def _smtp_config() -> dict:
    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from_email": os.getenv("FROM_EMAIL") or os.getenv("SMTP_USER", ""),
        "event_name": os.getenv("EVENT_NAME", "WFH Annual Event"),
    }


def _build_message(attendee: Attendee, barcode_path: Path, qr_path: Path, cfg: dict) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = f"Your entry pass for {cfg['event_name']}"
    msg["From"] = cfg["from_email"]
    msg["To"] = attendee.email

    text_body = (
        f"Hi {attendee.first_name},\n\n"
        f"You're invited to {cfg['event_name']}.\n"
        f"Your table color: {attendee.color}\n\n"
        "Please show the attached barcode (or QR code) at the entry desk for check-in.\n\n"
        "See you there!\n"
    )
    html_body = f"""\
<html><body style="font-family: Arial, sans-serif;">
  <h2>Hi {attendee.first_name},</h2>
  <p>You're invited to <strong>{cfg['event_name']}</strong>.</p>
  <p>Your table color: <strong style="color:{attendee.color.lower()};">{attendee.color}</strong></p>
  <p>Please present either code below at the entry desk:</p>
  <p><strong>Barcode:</strong><br><img src="cid:barcode_img" alt="barcode"></p>
  <p><strong>QR Code:</strong><br><img src="cid:qr_img" alt="qr"></p>
  <p>See you there!</p>
</body></html>
"""
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    with open(barcode_path, "rb") as f:
        msg.get_payload()[1].add_related(f.read(), "image", "png", cid="barcode_img")
    with open(qr_path, "rb") as f:
        msg.get_payload()[1].add_related(f.read(), "image", "png", cid="qr_img")

    return msg


def send_invite(attendee: Attendee, barcode_path: str | Path, qr_path: str | Path) -> bool:
    """Send one invite. Returns True on success, False on failure. Caller persists status."""
    cfg = _smtp_config()
    if not cfg["user"] or not cfg["password"]:
        logger.error("SMTP credentials not configured (SMTP_USER / SMTP_PASSWORD)")
        return False

    msg = _build_message(attendee, Path(barcode_path), Path(qr_path), cfg)

    try:
        with smtplib.SMTP(cfg["host"], cfg["port"]) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(cfg["user"], cfg["password"])
            smtp.send_message(msg)
        logger.info("sent invite to %s (sno=%s)", attendee.email, attendee.sno)
        return True
    except Exception as exc:
        logger.exception("send failed for sno=%s (%s): %s", attendee.sno, attendee.email, exc)
        return False


def send_all_invites(db: Session) -> dict:
    """Send invites to all Pending attendees with a barcode_path.

    Commits after each successful send so a crash is resumable.
    Returns { "sent": int, "failed": list[int] }.
    """
    pending = (
        db.query(Attendee)
        .filter(and_(Attendee.status == "Pending", Attendee.barcode_path.isnot(None)))
        .all()
    )

    sent = 0
    failed: list[int] = []
    for att in pending:
        barcode_path = Path(att.barcode_path)
        qr_path = barcode_path.parent / f"qr_{att.sno:04d}.png"
        if not barcode_path.exists() or not qr_path.exists():
            logger.error("missing artifacts for sno=%s", att.sno)
            failed.append(att.sno)
            continue

        ok = send_invite(att, barcode_path, qr_path)
        if ok:
            att.status = "Sent"
            att.email_sent_at = datetime.utcnow()
            db.add(att)
            db.commit()
            sent += 1
        else:
            failed.append(att.sno)

        time.sleep(SEND_THROTTLE_SECONDS)

    return {"sent": sent, "failed": failed}


def send_emails_node(state: AgentState) -> AgentState:
    errors = list(state.get("errors") or [])
    try:
        with SessionLocal() as db:
            result = send_all_invites(db)
        if result["failed"]:
            errors.append(f"emails failed: {result['failed']}")
        return {"emails_sent": result["sent"], "errors": errors}
    except Exception as exc:
        errors.append(f"send_emails: {exc}")
        return {"emails_sent": 0, "errors": errors}
