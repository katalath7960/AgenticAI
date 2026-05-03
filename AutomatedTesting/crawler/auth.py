"""Login / authentication handler — fills and submits detected login forms."""

from __future__ import annotations

import logging

from playwright.async_api import Page

from config.settings import LoginCredentials

log = logging.getLogger("autotester")


async def handle_login(page: Page, creds: LoginCredentials) -> bool:
    url = creds.login_url or page.url
    if creds.login_url:
        await page.goto(url, wait_until="networkidle", timeout=30_000)

    pw_field = await page.query_selector("input[type='password']")
    if not pw_field:
        log.warning("No password field found on %s — skipping login", url)
        return False

    form = await pw_field.evaluate_handle("el => el.closest('form')")
    user_field = await form.query_selector(
        "input[type='text'], input[type='email'], input[name='username'], input[name='email']"
    )
    if not user_field:
        log.warning("No username/email field found — skipping login")
        return False

    await user_field.fill(creds.username)
    await pw_field.fill(creds.password)

    submit = await form.query_selector("button[type='submit'], input[type='submit']")
    if submit:
        await submit.click()
    else:
        await pw_field.press("Enter")

    await page.wait_for_load_state("networkidle", timeout=15_000)
    log.info("Login submitted on %s", url)
    return True
