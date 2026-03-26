"""
Text chunking strategies for knowledge ingestion.
"""

import structlog

logger = structlog.get_logger()


class TextChunker:
    """
    Recursive character text splitter for knowledge documents.
    Splits text into overlapping chunks suitable for embedding.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        separators: list[str] | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def chunk(self, text: str) -> list[str]:
        """Split text into chunks using recursive character splitting."""
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        chunks: list[str] = []
        self._split_recursive(text, self.separators, chunks)
        return chunks

    def _split_recursive(self, text: str, separators: list[str], chunks: list[str]) -> None:
        if len(text) <= self.chunk_size:
            stripped = text.strip()
            if stripped:
                chunks.append(stripped)
            return

        separator = separators[0] if separators else ""
        remaining_separators = separators[1:] if len(separators) > 1 else [""]

        if separator:
            parts = text.split(separator)
        else:
            # Last resort: hard split by characters
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                chunk = text[i : i + self.chunk_size].strip()
                if chunk:
                    chunks.append(chunk)
            return

        current = ""
        for part in parts:
            candidate = current + separator + part if current else part
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current.strip():
                    chunks.append(current.strip())
                if len(part) > self.chunk_size:
                    self._split_recursive(part, remaining_separators, chunks)
                    current = ""
                else:
                    # Overlap: take the tail of the previous chunk
                    if current and self.chunk_overlap > 0:
                        overlap_text = current[-self.chunk_overlap :]
                        current = overlap_text + separator + part
                    else:
                        current = part

        if current.strip():
            chunks.append(current.strip())


def estimate_tokens(text: str) -> int:
    """Rough token count estimate (~4 chars per token for English)."""
    return len(text) // 4
