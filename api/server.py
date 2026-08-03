"""Backend mỏng cho demo frontend — tái sử dụng nguyên `src/` và `ingest.py`.

Chạy:
    EMBEDDING_PROVIDER=local .venv/bin/python -m uvicorn api.server:app --port 8000 --reload

Không gọi API trả phí. `llm_fn` mặc định là stub trích xuất (trả lại nguyên văn
đoạn ngữ cảnh top-1). Muốn dùng OpenAI thì đặt DEMO_LLM=openai và tự chịu chi phí.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from pathlib import Path
from typing import Any, AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ingest import build_knowledge_base, load_documents, parse_front_matter
from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import LocalEmbedder, OpenAIEmbedder, _mock_embed

load_dotenv()

DATA_DIR = Path(os.getenv("LAB_DATA_DIR", "data/k4_ecommerce"))
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
LLM_PROVIDER = os.getenv("DEMO_LLM", "openai").strip().lower()

SYSTEM_PROMPT = (
    "Bạn là trợ lý tra cứu chính sách thương mại điện tử Việt Nam. "
    "Chỉ trả lời dựa trên phần Context được cung cấp — không suy đoán, không bổ sung "
    "kiến thức ngoài. Nếu Context không đủ, nói thẳng là tài liệu không đề cập. "
    "Trích số hiệu nguồn dạng [1], [2] ngay sau ý lấy từ nguồn đó. "
    "Trả lời bằng tiếng Việt, ngắn gọn, ưu tiên nêu đúng con số và thời hạn."
)

CHUNKERS = {
    "fixed_size": lambda: FixedSizeChunker(chunk_size=500, overlap=50),
    "by_sentences": lambda: SentenceChunker(max_sentences_per_chunk=3),
    "recursive": lambda: RecursiveChunker(chunk_size=500),
}

app = FastAPI(title="SPIDERMAN K4 — Knowledge Base Demo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Backend:
    """Giữ store đã nạp sẵn để mỗi request không phải embed lại toàn corpus."""

    def __init__(self) -> None:
        self.embedder = None
        self.backend_name = ""
        self.stores: dict[str, Any] = {}

    def embedder_ready(self):
        if self.embedder is None:
            provider = os.getenv("EMBEDDING_PROVIDER", "mock").strip().lower()
            factory = {"local": LocalEmbedder, "openai": OpenAIEmbedder}.get(provider)
            try:
                self.embedder = factory() if factory else _mock_embed
            except Exception:
                self.embedder = _mock_embed
            self.backend_name = getattr(self.embedder, "_backend_name", "mock embeddings fallback")
        return self.embedder

    def store_for(self, strategy: str):
        if strategy not in CHUNKERS:
            raise HTTPException(400, f"strategy không hợp lệ: {strategy}")
        if strategy not in self.stores:
            embedder = self.embedder_ready()
            # Gắn tên backend vào collection: vector của mỗi model có số chiều khác
            # nhau (MiniLM 384, OpenAI 1536). Nếu Chroma đang persist mà dùng chung
            # tên, đổi provider sẽ đâm vào collection cũ và lỗi lệch chiều.
            tag = re.sub(r"[^a-z0-9]+", "-", self.backend_name.lower()).strip("-")[-24:]
            self.stores[strategy] = build_knowledge_base(
                DATA_DIR, embedding_fn=embedder,
                chunker=CHUNKERS[strategy](), collection_name=f"demo_{strategy}_{tag}",
            )
        return self.stores[strategy]

    def reset(self) -> None:
        self.stores.clear()


backend = Backend()


SOURCE_MARKER = re.compile(r"^\[\d+\]\s*\(source:[^)]*\)\s*", re.M)


def extractive_llm(prompt: str) -> str:
    """Không gọi LLM ngoài: trả lại TRỌN VẸN đoạn ngữ cảnh [1].

    Nội dung chunk có xuống dòng bên trong nên không thể cắt theo dòng — phải
    tách theo nhãn `[n] (source: ...)` mới lấy đúng ranh giới giữa các chunk.
    """
    body = prompt.split("Context:", 1)[-1].split("Question:", 1)[0].strip()
    blocks = [block.strip() for block in SOURCE_MARKER.split(body) if block.strip()]
    return blocks[0] if blocks else "Không có ngữ cảnh phù hợp trong kho tài liệu."


class PromptCapture:
    """Bắt lại prompt do `KnowledgeBaseAgent` dựng, để stream bằng OpenAI.

    Agent trả về `str` nên không stream được. Thay vì chép lại logic dựng prompt,
    ta truyền hàm này làm `llm_fn`: agent vẫn chạy đúng đường của nó, còn prompt
    thu được sẽ đem đi stream riêng.
    """

    def __init__(self) -> None:
        self.prompt: str | None = None

    def __call__(self, prompt: str) -> str:
        self.prompt = prompt
        return ""


_openai_client = None


def openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import AsyncOpenAI

        _openai_client = AsyncOpenAI()
    return _openai_client


class FilteredStoreView:
    """Cho `KnowledgeBaseAgent` thấy một store đã lọc sẵn theo metadata.

    `KnowledgeBaseAgent.answer()` chỉ gọi `search()`, không nhận metadata_filter.
    Nếu backend tự lọc ở bước hiển thị nhưng agent vẫn `search()` toàn corpus thì
    tiến trình hiện trên UI sẽ khác với câu trả lời. View này bịt đúng khe hở đó
    mà không phải chép lại logic dựng prompt của agent.
    """

    def __init__(self, store: Any, metadata_filter: dict) -> None:
        self._store = store
        self._filter = metadata_filter

    def get_collection_size(self) -> int:
        return self._store.get_collection_size()

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return self._store.search_with_filter(query, top_k, self._filter)


# ---------------------------------------------------------------- documents


def read_documents() -> list[dict[str, Any]]:
    items = []
    for path in sorted(DATA_DIR.glob("*.md")):
        metadata, body = parse_front_matter(path.read_text(encoding="utf-8"))
        items.append({
            "doc_id": metadata.get("doc_id", path.stem),
            "title": metadata.get("title", path.stem),
            "customer_role": metadata.get("customer_role", "unknown"),
            "category": metadata.get("category", ""),
            "language": metadata.get("language", ""),
            "source_url": metadata.get("source_url", ""),
            "retrieved_at": metadata.get("retrieved_at", ""),
            "document_version": metadata.get("document_version", "not-stated"),
            "file_name": path.name,
            "char_count": len(body),
            "content": body,
        })
    return items


@app.get("/api/documents")
def list_documents(strategy: str = "fixed_size") -> dict[str, Any]:
    docs = read_documents()
    chunker = CHUNKERS[strategy]() if strategy in CHUNKERS else CHUNKERS["fixed_size"]()
    for doc in docs:
        doc["chunk_count"] = len(chunker.chunk(doc["content"]))
        doc.pop("content")
    roles: dict[str, int] = {}
    for doc in docs:
        roles[doc["customer_role"]] = roles.get(doc["customer_role"], 0) + 1
    return {
        "documents": docs,
        "stats": {
            "total_documents": len(docs),
            "total_chunks": sum(d["chunk_count"] for d in docs),
            "total_chars": sum(d["char_count"] for d in docs),
            "roles": roles,
            "strategy": strategy,
        },
    }


@app.get("/api/documents/{doc_id}")
def get_document(doc_id: str) -> dict[str, Any]:
    for doc in read_documents():
        if doc["doc_id"] == doc_id:
            return doc
    raise HTTPException(404, f"không tìm thấy tài liệu: {doc_id}")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "data_dir": str(DATA_DIR),
        "embedding_backend": backend.backend_name or "chưa nạp",
        "llm": CHAT_MODEL if LLM_PROVIDER == "openai" else "stub trích xuất",
        "warm": "fixed_size" in backend.stores,
        "strategies": list(CHUNKERS),
    }


@app.on_event("startup")
async def warm_up() -> None:
    """Nạp trước model + index mặc định.

    Lần gọi đầu tốn ~12s tải model và ~3s embed corpus. Làm sẵn lúc khởi động
    để câu hỏi đầu tiên lúc demo không phải chờ.
    """

    async def preload() -> None:
        await asyncio.to_thread(backend.store_for, "fixed_size")
        print(f"[warmup] sẵn sàng — backend nhúng: {backend.backend_name}", flush=True)

    asyncio.create_task(preload())


# ---------------------------------------------------------------- chat


class ChatRequest(BaseModel):
    question: str
    top_k: int = 3
    strategy: str = "fixed_size"
    customer_role: str | None = None


def sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def run_chat(req: ChatRequest) -> AsyncIterator[str]:
    """Phát từng bước của pipeline RAG qua SSE để UI hiện tiến trình thật."""

    def step(sid: str, label: str, detail: str, elapsed_ms: float, extra: dict | None = None) -> str:
        return sse("step", {"id": sid, "label": label, "detail": detail,
                            "ms": round(elapsed_ms, 1), **(extra or {})})

    started = time.perf_counter()
    yield sse("start", {"question": req.question})

    mark = time.perf_counter()
    embedder = await asyncio.to_thread(backend.embedder_ready)
    yield step("embed-backend", "Chuẩn bị mô hình nhúng",
               f"Backend: {backend.backend_name}", (time.perf_counter() - mark) * 1000)

    mark = time.perf_counter()
    store = await asyncio.to_thread(backend.store_for, req.strategy)
    yield step("index", "Nạp cơ sở tri thức",
               f"{store.get_collection_size()} chunk từ {len(read_documents())} tài liệu "
               f"(chiến lược: {req.strategy})", (time.perf_counter() - mark) * 1000)

    mark = time.perf_counter()
    if req.customer_role:
        detail = f'Lọc metadata customer_role = "{req.customer_role}" trước khi chấm điểm'
    else:
        detail = "Không lọc metadata — tìm trên toàn bộ corpus"
    yield step("filter", "Áp bộ lọc metadata", detail, (time.perf_counter() - mark) * 1000)

    mark = time.perf_counter()
    if req.customer_role:
        results = await asyncio.to_thread(
            store.search_with_filter, req.question, req.top_k, {"customer_role": req.customer_role})
    else:
        results = await asyncio.to_thread(store.search, req.question, req.top_k)
    yield step("search", "Tìm kiếm vector",
               f"Trả về {len(results)} chunk gần nhất theo cosine similarity",
               (time.perf_counter() - mark) * 1000,
               {"results": [{
                   "id": r["id"],
                   "score": round(float(r["score"]), 4),
                   "doc_id": r["metadata"].get("doc_id", ""),
                   "customer_role": r["metadata"].get("customer_role", ""),
                   "source_url": r["metadata"].get("source_url", ""),
                   "preview": r["content"][:320],
               } for r in results]})

    mark = time.perf_counter()
    target = FilteredStoreView(store, {"customer_role": req.customer_role}) if req.customer_role else store
    capture = PromptCapture()
    fallback = await asyncio.to_thread(
        KnowledgeBaseAgent(store=target, llm_fn=capture).answer, req.question, req.top_k)

    if LLM_PROVIDER != "openai" or capture.prompt is None:
        # Store rỗng / không có kết quả: agent đã tự trả lời, không cần gọi LLM.
        answer = fallback or extractive_llm(capture.prompt or "")
        yield step("generate", "Sinh câu trả lời",
                   "llm_fn = stub trích xuất (không gọi API ngoài)",
                   (time.perf_counter() - mark) * 1000)
        yield sse("token", {"text": answer})
    else:
        yield step("generate", "Sinh câu trả lời",
                   f"OpenAI {CHAT_MODEL} — streaming, ngữ cảnh {req.top_k} chunk",
                   (time.perf_counter() - mark) * 1000)
        pieces: list[str] = []
        try:
            stream = await openai_client().chat.completions.create(
                model=CHAT_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": capture.prompt},
                ],
                temperature=0.2,
                stream=True,
            )
            async for part in stream:
                if not part.choices:
                    continue
                delta = part.choices[0].delta.content
                if delta:
                    pieces.append(delta)
                    yield sse("token", {"text": delta})
        except Exception as error:  # noqa: BLE001 - demo không được chết vì lỗi mạng
            yield step("llm-error", "OpenAI lỗi — quay về stub trích xuất",
                       f"{type(error).__name__}: {error}"[:200], 0.0)
            pieces = [extractive_llm(capture.prompt)]
            yield sse("token", {"text": pieces[0]})
        answer = "".join(pieces)

    yield sse("answer", {
        "answer": answer,
        "sources": [{
            "doc_id": r["metadata"].get("doc_id", ""),
            "source_url": r["metadata"].get("source_url", ""),
            "score": round(float(r["score"]), 4),
        } for r in results],
        "total_ms": round((time.perf_counter() - started) * 1000, 1),
    })


@app.post("/api/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    return StreamingResponse(run_chat(req), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
