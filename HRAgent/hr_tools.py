"""
hr_tools.py — LangChain @tool definitions for the HR Agent.

All tools return plain strings (JSON-encoded where structured data is needed)
so the LLM can reason about the results naturally.
"""

from __future__ import annotations

import json
from datetime import date, datetime

from langchain_core.tools import tool

import hr_database as db


def _json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


# ── Employee tools ────────────────────────────────────────────────────────────

@tool
def lookup_employee(query: str) -> str:
    """Search for employees by name, department, or role.
    Returns a list of matching employees with their id, name, department, and role.
    Use this before calling get_employee_details to find the employee id.
    """
    results = db.search_employees(query)
    if not results:
        return f"No employees found matching '{query}'."
    simplified = [
        {"id": e["id"], "name": e["name"], "department": e["department"], "role": e["role"]}
        for e in results
    ]
    return _json(simplified)


@tool
def get_employee_details(employee_id: int) -> str:
    """Get the full profile of an employee including their manager and leave balance.
    Args:
        employee_id: The numeric employee id (use lookup_employee first to find it).
    """
    emp = db.get_employee(employee_id)
    if not emp:
        return f"No employee found with id {employee_id}."
    return _json(emp)


@tool
def check_leave_balance(employee_id: int) -> str:
    """Check how many leave days an employee has remaining.
    Args:
        employee_id: The numeric employee id.
    """
    balance = db.get_leave_balance(employee_id)
    if balance is None:
        return f"No employee found with id {employee_id}."
    emp = db.get_employee(employee_id)
    name = emp["name"] if emp else f"Employee {employee_id}"
    return f"{name} has {balance} leave days remaining."


# ── Leave management tools ────────────────────────────────────────────────────

@tool
def apply_for_leave(
    employee_id: int,
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str,
) -> str:
    """Submit a leave request on behalf of an employee.
    Args:
        employee_id: The numeric employee id.
        leave_type: One of 'annual', 'sick', or 'personal'.
        start_date: Start date in YYYY-MM-DD format.
        end_date:   End date in YYYY-MM-DD format.
        reason:     Reason for the leave.
    """
    if leave_type not in ("annual", "sick", "personal"):
        return "Invalid leave_type. Must be 'annual', 'sick', or 'personal'."

    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        return "Invalid date format. Use YYYY-MM-DD."

    if end < start:
        return "end_date cannot be before start_date."

    days = (end - start).days + 1
    balance = db.get_leave_balance(employee_id)
    if balance is None:
        return f"No employee found with id {employee_id}."
    if leave_type == "annual" and days > balance:
        return (
            f"Insufficient annual leave balance. "
            f"Requested {days} days but only {balance} remaining."
        )

    request_id = db.create_leave_request(
        employee_id, leave_type, start_date, end_date, days, reason
    )
    return (
        f"Leave request submitted successfully. "
        f"Request ID: {request_id} | Type: {leave_type} | "
        f"Dates: {start_date} to {end_date} ({days} days) | Status: pending."
    )


@tool
def get_leave_requests(employee_id: int, status: str = "all") -> str:
    """Retrieve leave request history for an employee.
    Args:
        employee_id: The numeric employee id.
        status: Filter by status — 'pending', 'approved', 'rejected', or 'all' (default).
    """
    records = db.get_leave_requests(employee_id, status)
    if not records:
        return f"No leave requests found for employee {employee_id} with status '{status}'."
    return _json(records)


@tool
def approve_leave(request_id: int, approved: bool, note: str = "") -> str:
    """Approve or reject a leave request (manager action).
    Args:
        request_id: The leave request id.
        approved:   True to approve, False to reject.
        note:       Optional manager note.
    """
    new_status = "approved" if approved else "rejected"
    success = db.update_leave_status(request_id, new_status)
    if not success:
        return f"No leave request found with id {request_id}."
    action = "approved" if approved else "rejected"
    msg = f"Leave request {request_id} has been {action}."
    if note:
        msg += f" Manager note: {note}"
    return msg


# ── Policy search tool ────────────────────────────────────────────────────────

