# Load Report

Measured on: local dev (Windows 11, Python 3.11, SQLite, SMTP mocked)

## Full agent run — 1,000 attendees

| Stage | Value |
|---|---|
| Rows imported | 1,000 |
| Barcodes generated | 1,000 (Code128 + QR PNGs) |
| Emails sent (mocked SMTP) | 1,000 |
| Wall time | **29.8 s** |

Real-world sends will be dominated by the 0.5 s SMTP throttle (`SEND_THROTTLE_SECONDS`) → ~8 min/1,000. That's well under the 15 min target; headroom exists to lower the throttle if the SMTP provider allows.

## Scan endpoint latency — 200 attendees seeded, sequential scans via TestClient

| Percentile | Latency |
|---|---|
| p95 | **14.3 ms** |
| p99 | **18.1 ms** |

Target was p95 < 200 ms — massive headroom. Over the wire (not TestClient) add ~1–5 ms.

## How to rerun

```bash
pytest tests/test_load.py -m slow -s
```

## Notes

- SMTP is mocked via `unittest.mock.patch('agent.nodes.send_email.smtplib.SMTP')`. Real runs will be slower due to network + throttle.
- SQLite is single-writer. For >10 concurrent scanners, migrate to Postgres.
- Barcode/QR PNGs are written to disk sequentially. If generation becomes a bottleneck, parallelize with `ProcessPoolExecutor`.
