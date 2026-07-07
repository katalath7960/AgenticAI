"""All Playwright step action handlers. Each returns (success, actual_result, error)."""
import asyncio
from pathlib import Path
from typing import Optional

from playwright.async_api import Page, Locator, TimeoutError as PWTimeout
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from playwright_engine.wait_strategy import wait_for_navigation, smart_wait, wait_for_element
from utilities.config_loader import config
from utilities.logger import get_logger
from utilities.time_utils import now_str

log = get_logger(test="PageActions")

StepResult = tuple[bool, str, str]   # (success, actual_result, error)

_RETRY_COUNT = config.execution.retry_count
_RETRY_DELAY = config.execution.retry_delay_ms / 1000


# ─── Locator helpers ──────────────────────────────────────────────────────────

async def _resolve_locator(page: Page, target: str, target_type: str = "any") -> Optional[Locator]:
    """Try a ranked list of semantic locators; return the first visible one."""
    candidates: list[Locator] = []

    role_map = {
        "button": "button", "link": "link", "checkbox": "checkbox",
        "radio": "radio", "listbox": "listbox", "option": "option",
        "textbox": "textbox", "combobox": "combobox", "tab": "tab",
        "menuitem": "menuitem", "heading": "heading",
    }
    if target_type in role_map:
        candidates.append(page.get_by_role(role_map[target_type], name=target, exact=False))
    # Fallback role guesses
    for role in ("button", "link", "textbox", "combobox"):
        candidates.append(page.get_by_role(role, name=target, exact=False))

    candidates += [
        page.get_by_label(target, exact=False),
        page.get_by_placeholder(target, exact=False),
        page.get_by_text(target, exact=False),
        page.locator(f"[name*='{target}' i]"),
        page.locator(f"[id*='{target}' i]"),
        page.locator(f"[aria-label*='{target}' i]"),
        page.locator(f"[data-testid*='{target}' i]"),
        page.locator(f"[title*='{target}' i]"),
        page.locator(f"[value*='{target}' i]"),
    ]

    for loc in candidates:
        try:
            count = await loc.count()
            if count > 0:
                first = loc.first
                if await first.is_visible():
                    return first
        except Exception:
            continue
    return None


async def _safe_click(locator: Locator) -> None:
    try:
        await locator.click()
    except Exception:
        await locator.dispatch_event("click")


# ─── Login ────────────────────────────────────────────────────────────────────

async def login(page: Page, url: str, username: str, password: str) -> StepResult:
    try:
        await page.goto(url, wait_until="domcontentloaded")
        await wait_for_navigation(page)

        user_field = await _resolve_locator(page, "username", "textbox") or \
                     await _resolve_locator(page, "user", "textbox") or \
                     page.locator("input[type='text']").first
        await user_field.fill(username)

        pass_field = page.locator("input[type='password']").first
        await pass_field.fill(password)

        submit = await _resolve_locator(page, "login", "button") or \
                 await _resolve_locator(page, "sign in", "button") or \
                 page.locator("input[type='submit'], button[type='submit']").first
        await _safe_click(submit)

        await wait_for_navigation(page)
        await smart_wait(page)

        # Verify login by checking URL changed or dashboard element present
        if "login" in page.url.lower() or "signin" in page.url.lower():
            return False, "", "Login failed — still on login page after submit"

        return True, f"Logged in successfully. Current URL: {page.url}", ""
    except Exception as e:
        return False, "", f"Login error: {e}"


# ─── Click ────────────────────────────────────────────────────────────────────

async def click(page: Page, target: str, target_type: str = "any") -> StepResult:
    for attempt in range(_RETRY_COUNT):
        try:
            loc = await _resolve_locator(page, target, target_type)
            if not loc:
                await asyncio.sleep(_RETRY_DELAY)
                continue
            await _safe_click(loc)
            await smart_wait(page)
            return True, f"Clicked '{target}'", ""
        except Exception as e:
            if attempt == _RETRY_COUNT - 1:
                return False, "", f"Click '{target}' failed: {e}"
            await asyncio.sleep(_RETRY_DELAY)
    return False, "", f"Could not locate element to click: '{target}'"


# ─── Enter text ───────────────────────────────────────────────────────────────

