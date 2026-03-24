"""
Database access layer for knowledge entities.
"""
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.knowledge.models import KnowledgeChunk, KnowledgeDocument, KnowledgeRelation


class KnowledgeDocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, doc: KnowledgeDocument) -> KnowledgeDocument:
        self.session.add(doc)
        await self.session.flush()
        return doc

    async def get_by_id(self, doc_id: uuid.UUID) -> KnowledgeDocument | None:
        return await self.session.get(KnowledgeDocument, doc_id)

    async def get_by_content_hash(
        self, tenant_id: uuid.UUID, content_hash: str
    ) -> KnowledgeDocument | None:
        result = await self.session.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.tenant_id == tenant_id,
                KnowledgeDocument.content_hash == content_hash,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_url(
        self, tenant_id: uuid.UUID, url: str
    ) -> KnowledgeDocument | None:
        result = await self.session.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.tenant_id == tenant_id,
                KnowledgeDocument.url == url,
            )
        )
        return result.scalar_one_or_none()

    async def update_status(
        self, doc_id: uuid.UUID, status: str, error_message: str | None = None
    ) -> None:
        values: dict = {"status": status}
        if error_message is not None:
            values["error_message"] = error_message
        await self.session.execute(
            update(KnowledgeDocument).where(KnowledgeDocument.id == doc_id).values(**values)
        )

    async def list_by_user(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[KnowledgeDocument]:
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.tenant_id == tenant_id,
            KnowledgeDocument.user_id == user_id,
            KnowledgeDocument.deleted_at.is_(None),
        )
        if status is not None:
            stmt = stmt.where(KnowledgeDocument.status == status)
        stmt = stmt.order_by(KnowledgeDocument.captured_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class KnowledgeChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_batch(self, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]:
        self.session.add_all(chunks)
        await self.session.flush()
        return chunks

    async def search_by_embedding(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        embedding: list[float],
        limit: int = 10,
    ) -> list[KnowledgeChunk]:
        stmt = (
            select(KnowledgeChunk)
            .where(
                KnowledgeChunk.tenant_id == tenant_id,
                KnowledgeChunk.user_id == user_id,
                KnowledgeChunk.embedding.isnot(None),
                KnowledgeChunk.deleted_at.is_(None),
            )
            .order_by(KnowledgeChunk.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_document(self, document_id: uuid.UUID) -> list[KnowledgeChunk]:
        result = await self.session.execute(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.document_id == document_id)
            .order_by(KnowledgeChunk.chunk_index)
        )
        return list(result.scalars().all())


class KnowledgeRelationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_batch(self, relations: list[KnowledgeRelation]) -> list[KnowledgeRelation]:
        self.session.add_all(relations)
        await self.session.flush()
        return relations

    async def search_by_entity(
        self, tenant_id: uuid.UUID, entity_name: str
    ) -> list[KnowledgeRelation]:
        result = await self.session.execute(
            select(KnowledgeRelation).where(
                KnowledgeRelation.tenant_id == tenant_id,
                KnowledgeRelation.entity_name == entity_name,
            )
        )
        return list(result.scalars().all())
