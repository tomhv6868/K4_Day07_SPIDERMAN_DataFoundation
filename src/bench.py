"""Run the group's five-query retrieval benchmark on my personal package.

Examples:
    python src/bench.py
    python src/bench.py --strategy fixed --provider local

Mọi chunker/store lấy từ `src.K4_2A202601662_HoangCongThanh` (mã nguồn cá nhân);
chỉ khi thiếu gói đó mới rơi về `src` dùng chung, để con số in ra đúng là con số
của "mã nguồn cá nhân trong gói src" mà mục 5 báo cáo yêu cầu.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
# Chạy `python src/bench.py` thì sys.path[0] là src/, không phải repo root ->
# `ingest` và `src.*` sẽ không import được. Neo vào repo root cho chắc.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ingest import chunk_document, load_documents  # noqa: E402
from src.models import Document  # noqa: E402

try:
    from src.K4_2A202601662_HoangCongThanh import (  # noqa: E402
        LOCAL_EMBEDDING_MODEL,
        EmbeddingStore,
        FixedSizeChunker,
        HeadingFaqChunker,
        LocalEmbedder,
        OpenAIEmbedder,
        RecursiveChunker,
        SentenceChunker,
        _mock_embed,
    )

    SOLUTION_PACKAGE = "src.K4_2A202601662_HoangCongThanh"
except ImportError:  # The baseline checkout does not include the custom strategy.
    from src import (  # noqa: E402
        LOCAL_EMBEDDING_MODEL,
        EmbeddingStore,
        FixedSizeChunker,
        LocalEmbedder,
        OpenAIEmbedder,
        RecursiveChunker,
        SentenceChunker,
        _mock_embed,
    )

    HeadingFaqChunker = None
    SOLUTION_PACKAGE = "src"


DATA_DIR = REPO_ROOT / "data" / "k4_ecommerce"

QUERIES = [
    {
        "text": "Nhà Bán có bao nhiêu thời gian để xác nhận phương án xử lý yêu cầu đổi – trả – bảo hành của khách hàng?",
        "gold": (
            "02 ngày làm việc. Quá hạn, Tiki chủ động xử lý theo yêu cầu khách hàng "
            "(hoàn tiền hoặc tạo đơn hàng mới để đổi) và được quyền từ chối tiếp nhận "
            "khiếu nại của Nhà Bán phát sinh sau thời hạn này. Riêng mô hình NGON là "
            "tối đa 04 giờ làm việc."
        ),
        "evidence": "02 ngày làm việc",
        "filter": {"customer_role": "seller"},
    },
    {
        "text": "Thời gian bảo hành mà Nhà Bán được cam kết tối đa là bao lâu, và tính từ lúc nào?",
        "gold": (
            "Tối đa không quá 30 ngày, tính từ thời điểm Nhà Bán nhận được hàng đến khi "
            "bảo hành xong, không tính thời gian vận chuyển."
        ),
        "evidence": "tối đa không quá 30 ngày",
        "filter": None,
    },
    {
        "text": "Những loại hàng hóa nào Nhà Bán không được đăng bán trên sàn Tiki?",
        "gold": (
            "Vũ khí, chất nổ, pháo, hóa chất độc hại; thuốc lá điếu và xì gà; văn hóa "
            "phẩm đồi trụy/phản động; động thực vật hoang dã quý hiếm; ma túy và chất "
            "gây nghiện; đồ chơi nguy hiểm. Ngoài ra Tiki không hỗ trợ bán hàng cũ, đã "
            "qua sử dụng, like new, second hand."
        ),
        "evidence": "hàng cũ, đã qua sử dụng, like new, hàng second hand",
        "filter": {"customer_role": "seller"},
    },
    {
        "text": "Người tiêu dùng nên làm gì để phòng tránh rủi ro khi mua sắm trực tuyến?",
        "gold": (
            "Mua tại sàn TMĐT uy tín, được cấp phép, có thông tin liên lạc rõ ràng; "
            "chọn nhà bán có uy tín cao và đánh giá tích cực; tìm hiểu kỹ điều kiện "
            "giao dịch về bảo hành, trả lại hàng, hoàn tiền, giao nhận; tìm hiểu kỹ "
            "sản phẩm; cảnh giác với trang web lạ đòi cung cấp thông tin cá nhân hoặc "
            "đặt cọc trước."
        ),
        "evidence": "sàn giao dịch thương mại điện tử uy tín",
        "filter": {"customer_role": "buyer"},
    },
    {
        "text": "Theo Nghị định 85/2021/NĐ-CP, sàn TMĐT có trách nhiệm gì trong việc giải quyết khiếu nại của người tiêu dùng?",
        "gold": (
            "Chỉ định đầu mối tiếp nhận yêu cầu và cung cấp thông tin trực tuyến cho cơ "
            "quan quản lý nhà nước trong vòng 24 giờ; đại diện cho người bán nước ngoài "
            "trên sàn giải quyết khiếu nại của NTD; là đầu mối tiếp nhận và giải quyết "
            "khiếu nại khi một giao dịch trên sàn có nhiều hơn 02 bên tham gia."
        ),
        "evidence": "nhiều hơn 02 bên tham gia",
        "filter": None,
    },
]


def select_embedder(provider: str):
    provider = provider.lower()
    if provider == "local":
        try:
            return LocalEmbedder(os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception as exc:
            print(f"[warning] local embedder unavailable ({exc}); using mock")
    elif provider == "openai":
        try:
            return OpenAIEmbedder()
        except Exception as exc:
            print(f"[warning] OpenAI embedder unavailable ({exc}); using mock")
    return _mock_embed


def select_chunker(strategy: str):
    if strategy == "fixed":
        return FixedSizeChunker(chunk_size=500, overlap=50)
    if strategy == "sentence":
        return SentenceChunker(max_sentences_per_chunk=3)
    if strategy == "recursive":
        return RecursiveChunker(chunk_size=500)
    if strategy in {"heading", "heading_faq"}:
        if HeadingFaqChunker is None:
            raise RuntimeError("HeadingFaqChunker is not available in this checkout")
        return HeadingFaqChunker(max_chunk_size=900, min_chunk_size=120)
    raise ValueError(f"unknown strategy: {strategy}")


def build_store(data_dir: Path, strategy: str, embedder) -> EmbeddingStore:
    chunker = select_chunker(strategy)
    chunks: list[Document] = []
    for document in load_documents(data_dir):
        chunks.extend(chunk_document(document, chunker))

    # Gắn tên backend vào collection: mỗi model có số chiều vector khác nhau
    # (MiniLM 384, OpenAI 1536). Khi CHROMA_PERSIST_DIR bật, dùng chung một tên
    # thì đổi provider sẽ đâm vào collection cũ và lỗi lệch chiều.
    tag = re.sub(r"[^a-z0-9]+", "-", getattr(embedder, "_backend_name", "mock").lower()).strip("-")
    store = EmbeddingStore(collection_name=f"bench_{strategy}_{tag[-24:]}", embedding_fn=embedder)
    store.add_documents(chunks)
    return store


def retrieve(store: EmbeddingStore, query: dict, *, use_filter: bool) -> list[dict]:
    metadata_filter = query["filter"] if use_filter else None
    if metadata_filter:
        return store.search_with_filter(query["text"], top_k=3, metadata_filter=metadata_filter)
    return store.search(query["text"], top_k=3)


def extractive_answer(results: list[dict], evidence: str) -> str:
    """Return an auditable answer excerpt without pretending to call an LLM."""
    needle = evidence.casefold()
    for result in results:
        for sentence in re.split(r"(?<=[.!?])\s+", result["content"].replace("\n", " ")):
            if needle in sentence.casefold():
                return sentence.strip()
    return "Không có câu chứa evidence trong top-3."


def print_results(results: list[dict], evidence: str) -> list[int]:
    hits: list[int] = []
    needle = evidence.casefold()
    for rank, result in enumerate(results, start=1):
        content = " ".join(result["content"].split())
        relevant = needle in content.casefold()
        if relevant:
            hits.append(rank)
        print(
            f"  {rank}. score={result['score']:.4f} "
            f"relevant={'yes' if relevant else 'no'} id={result['id']}"
        )
        print(f"     {content[:240]}")
    return hits


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(os.getenv("LAB_DATA_DIR", str(DATA_DIR))),
    )
    parser.add_argument(
        "--strategy",
        choices=("heading", "heading_faq", "fixed", "sentence", "recursive"),
        default="heading",
        help="chunking strategy for this benchmark run (default: heading)",
    )
    parser.add_argument(
        "--provider",
        choices=("mock", "local", "openai"),
        default=os.getenv("EMBEDDING_PROVIDER", "mock"),
    )
    args = parser.parse_args()

    if not args.data_dir.exists():
        parser.error(f"data directory does not exist: {args.data_dir}")

    embedder = select_embedder(args.provider)
    store = build_store(args.data_dir, args.strategy, embedder)
    print(
        f"package={SOLUTION_PACKAGE} strategy={args.strategy} "
        f"provider={getattr(embedder, '_backend_name', 'mock')} "
        f"backend={'chroma' if store._use_chroma else 'in-memory'}"
    )
    if getattr(embedder, "_backend_name", "").startswith("mock"):
        print("LƯU Ý: MockEmbedder chỉ kiểm luồng kỹ thuật; score không phản ánh độ tương đồng ngữ nghĩa.")
    print(f"Đã nạp {store.get_collection_size()} chunk")

    for number, query in enumerate(QUERIES, start=1):
        print(f"\nQ{number}: {query['text']}")
        print(f"gold: {query['gold']}")
        if query["filter"]:
            print(f"filter: {query['filter']}")
        results = retrieve(store, query, use_filter=True)
        hits = print_results(results, query["evidence"])
        answer = extractive_answer(results, query["evidence"])
        if hits:
            print(f"  evidence ranks: {hits}; agent_answer (extractive): {answer}")
            print(
                "  assessment: related chunk found; inspect rank/coherence before assigning rubric points."
            )
        else:
            print(f"  agent_answer (extractive): {answer}")
            print("  assessment: FAILURE — top-3 has no chunk containing the declared evidence.")

        if query["filter"]:
            unfiltered = retrieve(store, query, use_filter=False)
            filtered_ids = [result["id"] for result in results]
            unfiltered_ids = [result["id"] for result in unfiltered]
            print(
                "  A/B filter: "
                + ("same top-3" if filtered_ids == unfiltered_ids else "different top-3")
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())