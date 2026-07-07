"""
Orchestrates test execution. Interprets steps, calls playwright_engine handlers,
captures evidence, and streams progress via a queue.Queue.
"""
import asyncio
import json
import queue
import re
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from excel.excel_reader import TestCase
import automation.playwright_engine as pe
from automation.playwright_engine import BrowserSession


# ─── Step interpretation (keyword + optional AI) ──────────────────────────────

_KEYWORD_RULES = [
    # action, regex, fn(match) -> (action_key, target, value)
    (r"\b(login|log in|sign in)\b",                      "login",           lambda m: ("login",           "", None)),
    (r"\b(logout|log out|sign out)\b",                   "logout",          lambda m: ("logout",          "", None)),
    (r"\bnavigate\s+to\s+(.+)",                          "navigate",        lambda m: ("navigate",        m.group(1).strip(), None)),
    (r"\benter\s+(?:text\s+)?['\"](.+?)['\"].*?in\s+(?:the\s+)?(.+)",
                                                          "enter_text",      lambda m: ("enter_text",      m.group(2).strip(), m.group(1).strip())),
    (r"\btype\s+['\"](.+?)['\"].*?in(?:to)?\s+(?:the\s+)?(.+)",
                                                          "enter_text",      lambda m: ("enter_text",      m.group(2).strip(), m.group(1).strip())),
    (r"\benter\s+(.+?)\s+in(?:to)?\s+(?:the\s+)?(.+)",  "enter_text",      lambda m: ("enter_text",      m.group(2).strip(), m.group(1).strip())),
    (r"\bselect\s+['\"]?(.+?)['\"]?\s+(?:from|in)\s+(?:the\s+)?(.+)",
                                                          "select_dropdown", lambda m: ("select_dropdown", m.group(2).strip(), m.group(1).strip())),
    (r"\bcheck\s+(?:the\s+)?(.+?)\s+checkbox",           "checkbox",        lambda m: ("check_checkbox",  m.group(1).strip(), None)),
    (r"\buncheck\s+(?:the\s+)?(.+?)\s+checkbox",         "uncheck",         lambda m: ("uncheck_checkbox",m.group(1).strip(), None)),
    (r"\bselect\s+(?:radio\s+)?(.+)",                    "radio",           lambda m: ("select_radio",    m.group(1).strip(), None)),
    (r"\bupload\s+(?:file\s+)?(.+)",                     "upload",          lambda m: ("upload_file",     m.group(1).strip(), None)),
    (r"\bdownload\s+(.+)",                               "download",        lambda m: ("download_file",   m.group(1).strip(), None)),
    (r"\bsearch\s+(?:for\s+)?['\"]?(.+?)['\"]?\s*$",    "search",          lambda m: ("search_records",  m.group(1).strip(), None)),
    (r"\badd\s+(?:new\s+)?(?:record|case|entry|item)",   "add_record",      lambda m: ("add_record",      "Add", None)),
    (r"\bedit\s+(?:record|case|entry)",                  "edit_record",     lambda m: ("edit_record",     "Edit", None)),
    (r"\bdelete\s+(?:record|case|entry)",                "delete_record",   lambda m: ("delete_record",   "Delete", None)),
    (r"\bsave\b",                                        "save",            lambda m: ("save",            "Save", None)),
    (r"\bcancel\b",                                      "cancel",          lambda m: ("cancel",          "Cancel", None)),
    (r"\bvalidate\s+(?:page\s+)?title\s+(?:contains?\s+)?['\"]?(.+?)['\"]?\s*$",
                                                          "val_title",       lambda m: ("validate_title",  "", m.group(1).strip())),
    (r"\bvalidate\s+(?:the\s+)?url\s+(?:contains?\s+)?['\"]?(.+?)['\"]?\s*$",
                                                          "val_url",         lambda m: ("validate_url",    "", m.group(1).strip())),
    (r"\bvalidate\s+(?:error|validation)\s+message",     "val_error",       lambda m: ("validate_error_message", "", None)),
    (r"\bvalidate\s+mandatory\s+fields?",                "val_mandatory",   lambda m: ("validate_mandatory", "", None)),
    (r"\bvalidate\s+(?:table|grid)\s*(.+)?",             "val_table",       lambda m: ("validate_table",  m.group(1) or "", None)),
    (r"\bvalidate\s+(?:navigation|page)\s+(?:to\s+)?(.+)",
                                                          "val_nav",         lambda m: ("validate_navigation", m.group(1).strip(), None)),
    (r"\bvalidate\s+(.+)",                               "validate",        lambda m: ("validate_text",   m.group(1).strip(), None)),
    (r"\bclick\s+(?:the\s+)?(?:menu\s+)?(.+)",          "click",           lambda m: ("click",           m.group(1).strip(), None)),
]


