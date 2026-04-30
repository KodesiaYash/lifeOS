# AI Life OS — System Design Document

**Version**: 0.1.0-draft  
**Status**: Current implementation baseline  
**Last Updated**: 2026-04-30

## 1. Vision

AI Life OS is a self-hosted, single-user life management platform with an AI-native control plane. It is built as a modular monolith so one person or a small team can move quickly without giving up internal boundaries.

The platform is organized around shared infrastructure:

- one communication layer for all channels
- one memory fabric for context and recall
- one retrieval layer for personal knowledge
- one orchestration layer for tools, workflows, and agents
- one plugin contract for domains such as health, finance, productivity, relationships, learning, and home

## 2. Design Goals

| Goal | Description |
|---|---|
| Platform-first | Shared infrastructure should benefit every domain. |
| AI-native kernel | Intent handling, context assembly, retrieval, and response generation are part of the core. |
| Single-user simplicity | The runtime and schema are optimized for one self-hosted instance. |
| Channel-agnostic behavior | Different channels normalize into the same internal message model. |
| Deterministic state changes | LLMs can reason and suggest, but durable mutations still go through explicit tools and services. |
| Auditable execution | Events, workflow state, and agent executions are persisted for inspection. |
| Plugin-based extensibility | New domains should plug in through declarations instead of kernel edits. |

## 3. Architecture Overview

```text
Inbound Channel
  -> Communication Adapter
  -> Communication Service / Stored Messages
  -> Global Orchestrator
     -> Memory Assembler
     -> Retrieval Coordinator
     -> Tool Registry / Agent Runtime
     -> Response Generation
     -> Event Bus
  -> Outbound Dispatcher
  -> Channel Adapter
```

At deployment time the stack is:

- `FastAPI` for HTTP APIs and webhooks
- `PostgreSQL` for relational state
- `pgvector` for semantic search
- `Redis` for short-term memory and queued background work
- `MinIO` for object storage
- `APScheduler` and `arq` for recurring and background work

## 4. Core Modules

| Module | Responsibility |
|---|---|
| `src/shared/` | Database base classes, crypto, pagination, time helpers |
| `src/core/` | Global settings, domain registry, request context middleware |
| `src/events/` | In-process publish/subscribe bus plus persisted event log |
| `src/communication/` | Channel adapters, identity resolution, conversations, stored messages |
| `src/memory/` | Short-term session memory, structured facts, semantic memory, context assembly |
| `src/knowledge/` | Document ingestion, chunking, embeddings, knowledge storage |
| `src/retrieval/` | Semantic, structured, and keyword retrieval with reranking |
| `src/kernel/` | LLM client, prompt registry, tool registry, global orchestrator |
| `src/orchestration/` | Workflow definitions and workflow execution runtime |
| `src/agents/` | Agent registry and ReAct-style execution records |
| `src/scheduling/` | Scheduled jobs and queued background tasks |
| `src/connectors/` | External service definitions, instances, and sync logs |
| `src/domains/` | Domain plugin declarations and routers |

## 5. Request Lifecycle

### 5.1 Inbound flow

1. A message arrives from a channel webhook or the REST endpoint.
2. The channel adapter converts it into a normalized inbound event.
3. The communication layer resolves channel identity, conversation, and message persistence.
4. The orchestrator receives the message with conversation and session context.

### 5.2 Context assembly

1. Short-term memory loads recent turns from Redis-backed session storage.
2. Structured memory loads durable facts from PostgreSQL.
3. Semantic memory and knowledge retrieval gather relevant personal context.
4. The retrieval coordinator fuses and reranks results into a bounded context window.

### 5.3 Execution

1. The orchestrator classifies intent.
2. Available tools are filtered by domain when a domain is known.
3. The LLM can call tools in a bounded loop.
4. Tool results are appended to the prompt state.
5. The final assistant response is generated.

### 5.4 Post-processing

1. A `system.message_processed` event is emitted.
2. The message exchange is appended to short-term memory.
3. Background tasks can consolidate memory or trigger downstream work.

