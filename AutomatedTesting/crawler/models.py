"""Data models for crawled page data."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class FormField(BaseModel):
    name: str = ""
    field_type: str = "text"
    required: bool = False
    placeholder: str = ""
    label: str = ""
    pattern: str = ""
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    options: list[str] = Field(default_factory=list)
    selector: str = ""


class FormInfo(BaseModel):
    action: str = ""
    method: str = "GET"
    fields: list[FormField] = Field(default_factory=list)
    submit_selector: str = ""
    selector: str = ""


class UIElement(BaseModel):
    tag: str
    text: str = ""
    element_type: str = ""
    selector: str = ""
    href: str = ""
    attributes: dict[str, str] = Field(default_factory=dict)


class APICall(BaseModel):
    url: str
    method: str = "GET"
    request_headers: dict[str, str] = Field(default_factory=dict)
    response_status: int = 0
    content_type: str = ""


class PageData(BaseModel):
    url: str
    title: str = ""
    headings: list[str] = Field(default_factory=list)
    meta_description: str = ""
    forms: list[FormInfo] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    buttons: list[UIElement] = Field(default_factory=list)
    inputs: list[UIElement] = Field(default_factory=list)
    dropdowns: list[UIElement] = Field(default_factory=list)
    images: list[UIElement] = Field(default_factory=list)
    api_calls: list[APICall] = Field(default_factory=list)
    screenshot_path: str = ""
    html_snippet: str = ""
    error_containers: list[str] = Field(default_factory=list)
    success_containers: list[str] = Field(default_factory=list)


class SiteMap(BaseModel):
    root_url: str
    pages: list[PageData] = Field(default_factory=list)
    broken_links: list[str] = Field(default_factory=list)
    total_links_found: int = 0