async def enter_text(page: Page, target: str, value: str) -> StepResult:
    for attempt in range(_RETRY_COUNT):
        try:
            loc = await _resolve_locator(page, target, "textbox")
            if not loc:
                await asyncio.sleep(_RETRY_DELAY)
                continue
            await loc.clear()
            await loc.fill(value)
            return True, f"Entered '{value}' into '{target}'", ""
        except Exception as e:
            if attempt == _RETRY_COUNT - 1:
                return False, "", f"Enter text '{target}' failed: {e}"
            await asyncio.sleep(_RETRY_DELAY)
    return False, "", f"Could not locate text field: '{target}'"


# ─── Select dropdown ──────────────────────────────────────────────────────────

async def select_dropdown(page: Page, target: str, value: str) -> StepResult:
    for attempt in range(_RETRY_COUNT):
        try:
            loc = await _resolve_locator(page, target, "combobox")
            if not loc:
                loc = page.locator(f"select[name*='{target}' i], select[id*='{target}' i]").first
            if await loc.count() == 0:
                await asyncio.sleep(_RETRY_DELAY)
                continue
            tag = await loc.evaluate("el => el.tagName.toLowerCase()")
            if tag == "select":
                try:
                    await loc.select_option(label=value)
                except Exception:
                    await loc.select_option(value=value)
            else:
                # Custom dropdown — click to open then select by text
                await _safe_click(loc)
                await smart_wait(page)
                option = page.get_by_role("option", name=value, exact=False)
                if await option.count() == 0:
                    option = page.get_by_text(value, exact=False)
                await option.first.click()
            await smart_wait(page)
            return True, f"Selected '{value}' in '{target}'", ""
        except Exception as e:
            if attempt == _RETRY_COUNT - 1:
                return False, "", f"Select dropdown '{target}' failed: {e}"
            await asyncio.sleep(_RETRY_DELAY)
    return False, "", f"Could not locate dropdown: '{target}'"


# ─── Select radio ─────────────────────────────────────────────────────────────

async def select_radio(page: Page, target: str, value: str = "") -> StepResult:
    try:
        label = value or target
        loc = page.get_by_label(label, exact=False)
        if await loc.count() == 0:
            loc = page.locator(f"input[type='radio'][value*='{label}' i]")
        await loc.first.check()
        return True, f"Selected radio '{label}'", ""
    except Exception as e:
        return False, "", f"Radio select failed: {e}"


# ─── Check checkbox ───────────────────────────────────────────────────────────

async def check_checkbox(page: Page, target: str, check: bool = True) -> StepResult:
    try:
        loc = await _resolve_locator(page, target, "checkbox")
        if not loc:
            loc = page.locator(f"input[type='checkbox'][name*='{target}' i]").first
        if check:
            await loc.check()
        else:
            await loc.uncheck()
        action = "Checked" if check else "Unchecked"
        return True, f"{action} checkbox '{target}'", ""
    except Exception as e:
        return False, "", f"Checkbox '{target}' failed: {e}"


# ─── Upload file ──────────────────────────────────────────────────────────────

async def upload_file(page: Page, target: str, file_path: str) -> StepResult:
    try:
        loc = page.locator(f"input[type='file']")
        if target:
            labeled = await _resolve_locator(page, target, "any")
            if labeled:
                loc = labeled
        await loc.first.set_input_files(file_path)
        return True, f"Uploaded file '{file_path}' to '{target}'", ""
    except Exception as e:
        return False, "", f"File upload failed: {e}"


# ─── Download file ────────────────────────────────────────────────────────────

async def download_file(page: Page, target: str, save_folder: str = "downloads") -> StepResult:
    try:
        Path(save_folder).mkdir(parents=True, exist_ok=True)
        loc = await _resolve_locator(page, target, "link") or \
              await _resolve_locator(page, target, "button")
        if not loc:
            return False, "", f"Download link/button not found: '{target}'"
        async with page.expect_download() as dl_info:
            await _safe_click(loc)
        download = await dl_info.value
        save_path = f"{save_folder}/{download.suggested_filename or 'download_' + now_str()}"
        await download.save_as(save_path)
        return True, f"Downloaded to '{save_path}'", ""
    except Exception as e:
        return False, "", f"Download failed: {e}"


# ─── Handle date picker ───────────────────────────────────────────────────────