## 6. Domain Plugin System

The domain plugin contract is the main extensibility mechanism.

Each domain provides:

- tools
- agents
- event handlers
- memory categories
- a FastAPI router
- optional workflow declarations

Startup wiring in `src/domains/loader.py`:

1. discover plugin instances under `src/domains/*`
2. validate naming and cross-references
3. register tools into the tool registry
4. register agents into the agent registry
5. subscribe event handlers to the event bus
6. record memory categories
7. mount the router under `/api/v1/domains/{domain_id}`
8. call the plugin lifecycle hook

Current scaffold inventory:

- `6` domains
- `26` tools
- `9` agents
- `12` event handlers
- `29` memory categories

This wiring is implemented today. Most domain handlers still return stub payloads and are intended to be replaced in Phase 1.

## 7. Memory and Retrieval

### 7.1 Memory layers

| Layer | Backing | Purpose |
|---|---|---|
| Short-term | Redis | Active session history and transient context |
| Structured | PostgreSQL | Durable facts with categories and confidence |
| Semantic | PostgreSQL + pgvector | Fuzzy recall over summaries and insights |
| Conversation summaries | PostgreSQL + pgvector | Condensed history across turns |

### 7.2 Knowledge layer

The knowledge pipeline supports:

1. document registration
2. content fetch or parse
3. deduplication by content hash
4. chunking
5. embedding
6. chunk storage
7. optional tagging

The current structure is in place, but several parsers and tagging paths are still stubs.

### 7.3 Retrieval strategies

The retrieval coordinator supports:

- semantic retrieval
- structured retrieval
- keyword retrieval
- hybrid fusion with reranking

Reranking combines relevance, recency, importance, and diversity signals.

## 8. Communication and Agents

### 8.1 Communication

The communication layer separates protocol handling from business logic:

- channel adapters normalize payloads
- identities map external accounts to local conversations
- messages and delivery events are stored centrally
- outbound dispatch routes replies back through the correct adapter

### 8.2 Agents

Agents are stored as definitions plus execution records:

- definitions describe prompts, model preferences, and tool access
- executions record inputs, outputs, tool calls, status, timing, and token usage

The runtime is bounded and explicit. It is not a free-form swarm system.

## 9. Storage and Deployment

### 9.1 Persistence

| System | Use |
|---|---|
| PostgreSQL | Source of truth for platform state |
| pgvector | Vector columns for memory and knowledge search |
| Redis | Session state and queued work |
| MinIO | S3-compatible object storage for attachments and source content |

### 9.2 Local deployment

The local Compose stack brings up:

- `app`
- `worker`
- `postgres`
- `redis`
- `minio`
- `pgadmin`
- `redisinsight`

This matches the self-hosted development model documented in `README.md`.

## 10. Testing Strategy

The repo uses a 5-tier test layout:

| Tier | Purpose |
|---|---|
| Unit | Isolated logic correctness |
| Integration | Cross-module behavior |
| E2E | Full message-to-response flows with cassettes |
| Drift | Real-model behavior checks |
| Architecture | Domain wiring, manifests, and requirement traceability |

Requirements live in `tests/requirements/` and architecture tests verify that domain declarations, tests, and requirements stay aligned.

## 11. Current Implementation Status

### Implemented well

- modular monolith structure
- plugin auto-wiring
- generic storage models and initial migration
- test architecture and CI pipeline
- local development stack
- single-user simplification across runtime and schema

### Still incomplete

- domain business logic is mostly stubbed
- intent classification in the orchestrator is still placeholder logic
- the REST message endpoint is not yet wired into the full orchestration path
- several knowledge parsers and tagging paths are placeholders
- domain-specific SQLAlchemy models are still planned, not implemented

## 12. Near-Term Priorities

1. Wire inbound REST messages into the orchestrator.
2. Replace domain stubs with real models and handlers.
3. Implement real intent routing.
4. Finish ingestion parser paths and tagging.
5. Add domain migrations as real tables land.

This document is intentionally aligned to the current repository state rather than earlier broader design explorations.
