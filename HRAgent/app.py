"""
app.py — Streamlit UI for the HR Agent.

Navigation (sidebar):
  Chat        — conversational HR assistant
  Employees   — directory search and detail view
  Leave       — request and history management
  Recruitment — job postings and applicant pipeline
  Policies    — HR policy search
"""

from __future__ import annotations

import os

import httpx
import streamlit as st

API_BASE = os.getenv("HR_API_URL", "http://localhost:8001")

st.set_page_config(page_title="HR Agent — Edureka Corp", layout="wide", page_icon="🏢")

# ── Sidebar navigation ────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🏢 HR Agent")
    st.caption("Edureka Corp · HR Management")
    st.divider()
    page = st.radio(
        "Navigate",
        ["💬 Chat", "👥 Employees", "📅 Leave", "💼 Recruitment", "📋 Policies"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption(f"API: {API_BASE}")


def _api(method: str, path: str, **kwargs):
    try:
        resp = httpx.request(method, f"{API_BASE}{path}", timeout=60, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        st.error("Cannot connect to the HR API. Make sure it is running.")
        return None
    except httpx.HTTPStatusError as e:
        st.error(f"API error {e.response.status_code}: {e.response.text}")
        return None


# ── Chat ──────────────────────────────────────────────────────────────────────

if page == "💬 Chat":
    st.header("💬 HR Assistant")
    st.caption("Ask anything about employees, leave, policies, or job openings.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask the HR agent…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                history = st.session_state.messages[:-1]
                result = _api(
                    "POST",
                    "/chat",
                    json={"message": prompt, "history": history},
                )
            if result:
                answer = result.get("answer", "")
                st.write(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

    if st.session_state.messages:
        if st.button("Clear conversation", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()

    with st.expander("💡 Example questions"):
        st.markdown("""
- Who works in the Engineering department?
- What is Bob Smith's leave balance?
- Apply for 3 days annual leave for employee 2 from 2026-03-10 to 2026-03-12 — vacation.
- What is the company's policy on sick leave?
- List all open job positions.
- What applicants have applied for job 1?
- Move applicant 1 to interview stage.
        """)


# ── Employees ─────────────────────────────────────────────────────────────────

elif page == "👥 Employees":
    st.header("👥 Employee Directory")

    col1, col2 = st.columns([3, 1])
    with col1:
        search_dept = st.text_input("Filter by department", placeholder="Engineering, HR, Marketing…")
    with col2:
        st.write("")
        st.write("")
        search_btn = st.button("Search", use_container_width=True)

    employees = _api("GET", "/employees", params={"department": search_dept} if search_dept else {})

    if employees is not None:
        if not employees:
            st.info("No employees found.")
        else:
            st.caption(f"{len(employees)} employee(s) found")
            import pandas as pd
            df = pd.DataFrame(employees)[
                ["id", "name", "email", "department", "role", "join_date", "leave_balance"]
            ]
            df.columns = ["ID", "Name", "Email", "Department", "Role", "Join Date", "Leave Balance"]
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("Employee Detail")
            emp_id = st.number_input("Enter Employee ID", min_value=1, step=1, value=1)
            if st.button("View Details"):
                emp = _api("GET", f"/employees/{int(emp_id)}")
                if emp:
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Name", emp["name"])
                    col2.metric("Department", emp["department"])
                    col3.metric("Role", emp["role"])
                    col1.metric("Email", emp["email"])
                    col2.metric("Join Date", emp["join_date"])
                    col3.metric("Leave Balance", f"{emp['leave_balance']} days")
                    if emp.get("manager_name"):
                        st.info(f"Reports to: **{emp['manager_name']}**")


# ── Leave ─────────────────────────────────────────────────────────────────────

elif page == "📅 Leave":
    st.header("📅 Leave Management")

    tab_request, tab_history, tab_approve = st.tabs(
        ["Apply for Leave", "Leave History", "Approve / Reject"]
    )

    with tab_request:
        st.subheader("Submit a Leave Request")
        with st.form("leave_form"):
            emp_id = st.number_input("Employee ID", min_value=1, step=1, value=2)
            leave_type = st.selectbox("Leave Type", ["annual", "sick", "personal"])
            col1, col2 = st.columns(2)
            start = col1.date_input("Start Date")
            end = col2.date_input("End Date")
            reason = st.text_area("Reason", height=80)
            submitted = st.form_submit_button("Submit Request")

        if submitted:
            result = _api(
                "POST",
                "/leave",
                json={
                    "employee_id": int(emp_id),
                    "leave_type": leave_type,
                    "start_date": str(start),
                    "end_date": str(end),
                    "reason": reason,
                },
            )
            if result:
                st.success(
                    f"Leave request submitted! ID: {result['id']} · "
                    f"{result['days']} day(s) · Status: {result['status']}"
                )

    with tab_history:
        st.subheader("Leave History")
        col1, col2 = st.columns(2)
        hist_emp_id = col1.number_input("Employee ID", min_value=1, step=1, value=2, key="hist_emp")
        hist_status = col2.selectbox("Status", ["all", "pending", "approved", "rejected"])
        if st.button("Load History"):
            records = _api(
                "GET",
                f"/leave/{int(hist_emp_id)}",
                params={"status": hist_status},
            )
            if records is not None:
                if not records:
                    st.info("No leave records found.")
                else:
                    import pandas as pd
                    df = pd.DataFrame(records)[
                        ["id", "leave_type", "start_date", "end_date", "days", "status", "reason"]
                    ]
                    df.columns = ["ID", "Type", "Start", "End", "Days", "Status", "Reason"]
                    st.dataframe(df, use_container_width=True, hide_index=True)

    with tab_approve:
        st.subheader("Approve / Reject Leave Request")
        with st.form("approve_form"):
            req_id = st.number_input("Leave Request ID", min_value=1, step=1, value=1)
            decision = st.radio("Decision", ["Approve", "Reject"], horizontal=True)
            note = st.text_input("Manager Note (optional)")
            approved = st.form_submit_button("Submit Decision")

        if approved:
            result = _api(
                "PUT",
                f"/leave/{int(req_id)}/approve",
                json={"approved": decision == "Approve", "note": note},
            )
            if result:
                st.success(f"Leave request {result['id']} → **{result['status']}**")


# ── Recruitment ───────────────────────────────────────────────────────────────

elif page == "💼 Recruitment":
    st.header("💼 Recruitment")

    tab_jobs, tab_apply, tab_pipeline = st.tabs(
        ["Open Positions", "Apply for a Job", "Applicant Pipeline"]
    )

    with tab_jobs:
        st.subheader("Open Positions")
        dept_filter = st.text_input("Filter by department", key="job_dept_filter",
                                    placeholder="Leave blank for all")
        jobs = _api("GET", "/jobs", params={"department": dept_filter} if dept_filter else {})
        if jobs is not None:
            if not jobs:
                st.info("No open positions found.")
            else:
                for job in jobs:
                    with st.expander(f"[ID {job['id']}] {job['title']} — {job['department']}"):
                        st.markdown(f"**Posted:** {job['posted_date']}")
                        st.markdown(f"**Description:** {job['description']}")
                        st.markdown(f"**Requirements:** {job['requirements']}")

        st.divider()
        st.subheader("Post a New Job")
        with st.form("post_job_form"):
            title = st.text_input("Job Title")
            dept = st.selectbox("Department", ["Engineering", "HR", "Marketing", "Finance", "Operations"])
            desc = st.text_area("Job Description", height=100)
            reqs = st.text_area("Requirements", height=80)
            posted = st.form_submit_button("Post Job")
        if posted:
            result = _api(
                "POST",
                "/jobs",
                json={"title": title, "department": dept, "description": desc, "requirements": reqs},
            )
            if result:
                st.success(f"Job posted! ID: {result['id']} · Title: {result['title']}")

    with tab_apply:
        st.subheader("Submit an Application")
        with st.form("apply_form"):
            job_id = st.number_input("Job ID", min_value=1, step=1, value=1)
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            resume = st.text_area("Resume Summary", height=120,
                                  placeholder="Brief summary of your experience and skills…")
            apply_btn = st.form_submit_button("Submit Application")
        if apply_btn:
            result = _api(
                "POST",
                f"/jobs/{int(job_id)}/apply",
                json={"name": name, "email": email, "resume_summary": resume},
            )
            if result:
                st.success(f"Application submitted! Applicant ID: {result['id']} · Status: {result['status']}")

    with tab_pipeline:
        st.subheader("Applicant Pipeline")
        pipeline_job_id = st.number_input("Job ID", min_value=1, step=1, value=1, key="pipeline_job")
        if st.button("Load Applicants"):
            applicants = _api("GET", f"/jobs/{int(pipeline_job_id)}/applicants")
            if applicants is not None:
                if not applicants:
                    st.info("No applicants yet.")
                else:
                    import pandas as pd
                    df = pd.DataFrame(applicants)[
                        ["id", "name", "email", "status", "applied_date", "resume_summary"]
                    ]
                    df.columns = ["ID", "Name", "Email", "Status", "Applied", "Resume Summary"]
                    st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Update Applicant Status")
        with st.form("pipeline_form"):
            app_id = st.number_input("Applicant ID", min_value=1, step=1, value=1)
            new_status = st.selectbox(
                "New Status", ["applied", "screening", "interview", "offered", "rejected"]
            )
            update_btn = st.form_submit_button("Update Status")
        if update_btn:
            result = _api(
                "PUT",
                f"/applicants/{int(app_id)}/status",
                json={"status": new_status},
            )
            if result:
                st.success(f"Applicant {result['id']} moved to **{result['status']}**")


# ── Policies ──────────────────────────────────────────────────────────────────

elif page == "📋 Policies":
    st.header("📋 HR Policies")
    st.caption("Search company HR policies — leave, benefits, code of conduct, recruitment, and more.")

    query = st.text_input("Search policies", placeholder="e.g. annual leave, referral bonus, sick leave certificate…")

    if query:
        with st.spinner("Searching policies…"):
            result = _api(
                "POST",
                "/chat",
                json={
                    "message": f"Search the HR policies for: {query}. "
                               "Return the relevant policy content verbatim, then briefly summarize the key points.",
                    "history": [],
                },
            )
        if result:
            st.markdown(result["answer"])
    else:
        st.info("Type a keyword above to search HR policies.")
        st.divider()
        st.subheader("Policy Categories")
        col1, col2, col3 = st.columns(3)
        col1.markdown("**Leave Policies**\n- Annual Leave\n- Sick Leave\n- Personal Leave")
        col2.markdown("**Workplace**\n- Code of Conduct\n- Remote Work Policy")
        col3.markdown("**Benefits & Recruitment**\n- Employee Benefits\n- Internal Referral Policy")
