"""
PDF content parser stub.
TODO: Implement using PyPDF2 or pdfplumber.
"""
import structlog

logger = structlog.get_logger()


class PdfParser:
    """Parse PDF documents into text content."""

    async def parse(self, pdf_bytes: bytes, filename: str | None = None) -> str | None:
        """Extract text content from a PDF file."""
        logger.info("pdf_parser_stub", filename=filename)
        # TODO: Implement with PyPDF2 or pdfplumber
        return None