def interpret_step(step: str) -> dict:
    """Return {action, target, value, target_type} from a natural language step."""
    lower = step.lower().strip()
    for pattern, _, fn in _KEYWORD_RULES:
        m = re.search(pattern, lower)
        if m:
            try:
                action, target, value = fn(m)
                return {"action": action, "target": target, "value": value, "target_type": "any"}
            except Exception:
                continue
    # Fallback: generic click on the whole text
    return {"action": "click", "target": step.strip(), "value": None, "target_type": "any"}


def _ai_interpret(step: str, client, model: str) -> dict:
    """Use Claude to interpret a step; returns same dict format as interpret_step."""
    system = """You are a test automation interpreter. Return ONLY valid JSON:
{"action":"<action>","target":"<ui_element>","value":"<value_or_null>","target_type":"<button|link|textbox|dropdown|checkbox|radio|any>"}
Actions: login,logout,navigate,click,enter_text,select_dropdown,select_radio,check_checkbox,upload_file,download_file,search_records,add_record,edit_record,delete_record,save,cancel,validate_text,validate_url,validate_title,validate_error_message,validate_navigation"""
    try:
        resp = client.messages.create(
            model=model, max_tokens=256, system=system,
            messages=[{"role": "user", "content": step}]
        )
        raw = resp.content[0].text.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw).rstrip("`").strip()
        return json.loads(raw)
    except Exception:
        return interpret_step(step)


# ─── Dispatcher ───────────────────────────────────────────────────────────────

async def _dispatch(page, spec: dict, ss_folder: str, dl_folder: str) -> pe.StepResult:
    a = spec["action"]
    t = spec.get("target", "")
    v = spec.get("value") or ""
    tt = spec.get("target_type", "any")

    # if/elif used instead of match to support Python 3.9+
    if a == "login":                    return await pe.do_login(page, "", "", "")
    elif a == "logout":                 return await pe.do_logout(page)
    elif a == "navigate":               return await pe.do_navigate(page, v or t)
    elif a == "click":                  return await pe.do_click(page, t, tt)
    elif a == "enter_text":             return await pe.do_enter_text(page, t, v)
    elif a == "select_dropdown":        return await pe.do_select_dropdown(page, t, v)
    elif a == "select_radio":           return await pe.do_select_radio(page, t, v)
    elif a == "check_checkbox":         return await pe.do_check_checkbox(page, t, True)
    elif a == "uncheck_checkbox":       return await pe.do_check_checkbox(page, t, False)
    elif a == "upload_file":            return await pe.do_upload_file(page, t, v or t)
    elif a == "download_file":          return await pe.do_download_file(page, t, dl_folder)
    elif a == "search_records":         return await pe.do_search(page, v or t)
    elif a == "add_record":             return await pe.do_add_record(page, t or "Add")
    elif a == "edit_record":            return await pe.do_edit_record(page, t or "Edit")
    elif a == "delete_record":          return await pe.do_delete_record(page, t or "Delete")
    elif a == "save":                   return await pe.do_save(page, t or "Save")
    elif a == "cancel":                 return await pe.do_cancel(page, t or "Cancel")
    elif a == "validate_text":          return await pe.do_validate_text(page, t, v or t)
    elif a == "validate_url":           return await pe.do_validate_url(page, v or t)
    elif a == "validate_title":         return await pe.do_validate_title(page, v or t)
    elif a == "validate_error_message": return await pe.do_validate_error_message(page, v or t)
    elif a == "validate_navigation":    return await pe.do_validate_navigation(page, v or t)
    elif a == "validate_table":         return await pe.do_validate_text(page, t, v or t)
    else:                               return await pe.do_click(page, t or a, tt)


