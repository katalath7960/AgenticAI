"""
hr_database.py — SQLite data layer for the HR Agent.

Schema:
  employees        — master employee directory
  leave_requests   — leave applications
  jobs             — job postings
  applicants       — job applicants
  hr_policies      — policy documents
  hr_policies_fts  — FTS5 virtual table for full-text policy search

Call init_db() once at startup; it is idempotent.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("HR_DB_PATH", "hr_data.db")


# ── Connection ────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _rows_to_dicts(rows) -> list[dict[str, Any]]:
    return [dict(r) for r in rows]


# ── Schema ────────────────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS employees (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    UNIQUE NOT NULL,
    department    TEXT    NOT NULL,
    role          TEXT    NOT NULL,
    manager_id    INTEGER REFERENCES employees(id),
    join_date     TEXT    NOT NULL,
    leave_balance INTEGER NOT NULL DEFAULT 20
);

CREATE TABLE IF NOT EXISTS leave_requests (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    leave_type  TEXT    NOT NULL CHECK(leave_type IN ('annual','sick','personal')),
    start_date  TEXT    NOT NULL,
    end_date    TEXT    NOT NULL,
    days        INTEGER NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending','approved','rejected')),
    reason      TEXT,
    created_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    department   TEXT NOT NULL,
    description  TEXT NOT NULL,
    requirements TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'open'
                 CHECK(status IN ('open','closed','filled')),
    posted_date  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS applicants (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id         INTEGER NOT NULL REFERENCES jobs(id),
    name           TEXT    NOT NULL,
    email          TEXT    NOT NULL,
    resume_summary TEXT,
    status         TEXT NOT NULL DEFAULT 'applied'
                   CHECK(status IN ('applied','screening','interview','offered','rejected')),
    applied_date   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hr_policies (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    title    TEXT NOT NULL UNIQUE,
    content  TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS hr_policies_fts
USING fts5(category, title, content, content='hr_policies', content_rowid='id');
"""

# ── Seed data ─────────────────────────────────────────────────────────────────

_SEED_EMPLOYEES = [
    (1, "Alice Johnson",  "alice@edureka.com",   "Engineering",  "VP of Engineering",   None, "2019-03-15", 20),
    (2, "Bob Smith",      "bob@edureka.com",     "Engineering",  "Senior Engineer",     1,    "2020-06-01", 18),
    (3, "Carol White",    "carol@edureka.com",   "Engineering",  "Software Engineer",   1,    "2021-09-10", 15),
    (4, "David Lee",      "david@edureka.com",   "HR",           "HR Manager",          None, "2018-11-20", 20),
    (5, "Eva Martinez",   "eva@edureka.com",     "HR",           "HR Coordinator",      4,    "2022-01-05", 12),
    (6, "Frank Brown",    "frank@edureka.com",   "Marketing",    "Marketing Director",  None, "2017-07-01", 20),
    (7, "Grace Kim",      "grace@edureka.com",   "Marketing",    "Content Strategist",  6,    "2023-03-22", 8),
    (8, "Henry Wilson",   "henry@edureka.com",   "Engineering",  "DevOps Engineer",     1,    "2022-08-15", 16),
]

_SEED_LEAVE = [
    (1, 2, "annual",   "2026-03-10", "2026-03-14", 5, "pending",  "Family vacation",  "2026-02-28T09:00:00"),
    (2, 3, "sick",     "2026-02-20", "2026-02-21", 2, "approved", "Flu",              "2026-02-19T08:30:00"),
    (3, 5, "personal", "2026-03-03", "2026-03-03", 1, "pending",  "Personal errand",  "2026-02-28T10:00:00"),
    (4, 7, "annual",   "2026-04-01", "2026-04-05", 5, "rejected", "Extended holiday", "2026-02-25T14:00:00"),
    (5, 8, "sick",     "2026-02-15", "2026-02-15", 1, "approved", "Doctor visit",     "2026-02-14T17:00:00"),
]

_SEED_JOBS = [
    (1, "Senior Python Developer", "Engineering",
     "Design and build scalable backend services using Python and FastAPI.",
     "5+ years Python, FastAPI or Django, REST APIs, SQL", "open", "2026-02-01"),
    (2, "HR Business Partner", "HR",
     "Partner with business leaders to deliver HR solutions and drive talent strategy.",
     "3+ years HR experience, SHRM certified preferred, strong communication", "open", "2026-02-10"),
    (3, "Growth Marketing Manager", "Marketing",
     "Lead demand-generation campaigns and manage marketing analytics.",
     "4+ years B2B marketing, data-driven mindset, HubSpot experience", "open", "2026-02-15"),
]

