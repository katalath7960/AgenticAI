"""Typed state object shared across LangGraph nodes."""

from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    csv_path: str
    imported: int
    updated: int
    barcodes_generated: int
    emails_sent: int
    errors: list[str]