# ─── Executor ─────────────────────────────────────────────────────────────────

def _msg(type_: str, **kw) -> dict:
    return {"type": type_, "ts": datetime.now().strftime("%H:%M:%S"), **kw}


class TestExecutor:
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        browser_type: str = "chromium",
        headless: bool = False,
        timeout_ms: int = 30000,
        screenshot_on_fail: bool = True,
        screenshot_on_pass: bool = False,
        continue_on_failure: bool = True,
        ai_api_key: str = "",
        ai_model: str = "claude-sonnet-4-6",
        screenshot_folder: str = "screenshots",
    ):
        self.url = url
        self.username = username
        self.password = password
        self.browser_type = browser_type
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.ss_on_fail = screenshot_on_fail
        self.ss_on_pass = screenshot_on_pass
        self.continue_on_failure = continue_on_failure
        self.ss_folder = screenshot_folder
        self.dl_folder = "downloads"
        self._ai_client = None
        self._ai_model = ai_model
        if ai_api_key:
            try:
                import anthropic
                self._ai_client = anthropic.Anthropic(api_key=ai_api_key)
            except Exception:
                pass

    async def run(
        self,
        test_cases: List[TestCase],
        progress_q: queue.Queue,
    ) -> List[TestCase]:
        total = len(test_cases)
        progress_q.put(_msg("start", message=f"Starting {total} test cases", total=total))

        session = BrowserSession(self.browser_type, self.headless, self.timeout_ms)
        await session.start()
        page = session.page

        # Register dialog auto-accept
        page.on("dialog", lambda d: asyncio.ensure_future(d.accept()))

        try:
            # Login once
            progress_q.put(_msg("log", message="Performing login...", level="INFO"))
            ok, actual, err = await pe.do_login(page, self.url, self.username, self.password)
            if not ok:
                progress_q.put(_msg("log", message=f"Login FAILED: {err}", level="ERROR"))
                for tc in test_cases:
                    tc.status = "SKIP"
                    tc.actual_result = "Skipped — login failed"
                    tc.error_details = err
                    tc.executed_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return test_cases
            progress_q.put(_msg("log", message="Login successful", level="SUCCESS"))

            for idx, tc in enumerate(test_cases, start=1):
                progress_q.put(_msg(
                    "tc_start",
                    message=f"[{idx}/{total}] {tc.tc_id}: {tc.test_case_name}",
                    tc_id=tc.tc_id,
                    progress=idx / total,
                ))
                await self._execute_tc(page, session, tc, progress_q)
                status_sym = "✅" if tc.status == "PASS" else ("⏭️" if tc.status == "SKIP" else "❌")
                progress_q.put(_msg(
                    "tc_done",
                    message=f"{status_sym} {tc.tc_id}: {tc.status} ({tc.execution_time})",
                    tc_id=tc.tc_id,
                    status=tc.status,
                    progress=idx / total,
                ))
        finally:
            await session.stop()

        progress_q.put(_msg("done", message="Execution complete"))
        return test_cases

    async def _execute_tc(
        self,
        page,
        session: BrowserSession,
        tc: TestCase,
        progress_q: queue.Queue,
    ) -> None:
        start_ms = time.monotonic()
        tc.executed_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        step_lines = [s.strip() for s in tc.steps.splitlines() if s.strip()]
        if not step_lines:
            step_lines = [tc.steps.strip()]

        all_pass = True
        step_results: list[str] = []
        first_error = ""
        first_ss = ""

        for i, raw_step in enumerate(step_lines, start=1):
            progress_q.put(_msg(
                "step",
                message=f"  → Step {i}: {raw_step}",
                tc_id=tc.tc_id,
                step_num=i,
            ))

            # Interpret step
            spec = (_ai_interpret(raw_step, self._ai_client, self._ai_model)
                    if self._ai_client else interpret_step(raw_step))

            # Handle login step specially
            if spec["action"] == "login":
                ok, act, err = await pe.do_login(page, self.url, self.username, self.password)
            else:
                ok, act, err = await _dispatch(page, spec, self.ss_folder, self.dl_folder)

            await pe.smart_wait(page, self.timeout_ms)

            level = "SUCCESS" if ok else "ERROR"
            progress_q.put(_msg(
                "step_result",
                message=f"    {'PASS' if ok else 'FAIL'}: {act or err}",
                tc_id=tc.tc_id,
                step_num=i,
                level=level,
            ))

            if ok:
                step_results.append(f"Step {i} PASS: {act}")
                if self.ss_on_pass:
                    await pe.take_screenshot(page, self.ss_folder, tc.tc_id, i, "PASS")
            else:
                all_pass = False
                step_results.append(f"Step {i} FAIL: {err}")
                if not first_error:
                    first_error = err
                if self.ss_on_fail and not first_ss:
                    first_ss = await pe.take_screenshot(page, self.ss_folder, tc.tc_id, i, "FAIL")
                if not self.continue_on_failure:
                    break

        elapsed_ms = int((time.monotonic() - start_ms) * 1000)
        tc.status = "PASS" if all_pass else "FAIL"
        tc.actual_result = " | ".join(step_results)
        tc.error_details = first_error
        tc.screenshot = first_ss
        tc.execution_time = f"{elapsed_ms}ms"


