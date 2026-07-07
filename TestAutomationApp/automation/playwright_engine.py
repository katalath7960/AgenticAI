"""Core Playwright browser and page interaction layer."""
import asyncio
from pathlib import Path
from typing import Optional

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    TimeoutError as PWTimeout,
)

from automation.locator_manager import resolve
from datetime import datetime


# ─── Browser lifecycle ────────────────────────────────────────────────────────

class BrowserSession:
    def __init__(self, browser_type: str = "chromium", headless: bool = False,
                 timeout_ms: int = 30000):
        self.browser_type = browser_type.lower()
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._pw: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.console_errors: list[str] = []

    async def start(self):
        self._pw = await async_playwright().start()
        launcher = getattr(self._pw, self.browser_type, None)
        if launcher is None:
            launcher = self._pw.chromium
        self.browser = await launcher.launch(
            headless=self.headless,
            args=["--start-maximized", "--disable-infobars"],
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True,
            ignore_https_errors=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        )
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.timeout_ms)
        self.page.on("console", self._on_console)
        self.context.on("page", self._on_new_page)

    async def stop(self):
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self._pw:
                await self._pw.stop()
        except Exception:
            pass

    def _on_console(self, msg):
        if msg.type in ("error", "warning"):
            self.console_errors.append(f"[{msg.type.upper()}] {msg.text}")

    def _on_new_page(self, new_page: Page):
        new_page.set_default_timeout(self.timeout_ms)

    def drain_errors(self) -> list[str]:
        errs = list(self.console_errors)
        self.console_errors.clear()
        return errs


# ─── Waits ────────────────────────────────────────────────────────────────────

async def smart_wait(page: Page, timeout_ms: int = 30000) -> None:
    try:
        await page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 8000))
    except PWTimeout:
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except PWTimeout:
            pass
    # Dismiss any loading spinners
    for sel in [".loading", ".spinner", ".loader", "[aria-busy='true']", ".overlay"]:
        try:
            loc = page.locator(sel)
            if await loc.count() > 0:
                await loc.wait_for(state="hidden", timeout=5000)
        except Exception:
            pass


# ─── Safe click ───────────────────────────────────────────────────────────────

async def safe_click(loc) -> None:
    try:
        await loc.click()
    except Exception:
        try:
            await loc.dispatch_event("click")
        except Exception:
            await loc.evaluate("el => el.click()")


# ─── Action handlers ──────────────────────────────────────────────────────────

StepResult = tuple[bool, str, str]   # (ok, actual_result, error)


async def do_login(page: Page, url: str, username: str, password: str) -> StepResult:
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await smart_wait(page)

        # Find username field
        user_field = (
            await resolve(page, "username", "textbox") or
            await resolve(page, "user name", "textbox") or
            await resolve(page, "user id", "textbox") or
            await resolve(page, "email", "textbox") or
            page.locator("input[type='text'], input[type='email']").first
        )
        await user_field.fill(username)

        # Find password field
        pass_field = page.locator("input[type='password']").first
        await pass_field.fill(password)

        # Find submit button
        submit = (
            await resolve(page, "login", "button") or
            await resolve(page, "sign in", "button") or
            await resolve(page, "log in", "button") or
            await resolve(page, "submit", "button") or
            page.locator("button[type='submit'], input[type='submit']").first
        )
        await safe_click(submit)
        await smart_wait(page)

        if "login" in page.url.lower() and username.lower() not in (await page.content()).lower():
            return False, "", "Login failed — still on login page"
        return True, f"Logged in. URL: {page.url}", ""
    except Exception as e:
        return False, "", f"Login error: {e}"


async def do_logout(page: Page) -> StepResult:
    for label in ["logout", "log out", "sign out", "signout"]:
        loc = await resolve(page, label, "link") or await resolve(page, label, "button")
        if loc:
            await safe_click(loc)
            await smart_wait(page)
            return True, "Logged out", ""
    return False, "", "Logout element not found"


async def do_click(page: Page, target: str, target_type: str = "any") -> StepResult:
    for _ in range(3):
        loc = await resolve(page, target, target_type)
        if loc:
            await safe_click(loc)
            await smart_wait(page)
            return True, f"Clicked '{target}'", ""
        await asyncio.sleep(0.8)
    return False, "", f"Element not found: '{target}'"


