"""
API endpoints for core entities (tenants, users, workspaces).
"""
import uuid

from fastapi import APIRouter, HTTPException, status

from src.core.schemas import (
    TenantCreate,
    TenantRead,
    TenantUserCreate,
    TenantUserRead,
    UserCreate,
    UserRead,
    WorkspaceCreate,
    WorkspaceRead,
)
from src.core.service import CoreService
from src.dependencies import DbSession, TenantId

router = APIRouter()


@router.post("/tenants", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
async def create_tenant(data: TenantCreate, db: DbSession) -> TenantRead:
    service = CoreService(db)
    tenant = await service.create_tenant(data)
    return TenantRead.model_validate(tenant)


@router.get("/tenants/{tenant_id}", response_model=TenantRead)
async def get_tenant(tenant_id: uuid.UUID, db: DbSession) -> TenantRead:
    service = CoreService(db)
    tenant = await service.tenants.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantRead.model_validate(tenant)


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, db: DbSession) -> UserRead:
    service = CoreService(db)
    user = await service.create_user(data)
    return UserRead.model_validate(user)


@router.get("/users/{user_id}", response_model=UserRead)
async def get_user(user_id: uuid.UUID, db: DbSession) -> UserRead:
    service = CoreService(db)
    user = await service.users.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)


@router.post(
    "/tenants/{tenant_id}/users",
    response_model=TenantUserRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_user_to_tenant(
    tenant_id: uuid.UUID,
    data: TenantUserCreate,
    db: DbSession,
) -> TenantUserRead:
    service = CoreService(db)
    tenant_user = await service.add_user_to_tenant(
        tenant_id=tenant_id,
        user_id=data.user_id,
        role=data.role,
    )
    return TenantUserRead.model_validate(tenant_user)


@router.post(
    "/workspaces",
    response_model=WorkspaceRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_workspace(
    data: WorkspaceCreate,
    db: DbSession,
    tenant_id: TenantId,
) -> WorkspaceRead:
    service = CoreService(db)
    workspace = await service.create_workspace(tenant_id, data)
    return WorkspaceRead.model_validate(workspace)