# ─── Thread entry point ───────────────────────────────────────────────────────

def run_in_thread(
    test_cases: List[TestCase],
    url: str,
    username: str,
    password: str,
    browser_type: str,
    headless: bool,
    timeout_ms: int,
    screenshot_on_fail: bool,
    screenshot_on_pass: bool,
    continue_on_failure: bool,
    ai_api_key: str,
    screenshot_folder: str,
    progress_q: queue.Queue,
    result_holder: dict,
):
    """Called from a background thread; creates its own asyncio event loop."""
    executor = TestExecutor(
        url=url,
        username=username,
        password=password,
        browser_type=browser_type,
        headless=headless,
        timeout_ms=timeout_ms,
        screenshot_on_fail=screenshot_on_fail,
        screenshot_on_pass=screenshot_on_pass,
        continue_on_failure=continue_on_failure,
        ai_api_key=ai_api_key,
        screenshot_folder=screenshot_folder,
    )

    async def _run():
        result_holder["results"] = await executor.run(test_cases, progress_q)

    # On Windows, Playwright requires the ProactorEventLoop (default in 3.10+).
    # Explicitly set the policy so it is correct on all Windows Python versions.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    try:
        asyncio.run(_run())
    except Exception as e:
        tb = traceback.format_exc()
        # First line: exception type + short message (always single line)
        short = f"{type(e).__name__}: {e}".split("\n")[0].strip() or repr(e)
        result_holder["error"] = tb
        progress_q.put(_msg("error", message=f"Fatal error — {short}", level="ERROR"))
        # Emit each traceback line separately so they render in the log panel
        for line in tb.splitlines():
            if line.strip():
                progress_q.put(_msg("log", message=f"  {line}", level="ERROR"))
    finally:
        if "results" not in result_holder:
            result_holder["results"] = test_cases
        progress_q.put(_msg("done", message="Thread finished"))
