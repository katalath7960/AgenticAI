"""
src/agents/quality_critic.py
Rule-based + optional LLM quality control on every generated ticket.
Auto-escalates priority when description contains crash or data loss keywords.
Writes metrics.csv after the run.
"""
from __future__ import annotations

import csv
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import src.config as config
from src.graph.state import AgentState, LogEntry, QCResult, Ticket

logger = logging.getLogger(__name__)

METRICS_FIELDS = [
    "run_id", "timestamp", "total_items", "bugs", "features",
    "praise", "complaints", "spam", "tickets_created",
    "qc_pass_rate", "avg_latency_ms",
]

ESCALATION_KEYWORDS = [
    "crash", "crashes", "data loss", "lost all data", "data lost",
    "unable to open", "frozen", "account locked",
]


def _check_ticket(ticket: Ticket) -> list[str]:
    """Return list of rule violation strings (empty = pass)."""
    failures = []
    if len(ticket.title) > 80:
        failures.append("title_too_long")
    if len(ticket.description) < 50:
        failures.append("description_too_short")
    if not ticket.priority:
        failures.append("missing_priority")
    if ticket.category not in ("Bug", "Feature Request", "Complaint"):
        failures.append("invalid_category")
    if ticket.category == "Bug" and not ticket.severity:
        failures.append("bug_missing_severity")
    return failures


def quality_critic_node(state: AgentState) -> dict:
    tickets: list[Ticket] = state.get("tickets", [])
    classified = state.get("classified_items", [])
    run_id = state.get("run_id", str(uuid.uuid4()))
    output_dir = state.get("metrics", {}).get("output_dir_override") or config.OUTPUT_DIR
    dry_run = state.get("metrics", {}).get("dry_run", False)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    qc_results: list[QCResult] = []
    log_entries: list[LogEntry] = []
    errors: list[str] = []
    escalated_count = 0

    for ticket in tickets:
        failures = _check_ticket(ticket)
        escalated = False
        desc_lower = ticket.description.lower()

        # Auto-escalate to Critical
        if any(kw in desc_lower for kw in ESCALATION_KEYWORDS):
            if ticket.priority != "Critical":
                ticket.priority = "Critical"
                escalated = True
                escalated_count += 1

        passed = len(failures) == 0
        if failures or escalated:
            ticket.status = "needs_review" if failures else ticket.status

        qc = QCResult(
            ticket_id=ticket.ticket_id,
            passed=passed,
            failed_rules=failures,
            qc_notes=(
                f"Rules failed: {', '.join(failures)}. " if failures else ""
            ) + ("Priority auto-escalated to Critical." if escalated else ""),
            priority_escalated=escalated,
        )
        qc_results.append(qc)

        log_entries.append(LogEntry(
            log_id=f"qc_{ticket.ticket_id}",
            source_id=ticket.source_id,
            stage="quality_critic",
            result="success" if passed else "error",
            details=f"passed={passed} rules={failures}",
            timestamp=datetime.now(timezone.utc).isoformat(),
        ))

    # Metrics
    pass_count = sum(1 for q in qc_results if q.passed)
    qc_pass_rate = round(pass_count / len(qc_results) * 100, 1) if qc_results else 100.0

    # Category counts from classified items
    cat_counts: dict[str, int] = {"Bug": 0, "Feature Request": 0,
                                   "Praise": 0, "Complaint": 0, "Spam": 0}
    for c in classified:
        cat = c.classification.category
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    run_metrics = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_items": len(classified),
        "bugs": cat_counts["Bug"],
        "features": cat_counts["Feature Request"],
        "praise": cat_counts["Praise"],
        "complaints": cat_counts["Complaint"],
        "spam": cat_counts["Spam"],
        "tickets_created": len(tickets),
        "qc_pass_rate": qc_pass_rate,
        "avg_latency_ms": "",   # populated by main.py after run
    }

    if not dry_run:
        _append_csv(os.path.join(output_dir, "metrics.csv"), METRICS_FIELDS, [run_metrics])
        logger.info("[quality_critic] metrics.csv updated (pass_rate=%.1f%%)", qc_pass_rate)

    # Update state metrics dict
    current_metrics = dict(state.get("metrics", {}))
    current_metrics.update({
        "qc_pass_rate": qc_pass_rate,
        "tickets_created": len(tickets),
        "total_items": len(classified),
        "escalated": escalated_count,
        **cat_counts,
    })

    logger.info("[quality_critic] %d/%d tickets passed QC, %d escalated",
                pass_count, len(tickets), escalated_count)
    return {
        "qc_results": qc_results,
        "tickets": tickets,  # updated priorities
        "metrics": current_metrics,
        "log_entries": log_entries,
        "errors": errors,
    }


def _append_csv(path: str, fields: list[str], rows: list[dict]) -> None:
    is_new = not os.path.exists(path)
    existing: list[dict] = []
    if not is_new:
        with open(path, newline="", encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(existing + rows)
    os.replace(tmp, path)
