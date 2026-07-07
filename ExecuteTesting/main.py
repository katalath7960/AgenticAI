"""
AI-Powered Excel-Driven Test Automation Framework
Entry point: python main.py
"""
import asyncio
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from excel_reader.formatter import write_results
from excel_reader.reader import read_excel_folder
from executor.base_executor import TestExecutor
from playwright_engine.browser_manager import BrowserManager
from reports.html_reporter import generate_html
from reports.json_reporter import generate_json
from reports.pdf_reporter import generate_pdf
from utilities.config_loader import config
from utilities.logger import setup_logger, logger
from utilities.time_utils import ms_to_human, now_str, now_iso


def _build_run_meta(run_id: str, start: str, end: str, test_cases, excel_files: list) -> dict:
    total = len(test_cases)
    passed = sum(1 for tc in test_cases if tc.status == "PASS")
    failed = sum(1 for tc in test_cases if tc.status == "FAIL")
    skipped = sum(1 for tc in test_cases if tc.status in ("SKIP", "NOT RUN"))
    total_ms = sum(tc.execution_time_ms for tc in test_cases)
    pass_pct = round((passed / total * 100), 1) if total else 0.0

    return {
        "run_id": run_id,
        "start_time": start,
        "end_time": end,
        "url": config.app.url,
        "browser": config.browser.type,
        "excel_files": ", ".join(Path(f).name for f in excel_files),
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "pass_percentage": pass_pct,
        "pass_pct": pass_pct,
        "total_execution_time_ms": total_ms,
        "total_time_human": ms_to_human(total_ms),
    }


def _print_summary(meta: dict) -> None:
    print("\n" + "=" * 60)
    print("  TEST EXECUTION SUMMARY")
    print("=" * 60)
    print(f"  Run ID       : {meta['run_id']}")
    print(f"  Total        : {meta['total']}")
    print(f"  Passed       : {meta['passed']}")
    print(f"  Failed       : {meta['failed']}")
    print(f"  Skipped      : {meta['skipped']}")
    print(f"  Pass Rate    : {meta['pass_pct']}%")
    print(f"  Exec Time    : {meta['total_time_human']}")
    print("=" * 60 + "\n")


async def run() -> int:
    run_id = now_str()
    start_time = now_iso()

    setup_logger(config.paths.log_folder)
    logger.info(f"=== Test run started: {run_id} ===")
    logger.info(f"Target: {config.app.url}")
    logger.info(f"Excel folder: {config.paths.excel_folder}")

    # --- Phase 1: Read all test cases ---
    test_cases = read_excel_folder(config.paths.excel_folder)
    if not test_cases:
        logger.warning("No test cases found. Place .xlsx files in the configured excel_inputs/ folder.")
        return 0

    # Group by file for per-file write-back
    by_file: dict[str, list] = defaultdict(list)
    for tc in test_cases:
        by_file[tc.file_path].append(tc)

    excel_files = list(by_file.keys())
    logger.info(f"Loaded {len(test_cases)} test cases from {len(excel_files)} file(s)")

    # --- Phase 2: Execute all test cases ---
    executor = TestExecutor()
    async with BrowserManager() as bm:
        executed = await executor.execute_all(bm.page, test_cases)

    end_time = now_iso()

    # --- Phase 3: Write results back to Excel ---
    for file_path, cases in by_file.items():
        write_results(file_path, cases)

    # --- Phase 4: Build run metadata ---
    meta = _build_run_meta(run_id, start_time, end_time, executed, excel_files)

    # --- Phase 5: Generate reports ---
    report_folder = config.paths.report_folder
    html_path = generate_html(meta, executed, report_folder)
    generate_pdf(html_path, report_folder)
    generate_json(meta, executed, report_folder)

    # --- Phase 6: Print summary ---
    _print_summary(meta)
    logger.info(f"Reports saved to: {report_folder}")
    logger.info(f"=== Test run complete: {run_id} ===")

    return meta["failed"]   # exit code: 0 if all pass, N if N failures


if __name__ == "__main__":
    exit_code = asyncio.run(run())
    sys.exit(exit_code)
