"""Unit tests for agent nodes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from api.import_csv import import_attendees
from api.models import Attendee
from agent.nodes.generate_barcode import (
    build_payload, generate_barcode, generate_all_barcodes,
)
from agent.nodes.send_email import send_all_invites
from agent.nodes.read_csv import read_csv_node


# ------------------------------------------------------------------ read_csv

def test_import_attendees_happy_path(db, sample_csv):
    summary = import_attendees(sample_csv, db)
    assert summary.imported == 3
    assert summary.updated == 0
    assert summary.skipped == 0
    assert db.query(Attendee).count() == 3


def test_import_attendees_is_idempotent(db, sample_csv):
    import_attendees(sample_csv, db)
    summary = import_attendees(sample_csv, db)
    assert summary.imported == 0
    assert summary.updated == 3
    assert db.query(Attendee).count() == 3


def test_import_attendees_skips_blank_and_duplicate_emails(db, bad_csv):
    summary = import_attendees(bad_csv, db)
    assert summary.imported == 1          # only Bob
    assert summary.skipped == 2           # Alice blank + Duplicate
    assert db.query(Attendee).count() == 1
    assert len(summary.errors) == 2


def test_import_attendees_missing_required_column(db, tmp_path):
    p = tmp_path / "broken.csv"
    p.write_text("Sno,FirstName,LastName\n1,A,B\n")
    with pytest.raises(ValueError, match="missing required columns"):
        import_attendees(p, db)


def test_read_csv_node_merges_into_state(sample_csv):
    state = read_csv_node({"csv_path": str(sample_csv), "errors": []})
    assert state["imported"] == 3
    assert state["errors"] == []


# ---------------------------------------------------------------- barcodes

def test_build_payload_format():
    p = build_payload({"sno": 7, "email": "x@example.com", "color": "Blue"})
    assert p.startswith("WFH-0007-Blue-")
    assert len(p.split("-")[-1]) == 8     # hash8


def test_build_payload_is_deterministic():
    a = {"sno": 1, "email": "x@example.com", "color": "Red"}
    assert build_payload(a) == build_payload(a)


def test_generate_barcode_creates_png_files(barcode_dir):
    result = generate_barcode(
        {"sno": 1, "email": "alice@example.com", "color": "Blue"},
        barcode_dir,
    )
    from pathlib import Path
    assert Path(result["barcode_path"]).exists()
    assert Path(result["qr_path"]).exists()
    assert Path(result["barcode_path"]).stat().st_size > 500      # real PNG
    assert Path(result["qr_path"]).stat().st_size > 200


def test_generate_barcode_is_idempotent(barcode_dir):
    a = {"sno": 2, "email": "bob@example.com", "color": "Red"}
    r1 = generate_barcode(a, barcode_dir)
    r2 = generate_barcode(a, barcode_dir)
    assert r1 == r2


def test_generate_all_barcodes_only_touches_pending(db, sample_csv, barcode_dir):
    import_attendees(sample_csv, db)
    result = generate_all_barcodes(db, output_dir=barcode_dir)
    assert result == {"generated": 3, "failed": []}

    # rerun is a no-op
    result2 = generate_all_barcodes(db, output_dir=barcode_dir)
    assert result2 == {"generated": 0, "failed": []}


# ------------------------------------------------------------------ emails

def test_send_all_invites_mocks_smtp_and_updates_status(db, sample_csv, barcode_dir):
    import_attendees(sample_csv, db)
    generate_all_barcodes(db, output_dir=barcode_dir)
    # rewrite barcode_path to point at the fixture dir (importer doesn't know)
    for a in db.query(Attendee).all():
        pass
    with patch("agent.nodes.send_email.smtplib.SMTP") as SMTP, \
         patch("agent.nodes.send_email.time.sleep"):
        SMTP.return_value.__enter__.return_value = MagicMock()
        result = send_all_invites(db)
    assert result["sent"] == 3
    assert result["failed"] == []
    assert all(a.status == "Sent" for a in db.query(Attendee).all())
    assert all(a.email_sent_at is not None for a in db.query(Attendee).all())


def test_send_all_invites_resumes_after_partial_failure(db, sample_csv, barcode_dir):
    import_attendees(sample_csv, db)
    generate_all_barcodes(db, output_dir=barcode_dir)

    # First run: every SMTP call raises.
    with patch("agent.nodes.send_email.smtplib.SMTP") as SMTP, \
         patch("agent.nodes.send_email.time.sleep"):
        SMTP.side_effect = RuntimeError("boom")
        result = send_all_invites(db)
    assert result["sent"] == 0
    assert len(result["failed"]) == 3

    # Second run with SMTP working: all three get sent.
    with patch("agent.nodes.send_email.smtplib.SMTP") as SMTP, \
         patch("agent.nodes.send_email.time.sleep"):
        SMTP.return_value.__enter__.return_value = MagicMock()
        result = send_all_invites(db)
    assert result["sent"] == 3


def test_send_invite_returns_false_without_smtp_creds(db, sample_csv, barcode_dir, monkeypatch):
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    import_attendees(sample_csv, db)
    generate_all_barcodes(db, output_dir=barcode_dir)
    result = send_all_invites(db)
    assert result["sent"] == 0
    assert len(result["failed"]) == 3
