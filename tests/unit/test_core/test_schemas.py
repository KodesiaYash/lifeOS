"""Unit tests for src/core/schemas.py — core entity schemas.

Single-user mode tests:
  - test_settings_update_optional_fields: All fields are optional
  - test_settings_read_has_required_fields: Read schema has all required fields
  - test_domain_registry_update_optional: Update fields are optional
"""

import uuid
from datetime import datetime

from src.core.schemas import DomainRegistryUpdate, SettingsRead, SettingsUpdate


class TestSettingsUpdate:
    """Verify settings update schema validation."""

    def test_settings_update_all_optional(self):
        """All fields should be optional for partial updates."""
        s = SettingsUpdate()
        assert s.timezone is None
        assert s.language is None
        assert s.preferences is None
        assert s.active_domains is None

    def test_settings_update_partial(self):
        """Can update just timezone."""
        s = SettingsUpdate(timezone="America/New_York")
        assert s.timezone == "America/New_York"
        assert s.language is None

    def test_settings_update_preferences(self):
        """Can update preferences dict."""
        s = SettingsUpdate(preferences={"theme": "dark"})
        assert s.preferences == {"theme": "dark"}


class TestSettingsRead:
    """Verify settings read schema."""

    def test_settings_read_valid(self):
        """Valid settings read with all required fields."""
        s = SettingsRead(
            id=uuid.uuid4(),
            timezone="UTC",
            language="en",
            preferences={},
            active_domains=["health", "finance"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert s.timezone == "UTC"
        assert s.language == "en"
        assert "health" in s.active_domains


class TestDomainRegistryUpdate:
    """Verify domain registry update schema."""

    def test_domain_registry_update_optional(self):
        """All fields are optional."""
        d = DomainRegistryUpdate()
        assert d.active is None
        assert d.config is None

    def test_domain_registry_update_active(self):
        """Can update active status."""
        d = DomainRegistryUpdate(active=False)
        assert d.active is False
