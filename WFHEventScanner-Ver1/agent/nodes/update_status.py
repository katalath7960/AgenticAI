"""LangGraph node: export processed roster to CSV + XLSX."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd

from api.database import SessionLocal
from api.models import Attendee
from agent.state import AgentState

logger = logging.getLogger(__name__)

PROCESSED_DIR = Path("data/processed")
CSV_NAME = "WFHAttendees_processed.csv"
XLSX_NAME = "WFHAttendees_processed.xlsx"


def export_processed_roster(output_dir: Path | None = None) -> dict:
    """Write the current attendees table to CSV + XLSX.

    Returns { "csv": str, "xlsx": str, "rows": int }.
    """
    out = Path(output_dir or os.getenv("PROCESSED_DIR", PROCESSED_DIR))
    out.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as db:
        rows = [
            {
                "Sno": a.sno,
                "FirstName": a.first_name,
                "LastName": a.last_name,
                "Email": a.email,
                "Color": a.color,
                "EventName": a.event_name,
                "Status": a.status,
                "BarcodePath": a.barcode_path or "",
                "EmailSentAt": a.email_sent_at.isoformat() if a.email_sent_at else "",
                "CheckedInAt": a.checked_in_at.isoformat() if a.checked_in_at else "",
            }
            for a in db.query(Attendee).order_by(Attendee.sno).all()
        ]

    df = pd.DataFrame(rows)
    csv_path = out / CSV_NAME
    xlsx_path = out / XLSX_NAME
    df.to_csv(csv_path, index=False)
    df.to_excel(xlsx_path, index=False, engine="openpyxl")

    return {"csv": str(csv_path), "xlsx": str(xlsx_path), "rows": len(rows)}


def update_status_node(state: AgentState) -> AgentState:
    errors = list(state.get("errors") or [])
    try:
        export_processed_roster()
    except Exception as exc:
        errors.append(f"update_status: {exc}")
    return {"errors": errors}
