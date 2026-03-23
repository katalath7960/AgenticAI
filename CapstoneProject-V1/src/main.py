"""
src/main.py — CLI entry point.
Usage: python -m src.main [--data-dir PATH] [--output-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

from src.graph.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Feedback Intelligence Pipeline")
    parser.add_argument("--data-dir",   default=None, help="Override DATA_DIR from .env")
    parser.add_argument("--output-dir", default=None, help="Override OUTPUT_DIR from .env")
    parser.add_argument("--dry-run",    action="store_true",
                        help="Classify only; do not write ticket CSV or ChromaDB upserts")
    args = parser.parse_args()

    t0 = time.time()
    result = run_pipeline(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
    )
    elapsed_ms = int((time.time() - t0) * 1000)

    metrics = result.get("metrics", {})
    tickets = result.get("tickets", [])
    qc_results = result.get("qc_results", [])
    errors = result.get("errors", [])
    qc_pass = sum(1 for q in qc_results if q.passed)

    print("\n" + "=" * 60)
    print(f"  Pipeline Run Complete — {result.get('run_id', '')[:8]}")
    print("=" * 60)
    print(f"  Total items processed : {metrics.get('total_items', len(result.get('feedback_items', [])))}")
    print(f"  Bugs                  : {metrics.get('Bug', 0)}")
    print(f"  Feature Requests      : {metrics.get('Feature Request', 0)}")
    print(f"  Praise                : {metrics.get('Praise', 0)}")
    print(f"  Complaints            : {metrics.get('Complaint', 0)}")
    print(f"  Spam                  : {metrics.get('Spam', 0)}")
    print(f"  Tickets created       : {len(tickets)}")
    print(f"  QC pass rate          : {qc_pass}/{len(qc_results)}")
    print(f"  Errors                : {len(errors)}")
    print(f"  Elapsed               : {elapsed_ms:,} ms")
    if args.dry_run:
        print("  [DRY RUN — no files written]")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
