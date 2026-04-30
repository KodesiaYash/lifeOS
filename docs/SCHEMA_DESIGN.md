# AI Life OS — Schema Design Document

**Version**: 0.1.0-draft  
**Status**: Current migration-aligned reference  
**Last Updated**: 2026-04-30

This document describes the schema that exists today in the committed Alembic migration:

- [6a88d45cecd6_initial_schema_for_single_user_mode.py](/Users/yashkodesia/Desktop/SysDes/lifeOS/alembic/versions/6a88d45cecd6_initial_schema_for_single_user_mode.py)

## 1. Principles

- The schema is optimized for a single self-hosted instance.
- Shared platform tables are implemented before domain-specific tables.
- PostgreSQL is the source of truth for durable state.
- `pgvector` is used where semantic similarity search is needed.
- Domain data is expected to grow through future Phase 1 migrations.

## 2. Naming Conventions

### 2.1 Table prefixes

| Prefix | Meaning |
|---|---|
| `core_` | Global application settings and domain registry |
| `comm_` | Communication channels, conversations, and messages |
| `mem_` | Memory and conversation summaries |
| `know_` | Knowledge ingestion and retrieval |
| `evt_` | Event log |
| `orch_` | Workflow definitions and executions |
| `sched_` | Scheduled jobs and background tasks |
| `agent_` | Agent definitions and execution records |
| `conn_` | External connector definitions, instances, and sync logs |

### 2.2 Standard columns

Most mutable tables inherit `TimestampedBase` and include:

- `id UUID PRIMARY KEY`
- `created_at TIMESTAMPTZ`
- `updated_at TIMESTAMPTZ`
- `deleted_at TIMESTAMPTZ NULL`

Some registry-style tables such as `core_settings`, `core_domain_registry`, `comm_channels`, `agent_definitions`, and `evt_events` define their timestamps directly.

## 3. Core Tables

| Table | Purpose | Key fields |
|---|---|---|
| `core_settings` | Singleton application settings row | `timezone`, `language`, `preferences`, `active_domains` |
| `core_domain_registry` | Installed domain manifests | `domain_id`, `name`, `version`, `manifest`, `active`, `config` |

Notes:

- `core_settings` models the global instance configuration.
- `core_domain_registry` stores which domain plugins are available and active.

## 4. Communication Tables

| Table | Purpose | Key fields |
|---|---|---|
| `comm_channels` | Available channel types | `type`, `display_name`, `config`, `active` |
| `comm_channel_accounts` | Account-level channel configuration | `channel_id`, `account_ref`, `display_name`, `credentials_ref`, `config` |
| `comm_channel_identities` | External person or chat identity | `channel_account_id`, `external_user_id`, `display_name`, `metadata` |
| `comm_conversations` | Conversation thread state | `channel_identity_id`, `channel_type`, `external_chat_id`, `message_count` |
| `comm_messages` | Inbound and outbound message history | `conversation_id`, `direction`, `content_type`, `body`, `idempotency_key`, `correlation_id` |
| `comm_message_events` | Delivery or processing events for a message | `message_id`, `event_type`, `channel_status`, `error_code`, `timestamp` |
| `comm_attachments` | Stored attachment metadata | `message_id`, `file_name`, `mime_type`, `storage_path` |

Important access patterns:

- look up conversations by `channel_identity_id`
- look up messages by `conversation_id`
- deduplicate or correlate message handling through `idempotency_key` and `correlation_id`

## 5. Memory Tables

| Table | Purpose | Key fields |
|---|---|---|
| `mem_facts` | Structured long-term facts | `domain`, `category`, `key`, `value`, `structured_value`, `confidence` |
| `mem_semantic_memories` | Semantic memories and summaries | `memory_type`, `content`, `embedding`, `source_domain`, `importance` |
| `mem_conversation_summaries` | Condensed conversation history | `conversation_id`, `session_id`, `summary`, `key_topics`, `domains_involved`, `embedding` |

Design notes:

- `mem_facts` supports supersession through `superseded_by`.
- semantic tables use vector columns sized for the configured embedding model.
- memory tables are cross-domain by design so domain insights can be reused.

## 6. Knowledge Tables

| Table | Purpose | Key fields |
|---|---|---|
| `know_documents` | Source document metadata and lifecycle | `source_type`, `url`, `title`, `content_hash`, `status`, `storage_path` |
| `know_chunks` | Chunked content for retrieval | `document_id`, `chunk_index`, `content`, `token_count`, `embedding` |
| `know_relations` | Extracted entities and relationships | `document_id`, `entity_name`, `entity_type`, `related_to`, `relation_type` |

Important behavior:

- `know_documents.content_hash` supports deduplication.
- `know_chunks` are deleted automatically with their parent document via `ON DELETE CASCADE`.
- chunk embeddings are the main knowledge retrieval surface.

