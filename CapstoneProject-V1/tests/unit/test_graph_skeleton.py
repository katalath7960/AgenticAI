"""
tests/unit/test_graph_skeleton.py — Smoke tests for BE-API-001.
Zero real API or ChromaDB calls.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from src.graph.state import (
    AgentState, FeedbackItem, ClassifiedItem, ClassificationResult,
    BugDetails, FeatureDetails, Ticket, QCResult,
)
from src.graph.pipeline import compile_graph, route_after_classify


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _classified(category: str) -> ClassifiedItem:
    return ClassifiedItem(
        id="REV-0001", source_type="review", text="test", metadata={}, raw_row={},
        classification=ClassificationResult(
            category=category, confidence=0.95, reasoning="test", needs_review=False,
        ),
    )


def _empty_state(**overrides) -> AgentState:
    base: AgentState = {
        "feedback_items": [], "classified_items": [], "bug_details": [],
        "feature_details": [], "tickets": [], "qc_results": [],
        "tech_doc_context": [], "log_entries": [], "errors": [],
        "metrics": {}, "run_id": "test-run",
    }
    base.update(overrides)
    return base


# ── 1. Graph compiles ─────────────────────────────────────────────────────────

def test_graph_compiles():
    assert compile_graph() is not None


# ── 2. State has all required fields ─────────────────────────────────────────

def test_agent_state_has_all_fields():
    required = {"feedback_items", "classified_items", "bug_details", "feature_details",
                "tickets", "qc_results", "tech_doc_context", "log_entries",
                "errors", "metrics", "run_id"}
    assert required <= set(_empty_state().keys())


# ── 3. Router — one category ──────────────────────────────────────────────────

@pytest.mark.parametrize("category,expected", [
    ("Bug",             "bug"),
    ("Feature Request", "feature"),
    ("Praise",          "other"),
    ("Complaint",       "other"),
    ("Spam",            "other"),
])
def test_route_single_category(category, expected):
    state = _empty_state(classified_items=[_classified(category)])
    assert route_after_classify(state) == expected


# ── 4. Router — mixed batch prefers Bug ───────────────────────────────────────

def test_route_prefers_bug_in_mixed_batch():
    state = _empty_state(classified_items=[
        _classified("Feature Request"),
        _classified("Bug"),
        _classified("Praise"),
    ])
    assert route_after_classify(state) == "bug"


# ── 5. Router — empty list ────────────────────────────────────────────────────

def test_route_empty_classified_items():
    assert route_after_classify(_empty_state()) == "other"


# ── 6. End-to-end stub traversal (ChromaDB mocked) ───────────────────────────

def test_stub_graph_traverses_end_to_end():
    # Agents bind `get_store` locally on import, so patching the function
    # object in src.db.chroma_store doesn't reach them.  Patching the
    # module-level singleton `_store` does — get_store() reads that global
    # and returns it directly when it is not None.
    import src.db.chroma_store as _chroma_mod

    mock_store = MagicMock()
    mock_store.index_tech_docs.return_value = 0
    mock_store.query_tech_docs.return_value = []
    mock_store.find_similar_reviews.return_value = []
    mock_store.find_similar_tickets.return_value = []

    # Point data_dir at a non-existent path so csv_reader returns zero items
    # and classifier never makes real LLM calls.
    state = _empty_state(metrics={"data_dir_override": "/nonexistent/__test__"})

    with patch.object(_chroma_mod, "_store", mock_store):
        graph = compile_graph()
        result = graph.invoke(state)

    assert isinstance(result, dict)
    for field in ("feedback_items", "classified_items", "bug_details",
                  "feature_details", "tickets", "qc_results"):
        assert isinstance(result.get(field, []), list)


# ── 7. Confidence clamping ────────────────────────────────────────────────────

def test_classification_confidence_clamped_high():
    cr = ClassificationResult(category="Bug", confidence=1.8, reasoning="x", needs_review=False)
    assert cr.confidence == 1.0


def test_classification_confidence_clamped_low():
    cr = ClassificationResult(category="Spam", confidence=-0.3, reasoning="x", needs_review=False)
    assert cr.confidence == 0.0


# ── 8. BugDetails steps_to_reproduce default ─────────────────────────────────

def test_bug_details_empty_steps_become_not_provided():
    bd = BugDetails(
        source_id="x", platform="iOS", device="iPhone 15",
        os_version="iOS 17", app_version="3.1.0",
        steps_to_reproduce=[], severity="High", affected_feature="Login",
    )
    assert bd.steps_to_reproduce == ["Not provided"]


def test_bug_details_steps_preserved_when_given():
    bd = BugDetails(
        source_id="x", platform="iOS", device="iPhone 15",
        os_version="iOS 17", app_version="3.1.0",
        steps_to_reproduce=["Open app", "Tap login"], severity="High", affected_feature="Login",
    )
    assert bd.steps_to_reproduce == ["Open app", "Tap login"]


# ── 9. FeatureDetails demand_score bounds ────────────────────────────────────

def test_feature_demand_score_too_high_rejected():
    with pytest.raises(Exception):
        FeatureDetails(
            source_id="x", feature_summary="Dark mode",
            description="Add dark mode", user_impact="eye strain",
            demand_score=6, user_segment="all users",
        )


def test_feature_demand_score_too_low_rejected():
    with pytest.raises(Exception):
        FeatureDetails(
            source_id="x", feature_summary="Dark mode",
            description="Add dark mode", user_impact="eye strain",
            demand_score=0, user_segment="all users",
        )


# ── 10. QC auto-escalation keyword check ─────────────────────────────────────

def test_qc_escalation_keywords():
    """quality_critic should escalate priority to Critical when desc contains 'crash'."""
    from src.agents.quality_critic import ESCALATION_KEYWORDS
    assert "crash" in ESCALATION_KEYWORDS
    assert "data loss" in ESCALATION_KEYWORDS


# ── 11. Log entry accumulation (operator.add) ────────────────────────────────

def test_log_entries_accumulate_across_nodes():
    from src.graph.state import LogEntry
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).isoformat()
    entry = LogEntry(log_id="l1", source_id="REV-0001", stage="test",
                     result="success", timestamp=ts)
    state = _empty_state(log_entries=[entry])
    # operator.add means new entries append to existing
    assert len(state["log_entries"]) == 1
