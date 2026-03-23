"""
src/agents/feature_extractor.py
Processes Feature Request-classified items.
Queries tech_docs (understand existing product) + feedback_reviews (demand signal)
+ generated_tickets (cross-run dedup) before calling gpt-4o.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from openai import OpenAI
from pydantic import BaseModel

import src.config as config
from src.db.chroma_store import get_store
from src.graph.state import (AgentState, ClassifiedItem, FeatureDetails, LogEntry)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a product manager extracting structured feature request data.

demand_score 1–5:
  5 = widely requested / high business value (e.g. dark mode, biometric login)
  4 = frequently mentioned, clear user benefit
  3 = moderate interest, useful for a segment
  2 = niche use case
  1 = highly specific / unlikely to benefit many users

user_segment examples: "all users", "power users", "iOS users", "enterprise customers",
                       "free tier users", "premium users"

feature_summary must be ≤ 15 words.
"""


class _LLMFeature(BaseModel):
    feature_summary: str
    description: str
    user_impact: str
    demand_score: int
    user_segment: str


def feature_extractor_node(state: AgentState) -> dict:
    classified: list[ClassifiedItem] = state.get("classified_items", [])
    features = [c for c in classified if c.classification.category == "Feature Request"]

    if not features:
        return {"feature_details": [], "log_entries": [], "errors": []}

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    store = get_store()
    threshold = config.DUPLICATE_SIMILARITY_THRESHOLD
    tech_ctx = state.get("tech_doc_context", [])

    details_list: list[FeatureDetails] = []
    log_entries: list[LogEntry] = []
    errors: list[str] = []

    for item in features:
        similar_features: list[dict] = []
        product_ctx: list[dict] = []
        is_duplicate = False
        duplicate_of: str | None = None

        try:
            # 1. Understand existing product features from tech docs
            product_hits = store.query_tech_docs(item.text[:300], k=4)
            product_ctx = [
                {"id": r.id, "text": r.text[:300], "source": r.metadata.get("source", "")}
                for r in product_hits
            ]

            # 2. Demand signal — similar feature requests
            review_hits = store.find_similar_reviews(item.text, k=5)
            similar_features = [
                {"id": r.id, "text": r.text[:200], "score": round(r.similarity_score, 3)}
                for r in review_hits
                if r.id != item.id and r.similarity_score > 0.5
            ]

            # 3. Duplicate check against existing tickets
            ticket_hits = store.find_similar_tickets(
                item.text, k=3, category="Feature Request"
            )
            for hit in ticket_hits:
                if hit.similarity_score >= threshold:
                    is_duplicate = True
                    duplicate_of = hit.id
                    break
        except Exception as exc:
            logger.warning("[feature_extractor] RAG query failed for %s: %s", item.id, exc)

        # Build prompt
        ctx_parts = []
        if product_ctx:
            ctx_parts.append("Existing product features (from docs):\n" +
                             "\n".join(f"  [{r['source']}] {r['text'][:200]}" for r in product_ctx[:3]))
        if similar_features:
            ctx_parts.append(f"Similar feature requests found ({len(similar_features)}):\n" +
                             "\n".join(f"  - {f['text'][:150]}" for f in similar_features[:3]))
        if tech_ctx:
            ctx_parts.append("Product overview:\n" +
                             "\n".join(f"  {c['text'][:150]}" for c in tech_ctx[:2]))

        user_msg = (
            f"Feature request text:\n{item.text[:1200]}\n\n"
            + ("\n\n".join(ctx_parts) if ctx_parts else "")
            + "\n\nExtract structured feature details."
        )

        try:
            response = client.beta.chat.completions.parse(
                model=config.OPENAI_MODEL,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_msg},
                ],
                response_format=_LLMFeature,
            )
            llm = response.choices[0].message.parsed
            demand = max(1, min(5, llm.demand_score))   # clamp to 1–5

            fd = FeatureDetails(
                source_id=item.id,
                feature_summary=llm.feature_summary[:80],
                description=llm.description,
                user_impact=llm.user_impact,
                demand_score=demand,
                user_segment=llm.user_segment or "all users",
                is_duplicate=is_duplicate,
                duplicate_of=duplicate_of,
                similar_features=similar_features,
                product_context=product_ctx,
            )
            details_list.append(fd)
            log_entries.append(LogEntry(
                log_id=f"feat_{item.id}", source_id=item.id,
                stage="feature_extractor", result="success",
                details=f"demand={demand} duplicate={is_duplicate}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            ))
        except Exception as exc:
            msg = f"[feature_extractor] Failed for {item.id}: {exc}"
            logger.error(msg)
            errors.append(msg)
            log_entries.append(LogEntry(
                log_id=f"feat_{item.id}", source_id=item.id,
                stage="feature_extractor", result="error",
                details=str(exc), timestamp=datetime.now(timezone.utc).isoformat(),
            ))

    logger.info("[feature_extractor] %d/%d features extracted", len(details_list), len(features))
    return {"feature_details": details_list, "log_entries": log_entries, "errors": errors}
