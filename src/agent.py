from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        if self.store.get_collection_size() == 0:
            return "Cơ sở tri thức đang trống. Không có ngữ cảnh để trả lời câu hỏi này."

        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy ngữ cảnh liên quan. Không thể trả lời câu hỏi này từ cơ sở tri thức."

        context_parts = []
        for i, record in enumerate(results, start=1):
            source = record["metadata"].get("doc_id", "unknown")
            context_parts.append(f"[{i}] (source: {source}) {record['content']}")
        context = "\n".join(context_parts)

        prompt = (
            "Instruction: Only use the context below to answer the question. "
            "If the context is not sufficient to answer, say so explicitly. "
            "Answer in Vietnamese.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n"
            "Answer:"
        )

        return self.llm_fn(prompt)
