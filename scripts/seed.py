"""
Seed script: populates the database with initial data for development/testing.
Creates default settings, domain registrations, and communication channels.

Single-user mode: No tenant/user/workspace models needed.

Usage:
    python -m scripts.seed
"""
import asyncio

from src.shared.database import async_session_factory


async def seed_data() -> None:
    """Seed the database with initial development data."""
    async with async_session_factory() as session:
        from src.core.models import DomainRegistry, Settings

        # --- Default Settings ---
        default_settings = Settings(
            key="app",
            value={
                "timezone": "UTC",
                "language": "en",
                "theme": "system",
                "notifications_enabled": True,
            },
        )
        session.add(default_settings)

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

        # --- Default Communication Channels ---
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
        print(f"   Settings: default app settings created")
        print(f"   Domains:  {len(domains)} registered")
        print(f"   Channels: {len(channels)} registered")


if __name__ == "__main__":
    asyncio.run(seed_data())
