"""
ui/pages/4_Tech_Docs.py
Upload product documentation for RAG context.

Features:
- Upload .md / .txt / .rst files → saved to docs/product/user_uploads/
- Re-index all docs into ChromaDB (tech_documents collection)
- Browse currently indexed docs with chunk counts
- Delete uploaded docs (built-in docs are protected)
- Preview file contents inline
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import src.config as config

UPLOAD_DIR = Path(config.TECH_DOCS_DIR) / "user_uploads"
BUILTIN_DIR = Path(config.TECH_DOCS_DIR)
ALLOWED_EXTENSIONS = {".md", ".txt", ".rst"}

st.set_page_config(page_title="Tech Docs · FIS", page_icon="📚", layout="wide")
st.title("📚 Tech Docs — RAG Knowledge Base")
st.markdown(
    "Upload product documentation to improve the AI pipeline's understanding of your product. "
    "Uploaded files are saved to `docs/product/user_uploads/` and indexed into ChromaDB "
    "so Bug Analyzer and Feature Extractor can retrieve relevant context during processing."
)


# ── Helper: get ChromaDB store (cached for session) ───────────────────────────
@st.cache_resource
def _get_store():
    from src.db.chroma_store import get_store
    return get_store()


def _reindex(store) -> int:
    """Re-index the entire docs directory and return total chunk count."""
    return store.index_tech_docs(str(BUILTIN_DIR))


def _list_docs(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(
        f for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
    )


# ── Section 1: Upload ─────────────────────────────────────────────────────────
st.subheader("1 · Upload New Document")

with st.form("upload_form", clear_on_submit=True):
    uploaded_files = st.file_uploader(
        "Choose Markdown / Text / reStructuredText files",
        type=["md", "txt", "rst"],
        accept_multiple_files=True,
        help="Files will be saved to docs/product/user_uploads/ and indexed immediately.",
    )
    index_after = st.checkbox("Re-index all docs after upload", value=True)
    submit_upload = st.form_submit_button("📤 Upload & Save", type="primary")

if submit_upload:
    if not uploaded_files:
        st.warning("No files selected.")
    else:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        saved = []
        for uf in uploaded_files:
            dest = UPLOAD_DIR / uf.name
            dest.write_bytes(uf.read())
            saved.append(uf.name)
            st.toast(f"Saved: {uf.name}", icon="✅")

        st.success(f"Saved {len(saved)} file(s): {', '.join(saved)}")

        if index_after:
            with st.spinner("Indexing docs into ChromaDB…"):
                try:
                    store  = _get_store()
                    chunks = _reindex(store)
                    st.success(f"✅ ChromaDB updated — **{chunks} chunks** indexed across all docs.")
                except Exception as exc:
                    st.error(f"Indexing failed: {exc}")

st.divider()

# ── Section 2: Re-index manually ─────────────────────────────────────────────
st.subheader("2 · Re-index Knowledge Base")
st.markdown(
    "Run this after editing any document files directly on disk, "
    "or to ensure ChromaDB is in sync with the file system."
)
if st.button("🔄 Re-index All Docs Now"):
    with st.spinner("Indexing…"):
        try:
            store  = _get_store()
            chunks = _reindex(store)
            st.success(f"✅ {chunks} chunks indexed into ChromaDB (tech_documents collection).")
        except Exception as exc:
            st.error(f"Failed to index: {exc}")

st.divider()

# ── Section 3: Browse docs ────────────────────────────────────────────────────
st.subheader("3 · Current Documents")

tab_builtin, tab_uploaded = st.tabs(["📂 Built-in Docs", "📤 Uploaded Docs"])

with tab_builtin:
    builtin_docs = [
        f for f in _list_docs(BUILTIN_DIR)
        if not f.parent.name == "user_uploads"
    ]
    if builtin_docs:
        for doc in builtin_docs:
            size_kb = doc.stat().st_size / 1024
            with st.expander(f"📄 `{doc.name}`  ({size_kb:.1f} KB)"):
                col_preview, col_info = st.columns([3, 1])
                with col_info:
                    st.metric("Size", f"{size_kb:.1f} KB")
                    paragraphs = len([p for p in doc.read_text(encoding="utf-8", errors="ignore").split("\n\n") if p.strip()])
                    st.metric("~Chunks", paragraphs)
                with col_preview:
                    content = doc.read_text(encoding="utf-8", errors="ignore")
                    st.markdown(content[:2000] + ("…" if len(content) > 2000 else ""))
    else:
        st.info("No built-in documents found in `docs/product/`.")

with tab_uploaded:
    uploaded_docs = _list_docs(UPLOAD_DIR)
    if not uploaded_docs:
        st.info("No uploaded documents yet. Use the upload form above to add files.")
    else:
        for doc in uploaded_docs:
            size_kb = doc.stat().st_size / 1024
            col_name, col_size, col_del, col_prev = st.columns([4, 1, 1, 1])
            with col_name:
                st.markdown(f"📄 `{doc.name}`")
            with col_size:
                st.markdown(f"{size_kb:.1f} KB")
            with col_del:
                if st.button("🗑️", key=f"del_{doc.name}", help=f"Delete {doc.name}"):
                    doc.unlink()
                    st.toast(f"Deleted {doc.name}", icon="🗑️")
                    st.rerun()
            with col_prev:
                if st.button("👁️", key=f"prev_{doc.name}", help="Preview"):
                    st.session_state[f"show_{doc.name}"] = not st.session_state.get(f"show_{doc.name}", False)

            if st.session_state.get(f"show_{doc.name}", False):
                content = doc.read_text(encoding="utf-8", errors="ignore")
                st.text_area(f"Contents of {doc.name}", value=content, height=300,
                             key=f"content_{doc.name}", disabled=True)

st.divider()

# ── Section 4: ChromaDB status ────────────────────────────────────────────────
st.subheader("4 · ChromaDB Status")
if st.button("📊 Show Collection Stats"):
    try:
        store = _get_store()
        counts = store.counts()
        c1, c2, c3 = st.columns(3)
        c1.metric("feedback_reviews",  counts["reviews"])
        c2.metric("generated_tickets", counts["tickets"])
        c3.metric("tech_documents",    counts["tech_docs"])

        if counts["tech_docs"] == 0:
            st.warning(
                "tech_documents collection is empty. Click **Re-index All Docs Now** above "
                "to populate it.",
                icon="⚠️",
            )
    except Exception as exc:
        st.error(f"Could not connect to ChromaDB: {exc}")

st.divider()

# ── Section 5: RAG query test ─────────────────────────────────────────────────
st.subheader("5 · Test RAG Query")
st.markdown("Verify that your docs are indexed correctly by running a test query.")

with st.form("rag_test_form"):
    query_text = st.text_input(
        "Query",
        placeholder="e.g. 'What causes login crashes?' or 'dark mode feature'",
    )
    top_k = st.slider("Top-K results", min_value=1, max_value=10, value=3)
    run_query = st.form_submit_button("🔍 Query ChromaDB")

if run_query and query_text:
    try:
        store   = _get_store()
        results = store.query_tech_docs(query_text, k=top_k)
        if results:
            for i, r in enumerate(results, 1):
                with st.expander(
                    f"#{i} — `{r.metadata.get('source', 'unknown')}` "
                    f"(chunk {r.metadata.get('chunk', '?')})  "
                    f"· similarity {r.similarity_score:.3f}"
                ):
                    st.markdown(r.text[:1000])
        else:
            st.info("No results found. Make sure the docs are indexed.")
    except Exception as exc:
        st.error(f"Query failed: {exc}")
elif run_query and not query_text:
    st.warning("Please enter a query.")
