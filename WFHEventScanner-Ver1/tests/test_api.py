"""Integration tests for the FastAPI app."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.import_csv import import_attendees
from api.main import app
from api.models import Attendee
from agent.nodes.generate_barcode import build_payload, generate_all_barcodes


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def seeded(db, sample_csv, barcode_dir):
    import_attendees(sample_csv, db)
    generate_all_barcodes(db, output_dir=barcode_dir)
    return db


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_import_endpoint(client, sample_csv):
    r = client.post("/api/attendees/import", params={"csv_path": str(sample_csv)})
    assert r.status_code == 200
    body = r.json()
    assert body["imported"] == 3


def test_list_and_detail(client, seeded):
    r = client.get("/api/attendees")
    assert r.status_code == 200
    assert len(r.json()) == 3

    r = client.get("/api/attendees/1")
    assert r.status_code == 200

    r = client.get("/api/attendees/999")
    assert r.status_code == 404


def test_barcode_png_endpoint(client, seeded):
    r = client.get("/api/attendees/1/barcode")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_scan_happy_path_then_duplicate(client, seeded, db):
    att = db.query(Attendee).filter_by(sno=1).one()
    payload = build_payload({"sno": att.sno, "email": att.email, "color": att.color})

    r1 = client.post("/api/scan", json={"payload": payload, "scanned_by": "staff1"})
    assert r1.status_code == 200
    body = r1.json()
    assert body["duplicate"] is False
    assert body["attendee"]["status"] == "CheckedIn"

    r2 = client.post("/api/scan", json={"payload": payload, "scanned_by": "staff1"})
    assert r2.status_code == 200
    assert r2.json()["duplicate"] is True


def test_scan_invalid_payload(client):
    r = client.post("/api/scan", json={"payload": "garbage"})
    assert r.status_code == 400


def test_scan_unknown_sno(client, seeded):
    r = client.post("/api/scan", json={"payload": "WFH-9999-Blue-00000000"})
    assert r.status_code == 404


def test_stats_reflects_db(client, seeded, db):
    r = client.get("/api/stats")
    body = r.json()
    assert body["total"] == 3
    assert body["pending"] == 3
    assert body["checked_in"] == 0

    att = db.query(Attendee).filter_by(sno=2).one()
    payload = build_payload({"sno": att.sno, "email": att.email, "color": att.color})
    client.post("/api/scan", json={"payload": payload, "scanned_by": "staff1"})

    body = client.get("/api/stats").json()
    assert body["checked_in"] == 1
    assert body["scans_today"] >= 1


def test_request_id_roundtrip(client):
    r = client.get("/health", headers={"X-Request-ID": "abc123"})
    assert r.headers["x-request-id"] == "abc123"


def test_resend_endpoint_sends_then_updates_status(client, seeded, db):
    with patch("agent.nodes.send_email.smtplib.SMTP") as SMTP, \
         patch("agent.nodes.send_email.time.sleep"):
        SMTP.return_value.__enter__.return_value = MagicMock()
        r = client.post("/api/attendees/1/resend")
    assert r.status_code == 200
    assert db.get(Attendee, 1).status == "Sent"
