from __future__ import annotations

import os
from typing import Any, Callable

from .chunking import compute_similarity
from .embeddings import _mock_embed
from .models import Document

CHROMA_PERSIST_DIR_ENV = "CHROMA_PERSIST_DIR"
# Chroma chỉ nhận metadata value thuộc các kiểu vô hướng này (và None).
CHROMA_SCALARS = (str, int, float, bool)


def _chroma_safe(metadata: dict[str, Any]) -> dict[str, Any]:
    """Ép metadata về kiểu Chroma chấp nhận (str/int/float/bool/None).

    Front matter `retrieved_at: 2026-08-03` được PyYAML parse thành `datetime.date`,
    Chroma từ chối kiểu này. Chỉ ép ở nhánh Chroma để bản in-memory giữ nguyên giá trị.
    """
    return {
        key: value if value is None or isinstance(value, CHROMA_SCALARS) else str(value)
        for key, value in metadata.items()
    }


def _chroma_where(metadata_filter: dict[str, Any]) -> dict[str, Any]:
    """Dịch filter phẳng nhiều khoá sang cú pháp `$and` của Chroma.

    Bản in-memory coi nhiều khoá là phép AND; Chroma ≥ 0.5 từ chối dict phẳng có
    hơn một khoá nên phải bọc lại, nếu không hai nhánh sẽ lệch hành vi.
    """
    if len(metadata_filter) == 1:
        return dict(metadata_filter)
    return {"$and": [{key: value} for key, value in metadata_filter.items()]}


class EmbeddingStore:
    """
    A vector store for text chunks.

    Dùng ChromaDB có persistence khi biến môi trường CHROMA_PERSIST_DIR được đặt
    và gói `chromadb` đã cài; ngoài ra chạy in-memory.
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

        # Chỉ bật Chroma khi người dùng CHỦ ĐỘNG đặt CHROMA_PERSIST_DIR. Bật tự
        # động theo "có cài gói hay không" sẽ làm collection sống dai giữa các lần
        # chạy, khiến test (vốn tái dùng tên collection) thấy dữ liệu lần trước.
        persist_dir = os.getenv(CHROMA_PERSIST_DIR_ENV, "").strip()
        if persist_dir:
            try:
                import chromadb

                client = chromadb.PersistentClient(path=persist_dir)
                # Chroma mặc định đo khoảng cách L2; ép sang cosine để `score`
                # cùng thang đo với nhánh in-memory (compute_similarity).
                self._collection = client.get_or_create_collection(
                    name=self._collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
                self._use_chroma = True
            except Exception:
                self._use_chroma = False
                self._collection = None

    @staticmethod
    def _from_chroma(result: dict[str, Any]) -> list[dict[str, Any]]:
        """Chuẩn hoá kết quả `collection.query` về đúng shape của nhánh in-memory."""
        return [
            {
                "id": result["ids"][0][index],
                "content": result["documents"][0][index],
                "metadata": result["metadatas"][0][index],
                # Không gian cosine: distance = 1 − similarity, nên đảo lại để
                # score cùng chiều "càng lớn càng giống" với compute_similarity.
                "score": 1.0 - result["distances"][0][index],
            }
            for index in range(len(result["ids"][0]))
        ]

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
        records = []
        for doc in docs:
            record = self._make_record(doc)
            record["insert_index"] = self._next_index
            self._next_index += 1
            records.append(record)

        if not records:
            return

        if self._use_chroma:
            # upsert chứ không add: collection đã persist nên chạy lại ingest sẽ
            # gặp lại đúng các id cũ; `add` báo lỗi trùng id, `upsert` thì ghi đè.
            self._collection.upsert(
                ids=[record["id"] for record in records],
                documents=[record["content"] for record in records],
                metadatas=[_chroma_safe(record["metadata"]) for record in records],
                embeddings=[record["embedding"] for record in records],
            )
        else:
            self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if top_k <= 0:
            return []

        if self._use_chroma:
            return self._from_chroma(
                self._collection.query(
                    query_embeddings=[self._embedding_fn(query)],
                    n_results=top_k,
                    include=["documents", "metadatas", "distances"],
                )
            )

        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k)

        if self._use_chroma:
            if top_k <= 0:
                return []
            # Chroma lọc ngay trong `where` — vẫn là lọc TRƯỚC khi chấm điểm,
            # chỉ khác là việc lọc chạy dưới engine thay vì trong Python.
            return self._from_chroma(
                self._collection.query(
                    query_embeddings=[self._embedding_fn(query)],
                    n_results=top_k,
                    where=_chroma_where(metadata_filter),
                    include=["documents", "metadatas", "distances"],
                )
            )

        # Lọc TRƯỚC rồi mới chấm điểm: chunk bị loại không chiếm slot nào trong top_k.
        candidates = [
            record
            for record in self._store
            if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
        ]
        return self._search_records(query, candidates, top_k)

    @staticmethod
    def _belongs_to_document(record_id: str, metadata: dict[str, Any], doc_id: str) -> bool:
        if metadata.get("doc_id") == doc_id:
            return True
        # Document nạp thẳng (không qua ingest) không có metadata['doc_id'];
        # chunk từ ingest.py mang id dạng "<doc_id>::chunk_<n>".
        return record_id == doc_id or record_id.startswith(f"{doc_id}::")

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma:
            # Lọc trong Python thay vì `where={"doc_id": ...}`: điều kiện khớp có
            # cả nhánh theo id, mà Chroma không so prefix trên id được. Collection
            # của lab cỡ vài trăm chunk nên quét toàn bộ vẫn rẻ.
            stored = self._collection.get(include=["metadatas"])
            doomed = [
                record_id
                for record_id, metadata in zip(stored["ids"], stored["metadatas"])
                if self._belongs_to_document(record_id, metadata or {}, doc_id)
            ]
            if not doomed:
                return False
            self._collection.delete(ids=doomed)
            return True

        remaining = [
            record
            for record in self._store
            if not self._belongs_to_document(record["id"], record["metadata"], doc_id)
        ]
        if len(remaining) == len(self._store):
            return False
        self._store = remaining
        return True
