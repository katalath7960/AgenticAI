"""Barcode + QR generation for attendees."""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

import barcode
import qrcode
from barcode.writer import ImageWriter
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.database import SessionLocal
from api.models import Attendee
from agent.state import AgentState

logger = logging.getLogger(__name__)


def build_payload(attendee: dict) -> str:
    """Stable encoded string: WFH-{sno:04d}-{color}-{email_hash8}."""
    email = str(attendee["email"]).strip().lower()
    email_hash8 = hashlib.sha1(email.encode("utf-8")).hexdigest()[:8]
    color = str(attendee["color"]).strip().replace(" ", "")
    return f"WFH-{int(attendee['sno']):04d}-{color}-{email_hash8}"


def generate_barcode(attendee: dict, output_dir: Path) -> dict:
    """Generate Code128 + QR PNGs for one attendee.

    Returns { "payload": str, "barcode_path": str, "qr_path": str }.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sno = int(attendee["sno"])
    payload = build_payload(attendee)

    code128 = barcode.get_barcode_class("code128")
    bc = code128(payload, writer=ImageWriter())
    barcode_stem = output_dir / f"barcode_{sno:04d}"
    barcode_path = Path(bc.save(str(barcode_stem)))

    qr_path = output_dir / f"qr_{sno:04d}.png"
    qr_img = qrcode.make(payload)
    qr_img.save(str(qr_path))

    return {
        "payload": payload,
        "barcode_path": str(barcode_path),
        "qr_path": str(qr_path),
    }


def generate_all_barcodes(db: Session, output_dir: Path | None = None) -> dict:
    """Generate barcodes for every Pending attendee missing a barcode_path.

    Returns { "generated": int, "failed": list[int] }. Commits per-row.
    """
    output_dir = Path(output_dir or os.getenv("BARCODE_OUTPUT_DIR", "data/output/barcodes"))
    output_dir.mkdir(parents=True, exist_ok=True)

    pending = (
        db.query(Attendee)
        .filter(Attendee.status == "Pending")
        .filter(or_(Attendee.barcode_path.is_(None), Attendee.barcode_path == ""))
        .all()
    )

    generated = 0
    failed: list[int] = []
    for att in pending:
        try:
            result = generate_barcode(
                {"sno": att.sno, "email": att.email, "color": att.color},
                output_dir,
            )
            att.barcode_path = result["barcode_path"]
            db.add(att)
            db.commit()
            generated += 1
        except Exception as exc:
            db.rollback()
            failed.append(att.sno)
            logger.exception("barcode generation failed for sno=%s: %s", att.sno, exc)

    return {"generated": generated, "failed": failed}


def generate_barcodes_node(state: AgentState) -> AgentState:
    errors = list(state.get("errors") or [])
    try:
        with SessionLocal() as db:
            result = generate_all_barcodes(db)
        if result["failed"]:
            errors.append(f"barcodes failed: {result['failed']}")
        return {"barcodes_generated": result["generated"], "errors": errors}
    except Exception as exc:
        errors.append(f"generate_barcodes: {exc}")
        return {"barcodes_generated": 0, "errors": errors}