async def handle_date_picker(page: Page, target: str, date_value: str) -> StepResult:
    try:
        loc = await _resolve_locator(page, target, "textbox")
        if not loc:
            return False, "", f"Date field not found: '{target}'"
        input_type = await loc.get_attribute("type") or "text"
        if input_type == "date":
            await loc.fill(date_value)
        else:
            await loc.click()
            await loc.fill(date_value)
            await page.keyboard.press("Tab")
        return True, f"Set date '{date_value}' in '{target}'", ""
    except Exception as e:
        return False, "", f"Date picker failed: {e}"


# ─── Handle rich text editor ─────────────────────────────────────────────────

async def handle_rich_text(page: Page, target: str, content: str) -> StepResult:
    try:
        # Try contenteditable (TinyMCE body, CKEditor body)
        frames = page.frames
        for frame in frames:
            body = frame.locator("body[contenteditable='true']")
            if await body.count() > 0:
                await body.click()
                await body.fill(content)
                return True, f"Entered rich text in '{target}'", ""
        # Fallback: find by label
        loc = await _resolve_locator(page, target, "textbox")
        if loc:
            await loc.fill(content)
            return True, f"Entered text in '{target}'", ""
        return False, "", f"Rich text editor not found: '{target}'"
    except Exception as e:
        return False, "", f"Rich text failed: {e}"


# ─── Navigation ───────────────────────────────────────────────────────────────

async def navigate(page: Page, url: str) -> StepResult:
    try:
        await page.goto(url, wait_until="domcontentloaded")
        await wait_for_navigation(page)
        return True, f"Navigated to {page.url}", ""
    except Exception as e:
        return False, "", f"Navigation failed: {e}"


# ─── Save / Cancel ────────────────────────────────────────────────────────────

async def save(page: Page, target: str = "Save") -> StepResult:
    return await click(page, target, "button")


async def cancel(page: Page, target: str = "Cancel") -> StepResult:
    return await click(page, target, "button")


# ─── Validate text ────────────────────────────────────────────────────────────

async def validate_text(page: Page, target: str, expected: str) -> StepResult:
    try:
        loc = await _resolve_locator(page, target, "any")
        if loc:
            actual = (await loc.inner_text()).strip()
        else:
            actual = (await page.locator(f"text={expected}").inner_text()).strip()
        if expected.lower() in actual.lower():
            return True, f"Found '{expected}' in '{actual}'", ""
        return False, actual, f"Expected '{expected}' not found. Actual: '{actual}'"
    except Exception as e:
        return False, "", f"Validate text failed: {e}"


# ─── Validate URL ─────────────────────────────────────────────────────────────

async def validate_url(page: Page, expected: str) -> StepResult:
    actual = page.url
    if expected.lower() in actual.lower():
        return True, f"URL matches: {actual}", ""
    return False, actual, f"Expected URL to contain '{expected}', got '{actual}'"


# ─── Validate page title ──────────────────────────────────────────────────────

async def validate_title(page: Page, expected: str) -> StepResult:
    actual = await page.title()
    if expected.lower() in actual.lower():
        return True, f"Title: '{actual}'", ""
    return False, actual, f"Expected title '{expected}', got '{actual}'"


# ─── Validate field value ─────────────────────────────────────────────────────

async def validate_field_value(page: Page, target: str, expected: str) -> StepResult:
    try:
        loc = await _resolve_locator(page, target, "textbox")
        if not loc:
            return False, "", f"Field not found: '{target}'"
        actual = await loc.input_value()
        if expected.lower() in actual.lower():
            return True, f"Field '{target}' = '{actual}'", ""
        return False, actual, f"Expected '{expected}', got '{actual}'"
    except Exception as e:
        return False, "", f"Validate field value failed: {e}"


# ─── Validate table ───────────────────────────────────────────────────────────

async def validate_table(page: Page, target: str, expected_text: str) -> StepResult:
    try:
        selector = "table" if not target else f"table[id*='{target}' i], #{target}, .{target}"
        table = page.locator(selector).first
        if await table.count() == 0:
            table = page.locator("table").first
        html = await table.inner_text()
        if expected_text.lower() in html.lower():
            return True, f"Table contains '{expected_text}'", ""
        return False, html[:200], f"Table does not contain '{expected_text}'"
    except Exception as e:
        return False, "", f"Validate table failed: {e}"


# ─── Validate error message ───────────────────────────────────────────────────