_SEED_APPLICANTS = [
    (1, 1, "Priya Nair",    "priya@email.com",   "8 yrs Python, FastAPI expert, led microservices at startup", "interview",  "2026-02-05"),
    (2, 1, "James Taylor",  "james@email.com",   "5 yrs Django/Flask, AWS certified, fintech background",       "screening",  "2026-02-08"),
    (3, 2, "Sara Ahmed",    "sara@email.com",    "SHRM-CP certified, 4 yrs HRBP at MNC",                        "applied",    "2026-02-12"),
    (4, 3, "Leo Garcia",    "leo@email.com",     "6 yrs B2B SaaS marketing, Marketo & HubSpot expert",          "interview",  "2026-02-18"),
]

_SEED_POLICIES = [
    ("leave", "Annual Leave Policy",
     "Full-time employees receive 20 days of annual leave per calendar year. "
     "Leave must be approved by the direct manager at least 5 business days in advance. "
     "Unused leave up to 10 days may be carried over to the next year. "
     "Leave encashment is available on separation from the company."),

    ("leave", "Sick Leave Policy",
     "Employees are entitled to 10 days of paid sick leave per year. "
     "A medical certificate is required for absences longer than 2 consecutive days. "
     "Sick leave cannot be carried over and is not encashable. "
     "Chronic illness cases are reviewed individually by HR."),

    ("leave", "Personal Leave Policy",
     "Employees receive 5 personal days per year for personal errands, family events, "
     "or other personal reasons. Personal leave requires 24-hour advance notice. "
     "Personal leave is non-encashable and cannot be carried forward."),

    ("code_of_conduct", "Workplace Code of Conduct",
     "All employees are expected to behave with integrity, respect, and professionalism. "
     "Harassment, discrimination, or bullying of any kind will not be tolerated and may "
     "result in disciplinary action including termination. Conflicts of interest must be "
     "disclosed to the HR department immediately. Confidential company information must "
     "not be shared externally without written approval."),

    ("benefits", "Employee Benefits Overview",
     "Edureka Corp offers a comprehensive benefits package including: "
     "health insurance (medical, dental, vision) for employee and dependents; "
     "provident fund with company matching up to 6% of basic salary; "
     "annual performance bonus (5-20% of annual CTC based on rating); "
     "professional development budget of INR 50,000 per year; "
     "flexible work-from-home policy (up to 3 days per week for eligible roles); "
     "employee stock option plan (ESOP) for senior roles."),

    ("recruitment", "Internal Referral Policy",
     "Employees can refer external candidates for open positions. "
     "If a referred candidate is hired and completes 6 months, the referring employee "
     "receives a referral bonus of INR 25,000 for junior roles or INR 50,000 for senior roles. "
     "Referrals must be submitted through the HR portal before the candidate applies directly. "
     "Employees cannot refer immediate family members."),
]


def init_db() -> None:
    conn = get_db()
    conn.executescript(_SCHEMA)

    # Employees
    conn.executemany(
        "INSERT OR IGNORE INTO employees "
        "(id,name,email,department,role,manager_id,join_date,leave_balance) "
        "VALUES (?,?,?,?,?,?,?,?)",
        _SEED_EMPLOYEES,
    )

    # Leave requests
    conn.executemany(
        "INSERT OR IGNORE INTO leave_requests "
        "(id,employee_id,leave_type,start_date,end_date,days,status,reason,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        _SEED_LEAVE,
    )

    # Jobs
    conn.executemany(
        "INSERT OR IGNORE INTO jobs "
        "(id,title,department,description,requirements,status,posted_date) "
        "VALUES (?,?,?,?,?,?,?)",
        _SEED_JOBS,
    )

    # Applicants
    conn.executemany(
        "INSERT OR IGNORE INTO applicants "
        "(id,job_id,name,email,resume_summary,status,applied_date) "
        "VALUES (?,?,?,?,?,?,?)",
        _SEED_APPLICANTS,
    )

    # Policies
    conn.executemany(
        "INSERT OR IGNORE INTO hr_policies (category,title,content) VALUES (?,?,?)",
        _SEED_POLICIES,
    )

    # Rebuild FTS index
    conn.execute("INSERT OR REPLACE INTO hr_policies_fts(hr_policies_fts) VALUES('rebuild')")
    conn.commit()


# ── Employee CRUD ─────────────────────────────────────────────────────────────

def search_employees(query: str) -> list[dict]:
    conn = get_db()
    q = f"%{query}%"
    rows = conn.execute(
        "SELECT * FROM employees WHERE name LIKE ? OR department LIKE ? OR role LIKE ?",
        (q, q, q),
    ).fetchall()
    return _rows_to_dicts(rows)


