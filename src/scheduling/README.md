# Scheduling Module (`src/scheduling/`)

Dual scheduling system: APScheduler for cron/interval jobs + arq for async background tasks.

## Contents

| File | Purpose |
|------|---------|
| `models.py` | SQLAlchemy models: ScheduledJob, BackgroundTask |
| `schemas.py` | Pydantic schemas, ScheduleType/TaskStatus enums |
| `repository.py` | Database access for scheduled jobs and background tasks |
| `scheduler.py` | APScheduler integration — cron/interval job management |
| `worker.py` | arq worker — async background task processing with Redis queue |

## Two Scheduling Systems

| System | Use Case | Backing |
|--------|----------|---------|
| APScheduler | Recurring cron/interval jobs (reminders, daily summaries) | In-process |
| arq | One-off async background tasks (ingestion, sync, consolidation) | Redis queue |

## Background Task Handlers

| Handler | Purpose |
|---------|---------|
| `process_knowledge_ingestion` | Run ingestion pipeline for a document |
| `process_memory_consolidation` | Consolidate short-term → long-term memory |
| `process_connector_sync` | Sync data from external connector |

## Running the Worker

```bash
arq src.scheduling.worker.WorkerSettings
```
