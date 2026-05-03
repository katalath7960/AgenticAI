"""Enriched analysis models — semantic layer on top of raw page data."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from crawler.models import FormInfo, PageData


class ElementRole(str, Enum):
    INPUT = "Input"
    ACTION = "Action"
    OUTPUT = "Output"
    NAVIGATION = "Navigation"


class ClassifiedElement(BaseModel):
    selector: str
    tag: str
    text: str = ""
    role: ElementRole
    confidence: float = 1.0


class FormAnalysis(BaseModel):
    form: FormInfo
    has_required_fields: bool = False
    has_pattern_validation: bool = False
    has_length_constraints: bool = False
    field_count: int = 0
    is_login_form: bool = False
    is_search_form: bool = False


class PageAnalysis(BaseModel):
    url: str
    title: str = ""
    headings: list[str] = Field(default_factory=list)
    meta_description: str = ""
    form_analyses: list[FormAnalysis] = Field(default_factory=list)
    classified_elements: list[ClassifiedElement] = Field(default_factory=list)
    error_messages: list[str] = Field(default_factory=list)
    success_messages: list[str] = Field(default_factory=list)
    internal_links: list[str] = Field(default_factory=list)
    api_endpoints: list[str] = Field(default_factory=list)
    screenshot_path: str = ""
    risk_score: float = 0.0


class SiteAnalysis(BaseModel):
    root_url: str
    pages: list[PageAnalysis] = Field(default_factory=list)
    total_forms: int = 0
    total_api_endpoints: int = 0
    broken_links: list[str] = Field(default_factory=list)
