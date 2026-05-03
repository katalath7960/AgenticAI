"""Self-healing selectors — multiple strategies per element for resilience."""

from __future__ import annotations

from crawler.models import FormField, UIElement


class SelectorSet:
    def __init__(self, strategies: list[str]):
        self.strategies = strategies

    def resolve(self, page) -> str | None:
        for selector in self.strategies:
            try:
                el = page.query_selector(selector)
                if el:
                    return selector
            except Exception:
                continue
        return None


def build_selectors_for_field(field: FormField) -> SelectorSet:
    strategies = []
    if field.selector:
        strategies.append(field.selector)
    if field.name:
        strategies.append(f"[name='{field.name}']")
        strategies.append(f"input[name='{field.name}']")
    if field.label:
        strategies.append(f"text={field.label}")
    if field.placeholder:
        strategies.append(f"[placeholder='{field.placeholder}']")
    strategies.append(f"input[type='{field.field_type}']")
    return SelectorSet(strategies)


def build_selectors_for_element(element: UIElement) -> SelectorSet:
    strategies = []
    if element.selector:
        strategies.append(element.selector)
    if element.text:
        strategies.append(f"text={element.text}")
    if element.href:
        strategies.append(f"a[href='{element.href}']")
    strategies.append(element.tag)
    return SelectorSet(strategies)
