"""Scanner router: POST /api/scan."""

from __future__ import annotations

import re
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Attendee, ScanLog
from api.schemas import ScanRequest, ScanResult

router = APIRouter(prefix="/api", tags=["scanner"])

PAYLOAD_RE = re.compile(r"^WFH-(\d{4})-([A-Za-z]+)-([0-9a-f]{8})$")


@router.post("/scan", response_model=ScanResult)
def scan(req: ScanRequest, db: Session = Depends(get_db)):
    m = PAYLOAD_RE.match(req.payload.strip())
    if not m:
        raise HTTPException(status_code=400, detail="invalid barcode payload format")

    sno = int(m.group(1))
    att = db.query(Attendee).filter(Attendee.sno == sno).one_or_none()
    if not att:
        raise HTTPException(status_code=404, detail=f"attendee sno={sno} not found")

    today_start = datetime.combine(date.today(), datetime.min.time())
    prior = (
        db.query(ScanLog)
        .filter(ScanLog.attendee_id == att.id)
        .filter(ScanLog.scanned_at >= today_start)
        .filter(ScanLog.is_duplicate.is_(False))
        .first()
    )

    already_checked_in = prior is not None
    is_duplicate = already_checked_in

    db.add(ScanLog(
        attendee_id=att.id,
        scanned_by=req.scanned_by,
        is_duplicate=is_duplicate,
    ))

    message = "duplicate scan" if is_duplicate else "checked in"
    if not is_duplicate:
        att.status = "CheckedIn"
        att.checked_in_at = datetime.utcnow()
        db.add(att)

    db.commit()
    db.refresh(att)

    return ScanResult(
        duplicate=is_duplicate,
        already_checked_in=already_checked_in,
        attendee=att,
        message=message,
    )


@router.get("/scans")
def list_scans(limit: int = 50, db: Session = Depends(get_db)):
    """Recent scans (joined with attendee) for the scan-log UI."""
    rows = (
        db.query(ScanLog, Attendee)
        .join(Attendee, Attendee.id == ScanLog.attendee_id)
        .order_by(ScanLog.scanned_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": s.id,
            "scanned_at": s.scanned_at.isoformat(),
            "scanned_by": s.scanned_by,
            "is_duplicate": s.is_duplicate,
            "attendee_id": a.id,
            "sno": a.sno,
            "name": f"{a.first_name} {a.last_name}",
            "color": a.color,
        }
        for s, a in rows
    ]
