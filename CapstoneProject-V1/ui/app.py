"""
ui/app.py  —  Feedback Intelligence System
Main Streamlit entry point.

Run with:
    streamlit run ui/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# ── Make src importable ───────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Feedback Intelligence System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar branding ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 Feedback Intelligence")
    st.markdown("AI-powered feedback analysis pipeline")
    st.divider()
    st.markdown(
        """
        **Navigation**
        - 📊 Dashboard
        - ▶️ Run Pipeline
        - 🎫 Tickets
        - 📚 Tech Docs
        - 📈 Analytics
        - ⚙️ Configuration
        """,
        unsafe_allow_html=False,
    )
    st.divider()
    st.caption("Powered by LangGraph + OpenAI gpt-4o")

# ── Home / landing ────────────────────────────────────────────────────────────
st.title("🧠 Feedback Intelligence System")
st.markdown(
    """
    Welcome! Use the sidebar to navigate between pages.

    | Page | Purpose |
    |------|---------|
    | 📊 **Dashboard** | KPIs, charts and recent tickets at a glance |
    | ▶️ **Run Pipeline** | Upload CSV feedback and trigger the AI pipeline |
    | 🎫 **Tickets** | Browse, filter, and edit generated tickets |
    | 📚 **Tech Docs** | Upload product documentation for RAG context |
    | 📈 **Analytics** | Trend charts and classification accuracy |
    | ⚙️ **Configuration** | Tune thresholds and pipeline settings |
    """
)

st.info(
    "Use the **Run Pipeline** page to process feedback for the first time, "
    "or upload tech docs on the **Tech Docs** page to improve RAG context quality.",
    icon="💡",
)
