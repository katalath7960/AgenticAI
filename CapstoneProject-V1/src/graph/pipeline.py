"""
src/graph/pipeline.py — LangGraph StateGraph wiring.

Node order:
  START → rag_loader → csv_reader → classifier → [conditional]
    ├─ bug_analyzer       ─┐
    ├─ feature_extractor  ─┤ → ticket_creator → quality_critic → END
    └─ passthrough        ─┘
"""
from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from src.graph.state import AgentState

logger = logging.getLogger(__name__)


# ── Import real agent functions ───────────────────────────────────────────────
from src.agents.rag_loader       import rag_loader_node
from src.agents.csv_reader       import csv_reader_node
from src.agents.classifier       import classifier_node
from src.agents.bug_analyzer     import bug_analyzer_node
from src.agents.feature_extractor import feature_extractor_node
from src.agents.ticket_creator   import ticket_creator_node
from src.agents.quality_critic   import quality_critic_node


def passthrough_node(state: AgentState) -> dict:
    """Praise / Complaint / Spam — no deep analysis; pass straight to ticket_creator."""
    return {}


# ── Conditional router ────────────────────────────────────────────────────────

def route_after_classify(state: AgentState) -> str:
    """
    Route to the analysis node needed for this batch.
    Bug takes priority; then Feature Request; else passthrough.
    """
    items = state.get("classified_items", [])
    cats = {c.classification.category for c in items}
    if "Bug" in cats:
        return "bug"
    if "Feature Request" in cats:
        return "feature"
    return "other"


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("rag_loader",          rag_loader_node)
    builder.add_node("csv_reader",          csv_reader_node)
    builder.add_node("classifier",          classifier_node)
    builder.add_node("bug_analyzer",        bug_analyzer_node)
    builder.add_node("feature_extractor",   feature_extractor_node)
    builder.add_node("passthrough",         passthrough_node)
    builder.add_node("ticket_creator",      ticket_creator_node)
    builder.add_node("quality_critic",      quality_critic_node)

    builder.add_edge(START,         "rag_loader")
    builder.add_edge("rag_loader",  "csv_reader")
    builder.add_edge("csv_reader",  "classifier")

    builder.add_conditional_edges(
        "classifier",
        route_after_classify,
        {"bug": "bug_analyzer", "feature": "feature_extractor", "other": "passthrough"},
    )

    builder.add_edge("bug_analyzer",      "ticket_creator")
    builder.add_edge("feature_extractor", "ticket_creator")
    builder.add_edge("passthrough",       "ticket_creator")
    builder.add_edge("ticket_creator",    "quality_critic")
    builder.add_edge("quality_critic",    END)

    return builder


def compile_graph():
    return build_graph().compile()


# ── Public runner ─────────────────────────────────────────────────────────────

def run_pipeline(
    data_dir: str | None = None,
    output_dir: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    graph = compile_graph()
    initial: AgentState = {
        "feedback_items":   [],
        "classified_items": [],
        "bug_details":      [],
        "feature_details":  [],
        "tickets":          [],
        "qc_results":       [],
        "tech_doc_context": [],
        "log_entries":      [],
        "errors":           [],
        "metrics":          {
            **({"data_dir_override": data_dir}   if data_dir   else {}),
            **({"output_dir_override": output_dir} if output_dir else {}),
            **({"dry_run": True}                 if dry_run    else {}),
        },
        "run_id": "",
    }
    logger.info("Pipeline starting (dry_run=%s)", dry_run)
    result = graph.invoke(initial)
    logger.info("Pipeline complete — run_id=%s tickets=%d",
                result.get("run_id"), len(result.get("tickets", [])))
    return result
