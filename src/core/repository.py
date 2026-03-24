"""
Database access layer for core entities.
"""
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import (
    DomainInstallation,
    DomainRegistry,
    Tenant,
    TenantUser,
    User,
    UserProfile,
    Workspace,
)


class TenantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, tenant: Tenant) -> Tenant:
        self.session.add(tenant)
        await self.session.flush()
        return tenant

    async def get_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        return await self.session.get(Tenant, tenant_id)

    async def get_by_slug(self, slug: str) -> Tenant | None:
        result = await self.session.execute(select(Tenant).where(Tenant.slug == slug))
        return result.scalar_one_or_none()

    async def list_all(self, active_only: bool = True) -> list[Tenant]:
        stmt = select(Tenant)
        if active_only:
            stmt = stmt.where(Tenant.active.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


class TenantUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, tenant_user: TenantUser) -> TenantUser:
        self.session.add(tenant_user)
        await self.session.flush()
        return tenant_user

    async def get_by_tenant_and_user(
        self, tenant_id: uuid.UUID, user_id: uuid.UUID
    ) -> TenantUser | None:
        result = await self.session.execute(
            select(TenantUser).where(
                TenantUser.tenant_id == tenant_id,
                TenantUser.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(self, tenant_id: uuid.UUID) -> list[TenantUser]:
        result = await self.session.execute(
            select(TenantUser).where(TenantUser.tenant_id == tenant_id)
        )
        return list(result.scalars().all())


class WorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, workspace: Workspace) -> Workspace:
        self.session.add(workspace)
        await self.session.flush()
        return workspace

    async def list_by_tenant(self, tenant_id: uuid.UUID) -> list[Workspace]:
        result = await self.session.execute(
            select(Workspace).where(
                Workspace.tenant_id == tenant_id,
                Workspace.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())


class UserProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(
        self, tenant_id: uuid.UUID, user_id: uuid.UUID
    ) -> UserProfile:
        result = await self.session.execute(
            select(UserProfile).where(
                UserProfile.tenant_id == tenant_id,
                UserProfile.user_id == user_id,
            )
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            profile = UserProfile(tenant_id=tenant_id, user_id=user_id)
            self.session.add(profile)
            await self.session.flush()
        return profile

    async def update_profile(
        self, tenant_id: uuid.UUID, user_id: uuid.UUID, **kwargs: object
    ) -> UserProfile | None:
        profile = await self.get_or_create(tenant_id, user_id)
        for key, value in kwargs.items():
            if value is not None and hasattr(profile, key):
                setattr(profile, key, value)
        await self.session.flush()
        return profile


class DomainRegistryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register(self, domain: DomainRegistry) -> DomainRegistry:
        self.session.add(domain)
        await self.session.flush()
        return domain

    async def get_by_domain_id(self, domain_id: str) -> DomainRegistry | None:
        result = await self.session.execute(
            select(DomainRegistry).where(DomainRegistry.domain_id == domain_id)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[DomainRegistry]:
        result = await self.session.execute(
            select(DomainRegistry).where(DomainRegistry.active.is_(True))
        )
        return list(result.scalars().all())
