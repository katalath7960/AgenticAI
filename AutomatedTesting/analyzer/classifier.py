"""AI-driven element classification — classifies each UI element by role."""

from __future__ import annotations

import json
import logging

from openai import OpenAI

from analyzer.models import ClassifiedElement, ElementRole
from crawler.models import PageData

log = logging.getLogger("autotester")

CLASSIFY_PROMPT = """\
You are a UI testing expert. Given the following HTML elements from a web page,
classify each element into one of these roles:
- Input: form fields, text inputs, checkboxes, file uploads
- Action: buttons, submit, cancel, toggles that trigger behavior
- Output: result displays, status messages, data tables
- Navigation: links, menus, tabs, breadcrumbs

Return a JSON array. Each item: {"selector": "...", "tag": "...", "text": "...", "role": "Input|Action|Output|Navigation", "confidence": 0.0-1.0}

Page URL: {url}
Page title: {title}

Elements:
{elements}
"""


def classify_elements(page: PageData, api_key: str, model: str = "gpt-4o-mini") -> list[ClassifiedElement]:
    elements_text = _build_elements_text(page)
    if not elements_text.strip():
        return _fallback_classify(page)

    if not api_key:
        log.info("No API key — using heuristic classification")
        return _fallback_classify(page)

    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a UI analysis assistant. Return only valid JSON."},
                {"role": "user", "content": CLASSIFY_PROMPT.format(
                    url=page.url, title=page.title, elements=elements_text
                )},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        data = json.loads(content)
        items = data if isinstance(data, list) else data.get("elements", [])
        return [ClassifiedElement(**item) for item in items]
    except Exception as exc:
        log.warning("AI classification failed (%s) — falling back to heuristics", exc)
        return _fallback_classify(page)


def _build_elements_text(page: PageData) -> str:
    lines = []
    for form in page.forms:
        for f in form.fields:
            lines.append(f"<input name='{f.name}' type='{f.field_type}' selector='{f.selector}'>")
        if form.submit_selector:
            lines.append(f"<button type='submit' selector='{form.submit_selector}'>")
    for btn in page.buttons:
        lines.append(f"<button text='{btn.text}' selector='{btn.selector}'>")
    for inp in page.inputs:
        lines.append(f"<input type='{inp.element_type}' placeholder='{inp.text}' selector='{inp.selector}'>")
    return "\n".join(lines[:100])


def _fallback_classify(page: PageData) -> list[ClassifiedElement]:
    result: list[ClassifiedElement] = []
    for form in page.forms:
        for f in form.fields:
            result.append(ClassifiedElement(
                selector=f.selector, tag="input", text=f.label or f.name, role=ElementRole.INPUT
            ))
        if form.submit_selector:
            result.append(ClassifiedElement(
                selector=form.submit_selector, tag="button", text="submit", role=ElementRole.ACTION
            ))
    for btn in page.buttons:
        result.append(ClassifiedElement(
            selector=btn.selector, tag="button", text=btn.text, role=ElementRole.ACTION
        ))
    for inp in page.inputs:
        result.append(ClassifiedElement(
            selector=inp.selector, tag="input", text=inp.text, role=ElementRole.INPUT
        ))
    return result
