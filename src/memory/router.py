"""
API endpoints for scoped memory CRUD and retrieval.
"""

import uuid

from fastapi import APIRouter, HTTPException, Query

from src.dependencies import DbSession
from src.memory.schemas import (
    MemoryFactRead,
    MemoryFactUpsertRequest,
    ScopedMemoryPacket,
    ScopedMemoryRetrieveRequest,
    SemanticMemoryRead,
    SemanticMemoryStoreRequest,
)
from src.memory.service import MemoryService

router = APIRouter()


@router.post("/facts", response_model=MemoryFactRead)
async def upsert_fact(payload: MemoryFactUpsertRequest, db: DbSession) -> MemoryFactRead:
    """Create or update a structured memory fact in a namespace."""
    service = MemoryService(db)
    fact = await service.upsert_fact(
        namespace=payload.namespace,
        category=payload.category,
        key=payload.key,
        value=payload.value,
        structured_value=payload.structured_value,
        confidence=payload.confidence,
        source=payload.source,
    )
    return MemoryFactRead.model_validate(fact)


@router.get("/facts", response_model=list[MemoryFactRead])
async def list_facts(
    db: DbSession,
    namespace: str = Query(default="general"),
    category: str | None = Query(default=None),
) -> list[MemoryFactRead]:
    """List active facts within a namespace."""
    service = MemoryService(db)
    facts = await service.list_facts(namespace=namespace, category=category)
    return [MemoryFactRead.model_validate(fact) for fact in facts]


@router.delete("/facts/{fact_id}", response_model=MemoryFactRead)
async def delete_fact(fact_id: uuid.UUID, db: DbSession) -> MemoryFactRead:
    """Soft-delete a structured fact."""
    service = MemoryService(db)
    fact = await service.delete_fact(fact_id)
    if fact is None:
        raise HTTPException(status_code=404, detail="Memory fact not found")
    return MemoryFactRead.model_validate(fact)


@router.post("/semantic", response_model=SemanticMemoryRead)
async def store_semantic_memory(payload: SemanticMemoryStoreRequest, db: DbSession) -> SemanticMemoryRead:
    """Create a semantic memory in a namespace."""
    service = MemoryService(db)
    memory = await service.store_semantic_memory(
        namespace=payload.namespace,
        memory_type=payload.memory_type,
        content=payload.content,
        related_domains=payload.related_domains,
        confidence=payload.confidence,
        importance=payload.importance,
        metadata=payload.metadata,
    )
    return SemanticMemoryRead.model_validate(memory)


@router.get("/semantic", response_model=list[SemanticMemoryRead])
async def list_semantic_memories(
    db: DbSession,
    namespace: str = Query(default="general"),
    limit: int = Query(default=25, ge=1, le=100),
) -> list[SemanticMemoryRead]:
    """List semantic memories within a namespace."""
    service = MemoryService(db)
    memories = await service.list_semantic_memories(namespace=namespace, limit=limit)
    return [SemanticMemoryRead.model_validate(memory) for memory in memories]


@router.delete("/semantic/{memory_id}", response_model=SemanticMemoryRead)
async def delete_semantic_memory(memory_id: uuid.UUID, db: DbSession) -> SemanticMemoryRead:
    """Soft-delete a semantic memory."""
    service = MemoryService(db)
    memory = await service.delete_semantic_memory(memory_id)
    if memory is None:
        raise HTTPException(status_code=404, detail="Semantic memory not found")
    return SemanticMemoryRead.model_validate(memory)


@router.post("/retrieve", response_model=ScopedMemoryPacket)
async def retrieve_scoped_memory(payload: ScopedMemoryRetrieveRequest, db: DbSession) -> ScopedMemoryPacket:
    """Retrieve shared and namespace-specific memory context for a routed domain."""
    service = MemoryService(db)
    return await service.retrieve_scoped_context(
        namespace=payload.namespace,
        query=payload.query,
        session_id=payload.session_id,
    )
