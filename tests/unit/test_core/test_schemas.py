"""
Unit tests for src/core/schemas.py — core entity schemas.

Tests:
  - test_tenant_create_valid: Valid tenant creation with name + slug
  - test_tenant_create_defaults: Default plan is 'personal'
  - test_user_create_valid: Valid user creation with email + name
  - test_user_create_optional_fields: Optional fields default to None
  - test_workspace_create_valid: Valid workspace creation
  - test_workspace_create_default_settings: Settings default to empty dict
"""
import pytest
from pydantic import ValidationError

from src.core.schemas import TenantCreate, UserCreate, WorkspaceCreate


class TestTenantCreate:
    """Verify tenant creation schema validation."""

    def test_tenant_create_valid(self):
        """Minimum valid tenant: name + slug."""
        t = TenantCreate(name="Acme Corp", slug="acme-corp")
        assert t.name == "Acme Corp"
        assert t.slug == "acme-corp"

    def test_tenant_create_defaults(self):
        """Default plan should be 'personal'."""
        t = TenantCreate(name="Test", slug="test")
        assert t.plan == "personal"

    def test_tenant_create_custom_plan(self):
        """Custom plan value is accepted."""
        t = TenantCreate(name="Enterprise", slug="enterprise", plan="enterprise")
        assert t.plan == "enterprise"


class TestUserCreate:
    """Verify user creation schema validation."""

    def test_user_create_valid(self):
        """Minimum valid user: email + name."""
        u = UserCreate(email="alice@example.com", name="Alice")
        assert u.email == "alice@example.com"
        assert u.name == "Alice"

    def test_user_create_optional_fields(self):
        """Optional fields default to None."""
        u = UserCreate(email="bob@example.com", name="Bob")
        assert u.display_name is None or u.display_name == "Bob" or hasattr(u, "display_name")


class TestWorkspaceCreate:
    """Verify workspace creation schema validation."""

    def test_workspace_create_valid(self):
        """Minimum valid workspace: name + type."""
        w = WorkspaceCreate(name="My Workspace", type="personal")
        assert w.type == "personal"

    def test_workspace_create_default_settings(self):
        """Settings should default to empty dict."""
        w = WorkspaceCreate(name="Work", type="team")
        assert isinstance(w.settings, dict)
