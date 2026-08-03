"""Chạy benchmark retrieval với chiến lược chunking của Nguyễn Hoàng Bảo Minh."""
from __future__ import annotations

import re
import sys
from pathlib import Path

# File này nằm ở src/K4_.../, còn ingest.py/main.py/data/ nằm ở project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingest import build_knowledge_base
from main import _select_embedder
from src.agent import KnowledgeBaseAgent
from src.chunking import RecursiveChunker
from data.benchmark_queries import QUERIES

SOURCE_MARKER = re.compile(r"^\[\d+\]\s*\(source:[^)]*\)\s*", re.M)


def extractive_llm(prompt: str) -> str:
    """Không gọi LLM ngoài: trả lại nguyên văn đoạn context [1] (top-1)."""
    body = prompt.split("Context:", 1)[-1].split("Question:", 1)[0].strip()
    blocks = [block.strip() for block in SOURCE_MARKER.split(body) if block.strip()]
    return blocks[0] if blocks else "Không có ngữ cảnh phù hợp trong kho tài liệu."


def print_results(label, results, evidence):
    print(f"  -- {label} --")
    for rank, r in enumerate(results, start=1):
        found = evidence.lower() in r["content"].lower()
        preview = r["content"][:100].replace("\n", " ")
        print(f"  [{rank}] score={r['score']:.3f} doc_id={r['metadata'].get('doc_id')} evidence_found={found} | {preview}...")


def main() -> None:
    # 1. Chọn chunker của riêng bạn, đây là DÒNG DUY NHẤT khác với bạn cùng nhóm
    chunker = RecursiveChunker(chunk_size=400)

    # 2. Nạp cả thư mục corpus. embedding_fn là tham số bắt buộc thứ hai.
    embedding_fn = _select_embedder()
    store = build_knowledge_base(
        PROJECT_ROOT / "data" / "k4_ecommerce",
        embedding_fn=embedding_fn,
        chunker=chunker,
        collection_name="bench_nguyen_hoang_bao_minh",
    )

    print(f"Strategy: {chunker.__class__.__name__} | chunk_size={chunker.chunk_size}")
    print(f"Số chunk đã nạp: {store.get_collection_size()}\n")

    # 3. Chạy 5 query qua search() hoặc search_with_filter(), in top-3 và câu trả lời của agent
    agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_llm)

    for i, q in enumerate(QUERIES, start=1):
        print(f"=== Query {i}: {q['text']}")
        results = (
            store.search_with_filter(q["text"], top_k=3, metadata_filter=q["filter"])
            if q["filter"]
            else store.search(q["text"], top_k=3)
        )
        print_results("with filter" if q["filter"] else "no filter", results, q["evidence"])

        # A/B: query bắt buộc filter thì chạy thêm bản không filter để so sánh
        if q["filter"]:
            no_filter_results = store.search(q["text"], top_k=3)
            print_results("no filter (A/B)", no_filter_results, q["evidence"])
            same_docs = {r["metadata"].get("doc_id") for r in results} == {
                r["metadata"].get("doc_id") for r in no_filter_results
            }
            print(f"  A/B same top-3 doc_id set: {same_docs}")

        print(f"  Agent answer: {agent.answer(q['text'], top_k=3, metadata_filter=q['filter'])}\n")


if __name__ == "__main__":
    main()
