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

    NO_CONTEXT = "(không tìm thấy đoạn tài liệu nào liên quan trong cơ sở tri thức)"

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3, metadata_filter: dict | None = None) -> str:
        """Truy xuất top-k chunk, dựng prompt có trích nguồn, rồi gọi llm_fn."""
        if metadata_filter:
            results = self.store.search_with_filter(question, top_k=top_k, metadata_filter=metadata_filter)
        else:
            results = self.store.search(question, top_k=top_k)

        return self.llm_fn(self._build_prompt(question, results))

    def _build_prompt(self, question: str, results: list[dict]) -> str:
        """Ghép ngữ cảnh có đánh số + nhãn nguồn để câu trả lời trích dẫn lại được."""
        if not results:
            context = self.NO_CONTEXT
        else:
            blocks = []
            for position, result in enumerate(results, start=1):
                metadata = result.get("metadata") or {}
                label = metadata.get("doc_id") or result.get("id") or "unknown"
                role = metadata.get("customer_role")
                header = f"[{position}] nguồn: {label}" + (f" | customer_role: {role}" if role else "")
                blocks.append(f"{header}\n{result.get('content', '').strip()}")
            context = "\n\n".join(blocks)

        return (
            "Bạn là trợ lý trả lời câu hỏi dựa trên tài liệu chính sách thương mại điện tử.\n"
            "Chỉ dùng thông tin trong phần NGỮ CẢNH bên dưới. Nếu ngữ cảnh không đủ để trả lời, "
            "hãy nói rõ là tài liệu không đề cập, tuyệt đối không suy đoán.\n"
            "Khi trả lời, trích số hiệu nguồn theo dạng [1], [2].\n\n"
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI: {question}\n\n"
            "TRẢ LỜI:"
        )
