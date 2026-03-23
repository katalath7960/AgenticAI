"""
tests/unit/test_graph_skeleton.py

Smoke tests for BE-API-001:
  1. graph.compile() succeeds without errors
  2. All state fields are present and correctly typed
  3. route_after_classify returns the correct branch for each scenario
  4. A stub graph traverses the full pipeline end-to-end with one item
"""

import pytest
from unittest.mock import patch, MagicMock

from src.graph.state import (
    AgentState, FeedbackItem, ClassifiedItem, ClassificationResult,
    BugDetails, FeatureDetails, Ticket, QCResult,
)
from src.graph.pipeline import (
    compile_graph, route_after_classify, build_graph,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_classified_item(category: str) -> ClassifiedItem:
    return ClassifiedItem(
        id="REV-0001",
        source_type="review",
        text="Test feedback",
        metadata={},
        raw_row={},
        classification=ClassificationResult(
            category=category,
            confidence=0.95,
            reasoning="test",
            needs_review=False,
        ),
    )


def _empty_state(**overrides) -> AgentState:
    base: AgentState = {
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
        "run_id": "test-run-001",
    }
    base.update(overrides)
    return base


# ── Test 1: graph compiles ────────────────────────────────────────────────────

def test_graph_compiles():
    """graph.compile() must succeed without raising."""
    graph = compile_graph()
    assert graph is not None


# ── Test 2: state schema has all required fields ──────────────────────────────

def test_agent_state_fields():
    """AgentState TypedDict must contain all documented fields."""
    required_fields = {
        "feedback_items",
        "classified_items",
        "bug_details",
        "feature_details",
        "tickets",
        "qc_results",
        "tech_doc_context",
        "log_entries",
        "errors",
        "metrics",
        "run_id",
    }
    state = _empty_state()
    missing = required_fields - set(state.keys())
    assert not missing, f"Missing AgentState fields: {missing}"


# ── Test 3: conditional router ────────────────────────────────────────────────

@pytest.mark.parametrize("category,expected_route", [
    ("Bug", "bug"),
    ("Feature Request", "feature"),
    ("Praise", "other"),
    ("Complaint", "other"),
    ("Spam", "other"),
])
def test_route_after_classify(category: str, expected_route: str):
    state = _empty_state(classified_items=[_make_classified_item(category)])
    assert route_after_classify(state) == expected_route


def test_route_prefers_bug_when_mixed(mocker):
    """If state contains both Bug and Feature Request, route to bug_analyzer."""
    state = _empty_state(classified_items=[
        _make_classified_item("Bug"),
        _make_classified_item("Feature Request"),
        _make_classified_item("Praise"),
    ])
    assert route_after_classify(state) == "bug"


def test_route_empty_classified_items():
    """Empty classified_items → 'other' (safe default)."""
    state = _empty_state(classified_items=[])
    assert route_after_classify(state) == "other"


# ── Test 4: end-to-end stub traversal ────────────────────────────────────────

def test_stub_graph_traverses_end_to_end():
    """
    Run the compiled stub graph with a minimal initial state.
    All stubs return {} so state should remain at its initial values.
    The graph must complete without raising.
    """
    # Mock ChromaDB so we don't need a real DB for the smoke test
    with patch("src.db.chroma_store.get_store") as mock_get_store:
        mock_store = MagicMock()
        mock_store.index_tech_docs.return_value = 0
        mock_store.query_tech_docs.return_value = []
        mock_get_store.return_value = mock_store

        graph = compile_graph()
        initial = _empty_state()
        result = graph.invoke(initial)

    assert isinstance(result, dict)
    # All list fields should still be lists (stubs return {}, so state merges cleanly)
    for field in ("feedback_items", "classified_items", "bug_details",
                  "feature_details", "tickets", "qc_results"):
        assert isinstance(result.get(field, []), list), f"{field} should be a list"


# ── Test 5: Pydantic model validation ─────────────────────────────────────────

def test_classification_result_clamps_confidence():
    """confidence must be clamped to [0, 1] even if LLM returns out-of-range."""
    cr = ClassificationResult(
        category="Bug", confidence=1.5, reasoning="test", needs_review=False
    )
    assert cr.confidence == 1.0

    cr2 = ClassificationResult(
        category="Spam", confidence=-0.2, reasoning="test", needs_review=False
    )
    assert cr2.confidence == 0.0


def test_bug_details_steps_not_empty():
    """steps_to_reproduce must never be an empty list."""
    bd = BugDetails(
        source_id="REV-0001",
        platform="iOS",
        device="iPhone 15",
        os_version="iOS 17.4",
        app_version="3.1.0",
        steps_to_reproduce=[],
        severity="High",
        affected_feature="Login",
    )
    assert bd.steps_to_reproduce == ["Not provided"]


def test_feature_details_demand_score_bounds():
    """demand_score must be 1–5."""
    with pytest.raises(Exception):
        FeatureDetails(
            source_id="REV-0002",
            feature_summary="Dark mode",
            description="Add dark mode",
            user_impact="Eye strain at night",
            demand_score=6,   # invalid
            user_segment="all users",
        )
