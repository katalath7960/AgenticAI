"""Agent router: kick off the LangGraph run, poll status."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from threading import Lock

from fastapi import APIRouter, BackgroundTasks, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["agent"])

_runs: dict[str, dict] = {}
_lock = Lock()


def _run_agent(run_id: str, csv_path: str | None) -> None:
    import os as _os
    from agent.graph import build_graph

    with _lock:
        _runs[run_id]["status"] = "running"

    initial_csv = csv_path or _os.getenv("INPUT_CSV", "data/input/WFHAttendees.csv")
    try:
        final = build_graph().invoke({"csv_path": initial_csv, "errors": []})
        with _lock:
            _runs[run_id].update({
                "status": "completed",
                "finished_at": datetime.utcnow().isoformat(),
                "state": {k: v for k, v in final.items() if k != "errors"},
                "errors": final.get("errors", []),
            })
    except Exception as exc:
        logger.exception("agent run %s failed", run_id)
        with _lock:
            _runs[run_id].update({
                "status": "failed",
                "finished_at": datetime.utcnow().isoformat(),
                "error": str(exc),
            })


@router.post("/run")
def run_agent(background: BackgroundTasks, csv_path: str | None = None):
    run_id = uuid.uuid4().hex[:12]
    with _lock:
        _runs[run_id] = {
            "run_id": run_id,
            "status": "started",
            "started_at": datetime.utcnow().isoformat(),
        }
    background.add_task(_run_agent, run_id, csv_path)
    return {"run_id": run_id, "status": "started"}


@router.get("/runs/{run_id}")
def get_run(run_id: str):
    with _lock:
        run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run_id not found")
    return run
