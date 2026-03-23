"""
src/graph/state.py

Defines the shared AgentState (TypedDict) that flows through the LangGraph
pipeline, plus all Pydantic models used as typed containers inside state.

Model hierarchy
---------------
FeedbackItem          raw normalised input (from CSV Reader)
  └─ ClassifiedItem   + classification (from Classifier)
       ├─ BugDetails          (from Bug Analyzer)
       ├─ FeatureDetails      (from Feature Extractor)
       └─ Ticket              (from Ticket Creator)
            └─ QCResult       (from Quality Critic)

RAG context is carried alongside the items so each agent can read what the
previous agents and the vector store retrieved without re-querying.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, TypedDict
import operator
from pydantic import BaseModel, Field, field_validator


# ══════════════════════════════════════════════════════════════════════════════
# Core input model
# ══════════════════════════════════════════════════════════════════════════════

class FeedbackItem(BaseModel):
    """
    Normalised representation of a single piece of user feedback.
    Produced by the CSV Reader node from either app_store_reviews or
    support_emails.
    """
    id: str
    source_type: Literal["review", "email"]
    text: str                   # review_text or concatenated subject + body
    metadata: dict[str, Any]   # platform/rating (review) or subject/priority (email)
    raw_row: dict[str, Any]    # original CSV row for traceability


# ══════════════════════════════════════════════════════════════════════════════
# Classifier output
# ══════════════════════════════════════════════════════════════════════════════

class ClassificationResult(BaseModel):
    category: Literal["Bug", "Feature Request", "Praise", "Complaint", "Spam"]
    confidence: float
    reasoning: str
    needs_review: bool          # True when confidence < CLASSIFICATION_THRESHOLD

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ClassifiedItem(FeedbackItem):
    """FeedbackItem enriched with classification output."""
    classification: ClassificationResult

    # Context retrieved from ChromaDB *before* classifying — similar past items
    similar_reviews: list[dict[str, Any]] = Field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════════════
# Bug Analyzer output
# ══════════════════════════════════════════════════════════════════════════════

class BugDetails(BaseModel):
    """Structured technical details extracted from a Bug-classified item."""
    source_id: str              # FK → FeedbackItem.id
    platform: str               # "iOS" | "Android" | "Unknown"
    device: str                 # e.g. "iPhone 15" | "Unknown"
    os_version: str             # e.g. "iOS 17.4" | "Unknown"
    app_version: str            # e.g. "3.0.1" | "Unknown"
    steps_to_reproduce: list[str]   # ["Not provided"] when absent
    severity: Literal["Critical", "High", "Medium", "Low"]
    affected_feature: str       # e.g. "Login", "Data Sync", "Unknown"

    # RAG context used during analysis
    similar_bugs: list[dict[str, Any]] = Field(default_factory=list)
    product_context: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("steps_to_reproduce")
    @classmethod
    def ensure_list(cls, v: list[str]) -> list[str]:
        return v if v else ["Not provided"]


# ══════════════════════════════════════════════════════════════════════════════
# Feature Extractor output
# ══════════════════════════════════════════════════════════════════════════════

class FeatureDetails(BaseModel):
    """Structured output for a Feature Request-classified item."""
    source_id: str
    feature_summary: str        # ≤ 15-word title
    description: str            # expanded description
    user_impact: str            # why users need this
    demand_score: int = Field(ge=1, le=5)
    user_segment: str           # "power users" | "all users" | "enterprise" | …
    is_duplicate: bool = False
    duplicate_of: str | None = None   # ticket_id of the original feature request

    # RAG context used during extraction
    similar_features: list[dict[str, Any]] = Field(default_factory=list)
    product_context: list[dict[str, Any]] = Field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════════════
# Ticket Creator output
# ══════════════════════════════════════════════════════════════════════════════

class Ticket(BaseModel):
    """
    A generated engineering/product ticket.
    Maps 1-to-1 with a row in generated_tickets.csv.
    """
    ticket_id: str              # TKT-YYYYMMDD-XXXX
    source_id: str
    source_type: Literal["review", "email"]
    title: str                  # ≤ 80 chars
    description: str            # Markdown: Summary / Steps / Expected Behavior
    category: Literal["Bug", "Feature Request", "Complaint"]
    priority: Literal["Critical", "High", "Medium", "Low"]
    severity: str = ""          # Non-empty for Bugs only
    assignee_team: Literal["Engineering", "Product", "Support"]
    tags: str = ""              # comma-separated: platform, feature area
    created_at: str             # ISO 8601
    status: Literal["open", "needs_review"] = "open"

    # Duplicate detection result from tickets collection
    is_duplicate: bool = False
    duplicate_of: str | None = None     # ticket_id of existing similar ticket


# ══════════════════════════════════════════════════════════════════════════════
# Quality Critic output
# ══════════════════════════════════════════════════════════════════════════════

class QCResult(BaseModel):
    """Per-ticket quality control result."""
    ticket_id: str
    passed: bool
    failed_rules: list[str] = Field(default_factory=list)
    qc_notes: str = ""
    llm_completeness_score: int | None = None   # 1–5, from LLM review
    llm_suggestions: str = ""
    priority_escalated: bool = False    # True if auto-escalated to Critical


# ══════════════════════════════════════════════════════════════════════════════
# Processing log entry
# ══════════════════════════════════════════════════════════════════════════════

class LogEntry(BaseModel):
    log_id: str
    source_id: str
    stage: str                              # node name
    result: Literal["success", "skipped", "error"]
    details: str = ""
    timestamp: str                          # ISO 8601


# ══════════════════════════════════════════════════════════════════════════════
# Shared AgentState — the single object that flows through every node
# ══════════════════════════════════════════════════════════════════════════════

class AgentState(TypedDict):
    # ── Input ─────────────────────────────────────────────────────────────────
    feedback_items: list[FeedbackItem]          # CSV Reader → Classifier

    # ── Per-stage outputs ──────────────────────────────────────────────────────
    classified_items: list[ClassifiedItem]      # Classifier → routers
    bug_details: list[BugDetails]               # Bug Analyzer → Ticket Creator
    feature_details: list[FeatureDetails]       # Feature Extractor → Ticket Creator
    tickets: list[Ticket]                       # Ticket Creator → QC Critic
    qc_results: list[QCResult]                  # Quality Critic → END

    # ── Shared RAG context ────────────────────────────────────────────────────
    # Loaded once at pipeline start and available to all nodes.
    # Each node may append additional retrieved chunks specific to the item.
    tech_doc_context: list[dict[str, Any]]      # from tech_documents collection

    # ── Bookkeeping ───────────────────────────────────────────────────────────
    log_entries: Annotated[list[LogEntry], operator.add]   # accumulates across nodes
    errors: Annotated[list[str], operator.add]             # item-level error strings
    metrics: dict[str, Any]                                # run-level metrics
    run_id: str                                            # UUID for this pipeline run
