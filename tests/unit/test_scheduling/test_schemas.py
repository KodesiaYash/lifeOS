"""
Unit tests for src/scheduling/schemas.py — scheduling schemas and enums.

Tests:
  - test_schedule_type_values: cron, interval, date
  - test_task_status_values: pending, running, completed, failed, retrying, cancelled
  - test_scheduled_job_create: Valid cron job creation with defaults
  - test_background_task_create: Valid background task with priority
  - test_background_task_defaults: Default priority=5, max_attempts=3
"""
import uuid

from src.scheduling.schemas import (
    BackgroundTaskCreate,
    ScheduleType,
    ScheduledJobCreate,
    TaskStatus,
)


class TestScheduleType:
    """Verify schedule type enum values."""

    def test_cron(self):
        assert ScheduleType.CRON == "cron"

    def test_interval(self):
        assert ScheduleType.INTERVAL == "interval"

    def test_date(self):
        assert ScheduleType.DATE == "date"


class TestTaskStatus:
    """Verify background task status enum values."""

    def test_all_statuses(self):
        expected = {"pending", "running", "completed", "failed", "retrying", "cancelled"}
        actual = {s.value for s in TaskStatus}
        assert expected == actual


class TestScheduledJobCreate:
    """Verify scheduled job creation schema."""

    def test_cron_job_create(self):
        """Valid cron job with daily 8am schedule."""
        job = ScheduledJobCreate(
            name="Daily Summary",
            job_type="daily_summary",
            schedule_type=ScheduleType.CRON,
            schedule_config={"hour": 8, "minute": 0},
            handler="src.scheduling.handlers.daily_summary",
        )
        assert job.schedule_type == "cron"
        assert job.schedule_config["hour"] == 8
        assert job.max_retries == 3

    def test_interval_job_create(self):
        """Valid interval job — every 30 minutes."""
        job = ScheduledJobCreate(
            name="Sync",
            job_type="connector_sync",
            schedule_type=ScheduleType.INTERVAL,
            schedule_config={"minutes": 30},
            handler="src.scheduling.handlers.sync",
        )
        assert job.schedule_type == "interval"


class TestBackgroundTaskCreate:
    """Verify background task creation schema."""

    def test_background_task_with_priority(self):
        """Custom priority is accepted."""
        task = BackgroundTaskCreate(
            task_type="process_knowledge_ingestion",
            payload={"document_id": str(uuid.uuid4())},
            priority=3,
        )
        assert task.priority == 3

    def test_background_task_defaults(self):
        """Default: priority=5, max_attempts=3."""
        task = BackgroundTaskCreate(task_type="test_task")
        assert task.priority == 5
        assert task.max_attempts == 3
        assert task.payload == {}
