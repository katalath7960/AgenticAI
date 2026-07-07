"""Routes an ActionSpec to the correct Playwright handler."""
from playwright.async_api import Page

from ai_engine.step_interpreter import ActionSpec
import playwright_engine.page_actions as pa
from utilities.logger import get_logger

log = get_logger(test="Dispatcher")

StepResult = tuple[bool, str, str]


async def dispatch(page: Page, spec: ActionSpec, download_folder: str = "downloads") -> StepResult:
    a = spec.action
    t = spec.target
    v = spec.value

    handlers = {
        "login":                   lambda: pa.login(page, "", "", ""),    # login handled separately
        "logout":                  lambda: pa.logout(page),
        "navigate":                lambda: pa.navigate(page, v or t),
        "click":                   lambda: pa.click(page, t, spec.target_type),
        "enter_text":              lambda: pa.enter_text(page, t, v or ""),
        "select_dropdown":         lambda: pa.select_dropdown(page, t, v or ""),
        "select_radio":            lambda: pa.select_radio(page, t, v),
        "check_checkbox":          lambda: pa.check_checkbox(page, t, True),
        "upload_file":             lambda: pa.upload_file(page, t, v or ""),
        "download_file":           lambda: pa.download_file(page, t, download_folder),
        "search_records":          lambda: pa.search_records(page, v or t),
        "add_record":              lambda: pa.add_record(page, t or "Add"),
        "edit_record":             lambda: pa.edit_record(page, t or "Edit"),
        "delete_record":           lambda: pa.delete_record(page, t or "Delete"),
        "save":                    lambda: pa.save(page, t or "Save"),
        "cancel":                  lambda: pa.cancel(page, t or "Cancel"),
        "validate_text":           lambda: pa.validate_text(page, t, v or t),
        "validate_url":            lambda: pa.validate_url(page, v or t),
        "validate_title":          lambda: pa.validate_title(page, v or t),
        "validate_field_value":    lambda: pa.validate_field_value(page, t, v or ""),
        "validate_table":          lambda: pa.validate_table(page, t, v or ""),
        "validate_error_message":  lambda: pa.validate_error_message(page, v or t),
        "validate_mandatory_fields": lambda: pa.validate_mandatory_fields(page),
        "validate_navigation":     lambda: pa.validate_navigation(page, v or t),
        "handle_date_picker":      lambda: pa.handle_date_picker(page, t, v or ""),
        "handle_rich_text":        lambda: pa.handle_rich_text(page, t, v or ""),
    }

    handler = handlers.get(a)
    if not handler:
        msg = f"Unknown action: '{a}' (step: {spec.raw_step!r})"
        log.warning(msg)
        return False, "", msg

    log.info(f"Dispatching: {a}({t!r}, value={v!r})")
    return await handler()
