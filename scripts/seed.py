"""
Seed script: populates the database with initial data for development/testing.
Creates a default tenant, user, workspace, and domain registrations.

Usage:
    python -m scripts.seed
"""
import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.shared.database import async_session_factory


async def seed_data() -> None:
    """Seed the database with initial development data."""
    async with async_session_factory() as session:
        from src.core.models import DomainRegistry, Tenant, TenantUser, User, Workspace

        # --- Default Tenant ---
        tenant = Tenant(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            name="Personal",
            slug="personal",
            plan="personal",
            settings={"default_timezone": "UTC"},
        )
        session.add(tenant)

        # --- Default User ---
        user = User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
            email="admin@lifeos.local",
            name="Admin User",
            display_name="Admin",
            timezone="UTC",
            language="en",
        )
        session.add(user)

        # --- Link User to Tenant ---
        tenant_user = TenantUser(
            tenant_id=tenant.id,
            user_id=user.id,
            role="owner",
        )
        session.add(tenant_user)

        # --- Default Workspace ---
        workspace = Workspace(
            tenant_id=tenant.id,
            name="My Life",
            type="personal",
            settings={},
        )
        session.add(workspace)

        # --- Domain Registrations ---
        domains = [
            {
                "domain_id": "health",
                "name": "Health & Fitness",
                "version": "0.1.0",
                "description": "Nutrition, exercise, sleep, vitals, and wellness tracking.",
                "manifest": {"tools": [], "agents": [], "event_types": []},
            },
            {
                "domain_id": "finance",
                "name": "Finance",
                "version": "0.1.0",
                "description": "Transaction tracking, budgets, investments, and financial goals.",
                "manifest": {"tools": [], "agents": [], "event_types": []},
            },
            {
                "domain_id": "productivity",
                "name": "Productivity",
                "version": "0.1.0",
                "description": "Tasks, projects, goals, habits, and time tracking.",
                "manifest": {"tools": [], "agents": [], "event_types": []},
            },
            {
                "domain_id": "relationships",
                "name": "Relationships",
                "version": "0.1.0",
                "description": "Contacts, interactions, relationship health, and social events.",
                "manifest": {"tools": [], "agents": [], "event_types": []},
            },
            {
                "domain_id": "learning",
                "name": "Learning",
                "version": "0.1.0",
                "description": "Courses, reading, skills, certifications, and learning goals.",
                "manifest": {"tools": [], "agents": [], "event_types": []},
            },
            {
                "domain_id": "home",
                "name": "Home & Environment",
                "version": "0.1.0",
                "description": "Household tasks, maintenance, inventory, and smart home.",
                "manifest": {"tools": [], "agents": [], "event_types": []},
            },
        ]
        for d in domains:
            session.add(DomainRegistry(**d))

        # --- Default Communication Channel ---
        from src.communication.models import Channel
        channels = [
            Channel(type="whatsapp", display_name="WhatsApp"),
            Channel(type="telegram", display_name="Telegram"),
            Channel(type="rest_api", display_name="REST API"),
        ]
        for ch in channels:
            session.add(ch)

        await session.commit()
        print("✅ Seed data created successfully.")
        print(f"   Tenant ID: {tenant.id}")
        print(f"   User ID:   {user.id}")
        print(f"   Domains:   {len(domains)} registered")


if __name__ == "__main__":
    asyncio.run(seed_data())