async def do_enter_text(page: Page, target: str, value: str) -> StepResult:
    for _ in range(3):
        loc = await resolve(page, target, "textbox")
        if loc:
            await loc.clear()
            await loc.fill(value)
            return True, f"Entered '{value}' into '{target}'", ""
        await asyncio.sleep(0.8)
    return False, "", f"Text field not found: '{target}'"


async def do_select_dropdown(page: Page, target: str, value: str) -> StepResult:
    for _ in range(3):
        loc = await resolve(page, target, "combobox")
        if not loc:
            loc_raw = page.locator(
                f"select[name*='{target}' i], select[id*='{target}' i], select[aria-label*='{target}' i]"
            ).first
            if await loc_raw.count() > 0:
                loc = loc_raw
        if loc:
            tag = await loc.evaluate("el => el.tagName.toLowerCase()")
            if tag == "select":
                try:
                    await loc.select_option(label=value)
                except Exception:
                    try:
                        await loc.select_option(value=value)
                    except Exception:
                        await loc.select_option(index=1)
            else:
                await safe_click(loc)
                await asyncio.sleep(0.3)
                opt = page.get_by_role("option", name=value, exact=False)
                if await opt.count() == 0:
                    opt = page.get_by_text(value, exact=False)
                await opt.first.click()
            await smart_wait(page)
            return True, f"Selected '{value}' from '{target}'", ""
        await asyncio.sleep(0.8)
    return False, "", f"Dropdown not found: '{target}'"


async def do_select_radio(page: Page, target: str, value: str = "") -> StepResult:
    try:
        label = value or target
        loc = page.get_by_label(label, exact=False)
        if await loc.count() == 0:
            loc = page.locator(f"input[type='radio'][value*='{label}' i]")
        await loc.first.check()
        return True, f"Selected radio '{label}'", ""
    except Exception as e:
        return False, "", f"Radio error: {e}"


async def do_check_checkbox(page: Page, target: str, check: bool = True) -> StepResult:
    try:
        loc = await resolve(page, target, "checkbox")
        if not loc:
            loc = page.locator(f"input[type='checkbox'][name*='{target}' i]").first
        if check:
            await loc.check()
        else:
            await loc.uncheck()
        return True, f"{'Checked' if check else 'Unchecked'} '{target}'", ""
    except Exception as e:
        return False, "", f"Checkbox error: {e}"


async def do_upload_file(page: Page, target: str, file_path: str) -> StepResult:
    try:
        loc = page.locator("input[type='file']").first
        await loc.set_input_files(file_path)
        return True, f"Uploaded '{file_path}'", ""
    except Exception as e:
        return False, "", f"Upload error: {e}"


async def do_download_file(page: Page, target: str, save_folder: str = "downloads") -> StepResult:
    try:
        Path(save_folder).mkdir(parents=True, exist_ok=True)
        loc = await resolve(page, target, "link") or await resolve(page, target, "button")
        if not loc:
            return False, "", f"Download element not found: '{target}'"
        async with page.expect_download() as dl_info:
            await safe_click(loc)
        dl = await dl_info.value
        path = str(Path(save_folder) / (dl.suggested_filename or f"download_{int(asyncio.get_event_loop().time())}.bin"))
        await dl.save_as(path)
        return True, f"Downloaded to '{path}'", ""
    except Exception as e:
        return False, "", f"Download error: {e}"


async def do_navigate(page: Page, url: str) -> StepResult:
    try:
        await page.goto(url, wait_until="domcontentloaded")
        await smart_wait(page)
        return True, f"Navigated to {page.url}", ""
    except Exception as e:
        return False, "", f"Navigation error: {e}"


async def do_search(page: Page, search_text: str) -> StepResult:
    try:
        box = (
            await resolve(page, "search", "textbox") or
            page.locator("input[type='search'], input[name*='search' i], input[placeholder*='search' i]").first
        )
        await box.fill(search_text)
        btn = (
            await resolve(page, "search", "button") or
            page.locator("button[type='submit']").first
        )
        await safe_click(btn)
        await smart_wait(page)
        return True, f"Searched '{search_text}'", ""
    except Exception as e:
        return False, "", f"Search error: {e}"


async def do_save(page: Page, target: str = "Save") -> StepResult:
    return await do_click(page, target, "button")


