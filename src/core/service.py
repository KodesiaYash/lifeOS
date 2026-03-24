"""
Business logic for core entities.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Tenant, TenantUser, User, Workspace
from src.core.repository import (
    TenantRepository,
    TenantUserRepository,
    UserRepository,
    WorkspaceRepository,
)
from src.core.schemas import TenantCreate, UserCreate, WorkspaceCreate


class CoreService:
    """Service layer for core platform operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tenants = TenantRepository(session)
        self.users = UserRepository(session)
        self.tenant_users = TenantUserRepository(session)
        self.workspaces = WorkspaceRepository(session)

    async def create_tenant(self, data: TenantCreate) -> Tenant:
        """Create a new tenant."""
        tenant = Tenant(
            name=data.name,
            slug=data.slug,
            plan=data.plan,
            settings=data.settings,
        )
        return await self.tenants.create(tenant)

    async def create_user(self, data: UserCreate) -> User:
        """Create a new user (not yet linked to a tenant)."""
        user = User(
            email=data.email,
            name=data.name,
            display_name=data.display_name,
            timezone=data.timezone,
            language=data.language,
        )
        return await self.users.create(user)

    async def add_user_to_tenant(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str = "member",
    ) -> TenantUser:
        """Link a user to a tenant with the given role."""
        existing = await self.tenant_users.get_by_tenant_and_user(tenant_id, user_id)
        if existing:
            return existing
        tenant_user = TenantUser(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
        )
        return await self.tenant_users.create(tenant_user)

    async def create_workspace(
        self, tenant_id: uuid.UUID, data: WorkspaceCreate
    ) -> Workspace:
        """Create a workspace within a tenant."""
        workspace = Workspace(
            tenant_id=tenant_id,
            name=data.name,
            type=data.type,
            settings=data.settings,
        )
        return await self.workspaces.create(workspace)
