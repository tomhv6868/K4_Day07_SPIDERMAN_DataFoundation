from __future__ import annotations

import math
import re
import numpy as np

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

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        text_length = len(text)
        sentences: list[str] = []
        start = 0
        i = 0

        while i < text_length - 1:
            ch = text[i]
            if ch == ".":
                sep = text[i + 1]
                if sep == " " or sep == "\n":
                    sentence = text[start : i + 1].strip()
                    if sentence:
                        sentences.append(sentence)
                    start = i + 2
                    i += 1
            elif ch == "!" or ch == "?":
                if text[i + 1] == " ":
                    sentence = text[start : i + 1].strip()
                    if sentence:
                        sentences.append(sentence)
                    start = i + 2
                    i += 1
            i += 1

        tail = text[start:].strip()
        if tail:
            sentences.append(tail)

        if not sentences:
            return [text.strip()] if text.strip() else []

        chunks: list[str] = []
        for j in range(0, len(sentences), self.max_sentences_per_chunk):
            grouped = sentences[j : j + self.max_sentences_per_chunk]
            chunks.append(" ".join(grouped).strip())

        return chunks


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
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        if separator == "":
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        split_text = current_text.split(separator)
        if len(split_text) == 1:
            return self._split(current_text, next_separators)

        chunks: list[str] = []
        current_parts: list[str] = []
        current_size = 0

        for part in split_text:
            if not current_parts:
                if len(part) > self.chunk_size:
                    chunks.extend(self._split(part, next_separators))
                else:
                    current_parts = [part]
                    current_size = len(part)
                continue

            added_size = len(separator) + len(part)
            if current_size + added_size <= self.chunk_size:
                current_parts.append(part)
                current_size += added_size
                continue

            chunks.append(separator.join(current_parts))
            if len(part) > self.chunk_size:
                chunks.extend(self._split(part, next_separators))
                current_parts = []
                current_size = 0
            else:
                current_parts = [part]
                current_size = len(part)

        if current_parts:
            chunks.append(separator.join(current_parts))

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    a = np.asarray(vec_a)
    b = np.asarray(vec_b)

    return 0 if np.sum(a**2) == 0 or np.sum(b**2) == 0 else (a @ b)/(np.sqrt(np.sum(a**2))*np.sqrt(np.sum(b**2)))


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        results: dict[str, dict[str, object]] = {}

        fixed_chunks = FixedSizeChunker(chunk_size=chunk_size, overlap=0).chunk(text)
        sentence_chunks = SentenceChunker().chunk(text)
        recursive_chunks = RecursiveChunker(chunk_size=chunk_size).chunk(text)

        def _build_stats(chunks: list[str]) -> dict[str, object]:
            chunk_count = len(chunks)
            avg_length = sum(map(len, chunks)) / chunk_count if chunk_count else 0.0
            return {
                "count": chunk_count,
                "avg_length": avg_length,
                "chunks": chunks,
            }

        results["fixed_size"] = _build_stats(fixed_chunks)
        results["by_sentences"] = _build_stats(sentence_chunks)
        results["recursive"] = _build_stats(recursive_chunks)

        return results
