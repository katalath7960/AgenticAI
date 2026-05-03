"""Main analysis pipeline — enriches crawled SiteMap into SiteAnalysis."""

from __future__ import annotations

import logging

from analyzer.classifier import classify_elements
from analyzer.forms import analyze_form
from analyzer.models import PageAnalysis, SiteAnalysis
from crawler.models import SiteMap

log = logging.getLogger("autotester")


def analyze_site(site_map: SiteMap, api_key: str = "", ai_model: str = "gpt-4o-mini") -> SiteAnalysis:
    pages: list[PageAnalysis] = []
    total_forms = 0
    total_apis = 0

    for page in site_map.pages:
        form_analyses = [analyze_form(f) for f in page.forms]
        classified = classify_elements(page, api_key=api_key, model=ai_model)
        api_endpoints = list({c.url for c in page.api_calls})

        risk = _compute_risk(page, form_analyses)

        pa = PageAnalysis(
            url=page.url,
            title=page.title,
            headings=page.headings,
            meta_description=page.meta_description,
            form_analyses=form_analyses,
            classified_elements=classified,
            error_messages=page.error_containers,
            success_messages=page.success_containers,
            internal_links=page.links,
            api_endpoints=api_endpoints,
            screenshot_path=page.screenshot_path,
            risk_score=risk,
        )
        pages.append(pa)
        total_forms += len(form_analyses)
        total_apis += len(api_endpoints)

    log.info("Analysis complete: %d pages, %d forms, %d API endpoints", len(pages), total_forms, total_apis)

    return SiteAnalysis(
        root_url=site_map.root_url,
        pages=pages,
        total_forms=total_forms,
        total_api_endpoints=total_apis,
        broken_links=site_map.broken_links,
    )


def _compute_risk(page, form_analyses) -> float:
    score = 0.0
    for fa in form_analyses:
        if fa.is_login_form:
            score += 3.0
        if fa.has_required_fields:
            score += 1.0
        score += fa.field_count * 0.3
    score += len(page.api_calls) * 0.5
    return round(min(score, 10.0), 1)
