"""DOM element extraction — forms, buttons, inputs, links, headings."""

from __future__ import annotations

import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from crawler.models import FormField, FormInfo, PageData, UIElement

log = logging.getLogger("autotester")


def extract_page_data(html: str, url: str) -> PageData:
    soup = BeautifulSoup(html, "lxml")
    return PageData(
        url=url,
        title=_title(soup),
        headings=_headings(soup),
        meta_description=_meta_desc(soup),
        forms=_forms(soup, url),
        links=_links(soup, url),
        buttons=_buttons(soup),
        inputs=_standalone_inputs(soup),
        dropdowns=_dropdowns(soup),
        images=_images(soup),
        error_containers=_message_containers(soup, kind="error"),
        success_containers=_message_containers(soup, kind="success"),
        html_snippet=str(soup.body)[:5000] if soup.body else "",
    )


def _title(soup: BeautifulSoup) -> str:
    t = soup.find("title")
    return t.get_text(strip=True) if t else ""


def _headings(soup: BeautifulSoup) -> list[str]:
    return [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])]


def _meta_desc(soup: BeautifulSoup) -> str:
    tag = soup.find("meta", attrs={"name": "description"})
    return tag["content"] if tag and tag.get("content") else ""


def _css_selector(tag: Tag) -> str:
    parts = [tag.name]
    if tag.get("id"):
        return f"#{tag['id']}"
    for cls in (tag.get("class") or [])[:2]:
        parts.append(f".{cls}")
    if tag.get("name"):
        parts.append(f"[name='{tag['name']}']")
    return "".join(parts)


def _forms(soup: BeautifulSoup, base_url: str) -> list[FormInfo]:
    results = []
    for form in soup.find_all("form"):
        fields = []
        for inp in form.find_all(["input", "textarea", "select"]):
            if inp.get("type") == "hidden":
                continue
            label_tag = None
            if inp.get("id"):
                label_tag = soup.find("label", attrs={"for": inp["id"]})
            options = [o.get_text(strip=True) for o in inp.find_all("option")] if inp.name == "select" else []
            fields.append(FormField(
                name=inp.get("name", ""),
                field_type=inp.get("type", "text") if inp.name != "textarea" else "textarea",
                required=inp.has_attr("required"),
                placeholder=inp.get("placeholder", ""),
                label=label_tag.get_text(strip=True) if label_tag else "",
                pattern=inp.get("pattern", ""),
                min_length=_int_attr(inp, "minlength"),
                max_length=_int_attr(inp, "maxlength"),
                min_value=inp.get("min", ""),
                max_value=inp.get("max", ""),
                options=options,
                selector=_css_selector(inp),
            ))

        submit = form.find(["button", "input"], attrs={"type": "submit"})
        results.append(FormInfo(
            action=urljoin(base_url, form.get("action", "")),
            method=(form.get("method") or "GET").upper(),
            fields=fields,
            submit_selector=_css_selector(submit) if submit else "",
            selector=_css_selector(form),
        ))
    return results


def _links(soup: BeautifulSoup, base_url: str) -> list[str]:
    seen = set()
    out = []
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        if href not in seen and not href.startswith(("javascript:", "mailto:", "tel:")):
            seen.add(href)
            out.append(href)
    return out


def _buttons(soup: BeautifulSoup) -> list[UIElement]:
    return [
        UIElement(tag="button", text=b.get_text(strip=True), element_type=b.get("type", "button"), selector=_css_selector(b))
        for b in soup.find_all("button")
    ]


def _standalone_inputs(soup: BeautifulSoup) -> list[UIElement]:
    results = []
    for inp in soup.find_all("input"):
        if inp.find_parent("form") or inp.get("type") == "hidden":
            continue
        results.append(UIElement(tag="input", text=inp.get("placeholder", ""), element_type=inp.get("type", "text"), selector=_css_selector(inp)))
    return results


def _dropdowns(soup: BeautifulSoup) -> list[UIElement]:
    results = []
    for sel in soup.find_all("select"):
        if sel.find_parent("form"):
            continue
        results.append(UIElement(tag="select", text=sel.get("name", ""), selector=_css_selector(sel)))
    return results


def _images(soup: BeautifulSoup) -> list[UIElement]:
    return [
        UIElement(tag="img", text=img.get("alt", ""), attributes={"src": img.get("src", "")}, selector=_css_selector(img))
        for img in soup.find_all("img")[:50]
    ]


def _message_containers(soup: BeautifulSoup, kind: str = "error") -> list[str]:
    selectors = {
        "error": [".error", ".alert-danger", ".invalid-feedback", "[role='alert']", ".form-error"],
        "success": [".success", ".alert-success", ".valid-feedback", ".form-success"],
    }
    found = []
    for sel in selectors.get(kind, []):
        for el in soup.select(sel):
            text = el.get_text(strip=True)
            if text:
                found.append(text)
    return found


def _int_attr(tag: Tag, attr: str):
    val = tag.get(attr)
    if val and val.isdigit():
        return int(val)
    return None
