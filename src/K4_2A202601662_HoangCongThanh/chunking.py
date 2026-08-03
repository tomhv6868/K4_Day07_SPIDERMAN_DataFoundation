from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    # Cắt tại khoảng trắng ĐỨNG SAU dấu kết câu, nên dấu câu ở lại cuối câu trước.
    SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        sentences = [part.strip() for part in self.SENTENCE_BOUNDARY.split(text) if part.strip()]
        limit = self.max_sentences_per_chunk
        return [" ".join(sentences[start : start + limit]) for start in range(0, len(sentences), limit)]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return [piece.strip() for piece in self._split(text, self.separators) if piece.strip()]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Base case 1: đã đủ ngắn, không cần chia tiếp.
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Base case 2: hết separator (hoặc separator rỗng) -> cắt cứng theo chunk_size.
        if not remaining_separators or remaining_separators[0] == "":
            return self._fixed_slices(current_text)

        separator, *lower_priority = remaining_separators
        if separator not in current_text:
            # Separator này không có trong text: hạ một bậc ưu tiên, text giữ nguyên.
            return self._split(current_text, lower_priority)

        chunks: list[str] = []
        buffer = ""
        for piece in current_text.split(separator):
            candidate = f"{buffer}{separator}{piece}" if buffer else piece
            if len(candidate) <= self.chunk_size:
                buffer = candidate
                continue

            # Gộp thêm sẽ vượt giới hạn: chốt buffer hiện tại lại.
            if buffer:
                chunks.append(buffer)
                buffer = ""
            if len(piece) > self.chunk_size:
                # Riêng phần này vẫn quá dài -> xử lý lại bằng separator ưu tiên thấp hơn.
                chunks.extend(self._split(piece, lower_priority))
            else:
                buffer = piece

        if buffer:
            chunks.append(buffer)
        return chunks

    def _fixed_slices(self, current_text: str) -> list[str]:
        size = max(1, self.chunk_size)
        return [current_text[start : start + size] for start in range(0, len(current_text), size)]


class HeadingFaqChunker:
    """
    Chunker cá nhân (Hoàng Công Thành) — chia theo ĐƠN VỊ CẤU TRÚC của văn bản
    chính sách, không theo độ dài.

    Ranh giới nhận diện ở đầu dòng: heading Markdown (`#`), mục La Mã (`I.`,
    `II.`) và câu hỏi FAQ đánh số (`1.`, `2.`). Mỗi chunk là một cặp hỏi–đáp
    hoặc một khoản trọn vẹn.

    KHÔNG cắt ở ý chữ cái (`a)`, `b)`) — đây là bộ phận của khoản cha, tách ra
    thì mỗi ý thành một mẩu ngắn mất ngữ cảnh. Bản đầu có cắt ở đây và tụt từ
    9/10 xuống 7/10 trên benchmark nhóm (xem REPORT_CANHAN mục 5).

    Hai điểm khác biệt so với ba chunker baseline:

    1. **Gắn ngữ cảnh cha vào đầu chunk** — mỗi chunk mang theo tiêu đề tài liệu
       và tiêu đề mục chứa nó. Trong corpus K4 có nhiều quy định trùng chủ đề
       nhưng khác phạm vi áp dụng (thời hạn phản hồi của mô hình NGON khác với
       thời hạn chung); thiếu tiêu đề mục thì hai chunk gần như không phân biệt được.
    2. **Có tầng dự phòng** — khoản nào vượt `max_chunk_size` được đẩy qua
       `RecursiveChunker`, nên tài liệu không có đánh số (các bài trên moit.gov.vn)
       vẫn chia được thay vì trả về một chunk khổng lồ.
    """

    BOUNDARY = re.compile(r"^(?=(?:#{1,6}\s|[IVXLC]{1,5}\.\s|\d{1,2}\.\s))", re.M)
    SECTION_HEAD = re.compile(r"^(?:#{1,6}\s|[IVXLC]{1,5}\.\s)")
    TITLE_HEAD = re.compile(r"^#\s")

    def __init__(self, max_chunk_size: int = 900, min_chunk_size: int = 120) -> None:
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self._fallback = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        parts = [part.strip() for part in self.BOUNDARY.split(text) if part.strip()]
        title = ""
        section = ""
        chunks: list[str] = []

        for part in parts:
            if self.SECTION_HEAD.match(part):
                head, _, body = part.partition("\n")
                if self.TITLE_HEAD.match(part):
                    title, section = head.lstrip("# ").strip(), ""
                else:
                    section = head.strip()
                part = body.strip()
                if not part:
                    continue

            prefix = " — ".join(value for value in (title, section) if value)
            if len(part) > self.max_chunk_size:
                chunks.extend(self._with_prefix(prefix, piece) for piece in self._fallback.chunk(part))
                continue

            candidate = self._with_prefix(prefix, part)
            # Mảnh quá ngắn (dòng tiêu đề trơ trọi, một gạch đầu dòng) tự nó
            # không trả lời được gì -> nhập vào chunk liền trước.
            if chunks and len(candidate) < self.min_chunk_size:
                chunks[-1] = f"{chunks[-1]}\n{part}"
            else:
                chunks.append(candidate)

        return chunks

    @staticmethod
    def _with_prefix(prefix: str, body: str) -> str:
        return f"[{prefix}]\n{body}" if prefix else body


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if not norm_a or not norm_b:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            # overlap tỉ lệ theo chunk_size để bảng so sánh phản ánh chiến lược,
            # không phải phản ánh một hằng số overlap mặc định.
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=chunk_size // 10),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            total_length = sum(len(piece) for piece in chunks)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": total_length / len(chunks) if chunks else 0.0,
                "chunks": chunks,
            }
        return comparison
