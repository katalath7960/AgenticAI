"""
src/graph/state.py — AgentState and all Pydantic data models.

Flow:  FeedbackItem → ClassifiedItem → BugDetails / FeatureDetails → Ticket → QCResult
"""
from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

from pydantic import BaseModel, Field, field_validator


# ── Raw input ─────────────────────────────────────────────────────────────────

class FeedbackItem(BaseModel):
    id: str
    source_type: Literal["review", "email"]
    text: str
    metadata: dict[str, Any]
    raw_row: dict[str, Any]


# ── Classifier output ─────────────────────────────────────────────────────────

class ClassificationResult(BaseModel):
    category: Literal["Bug", "Feature Request", "Praise", "Complaint", "Spam"]
    confidence: float
    reasoning: str
    needs_review: bool

    @field_validator("confidence")
    @classmethod
    def clamp(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ClassifiedItem(FeedbackItem):
    classification: ClassificationResult
    similar_reviews: list[dict[str, Any]] = Field(default_factory=list)


# ── Bug Analyzer output ───────────────────────────────────────────────────────

class BugDetails(BaseModel):
    source_id: str
    platform: str
    device: str
    os_version: str
    app_version: str
    steps_to_reproduce: list[str]
    severity: Literal["Critical", "High", "Medium", "Low"]
    affected_feature: str
    similar_bugs: list[dict[str, Any]] = Field(default_factory=list)
    product_context: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("steps_to_reproduce")
    @classmethod
    def ensure_list(cls, v: list[str]) -> list[str]:
        return v if v else ["Not provided"]


# ── Feature Extractor output ──────────────────────────────────────────────────

class FeatureDetails(BaseModel):
    source_id: str
    feature_summary: str
    description: str
    user_impact: str
    demand_score: int = Field(ge=1, le=5)
    user_segment: str
    is_duplicate: bool = False
    duplicate_of: str | None = None
    similar_features: list[dict[str, Any]] = Field(default_factory=list)
    product_context: list[dict[str, Any]] = Field(default_factory=list)


# ── Ticket Creator output ─────────────────────────────────────────────────────

class Ticket(BaseModel):
    ticket_id: str
    source_id: str
    source_type: Literal["review", "email"]
    title: str
    description: str
    category: Literal["Bug", "Feature Request", "Complaint"]
    priority: Literal["Critical", "High", "Medium", "Low"]
    severity: str = ""
    assignee_team: Literal["Engineering", "Product", "Support"]
    tags: str = ""
    created_at: str
    status: Literal["open", "needs_review", "in_progress", "resolved", "closed"] = "open"
    is_duplicate: bool = False
    duplicate_of: str | None = None


# ── Quality Critic output ─────────────────────────────────────────────────────

class QCResult(BaseModel):
    ticket_id: str
    passed: bool
    failed_rules: list[str] = Field(default_factory=list)
    qc_notes: str = ""
    llm_completeness_score: int | None = None
    llm_suggestions: str = ""
    priority_escalated: bool = False


# ── Processing log ────────────────────────────────────────────────────────────

class LogEntry(BaseModel):
    log_id: str
    source_id: str
    stage: str
    result: Literal["success", "skipped", "error"]
    details: str = ""
    timestamp: str


# ── Shared AgentState ─────────────────────────────────────────────────────────

class AgentState(TypedDict):
    feedback_items:   list[FeedbackItem]
    classified_items: list[ClassifiedItem]
    bug_details:      list[BugDetails]
    feature_details:  list[FeatureDetails]
    tickets:          list[Ticket]
    qc_results:       list[QCResult]
    tech_doc_context: list[dict[str, Any]]
    log_entries:      Annotated[list[LogEntry], operator.add]
    errors:           Annotated[list[str],      operator.add]
    metrics:          dict[str, Any]
    run_id:           str