@tool
def search_hr_policy(query: str) -> str:
    """Search HR policies using a keyword query. Returns the most relevant policy content.
    Use this to answer questions about leave rules, benefits, code of conduct,
    recruitment policies, and other HR-related topics.
    Args:
        query: Keywords to search for (e.g. 'annual leave carryover', 'referral bonus').
    """
    results = db.search_policies(query, limit=3)
    if not results:
        return f"No HR policies found matching '{query}'."
    parts = []
    for p in results:
        parts.append(f"[{p['category'].upper()}] {p['title']}\n{p['content']}")
    return "\n\n---\n\n".join(parts)


# ── Job / Recruitment tools ───────────────────────────────────────────────────

@tool
def list_job_openings(department: str = "") -> str:
    """List all open job positions, optionally filtered by department.
    Args:
        department: Optional department name to filter (e.g. 'Engineering', 'HR', 'Marketing').
                    Leave empty to see all open positions.
    """
    jobs = db.list_jobs(department=department, status="open")
    if not jobs:
        dept_msg = f" in {department}" if department else ""
        return f"No open positions found{dept_msg}."
    simplified = [
        {
            "id": j["id"],
            "title": j["title"],
            "department": j["department"],
            "requirements": j["requirements"],
            "posted_date": j["posted_date"],
        }
        for j in jobs
    ]
    return _json(simplified)


@tool
def post_job(
    title: str,
    department: str,
    description: str,
    requirements: str,
) -> str:
    """Create a new job posting.
    Args:
        title:        Job title (e.g. 'Senior Python Developer').
        department:   Department name (e.g. 'Engineering').
        description:  Full job description.
        requirements: Required skills and qualifications.
    """
    job_id = db.create_job(title, department, description, requirements)
    return (
        f"Job posting created successfully. "
        f"Job ID: {job_id} | Title: '{title}' | Department: {department} | "
        f"Status: open | Posted: {date.today().isoformat()}"
    )


@tool
def submit_application(
    job_id: int,
    name: str,
    email: str,
    resume_summary: str,
) -> str:
    """Submit a job application for an open position.
    Args:
        job_id:          The numeric job id (use list_job_openings to find it).
        name:            Applicant's full name.
        email:           Applicant's email address.
        resume_summary:  Brief summary of the applicant's experience and skills.
    """
    jobs = db.list_jobs(status="open")
    job_ids = {j["id"] for j in jobs}
    if job_id not in job_ids:
        return f"Job id {job_id} does not exist or is no longer open."
    applicant_id = db.create_applicant(job_id, name, email, resume_summary)
    return (
        f"Application submitted successfully. "
        f"Applicant ID: {applicant_id} | Name: {name} | Job ID: {job_id} | "
        f"Status: applied | Date: {date.today().isoformat()}"
    )


@tool
def list_applicants(job_id: int) -> str:
    """List all applicants for a specific job posting.
    Args:
        job_id: The numeric job id.
    """
    applicants = db.list_applicants_for_job(job_id)
    if not applicants:
        return f"No applicants found for job id {job_id}."
    return _json(applicants)


@tool
def update_applicant_status(applicant_id: int, status: str) -> str:
    """Update the recruitment pipeline status of a job applicant.
    Args:
        applicant_id: The numeric applicant id.
        status: New status — one of 'applied', 'screening', 'interview', 'offered', 'rejected'.
    """
    valid = {"applied", "screening", "interview", "offered", "rejected"}
    if status not in valid:
        return f"Invalid status '{status}'. Must be one of: {', '.join(sorted(valid))}."
    success = db.update_applicant_status(applicant_id, status)
    if not success:
        return f"No applicant found with id {applicant_id}."
    return f"Applicant {applicant_id} status updated to '{status}'."


# ── Tool registry ─────────────────────────────────────────────────────────────

ALL_TOOLS = [
    lookup_employee,
    get_employee_details,
    check_leave_balance,
    apply_for_leave,
    get_leave_requests,
    approve_leave,
    search_hr_policy,
    list_job_openings,
    post_job,
    submit_application,
    list_applicants,
    update_applicant_status,
]