async def validate_error_message(page: Page, expected: str) -> StepResult:
    selectors = [
        ".error", ".alert-danger", ".validation-error",
        "[class*='error']", "[class*='alert']", "[role='alert']",
        ".field-validation-error", ".text-danger",
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel)
            if await loc.count() > 0:
                text = (await loc.first.inner_text()).strip()
                if not expected or expected.lower() in text.lower():
                    return True, f"Error message found: '{text}'", ""
        except Exception:
            continue
    return False, "", f"Error message '{expected}' not found on page"


# ─── Validate mandatory fields ────────────────────────────────────────────────

async def validate_mandatory_fields(page: Page) -> StepResult:
    try:
        invalid = page.locator(":invalid, .field-validation-error, .required-error")
        count = await invalid.count()
        if count > 0:
            return True, f"{count} mandatory field error(s) displayed", ""
        return False, "0 errors", "No mandatory field validation errors found"
    except Exception as e:
        return False, "", f"Mandatory field validation check failed: {e}"


# ─── Validate navigation ──────────────────────────────────────────────────────

async def validate_navigation(page: Page, target_page: str) -> StepResult:
    await smart_wait(page)
    url_ok, url_actual, _ = await validate_url(page, target_page)
    if url_ok:
        return True, f"Navigated to '{target_page}': {url_actual}", ""
    title_ok, title_actual, _ = await validate_title(page, target_page)
    if title_ok:
        return True, f"Page title matches '{target_page}': {title_actual}", ""
    heading = page.get_by_role("heading", name=target_page, exact=False)
    if await heading.count() > 0:
        return True, f"Heading '{target_page}' found on page", ""
    return False, page.url, f"Page '{target_page}' not found. URL={page.url}"


# ─── Search ───────────────────────────────────────────────────────────────────

async def search_records(page: Page, search_text: str) -> StepResult:
    try:
        search_box = await _resolve_locator(page, "search", "textbox") or \
                     page.locator("input[type='search'], input[name*='search' i]").first
        await search_box.fill(search_text)
        btn = await _resolve_locator(page, "search", "button") or \
              page.locator("button[type='submit']").first
        await _safe_click(btn)
        await smart_wait(page)
        return True, f"Searched for '{search_text}'", ""
    except Exception as e:
        return False, "", f"Search failed: {e}"


# ─── Add / Edit / Delete record ───────────────────────────────────────────────

async def add_record(page: Page, target: str = "Add") -> StepResult:
    return await click(page, target, "button")


async def edit_record(page: Page, target: str = "Edit") -> StepResult:
    return await click(page, target, "button")


async def delete_record(page: Page, target: str = "Delete") -> StepResult:
    success, actual, err = await click(page, target, "button")
    if success:
        # Handle confirmation dialog if it appears
        await asyncio.sleep(0.5)
        confirm = await _resolve_locator(page, "ok", "button") or \
                  await _resolve_locator(page, "yes", "button") or \
                  await _resolve_locator(page, "confirm", "button")
        if confirm:
            await _safe_click(confirm)
        await smart_wait(page)
    return success, actual, err


# ─── Logout ───────────────────────────────────────────────────────────────────

async def logout(page: Page) -> StepResult:
    for label in ["logout", "log out", "sign out", "signout"]:
        loc = await _resolve_locator(page, label, "link")
        if not loc:
            loc = await _resolve_locator(page, label, "button")
        if loc:
            await _safe_click(loc)
            await wait_for_navigation(page)
            return True, "Logged out successfully", ""
    return False, "", "Logout link/button not found"


# ─── Screenshot ───────────────────────────────────────────────────────────────

async def take_screenshot(page: Page, folder: str, tc_id: str, step_idx: int, status: str) -> str:
    Path(folder).mkdir(parents=True, exist_ok=True)
    filename = f"{tc_id}_step{step_idx:02d}_{status}_{now_str()}.png"
    path = str(Path(folder) / filename)
    try:
        await page.screenshot(path=path, full_page=False)
        return path
    except Exception as e:
        log.warning(f"Screenshot failed: {e}")
        return ""


# ─── HTML snapshot ────────────────────────────────────────────────────────────

async def take_html_snapshot(page: Page, folder: str, tc_id: str) -> str:
    Path(folder).mkdir(parents=True, exist_ok=True)
    filename = f"{tc_id}_{now_str()}.html"
    path = str(Path(folder) / filename)
    try:
        content = await page.content()
        Path(path).write_text(content, encoding="utf-8")
        return path
    except Exception as e:
        log.warning(f"HTML snapshot failed: {e}")
        return ""
