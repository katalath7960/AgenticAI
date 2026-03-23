"""
src/agents/ticket_creator.py
Creates structured tickets for Bug, Feature Request, and Complaint items.
Checks the generated_tickets collection for cross-run duplicates before writing.
Upserts every new (non-duplicate) ticket back into ChromaDB.
Writes generated_tickets.csv and processing_log.csv (append-safe).
"""
from __future__ import annotations

import csv
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import src.config as config
from src.db.chroma_store import get_store
from src.graph.state import (AgentState, BugDetails, ClassifiedItem,
                              FeatureDetails, LogEntry, Ticket)

logger = logging.getLogger(__name__)

TICKET_FIELDS = [
    "ticket_id", "source_id", "source_type", "title", "description",
    "category", "priority", "severity", "assignee_team", "tags",
    "created_at", "status", "is_duplicate", "duplicate_of",
]
LOG_FIELDS = ["log_id", "source_id", "stage", "result", "details", "timestamp"]

_TEAM_MAP = {
    "Bug": "Engineering",
    "Feature Request": "Product",
    "Complaint": "Support",
}
_PRIORITY_MAP = {
    "Bug": "High",
    "Feature Request": "Medium",
    "Complaint": "Medium",
}


def _ticket_id(run_id: str, seq: int) -> str:
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    short_run = run_id[:8] if run_id else "00000000"
    return f"TKT-{date}-{short_run}-{seq:04d}"


def _make_description(item: ClassifiedItem, bug: BugDetails | None,
                       feature: FeatureDetails | None) -> str:
    cat = item.classification.category
    if cat == "Bug" and bug:
        steps = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(bug.steps_to_reproduce))
        return (
            f"**Summary**\n{item.text[:300]}\n\n"
            f"**Technical Details**\n"
            f"- Platform: {bug.platform}\n"
            f"- Device: {bug.device}\n"
            f"- OS: {bug.os_version}\n"
            f"- App version: {bug.app_version}\n"
            f"- Affected feature: {bug.affected_feature}\n\n"
            f"**Steps to Reproduce**\n{steps}\n\n"
            f"**Expected Behavior**\nThe feature should work without errors."
        )
    if cat == "Feature Request" and feature:
        return (
            f"**Summary**\n{feature.feature_summary}\n\n"
            f"**Description**\n{feature.description}\n\n"
            f"**User Impact**\n{feature.user_impact}\n\n"
            f"**Demand Score**\n{feature.demand_score}/5 — segment: {feature.user_segment}"
        )
    return f"**Summary**\n{item.text[:500]}\n\n**Expected Behavior**\nUser satisfaction and resolution."


def _make_tags(item: ClassifiedItem, bug: BugDetails | None) -> str:
    tags = [item.source_type]
    if bug:
        if bug.platform != "Unknown":
            tags.append(bug.platform.lower())
        if bug.affected_feature != "Unknown":
            tags.append(bug.affected_feature.lower().replace(" ", "-"))
    return ",".join(tags)


def ticket_creator_node(state: AgentState) -> dict:
    classified: list[ClassifiedItem] = state.get("classified_items", [])
    bug_map: dict[str, BugDetails] = {b.source_id: b for b in state.get("bug_details", [])}
    feat_map: dict[str, FeatureDetails] = {f.source_id: f for f in state.get("feature_details", [])}

    store = get_store()
    threshold = config.DUPLICATE_SIMILARITY_THRESHOLD
    run_id = state.get("run_id", "")
    output_dir = state.get("metrics", {}).get("output_dir_override") or config.OUTPUT_DIR
    dry_run = state.get("metrics", {}).get("dry_run", False)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    tickets: list[Ticket] = []
    log_entries: list[LogEntry] = []
    errors: list[str] = []
    seq = 0

    for item in classified:
        cat = item.classification.category
        ts = datetime.now(timezone.utc).isoformat()

        if cat in ("Praise", "Spam"):
            log_entries.append(LogEntry(
                log_id=f"skip_{item.id}", source_id=item.id,
                stage="ticket_creator",
                result="skipped",
                details=f"{cat} — no ticket created",
                timestamp=ts,
            ))
            continue

        if cat not in ("Bug", "Feature Request", "Complaint"):
            continue

        bug = bug_map.get(item.id)
        feat = feat_map.get(item.id)
        seq += 1
        tid = _ticket_id(run_id, seq)

        title_base = item.text[:80].replace("\n", " ").strip()
        if bug and bug.affected_feature != "Unknown":
            title_base = f"[{bug.severity}] {bug.affected_feature}: {item.text[:60].strip()}"
        elif feat:
            title_base = feat.feature_summary[:80]
        title = title_base[:80]

        description = _make_description(item, bug, feat)
        priority = (bug.severity if bug else
                    ("High" if feat and feat.demand_score >= 4 else
                     _PRIORITY_MAP.get(cat, "Medium")))

        # Duplicate detection against existing tickets collection
        is_dup = False
        dup_of: str | None = None
        if cat in ("Bug", "Feature Request"):
            try:
                hits = store.find_similar_tickets(
                    f"{title}\n{description[:200]}", k=3, category=cat
                )
                for hit in hits:
                    if hit.similarity_score >= threshold:
                        is_dup = True
                        dup_of = hit.id
                        break
            except Exception as exc:
                logger.warning("[ticket_creator] Dedup query failed for %s: %s", item.id, exc)

        ticket = Ticket(
            ticket_id=tid,
            source_id=item.id,
            source_type=item.source_type,
            title=title,
            description=description,
            category=cat,
            priority=priority,
            severity=bug.severity if bug else "",
            assignee_team=_TEAM_MAP[cat],
            tags=_make_tags(item, bug),
            created_at=ts,
            status="open",
            is_duplicate=is_dup,
            duplicate_of=dup_of,
        )
        tickets.append(ticket)

        # Upsert into tickets collection (even duplicates — for tracking)
        if not dry_run:
            try:
                store.upsert_ticket(tid, title, description,
                                    {"category": cat, "priority": priority,
                                     "source_id": item.id, "run_id": run_id})
            except Exception as exc:
                logger.warning("[ticket_creator] ChromaDB upsert failed for %s: %s", tid, exc)

        log_entries.append(LogEntry(
            log_id=f"tkt_{item.id}", source_id=item.id,
            stage="ticket_creator", result="success",
            details=f"{tid} dup={is_dup}",
            timestamp=ts,
        ))

    # Write CSVs
    if not dry_run and tickets:
        _append_csv(
            os.path.join(output_dir, "generated_tickets.csv"),
            TICKET_FIELDS,
            [t.model_dump() for t in tickets],
        )
        logger.info("[ticket_creator] %d tickets written to generated_tickets.csv", len(tickets))

    if not dry_run:
        all_logs = state.get("log_entries", []) + log_entries
        _append_csv(
            os.path.join(output_dir, "processing_log.csv"),
            LOG_FIELDS,
            [e.model_dump() for e in all_logs],
        )

    logger.info("[ticket_creator] %d tickets created, %d items skipped",
                len(tickets), len(classified) - len(tickets))
    return {"tickets": tickets, "log_entries": log_entries, "errors": errors}


def _append_csv(path: str, fields: list[str], rows: list[dict]) -> None:
    """Append rows to a CSV file, writing the header only if the file is new."""
    is_new = not os.path.exists(path)
    tmp = path + ".tmp"
    # Read existing rows if file already exists
    existing: list[dict] = []
    if not is_new:
        with open(path, newline="", encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
    all_rows = existing + rows
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)
    os.replace(tmp, path)
