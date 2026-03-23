"""
src/db/chroma_store.py

Three ChromaDB collections, all embedded with OpenAI text-embedding-3-small:

  feedback_reviews   — every raw review / email ingested by CSV Reader.
                       Classifier queries this for similar past items.
                       Bug Analyzer queries this for similar past bug reports.

  generated_tickets  — every ticket written by Ticket Creator.
                       Ticket Creator queries this to detect cross-run duplicates.

  tech_documents     — product/architecture docs from docs/product/*.md.
                       RAG Loader indexes these at pipeline startup.
                       Bug Analyzer + Feature Extractor query for product context.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

import chromadb
from chromadb import Collection
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

import src.config as config

logger = logging.getLogger(__name__)


@dataclass
class SimilarResult:
    id: str
    text: str
    metadata: dict
    similarity_score: float   # 1.0 = identical, 0.0 = unrelated (inverted cosine distance)


def _embed_fn() -> OpenAIEmbeddingFunction:
    return OpenAIEmbeddingFunction(
        api_key=config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", ""),
        model_name="text-embedding-3-small",
    )


class ChromaStore:
    """Manages the three ChromaDB collections used by the pipeline."""

    def __init__(self, path: str | None = None) -> None:
        self._path = path or config.CHROMA_PATH
        self._client: chromadb.ClientAPI | None = None
        self._ef = _embed_fn()
        self._reviews: Collection | None = None
        self._tickets: Collection | None = None
        self._tech_docs: Collection | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def init(self) -> "ChromaStore":
        os.makedirs(self._path, exist_ok=True)
        self._client = chromadb.PersistentClient(path=self._path)
        _kw = dict(embedding_function=self._ef, metadata={"hnsw:space": "cosine"})
        self._reviews   = self._client.get_or_create_collection(config.CHROMA_COLLECTION_REVIEWS,   **_kw)
        self._tickets   = self._client.get_or_create_collection(config.CHROMA_COLLECTION_TICKETS,   **_kw)
        self._tech_docs = self._client.get_or_create_collection(config.CHROMA_COLLECTION_TECH_DOCS, **_kw)
        logger.info("ChromaDB ready at %s (reviews=%d tickets=%d tech_docs=%d)",
                    self._path, self._reviews.count(),
                    self._tickets.count(), self._tech_docs.count())
        return self

    def _check(self) -> None:
        if self._client is None:
            raise RuntimeError("Call ChromaStore.init() before use.")

    # ── Reviews / Emails ──────────────────────────────────────────────────────

    def upsert_review(self, id: str, text: str, metadata: dict) -> None:
        """Store a raw FeedbackItem in the reviews collection."""
        self._check()
        self._reviews.upsert(ids=[id], documents=[text], metadatas=[metadata])

    def find_similar_reviews(
        self,
        text: str,
        k: int = 5,
        threshold: float | None = None,
        source_type: str | None = None,
    ) -> list[SimilarResult]:
        self._check()
        if self._reviews.count() == 0:
            return []
        where = {"source_type": source_type} if source_type else None
        results = self._reviews.query(
            query_texts=[text],
            n_results=min(k, self._reviews.count()),
            where=where,
        )
        return _parse(results, threshold)

    # ── Tickets ───────────────────────────────────────────────────────────────

    def upsert_ticket(self, ticket_id: str, title: str, description: str, metadata: dict) -> None:
        """Store a generated ticket for future duplicate detection."""
        self._check()
        self._tickets.upsert(
            ids=[ticket_id],
            documents=[f"{title}\n\n{description}"],
            metadatas=[metadata],
        )

    def find_similar_tickets(
        self,
        text: str,
        k: int = 3,
        threshold: float | None = None,
        category: str | None = None,
    ) -> list[SimilarResult]:
        self._check()
        if self._tickets.count() == 0:
            return []
        where = {"category": category} if category else None
        results = self._tickets.query(
            query_texts=[text],
            n_results=min(k, self._tickets.count()),
            where=where,
        )
        return _parse(results, threshold)

    # ── Tech Docs ─────────────────────────────────────────────────────────────

    def index_tech_docs(self, docs_dir: str | None = None) -> int:
        """Walk docs_dir, chunk by paragraph, upsert into tech_documents. Idempotent."""
        self._check()
        path = docs_dir or config.TECH_DOCS_DIR
        if not os.path.isdir(path):
            logger.warning("Tech docs dir not found: %s — skipping", path)
            return 0
        ids, docs, metas = [], [], []
        for root, _, files in os.walk(path):
            for fname in sorted(files):
                if not fname.endswith((".md", ".txt", ".rst")):
                    continue
                fpath = os.path.join(root, fname)
                with open(fpath, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for i, para in enumerate(p.strip() for p in content.split("\n\n") if p.strip()):
                    ids.append(f"doc__{fname}__{i}")
                    docs.append(para)
                    metas.append({"source": fname, "chunk": i})
        if ids:
            for start in range(0, len(ids), 100):
                self._tech_docs.upsert(
                    ids=ids[start:start+100],
                    documents=docs[start:start+100],
                    metadatas=metas[start:start+100],
                )
            logger.info("Indexed %d chunks from %s", len(ids), path)
        return len(ids)

    def upsert_tech_doc(self, doc_id: str, text: str, metadata: dict) -> None:
        self._check()
        self._tech_docs.upsert(ids=[doc_id], documents=[text], metadatas=[metadata])

    def query_tech_docs(self, query: str, k: int = 5) -> list[SimilarResult]:
        """Retrieve top-k product doc chunks relevant to query."""
        self._check()
        if self._tech_docs.count() == 0:
            return []
        results = self._tech_docs.query(
            query_texts=[query],
            n_results=min(k, self._tech_docs.count()),
        )
        return _parse(results, threshold=None)

    # ── Aliases (TASKS.md BE-DB-006 API) ─────────────────────────────────────

    def upsert_feedback(self, id: str, text: str, metadata: dict) -> None:
        self.upsert_review(id, text, metadata)

    def find_similar(self, text: str, k: int = 5, threshold: float = 0.85) -> list[SimilarResult]:
        return self.find_similar_reviews(text, k=k, threshold=threshold)

    def counts(self) -> dict[str, int]:
        self._check()
        return {
            "reviews": self._reviews.count(),
            "tickets": self._tickets.count(),
            "tech_docs": self._tech_docs.count(),
        }


def _parse(results: dict, threshold: float | None) -> list[SimilarResult]:
    out: list[SimilarResult] = []
    ids      = results.get("ids",       [[]])[0]
    docs     = results.get("documents", [[]])[0]
    metas    = results.get("metadatas", [[]])[0]
    dists    = results.get("distances", [[]])[0]
    for id_, doc, meta, dist in zip(ids, docs, metas, dists):
        sim = max(0.0, 1.0 - dist)   # cosine distance → similarity
        if threshold is not None and sim < threshold:
            continue
        out.append(SimilarResult(id=id_, text=doc, metadata=meta or {}, similarity_score=sim))
    return out


# ── Module-level singleton ────────────────────────────────────────────────────
_store: ChromaStore | None = None


def get_store() -> ChromaStore:
    global _store
    if _store is None:
        _store = ChromaStore().init()
    return _store
