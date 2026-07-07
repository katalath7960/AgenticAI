"""Executes all test cases from a single Excel file against the browser."""
import asyncio
import time
from pathlib import Path
from typing import List

from playwright.async_api import Page

from ai_engine.failure_analyzer import FailureAnalyzer
from ai_engine.flaky_detector import FlakyDetector
from ai_engine.step_interpreter import StepInterpreter, ActionSpec
from excel_reader.models import TestCase
from executor.step_dispatcher import dispatch
from playwright_engine import page_actions as pa
from playwright_engine.dialog_handler import register_dialog_handler
from playwright_engine.wait_strategy import smart_wait
from utilities.config_loader import config
from utilities.logger import get_logger

log = get_logger(test="Executor")


class TestExecutor:
    def __init__(self):
        self._interpreter = StepInterpreter()
        self._analyzer = FailureAnalyzer()
        self._flaky = FlakyDetector()
        self._ss_folder = config.paths.screenshot_folder
        self._snap_folder = str(Path(config.paths.log_folder) / "html_snapshots")

    async def execute_all(self, page: Page, test_cases: List[TestCase]) -> List[TestCase]:
        register_dialog_handler(page, auto_accept=True)

        # Login once before all test cases
        log.info("Performing initial login")
        success, actual, err = await pa.login(
            page,
            config.app.url,
            config.app.username,
            config.app.password,
        )
        if not success:
            log.error(f"Login failed: {err}")
            for tc in test_cases:
                tc.status = "SKIP"
                tc.actual_result = "Skipped — login failed"
                tc.error_message = err
            return test_cases

        for tc in test_cases:
            await self._run_one(page, tc)

        return test_cases

    async def _run_one(self, page: Page, tc: TestCase) -> None:
        log = get_logger(test=tc.tc_id, step=tc.test_case_name[:40])
        log.info(f"Starting: {tc.test_case_name}")
        start = time.monotonic()

        steps_raw = tc.steps.strip()
        # Support multi-line steps (one per line) or a single step
        step_lines = [s.strip() for s in steps_raw.splitlines() if s.strip()]
        if not step_lines:
            step_lines = [steps_raw]

        overall_pass = True
        step_results: list[str] = []

        for idx, raw_step in enumerate(step_lines, start=1):
            log.info(f"  Step {idx}: {raw_step!r}")
            spec: ActionSpec = self._interpreter.interpret(raw_step)

            # Special handling: login step mid-suite
            if spec.action == "login":
                ok, act, err = await pa.login(
                    page, config.app.url,
                    config.app.username, config.app.password
                )
            else:
                ok, act, err = await dispatch(page, spec)

            await smart_wait(page)
            console_errs = []  # drained at BrowserManager level

            if ok:
                step_results.append(f"Step {idx} PASS: {act}")
                if config.execution.screenshot_on_pass:
                    await pa.take_screenshot(page, self._ss_folder, tc.tc_id, idx, "PASS")
            else:
                overall_pass = False
                step_results.append(f"Step {idx} FAIL: {err}")
                # Screenshot on failure
                if config.execution.screenshot_on_fail:
                    path = await pa.take_screenshot(page, self._ss_folder, tc.tc_id, idx, "FAIL")
                    tc.screenshot_path = path
                # HTML snapshot on critical failures
                if config.execution.html_snapshot_on_critical:
                    tc.html_snapshot_path = await pa.take_html_snapshot(
                        page, self._snap_folder, tc.tc_id
                    )
                # AI failure analysis
                analysis = self._analyzer.analyze(
                    raw_step, err, page.url, await page.title()
                )
                tc.failure_analysis = analysis.to_str()

                if not config.execution.continue_on_failure:
                    break

        elapsed_ms = int((time.monotonic() - start) * 1000)
        tc.execution_time_ms = elapsed_ms
        tc.status = "PASS" if overall_pass else "FAIL"
        tc.actual_result = " | ".join(step_results)
        tc.error_message = " | ".join(r for r in step_results if "FAIL" in r)

        self._flaky.record(tc.tc_id, tc.status)
        tc.is_flaky = self._flaky.is_flaky(tc.tc_id)

        flag = "[FLAKY]" if tc.is_flaky else ""
        log.info(f"  Result: {tc.status} {flag} ({elapsed_ms}ms)")
