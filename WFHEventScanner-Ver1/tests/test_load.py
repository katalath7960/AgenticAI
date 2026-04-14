"""Load check — marked slow, skipped by default.

TASK-038: time a full agent run on a 1,000-row synthetic CSV and assert the
scan endpoint's p95 latency stays under a threshold. Run with:

    pytest tests/test_load.py -m slow
"""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from agent.graph import build_graph
from agent.nodes.generate_barcode import build_payload
from api.main import app
from api.models import Attendee

pytestmark = pytest.mark.slow


def _synth_csv(path: Path, n: int) -> Path:
    colors = ["Blue", "Red", "Green", "Yellow", "Orange"]
    rows = [
        {"Sno": i, "FirstName": f"F{i}", "LastName": f"L{i}",
         "Color": colors[i % len(colors)], "EmailAddress": f"user{i}@example.com",
         "Status": "", "EventName": "Load Test"}
        for i in range(1, n + 1)
    ]
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_1k_agent_run(db, tmp_path, barcode_dir, monkeypatch):
    monkeypatch.setenv("BARCODE_OUTPUT_DIR", str(barcode_dir))
    csv = _synth_csv(tmp_path / "1k.csv", 1000)

    with patch("agent.nodes.send_email.smtplib.SMTP") as SMTP, \
         patch("agent.nodes.send_email.time.sleep"):   # no throttle in tests
        SMTP.return_value.__enter__.return_value = MagicMock()
        t0 = time.perf_counter()
        final = build_graph().invoke({"csv_path": str(csv), "errors": []})
        elapsed = time.perf_counter() - t0

    assert final["imported"] == 1000
    assert final["emails_sent"] == 1000
    print(f"\n[load] 1,000-row run: {elapsed:.1f}s")
    # very loose bound — adjust per host
    assert elapsed < 120, f"agent run too slow: {elapsed:.1f}s"


def test_scan_latency(db, tmp_path, barcode_dir, monkeypatch):
    monkeypatch.setenv("BARCODE_OUTPUT_DIR", str(barcode_dir))
    csv = _synth_csv(tmp_path / "200.csv", 200)

    with patch("agent.nodes.send_email.smtplib.SMTP") as SMTP, \
         patch("agent.nodes.send_email.time.sleep"):
        SMTP.return_value.__enter__.return_value = MagicMock()
        build_graph().invoke({"csv_path": str(csv), "errors": []})

    client = TestClient(app)
    payloads = [
        build_payload({"sno": a.sno, "email": a.email, "color": a.color})
        for a in db.query(Attendee).order_by(Attendee.sno).all()
    ]

    latencies: list[float] = []
    for p in payloads:
        t0 = time.perf_counter()
        r = client.post("/api/scan", json={"payload": p})
        latencies.append((time.perf_counter() - t0) * 1000)
        assert r.status_code == 200

    latencies.sort()
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    print(f"\n[load] scan latency  p95={p95:.1f}ms  p99={p99:.1f}ms")
    assert p95 < 500, f"p95 too high: {p95:.1f}ms"