## 7. Workflow Tables

| Table | Purpose | Key fields |
|---|---|---|
| `orch_workflow_definitions` | Reusable workflow templates | `name`, `domain`, `version`, `trigger_type`, `steps`, `active` |
| `orch_workflow_executions` | Runtime workflow instances | `definition_id`, `correlation_id`, `status`, `current_step`, `context`, `result` |
| `orch_workflow_step_executions` | Per-step execution trace | `execution_id`, `step_index`, `step_type`, `status`, `input_data`, `output_data` |

These tables are meant to support event-driven and scheduled workflows without pushing orchestration state into transient memory only.

## 8. Agent Tables

| Table | Purpose | Key fields |
|---|---|---|
| `agent_definitions` | Agent templates | `agent_type`, `name`, `domain`, `system_prompt`, `tools`, `model_preference` |
| `agent_executions` | Runtime records for agent runs | `agent_type`, `correlation_id`, `status`, `input_data`, `output_data`, `tool_calls`, `total_tokens` |

The split keeps declarative agent setup separate from operational telemetry.

## 9. Scheduling Tables

| Table | Purpose | Key fields |
|---|---|---|
| `sched_jobs` | Recurring scheduled jobs | `name`, `job_type`, `schedule_type`, `schedule_config`, `handler`, `next_run_at` |
| `sched_background_tasks` | One-off async tasks | `task_type`, `status`, `priority`, `payload`, `attempts`, `correlation_id` |

The model matches the runtime split:

- APScheduler for recurring jobs
- `arq` for queued background work

## 10. Connector Tables

| Table | Purpose | Key fields |
|---|---|---|
| `conn_definitions` | Available connector types | `connector_type`, `provider`, `auth_type`, `config_schema`, `capabilities` |
| `conn_instances` | Installed connector instances | `connector_type`, `display_name`, `credentials_encrypted`, `config`, `status`, `last_sync_at` |
| `conn_sync_logs` | Connector sync history | `instance_id`, `sync_type`, `status`, `records_fetched`, `records_updated`, `duration_ms` |

Credentials are stored encrypted and sync operations are logged explicitly.

## 11. Event Table

| Table | Purpose | Key fields |
|---|---|---|
| `evt_events` | Append-only platform event log | `event_type`, `event_category`, `domain`, `correlation_id`, `payload`, `source`, `importance`, `timestamp` |

This table supports:

- auditability
- replay-friendly event history
- cross-module decoupling
- debugging through shared correlation IDs

## 12. Vector Columns

The current schema includes vector storage in:

| Table | Column | Purpose |
|---|---|---|
| `mem_semantic_memories` | `embedding` | Long-term semantic recall |
| `mem_conversation_summaries` | `embedding` | Similar summary lookup |
| `know_chunks` | `embedding` | Knowledge retrieval |

The migration enables `pgvector` with:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## 13. Current Index Highlights

Representative indexes from the migration:

- `agent_executions.agent_type`
- `agent_executions.correlation_id`
- `comm_channel_identities.channel_account_id`
- `comm_conversations.channel_identity_id`
- `comm_messages.conversation_id`
- `comm_messages.correlation_id`
- `comm_message_events.message_id`
- `conn_sync_logs.instance_id`
- `core_domain_registry.domain_id`
- `evt_events.event_type`
- `evt_events.correlation_id`
- `know_documents.content_hash`
- `know_chunks.document_id`
- `orch_workflow_executions.correlation_id`
- `orch_workflow_step_executions.execution_id`
- `sched_background_tasks.task_type`
- `sched_background_tasks.correlation_id`

## 14. Tables Not Yet Implemented

The current migration does not yet include domain-specific business tables for:

- health
- finance
- productivity
- relationships
- learning
- home

Those models are still placeholders in:

- [src/domains/health/models.py](/Users/yashkodesia/Desktop/SysDes/lifeOS/src/domains/health/models.py)
- [src/domains/finance/models.py](/Users/yashkodesia/Desktop/SysDes/lifeOS/src/domains/finance/models.py)
- [src/domains/productivity/models.py](/Users/yashkodesia/Desktop/SysDes/lifeOS/src/domains/productivity/models.py)
- [src/domains/relationships/models.py](/Users/yashkodesia/Desktop/SysDes/lifeOS/src/domains/relationships/models.py)
- [src/domains/learning/models.py](/Users/yashkodesia/Desktop/SysDes/lifeOS/src/domains/learning/models.py)
- [src/domains/home/models.py](/Users/yashkodesia/Desktop/SysDes/lifeOS/src/domains/home/models.py)

The next schema expansion will come from those domain implementations rather than from another generic platform rewrite.
