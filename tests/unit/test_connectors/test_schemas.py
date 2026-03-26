"""
Unit tests for src/connectors/schemas.py — connector schemas.

Tests:
  - test_connector_definition_create: Valid connector type definition
  - test_connector_instance_create: Valid user-installed instance
  - test_connector_instance_defaults: Default credentials={}, config={}
  - test_sync_log_read: Sync log fields are preserved
"""

import uuid
from datetime import UTC, datetime

from src.connectors.schemas import (
    ConnectorDefinitionCreate,
    ConnectorInstanceCreate,
    SyncLogRead,
)


class TestConnectorDefinitionCreate:
    """Verify connector definition creation schema."""

    def test_valid_definition(self):
        """All required fields present."""
        d = ConnectorDefinitionCreate(
            connector_type="fitbit",
            name="Fitbit",
            provider="fitbit",
            auth_type="oauth2",
        )
        assert d.connector_type == "fitbit"
        assert d.auth_type == "oauth2"
        assert d.config_schema == {}
        assert d.capabilities == {}


class TestConnectorInstanceCreate:
    """Verify connector instance creation schema."""

    def test_valid_instance(self):
        """Minimum valid instance: type + display_name."""
        inst = ConnectorInstanceCreate(
            connector_type="fitbit",
            display_name="My Fitbit",
            credentials={"access_token": "abc123"},
        )
        assert inst.connector_type == "fitbit"
        assert inst.credentials["access_token"] == "abc123"

    def test_defaults(self):
        """Default credentials={}, config={}, sync_frequency=None."""
        inst = ConnectorInstanceCreate(
            connector_type="google_calendar",
            display_name="Google Calendar",
        )
        assert inst.credentials == {}
        assert inst.config == {}
        assert inst.sync_frequency_minutes is None


class TestSyncLogRead:
    """Verify sync log read schema."""

    def test_sync_log_fields(self):
        """All fields preserved from DB read."""
        log = SyncLogRead(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            sync_type="incremental",
            status="completed",
            records_fetched=24,
            records_created=18,
            records_updated=6,
            records_skipped=0,
            error_message=None,
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            duration_ms=1200,
        )
        assert log.records_fetched == 24
        assert log.records_created == 18
        assert log.duration_ms == 1200
