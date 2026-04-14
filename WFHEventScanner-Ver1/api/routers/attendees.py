"""Attendees router: import, list, detail, barcode PNG."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api.database import get_db
from api.import_csv import import_attendees
from api.models import Attendee
from api.schemas import AttendeeRead, ImportSummary

router = APIRouter(prefix="/api/attendees", tags=["attendees"])


@router.post("/import", response_model=ImportSummary)
def import_from_csv(csv_path: str | None = None, db: Session = Depends(get_db)):
    path = csv_path or os.getenv("INPUT_CSV", "data/input/WFHAttendees.csv")
    try:
        return import_attendees(path, db)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=list[AttendeeRead])
def list_attendees(
    status: str | None = Query(None, description="Filter: Pending/Sent/CheckedIn"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Attendee)
    if status:
        q = q.filter(Attendee.status == status)
    return q.order_by(Attendee.sno).offset(offset).limit(limit).all()


@router.get("/{attendee_id}", response_model=AttendeeRead)
def get_attendee(attendee_id: int, db: Session = Depends(get_db)):
    att = db.get(Attendee, attendee_id)
    if not att:
        raise HTTPException(status_code=404, detail="attendee not found")
    return att


@router.post("/{attendee_id}/resend")
def resend_invite(attendee_id: int, db: Session = Depends(get_db)):
    from datetime import datetime
    from pathlib import Path

    from agent.nodes.send_email import send_invite

    att = db.get(Attendee, attendee_id)
    if not att:
        raise HTTPException(status_code=404, detail="attendee not found")
    if not att.barcode_path or not Path(att.barcode_path).exists():
        raise HTTPException(status_code=400, detail="barcode not generated yet")
    qr_path = Path(att.barcode_path).parent / f"qr_{att.sno:04d}.png"
    ok = send_invite(att, att.barcode_path, qr_path)
    if not ok:
        raise HTTPException(status_code=502, detail="email send failed")
    att.status = "Sent"
    att.email_sent_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "email": att.email, "email_sent_at": att.email_sent_at.isoformat()}


@router.get("/{attendee_id}/barcode")
def get_barcode_png(attendee_id: int, db: Session = Depends(get_db)):
    att = db.get(Attendee, attendee_id)
    if not att:
        raise HTTPException(status_code=404, detail="attendee not found")
    if not att.barcode_path or not Path(att.barcode_path).exists():
        raise HTTPException(status_code=404, detail="barcode not generated")
    return FileResponse(att.barcode_path, media_type="image/png")
