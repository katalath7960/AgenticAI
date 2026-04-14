"""End-to-end smoke test: agent + API scan flow with mocked SMTP.

Covers TASK-037 without docker — runs the full graph (read_csv → barcodes → emails
→ update_status) against an isolated DB, then simulates staff scans via the API
and asserts state transitions.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from agent.graph import build_graph
from agent.nodes.generate_barcode import build_payload
from api.main import app
from api.models import Attendee


@pytest.fixture()
def five_row_csv(tmp_path) -> Path:
    rows = [
        {"Sno": i, "FirstName": f"First{i}", "LastName": f"Last{i}",
         "Color": ["Blue", "Red", "Green", "Yellow", "Orange"][i - 1],
         "EmailAddress": f"user{i}@example.com",
         "Status": "", "EventName": "WFH E2E Test"}
        for i in range(1, 6)
    ]
    p = tmp_path / "attendees.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    return p


def test_e2e_agent_run_then_scans(db, five_row_csv, barcode_dir, monkeypatch):
    monkeypatch.setenv("BARCODE_OUTPUT_DIR", str(barcode_dir))

    with patch("agent.nodes.send_email.smtplib.SMTP") as SMTP, \
         patch("agent.nodes.send_email.time.sleep"):
        smtp_ctx = MagicMock()
        SMTP.return_value.__enter__.return_value = smtp_ctx
        final = build_graph().invoke({"csv_path": str(five_row_csv), "errors": []})

    assert final["imported"] == 5
    assert final["barcodes_generated"] == 5
    assert final["emails_sent"] == 5
    assert smtp_ctx.send_message.call_count == 5

    # every row got a barcode PNG written
    assert len(list(barcode_dir.glob("barcode_*.png"))) == 5
    assert len(list(barcode_dir.glob("qr_*.png"))) == 5

    # Now simulate staff scans through the API
    client = TestClient(app)
    attendees = db.query(Attendee).order_by(Attendee.sno).all()
    for a in attendees:
        payload = build_payload({"sno": a.sno, "email": a.email, "color": a.color})
        r = client.post("/api/scan", json={"payload": payload, "scanned_by": "e2e"})
        assert r.status_code == 200
        assert r.json()["duplicate"] is False

    stats = client.get("/api/stats").json()
    assert stats["total"] == 5
    assert stats["checked_in"] == 5
    assert stats["scans_today"] == 5
