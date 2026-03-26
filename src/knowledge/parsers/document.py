"""
Office document parser stub (DOCX, PPTX, etc.).
TODO: Implement using python-docx or similar.
"""

import structlog

logger = structlog.get_logger()


class DocumentParser:
    """Parse office documents (DOCX, PPTX, etc.) into text content."""

    async def parse(self, doc_bytes: bytes, filename: str | None = None) -> str | None:
        """Extract text content from an office document."""
        logger.info("document_parser_stub", filename=filename)
        # TODO: Implement with python-docx, python-pptx
        return None
