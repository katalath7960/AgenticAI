from playwright.async_api import Page, Dialog

from utilities.logger import get_logger

log = get_logger(test="DialogHandler")


def register_dialog_handler(page: Page, auto_accept: bool = True) -> list[str]:
    """Register a dialog listener. Returns a list that collects dialog messages."""
    messages: list[str] = []

    async def _handler(dialog: Dialog):
        msg = dialog.message
        messages.append(f"[{dialog.type.upper()}] {msg}")
        log.info(f"Dialog [{dialog.type}]: {msg!r} — {'accepting' if auto_accept else 'dismissing'}")
        if auto_accept:
            await dialog.accept()
        else:
            await dialog.dismiss()

    page.on("dialog", _handler)
    return messages


async def wait_for_modal(page: Page, modal_selector: str = ".modal", timeout_ms: int = 10000) -> bool:
    try:
        await page.locator(modal_selector).wait_for(state="visible", timeout=timeout_ms)
        return True
    except Exception:
        return False


async def close_modal(page: Page, close_selector: str = ".modal .close, .modal [data-dismiss='modal']") -> None:
    try:
        btn = page.locator(close_selector).first
        if await btn.count() > 0:
            await btn.click()
    except Exception as e:
        log.warning(f"Could not close modal: {e}")
