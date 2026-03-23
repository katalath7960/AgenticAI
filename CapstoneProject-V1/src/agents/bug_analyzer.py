"""
src/agents/bug_analyzer.py
Processes Bug-classified items.  Queries both the feedback_reviews collection
(similar past bugs) and the tech_documents collection (product/feature context)
before calling the LLM to extract structured BugDetails.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from openai import OpenAI
from pydantic import BaseModel
from typing import Literal

import src.config as config
from src.db.chroma_store import get_store
from src.graph.state import (AgentState, BugDetails, ClassifiedItem, LogEntry)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior mobile engineer performing bug triage.
Extract structured technical details from user feedback for bug items.

Severity rules (apply these even if user doesn't state them explicitly):
  Critical — crash, data loss, unable to open app, frozen, account locked out
  High     — login failure, sync failure, feature completely broken
  Medium   — degraded performance, intermittent issue, notification not working
  Low      — cosmetic issue, minor UI glitch, slow loading

Always fill every field. Use "Unknown" (never null/None) for missing info.
steps_to_reproduce must always be a list of strings.
"""


class _LLMBug(BaseModel):
    platform: str
    device: str
    os_version: str
    app_version: str
    steps_to_reproduce: list[str]
    severity: Literal["Critical", "High", "Medium", "Low"]
    affected_feature: str


def _severity_heuristic(text: str) -> str | None:
    """Pre-LLM keyword check — used to validate/override LLM output."""
    t = text.lower()
    if any(k in t for k in ["crash", "data loss", "lost all", "unable to open", "frozen", "account locked"]):
        return "Critical"
    if any(k in t for k in ["cannot login", "can't login", "login fail", "sign in fail",
                              "sync fail", "not syncing", "completely broken"]):
        return "High"
    if any(k in t for k in ["notification", "slow", "intermittent", "sometimes", "battery"]):
        return "Medium"
    return None


def bug_analyzer_node(state: AgentState) -> dict:
    classified: list[ClassifiedItem] = state.get("classified_items", [])
    bugs = [c for c in classified if c.classification.category == "Bug"]

    if not bugs:
        return {"bug_details": [], "log_entries": [], "errors": []}

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    store = get_store()
    tech_ctx = state.get("tech_doc_context", [])

    details_list: list[BugDetails] = []
    log_entries: list[LogEntry] = []
    errors: list[str] = []

    for item in bugs:
        similar_bugs: list[dict] = []
        product_ctx: list[dict] = []

        try:
            # 1. Similar past bug reports
            hits = store.find_similar_reviews(item.text, k=3, source_type=None)
            similar_bugs = [
                {"id": r.id, "text": r.text[:250], "score": round(r.similarity_score, 3)}
                for r in hits if r.id != item.id
            ]

            # 2. Relevant product/architecture docs
            feature_query = f"bug crash error {item.text[:200]}"
            hits2 = store.query_tech_docs(feature_query, k=4)
            product_ctx = [
                {"id": r.id, "text": r.text[:300], "source": r.metadata.get("source", "")}
                for r in hits2
            ]
        except Exception as exc:
            logger.warning("[bug_analyzer] RAG query failed for %s: %s", item.id, exc)

        # Build user prompt with RAG context
        ctx_parts = []
        if similar_bugs:
            ctx_parts.append("Similar past bug reports:\n" +
                             "\n".join(f"  - {b['text'][:150]}" for b in similar_bugs[:2]))
        if product_ctx:
            ctx_parts.append("Relevant product documentation:\n" +
                             "\n".join(f"  [{r['source']}] {r['text'][:200]}" for r in product_ctx[:3]))
        if tech_ctx:
            ctx_parts.append("General product context:\n" +
                             "\n".join(f"  {c['text'][:150]}" for c in tech_ctx[:2]))

        user_msg = (
            f"Feedback text:\n{item.text[:1500]}\n\n"
            + ("\n\n".join(ctx_parts) if ctx_parts else "")
            + "\n\nExtract structured bug details."
        )

        try:
            response = client.beta.chat.completions.parse(
                model=config.OPENAI_MODEL,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_msg},
                ],
                response_format=_LLMBug,
            )
            llm = response.choices[0].message.parsed

            # Keyword heuristic can override LLM severity upward
            heuristic_sev = _severity_heuristic(item.text)
            severity_order = ["Low", "Medium", "High", "Critical"]
            final_sev = llm.severity
            if heuristic_sev:
                if severity_order.index(heuristic_sev) > severity_order.index(llm.severity):
                    final_sev = heuristic_sev

            details = BugDetails(
                source_id=item.id,
                platform=llm.platform or "Unknown",
                device=llm.device or "Unknown",
                os_version=llm.os_version or "Unknown",
                app_version=llm.app_version or "Unknown",
                steps_to_reproduce=llm.steps_to_reproduce or ["Not provided"],
                severity=final_sev,
                affected_feature=llm.affected_feature or "Unknown",
                similar_bugs=similar_bugs,
                product_context=product_ctx,
            )
            details_list.append(details)
            log_entries.append(LogEntry(
                log_id=f"bug_{item.id}",
                source_id=item.id,
                stage="bug_analyzer",
                result="success",
                details=f"severity={final_sev} feature={details.affected_feature}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            ))
        except Exception as exc:
            msg = f"[bug_analyzer] Failed for {item.id}: {exc}"
            logger.error(msg)
            errors.append(msg)
            log_entries.append(LogEntry(
                log_id=f"bug_{item.id}", source_id=item.id,
                stage="bug_analyzer", result="error",
                details=str(exc), timestamp=datetime.now(timezone.utc).isoformat(),
            ))

    logger.info("[bug_analyzer] %d/%d bugs analysed", len(details_list), len(bugs))
    return {"bug_details": details_list, "log_entries": log_entries, "errors": errors}