def get_employee(employee_id: int) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM employees WHERE id=?", (employee_id,)).fetchone()
    if not row:
        return None
    emp = dict(row)
    if emp.get("manager_id"):
        mgr = conn.execute(
            "SELECT name FROM employees WHERE id=?", (emp["manager_id"],)
        ).fetchone()
        emp["manager_name"] = mgr["name"] if mgr else None
    else:
        emp["manager_name"] = None
    return emp


def list_employees(department: str = "") -> list[dict]:
    conn = get_db()
    if department:
        rows = conn.execute(
            "SELECT * FROM employees WHERE department=?", (department,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM employees").fetchall()
    return _rows_to_dicts(rows)


# ── Leave CRUD ────────────────────────────────────────────────────────────────

def get_leave_balance(employee_id: int) -> int | None:
    conn = get_db()
    row = conn.execute(
        "SELECT leave_balance FROM employees WHERE id=?", (employee_id,)
    ).fetchone()
    return row["leave_balance"] if row else None


def create_leave_request(
    employee_id: int,
    leave_type: str,
    start_date: str,
    end_date: str,
    days: int,
    reason: str,
) -> int:
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO leave_requests "
        "(employee_id,leave_type,start_date,end_date,days,status,reason,created_at) "
        "VALUES (?,?,?,?,?,'pending',?,?)",
        (employee_id, leave_type, start_date, end_date, days, reason,
         datetime.utcnow().isoformat()),
    )
    conn.commit()
    return cursor.lastrowid


def get_leave_requests(employee_id: int, status: str = "all") -> list[dict]:
    conn = get_db()
    if status == "all":
        rows = conn.execute(
            "SELECT * FROM leave_requests WHERE employee_id=? ORDER BY created_at DESC",
            (employee_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM leave_requests WHERE employee_id=? AND status=? "
            "ORDER BY created_at DESC",
            (employee_id, status),
        ).fetchall()
    return _rows_to_dicts(rows)


def update_leave_status(request_id: int, status: str) -> bool:
    conn = get_db()
    cursor = conn.execute(
        "UPDATE leave_requests SET status=? WHERE id=?", (status, request_id)
    )
    conn.commit()
    return cursor.rowcount > 0


# ── Job CRUD ──────────────────────────────────────────────────────────────────

def list_jobs(department: str = "", status: str = "open") -> list[dict]:
    conn = get_db()
    if department:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE department=? AND status=?", (department, status)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE status=?", (status,)
        ).fetchall()
    return _rows_to_dicts(rows)


def create_job(
    title: str, department: str, description: str, requirements: str
) -> int:
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO jobs (title,department,description,requirements,status,posted_date) "
        "VALUES (?,?,?,?,'open',?)",
        (title, department, description, requirements, date.today().isoformat()),
    )
    conn.commit()
    return cursor.lastrowid


# ── Applicant CRUD ────────────────────────────────────────────────────────────

def list_applicants_for_job(job_id: int) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM applicants WHERE job_id=? ORDER BY applied_date DESC", (job_id,)
    ).fetchall()
    return _rows_to_dicts(rows)


def create_applicant(
    job_id: int, name: str, email: str, resume_summary: str
) -> int:
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO applicants (job_id,name,email,resume_summary,status,applied_date) "
        "VALUES (?,?,?,?,'applied',?)",
        (job_id, name, email, resume_summary, date.today().isoformat()),
    )
    conn.commit()
    return cursor.lastrowid


def update_applicant_status(applicant_id: int, status: str) -> bool:
    conn = get_db()
    cursor = conn.execute(
        "UPDATE applicants SET status=? WHERE id=?", (status, applicant_id)
    )
    conn.commit()
    return cursor.rowcount > 0


# ── Policy search ─────────────────────────────────────────────────────────────

def search_policies(query: str, limit: int = 3) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT p.id, p.category, p.title, p.content "
        "FROM hr_policies_fts f "
        "JOIN hr_policies p ON p.id = f.rowid "
        "WHERE hr_policies_fts MATCH ? "
        "ORDER BY rank LIMIT ?",
        (query, limit),
    ).fetchall()
    if not rows:
        # Fallback to LIKE search
        q = f"%{query}%"
        rows = conn.execute(
            "SELECT id, category, title, content FROM hr_policies "
            "WHERE title LIKE ? OR content LIKE ? OR category LIKE ? LIMIT ?",
            (q, q, q, limit),
        ).fetchall()
    return _rows_to_dicts(rows)


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    conn = get_db()
    print("Employees:", conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0])
    print("Leave requests:", conn.execute("SELECT COUNT(*) FROM leave_requests").fetchone()[0])
    print("Jobs:", conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0])
    print("Applicants:", conn.execute("SELECT COUNT(*) FROM applicants").fetchone()[0])
    print("Policies:", conn.execute("SELECT COUNT(*) FROM hr_policies").fetchone()[0])
    print("Database initialised at:", DB_PATH)
