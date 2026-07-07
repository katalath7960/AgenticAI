"""Smart element resolution — tries semantic locators in priority order."""
from typing import Optional

from playwright.async_api import Page, Locator


_ROLE_MAP = {
    "button":   "button",
    "link":     "link",
    "checkbox": "checkbox",
    "radio":    "radio",
    "combobox": "combobox",
    "listbox":  "listbox",
    "textbox":  "textbox",
    "option":   "option",
    "tab":      "tab",
    "menuitem": "menuitem",
    "heading":  "heading",
}


async def resolve(
    page: Page,
    target: str,
    target_type: str = "any",
    *,
    visible_only: bool = True,
) -> Optional[Locator]:
    """
    Return the first resolvable, visible Playwright Locator for `target`.
    Tries strategies in priority order so absolute XPath is never needed.
    """
    if not target:
        return None

    candidates: list[Locator] = []

    # 1. ARIA role + accessible name
    role = _ROLE_MAP.get(target_type.lower())
    if role:
        candidates.append(page.get_by_role(role, name=target, exact=False))
    # Also try common roles regardless of target_type
    for r in ("button", "link", "textbox", "combobox", "checkbox", "radio"):
        if r != role:
            candidates.append(page.get_by_role(r, name=target, exact=False))

    # 2. Label association
    candidates.append(page.get_by_label(target, exact=False))

    # 3. Placeholder text
    candidates.append(page.get_by_placeholder(target, exact=False))

    # 4. Visible text
    candidates.append(page.get_by_text(target, exact=False))

    # 5. Attribute-based (partial, case-insensitive via contains-style selectors)
    safe = target.replace("'", "\\'")
    for attr in ("name", "id", "aria-label", "data-testid", "title", "value", "placeholder"):
        candidates.append(page.locator(f"[{attr}*='{safe}' i]"))

    # 6. Alt text (for images acting as buttons)
    candidates.append(page.get_by_alt_text(target, exact=False))

    for loc in candidates:
        try:
            count = await loc.count()
            if count == 0:
                continue
            first = loc.first
            if visible_only:
                if await first.is_visible():
                    return first
            else:
                return first
        except Exception:
            continue

    return None


async def resolve_all(page: Page, target: str, target_type: str = "any") -> list[Locator]:
    """Return ALL candidates that are visible — useful for tables or repeated elements."""
    results: list[Locator] = []
    loc = page.get_by_text(target, exact=False)
    try:
        count = await loc.count()
        for i in range(count):
            item = loc.nth(i)
            if await item.is_visible():
                results.append(item)
    except Exception:
        pass
    return results
