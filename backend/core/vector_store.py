"""
AURA-EPC Vector Store
FAISS-backed semantic search over RFI logs, TIA-942 specs, and vendor submittals.
Uses sentence-transformers for local embeddings (no API cost).
"""
from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False

INDEX_DIR = Path("./data/vector_index")
INDEX_PATH = INDEX_DIR / "faiss.index"
META_PATH = INDEX_DIR / "metadata.pkl"
EMBED_MODEL = "all-MiniLM-L6-v2"


@dataclass
class SearchResult:
    doc_id: str
    source: str
    content: str
    score: float
    metadata: dict[str, Any]


class VectorStore:
    def __init__(self):
        self._model: SentenceTransformer | None = None
        self._index: Any = None  # faiss.Index
        self._metadata: list[dict[str, Any]] = []
        self._loaded = False

    def _get_model(self) -> "SentenceTransformer":
        if self._model is None:
            if not ST_AVAILABLE:
                raise RuntimeError("sentence-transformers not installed")
            self._model = SentenceTransformer(EMBED_MODEL)
        return self._model

    def _embed(self, texts: list[str]) -> np.ndarray:
        model = self._get_model()
        embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return embeddings.astype(np.float32)

    def build_index(self, documents: list[dict[str, Any]]) -> None:
        """
        Build FAISS index from a list of document dicts.
        Each dict must have: id, source, content, metadata (optional)
        """
        if not FAISS_AVAILABLE:
            raise RuntimeError("faiss-cpu not installed")

        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        texts = [doc["content"] for doc in documents]
        embeddings = self._embed(texts)

        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)  # Inner product = cosine on normalized vecs
        index.add(embeddings)

        self._index = index
        self._metadata = [
            {
                "id": doc.get("id", str(i)),
                "source": doc.get("source", ""),
                "content": doc["content"],
                "metadata": doc.get("metadata", {}),
            }
            for i, doc in enumerate(documents)
        ]

        faiss.write_index(index, str(INDEX_PATH))
        with open(META_PATH, "wb") as f:
            pickle.dump(self._metadata, f)

        self._loaded = True
        print(f"[VectorStore] Index built: {len(documents)} docs, dim={dim}")

    def load(self) -> None:
        """Load persisted index from disk."""
        if not FAISS_AVAILABLE:
            raise RuntimeError("faiss-cpu not installed")
        if not INDEX_PATH.exists():
            raise FileNotFoundError(f"FAISS index not found at {INDEX_PATH}")

        self._index = faiss.read_index(str(INDEX_PATH))
        with open(META_PATH, "rb") as f:
            self._metadata = pickle.load(f)
        self._loaded = True
        print(f"[VectorStore] Loaded {len(self._metadata)} documents from index.")

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Return top_k most semantically similar documents."""
        if not self._loaded:
            if INDEX_PATH.exists():
                self.load()
            else:
                return []

        query_emb = self._embed([query])
        scores, indices = self._index.search(query_emb, min(top_k, len(self._metadata)))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            meta = self._metadata[idx]
            results.append(SearchResult(
                doc_id=meta["id"],
                source=meta["source"],
                content=meta["content"],
                score=float(score),
                metadata=meta["metadata"],
            ))
        return results

    def is_ready(self) -> bool:
        return self._loaded and self._index is not None


# Module-level singleton
_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    if not _store.is_ready() and INDEX_PATH.exists():
        _store.load()
    return _store

