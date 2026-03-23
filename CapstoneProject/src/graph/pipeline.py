"""
src/graph/pipeline.py

LangGraph StateGraph wiring.  Node implementations live in src/agents/.
This module wires the graph, defines the conditional router, and exposes
compile() + run_pipeline() for use by the CLI and the Streamlit UI.

Node execution order
--------------------

  [START]
     │
  rag_loader          ← loads tech_docs into state + indexes reviews into ChromaDB
     │
  csv_reader          ← normalises CSVs → feedback_items; upserts each into reviews collection
     │
  classifier          ← classifies each item; writes to classified_items
     │
  route_after_classify ─┬─ "bug"     → bug_analyzer
                         ├─ "feature" → feature_extractor
                         └─ "other"   → passthrough
                              │
                         (fan-in) ────→ ticket_creator   ← queries tickets collection for duplicates
                                              │
                                        quality_critic    ← auto-escalation + rule checks
                                              │
                                           [END]
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from langgraph.graph import StateGraph, START, END

import src.config as config
from src.graph.state import AgentState, FeedbackItem, ClassifiedItem, BugDetails, FeatureDetails, Ticket, QCResult, LogEntry

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Stub node helpers
# Every stub logs that it was called and returns the state unchanged.
# Real implementations in src/agents/ will replace these stubs.
# ══════════════════════════════════════════════════════════════════════════════

def _stub(name: str, state: AgentState) -> dict:
    logger.debug("[STUB] %s called", name)
    return {}


# ══════════════════════════════════════════════════════════════════════════════
# RAG Loader node
# Runs once at pipeline start.
# 1. Indexes any new tech docs found in TECH_DOCS_DIR.
# 2. Loads a summary of the tech_docs collection into state so all downstream
#    nodes can reference it without re-querying.
# ══════════════════════════════════════════════════════════════════════════════

def rag_loader_node(state: AgentState) -> dict:
    """
    Initialise RAG context for this pipeline run.
    Real implementation in src/agents/rag_loader.py will replace this stub.
    """
    logger.info("[rag_loader] Indexing tech docs and priming RAG context...")
    try:
        from src.db.chroma_store import get_store
        store = get_store()
        n = store.index_tech_docs()
        logger.info("[rag_loader] %d tech doc chunks available", n)

        # Load a broad architectural context query upfront
        context_chunks = store.query_tech_docs(
            "product overview features architecture", k=5
        )
        tech_doc_context = [
            {"id": r.id, "text": r.text, "source": r.metadata.get("source", "")}
            for r in context_chunks
        ]
    except Exception as exc:
        logger.warning("[rag_loader] Could not load RAG context: %s", exc)
        tech_doc_context = []

    return {
        "tech_doc_context": tech_doc_context,
        "run_id": str(uuid.uuid4()),
        "metrics": {"run_start": datetime.now(timezone.utc).isoformat()},
        "log_entries": [],
        "errors": [],
    }


# ══════════════════════════════════════════════════════════════════════════════
# CSV Reader node  (stub — real impl: src/agents/csv_reader.py)
# ══════════════════════════════════════════════════════════════════════════════

def csv_reader_node(state: AgentState) -> dict:
    """
    Reads app_store_reviews.csv and support_emails.csv.
    Normalises rows → FeedbackItem list.
    Upserts each item into the ChromaDB reviews collection.
    Real implementation: src/agents/csv_reader.py
    """
    return _stub("csv_reader", state)


# ══════════════════════════════════════════════════════════════════════════════
# Classifier node  (stub — real impl: src/agents/classifier.py)
# ══════════════════════════════════════════════════════════════════════════════

def classifier_node(state: AgentState) -> dict:
    """
    Uses OpenAI gpt-4o with structured output to classify each FeedbackItem.
    Queries the reviews collection for similar past items to provide RAG context.
    Real implementation: src/agents/classifier.py
    """
    return _stub("classifier", state)


# ══════════════════════════════════════════════════════════════════════════════
# Conditional router
# ══════════════════════════════════════════════════════════════════════════════

def route_after_classify(state: AgentState) -> str:
    """
    Inspects classified_items and decides which branch to take next.

    Returns
    -------
    "bug"      → bug_analyzer node
    "feature"  → feature_extractor node
    "other"    → passthrough node  (Praise / Complaint / Spam)

    Priority: if there are ANY bugs, route to bug_analyzer first so the fan-in
    at ticket_creator always has a complete picture.  LangGraph will handle
    running feature_extractor in parallel on the same state snapshot.
    """
    items = state.get("classified_items", [])
    categories = {item.classification.category for item in items}

    if "Bug" in categories:
        return "bug"
    if "Feature Request" in categories:
        return "feature"
    return "other"


# ══════════════════════════════════════════════════════════════════════════════
# Bug Analyzer node  (stub — real impl: src/agents/bug_analyzer.py)
# ══════════════════════════════════════════════════════════════════════════════

def bug_analyzer_node(state: AgentState) -> dict:
    """
    Processes all Bug-classified items.
    Queries tech_docs and reviews collections for:
      - Similar past bugs (pattern recognition)
      - Product component docs (understand affected feature)
    Real implementation: src/agents/bug_analyzer.py
    """
    return _stub("bug_analyzer", state)


# ══════════════════════════════════════════════════════════════════════════════
# Feature Extractor node  (stub — real impl: src/agents/feature_extractor.py)
# ══════════════════════════════════════════════════════════════════════════════

def feature_extractor_node(state: AgentState) -> dict:
    """
    Processes all Feature Request-classified items.
    Queries tech_docs to understand existing product features before scoring.
    Queries reviews collection to find similar feature requests (demand signal).
    Queries tickets collection to detect duplicate feature tickets.
    Real implementation: src/agents/feature_extractor.py
    """
    return _stub("feature_extractor", state)


# ══════════════════════════════════════════════════════════════════════════════
# Passthrough node  (Praise / Complaint / Spam — no deep analysis needed)
# ══════════════════════════════════════════════════════════════════════════════

def passthrough_node(state: AgentState) -> dict:
    """
    Items that are not Bug or Feature Request skip deep analysis.
    They pass through to ticket_creator which handles Complaints,
    and logs/discards Praise and Spam.
    """
    return _stub("passthrough", state)


# ══════════════════════════════════════════════════════════════════════════════
# Ticket Creator node  (stub — real impl: src/agents/ticket_creator.py)
# ══════════════════════════════════════════════════════════════════════════════

def ticket_creator_node(state: AgentState) -> dict:
    """
    Creates Ticket objects for Bug, Feature Request, and Complaint items.
    Queries the tickets collection to detect cross-run duplicates before writing.
    Upserts new tickets into the tickets collection.
    Writes generated_tickets.csv and processing_log.csv.
    Real implementation: src/agents/ticket_creator.py
    """
    return _stub("ticket_creator", state)


# ══════════════════════════════════════════════════════════════════════════════
# Quality Critic node  (stub — real impl: src/agents/quality_critic.py)
# ══════════════════════════════════════════════════════════════════════════════

def quality_critic_node(state: AgentState) -> dict:
    """
    Rule-based + optional LLM-based QC of all generated tickets.
    Auto-escalates priority for crash/data-loss descriptions.
    Writes metrics.csv.
    Real implementation: src/agents/quality_critic.py
    """
    return _stub("quality_critic", state)


# ══════════════════════════════════════════════════════════════════════════════
# Graph construction
# ══════════════════════════════════════════════════════════════════════════════

def build_graph() -> StateGraph:
    """
    Wire all nodes and edges into a compiled StateGraph.

    The graph runs:
      START → rag_loader → csv_reader → classifier → [conditional]
        ├─ bug_analyzer   ─┐
        ├─ feature_extractor ─┤ (fan-in via ticket_creator)
        └─ passthrough   ─┘
                └─ ticket_creator → quality_critic → END
    """
    builder = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    builder.add_node("rag_loader", rag_loader_node)
    builder.add_node("csv_reader", csv_reader_node)
    builder.add_node("classifier", classifier_node)
    builder.add_node("bug_analyzer", bug_analyzer_node)
    builder.add_node("feature_extractor", feature_extractor_node)
    builder.add_node("passthrough", passthrough_node)
    builder.add_node("ticket_creator", ticket_creator_node)
    builder.add_node("quality_critic", quality_critic_node)

    # ── Linear edges ──────────────────────────────────────────────────────────
    builder.add_edge(START, "rag_loader")
    builder.add_edge("rag_loader", "csv_reader")
    builder.add_edge("csv_reader", "classifier")

    # ── Conditional branching after classifier ────────────────────────────────
    builder.add_conditional_edges(
        "classifier",
        route_after_classify,
        {
            "bug": "bug_analyzer",
            "feature": "feature_extractor",
            "other": "passthrough",
        },
    )

    # ── Fan-in: all three branches converge at ticket_creator ─────────────────
    builder.add_edge("bug_analyzer", "ticket_creator")
    builder.add_edge("feature_extractor", "ticket_creator")
    builder.add_edge("passthrough", "ticket_creator")

    # ── Final QC and end ──────────────────────────────────────────────────────
    builder.add_edge("ticket_creator", "quality_critic")
    builder.add_edge("quality_critic", END)

    return builder


def compile_graph():
    """Return a compiled, runnable LangGraph."""
    return build_graph().compile()


# ══════════════════════════════════════════════════════════════════════════════
# Public pipeline runner (used by CLI + Streamlit)
# ══════════════════════════════════════════════════════════════════════════════

def run_pipeline(
    data_dir: str | None = None,
    output_dir: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Execute the full pipeline end-to-end.

    Parameters
    ----------
    data_dir   : override DATA_DIR from config
    output_dir : override OUTPUT_DIR from config
    dry_run    : classify only, do not write ticket CSVs

    Returns
    -------
    Final AgentState as a plain dict.
    """
    graph = compile_graph()

    initial_state: AgentState = {
        "feedback_items": [],
        "classified_items": [],
        "bug_details": [],
        "feature_details": [],
        "tickets": [],
        "qc_results": [],
        "tech_doc_context": [],
        "log_entries": [],
        "errors": [],
        "metrics": {},
        "run_id": "",
    }

    # Allow callers to inject overrides via metrics dict for nodes to pick up
    if data_dir:
        initial_state["metrics"]["data_dir_override"] = data_dir
    if output_dir:
        initial_state["metrics"]["output_dir_override"] = output_dir
    if dry_run:
        initial_state["metrics"]["dry_run"] = True

    logger.info("Starting pipeline run (dry_run=%s)", dry_run)
    result = graph.invoke(initial_state)
    logger.info("Pipeline run complete. run_id=%s", result.get("run_id"))
    return result
