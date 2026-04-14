"""LangGraph node: import the attendees CSV into the DB."""

from __future__ import annotations

import os

from api.database import SessionLocal
from api.import_csv import import_attendees
from agent.state import AgentState


def read_csv_node(state: AgentState) -> AgentState:
    csv_path = state.get("csv_path") or os.getenv("INPUT_CSV", "data/input/WFHAttendees.csv")
    errors = list(state.get("errors") or [])
    try:
        with SessionLocal() as db:
            summary = import_attendees(csv_path, db)
        errors.extend(summary.errors)
        return {
            "csv_path": csv_path,
            "imported": summary.imported,
            "updated": summary.updated,
            "errors": errors,
        }
    except Exception as exc:
        errors.append(f"read_csv: {exc}")
        return {"csv_path": csv_path, "imported": 0, "updated": 0, "errors": errors}
