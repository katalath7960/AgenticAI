"""UI change detection — compare current DOM against a baseline."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from crawler.models import PageData

log = logging.getLogger("autotester")


def _fingerprint(page: PageData) -> dict:
    return {
        "url": page.url,
        "title": page.title,
        "form_count": len(page.forms),
        "fields": [
            {"name": f.name, "type": f.field_type, "required": f.required}
            for form in page.forms for f in form.fields
        ],
        "buttons": [b.text for b in page.buttons],
        "link_count": len(page.links),
        "heading_hash": hashlib.md5("|".join(page.headings).encode()).hexdigest(),
    }


def save_baseline(pages: list[PageData], baseline_path: Path) -> None:
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    data = {p.url: _fingerprint(p) for p in pages}
    baseline_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    log.info("Baseline saved: %d pages → %s", len(pages), baseline_path)


def detect_changes(pages: list[PageData], baseline_path: Path) -> list[dict]:
    if not baseline_path.exists():
        log.info("No baseline found — skipping diff")
        return []

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    changes: list[dict] = []

    for page in pages:
        fp = _fingerprint(page)
        old = baseline.get(page.url)
        if old is None:
            changes.append({"url": page.url, "change": "new_page"})
            continue
        diffs = []
        if fp["title"] != old["title"]:
            diffs.append(f"title: '{old['title']}' → '{fp['title']}'")
        if fp["form_count"] != old["form_count"]:
            diffs.append(f"forms: {old['form_count']} → {fp['form_count']}")
        if fp["fields"] != old["fields"]:
            diffs.append("form fields changed")
        if fp["heading_hash"] != old["heading_hash"]:
            diffs.append("headings changed")
        if fp["link_count"] != old["link_count"]:
            diffs.append(f"links: {old['link_count']} → {fp['link_count']}")
        if diffs:
            changes.append({"url": page.url, "change": "; ".join(diffs)})

    removed = set(baseline.keys()) - {p.url for p in pages}
    for url in removed:
        changes.append({"url": url, "change": "page_removed"})

    if changes:
        log.info("Detected %d changes since baseline", len(changes))
    return changes
