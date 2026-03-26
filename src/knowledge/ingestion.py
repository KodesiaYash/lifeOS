"""
Knowledge ingestion pipeline orchestrator.
Coordinates: fetch → parse → deduplicate → chunk → embed → tag → store.

Single-user mode: No tenant_id or user_id needed.
"""

import hashlib

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.knowledge.chunking import TextChunker, estimate_tokens
from src.knowledge.embedding import EmbeddingService
from src.knowledge.models import KnowledgeChunk, KnowledgeDocument
from src.knowledge.repository import KnowledgeChunkRepository, KnowledgeDocumentRepository
from src.knowledge.schemas import KnowledgeDocumentCreate

logger = structlog.get_logger()


class IngestionPipeline:
    """
    Orchestrates the knowledge ingestion process.

    Steps:
    1. Create document record (status=pending)
    2. Fetch and parse content
    3. Deduplication check (content_hash)
    4. Chunk text
    5. Generate embeddings
    6. Store chunks with embeddings
    7. Tag and classify (LLM-based)
    8. Update document status (status=completed)
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.doc_repo = KnowledgeDocumentRepository(session)
        self.chunk_repo = KnowledgeChunkRepository(session)
        self.chunker = TextChunker()
        self.embedding_service = EmbeddingService()

    async def ingest(
        self,
        data: KnowledgeDocumentCreate,
        raw_content: str | None = None,
    ) -> KnowledgeDocument:
        """
        Run the full ingestion pipeline for a document.
        If raw_content is not provided, the pipeline will attempt to fetch it.
        """
        # 1. Create document record
        doc = KnowledgeDocument(
            source_type=data.source_type,
            url=data.url,
            title=data.title,
            author=data.author,
            description=data.description,
            content_type=data.content_type,
            language=data.language,
            domain_tags=data.domain_tags,
            user_tags=data.user_tags,
            source_channel=data.source_channel,
            status="processing",
        )
        doc = await self.doc_repo.create(doc)

        try:
            # 2. Fetch content if not provided
            if raw_content is None:
                raw_content = await self._fetch_content(doc)

            if not raw_content:
                await self.doc_repo.update_status(doc.id, "failed", "No content to process")
                return doc

            # 3. Deduplication check
            content_hash = hashlib.sha256(raw_content.encode()).hexdigest()
            existing = await self.doc_repo.get_by_content_hash(content_hash)
            if existing and existing.id != doc.id:
                await self.doc_repo.update_status(doc.id, "failed", f"Duplicate of document {existing.id}")
                logger.info("document_duplicate", doc_id=str(doc.id), existing_id=str(existing.id))
                return doc

            doc.content_hash = content_hash
            doc.word_count = len(raw_content.split())

            # 4. Chunk text
            chunks_text = self.chunker.chunk(raw_content)
            if not chunks_text:
                await self.doc_repo.update_status(doc.id, "failed", "No chunks produced")
                return doc

            # 5. Generate embeddings
            embeddings = await self.embedding_service.embed_batch(chunks_text)

            # 6. Store chunks
            chunks = [
                KnowledgeChunk(
                    document_id=doc.id,
                    chunk_index=i,
                    text=text,
                    token_count=estimate_tokens(text),
                    embedding=emb,
                )
                for i, (text, emb) in enumerate(zip(chunks_text, embeddings, strict=False))
            ]
            await self.chunk_repo.create_batch(chunks)
            doc.chunk_count = len(chunks)

            # 7. Update status
            from src.shared.time import utc_now

            doc.processed_at = utc_now()
            doc.status = "completed"
            await self.session.flush()

            logger.info(
                "document_ingested",
                doc_id=str(doc.id),
                chunks=len(chunks),
                words=doc.word_count,
            )
            return doc

        except Exception as e:
            await self.doc_repo.update_status(doc.id, "failed", str(e))
            logger.exception("ingestion_failed", doc_id=str(doc.id))
            raise

    async def _fetch_content(self, doc: KnowledgeDocument) -> str | None:
        """
        Fetch content based on source type.
        TODO: Implement actual fetching via parsers.
        """
        if doc.url:
            logger.info("fetch_content_stub", url=doc.url)
            # Will delegate to parsers (html, pdf, youtube, etc.)
            return None
        return None
