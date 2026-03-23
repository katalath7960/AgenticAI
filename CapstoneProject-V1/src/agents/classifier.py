"""
src/agents/classifier.py
Classifies every FeedbackItem using OpenAI gpt-4o structured output.
Queries the feedback_reviews collection for similar past items and injects
them as RAG context so the model can reason from historical patterns.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from openai import OpenAI
from pydantic import BaseModel
from typing import Literal

import src.config as config
from src.db.chroma_store import get_store
from src.graph.state import (AgentState, ClassificationResult,
                              ClassifiedItem, FeedbackItem, LogEntry)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior product triage analyst for a B2C mobile productivity app.
Classify user feedback into EXACTLY one of these categories:

  Bug           — report of broken functionality, crash, or data loss
  Feature Request — request for new or enhanced functionality
  Praise        — positive feedback, compliments, appreciation
  Complaint     — negative feedback about price, support, UX without a specific bug
  Spam          — promotional content, gibberish, or completely off-topic

Rules:
- A crash or "not working" is always Bug, not Complaint.
- A price complaint is Complaint, not Bug.
- If it mentions both a bug and a feature, classify by the primary intent.
- Confidence 0.0–1.0. If < {threshold}, set needs_review=true.

Return JSON matching the schema exactly.
"""

ONE_SHOT = """
Examples:
  "App crashes when I open my profile" → Bug, confidence 0.97
  "Please add dark mode" → Feature Request, confidence 0.95
  "Amazing app, love it!" → Praise, confidence 0.98
  "The subscription is too expensive" → Complaint, confidence 0.92
  "Download free apps at freeapps.com" → Spam, confidence 0.99
"""


class _LLMResult(BaseModel):
    category: Literal["Bug", "Feature Request", "Praise", "Complaint", "Spam"]
    confidence: float
    reasoning: str
    needs_review: bool


def _build_user_prompt(item: FeedbackItem, similar: list[dict]) -> str:
    ctx = ""
    if similar:
        examples = "\n".join(
            f"  - [{r['metadata'].get('source_type','?')}] {r['text'][:120]}"
            for r in similar[:3]
        )
        ctx = f"\nSimilar past feedback for context:\n{examples}\n"
    return (
        f"Source type: {item.source_type}\n"
        f"Text: {item.text[:1000]}{ctx}\n"
        "Classify this feedback item."
    )


def classifier_node(state: AgentState) -> dict:
    items: list[FeedbackItem] = state.get("feedback_items", [])
    if not items:
        return {"classified_items": [], "log_entries": [], "errors": []}

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    store = get_store()
    threshold = config.CLASSIFICATION_THRESHOLD
    batch_size = config.CLASSIFIER_BATCH_SIZE

    classified: list[ClassifiedItem] = []
    log_entries: list[LogEntry] = []
    errors: list[str] = []

    system = SYSTEM_PROMPT.format(threshold=threshold) + ONE_SHOT

    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        for item in batch:
            # RAG: retrieve similar past reviews for context
            similar_results: list[dict] = []
            try:
                hits = store.find_similar_reviews(item.text, k=3)
                similar_results = [
                    {"id": r.id, "text": r.text[:200],
                     "metadata": r.metadata, "score": r.similarity_score}
                    for r in hits
                    if r.id != item.id   # exclude self
                ]
            except Exception as exc:
                logger.warning("[classifier] RAG query failed for %s: %s", item.id, exc)

            try:
                response = client.beta.chat.completions.parse(
                    model=config.OPENAI_MODEL,
                    temperature=config.OPENAI_TEMPERATURE,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user",   "content": _build_user_prompt(item, similar_results)},
                    ],
                    response_format=_LLMResult,
                )
                llm = response.choices[0].message.parsed
                conf = max(0.0, min(1.0, llm.confidence))
                result = ClassificationResult(
                    category=llm.category,
                    confidence=conf,
                    reasoning=llm.reasoning,
                    needs_review=conf < threshold,
                )
                classified.append(ClassifiedItem(
                    **item.model_dump(),
                    classification=result,
                    similar_reviews=similar_results,
                ))
                log_entries.append(LogEntry(
                    log_id=f"cls_{item.id}",
                    source_id=item.id,
                    stage="classifier",
                    result="success",
                    details=f"{result.category} conf={conf:.2f}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ))
            except Exception as exc:
                msg = f"[classifier] Failed for {item.id}: {exc}"
                logger.error(msg)
                errors.append(msg)
                log_entries.append(LogEntry(
                    log_id=f"cls_{item.id}",
                    source_id=item.id,
                    stage="classifier",
                    result="error",
                    details=str(exc),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ))

    logger.info("[classifier] %d/%d items classified", len(classified), len(items))
    return {"classified_items": classified, "log_entries": log_entries, "errors": errors}
