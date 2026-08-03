"""Chạy benchmark retrieval với chiến lược chunking của Trần Văn Ngọc."""
from __future__ import annotations

import sys
from pathlib import Path

# File này nằm ở src/K4_.../, còn ingest.py nằm ở project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingest import build_knowledge_base
from main import _select_embedder
from src.chunking import RecursiveChunker


# Chỉ thay dòng này khi thử chiến lược/parameter khác.
CHUNKER = RecursiveChunker(chunk_size=400)

# Bộ query chung đã chốt trong REPORT_NHOM.md và REPORT_CANHAN của Hoàng Công Thành.
# Không thay đổi các câu này khi đã bắt đầu so sánh strategy.
QUERIES: list[dict[str, object]] = [
    {
        "id": "Q1",
        "query": "Nhà Bán có bao nhiêu thời gian để xác nhận phương án xử lý đổi/trả/bảo hành?",
        "metadata_filter": {"customer_role": "seller"},
        "expected_doc": "tiki-xu-ly-doi-tra-bao-hanh",
    },
    {
        "id": "Q2",
        "query": "Thời gian bảo hành Nhà Bán cam kết tối đa là bao lâu?",
        "metadata_filter": None,
        "expected_doc": "tiki-xu-ly-doi-tra-bao-hanh",
    },
    {
        "id": "Q3",
        "query": "Hàng hóa nào Nhà Bán không được đăng bán trên Tiki?",
        "metadata_filter": {"customer_role": "seller"},
        "expected_doc": "tiki-danh-muc-hang-cam-ban",
    },
    {
        "id": "Q4",
        "query": "Người tiêu dùng nên làm gì để phòng tránh rủi ro mua sắm trực tuyến?",
        "metadata_filter": {"customer_role": "buyer"},
        "expected_doc": "bvntd-rui-ro-mua-sam-truc-tuyen",
    },
    {
        "id": "Q5",
        "query": "Theo NĐ 85/2021, sàn TMĐT có trách nhiệm gì khi giải quyết khiếu nại?",
        "metadata_filter": None,
        "expected_doc": "moit-nghi-dinh-85-2021-tmdt",
    },
]


def main() -> None:
    embedding_fn = _select_embedder()
    store = build_knowledge_base(
        PROJECT_ROOT / "data" / "k4_ecommerce",
        embedding_fn=embedding_fn,
        chunker=CHUNKER,
        collection_name="bench_tran_van_ngoc",
    )

    print(f"Strategy: {CHUNKER.__class__.__name__} (chunk_size=400)")
    print(f"Embedder: {getattr(embedding_fn, '_backend_name', embedding_fn.__class__.__name__)}")
    print(f"Chunks loaded: {store.get_collection_size()}")

    for benchmark in QUERIES:
        metadata_filter = benchmark.get("metadata_filter")
        if metadata_filter is None:
            results = store.search(str(benchmark["query"]), top_k=3)
        else:
            results = store.search_with_filter(
                str(benchmark["query"]), top_k=3, metadata_filter=metadata_filter
            )

        print(f"\n{benchmark['id']}: {benchmark['query']}")
        print(f"Filter: {metadata_filter}")
        print(f"Expected document: {benchmark['expected_doc']}")
        for rank, result in enumerate(results, start=1):
            preview = result["content"].replace("\n", " ")[:160]
            print(
                f"{rank}. score={result['score']:.3f} "
                f"doc_id={result['metadata'].get('doc_id')}\n"
                f"   {preview}..."
            )


if __name__ == "__main__":
    main()
