"""
src/agents/rag_loader.py
First node in the pipeline.
1. Indexes any new tech docs found in TECH_DOCS_DIR into ChromaDB (idempotent).
2. Runs a warm-up query and stores the results in state["tech_doc_context"]
   so every downstream agent has product knowledge without re-querying.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

import src.config as config
from src.db.chroma_store import get_store
from src.graph.state import AgentState

logger = logging.getLogger(__name__)


def rag_loader_node(state: AgentState) -> dict:
    run_id = str(uuid.uuid4())
    tech_doc_context: list[dict] = []

    try:
        store = get_store()
        n_chunks = store.index_tech_docs(config.TECH_DOCS_DIR)
        logger.info("[rag_loader] %d tech-doc chunks available", n_chunks)

        # Broad warm-up queries to prime context for all agent types
        warmup_queries = [
            "product overview features architecture",
            "known bugs crashes errors login sync",
            "feature requests roadmap planned improvements",
        ]
        seen: set[str] = set()
        for q in warmup_queries:
            for r in store.query_tech_docs(q, k=3):
                if r.id not in seen:
                    seen.add(r.id)
                    tech_doc_context.append({
                        "id": r.id,
                        "text": r.text,
                        "source": r.metadata.get("source", ""),
                        "similarity": round(r.similarity_score, 3),
                    })
    except Exception as exc:
        logger.warning("[rag_loader] Could not load RAG context: %s", exc)

    # Merge into existing metrics so callers can pass data_dir_override, dry_run, etc.
    merged_metrics = {**state.get("metrics", {}),
                      "run_start": datetime.now(timezone.utc).isoformat(),
                      "run_id": run_id}
    return {
        "run_id": run_id,
        "tech_doc_context": tech_doc_context,
        "metrics": merged_metrics,
        "log_entries": [],
        "errors": [],
    }
