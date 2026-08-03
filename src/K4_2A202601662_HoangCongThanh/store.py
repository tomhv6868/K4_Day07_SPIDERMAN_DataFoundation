from __future__ import annotations

from typing import Any, Callable

from .chunking import compute_similarity
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            self._chroma_available = True
        except Exception:
            self._chroma_available = False
        # Lưu trữ luôn chạy in-memory: đây là đường đi duy nhất được test phủ.
        # Persistence bằng ChromaDB (CHROMA_PERSIST_DIR) là bonus task, chưa làm.
        self._use_chroma = False
        self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Chuẩn hoá một Document thành record lưu trong store (embed ngay tại đây)."""
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": dict(doc.metadata or {}),
            "embedding": self._embedding_fn(doc.content),
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Chấm điểm cosine giữa query và từng record, trả top_k theo thứ tự giảm dần."""
        if not records or top_k <= 0:
            return []

        query_embedding = self._embedding_fn(query)
        scored = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": record["metadata"],
                "score": compute_similarity(query_embedding, record["embedding"]),
            }
            for record in records
        ]
        # sort ổn định: điểm bằng nhau thì giữ thứ tự nạp vào, kết quả tái lập được.
        scored.sort(key=lambda result: result["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        for doc in docs:
            record = self._make_record(doc)
            record["insert_index"] = self._next_index
            self._next_index += 1
            self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        candidates = self._store
        if metadata_filter:
            # Lọc TRƯỚC rồi mới chấm điểm: chunk bị loại không chiếm slot nào trong top_k.
            candidates = [
                record
                for record in self._store
                if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
            ]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """

        def belongs_to_document(record: dict[str, Any]) -> bool:
            if record["metadata"].get("doc_id") == doc_id:
                return True
            # Document nạp thẳng (không qua ingest) không có metadata['doc_id'];
            # chunk từ ingest.py mang id dạng "<doc_id>::chunk_<n>".
            return record["id"] == doc_id or record["id"].startswith(f"{doc_id}::")

        remaining = [record for record in self._store if not belongs_to_document(record)]
        if len(remaining) == len(self._store):
            return False
        self._store = remaining
        return True
