"""Form field analysis — detects login, search, validation constraints."""

from __future__ import annotations

from crawler.models import FormInfo
from analyzer.models import FormAnalysis


def analyze_form(form: FormInfo) -> FormAnalysis:
    field_types = {f.field_type for f in form.fields}
    field_names = {f.name.lower() for f in form.fields}

    is_login = "password" in field_types and len(form.fields) <= 4
    is_search = (
        len(form.fields) == 1
        and (form.fields[0].field_type == "search" or "search" in form.fields[0].name.lower())
    ) if form.fields else False

    return FormAnalysis(
        form=form,
        has_required_fields=any(f.required for f in form.fields),
        has_pattern_validation=any(f.pattern for f in form.fields),
        has_length_constraints=any(f.min_length or f.max_length for f in form.fields),
        field_count=len(form.fields),
        is_login_form=is_login,
        is_search_form=is_search,
    )