async def do_cancel(page: Page, target: str = "Cancel") -> StepResult:
    return await do_click(page, target, "button")


async def do_add_record(page: Page, target: str = "Add") -> StepResult:
    return await do_click(page, target, "button")


async def do_edit_record(page: Page, target: str = "Edit") -> StepResult:
    return await do_click(page, target, "button")


async def do_delete_record(page: Page, target: str = "Delete") -> StepResult:
    ok, actual, err = await do_click(page, target, "button")
    if ok:
        await asyncio.sleep(0.5)
        for label in ["ok", "yes", "confirm", "delete"]:
            confirm = await resolve(page, label, "button")
            if confirm:
                await safe_click(confirm)
                break
        await smart_wait(page)
    return ok, actual, err


async def do_validate_text(page: Page, target: str, expected: str) -> StepResult:
    try:
        loc = await resolve(page, target, "any")
        actual = (await loc.inner_text()).strip() if loc else ""
        if not actual:
            # Search the entire page
            txt_loc = page.get_by_text(expected, exact=False)
            if await txt_loc.count() > 0:
                return True, f"Text '{expected}' found on page", ""
        if expected.lower() in actual.lower():
            return True, f"Validated: '{actual}'", ""
        return False, actual, f"Expected '{expected}', found '{actual}'"
    except Exception as e:
        return False, "", f"Validate text error: {e}"


async def do_validate_url(page: Page, expected: str) -> StepResult:
    actual = page.url
    if expected.lower() in actual.lower():
        return True, f"URL: {actual}", ""
    return False, actual, f"Expected URL contains '{expected}', got '{actual}'"


async def do_validate_title(page: Page, expected: str) -> StepResult:
    actual = await page.title()
    if expected.lower() in actual.lower():
        return True, f"Title: '{actual}'", ""
    return False, actual, f"Expected title '{expected}', got '{actual}'"


async def do_validate_error_message(page: Page, expected: str = "") -> StepResult:
    selectors = [
        ".error", ".alert-danger", "[class*='error']", "[role='alert']",
        ".validation-error", ".field-validation-error", ".text-danger",
        ".alert-error", "[class*='alert']",
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel)
            if await loc.count() > 0:
                text = (await loc.first.inner_text()).strip()
                if not expected or expected.lower() in text.lower():
                    return True, f"Error message: '{text}'", ""
        except Exception:
            continue
    return False, "", f"Error message '{expected}' not found"


async def do_validate_navigation(page: Page, target: str) -> StepResult:
    await smart_wait(page)
    ok, actual, _ = await do_validate_url(page, target)
    if ok:
        return ok, actual, ""
    ok2, actual2, _ = await do_validate_title(page, target)
    if ok2:
        return ok2, actual2, ""
    h = page.get_by_role("heading", name=target, exact=False)
    if await h.count() > 0:
        return True, f"Heading '{target}' found", ""
    return False, page.url, f"Navigation to '{target}' not confirmed"


async def do_date_picker(page: Page, target: str, value: str) -> StepResult:
    try:
        loc = await resolve(page, target, "textbox")
        if not loc:
            return False, "", f"Date field not found: '{target}'"
        input_type = await loc.get_attribute("type") or "text"
        if input_type == "date":
            await loc.fill(value)
        else:
            await loc.click()
            await loc.fill(value)
            await page.keyboard.press("Escape")
        return True, f"Set date '{value}' in '{target}'", ""
    except Exception as e:
        return False, "", f"Date picker error: {e}"


async def do_handle_modal(page: Page, action: str = "accept") -> StepResult:
    try:
        modal_btn = page.locator(
            ".modal .btn-primary, .modal [data-action='confirm'], .modal button:visible"
        ).first
        if await modal_btn.count() > 0:
            await safe_click(modal_btn)
            await smart_wait(page)
            return True, "Modal handled", ""
        return False, "", "No modal button found"
    except Exception as e:
        return False, "", f"Modal error: {e}"


# ─── Evidence capture ─────────────────────────────────────────────────────────

async def take_screenshot(page: Page, folder: str, tc_id: str, step_idx: int, status: str) -> str:
    Path(folder).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{tc_id}_step{step_idx:02d}_{status}_{ts}.png"
    path = str(Path(folder) / filename)
    try:
        await page.screenshot(path=path, full_page=False)
        return path
    except Exception:
        return ""
