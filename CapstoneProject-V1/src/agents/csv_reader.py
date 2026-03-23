"""
src/agents/csv_reader.py
Reads app_store_reviews.csv and support_emails.csv, normalises every row
into a FeedbackItem, and upserts each one into the ChromaDB feedback_reviews
collection so subsequent agents can retrieve similar past items.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import pandas as pd

import src.config as config
from src.db.chroma_store import get_store
from src.graph.state import AgentState, FeedbackItem, LogEntry

logger = logging.getLogger(__name__)


def _log(source_id: str, result: str, details: str = "") -> LogEntry:
    return LogEntry(
        log_id=f"log_{source_id}",
        source_id=source_id,
        stage="csv_reader",
        result=result,
        details=details,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def csv_reader_node(state: AgentState) -> dict:
    store = get_store()
    items: list[FeedbackItem] = []
    log_entries: list[LogEntry] = []
    errors: list[str] = []

    data_dir = state.get("metrics", {}).get("data_dir_override") or config.DATA_DIR

    # ── Reviews ───────────────────────────────────────────────────────────────
    reviews_path = os.path.join(data_dir, "app_store_reviews.csv")
    try:
        df = pd.read_csv(reviews_path, dtype=str).fillna("")
        for _, row in df.iterrows():
            rid = str(row.get("review_id", "")).strip()
            text = str(row.get("review_text", "")).strip()
            if not rid or not text:
                logger.warning("[csv_reader] Skipping malformed review row: %s", dict(row))
                errors.append(f"csv_reader: malformed review row id={rid!r}")
                log_entries.append(_log(rid or "unknown", "skipped", "missing review_id or text"))
                continue
            metadata = {
                "source_type": "review",
                "platform": row.get("platform", ""),
                "rating": row.get("rating", ""),
                "date": row.get("date", ""),
                "app_version": row.get("app_version", ""),
                "user_name": row.get("user_name", ""),
            }
            item = FeedbackItem(id=rid, source_type="review", text=text,
                                metadata=metadata, raw_row=dict(row))
            items.append(item)
            try:
                store.upsert_review(rid, text, metadata)
            except Exception as exc:
                logger.warning("[csv_reader] ChromaDB upsert failed for %s: %s", rid, exc)
            log_entries.append(_log(rid, "success", "review normalised"))
    except FileNotFoundError:
        msg = f"[csv_reader] Reviews file not found: {reviews_path}"
        logger.error(msg)
        errors.append(msg)

    # ── Emails ────────────────────────────────────────────────────────────────
    emails_path = os.path.join(data_dir, "support_emails.csv")
    try:
        df = pd.read_csv(emails_path, dtype=str).fillna("")
        for _, row in df.iterrows():
            eid = str(row.get("email_id", "")).strip()
            subject = str(row.get("subject", "")).strip()
            body = str(row.get("body", "")).strip()
            text = f"{subject}\n\n{body}".strip()
            if not eid or not text:
                logger.warning("[csv_reader] Skipping malformed email row: %s", dict(row))
                errors.append(f"csv_reader: malformed email row id={eid!r}")
                log_entries.append(_log(eid or "unknown", "skipped", "missing email_id or text"))
                continue
            metadata = {
                "source_type": "email",
                "subject": subject,
                "sender_email": row.get("sender_email", ""),
                "timestamp": row.get("timestamp", ""),
                "priority": row.get("priority", ""),
            }
            item = FeedbackItem(id=eid, source_type="email", text=text,
                                metadata=metadata, raw_row=dict(row))
            items.append(item)
            try:
                store.upsert_review(eid, text, metadata)
            except Exception as exc:
                logger.warning("[csv_reader] ChromaDB upsert failed for %s: %s", eid, exc)
            log_entries.append(_log(eid, "success", "email normalised"))
    except FileNotFoundError:
        msg = f"[csv_reader] Emails file not found: {emails_path}"
        logger.error(msg)
        errors.append(msg)

    logger.info("[csv_reader] %d items loaded (%d errors)", len(items), len(errors))
    return {"feedback_items": items, "log_entries": log_entries, "errors": errors}
