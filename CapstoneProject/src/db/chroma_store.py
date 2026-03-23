"""
src/db/chroma_store.py

ChromaDB vector store with three collections:

  feedback_reviews  — every raw review / email ingested by the pipeline.
                      Enables the Bug & Feature agents to search for similar
                      past feedback before analysing a new item.

  generated_tickets — every ticket created by the Ticket Creator.
                      Used to detect duplicate tickets across pipeline runs.

  tech_documents    — product & architecture documentation loaded at startup.
                      Bug Analyzer and Feature Extractor query this to understand
                      the product before reasoning about an issue or request.

All collections use OpenAI text-embedding-3-small via ChromaDB's
EmbeddingFunction interface so embeddings are consistent across collections.
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from typing import Optional

import chromadb
from chromadb import Collection
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

import src.config as config

logger = logging.getLogger(__name__)

# ── Shared embedding function (OpenAI text-embedding-3-small) ────────────────

def _make_embedding_fn() -> OpenAIEmbeddingFunction:
    api_key = config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
    return OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name="text-embedding-3-small",
    )


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class SimilarResult:
    id: str
    text: str
    metadata: dict
    similarity_score: float  # 0.0 (identical) – 1.0 (completely different) for L2; inverted for display


# ── ChromaStore ───────────────────────────────────────────────────────────────

class ChromaStore:
    """
    Wraps three ChromaDB collections and exposes simple upsert / search helpers.

    Usage
    -----
    store = ChromaStore()          # uses config.CHROMA_PATH
    store.init()                   # creates/loads collections
    store.upsert_review(...)
    store.upsert_ticket(...)
    store.index_tech_docs(path)    # call once at pipeline startup
    results = store.find_similar_tickets(text, k=3)
    context  = store.query_tech_docs(query, k=5)
    """

    def __init__(self, path: str | None = None) -> None:
        self._path = path or config.CHROMA_PATH
        self._client: chromadb.ClientAPI | None = None
        self._embed_fn = _make_embedding_fn()

        self._reviews: Collection | None = None
        self._tickets: Collection | None = None
        self._tech_docs: Collection | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def init(self) -> "ChromaStore":
        """Initialise the persistent client and create/load all collections."""
        os.makedirs(self._path, exist_ok=True)
        self._client = chromadb.PersistentClient(path=self._path)

        self._reviews = self._client.get_or_create_collection(
            name=config.CHROMA_COLLECTION_REVIEWS,
            embedding_function=self._embed_fn,
            metadata={"hnsw:space": "cosine"},
        )
        self._tickets = self._client.get_or_create_collection(
            name=config.CHROMA_COLLECTION_TICKETS,
            embedding_function=self._embed_fn,
            metadata={"hnsw:space": "cosine"},
        )
        self._tech_docs = self._client.get_or_create_collection(
            name=config.CHROMA_COLLECTION_TECH_DOCS,
            embedding_function=self._embed_fn,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB initialised at %s", self._path)
        return self

    def _ensure_init(self) -> None:
        if self._client is None:
            raise RuntimeError("ChromaStore.init() must be called before use.")

    # ── Reviews / Emails ──────────────────────────────────────────────────────

    def upsert_review(self, id: str, text: str, metadata: dict) -> None:
        """
        Store a raw review or support email.
        Call after the CSV Reader node normalises each FeedbackItem.
        """
        self._ensure_init()
        self._reviews.upsert(
            ids=[id],
            documents=[text],
            metadatas=[metadata],
        )

    def find_similar_reviews(
        self,
        text: str,
        k: int = 5,
        threshold: float | None = None,
        source_type: str | None = None,
    ) -> list[SimilarResult]:
        """
        Find k most similar reviews/emails to *text*.

        Parameters
        ----------
        threshold : float | None
            If given, only results with cosine distance ≤ threshold are returned.
            Lower distance = more similar (cosine space).
        source_type : str | None
            Optional filter: "review" or "email".
        """
        self._ensure_init()
        if self._reviews.count() == 0:
            return []

        where = {"source_type": source_type} if source_type else None
        results = self._reviews.query(
            query_texts=[text],
            n_results=min(k, self._reviews.count()),
            where=where,
        )
        return _parse_results(results, threshold)

    # ── Tickets ───────────────────────────────────────────────────────────────

    def upsert_ticket(self, ticket_id: str, title: str, description: str, metadata: dict) -> None:
        """
        Store a generated ticket in the tickets collection.
        The combined title + description is used as the document for richer matching.
        """
        self._ensure_init()
        document = f"{title}\n\n{description}"
        self._tickets.upsert(
            ids=[ticket_id],
            documents=[document],
            metadatas=[metadata],
        )

    def find_similar_tickets(
        self,
        text: str,
        k: int = 3,
        threshold: float | None = None,
        category: str | None = None,
    ) -> list[SimilarResult]:
        """
        Detect duplicate tickets before creating a new one.

        Parameters
        ----------
        category : str | None
            Optional filter so Bug duplicates only match Bug tickets, etc.
        """
        self._ensure_init()
        if self._tickets.count() == 0:
            return []

        where = {"category": category} if category else None
        results = self._tickets.query(
            query_texts=[text],
            n_results=min(k, self._tickets.count()),
            where=where,
        )
        return _parse_results(results, threshold)

    # ── Tech Docs ─────────────────────────────────────────────────────────────

    def index_tech_docs(self, docs_dir: str | None = None) -> int:
        """
        Walk *docs_dir* and index every .md / .txt / .rst file.
        Files are chunked by paragraph (double newline) so each chunk fits
        comfortably in a context window.

        Returns the number of chunks indexed.
        """
        self._ensure_init()
        path = docs_dir or config.TECH_DOCS_DIR
        if not os.path.isdir(path):
            logger.warning("Tech docs dir not found: %s — skipping indexing", path)
            return 0

        ids, documents, metadatas = [], [], []
        chunk_count = 0

        for root, _, files in os.walk(path):
            for fname in files:
                if not fname.endswith((".md", ".txt", ".rst")):
                    continue
                fpath = os.path.join(root, fname)
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Split by paragraph — keeps chunks meaningful
                paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
                for i, para in enumerate(paragraphs):
                    chunk_id = f"doc_{fname}_{i}"
                    ids.append(chunk_id)
                    documents.append(para)
                    metadatas.append({"source": fname, "chunk_index": i})
                    chunk_count += 1

        if ids:
            # Upsert in batches of 100 to stay within ChromaDB limits
            batch_size = 100
            for start in range(0, len(ids), batch_size):
                self._tech_docs.upsert(
                    ids=ids[start : start + batch_size],
                    documents=documents[start : start + batch_size],
                    metadatas=metadatas[start : start + batch_size],
                )
            logger.info("Indexed %d tech doc chunks from %s", chunk_count, path)

        return chunk_count

    def upsert_tech_doc(self, doc_id: str, text: str, metadata: dict) -> None:
        """Upsert a single tech doc chunk (useful for programmatic indexing)."""
        self._ensure_init()
        self._tech_docs.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata],
        )

    def query_tech_docs(self, query: str, k: int = 5) -> list[SimilarResult]:
        """
        Retrieve the top-k most relevant tech doc chunks for a query.
        Used by Bug Analyzer and Feature Extractor to ground their reasoning
        in the actual product documentation.
        """
        self._ensure_init()
        if self._tech_docs.count() == 0:
            return []

        results = self._tech_docs.query(
            query_texts=[query],
            n_results=min(k, self._tech_docs.count()),
        )
        return _parse_results(results, threshold=None)

    # ── Generic upsert (for backward compat with TASKS.md BE-DB-006 API) ──────

    def upsert_feedback(self, id: str, text: str, metadata: dict) -> None:
        """Alias: upsert into the reviews collection."""
        self.upsert_review(id, text, metadata)

    def find_similar(
        self, text: str, k: int = 5, threshold: float = 0.85
    ) -> list[SimilarResult]:
        """Alias: search reviews collection (used by Feature Extractor)."""
        return self.find_similar_reviews(text, k=k, threshold=threshold)

    # ── Stats ─────────────────────────────────────────────────────────────────

    def counts(self) -> dict[str, int]:
        self._ensure_init()
        return {
            "reviews": self._reviews.count(),
            "tickets": self._tickets.count(),
            "tech_docs": self._tech_docs.count(),
        }


# ── Helper ────────────────────────────────────────────────────────────────────

def _parse_results(
    results: dict,
    threshold: float | None,
) -> list[SimilarResult]:
    """Convert ChromaDB query results dict into SimilarResult list."""
    out: list[SimilarResult] = []
    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for id_, doc, meta, dist in zip(ids, docs, metas, distances):
        # Cosine distance: 0 = identical, 2 = opposite. Normalise to similarity 0–1.
        similarity = max(0.0, 1.0 - dist)
        if threshold is not None and dist > (1.0 - threshold):
            continue
        out.append(SimilarResult(id=id_, text=doc, metadata=meta or {}, similarity_score=similarity))
    return out


# ── Module-level singleton ────────────────────────────────────────────────────

_store: ChromaStore | None = None


def get_store() -> ChromaStore:
    """Return the module-level singleton, initialising it on first call."""
    global _store
    if _store is None:
        _store = ChromaStore().init()
    return _store
