"""
api.py — FastAPI REST API for the HR Agent.

Endpoints:
  POST /chat                    → HR agent chat
  GET  /employees               → list employees (optional ?department=)
  GET  /employees/{id}          → employee detail
  GET  /leave/{employee_id}     → leave history (optional ?status=)
  POST /leave                   → submit leave request
  PUT  /leave/{id}/approve      → approve or reject
  GET  /jobs                    → list open jobs (optional ?department=)
  POST /jobs                    → create job posting
  GET  /jobs/{id}/applicants    → list applicants
  POST /jobs/{id}/apply         → submit application
  PUT  /applicants/{id}/status  → update applicant pipeline status
  GET  /                        → health check
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import hr_database as db
from hr_agent import run as agent_run
from hr_database import init_db

# Initialise DB on startup
init_db()

app = FastAPI(title="HR Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str


class LeaveRequest(BaseModel):
    employee_id: int
    leave_type: str = Field(..., pattern="^(annual|sick|personal)$")
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    reason: str = ""


class ApproveLeaveRequest(BaseModel):
    approved: bool
    note: str = ""


class JobPostRequest(BaseModel):
    title: str = Field(..., min_length=1)
    department: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    requirements: str = Field(..., min_length=1)


class ApplicationRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    resume_summary: str = ""


class ApplicantStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(applied|screening|interview|offered|rejected)$")


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "hr-agent-api"}


# ── Chat ──────────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    history = [m.model_dump() for m in request.history]
    answer = agent_run(request.message, history)
    return ChatResponse(answer=answer)


# ── Employees ─────────────────────────────────────────────────────────────────

@app.get("/employees")
def list_employees(department: str = "") -> list[dict[str, Any]]:
    return db.list_employees(department)


@app.get("/employees/{employee_id}")
def get_employee(employee_id: int) -> dict[str, Any]:
    emp = db.get_employee(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    return emp


# ── Leave ─────────────────────────────────────────────────────────────────────

@app.get("/leave/{employee_id}")
def get_leave(employee_id: int, status: str = "all") -> list[dict[str, Any]]:
    return db.get_leave_requests(employee_id, status)


@app.post("/leave", status_code=201)
def submit_leave(request: LeaveRequest) -> dict[str, Any]:
    from datetime import date as _date
    try:
        start = _date.fromisoformat(request.start_date)
        end = _date.fromisoformat(request.end_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format. Use YYYY-MM-DD.")
    if end < start:
        raise HTTPException(status_code=422, detail="end_date cannot be before start_date.")
    days = (end - start).days + 1
    balance = db.get_leave_balance(request.employee_id)
    if balance is None:
        raise HTTPException(status_code=404, detail=f"Employee {request.employee_id} not found.")
    if request.leave_type == "annual" and days > balance:
        raise HTTPException(
            status_code=422,
            detail=f"Insufficient leave balance. Requested {days} days, balance is {balance}.",
        )
    request_id = db.create_leave_request(
        request.employee_id,
        request.leave_type,
        request.start_date,
        request.end_date,
        days,
        request.reason,
    )
    return {"id": request_id, "days": days, "status": "pending"}


@app.put("/leave/{request_id}/approve")
def approve_leave(request_id: int, body: ApproveLeaveRequest) -> dict[str, Any]:
    new_status = "approved" if body.approved else "rejected"
    success = db.update_leave_status(request_id, new_status)
    if not success:
        raise HTTPException(status_code=404, detail=f"Leave request {request_id} not found.")
    return {"id": request_id, "status": new_status, "note": body.note}


# ── Jobs ──────────────────────────────────────────────────────────────────────

@app.get("/jobs")
def list_jobs(department: str = "") -> list[dict[str, Any]]:
    return db.list_jobs(department=department, status="open")


@app.post("/jobs", status_code=201)
def create_job(request: JobPostRequest) -> dict[str, Any]:
    job_id = db.create_job(
        request.title, request.department, request.description, request.requirements
    )
    return {"id": job_id, "title": request.title, "status": "open"}


@app.get("/jobs/{job_id}/applicants")
def get_applicants(job_id: int) -> list[dict[str, Any]]:
    return db.list_applicants_for_job(job_id)


@app.post("/jobs/{job_id}/apply", status_code=201)
def apply_for_job(job_id: int, request: ApplicationRequest) -> dict[str, Any]:
    jobs = db.list_jobs(status="open")
    if job_id not in {j["id"] for j in jobs}:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found or not open.")
    applicant_id = db.create_applicant(
        job_id, request.name, request.email, request.resume_summary
    )
    return {"id": applicant_id, "job_id": job_id, "status": "applied"}


# ── Applicants ────────────────────────────────────────────────────────────────

@app.put("/applicants/{applicant_id}/status")
def update_status(applicant_id: int, body: ApplicantStatusRequest) -> dict[str, Any]:
    success = db.update_applicant_status(applicant_id, body.status)
    if not success:
        raise HTTPException(status_code=404, detail=f"Applicant {applicant_id} not found.")
    return {"id": applicant_id, "status": body.status}
