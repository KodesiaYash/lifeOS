# AI Life OS — System Design Document

**Version**: 0.1.0-draft
**Status**: Design Phase
**Last Updated**: 2026-03-24
**Authors**: Engineering Team

---

## Table of Contents

1. [Vision and Design Goals](#1-vision-and-design-goals)
2. [Non-Goals](#2-non-goals)
3. [Product Philosophy](#3-product-philosophy)
4. [Architecture Overview](#4-architecture-overview)
5. [Communication Layer Design](#5-communication-layer-design)
6. [AI-Native Kernel Design](#6-ai-native-kernel-design)
7. [Memory Architecture](#7-memory-architecture)
8. [RAG and Retrieval Architecture](#8-rag-and-retrieval-architecture)
9. [Workflow and Orchestration Architecture](#9-workflow-and-orchestration-architecture)
10. [Domain Plugin Architecture](#10-domain-plugin-architecture)
11. [Multi-Tenant Model](#11-multi-tenant-model)
12. [Database and Schema Design](#12-database-and-schema-design)
13. [Event Model](#13-event-model)
14. [Knowledge Ingestion Design](#14-knowledge-ingestion-design)
15. [Scheduling / Reminders / Tasking Model](#15-scheduling--reminders--tasking-model)
16. [Generic Agent Model](#16-generic-agent-model)
17. [Connector Model](#17-connector-model)
18. [Security / Privacy / Safety Model](#18-security--privacy--safety-model)
19. [Observability and Auditability](#19-observability-and-auditability)
20. [Scalability Path](#20-scalability-path)
21. [Suggested Technology Stack](#21-suggested-technology-stack)
22. [Project Structure](#22-project-structure)
23. [Domain Module Contracts](#23-domain-module-contracts)
24. [Example Domain Implementations](#24-example-domain-implementations)
25. [Example Workflows](#25-example-workflows)
26. [Implementation Phases](#26-implementation-phases)
27. [Risks and Tradeoffs](#27-risks-and-tradeoffs)

---

## 1. Vision and Design Goals

### 1.1 Vision

AI Life OS is a **generic, AI-native life operating system** — a platform that provides shared intelligent infrastructure on top of which many domain-specific systems (health, finance, education, language learning, knowledge management, life tracking, and arbitrary future domains) can be built.

It is **not** a chatbot. It is **not** a collection of LLM wrappers. It is an operating system for life management where AI is a first-class citizen embedded into the kernel — responsible for reasoning, personalization, memory consolidation, retrieval, planning, and adaptation — while deterministic services handle state mutations, calculations, and source-of-truth management.

### 1.2 Design Goals

| # | Goal | Description |
|---|------|-------------|
| G1 | **Platform-first** | All infrastructure is shared. Domains are plugins, not standalone apps. |
| G2 | **AI-native kernel** | AI is embedded into the core orchestration, memory, and retrieval — not bolted on. |
| G3 | **Multi-tenant capable from day 1** | Schema, isolation, and identity designed for multi-tenancy even if MVP is single-user. |
| G4 | **Channel-agnostic** | Communication channels are adapters. Business logic never depends on a specific channel. |
| G5 | **Shared memory fabric** | One memory system serves all domains — short-term, long-term, semantic, and knowledge. |
| G6 | **Shared retrieval/RAG** | One retrieval pipeline serves all domains with domain-filtered, hybrid search. |
| G7 | **Hierarchical orchestration** | Controlled, bounded agent execution — not free-form agent swarms. |
| G8 | **Event-driven internals** | Every meaningful action emits an event for auditability, replay, and personalization. |
| G9 | **Modular monolith first** | Single deployable unit with clean internal boundaries. Service split only when proven necessary. |
| G10 | **Deterministic where it matters** | Financial calculations, medication tracking, state mutations use deterministic code, not LLMs. |
| G11 | **Auditable and explainable** | Every AI decision, retrieval, and state change is traceable. |
| G12 | **Extensible by contract** | Any new domain plugs in through a well-defined contract without modifying the kernel. |

### 1.3 Success Criteria

- A new domain module can be added by implementing a plugin contract without touching kernel code.
- The same user message arriving from WhatsApp, Telegram, or REST API produces identical domain behavior.
- Memory from one domain is available to other domains through the shared fabric (with proper scoping).
- The system can be deployed as a single Docker Compose stack for a solo developer and later scaled horizontally.

---

## 2. Non-Goals

| # | Non-Goal | Rationale |
|---|----------|-----------|
| NG1 | Real-time collaboration between users | V1 is personal. Collaboration can be added later. |
| NG2 | Building a general-purpose AI agent framework | We use orchestration frameworks, not build one from scratch. |
| NG3 | Replacing specialized apps (MyFitnessPal, YNAB, Anki) | We integrate with or complement them, not replace their full feature sets. |
| NG4 | Running fine-tuned models in-house | MVP uses hosted LLM APIs. Fine-tuning is a future optimization. |
| NG5 | Mobile native apps | MVP channels are messaging apps and REST API. Native apps come later. |
| NG6 | HIPAA/SOC2/GDPR full compliance in MVP | Architecture accommodates compliance; formal certification is deferred. |
| NG7 | Full offline operation | Requires network for LLM calls and most operations. |
| NG8 | Multi-language UI in MVP | English first. Multi-language content (e.g., Dutch tutor content) is domain data, not platform localization. |

---

## 3. Product Philosophy

### 3.1 Core Principles

**1. The platform is the product, domains are features.**
Every investment in the kernel — memory, retrieval, orchestration, scheduling — pays dividends across all domains. Building a great health module should simultaneously make the finance module better through shared infrastructure.

**2. AI is the kernel, not a feature.**
AI doesn't sit on top. It is embedded into: how intents are understood, how memory is consolidated, how context is assembled, how responses are generated, and how the system adapts over time.

**3. Structured truth, semantic understanding.**
There are always two representations: the **deterministic source of truth** (a transaction amount, a body weight measurement, a task status) and the **semantic understanding** (why the user overspent, how their weight trend relates to their mood, which tasks they tend to procrastinate on). Both matter. They live in different layers. They are never confused.

**4. Memory is a first-class citizen.**
The system remembers. Not just chat history, but consolidated facts, behavioral patterns, preferences, cross-domain correlations, and evolving understanding. Memory is the moat.

**5. Bounded AI, not autonomous AI.**
Agents operate within bounded scopes, with explicit tool access, under orchestrator supervision. The system never "just figures it out" in an uncontrolled way. Every LLM call has a defined role, constrained tools, and auditable output.

**6. Progressive intelligence.**
Day 1: basic intent routing and response generation. Month 3: personalized suggestions based on behavioral patterns. Month 6: cross-domain insights ("You tend to overspend when you skip workouts"). The architecture must support this progression without redesign.

### 3.2 Separation of Concerns

```
┌─────────────────────────────────────────────────────────┐
│ What LLMs DO                                            │
├─────────────────────────────────────────────────────────┤
│ • Interpret natural language intent                     │
│ • Reason about ambiguous situations                     │
│ • Plan multi-step workflows                             │
│ • Summarize and consolidate memory                      │
│ • Generate natural language responses                   │
│ • Extract entities from unstructured input              │
│ • Identify patterns across behavioral data              │
│ • Adapt tone and detail level to user preferences       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ What LLMs DO NOT DO                                     │
├─────────────────────────────────────────────────────────┤
│ • Calculate financial returns or balances                │
│ • Mutate database state directly                        │
│ • Make medical decisions                                │
│ • Execute transactions                                  │
│ • Bypass guardrails or access controls                  │
│ • Generate final answers for regulated domains          │
│   without deterministic verification                    │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Architecture Overview

### 4.1 Layered Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        COMMUNICATION LAYER                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ WhatsApp │  │ Telegram │  │ REST API │  │ Future.. │            │
│  │ Adapter  │  │ Adapter  │  │ Adapter  │  │ Adapters │            │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
│       └──────────────┴──────────────┴──────────────┘                 │
│                    Normalized Message Bus                             │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│                      AI KERNEL / CONTROL PLANE                       │
│                                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐              │
│  │   Global    │  │   Domain     │  │   Response     │              │
│  │ Orchestrator│──│   Router     │──│  Synthesizer   │              │
│  └──────┬──────┘  └──────────────┘  └────────────────┘              │
│         │                                                            │
│  ┌──────▼──────┐  ┌──────────────┐  ┌────────────────┐              │
│  │  Workflow   │  │    Agent     │  │   Policy /     │              │
│  │  Engine     │  │   Runtime    │  │  Guardrails    │              │
│  └─────────────┘  └──────────────┘  └────────────────┘              │
│                                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐              │
│  │   Memory    │  │  Retrieval   │  │   Prompt       │              │
│  │  Assembler  │  │ Coordinator  │  │  Registry      │              │
│  └─────────────┘  └──────────────┘  └────────────────┘              │
│                                                                      │
│  ┌─────────────┐  ┌──────────────┐                                   │
│  │    Tool     │  │   Event      │                                   │
│  │  Registry   │  │  Dispatcher  │                                   │
│  └─────────────┘  └──────────────┘                                   │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│                    MEMORY & KNOWLEDGE FABRIC                         │
│                                                                      │
│  ┌────────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ Short-term │ │ Long-term │ │ Semantic │ │Knowledge │ │ Event  │ │
│  │  Memory    │ │ Structured│ │  Memory  │ │  Memory  │ │  Log   │ │
│  └────────────┘ └───────────┘ └──────────┘ └──────────┘ └────────┘ │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│                       DOMAIN PLUGIN LAYER                            │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │  Health  │  │ Finance  │  │  Tutor   │  │ Return-  │            │
│  │  Module  │  │  Module  │  │  Module  │  │  Later   │  . . .    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│                     INFRASTRUCTURE / EXECUTION                       │
│                                                                      │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │
│  │Postgres│ │pgvector│ │ Redis  │ │ Queue  │ │Object  │ │  Auth  │ │
│  │  (SQL) │ │(Vector)│ │(Cache) │ │System  │ │Storage │ │Tenancy │ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Deployment model | Modular monolith | Solo/small team. Clean module boundaries allow future extraction. Avoids premature distributed system complexity. |
| Primary database | PostgreSQL + pgvector | Single database for relational data and vector embeddings. Operational simplicity. pgvector is production-ready for moderate scale. |
| Cache / short-term state | Redis | Session state, rate limiting, pub/sub for lightweight events, job queues. |
| LLM integration | Provider-agnostic abstraction | Wrap OpenAI/Anthropic/etc behind a common interface. Swap models per task. |
| Orchestration | LangGraph (or equivalent) | Graph-based workflow with state machines. Supports conditional branching, human-in-the-loop, retry. |
| Queue / workers | Redis-backed (e.g., arq, Celery) | Background jobs for ingestion, embedding, scheduled tasks. Same Redis instance. |
| API framework | FastAPI | Async-native, good typing, OpenAPI generation, Python ecosystem. |
| Communication | Adapter pattern | Each channel is an adapter implementing a common interface. Business logic never touches channel-specific code. |

### 4.3 Request Flow — High Level

```
1. User sends message via channel (WhatsApp/Telegram/API)
2. Channel adapter normalizes → NormalizedMessage
3. NormalizedMessage → Communication Layer → Internal Event Bus
4. Global Orchestrator receives message_received event
5. Orchestrator assembles context:
   a. Load short-term memory (session state, recent turns)
   b. Route to domain(s) via Domain Router
   c. Retrieve relevant long-term memory
   d. Retrieve relevant knowledge via RAG
6. Orchestrator selects workflow and invokes Domain Orchestrator(s)
7. Domain Orchestrator executes workflow:
   a. Calls domain agents/tools
   b. Calls deterministic services for state mutations
   c. Updates domain state
   d. Emits domain events
8. Results flow back to Global Orchestrator
9. Response Synthesizer generates final response
10. Communication Layer dispatches response via originating channel adapter
11. Events logged for audit trail
```

---

## 5. Communication Layer Design

### 5.1 Design Principles

- **Channel adapters are dumb translators.** They convert channel-specific formats to/from a normalized internal format. Zero business logic.
- **The platform speaks one internal language.** All downstream processing operates on `NormalizedMessage` objects.
- **Multi-channel identity resolution.** The same human may use WhatsApp and Telegram. The system must link them to one platform user.
- **Idempotent processing.** Duplicate webhook deliveries must not cause duplicate processing.
- **Delivery tracking.** The platform tracks whether outbound messages were delivered and read (where the channel supports it).

### 5.2 Channel Adapter Interface

Every channel adapter implements this interface:

```python
from abc import ABC, abstractmethod
from typing import Optional

class ChannelAdapter(ABC):
    """
    Base interface for all communication channel adapters.
    Adapters are stateless translators between channel-specific
    formats and the platform's normalized message format.
    """

    @abstractmethod
    async def handle_webhook(self, raw_payload: dict) -> list[NormalizedInboundEvent]:
        """
        Parse a raw webhook payload from the channel provider
        into one or more normalized inbound events.
        Must be idempotent — same payload yields same events.
        """
        ...

    @abstractmethod
    async def send_message(self, message: OutboundMessage) -> DeliveryResult:
        """
        Send a normalized outbound message through this channel.
        Returns delivery status and channel-specific message ID.
        """
        ...

    @abstractmethod
    async def validate_webhook(self, request: Request) -> bool:
        """
        Validate webhook signature/authenticity for this channel.
        """
        ...

    @abstractmethod
    def get_channel_type(self) -> ChannelType:
        """Return the channel type identifier."""
        ...
```

### 5.3 Normalized Message Schema

```python
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class ChannelType(str, Enum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    REST_API = "rest_api"
    WEB_APP = "web_app"
    EMAIL = "email"
    SLACK = "slack"
    VOICE = "voice"

class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    INTERACTIVE = "interactive"
    SYSTEM = "system"

class NormalizedInboundEvent(BaseModel):
    """
    The universal internal representation of any inbound event
    from any communication channel.
    """
    event_id: UUID = Field(default_factory=uuid4)
    idempotency_key: str          # Channel-derived key for dedup
    channel_type: ChannelType
    channel_account_id: str       # Which of our accounts received this
    channel_user_id: str          # Sender's channel-specific ID
    channel_message_id: str       # Channel's message ID
    conversation_id: Optional[str] = None  # Channel's conversation/chat ID

    content_type: ContentType
    text: Optional[str] = None
    media_url: Optional[str] = None
    media_mime_type: Optional[str] = None
    metadata: dict = Field(default_factory=dict)  # Channel-specific extras

    timestamp: datetime
    received_at: datetime = Field(default_factory=datetime.utcnow)

class OutboundMessage(BaseModel):
    """
    The universal internal representation of a message to send
    to a user through any channel.
    """
    message_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID          # Links to the triggering inbound event or workflow
    channel_type: ChannelType
    channel_account_id: str
    channel_user_id: str
    conversation_id: Optional[str] = None

    content_type: ContentType
    text: Optional[str] = None
    media_url: Optional[str] = None
    interactive_payload: Optional[dict] = None
    metadata: dict = Field(default_factory=dict)

class DeliveryResult(BaseModel):
    success: bool
    channel_message_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    delivered_at: Optional[datetime] = None
```

### 5.4 Core Communication Entities

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│     Channel      │     │ ChannelAccount   │     │ ChannelIdentity  │
│                  │     │                  │     │                  │
│ id               │     │ id               │     │ id               │
│ type (whatsapp,  │◄────│ channel_id       │     │ channel_account_id│
│   telegram, etc) │     │ account_ref      │◄────│ external_user_id │
│ display_name     │     │ credentials_ref  │     │ platform_user_id │
│ config           │     │ tenant_id        │     │ display_name     │
│ active           │     │ active           │     │ metadata         │
└──────────────────┘     └──────────────────┘     │ first_seen_at    │
                                                   │ last_seen_at     │
                                                   └──────────────────┘
                                                          │
                              ┌────────────────────────────┘
                              ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Conversation    │     │    Message       │     │  MessageEvent    │
│                  │     │                  │     │                  │
│ id               │     │ id               │     │ id               │
│ channel_identity_│◄────│ conversation_id  │────►│ message_id       │
│   id             │     │ direction        │     │ event_type       │
│ platform_user_id │     │ content_type     │     │  (sent, delivered│
│ tenant_id        │     │ text             │     │   read, failed)  │
│ started_at       │     │ media_ref        │     │ timestamp        │
│ last_message_at  │     │ channel_msg_id   │     │ metadata         │
│ metadata         │     │ idempotency_key  │     └──────────────────┘
└──────────────────┘     │ correlation_id   │
                         │ tenant_id        │
                         │ created_at       │
                         └──────────────────┘
```

### 5.5 Identity Resolution

A single platform user may interact through multiple channels. The system resolves identity as follows:

1. **First contact**: Inbound message arrives from unknown `channel_user_id`. System creates a `ChannelIdentity` record and a new `platform_user` (or prompts linking).
2. **Linking**: User can link identities by confirming from another channel or via an API call. This creates a mapping: multiple `ChannelIdentity` records → one `platform_user_id`.
3. **Resolution at ingress**: When a message arrives, the communication layer looks up `ChannelIdentity` by `(channel_account_id, external_user_id)` to find the `platform_user_id`.
4. **Cross-channel responses**: The platform can proactively reach the user on any linked channel (e.g., send a reminder via Telegram even if the original conversation was on WhatsApp).

### 5.6 Conversation Management

- **Conversations are per-channel, per-user.** A WhatsApp conversation and a Telegram conversation are separate even for the same user.
- **Sessions** are a kernel concept layered on top. A session spans one or more messages within a time window and tracks the active workflow/context.
- **Conversation history** is raw communication data — never modified, append-only.
- **Session state** is working memory — mutable, short-lived, used by the orchestrator.

### 5.7 Idempotency and Deduplication

- Every inbound message gets an `idempotency_key` derived from channel-specific identifiers (e.g., WhatsApp message ID + timestamp).
- Before processing, the system checks if the `idempotency_key` exists in the `messages` table.
- If it exists, the webhook handler returns a success response without re-processing.
- Redis is used as a fast-path dedup cache with a 24-hour TTL; Postgres is the durable dedup source.

### 5.8 Outbound Dispatch

```
OutboundMessage
      │
      ▼
┌─────────────┐     ┌─────────────┐
│  Dispatch   │────►│  Channel    │──── Channel Provider API
│  Router     │     │  Adapter    │
└─────────────┘     └─────────────┘
      │                    │
      │                    ▼
      │             DeliveryResult
      │                    │
      ▼                    ▼
 Store in DB        Update MessageEvent
```

- The dispatch router selects the correct adapter based on `channel_type`.
- Adapters handle retries with exponential backoff (3 attempts, 1s/5s/30s).
- Failed deliveries emit a `message_delivery_failed` event for alerting and potential fallback to another channel.
- All outbound messages carry a `correlation_id` linking them to the triggering inbound event or scheduled job.

---

## 6. AI-Native Kernel Design

### 6.1 Kernel Overview

The AI kernel is the central nervous system of AI Life OS. It is **not** an LLM wrapper — it is a structured control plane that uses LLMs as reasoning components within a deterministic orchestration framework.

```
┌────────────────────────────────────────────────────────────────┐
│                        AI KERNEL                               │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 GLOBAL ORCHESTRATOR                       │  │
│  │                                                          │  │
│  │  1. Receive normalized event                             │  │
│  │  2. Load session state (short-term memory)               │  │
│  │  3. Classify intent                                      │  │
│  │  4. Route to domain(s)                                   │  │
│  │  5. Assemble memory context                              │  │
│  │  6. Execute workflow via domain orchestrator              │  │
│  │  7. Synthesize response                                  │  │
│  │  8. Dispatch response                                    │  │
│  │  9. Emit events                                          │  │
│  │  10. Update session state                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│  │  Domain    │ │  Memory    │ │ Retrieval  │ │  Prompt    │  │
│  │  Router    │ │ Assembler  │ │Coordinator │ │  Registry  │  │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘  │
│                                                                │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│  │  Workflow  │ │   Agent    │ │   Tool     │ │  Policy /  │  │
│  │  Engine    │ │  Runtime   │ │  Registry  │ │ Guardrails │  │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘  │
│                                                                │
│  ┌────────────┐ ┌────────────┐                                 │
│  │  Response  │ │   Event    │                                 │
│  │Synthesizer │ │ Dispatcher │                                 │
│  └────────────┘ └────────────┘                                 │
└────────────────────────────────────────────────────────────────┘
```

### 6.2 Global Orchestrator

The global orchestrator is the entry point for all user interactions and scheduled triggers. It is implemented as a **state machine graph** (LangGraph or equivalent).

**Responsibilities:**

1. **Intent classification**: Determine what the user wants. This uses an LLM call with the user's message, recent session context, and the list of registered domain capabilities.
2. **Domain routing**: Based on classified intent, select one or more relevant domain orchestrators. Supports multi-domain messages (e.g., "Log my lunch and remind me to study Dutch at 3pm" → Health + Tutor).
3. **Memory assembly**: Coordinate with the Memory Assembler to build the context window: session state, relevant facts, relevant semantic memories, relevant knowledge chunks.
4. **Workflow selection**: Each domain intent maps to a workflow. The orchestrator selects and initiates it.
5. **Cross-domain coordination**: When multiple domains are involved, the orchestrator sequences or parallelizes their execution and merges results.
6. **Response synthesis**: Takes structured results from domain orchestrators and generates a natural language response using the Response Synthesizer.
7. **Event emission**: Emits audit events for the entire processing pipeline.

**State Machine:**

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   LOAD      │ Load session, user profile
                    │   CONTEXT   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  CLASSIFY   │ Intent + domain routing
                    │   INTENT    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  ASSEMBLE   │ Memory + RAG retrieval
                    │   MEMORY    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  EXECUTE    │ Domain orchestrator(s)
                    │  WORKFLOW   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ SYNTHESIZE  │ Generate response
                    │  RESPONSE   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   EMIT      │ Events + audit + state update
                    │  EVENTS     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    END      │
                    └─────────────┘
```

### 6.3 Domain Router

The domain router maintains a registry of all installed domain plugins and their capabilities.

```python
class DomainCapability(BaseModel):
    domain_id: str                    # e.g., "health", "finance"
    intent_patterns: list[str]        # Description of intents this domain handles
    keywords: list[str]               # Trigger keywords
    example_messages: list[str]       # Few-shot examples for the classifier
    priority: int = 0                 # Higher = checked first on ambiguity
    can_coexist: list[str] = []       # Domains it can run alongside

class DomainRoutingResult(BaseModel):
    primary_domain: str
    secondary_domains: list[str] = []
    confidence: float
    raw_intent: str
    classified_intent: str
```

Routing uses a two-phase approach:
1. **Fast path**: Keyword/pattern matching for obvious intents (e.g., message contains a URL → return-later domain).
2. **LLM path**: For ambiguous messages, an LLM classifies the intent against registered domain capabilities using few-shot examples.

### 6.4 Memory Assembler

The Memory Assembler builds the context packet for each request. It is a critical component that determines what information the LLM sees.

```python
class MemoryPacket(BaseModel):
    """
    The assembled context for a single request.
    Passed to domain orchestrators and the response synthesizer.
    """
    session_state: SessionState               # Current session/workflow state
    recent_turns: list[ConversationTurn]       # Last N turns
    user_profile: UserProfile                  # Core profile facts
    relevant_facts: list[MemoryFact]           # From long-term structured memory
    semantic_memories: list[SemanticMemory]    # From semantic memory
    knowledge_chunks: list[KnowledgeChunk]     # From RAG retrieval
    domain_context: dict[str, Any]             # Domain-specific assembled context
    active_tasks: list[Task]                   # Currently active tasks
    active_goals: list[Goal]                   # Currently active goals

    def to_prompt_context(self) -> str:
        """Serialize into a string for prompt injection."""
        ...

    def token_budget(self) -> int:
        """Estimate token count for budget management."""
        ...
```

The assembler follows a **budget-aware** strategy:
1. Always include: session state, recent turns, user profile (high priority).
2. Include if relevant: domain-specific facts, retrieved knowledge (medium priority).
3. Include if budget allows: semantic memories, cross-domain patterns (lower priority).
4. Apply token budgeting to stay within model context limits.

### 6.5 Prompt Registry

All prompts are versioned and stored in a registry, never hardcoded in business logic.

```python
class PromptTemplate(BaseModel):
    prompt_id: str                    # e.g., "health.meal_parser.v2"
    domain: Optional[str]            # None for kernel-level prompts
    version: int
    template: str                    # Jinja2 or f-string template
    input_variables: list[str]
    model_preference: Optional[str]  # e.g., "gpt-4o-mini" for cheap tasks
    max_tokens: Optional[int]
    temperature: Optional[float]
    active: bool = True
```

Benefits:
- **A/B testing**: Run two prompt versions side by side.
- **Audit trail**: Know exactly which prompt produced which output.
- **Model routing**: Different prompts can prefer different models (cheap model for classification, expensive model for synthesis).

### 6.6 Tool Registry

Tools are functions that agents can invoke. They are registered centrally and scoped by domain.

```python
class ToolDefinition(BaseModel):
    tool_id: str                     # e.g., "health.log_meal"
    domain: Optional[str]            # None for shared tools
    name: str
    description: str                 # For the LLM's tool-use understanding
    parameters_schema: dict          # JSON Schema for inputs
    requires_confirmation: bool      # Should the user confirm before execution?
    is_deterministic: bool           # True = no LLM involved in execution
    handler: str                     # Dotted path to handler function
    permissions: list[str] = []      # Required permissions
```

### 6.7 Policy and Guardrail Layer

The policy layer enforces safety constraints before and after LLM calls.

**Pre-execution policies:**
- Input sanitization (PII detection, injection prevention)
- Rate limiting per user and per domain
- Content filtering for harmful requests
- Domain-specific safety boundaries (e.g., health module cannot prescribe medication)

**Post-execution policies:**
- Output validation against expected schemas
- Hallucination detection heuristics (e.g., referencing nonexistent user data)
- Confidence thresholds — below threshold, ask for clarification instead of guessing
- Financial/health disclaimers injection where required

```python
class PolicyResult(BaseModel):
    allowed: bool
    modified_input: Optional[str] = None   # If input was sanitized
    modified_output: Optional[str] = None  # If output was amended
    warnings: list[str] = []
    blocked_reason: Optional[str] = None
```

### 6.8 Response Synthesizer

The Response Synthesizer generates the final user-facing message from structured domain results.

**Responsibilities:**
- Convert structured results into natural language
- Apply user's preferred tone and verbosity level
- Merge results from multiple domains into a coherent response
- Format for the target channel (e.g., WhatsApp supports limited markdown)
- Append disclaimers or follow-up suggestions where appropriate

```python
class SynthesisInput(BaseModel):
    user_profile: UserProfile
    channel_type: ChannelType
    domain_results: list[DomainResult]
    memory_packet: MemoryPacket
    response_guidelines: Optional[str] = None  # e.g., "keep it brief"

class SynthesisOutput(BaseModel):
    text: str
    suggested_actions: list[str] = []     # Quick reply suggestions
    follow_up_scheduled: bool = False
    metadata: dict = {}
```

---

## 7. Memory Architecture

### 7.1 Memory Layer Overview

AI Life OS uses a **five-layer memory architecture** where each layer has a distinct purpose, storage mechanism, write policy, and retrieval strategy.

```
┌────────────────────────────────────────────────────────────────┐
│                    MEMORY FABRIC                               │
│                                                                │
│  Layer 1: SHORT-TERM MEMORY                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Session state, active workflow, recent turns, pending    │  │
│  │ clarifications, temporary assumptions                    │  │
│  │ Storage: Redis   TTL: minutes to hours                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  Layer 2: LONG-TERM STRUCTURED MEMORY                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Profile, preferences, goals, tasks, plans, logs,         │  │
│  │ transactions, metrics, study progress, settings          │  │
│  │ Storage: Postgres   Retention: permanent                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  Layer 3: LONG-TERM SEMANTIC MEMORY                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Conversation summaries, behavioral patterns, learned     │  │
│  │ preferences, cross-domain insights, repeated blockers    │  │
│  │ Storage: Postgres + pgvector   Retention: permanent      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  Layer 4: KNOWLEDGE MEMORY                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Links, articles, PDFs, notes, uploaded files, extracted  │  │
│  │ summaries, chunked content, embeddings, topic graph      │  │
│  │ Storage: Postgres + pgvector + Object Storage            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  Layer 5: EVENT / LIFE LOG MEMORY                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Every meaningful action: meal logged, workout skipped,   │  │
│  │ transaction imported, article saved, mood logged, etc.   │  │
│  │ Storage: Postgres (append-only)   Retention: permanent   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 7.2 Layer 1: Short-Term Memory

**Purpose**: Working memory for the current interaction session.

**Contents:**
- Current session ID and state
- Active workflow step and intermediate results
- Last N conversation turns (typically 10-20)
- Pending clarifications the system is waiting for
- Temporary assumptions (e.g., "user probably means dinner, not lunch")
- Domain-specific transient state (e.g., partially constructed meal log)

**Storage**: Redis with structured keys.

```
Key pattern: stm:{tenant_id}:{user_id}:{session_id}
TTL: 2 hours (configurable per domain)
```

**Data structure:**

```python
class SessionState(BaseModel):
    session_id: UUID
    user_id: UUID
    tenant_id: UUID
    channel_type: ChannelType
    conversation_id: UUID
    started_at: datetime
    last_activity_at: datetime

    active_domain: Optional[str] = None
    active_workflow_id: Optional[str] = None
    active_workflow_state: Optional[dict] = None

    recent_turns: list[ConversationTurn] = []
    pending_clarification: Optional[str] = None
    temporary_context: dict = Field(default_factory=dict)
```

**Write policy**: Updated on every interaction. Overwritten, not appended.

**Eviction**: TTL-based. On expiry, the session is summarized and stored in semantic memory (Layer 3) if it contained meaningful content.

### 7.3 Layer 2: Long-Term Structured Memory

**Purpose**: Source-of-truth for all structured, factual data about the user and their domains.

**Contents:**

| Category | Examples |
|----------|----------|
| Profile | Name, timezone, language, communication preferences |
| Preferences | Dietary restrictions, risk tolerance, study goals |
| Goals | Lose 5kg by June, save €500/month, reach B2 Dutch |
| Tasks | Pending actions with due dates and statuses |
| Plans | Multi-step plans generated by the system |
| Domain entities | Meals, workouts, transactions, study sessions, captured links |
| Settings | Notification preferences, active domains, connected accounts |
| Relationships | Connections between entities (meal → ingredients, transaction → category) |

**Storage**: PostgreSQL relational tables with proper schemas, indexes, and foreign keys.

**Write policy**: Written by deterministic services only. LLMs propose writes; deterministic code validates and executes them.

**Retention**: Permanent. Soft-delete with `deleted_at` timestamp for recovery.

**Retrieval**: SQL queries via domain services. Also exposed to the Memory Assembler for context building.

### 7.4 Layer 3: Long-Term Semantic Memory

**Purpose**: Emergent understanding that the AI builds over time — patterns, preferences, and insights that are not explicitly stated but inferred from behavior.

**Contents:**

| Type | Examples |
|------|----------|
| Conversation summaries | "On March 15, user discussed frustration with Dutch grammar. Resolved by switching to pattern-based learning." |
| Learned preferences | "User prefers concise responses in the morning, more detailed in the evening." |
| Behavioral patterns | "User consistently skips workouts on Mondays." |
| Cross-domain insights | "User's spending increases when they report low mood." |
| Successful interventions | "Gentle reminders at 8am have 70% follow-through; 6pm reminders are ignored." |
| Repeated blockers | "User frequently postpones meal logging when busy at work." |

**Storage**: PostgreSQL table with text content + pgvector embeddings for semantic search.

```python
class SemanticMemory(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    memory_type: str                  # "summary", "pattern", "insight", "preference"
    content: str                      # Natural language description
    embedding: list[float]            # Vector embedding
    source_domain: Optional[str]      # Domain that originated this, or None for cross-domain
    related_domains: list[str] = []   # Domains this is relevant to
    confidence: float = 1.0           # How confident the system is
    importance: float = 0.5           # 0-1 importance score
    access_count: int = 0             # How often this has been retrieved
    last_accessed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    superseded_by: Optional[UUID] = None  # If this memory was refined/replaced
```

**Write policy**: Written by background consolidation jobs, not in the hot path. After a session ends or on a schedule, the system:
1. Summarizes recent interactions.
2. Extracts new patterns or preference signals.
3. Checks for contradictions with existing memories.
4. Creates new memories or updates existing ones (sets `superseded_by`).

**Consolidation strategy**:
- **Session-end**: Summarize the session if it had >3 turns or meaningful content.
- **Daily**: Scan day's events for behavioral patterns.
- **Weekly**: Cross-domain pattern analysis.
- **On-demand**: When a domain requests pattern analysis for a specific topic.

**Retrieval**: Semantic search via embeddings + metadata filters (domain, type, recency).

### 7.5 Layer 4: Knowledge Memory

**Purpose**: External knowledge ingested by the user — links, documents, articles, notes. This is the user's "second brain."

**Contents:**

| Type | Examples |
|------|----------|
| Web links | Articles, blog posts, research papers |
| Documents | PDFs, uploaded files |
| Notes | Free-text notes and snippets |
| Extracted content | Parsed text, summaries, key points |
| Chunks | Overlapping text chunks for RAG retrieval |
| Embeddings | Vector representations of chunks |
| Entity/topic graph | Entities and relationships extracted from knowledge |

**Storage**:
- **Metadata**: PostgreSQL (`knowledge_documents` table)
- **Raw content**: Object storage (S3/MinIO)
- **Chunks + embeddings**: PostgreSQL + pgvector (`knowledge_chunks` table)
- **Entity graph**: PostgreSQL (`knowledge_relations` table) — not a full graph DB in MVP; upgrade path to Neo4j if needed

**Write policy**: Async pipeline. Content is ingested, queued, and processed in background workers. See Section 14 (Knowledge Ingestion) for the full pipeline.

**Retention**: Permanent unless user explicitly deletes. Raw content in object storage can have lifecycle policies for cost management.

**Retrieval**: Hybrid (semantic + keyword + metadata) via the shared retrieval layer.

### 7.6 Layer 5: Event / Life Log Memory

**Purpose**: An immutable, append-only log of every meaningful action and state change. This is the behavioral record that powers personalization, pattern detection, and auditability.

**Contents:**

```python
class LifeLogEvent(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    event_type: str            # e.g., "meal_logged", "workout_skipped"
    domain: str                # e.g., "health", "finance"
    payload: dict              # Event-specific data
    source: str                # "user", "system", "connector"
    channel: Optional[str]     # Channel the event originated from
    correlation_id: Optional[UUID]  # Links to triggering interaction
    importance: float = 0.5    # For retrieval ranking
    created_at: datetime
```

**Examples:**
- `meal_logged` → `{meal_type: "lunch", items: [...], calories: 650}`
- `workout_skipped` → `{planned_workout: "running", reason: "felt tired"}`
- `transaction_imported` → `{amount: -45.50, currency: "EUR", category: "dining"}`
- `link_captured` → `{url: "...", title: "...", source_channel: "whatsapp"}`
- `mood_logged` → `{mood: "stressed", energy: 3, notes: "deadline pressure"}`
- `topic_mastered` → `{topic: "dutch_past_tense", domain: "tutor", confidence: 0.85}`

**Storage**: PostgreSQL append-only table, partitioned by month for performance.

**Write policy**: Events are immutable once written. Never updated or deleted (logical deletion via separate `event_corrections` table if needed).

**Retention**: Permanent. Older partitions can be moved to cold storage.

**Retrieval**: Time-range queries, domain filters, event-type filters. Also feeds into semantic memory consolidation.

### 7.7 Memory Interaction Patterns

```
Interaction Flow:
                         ┌─────────────────┐
                         │   User Message   │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │  Short-term Mem  │ Read session state
                         │    (Layer 1)     │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │  Memory Assembler│ Query Layers 2-5
                         └────────┬─────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
            ┌──────────┐  ┌──────────┐  ┌──────────┐
            │  Facts   │  │ Semantic │  │Knowledge │
            │(Layer 2) │  │(Layer 3) │  │(Layer 4) │
            └──────────┘  └──────────┘  └──────────┘
                    │             │             │
                    └─────────────┼─────────────┘
                                  ▼
                         ┌────────────────┐
                         │MemoryPacket    │ → Orchestrator
                         └────────────────┘
                                  │
                         ┌────────▼────────┐
                         │  Process &      │
                         │  Generate       │
                         └────────┬────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
            ┌──────────┐  ┌──────────┐  ┌──────────┐
            │Update STM│  │Write to  │  │Emit to   │
            │(Layer 1) │  │Structured│  │Event Log │
            └──────────┘  │(Layer 2) │  │(Layer 5) │
                          └──────────┘  └──────────┘
                                  │
                          ┌───────▼───────┐
                          │ Background:   │
                          │ Consolidate   │ → Semantic Memory (Layer 3)
                          │ to Semantic   │
                          └───────────────┘
```

### 7.8 Cross-Domain Memory Access

All memory layers are **shared** but **scoped**. Any domain can read memory from any other domain through the Memory Assembler, but the assembler applies scoping rules:

1. **Same-domain data**: Always accessible.
2. **Cross-domain structured data**: Accessible via explicit cross-domain queries (the requesting domain must declare `cross_domain_reads` in its manifest).
3. **Semantic memory**: Always accessible — semantic memories are intentionally cross-domain.
4. **Knowledge memory**: Always accessible — knowledge is user-owned, not domain-owned.
5. **Event log**: Readable by any domain for pattern analysis.

This enables the key use case: the health module can access mood data, the finance module can correlate spending with behavioral patterns, and the tutor module can adapt based on energy levels — all without these domains being coupled.

---

## 8. RAG and Retrieval Architecture

### 8.1 Retrieval Layer Overview

The retrieval layer is a shared service that all domains use to find relevant context. It supports multiple retrieval strategies and combines them using a configurable fusion approach.

```
┌────────────────────────────────────────────────────────────────┐
│                    RETRIEVAL COORDINATOR                       │
│                                                                │
│  ┌──────────────┐                                              │
│  │ RetrievalReq │                                              │
│  └──────┬───────┘                                              │
│         │                                                      │
│         ▼                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Structured  │    │   Semantic   │    │   Keyword    │      │
│  │  Retriever   │    │  Retriever   │    │  Retriever   │      │
│  │  (SQL)       │    │  (pgvector)  │    │ (tsvector)   │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                   │                   │              │
│         └───────────────────┼───────────────────┘              │
│                             ▼                                  │
│                    ┌────────────────┐                           │
│                    │    Fusion &    │                           │
│                    │   Reranking    │                           │
│                    └────────┬───────┘                           │
│                             │                                  │
│                    ┌────────▼────────┐                          │
│                    │ Memory Packet   │                          │
│                    │   Assembly      │                          │
│                    └─────────────────┘                          │
└────────────────────────────────────────────────────────────────┘
```

### 8.2 Retrieval Strategies

| Strategy | Source | Method | Use Case |
|----------|--------|--------|----------|
| **Structured** | PostgreSQL tables | SQL queries with filters | "What did I eat yesterday?" — direct fact lookup |
| **Semantic** | pgvector embeddings | Cosine similarity search | "What do I know about intermittent fasting?" — fuzzy knowledge retrieval |
| **Keyword** | PostgreSQL tsvector | Full-text search | "Find my notes about React hooks" — keyword-specific search |
| **Hybrid** | Combined | Reciprocal Rank Fusion (RRF) | Most queries — combines semantic understanding with keyword precision |
| **Domain-filtered** | Any source + domain tag | Filter by domain metadata | "What are my health goals?" — scoped to health domain |
| **Recency-aware** | Any source + timestamp | Time-decayed scoring | "What have I been studying recently?" — recent items ranked higher |
| **Importance-aware** | Any source + importance score | Importance-weighted ranking | Prioritize high-importance memories over low-importance ones |
| **Relationship-aware** | Knowledge relations | Graph traversal | "What's related to this article?" — follow entity/topic links |

### 8.3 Retrieval Request Model

```python
class RetrievalRequest(BaseModel):
    tenant_id: UUID
    user_id: UUID
    query: str                                # Natural language query
    query_embedding: Optional[list[float]]    # Pre-computed (or computed by coordinator)

    # Filtering
    domains: Optional[list[str]] = None       # Filter to specific domains
    memory_layers: list[str] = ["all"]        # Which layers to search
    event_types: Optional[list[str]] = None   # Filter event log by type
    time_range: Optional[TimeRange] = None    # Recency filter
    content_types: Optional[list[str]] = None # Filter knowledge by type

    # Strategy
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    max_results: int = 20
    min_relevance_score: float = 0.3

    # Ranking modifiers
    recency_weight: float = 0.3               # 0-1, how much to favor recent items
    importance_weight: float = 0.2            # 0-1, how much to favor important items
    diversity_factor: float = 0.1             # 0-1, penalize too-similar results

class RetrievalStrategy(str, Enum):
    STRUCTURED = "structured"
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"

class TimeRange(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None
```

### 8.4 Retrieval Result Model

```python
class RetrievalResult(BaseModel):
    items: list[RetrievedItem]
    total_found: int
    strategy_used: RetrievalStrategy
    retrieval_time_ms: float

class RetrievedItem(BaseModel):
    source_layer: str                # "structured", "semantic", "knowledge", "event_log"
    source_id: UUID                  # ID in the source table
    content: str                     # The actual text content
    content_type: str                # "fact", "summary", "chunk", "event"
    domain: Optional[str]
    relevance_score: float           # 0-1 combined score
    semantic_score: Optional[float]  # Raw semantic similarity
    keyword_score: Optional[float]   # Raw keyword match score
    recency_score: Optional[float]   # Time-decay score
    importance: float
    metadata: dict                   # Source-specific metadata
    created_at: datetime
```

### 8.5 Embeddings Strategy

**Model**: `text-embedding-3-small` (OpenAI) for MVP — good quality/cost ratio. Abstracted behind an interface for future model swaps.

**What gets embedded:**
1. Knowledge chunks (articles, documents, notes)
2. Semantic memories (summaries, patterns, insights)
3. Memory facts (key profile facts and preferences)
4. Event descriptions (human-readable event summaries)

**What does NOT get embedded:**
- Raw conversation messages (too noisy; summaries are embedded instead)
- Structured numerical data (searched via SQL)
- Binary files (only their extracted text is embedded)

**Embedding interface:**

```python
class EmbeddingService:
    async def embed_text(self, text: str) -> list[float]:
        ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        ...

    def get_dimension(self) -> int:
        ...
```

### 8.6 Chunking Strategy

For knowledge documents, content is chunked before embedding:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Chunk size | 512 tokens | Good balance of context and specificity |
| Overlap | 64 tokens | Prevent information loss at boundaries |
| Splitter | Recursive character splitter | Respects paragraph/sentence boundaries |
| Metadata per chunk | document_id, chunk_index, title, domain_tags, created_at | Enables filtered retrieval |

For very short content (tweets, brief notes): embed as-is, no chunking.
For very long content (books, long PDFs): chapter-level splitting first, then chunk within chapters.

### 8.7 Metadata Tagging

Every embedded item carries metadata that enables filtered search:

```python
class ChunkMetadata(BaseModel):
    document_id: UUID
    chunk_index: int
    tenant_id: UUID
    user_id: UUID
    domain_tags: list[str]          # ["health", "nutrition"]
    content_type: str               # "article", "pdf", "note", etc.
    source_url: Optional[str]
    title: Optional[str]
    author: Optional[str]
    language: Optional[str]
    created_at: datetime
    importance: float = 0.5
    topics: list[str] = []          # Extracted topics
    entities: list[str] = []        # Extracted named entities
```

### 8.8 Reranking

After initial retrieval, results are reranked using a multi-signal approach:

```
Final Score = (w_semantic × semantic_score)
            + (w_keyword × keyword_score)
            + (w_recency × recency_score)
            + (w_importance × importance_score)
            - (w_diversity × similarity_to_already_selected)
```

Default weights (tunable per query):
- `w_semantic` = 0.4
- `w_keyword` = 0.2
- `w_recency` = 0.2
- `w_importance` = 0.15
- `w_diversity` = 0.05

**Recency scoring function:**
```python
def recency_score(created_at: datetime, half_life_days: float = 30.0) -> float:
    age_days = (datetime.utcnow() - created_at).total_seconds() / 86400
    return math.exp(-0.693 * age_days / half_life_days)
```

**Future enhancement**: Use a cross-encoder reranker (e.g., Cohere Rerank or a local model) for the top-K results. This is more accurate but adds latency, so it's a Phase 4+ optimization.

### 8.9 Memory Packet Assembly

The final step of retrieval is assembling the `MemoryPacket` that gets passed to the orchestrator. The assembly process:

1. **Structured query**: Fetch user profile, active goals, active tasks, and domain-specific entities based on the classified intent.
2. **Semantic search**: Embed the user's query, search semantic memory and knowledge memory.
3. **Event log scan**: Fetch recent relevant events (last 7 days, filtered by domain).
4. **Fusion and reranking**: Combine all results, rerank, and deduplicate.
5. **Token budgeting**: Trim results to fit within the token budget (model context - system prompt - output reserve).
6. **Packet construction**: Build the `MemoryPacket` with all assembled context.

```python
class MemoryPacketAssembler:
    async def assemble(
        self,
        tenant_id: UUID,
        user_id: UUID,
        query: str,
        classified_intent: str,
        target_domains: list[str],
        token_budget: int = 8000,
    ) -> MemoryPacket:
        # 1. Always load (high priority, fixed budget)
        session = await self.short_term_memory.get_session(tenant_id, user_id)
        profile = await self.structured_memory.get_profile(tenant_id, user_id)
        recent_turns = session.recent_turns[-10:]

        # 2. Domain-specific structured data
        domain_context = {}
        for domain in target_domains:
            domain_context[domain] = await self.structured_memory.get_domain_context(
                tenant_id, user_id, domain, classified_intent
            )

        # 3. Retrieval (budget-aware)
        remaining_budget = token_budget - estimate_tokens(session, profile, recent_turns, domain_context)

        retrieval_result = await self.retrieval_coordinator.retrieve(
            RetrievalRequest(
                tenant_id=tenant_id,
                user_id=user_id,
                query=query,
                domains=target_domains,
                max_results=15,
                strategy=RetrievalStrategy.HYBRID,
            )
        )

        # 4. Budget-fit the retrieval results
        fitted_items = self._fit_to_budget(retrieval_result.items, remaining_budget)

        # 5. Assemble
        return MemoryPacket(
            session_state=session,
            recent_turns=recent_turns,
            user_profile=profile,
            relevant_facts=[i for i in fitted_items if i.source_layer == "structured"],
            semantic_memories=[i for i in fitted_items if i.source_layer == "semantic"],
            knowledge_chunks=[i for i in fitted_items if i.source_layer == "knowledge"],
            domain_context=domain_context,
            active_tasks=await self.structured_memory.get_active_tasks(tenant_id, user_id),
            active_goals=await self.structured_memory.get_active_goals(tenant_id, user_id),
        )
```

---

## 9. Workflow and Orchestration Architecture

### 9.1 Hierarchical Orchestration Model

AI Life OS uses a **three-tier hierarchical orchestration model** to avoid uncontrolled agent behavior while maintaining flexibility.

```
┌─────────────────────────────────────────────────────────────┐
│                  TIER 1: GLOBAL ORCHESTRATOR                │
│                                                             │
│  • Entry point for all interactions and triggers            │
│  • Intent classification and domain routing                 │
│  • Memory assembly and context building                     │
│  • Cross-domain coordination                                │
│  • Response synthesis                                       │
│  • Implemented as a LangGraph state machine                 │
└────────────────────────┬────────────────────────────────────┘
                         │ delegates to
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌────────────────┐┌────────────────┐┌────────────────┐
│ TIER 2: DOMAIN ││ TIER 2: DOMAIN ││ TIER 2: DOMAIN │
│  ORCHESTRATOR  ││  ORCHESTRATOR  ││  ORCHESTRATOR  │
│   (Health)     ││  (Finance)     ││   (Tutor)      │
│                ││                ││                │
│ • Domain-      ││ • Domain-      ││ • Domain-      │
│   specific     ││   specific     ││   specific     │
│   workflows    ││   workflows    ││   workflows    │
│ • Domain       ││ • Domain       ││ • Domain       │
│   agents       ││   agents       ││   agents       │
│ • Domain       ││ • Domain       ││ • Domain       │
│   state mgmt   ││   state mgmt   ││   state mgmt   │
└───────┬────────┘└───────┬────────┘└───────┬────────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌────────────────────────────────────────────────────┐
│            TIER 3: WORKER AGENTS / TOOLS           │
│                                                    │
│  meal_parser  │  transaction_classifier  │  quiz   │
│  grocery_rec  │  budget_calculator       │  gen    │
│  symptom_sum  │  portfolio_analyzer      │  sr_    │
│  workout_plan │  expense_categorizer     │  plan   │
└────────────────────────────────────────────────────┘
```

### 9.2 Why Not Agent Swarms

| Agent Swarm Problem | Our Solution |
|---------------------|--------------|
| Unpredictable execution paths | State machine graphs with defined transitions |
| Unbounded tool access | Scoped tool registries per agent |
| No cost control | Token budgets per workflow step |
| Hard to debug | Full trace logging at every node |
| Emergent failures | Explicit error handling at each tier |
| Hallucination cascades | Deterministic services for state mutations |

### 9.3 Workflow Engine

Workflows are the primary execution unit. Every intent maps to a workflow.

```python
class WorkflowDefinition(BaseModel):
    workflow_id: str                      # e.g., "health.log_meal"
    domain: str
    name: str
    description: str
    trigger_intents: list[str]            # Intents that activate this workflow
    steps: list[WorkflowStep]
    timeout_seconds: int = 300
    max_retries: int = 2
    requires_confirmation: bool = False   # Ask user before executing?

class WorkflowStep(BaseModel):
    step_id: str
    step_type: StepType                   # "llm_call", "tool_call", "deterministic", "branch", "human_input"
    agent_or_tool_id: Optional[str]       # Which agent/tool to invoke
    input_mapping: dict                   # How to map workflow state → step input
    output_mapping: dict                  # How to map step output → workflow state
    next_step: Optional[str]              # Next step ID (or None for end)
    branch_conditions: Optional[dict]     # For "branch" type steps
    error_handler: Optional[str]          # Step to jump to on error
    timeout_seconds: Optional[int]

class StepType(str, Enum):
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    DETERMINISTIC = "deterministic"
    BRANCH = "branch"
    HUMAN_INPUT = "human_input"
    PARALLEL = "parallel"
    SUB_WORKFLOW = "sub_workflow"
```

### 9.4 Workflow Runtime

```python
class WorkflowRun(BaseModel):
    run_id: UUID
    workflow_id: str
    tenant_id: UUID
    user_id: UUID
    status: WorkflowStatus                # pending, running, waiting_input, completed, failed
    current_step: Optional[str]
    state: dict                           # Accumulated workflow state
    input_data: dict
    output_data: Optional[dict]
    started_at: datetime
    completed_at: Optional[datetime]
    steps_executed: list[StepExecution]
    error: Optional[str]
    correlation_id: UUID                  # Links to triggering event

class StepExecution(BaseModel):
    step_id: str
    status: str
    input_data: dict
    output_data: Optional[dict]
    started_at: datetime
    completed_at: Optional[datetime]
    tokens_used: Optional[int]
    model_used: Optional[str]
    error: Optional[str]
```

### 9.5 Workflow Example: Log Meal

```
Workflow: health.log_meal

Step 1: parse_meal (LLM_CALL)
  Agent: health.meal_parser
  Input: user message text + memory context
  Output: structured MealData {items, quantities, meal_type}

Step 2: validate_meal (DETERMINISTIC)
  Tool: health.meal_validator
  Input: MealData from step 1
  Output: validated MealData with normalized units

Step 3: estimate_nutrition (TOOL_CALL)
  Tool: health.nutrition_calculator
  Input: validated MealData
  Output: NutritionEstimate {calories, protein, carbs, fat}

Step 4: check_goals (DETERMINISTIC)
  Tool: health.goal_checker
  Input: NutritionEstimate + user's daily goals
  Output: GoalProgress {on_track, warnings, remaining}

Step 5: store_meal (DETERMINISTIC)
  Tool: health.meal_store
  Input: MealData + NutritionEstimate
  Output: stored meal ID
  Side effect: emit meal_logged event

Step 6: generate_response (LLM_CALL)
  Agent: response_synthesizer
  Input: MealData + NutritionEstimate + GoalProgress
  Output: natural language response to user
```

### 9.6 Cross-Domain Workflows

When a message involves multiple domains, the global orchestrator coordinates:

```
User: "Log my lunch: chicken salad. Also, I spent €15 on it. Remind me to study Dutch at 3pm."

Global Orchestrator detects 3 intents:
  1. health.log_meal → Health Domain Orchestrator
  2. finance.log_expense → Finance Domain Orchestrator
  3. tutor.set_reminder → Tutor Domain Orchestrator (via Scheduler)

Execution:
  - Health and Finance run in PARALLEL (independent)
  - Tutor reminder is scheduled (async, immediate response)
  - Results merged by Response Synthesizer

Response: "Logged your chicken salad lunch (450 cal, 35g protein — 
you're on track for today). €15 expense recorded under 'dining out'. 
I'll remind you to study Dutch at 3pm."
```

---

## 10. Domain Plugin Architecture

### 10.1 Plugin Contract

Every domain module is a plugin that implements a standard contract. This ensures the kernel never needs to know domain-specific details.

```python
class DomainPlugin(ABC):
    """
    Base contract that every domain module must implement.
    The kernel discovers and loads plugins through this interface.
    """

    @abstractmethod
    def get_manifest(self) -> DomainManifest:
        """Return the plugin's manifest describing its capabilities."""
        ...

    @abstractmethod
    def get_orchestrator(self) -> DomainOrchestrator:
        """Return the domain's orchestrator instance."""
        ...

    @abstractmethod
    def get_workflows(self) -> list[WorkflowDefinition]:
        """Return all workflow definitions for this domain."""
        ...

    @abstractmethod
    def get_tools(self) -> list[ToolDefinition]:
        """Return all tool definitions for this domain."""
        ...

    @abstractmethod
    def get_prompts(self) -> list[PromptTemplate]:
        """Return all prompt templates for this domain."""
        ...

    @abstractmethod
    def get_scheduled_jobs(self) -> list[ScheduledJobDefinition]:
        """Return all scheduled job definitions."""
        ...

    @abstractmethod
    async def on_install(self, tenant_id: UUID) -> None:
        """Called when the plugin is installed for a tenant. Run migrations, seed data."""
        ...

    @abstractmethod
    async def on_uninstall(self, tenant_id: UUID) -> None:
        """Called when the plugin is removed for a tenant. Cleanup."""
        ...
```

### 10.2 Domain Manifest

```python
class DomainManifest(BaseModel):
    domain_id: str                        # e.g., "health"
    name: str                             # "Health & Wellness"
    version: str                          # "0.1.0"
    description: str
    author: str

    # Capabilities
    supported_intents: list[IntentDeclaration]
    entities: list[EntityDeclaration]
    capabilities: list[str]               # Freeform capability tags

    # Dependencies
    required_kernel_version: str          # semver range
    cross_domain_reads: list[str]         # Domains this plugin reads from
    cross_domain_writes: list[str]        # Domains this plugin writes to (rare)

    # Resources
    requires_vector_storage: bool = True
    requires_object_storage: bool = False
    requires_scheduler: bool = True

    # Configuration
    default_config: dict = {}
    user_configurable_settings: list[SettingDeclaration] = []

class IntentDeclaration(BaseModel):
    intent_id: str                        # e.g., "health.log_meal"
    description: str
    example_messages: list[str]           # For the domain router's classifier
    keywords: list[str]
    workflow_id: str                      # Which workflow handles this intent

class EntityDeclaration(BaseModel):
    entity_name: str                      # e.g., "Meal"
    table_name: str                       # e.g., "health_meals"
    description: str
    fields: list[FieldDeclaration]

class SettingDeclaration(BaseModel):
    key: str
    label: str
    type: str                             # "boolean", "string", "number", "enum"
    default: Any
    options: Optional[list[str]] = None   # For enum type
```

### 10.3 Domain Orchestrator

Each domain has its own orchestrator — a sub-graph that handles domain-specific workflow execution.

```python
class DomainOrchestrator(ABC):
    """
    Domain-level orchestrator. Receives a classified intent and
    memory packet from the global orchestrator, executes the
    appropriate domain workflow, and returns structured results.
    """

    @abstractmethod
    async def handle_intent(
        self,
        intent: ClassifiedIntent,
        memory_packet: MemoryPacket,
        workflow_context: WorkflowContext,
    ) -> DomainResult:
        """
        Execute the domain workflow for the given intent.
        Returns a structured result that the response synthesizer
        will convert to natural language.
        """
        ...

    @abstractmethod
    async def handle_scheduled_job(
        self,
        job: ScheduledJob,
        memory_packet: MemoryPacket,
    ) -> DomainResult:
        """Handle a scheduled job trigger."""
        ...

class DomainResult(BaseModel):
    domain_id: str
    intent: str
    success: bool
    result_type: str                      # "data", "confirmation", "question", "error"
    structured_data: Optional[dict]       # Machine-readable result
    summary: str                          # Human-readable summary for synthesis
    follow_up_actions: list[FollowUpAction] = []
    events_to_emit: list[dict] = []       # Events for the event bus
    state_mutations: list[StateMutation] = []  # State changes to apply
    error: Optional[str] = None
```

### 10.4 Plugin Lifecycle

```
1. REGISTRATION
   Developer creates a domain module implementing DomainPlugin.
   Module is registered in the domain_registry table.

2. INSTALLATION (per tenant)
   on_install() is called:
   - Run domain-specific DB migrations
   - Seed default data (e.g., default meal categories)
   - Register scheduled jobs
   - Register tools and prompts

3. ACTIVE
   Domain receives intents from the global orchestrator.
   Workflows execute. Events emit. State mutates.

4. CONFIGURATION
   User can configure domain-specific settings
   (e.g., dietary preferences, currency, target language).

5. UNINSTALLATION (per tenant)
   on_uninstall() is called:
   - Cancel scheduled jobs
   - Optionally archive or delete domain data
   - Deregister tools and prompts
```

### 10.5 Plugin Discovery

In the modular monolith, plugins are Python packages within the `domains/` directory. Discovery is via a registry pattern:

```python
# domains/__init__.py
DOMAIN_REGISTRY: dict[str, type[DomainPlugin]] = {}

def register_domain(domain_id: str):
    def decorator(cls):
        DOMAIN_REGISTRY[domain_id] = cls
        return cls
    return decorator

# domains/health/plugin.py
@register_domain("health")
class HealthPlugin(DomainPlugin):
    ...
```

At startup, the kernel scans the registry, validates manifests, and initializes all registered domains.

---

## 11. Multi-Tenant Model

### 11.1 Design Approach

AI Life OS is designed as **multi-tenant from day 1** in schema and isolation strategy, even though the MVP runs as a single-tenant personal system.

The tenancy model supports four tiers of usage:

| Tier | Description | Example |
|------|-------------|---------|
| **Personal** | Single user, single tenant | Solo user running their own instance |
| **Family** | Single tenant, multiple users | Family workspace with shared and private data |
| **Consumer** | Multiple tenants, each with one user | SaaS with many individual users |
| **B2B** | Multiple tenants, each with multiple users | Coaching platform with coaches and clients |

### 11.2 Core Entities

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│    Tenant    │      │     User     │      │  TenantUser  │
│              │      │              │      │              │
│ id           │      │ id           │      │ id           │
│ name         │◄─────│              │      │ tenant_id ───┼──► Tenant
│ slug         │      │ email        │      │ user_id ─────┼──► User
│ plan         │      │ name         │      │ role         │
│ settings     │      │ auth_provider│      │ settings     │
│ created_at   │      │ created_at   │      │ active       │
│ active       │      │ active       │      │ joined_at    │
└──────────────┘      └──────────────┘      └──────────────┘
       │
       ▼
┌──────────────┐
│  Workspace   │
│              │
│ id           │
│ tenant_id    │
│ name         │
│ type         │  ("personal", "shared", "team")
│ settings     │
│ created_at   │
└──────────────┘
```

### 11.3 Tenant Isolation Strategy

**Database-level isolation**: Row-level. Every table with user data carries a `tenant_id` column.

**Isolation mechanisms:**

1. **Application-level**: Every query includes `tenant_id` in the WHERE clause. Enforced by a middleware that injects the tenant context from the authenticated session.
2. **Row-Level Security (RLS)**: PostgreSQL RLS policies as a second line of defense. Even if application code has a bug, RLS prevents cross-tenant data access.
3. **Vector data**: All vector embeddings carry `tenant_id` in metadata. Vector searches are always filtered by tenant.
4. **Redis keys**: Namespaced by tenant: `{tenant_id}:{key_type}:{id}`.
5. **Object storage**: Prefixed by tenant: `{tenant_id}/{document_id}/{filename}`.
6. **Scheduled jobs**: Each job record carries `tenant_id`. Scheduler dispatches per-tenant.

```python
class TenantContext:
    """
    Set at the start of every request/job.
    All repository methods read from this context.
    """
    tenant_id: UUID
    user_id: UUID
    workspace_id: Optional[UUID]
    role: str                    # "owner", "admin", "member", "viewer"

# Middleware example
async def tenant_middleware(request: Request, call_next):
    token = extract_token(request)
    tenant_ctx = resolve_tenant_context(token)
    request.state.tenant = tenant_ctx
    set_rls_context(tenant_ctx.tenant_id)  # SET app.current_tenant_id = ...
    response = await call_next(request)
    return response
```

### 11.4 RBAC Model

Simple role-based access for MVP, extensible later:

| Role | Permissions |
|------|-------------|
| **owner** | Full access. Manage tenant settings, users, billing. |
| **admin** | Manage users, manage domains, view all data. |
| **member** | Full access to own data. Shared workspace read access. |
| **viewer** | Read-only access to shared workspaces. |

### 11.5 Shared vs. Isolated Resources

| Resource | Isolation Level | Notes |
|----------|----------------|-------|
| LLM API keys | Tenant-level | Each tenant can bring their own key, or use platform keys |
| Connector credentials | Tenant-level | Encrypted, per-tenant |
| Vector embeddings | Row-level (tenant_id filter) | Shared pgvector instance |
| Object storage | Prefix-level | `{tenant_id}/` prefix |
| Scheduled jobs | Tenant-scoped | Jobs tagged with tenant_id |
| Domain plugins | Platform-level (shared code) | Configuration is per-tenant |
| Prompt templates | Platform-level (shared) | Overrides per-tenant possible later |

### 11.6 Personal → Multi-Tenant Migration Path

1. **Phase 0 (MVP)**: Single tenant, single user. `tenant_id` and `user_id` exist in the schema but are always the same value. No auth complexity.
2. **Phase 1**: Add authentication (API keys or simple JWT). Still single tenant.
3. **Phase 3**: Add tenant provisioning, user invitation, workspace management.
4. **Phase 5**: Add RLS enforcement, billing, resource quotas, tenant admin UI.

The key insight: by including `tenant_id` in every table and every query from day 1, the migration to multi-tenant is a matter of adding auth, provisioning, and admin UIs — not a schema redesign.

---

## 12. Database and Schema Design

The full schema design is documented in a separate companion document: **[SCHEMA_DESIGN.md](./SCHEMA_DESIGN.md)**.

### 12.1 Schema Organization

The schema is organized into these namespaces:

| Namespace | Prefix | Description |
|-----------|--------|-------------|
| **Core** | `core_` | Tenants, users, workspaces, settings |
| **Communication** | `comm_` | Channels, conversations, messages |
| **Memory** | `mem_` | Facts, summaries, embeddings, semantic memories |
| **Knowledge** | `know_` | Documents, chunks, relations |
| **Orchestration** | `orch_` | Workflows, workflow runs, steps |
| **Scheduling** | `sched_` | Jobs, reminders, tasks |
| **Events** | `evt_` | Life log events, audit events |
| **Domain: Health** | `health_` | Meals, workouts, metrics, conditions |
| **Domain: Finance** | `fin_` | Accounts, transactions, budgets, investments |
| **Domain: Education** | `edu_` | Courses, study sessions, vocabulary, progress |
| **Domain: Return-Later** | `rl_` | Captured links, reading queue, annotations |

### 12.2 Key Design Principles

1. **Every table has `tenant_id`** — no exceptions for user-data tables.
2. **UUIDs for primary keys** — globally unique, no tenant-sequence collisions.
3. **Timestamps everywhere** — `created_at`, `updated_at`, and `deleted_at` (soft delete) on all tables.
4. **JSONB for flexible metadata** — structured columns for queryable fields, JSONB for extensible metadata.
5. **Partitioning for append-only tables** — events and messages partitioned by month.
6. **Indexes designed for common access patterns** — composite indexes on `(tenant_id, user_id, ...)`.

### 12.3 Entity Relationship Summary

See [SCHEMA_DESIGN.md](./SCHEMA_DESIGN.md) for full entity definitions, field types, indexes, and constraints.

---

## 13. Event Model

### 13.1 Event-Driven Architecture

Every meaningful action in AI Life OS produces an **event**. Events are the connective tissue of the system — they enable auditability, personalization, cross-domain intelligence, and future replay/derivation.

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Producer   │────►│   Event Bus     │────►│   Consumers     │
│             │     │                 │     │                 │
│ - Domains   │     │ - In-process    │     │ - Event Logger  │
│ - Kernel    │     │   (sync MVP)    │     │ - Memory Consol.│
│ - Scheduler │     │ - Redis pub/sub │     │ - Schedulers    │
│ - Connectors│     │   (async later) │     │ - Alerting      │
│             │     │                 │     │ - Analytics     │
└─────────────┘     └─────────────────┘     │ - Domain X      │
                                            └─────────────────┘
```

### 13.2 Event Schema

```python
class PlatformEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str                   # e.g., "health.meal_logged"
    event_category: str               # "domain", "system", "communication"
    domain: Optional[str]             # Source domain, None for system events
    tenant_id: UUID
    user_id: UUID
    correlation_id: Optional[UUID]    # Links to triggering request
    causation_id: Optional[UUID]      # Event that caused this event

    payload: dict                     # Event-specific data
    metadata: dict = {}               # Processing metadata

    source: str                       # "user_action", "system", "scheduler", "connector"
    importance: float = 0.5           # 0-1 for retrieval ranking
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### 13.3 Event Categories and Examples

**Domain Events:**

| Event Type | Domain | Payload Example |
|------------|--------|-----------------|
| `health.meal_logged` | health | `{meal_type: "lunch", calories: 650, items: [...]}` |
| `health.workout_completed` | health | `{type: "running", duration_min: 30, distance_km: 5}` |
| `health.workout_skipped` | health | `{planned: "gym", reason: "tired"}` |
| `health.mood_logged` | health | `{mood: "stressed", energy: 3}` |
| `finance.transaction_imported` | finance | `{amount: -45.50, currency: "EUR", category: "dining"}` |
| `finance.budget_exceeded` | finance | `{budget: "dining", limit: 200, current: 215}` |
| `tutor.lesson_completed` | tutor | `{language: "dutch", topic: "past_tense", score: 0.8}` |
| `tutor.vocab_reviewed` | tutor | `{words_reviewed: 20, correct: 16}` |
| `edu.study_session_logged` | education | `{subject: "ML", duration_min: 45}` |
| `rl.link_captured` | return-later | `{url: "...", title: "...", tags: ["ai", "health"]}` |
| `rl.document_processed` | return-later | `{doc_id: "...", chunks: 12, summary: "..."}` |

**System Events:**

| Event Type | Payload Example |
|------------|-----------------|
| `system.user_message_received` | `{channel: "whatsapp", content_type: "text"}` |
| `system.response_sent` | `{channel: "whatsapp", domains_involved: ["health"]}` |
| `system.workflow_completed` | `{workflow: "health.log_meal", duration_ms: 1200}` |
| `system.workflow_failed` | `{workflow: "...", error: "..."}` |
| `system.memory_consolidated` | `{memories_created: 3, type: "daily_summary"}` |
| `system.knowledge_ingested` | `{doc_id: "...", chunks: 8}` |
| `system.scheduled_job_executed` | `{job_id: "...", domain: "tutor"}` |

### 13.4 Event Bus Implementation

**MVP (Modular Monolith):**
- In-process event dispatcher using a simple publish/subscribe pattern.
- Synchronous for critical consumers (event logger), async for non-critical (consolidation).

```python
class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._global_handlers: list[Callable] = []

    def subscribe(self, event_type: str, handler: Callable):
        self._handlers[event_type].append(handler)

    def subscribe_all(self, handler: Callable):
        self._global_handlers.append(handler)

    async def publish(self, event: PlatformEvent):
        # Always log (synchronous)
        await self._persist_event(event)

        # Notify specific handlers
        for handler in self._handlers.get(event.event_type, []):
            await self._safe_dispatch(handler, event)

        # Notify global handlers
        for handler in self._global_handlers:
            await self._safe_dispatch(handler, event)

    async def _persist_event(self, event: PlatformEvent):
        """Write to events table — this is the audit trail."""
        ...

    async def _safe_dispatch(self, handler: Callable, event: PlatformEvent):
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Event handler failed: {handler.__name__}, event: {event.event_type}", exc_info=e)
```

**Future (scaled):**
- Replace in-process dispatch with Redis Streams or a proper message broker.
- Consumers become independent workers.
- Event replay from persistent store for rebuilding state or backfilling.

### 13.5 Auditability

Every event is persisted to the `evt_events` table (append-only, partitioned by month). This provides:

1. **Full audit trail**: Who did what, when, triggered by what.
2. **Replay capability**: Events can be replayed to rebuild materialized views or backfill new features.
3. **Personalization data**: Events are the raw data for behavioral pattern detection.
4. **Debugging**: Full causal chain via `correlation_id` and `causation_id`.

### 13.6 Event Consumption Patterns

| Consumer | Purpose | Sync/Async |
|----------|---------|------------|
| Event Logger | Persist to DB | Sync (always) |
| Memory Consolidator | Detect patterns, create semantic memories | Async (background) |
| Scheduler Trigger | Some events trigger follow-up jobs | Async |
| Domain Cross-Listeners | E.g., Finance listens to health.meal_logged for expense correlation | Async |
| Alerting | Trigger alerts on threshold events (budget exceeded) | Async |
| Analytics | Update aggregate counters | Async |

---

## 14. Knowledge Ingestion Design

### 14.1 Overview

The knowledge ingestion system is a shared pipeline that processes external content from any source and makes it searchable, summarizable, and usable across all domains.

```
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION PIPELINE                            │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ WhatsApp │  │ Telegram │  │ REST API │  │ Browser  │       │
│  │  Link    │  │  Link    │  │  Upload  │  │Extension │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       └──────────────┴──────────────┴──────────────┘             │
│                          │                                      │
│                 ┌────────▼────────┐                              │
│                 │   INGEST QUEUE  │ (Redis / DB queue)           │
│                 └────────┬────────┘                              │
│                          │                                      │
│              ┌───────────▼───────────┐                           │
│              │   INGESTION WORKER    │                           │
│              │                       │                           │
│              │  1. Deduplication     │                           │
│              │  2. Metadata extract  │                           │
│              │  3. Content fetch     │                           │
│              │  4. Parse & clean     │                           │
│              │  5. Chunk             │                           │
│              │  6. Embed             │                           │
│              │  7. Tag & categorize  │                           │
│              │  8. Entity extract    │                           │
│              │  9. Summarize         │                           │
│              │ 10. Domain routing    │                           │
│              │ 11. Store             │                           │
│              └───────────┬───────────┘                           │
│                          │                                      │
│              ┌───────────▼───────────┐                           │
│              │   KNOWLEDGE STORE     │                           │
│              │                       │                           │
│              │  • Postgres (metadata)│                           │
│              │  • pgvector (chunks)  │                           │
│              │  • Object store (raw) │                           │
│              └───────────────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

### 14.2 Ingestion Request

```python
class IngestionRequest(BaseModel):
    tenant_id: UUID
    user_id: UUID
    source_type: str                  # "url", "file_upload", "note", "browser_capture"
    url: Optional[str] = None
    file_content: Optional[bytes] = None
    file_name: Optional[str] = None
    file_mime_type: Optional[str] = None
    note_text: Optional[str] = None
    source_channel: Optional[str]     # Which channel it came from
    user_tags: list[str] = []         # Tags the user explicitly provided
    user_note: Optional[str] = None   # User's note about the content
    priority: str = "normal"          # "high", "normal", "low"
    correlation_id: Optional[UUID]
```

### 14.3 Pipeline Steps

**Step 1: Deduplication**
- Hash the URL or file content.
- Check against `know_documents` table: `(tenant_id, content_hash)`.
- If duplicate: update `last_captured_at`, merge tags, skip re-processing. Notify user.
- If URL was captured before but content changed (re-fetch): create new version.

**Step 2: Metadata Extraction**
- For URLs: fetch HTTP headers, extract `og:title`, `og:description`, `og:image`, `content-type`.
- For files: extract MIME type, file size, page count (PDFs).
- For notes: extract length, detect language.

**Step 3: Content Fetch**
- For URLs: use a headless browser or readability library to extract main content (strip navigation, ads, etc.).
- For PDFs: use `pymupdf` or `pdfplumber` to extract text.
- For other files: use appropriate parsers (docx, xlsx, etc.).
- Timeout: 30 seconds. Max content size: 10MB.
- Store raw content in object storage.

**Step 4: Parse and Clean**
- Strip HTML, normalize whitespace, fix encoding.
- Detect language.
- Extract structured elements (tables, lists, code blocks) and preserve structure.

**Step 5: Chunking**
- Apply recursive character splitting (512 tokens, 64 token overlap).
- Preserve paragraph boundaries where possible.
- Each chunk gets: `chunk_index`, `document_id`, `text`, position metadata.

**Step 6: Embedding**
- Embed each chunk using the shared `EmbeddingService`.
- Batch embedding for efficiency (up to 100 chunks per API call).
- Store embeddings in `know_chunks` table (pgvector column).

**Step 7: Tagging and Categorization**
- LLM call to classify content into domains and topics.
- Input: document title + first 500 tokens + user tags.
- Output: `{domains: ["health", "nutrition"], topics: ["intermittent fasting", "meal planning"], content_type: "article"}`.
- This enables domain-filtered retrieval.

**Step 8: Entity Extraction**
- LLM call to extract named entities and key concepts.
- Output: `{entities: [{name: "intermittent fasting", type: "concept"}, {name: "16:8 method", type: "method"}]}`.
- Stored in `know_relations` table for relationship-aware retrieval.

**Step 9: Summarization**
- LLM call to generate a concise summary (2-3 sentences).
- Stored in `know_documents.summary` field.
- Also generates key takeaways (3-5 bullet points) stored in `know_documents.key_points`.

**Step 10: Domain Routing**
- Based on tags from Step 7, notify relevant domains that new knowledge is available.
- Domains can react (e.g., Tutor module sees a Dutch article → adds to reading list).
- Implemented via internal events: `system.knowledge_ingested` with domain tags.

**Step 11: Storage**
- `know_documents` table: metadata, summary, key points, status.
- `know_chunks` table: chunk text, embeddings, metadata.
- `know_relations` table: entity/topic links.
- Object storage: raw content.
- Emit `rl.link_captured` or `rl.document_processed` event.

### 14.4 Content Type Support

| Content Type | Parser | Notes |
|--------------|--------|-------|
| Web pages (HTML) | readability + BeautifulSoup | Main content extraction |
| PDFs | pymupdf / pdfplumber | Text extraction, table detection |
| Plain text | Direct | Minimal processing |
| Markdown | Direct | Preserve structure |
| YouTube videos | youtube-transcript-api | Transcript extraction |
| Images | LLM vision (GPT-4o) | Description extraction |
| Office docs | python-docx, openpyxl | Text extraction |

### 14.5 How Knowledge Serves Domains

| Domain | Knowledge Use Case |
|--------|--------------------|
| **Health** | Articles about nutrition, exercise research, supplement info |
| **Finance** | Investment articles, financial news, tax guides |
| **Tutor** | Dutch articles for reading practice, grammar references |
| **Education** | Study materials, textbook chapters, lecture notes |
| **Return-Later** | Primary domain — manages the full reading queue |
| **Life Tracker** | Any content the user captures as personally meaningful |

---

## 15. Scheduling / Reminders / Tasking Model

### 15.1 Shared Scheduling System

The scheduler is a kernel-level service that all domains use for time-based triggers.

```
┌────────────────────────────────────────────────────────┐
│                  SCHEDULER SERVICE                      │
│                                                        │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │  Job Definitions │  │   Job Scheduler  │            │
│  │                  │  │                  │            │
│  │  • One-time      │  │  • Cron parser   │            │
│  │  • Recurring     │  │  • Next-run calc │            │
│  │  • Cron-based    │  │  • Timezone-aware│            │
│  │  • Spaced rep.   │  │  • Tenant-scoped │            │
│  └──────────────────┘  └────────┬─────────┘            │
│                                 │                      │
│                        ┌────────▼─────────┐            │
│                        │   Job Runner     │            │
│                        │                  │            │
│                        │  • Dispatch to   │            │
│                        │    domain orch.  │            │
│                        │  • Handle        │            │
│                        │    retries       │            │
│                        │  • Log execution │            │
│                        └──────────────────┘            │
└────────────────────────────────────────────────────────┘
```

### 15.2 Job Definition

```python
class ScheduledJobDefinition(BaseModel):
    job_id: str                           # e.g., "health.daily_checkin"
    domain: str
    name: str
    description: str
    schedule_type: ScheduleType           # "once", "recurring", "cron", "spaced_repetition"

    # For "once"
    run_at: Optional[datetime] = None

    # For "recurring"
    interval_seconds: Optional[int] = None

    # For "cron"
    cron_expression: Optional[str] = None  # e.g., "0 9 * * *" (daily at 9am)

    # For "spaced_repetition"
    sr_algorithm: Optional[str] = None     # e.g., "sm2"
    sr_initial_interval_hours: Optional[int] = None

    # Common
    timezone: str = "UTC"                  # User's timezone for scheduling
    payload: dict = {}                     # Data passed to the job handler
    enabled: bool = True
    max_retries: int = 2

class ScheduleType(str, Enum):
    ONCE = "once"
    RECURRING = "recurring"
    CRON = "cron"
    SPACED_REPETITION = "spaced_repetition"
```

### 15.3 Job Instance

```python
class ScheduledJobInstance(BaseModel):
    instance_id: UUID
    job_id: str
    tenant_id: UUID
    user_id: UUID
    scheduled_for: datetime
    status: JobStatus                     # "pending", "running", "completed", "failed", "skipped"
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[dict]
    error: Optional[str]
    retry_count: int = 0
    next_run_at: Optional[datetime]       # For recurring jobs

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
```

### 15.4 Scheduling Use Cases by Domain

| Domain | Job | Schedule | Description |
|--------|-----|----------|-------------|
| **Health** | Daily check-in | Cron: `0 9 * * *` | "Good morning! How are you feeling? Any meals to log from yesterday?" |
| **Health** | Weekly summary | Cron: `0 18 * * 0` | Weekly health stats: meals logged, workouts, mood trends |
| **Finance** | Daily expense reminder | Cron: `0 20 * * *` | "Any expenses to log today?" |
| **Finance** | Weekly finance review | Cron: `0 10 * * 6` | Budget vs. actual, upcoming bills, investment summary |
| **Finance** | Monthly report | Cron: `0 9 1 * *` | Full monthly financial report |
| **Tutor** | Daily vocabulary practice | Cron: `0 8 * * *` | Spaced repetition vocabulary quiz |
| **Tutor** | Spaced repetition | SM-2 algorithm | Review words based on individual item intervals |
| **Education** | Study reminder | User-configured | "Time to study {subject}!" |
| **Return-Later** | Reading digest | Cron: `0 19 * * *` | "You have 5 unread articles. Here's today's pick: ..." |
| **Return-Later** | Stale link cleanup | Cron: `0 0 1 * *` | Remind about links captured >30 days ago and unread |
| **Cross-domain** | Weekly life review | Cron: `0 18 * * 0` | Cross-domain summary: health + finance + education + mood |

### 15.5 Task Model

Tasks are user-facing action items that may be created by the user or by the system.

```python
class Task(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    domain: Optional[str]                 # Originating domain, None for general
    title: str
    description: Optional[str]
    status: TaskStatus                    # "pending", "in_progress", "completed", "cancelled"
    priority: TaskPriority                # "low", "medium", "high", "urgent"
    due_at: Optional[datetime]
    remind_at: Optional[datetime]
    recurrence: Optional[str]             # Cron expression for recurring tasks
    tags: list[str] = []
    parent_task_id: Optional[UUID]        # For subtasks
    created_by: str                       # "user" or "system"
    created_at: datetime
    completed_at: Optional[datetime]
    metadata: dict = {}
```

### 15.6 Reminder Model

Reminders are lightweight, time-triggered notifications.

```python
class Reminder(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    domain: Optional[str]
    message: str
    remind_at: datetime
    channel_preference: Optional[ChannelType]  # Preferred delivery channel
    status: str                           # "pending", "sent", "acknowledged", "snoozed"
    snooze_until: Optional[datetime]
    recurrence: Optional[str]
    correlation_id: Optional[UUID]        # What triggered this reminder
    created_at: datetime
```

### 15.7 Scheduler Implementation

**MVP**: Redis-backed polling scheduler.
- A background worker polls `sched_job_instances` every 30 seconds for jobs where `scheduled_for <= now() AND status = 'pending'`.
- Claims jobs using optimistic locking (`UPDATE ... WHERE status = 'pending' RETURNING ...`).
- Dispatches to the appropriate domain orchestrator.
- Updates status and calculates `next_run_at` for recurring jobs.

**Timezone handling**: All schedules stored in UTC internally. User's timezone applied when calculating next run time for cron expressions.

**Missed job handling**: If a job's `scheduled_for` is in the past by more than a configurable threshold (default: 1 hour), it's marked as `skipped` and the next occurrence is scheduled. Prevents a burst of stale jobs after downtime.

---

## 16. Generic Agent Model

### 16.1 Agent Philosophy

Agents in AI Life OS are **bounded, supervised, and auditable**. They are not autonomous entities roaming freely — they are specialized workers invoked by orchestrators for specific tasks.

```
┌────────────────────────────────────────────────────────┐
│                  AGENT CHARACTERISTICS                  │
│                                                        │
│  ✓ Single, well-defined responsibility                 │
│  ✓ Explicit input/output schemas                       │
│  ✓ Scoped tool access (only tools they need)           │
│  ✓ Token budget limits                                 │
│  ✓ Timeout limits                                      │
│  ✓ Full execution logging                              │
│  ✓ Invoked by orchestrators, never self-triggered      │
│                                                        │
│  ✗ No autonomous goal-setting                          │
│  ✗ No unbounded tool chains                            │
│  ✗ No direct database access                           │
│  ✗ No cross-agent communication without orchestrator   │
│  ✗ No self-modification                                │
└────────────────────────────────────────────────────────┘
```

### 16.2 Agent Definition

```python
class AgentDefinition(BaseModel):
    agent_id: str                         # e.g., "health.meal_parser"
    domain: Optional[str]                 # None for shared agents
    name: str
    description: str
    role: str                             # System prompt role description

    # LLM configuration
    model: str                            # e.g., "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: int = 1000
    prompt_template_id: str               # Reference to prompt registry

    # Tool access
    allowed_tools: list[str] = []         # Tool IDs this agent can use
    max_tool_calls: int = 5               # Max tool invocations per run

    # Input/Output
    input_schema: dict                    # JSON Schema for expected input
    output_schema: dict                   # JSON Schema for expected output
    structured_output: bool = True        # Use structured output mode

    # Guardrails
    timeout_seconds: int = 30
    max_retries: int = 1
    require_output_validation: bool = True

class AgentInvocation(BaseModel):
    invocation_id: UUID
    agent_id: str
    input_data: dict
    output_data: Optional[dict]
    model_used: str
    prompt_version: int
    tokens_input: int
    tokens_output: int
    tool_calls: list[ToolCallRecord]
    latency_ms: float
    status: str                           # "success", "failed", "timeout"
    error: Optional[str]
    timestamp: datetime
```

### 16.3 Agent Types

| Type | Description | Examples |
|------|-------------|---------|
| **Parser agents** | Extract structured data from natural language | Meal parser, expense parser, mood parser |
| **Classifier agents** | Categorize or label input | Intent classifier, transaction categorizer, topic classifier |
| **Generator agents** | Create content | Quiz generator, summary generator, report generator |
| **Analyzer agents** | Reason about data and produce insights | Budget analyzer, health trend analyzer, study progress analyzer |
| **Planner agents** | Create multi-step plans | Meal plan generator, study plan generator, workout planner |
| **Synthesis agents** | Combine information into coherent output | Response synthesizer, weekly review composer |

### 16.4 Agent vs. Deterministic Service

The system clearly separates when to use an agent (LLM) vs. a deterministic service:

| Criterion | Use Agent (LLM) | Use Deterministic Service |
|-----------|------------------|---------------------------|
| Input is natural language | ✓ | |
| Output requires reasoning | ✓ | |
| Task involves interpretation | ✓ | |
| Task involves exact calculations | | ✓ |
| Task mutates source-of-truth state | | ✓ |
| Task has regulatory implications | | ✓ (with LLM assist for input) |
| Task is pattern recognition | ✓ | |
| Task is data transformation with fixed rules | | ✓ |

**Example**: Logging a meal
- **Agent**: Parses "chicken salad with avocado, about 400g" → `{items: [{name: "chicken breast", qty: 200, unit: "g"}, {name: "mixed salad", qty: 150, unit: "g"}, {name: "avocado", qty: 50, unit: "g"}], meal_type: "lunch"}`
- **Deterministic service**: Looks up nutrition database, calculates totals: `{calories: 485, protein: 42, carbs: 12, fat: 30}`
- **Deterministic service**: Writes to database, updates daily totals.

### 16.5 Agent Execution Runtime

```python
class AgentRuntime:
    async def invoke(
        self,
        agent_id: str,
        input_data: dict,
        memory_packet: MemoryPacket,
        tenant_context: TenantContext,
    ) -> AgentInvocation:
        # 1. Load agent definition
        agent_def = self.agent_registry.get(agent_id)

        # 2. Build prompt from template + input + memory
        prompt = self.prompt_registry.render(
            agent_def.prompt_template_id,
            input_data=input_data,
            memory_context=memory_packet.to_prompt_context(),
        )

        # 3. Pre-execution policy check
        policy_result = await self.policy_layer.check_pre_execution(
            agent_id, input_data, tenant_context
        )
        if not policy_result.allowed:
            return AgentInvocation(status="blocked", error=policy_result.blocked_reason, ...)

        # 4. Invoke LLM with tool access
        llm_result = await self.llm_client.call(
            model=agent_def.model,
            messages=[{"role": "system", "content": agent_def.role}, {"role": "user", "content": prompt}],
            tools=[self.tool_registry.get(t) for t in agent_def.allowed_tools],
            max_tokens=agent_def.max_tokens,
            temperature=agent_def.temperature,
            response_format=agent_def.output_schema if agent_def.structured_output else None,
            timeout=agent_def.timeout_seconds,
        )

        # 5. Post-execution policy check
        policy_result = await self.policy_layer.check_post_execution(
            agent_id, llm_result, tenant_context
        )

        # 6. Validate output against schema
        if agent_def.require_output_validation:
            validated_output = validate_against_schema(llm_result.output, agent_def.output_schema)

        # 7. Log invocation
        invocation = AgentInvocation(
            invocation_id=uuid4(),
            agent_id=agent_id,
            input_data=input_data,
            output_data=validated_output,
            model_used=agent_def.model,
            tokens_input=llm_result.usage.input_tokens,
            tokens_output=llm_result.usage.output_tokens,
            tool_calls=llm_result.tool_calls,
            latency_ms=llm_result.latency_ms,
            status="success",
            timestamp=datetime.utcnow(),
        )
        await self.invocation_logger.log(invocation)

        return invocation
```

### 16.6 Tool Execution Within Agents

When an agent has tool access, tool calls are executed by the runtime, not by the agent itself:

1. LLM returns a tool call request.
2. Runtime validates the tool call against the agent's `allowed_tools`.
3. Runtime executes the tool via the tool registry.
4. Tool result is fed back to the LLM for the next step.
5. Maximum `max_tool_calls` iterations before forcing a response.

This keeps the agent bounded — it cannot make tool calls outside its scope, and it cannot loop indefinitely.

---

## 17. Connector Model

### 17.1 Overview

Connectors are integrations with external services that import data into or export data out of AI Life OS. They are distinct from **communication adapters** (which handle user interaction channels) — connectors handle **data integrations**.

```
┌────────────────────────────────────────────────────────────────┐
│                      CONNECTOR LAYER                           │
│                                                                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │   Bank     │  │  Fitness   │  │  Calendar  │  . . .        │
│  │ Connector  │  │ Connector  │  │ Connector  │               │
│  │ (Plaid/    │  │ (Apple     │  │ (Google    │               │
│  │  manual)   │  │  Health)   │  │  Calendar) │               │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘               │
│        └────────────────┼────────────────┘                     │
│                         │                                      │
│                ┌────────▼────────┐                              │
│                │   Connector     │                              │
│                │   Runtime       │                              │
│                │                 │                              │
│                │ • Auth mgmt     │                              │
│                │ • Sync schedule │                              │
│                │ • Data mapping  │                              │
│                │ • Error handling│                              │
│                └────────┬────────┘                              │
│                         │                                      │
│                ┌────────▼────────┐                              │
│                │  Normalized     │                              │
│                │  Domain Events  │ → Event Bus → Domain Modules │
│                └─────────────────┘                              │
└────────────────────────────────────────────────────────────────┘
```

### 17.2 Connector Interface

```python
class Connector(ABC):
    """
    Base interface for external data connectors.
    Connectors pull data from external services and push
    normalized events into the platform's event bus.
    """

    @abstractmethod
    def get_manifest(self) -> ConnectorManifest:
        ...

    @abstractmethod
    async def authenticate(self, credentials: dict) -> AuthResult:
        ...

    @abstractmethod
    async def sync(self, config: SyncConfig) -> SyncResult:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...

class ConnectorManifest(BaseModel):
    connector_id: str                     # e.g., "bank.plaid"
    name: str
    description: str
    target_domain: str                    # Primary domain this feeds
    auth_type: str                        # "oauth2", "api_key", "credentials", "manual"
    sync_modes: list[str]                 # "pull", "push", "webhook"
    default_sync_interval_minutes: int
    required_scopes: list[str] = []
    config_schema: dict = {}

class SyncConfig(BaseModel):
    tenant_id: UUID
    user_id: UUID
    connector_id: str
    credentials_ref: str                  # Reference to encrypted credential store
    last_sync_at: Optional[datetime]
    config: dict = {}

class SyncResult(BaseModel):
    success: bool
    events: list[PlatformEvent]           # Normalized events to publish
    items_synced: int
    items_failed: int
    next_sync_at: Optional[datetime]
    error: Optional[str]
```

### 17.3 Example Connectors

| Connector | Domain | Sync Mode | Data |
|-----------|--------|-----------|------|
| **Bank (manual CSV)** | Finance | Pull (user upload) | Transactions |
| **Bank (Plaid)** | Finance | Pull (API) | Transactions, balances |
| **Apple Health** | Health | Push (webhook/export) | Steps, heart rate, sleep, workouts |
| **Google Calendar** | Scheduling | Pull (API) | Events, availability |
| **Pocket / Instapaper** | Return-Later | Pull (API) | Saved articles |
| **Goodreads** | Education | Pull (API) | Reading list, progress |
| **Notion** | Knowledge | Pull (API) | Notes, databases |

### 17.4 Credential Management

Connector credentials are sensitive and require special handling:

1. **Encryption at rest**: Credentials stored in a dedicated `connector_credentials` table with AES-256 encryption. Encryption key from environment variable, not in the database.
2. **Never logged**: Credentials are never written to logs, events, or error messages.
3. **Scoped access**: Only the connector runtime can decrypt credentials. Domain code never sees raw credentials.
4. **Rotation**: OAuth tokens are auto-refreshed before expiry. API keys require manual rotation.
5. **Revocation**: User can revoke a connector at any time, which deletes stored credentials immediately.

```python
class ConnectorCredential(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    connector_id: str
    encrypted_data: bytes                 # AES-256 encrypted JSON blob
    auth_type: str
    expires_at: Optional[datetime]
    refresh_token_ref: Optional[str]
    created_at: datetime
    updated_at: datetime
    active: bool = True
```

### 17.5 Sync Scheduling

Connectors use the shared scheduling system (Section 15):

- Each active connector instance has a recurring `ScheduledJobDefinition`.
- Sync frequency is configurable per connector and per user.
- Failed syncs are retried with exponential backoff (max 3 retries).
- Persistent failures trigger a `connector.sync_failed` event and user notification.

---

## 18. Security / Privacy / Safety Model

### 18.1 Security Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                     SECURITY LAYERS                            │
│                                                                │
│  Layer 1: TRANSPORT                                            │
│  • TLS 1.3 for all external connections                        │
│  • Webhook signature verification per channel                  │
│  • API rate limiting                                           │
│                                                                │
│  Layer 2: AUTHENTICATION                                       │
│  • JWT tokens for API access                                   │
│  • API keys for service-to-service                             │
│  • Channel-specific identity verification                      │
│                                                                │
│  Layer 3: AUTHORIZATION                                        │
│  • Tenant isolation (row-level + RLS)                          │
│  • Role-based access control                                   │
│  • Domain-level permissions                                    │
│                                                                │
│  Layer 4: DATA PROTECTION                                      │
│  • Encryption at rest (credentials, sensitive fields)          │
│  • PII handling and minimization                               │
│  • Soft-delete with retention policies                         │
│                                                                │
│  Layer 5: AI SAFETY                                            │
│  • Prompt injection prevention                                 │
│  • Output guardrails                                           │
│  • Domain-specific safety boundaries                           │
│  • Hallucination detection heuristics                          │
└────────────────────────────────────────────────────────────────┘
```

### 18.2 Authentication

**MVP Authentication Flow:**

| Client | Auth Method | Notes |
|--------|-------------|-------|
| REST API clients | JWT Bearer token | Issued after login, 1-hour expiry, refresh token rotation |
| WhatsApp webhook | Webhook signature verification | Meta's X-Hub-Signature-256 header |
| Telegram webhook | Secret token in URL path | Telegram's built-in webhook secret |
| Service-to-service | API key in header | For internal services (future) |
| Scheduled jobs | System context | No external auth; tenant context set from job metadata |

**Token Structure:**
```json
{
  "sub": "<user_id>",
  "tid": "<tenant_id>",
  "role": "owner",
  "iat": 1711234567,
  "exp": 1711238167,
  "iss": "ai-life-os"
}
```

### 18.3 Tenant Isolation

Covered in detail in Section 11.3. Summary of defense layers:

1. **Application-level**: Every database query includes `WHERE tenant_id = :current_tenant_id`.
2. **PostgreSQL RLS**: `CREATE POLICY tenant_isolation ON <table> USING (tenant_id = current_setting('app.current_tenant_id')::uuid)`.
3. **Vector search**: All pgvector queries include `WHERE tenant_id = :tid` in pre-filter.
4. **Redis**: Key namespace `{tenant_id}:*`.
5. **Object storage**: Path prefix `{tenant_id}/`.
6. **Logging**: Tenant context attached to all log entries for filtering.

### 18.4 API Security

- **Rate limiting**: Per-tenant, per-endpoint. Defaults: 100 req/min standard, 10/min LLM-intensive.
- **Input validation**: All API inputs validated via Pydantic models with strict type checking.
- **CORS**: Restricted to known origins (configurable per tenant).
- **Request size limits**: 10MB max for file uploads. 1MB for standard requests.
- **Idempotency**: All write endpoints accept an `Idempotency-Key` header.

### 18.5 PII Handling

| Data Type | Classification | Handling |
|-----------|---------------|----------|
| Name, email | PII | Stored in user profile. Not included in embeddings. |
| Phone number (WhatsApp) | PII | Stored as channel identity. Hashed in logs. |
| Health data | Sensitive PII | Stored in domain tables. Never sent to external APIs except LLM (with user consent). |
| Financial data | Sensitive PII | Stored in domain tables. Amounts rounded in logs. |
| Conversation content | PII | Stored raw. Summaries may be anonymized for analytics. |
| LLM prompts/responses | Contains PII | Logged with tenant isolation. Retention policy configurable. |

**PII Minimization in Logs:**
- Structured logs include `tenant_id` and `user_id` but not raw content.
- Debug-level logs with content are disabled in production.
- LLM interaction logs stored in a separate, access-controlled table.

### 18.6 AI Safety Boundaries

**Prompt Injection Prevention:**
- User input is always placed in the `user` role, never in `system`.
- System prompts include explicit instructions to ignore prompt injection attempts.
- Input is scanned for known injection patterns (heuristic, not foolproof).
- Structured output mode reduces the surface area for injection.

**Domain-Specific Safety:**

| Domain | Safety Boundary |
|--------|----------------|
| **Health** | Never diagnose conditions. Never prescribe medication. Always add disclaimer for health advice. Flag concerning symptoms for professional consultation. |
| **Finance** | Never provide investment advice as fact. All projections labeled as estimates. Never execute real transactions without explicit confirmation. |
| **All** | Never generate content that could be harmful, illegal, or abusive. |

**Output Guardrails:**
- Post-processing checks for disallowed content patterns.
- Confidence thresholds: if the LLM's confidence is below threshold, ask for clarification instead of guessing.
- Mandatory disclaimers for health and financial topics.

### 18.7 Encryption

| Data | At Rest | In Transit |
|------|---------|------------|
| Database | PostgreSQL TDE (optional, OS-level) | TLS to database |
| Connector credentials | AES-256 application-level | TLS |
| Object storage | Server-side encryption (S3-compatible) | TLS |
| Redis | AUTH + optional TLS | TLS (if remote) |
| LLM API calls | N/A | TLS 1.3 |

### 18.8 Data Deletion and Retention

**User-initiated deletion:**
- User can request full account deletion.
- Soft-delete (`deleted_at` timestamp) with 30-day grace period.
- After grace period: hard-delete all user data, embeddings, object storage files, and Redis keys.
- Event log entries anonymized (PII stripped) but retained for system analytics.

**Retention policies (configurable per tenant):**

| Data Type | Default Retention | Notes |
|-----------|------------------|-------|
| Conversation messages | 2 years | Can be reduced by user |
| Session state (Redis) | 2 hours | Auto-evicted |
| Events | Permanent | Partitioned, older partitions to cold storage |
| Knowledge documents | Until user deletes | No auto-expiry |
| LLM interaction logs | 90 days | For debugging and prompt improvement |
| Connector sync logs | 30 days | Operational logs only |

---

## 19. Observability and Auditability

### 19.1 Observability Stack

```
┌────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY LAYERS                         │
│                                                                │
│  STRUCTURED LOGGING                                            │
│  • JSON-formatted logs with structlog                          │
│  • Correlation IDs on every log line                           │
│  • Tenant + user context on every log line                     │
│  • Log levels: DEBUG, INFO, WARN, ERROR                        │
│  • Sink: stdout → log aggregator (Loki, CloudWatch, etc.)      │
│                                                                │
│  REQUEST TRACING                                               │
│  • Unique request_id per inbound event                         │
│  • Correlation ID propagated through entire processing chain   │
│  • Spans for: channel adapter → orchestrator → domain →        │
│    agent → tool → response                                     │
│  • OpenTelemetry-compatible                                    │
│                                                                │
│  METRICS                                                       │
│  • Request latency (p50, p95, p99)                             │
│  • LLM call latency and token usage                            │
│  • Workflow success/failure rates                               │
│  • Events per domain per hour                                  │
│  • Queue depth and processing lag                              │
│  • Prometheus-compatible                                       │
│                                                                │
│  ALERTING                                                      │
│  • Workflow failure rate threshold                              │
│  • LLM error rate threshold                                    │
│  • Queue backlog threshold                                     │
│  • Connector sync failure                                      │
└────────────────────────────────────────────────────────────────┘
```

### 19.2 Correlation ID Propagation

Every inbound event generates a `correlation_id` (UUID) that is attached to:

1. The inbound `NormalizedInboundEvent`
2. All log lines during processing
3. All database writes (events, state mutations)
4. All LLM calls (agent invocations)
5. The outbound response message
6. All emitted domain events (via `correlation_id` field)

This enables **end-to-end tracing**: given any correlation ID, reconstruct the full processing chain from inbound message to outbound response, including every LLM call, tool execution, and state mutation.

### 19.3 Audit Trail

The audit trail consists of three complementary sources:

| Source | What It Records | Storage |
|--------|----------------|---------|
| **Event log** (`evt_events`) | Every domain and system event with payloads | Postgres (append-only, partitioned) |
| **Agent invocation log** (`audit_agent_invocations`) | Every LLM call: input, output, model, tokens, latency | Postgres (retention policy) |
| **Workflow execution log** (`orch_workflow_runs` + `orch_step_executions`) | Every workflow run with step-by-step execution trace | Postgres |

### 19.4 What Gets Logged

| Action | Log Level | Audit Table | Details |
|--------|-----------|-------------|---------|
| Message received | INFO | `evt_events` | Channel, content type (not content) |
| Intent classified | INFO | `audit_agent_invocations` | Intent, confidence, model used |
| Memory retrieved | DEBUG | Request trace | Items retrieved, scores |
| Workflow started | INFO | `orch_workflow_runs` | Workflow ID, input summary |
| Agent invoked | INFO | `audit_agent_invocations` | Full input/output, tokens, latency |
| Tool executed | INFO | `orch_step_executions` | Tool ID, input/output, success |
| State mutated | INFO | `evt_events` | Entity type, mutation type, before/after |
| Response sent | INFO | `evt_events` | Channel, delivery status |
| Error occurred | ERROR | `evt_events` + application logs | Full error context, stack trace |

### 19.5 Prompt and Model Version Tracking

Every agent invocation records:
- `prompt_template_id` and `version` from the prompt registry
- `model` used (e.g., "gpt-4o-mini")
- `temperature` and other generation parameters

This enables:
- **Regression detection**: If a prompt version change causes quality degradation.
- **Cost tracking**: Token usage per model per domain.
- **A/B analysis**: Compare outcomes across prompt versions.

### 19.6 Dashboard (Future)

MVP observability is logs + events table. Future dashboard surfaces:
- Request volume and latency graphs
- Token usage and cost per domain
- Workflow success rates
- Memory growth over time
- Top intents and domains
- Error rate trends

---

## 20. Scalability Path

### 20.1 MVP: Single-Instance Modular Monolith

The MVP runs as a **single process** with all modules in-process:

```
┌─────────────────────────────────────────┐
│         Single Docker Compose           │
│                                         │
│  ┌──────────┐  ┌──────────┐             │
│  │ FastAPI  │  │  Worker  │             │
│  │ (API +   │  │ (async   │             │
│  │  webhooks│  │  jobs)   │             │
│  └────┬─────┘  └────┬─────┘             │
│       │              │                  │
│  ┌────▼──────────────▼─────┐            │
│  │      PostgreSQL         │            │
│  │      (+ pgvector)       │            │
│  └─────────────────────────┘            │
│  ┌─────────────────────────┐            │
│  │        Redis            │            │
│  └─────────────────────────┘            │
│  ┌─────────────────────────┐            │
│  │   MinIO (object store)  │            │
│  └─────────────────────────┘            │
└─────────────────────────────────────────┘
```

**Capacity**: ~100 concurrent users, ~10,000 messages/day. Bottleneck is LLM API rate limits, not infrastructure.

### 20.2 Scale Phase 1: Horizontal Workers

When background job processing becomes a bottleneck:

- **Scale workers horizontally**: Run multiple worker instances consuming from the same Redis queue.
- **Separate ingestion workers**: Knowledge ingestion is CPU/IO heavy; give it dedicated workers.
- **Connection pooling**: PgBouncer in front of PostgreSQL.

### 20.3 Scale Phase 2: Read Replicas and Caching

When database reads become a bottleneck:

- **PostgreSQL read replicas**: Route read-heavy queries (retrieval, search) to replicas.
- **Redis caching layer**: Cache frequently accessed data: user profiles, domain configs, recent session states.
- **Embedding cache**: Cache recently computed embeddings to avoid re-computation.

### 20.4 Scale Phase 3: Service Extraction

When the monolith becomes unwieldy for team development:

| Service | Extract When | Boundary |
|---------|-------------|----------|
| **Communication Service** | Multiple channels with different scaling needs | Webhook ingress, message dispatch |
| **Ingestion Service** | Heavy document processing load | Knowledge pipeline workers |
| **Retrieval Service** | Search latency requirements | Vector search + reranking |
| **Scheduler Service** | High volume of scheduled jobs | Job scheduling and dispatch |

**Rule**: Extract a service only when you have a clear scaling or team-ownership reason. Premature extraction adds distributed system complexity without benefit.

### 20.5 Scale Phase 4: Dedicated Vector Database

When pgvector performance degrades with large embedding volumes (>10M vectors):

- Migrate to dedicated vector database (Qdrant, Weaviate, or Pinecone).
- Keep pgvector as the development/staging option.
- Abstract behind the existing `EmbeddingService` / retrieval interface — no domain code changes.

### 20.6 Scaling Limits and Mitigations

| Bottleneck | Threshold | Mitigation |
|------------|-----------|------------|
| LLM API rate limits | ~1000 RPM (OpenAI) | Request queuing, model routing (cheap model for simple tasks), caching common responses |
| PostgreSQL connections | ~200 concurrent | PgBouncer connection pooling |
| pgvector search latency | >100ms at >5M vectors | IVFFlat → HNSW index, dedicated vector DB |
| Redis memory | >4GB | Eviction policies, separate Redis instances for cache vs. queue |
| Object storage | Rarely a bottleneck | S3-compatible, essentially unlimited |
| Worker throughput | Job queue depth >1000 | Horizontal worker scaling |

---

## 21. Suggested Technology Stack

### 21.1 Core Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Language** | Python | 3.12+ | Rich AI/ML ecosystem, fast prototyping, async support |
| **Web framework** | FastAPI | 0.110+ | Async-native, Pydantic integration, OpenAPI generation, excellent typing |
| **Database** | PostgreSQL | 16+ | Mature, reliable, rich feature set (JSONB, RLS, partitioning, tsvector) |
| **Vector store** | pgvector | 0.7+ | Embedded in PostgreSQL — no separate service to manage. HNSW index support. |
| **Cache / Queue** | Redis | 7+ | Session state, pub/sub, job queue, rate limiting — one service, many uses |
| **Object storage** | MinIO (dev) / S3 (prod) | — | S3-compatible API. MinIO for local development, S3 for production. |
| **Task queue** | arq | 0.25+ | Lightweight, Redis-backed, async-native Python job queue. Simpler than Celery for our scale. |

### 21.2 AI / LLM Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **LLM provider** | OpenAI (primary), Anthropic (secondary) | GPT-4o for complex tasks, GPT-4o-mini for classification/parsing. Anthropic as fallback. |
| **LLM abstraction** | LiteLLM | Provider-agnostic LLM client. Supports 100+ models through one interface. |
| **Orchestration** | LangGraph | Graph-based workflow engine with state machines. Supports conditional branching, human-in-the-loop, checkpointing. |
| **Embeddings** | OpenAI text-embedding-3-small | Good quality/cost ratio. 1536 dimensions. Abstracted for future model swaps. |
| **Structured output** | Pydantic + instructor | Type-safe LLM outputs. Instructor library for reliable structured extraction. |

### 21.3 Infrastructure / DevOps

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Containerization** | Docker + Docker Compose | Local dev and single-server deployment |
| **Migrations** | Alembic | Standard SQLAlchemy migration tool |
| **ORM** | SQLAlchemy 2.0 (async) | Mature, typed, async support, excellent PostgreSQL support |
| **Logging** | structlog | Structured JSON logging, easy context binding |
| **Config** | Pydantic Settings | Type-safe configuration from environment variables |
| **Testing** | pytest + pytest-asyncio | Standard Python testing with async support |
| **Linting** | Ruff | Fast, comprehensive Python linter and formatter |
| **Type checking** | mypy (strict) | Catch type errors before runtime |

### 21.4 Communication Channel Libraries

| Channel | Library/API | Notes |
|---------|------------|-------|
| WhatsApp | Meta Cloud API (direct HTTP) | Webhook-based. No SDK needed — direct REST calls. |
| Telegram | python-telegram-bot or aiogram | Webhook mode. aiogram is async-native. |
| REST API | FastAPI endpoints | Native — no additional library. |

### 21.5 Knowledge Ingestion Libraries

| Task | Library | Notes |
|------|---------|-------|
| HTML readability | readability-lxml, trafilatura | Main content extraction from web pages |
| PDF parsing | pymupdf (fitz) | Fast, reliable PDF text extraction |
| HTML parsing | BeautifulSoup4 | Fallback HTML parsing |
| Office docs | python-docx, openpyxl | Word and Excel parsing |
| YouTube transcripts | youtube-transcript-api | Transcript fetching |
| URL fetching | httpx | Async HTTP client |
| Text chunking | langchain text splitters | Recursive character splitter |

### 21.6 Future Additions

| Component | Technology | When |
|-----------|-----------|------|
| **Dashboard** | Next.js + shadcn/ui + TailwindCSS | Phase 3+ |
| **Dedicated vector DB** | Qdrant | Phase 4+ (if pgvector insufficient) |
| **Message broker** | Redis Streams → NATS/Kafka | Phase 4+ (if in-process event bus insufficient) |
| **Monitoring** | Prometheus + Grafana | Phase 2+ |
| **Tracing** | OpenTelemetry + Jaeger | Phase 2+ |
| **CI/CD** | GitHub Actions | Phase 1 |

### 21.7 Why This Stack

**Python over TypeScript/Go**: The AI/ML ecosystem is Python-first. LangGraph, LiteLLM, instructor, and most embedding/RAG tooling is Python-native. The cost of using another language is constant translation overhead.

**FastAPI over Django/Flask**: Async-native (important for LLM calls that are IO-bound), Pydantic integration for request/response validation, automatic OpenAPI docs.

**PostgreSQL + pgvector over separate vector DB**: One fewer service to manage. pgvector is production-ready for moderate scale (<10M vectors). We can migrate to a dedicated vector DB later without changing application code (abstracted interface).

**arq over Celery**: Lighter weight, async-native, Redis-backed. Celery is overkill for our scale and adds complexity (broker, result backend, worker management).

**LangGraph over custom orchestration**: Provides state machine graphs with checkpointing, conditional branching, and human-in-the-loop out of the box. Building this from scratch is 3-6 months of work.

---

## 22. Project Structure

### 22.1 Repository Layout

```
ai-life-os/
├── README.md
├── pyproject.toml                    # Project metadata, dependencies
├── alembic.ini                       # Alembic migration config
├── docker-compose.yml                # Local development stack
├── Dockerfile                        # Application container
├── .env.example                      # Environment variable template
├── .github/
│   └── workflows/
│       ├── ci.yml                    # Lint, type-check, test
│       └── deploy.yml                # Deployment pipeline
│
├── alembic/
│   ├── env.py
│   └── versions/                     # Database migrations
│
├── src/
│   ├── __init__.py
│   ├── main.py                       # FastAPI application entry point
│   ├── config.py                     # Pydantic Settings configuration
│   ├── dependencies.py               # FastAPI dependency injection
│   │
│   ├── core/                         # Core platform entities
│   │   ├── __init__.py
│   │   ├── models.py                 # Tenant, User, TenantUser, Workspace
│   │   ├── schemas.py                # Pydantic schemas
│   │   ├── repository.py             # Database access
│   │   ├── service.py                # Business logic
│   │   └── middleware.py             # Tenant context middleware
│   │
│   ├── communication/                # Communication layer
│   │   ├── __init__.py
│   │   ├── schemas.py                # NormalizedMessage, OutboundMessage
│   │   ├── router.py                 # Webhook endpoints
│   │   ├── dispatcher.py             # Outbound message dispatch
│   │   ├── service.py                # Conversation management
│   │   ├── models.py                 # Channel, Message, Conversation DB models
│   │   ├── repository.py
│   │   └── adapters/
│   │       ├── __init__.py
│   │       ├── base.py               # ChannelAdapter ABC
│   │       ├── whatsapp.py           # WhatsApp adapter
│   │       ├── telegram.py           # Telegram adapter
│   │       └── rest_api.py           # REST API adapter
│   │
│   ├── kernel/                       # AI kernel / control plane
│   │   ├── __init__.py
│   │   ├── orchestrator.py           # Global orchestrator (LangGraph)
│   │   ├── domain_router.py          # Intent classification + domain routing
│   │   ├── response_synthesizer.py   # Final response generation
│   │   ├── policy.py                 # Guardrails and policy layer
│   │   ├── prompt_registry.py        # Prompt template management
│   │   ├── tool_registry.py          # Tool registration and lookup
│   │   └── llm_client.py             # LLM provider abstraction (LiteLLM)
│   │
│   ├── memory/                       # Memory fabric
│   │   ├── __init__.py
│   │   ├── short_term.py             # Redis-backed session state
│   │   ├── structured.py             # Long-term structured memory (SQL)
│   │   ├── semantic.py               # Long-term semantic memory (pgvector)
│   │   ├── assembler.py              # Memory packet assembly
│   │   ├── consolidation.py          # Background memory consolidation
│   │   ├── models.py                 # Memory DB models
│   │   └── repository.py
│   │
│   ├── knowledge/                    # Knowledge ingestion + storage
│   │   ├── __init__.py
│   │   ├── ingestion.py              # Ingestion pipeline orchestrator
│   │   ├── parsers/
│   │   │   ├── __init__.py
│   │   │   ├── html.py               # Web page parser
│   │   │   ├── pdf.py                # PDF parser
│   │   │   ├── document.py           # Office doc parser
│   │   │   └── youtube.py            # YouTube transcript parser
│   │   ├── chunking.py               # Text chunking strategies
│   │   ├── embedding.py              # Embedding service
│   │   ├── tagging.py                # LLM-based tagging and classification
│   │   ├── models.py                 # Knowledge DB models
│   │   └── repository.py
│   │
│   ├── retrieval/                    # RAG / retrieval layer
│   │   ├── __init__.py
│   │   ├── coordinator.py            # Retrieval coordinator
│   │   ├── structured_retriever.py   # SQL-based retrieval
│   │   ├── semantic_retriever.py     # Vector-based retrieval
│   │   ├── keyword_retriever.py      # Full-text search retrieval
│   │   ├── reranker.py               # Result fusion and reranking
│   │   └── schemas.py                # RetrievalRequest, RetrievalResult
│   │
│   ├── orchestration/                # Workflow engine
│   │   ├── __init__.py
│   │   ├── engine.py                 # Workflow execution engine
│   │   ├── models.py                 # WorkflowRun, StepExecution DB models
│   │   ├── repository.py
│   │   └── schemas.py                # WorkflowDefinition, WorkflowStep
│   │
│   ├── agents/                       # Agent runtime
│   │   ├── __init__.py
│   │   ├── runtime.py                # Agent invocation runtime
│   │   ├── registry.py               # Agent registration
│   │   ├── models.py                 # AgentInvocation DB model
│   │   └── schemas.py                # AgentDefinition
│   │
│   ├── scheduling/                   # Scheduler + tasks + reminders
│   │   ├── __init__.py
│   │   ├── scheduler.py              # Job scheduling and dispatch
│   │   ├── worker.py                 # Background job runner
│   │   ├── models.py                 # ScheduledJob, Task, Reminder DB models
│   │   ├── repository.py
│   │   └── schemas.py
│   │
│   ├── events/                       # Event bus
│   │   ├── __init__.py
│   │   ├── bus.py                    # Event publisher/subscriber
│   │   ├── models.py                 # Event DB model
│   │   ├── repository.py
│   │   └── schemas.py                # PlatformEvent schema
│   │
│   ├── connectors/                   # External data connectors
│   │   ├── __init__.py
│   │   ├── base.py                   # Connector ABC
│   │   ├── runtime.py                # Connector execution runtime
│   │   ├── credentials.py            # Encrypted credential management
│   │   ├── models.py
│   │   └── implementations/
│   │       ├── __init__.py
│   │       ├── bank_csv.py           # Manual CSV bank import
│   │       └── apple_health.py       # Apple Health data import
│   │
│   ├── domains/                      # Domain plugin modules
│   │   ├── __init__.py               # Domain registry
│   │   ├── base.py                   # DomainPlugin ABC, DomainOrchestrator ABC
│   │   │
│   │   ├── health/
│   │   │   ├── __init__.py
│   │   │   ├── plugin.py             # HealthPlugin(DomainPlugin)
│   │   │   ├── orchestrator.py       # Health domain orchestrator
│   │   │   ├── workflows.py          # Workflow definitions
│   │   │   ├── agents.py             # Agent definitions (meal_parser, etc.)
│   │   │   ├── tools.py              # Deterministic tools
│   │   │   ├── prompts.py            # Prompt templates
│   │   │   ├── models.py             # Health DB models (Meal, Workout, etc.)
│   │   │   ├── schemas.py            # Pydantic schemas
│   │   │   ├── repository.py
│   │   │   └── service.py            # Deterministic business logic
│   │   │
│   │   ├── finance/
│   │   │   ├── __init__.py
│   │   │   ├── plugin.py
│   │   │   ├── orchestrator.py
│   │   │   ├── workflows.py
│   │   │   ├── agents.py
│   │   │   ├── tools.py
│   │   │   ├── prompts.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   │
│   │   ├── tutor/
│   │   │   ├── __init__.py
│   │   │   ├── plugin.py
│   │   │   ├── orchestrator.py
│   │   │   ├── workflows.py
│   │   │   ├── agents.py
│   │   │   ├── tools.py
│   │   │   ├── prompts.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   │
│   │   ├── education/
│   │   │   └── ...                   # Same structure
│   │   │
│   │   └── return_later/
│   │       └── ...                   # Same structure
│   │
│   └── shared/                       # Shared utilities
│       ├── __init__.py
│       ├── database.py               # Database engine, session factory
│       ├── base_model.py             # SQLAlchemy base with tenant_id, timestamps
│       ├── pagination.py             # Pagination utilities
│       ├── crypto.py                 # Encryption/decryption helpers
│       └── time.py                   # Timezone utilities
│
├── tests/
│   ├── conftest.py                   # Shared fixtures
│   ├── factories.py                  # Test data factories
│   ├── unit/
│   │   ├── test_communication/
│   │   ├── test_kernel/
│   │   ├── test_memory/
│   │   ├── test_retrieval/
│   │   ├── test_domains/
│   │   └── ...
│   ├── integration/
│   │   ├── test_workflows/
│   │   ├── test_ingestion/
│   │   └── ...
│   └── e2e/
│       ├── test_whatsapp_flow.py
│       ├── test_telegram_flow.py
│       └── ...
│
└── scripts/
    ├── seed_dev_data.py              # Seed development database
    ├── run_migration.py              # Migration helper
    └── test_llm_connection.py        # Verify LLM API connectivity
```

### 22.2 Module Dependency Rules

```
Communication ──► Kernel ──► Memory
                    │         │
                    ▼         ▼
              Orchestration  Retrieval
                    │         │
                    ▼         ▼
                 Domains ──► Events
                    │
                    ▼
                Connectors

Rules:
1. Domains depend on kernel contracts, NEVER on other domains.
2. Kernel depends on memory and retrieval abstractions, not implementations.
3. Communication depends on kernel for dispatching, never on domains directly.
4. Events are depended on by everyone (lightweight, no circular deps).
5. Connectors depend on events (for publishing) and domains (for schema awareness).
6. Shared utilities are depended on by everything, depend on nothing.
```

---

## 23. Domain Module Contracts

### 23.1 Contract Summary

Every domain module must provide the following artifacts through the `DomainPlugin` interface:

| Artifact | Required | Description |
|----------|----------|-------------|
| **Manifest** | Yes | Domain ID, name, version, capabilities, dependencies |
| **Orchestrator** | Yes | Handles classified intents and scheduled jobs |
| **Workflows** | Yes | At least one workflow definition per supported intent |
| **Tools** | Yes | Deterministic tools and/or agent-backed tools |
| **Prompts** | Yes | Prompt templates for all LLM-based steps |
| **Scheduled jobs** | No | Recurring jobs (daily check-ins, reviews, etc.) |
| **DB models** | Yes | SQLAlchemy models for domain entities |
| **Migrations** | Yes | Alembic migrations for domain tables |
| **Repository** | Yes | Data access layer for domain entities |
| **Service** | Yes | Deterministic business logic |
| **Schemas** | Yes | Pydantic models for domain data |

### 23.2 Intent Contract

Each domain declares the intents it handles. The kernel's domain router uses these declarations for classification.

```python
# Example: Health domain intent declarations
HEALTH_INTENTS = [
    IntentDeclaration(
        intent_id="health.log_meal",
        description="User wants to log a meal, food, or snack they ate",
        example_messages=[
            "I had chicken salad for lunch",
            "Log breakfast: 2 eggs and toast",
            "Just ate a banana",
            "Had pizza for dinner, about 3 slices",
        ],
        keywords=["ate", "eaten", "meal", "breakfast", "lunch", "dinner", "snack", "food"],
        workflow_id="health.log_meal",
    ),
    IntentDeclaration(
        intent_id="health.log_workout",
        description="User wants to log a workout or exercise session",
        example_messages=[
            "Just finished a 5km run",
            "Did 30 minutes of yoga",
            "Went to the gym, did chest and back",
        ],
        keywords=["workout", "exercise", "run", "gym", "yoga", "swim", "bike"],
        workflow_id="health.log_workout",
    ),
    IntentDeclaration(
        intent_id="health.log_mood",
        description="User wants to log their mood or emotional state",
        example_messages=[
            "Feeling great today",
            "I'm stressed about work",
            "Mood is low, tired and unmotivated",
        ],
        keywords=["mood", "feeling", "stressed", "happy", "sad", "anxious", "tired", "energy"],
        workflow_id="health.log_mood",
    ),
    IntentDeclaration(
        intent_id="health.get_summary",
        description="User wants to see their health summary or stats",
        example_messages=[
            "How's my health this week?",
            "Show me what I ate today",
            "Give me my weekly health summary",
        ],
        keywords=["summary", "stats", "progress", "report", "how am I doing"],
        workflow_id="health.generate_summary",
    ),
]
```

### 23.3 Workflow Contract

Each workflow must define its steps with explicit types, input/output mappings, and error handlers.

```python
# Example: Health domain workflow definition
HEALTH_WORKFLOWS = [
    WorkflowDefinition(
        workflow_id="health.log_meal",
        domain="health",
        name="Log Meal",
        description="Parse, validate, calculate nutrition, and store a meal",
        trigger_intents=["health.log_meal"],
        timeout_seconds=60,
        steps=[
            WorkflowStep(
                step_id="parse",
                step_type=StepType.LLM_CALL,
                agent_or_tool_id="health.meal_parser",
                input_mapping={"user_message": "$.input.text", "context": "$.memory"},
                output_mapping={"meal_data": "$.parse.output"},
                next_step="validate",
                error_handler="parse_error",
            ),
            WorkflowStep(
                step_id="validate",
                step_type=StepType.DETERMINISTIC,
                agent_or_tool_id="health.meal_validator",
                input_mapping={"meal_data": "$.parse.output"},
                output_mapping={"validated_meal": "$.validate.output"},
                next_step="calculate_nutrition",
            ),
            WorkflowStep(
                step_id="calculate_nutrition",
                step_type=StepType.DETERMINISTIC,
                agent_or_tool_id="health.nutrition_calculator",
                input_mapping={"meal_data": "$.validate.output"},
                output_mapping={"nutrition": "$.nutrition.output"},
                next_step="store",
            ),
            WorkflowStep(
                step_id="store",
                step_type=StepType.DETERMINISTIC,
                agent_or_tool_id="health.meal_store",
                input_mapping={
                    "meal_data": "$.validate.output",
                    "nutrition": "$.nutrition.output",
                },
                output_mapping={"meal_id": "$.store.output.id"},
                next_step=None,  # End
            ),
        ],
    ),
]
```

### 23.4 Tool Contract

```python
# Example: Health domain tools
HEALTH_TOOLS = [
    ToolDefinition(
        tool_id="health.meal_validator",
        domain="health",
        name="Validate Meal Data",
        description="Validates and normalizes parsed meal data",
        parameters_schema={
            "type": "object",
            "properties": {
                "meal_data": {"type": "object"},
            },
            "required": ["meal_data"],
        },
        requires_confirmation=False,
        is_deterministic=True,
        handler="src.domains.health.tools.validate_meal",
    ),
    ToolDefinition(
        tool_id="health.nutrition_calculator",
        domain="health",
        name="Calculate Nutrition",
        description="Calculates calories and macros for a validated meal",
        parameters_schema={
            "type": "object",
            "properties": {
                "meal_data": {"type": "object"},
            },
            "required": ["meal_data"],
        },
        requires_confirmation=False,
        is_deterministic=True,
        handler="src.domains.health.tools.calculate_nutrition",
    ),
]
```

### 23.5 Event Contract

Each domain declares which events it emits and which events it listens to:

```python
# Health domain event declarations
HEALTH_EVENTS_EMITTED = [
    "health.meal_logged",
    "health.workout_completed",
    "health.workout_skipped",
    "health.mood_logged",
    "health.metric_recorded",
    "health.goal_updated",
    "health.daily_summary_generated",
]

HEALTH_EVENTS_SUBSCRIBED = [
    "system.daily_trigger",          # For daily check-in
    "system.weekly_trigger",         # For weekly summary
    "finance.transaction_imported",  # Correlate food spending with meals
]
```

---

## 24. Example Domain Implementations

### 24.1 Health Domain

**Purpose**: Track meals, workouts, mood, body metrics, and health goals. Provide insights and patterns.

**Entities**: Meals, Meal Items, Workouts, Mood Entries, Body Metrics, Health Goals, Health Conditions (informational only)

**Key Workflows**:
- `health.log_meal` — Parse and store meals with nutrition estimates
- `health.log_workout` — Parse and store workouts
- `health.log_mood` — Parse and store mood entries with energy level
- `health.record_metric` — Store body metrics (weight, blood pressure, etc.)
- `health.generate_summary` — Daily/weekly/monthly health summaries
- `health.set_goal` — Create or update health goals

**Agents**: `meal_parser`, `workout_parser`, `mood_parser`, `health_summarizer`, `health_insight_generator`

**Deterministic Services**: `nutrition_calculator`, `goal_progress_checker`, `metric_trend_calculator`

**Scheduled Jobs**:
- Morning check-in (daily, 9am)
- Weekly health summary (Sunday, 6pm)

**Safety**: Never diagnoses. Never prescribes. Adds disclaimers to health suggestions. Flags concerning patterns for professional review.

### 24.2 Finance Domain

**Purpose**: Track expenses, income, budgets, investments, and financial goals. Provide spending insights and budget adherence.

**Entities**: Accounts, Transactions, Categories, Budgets, Budget Periods, Investments, Financial Goals

**Key Workflows**:
- `finance.log_expense` — Parse and store an expense
- `finance.log_income` — Parse and store income
- `finance.import_transactions` — Import from CSV or connector
- `finance.categorize_transaction` — Classify a transaction
- `finance.generate_report` — Weekly/monthly financial report
- `finance.check_budget` — Check budget status
- `finance.set_budget` — Create or update a budget

**Agents**: `expense_parser`, `transaction_categorizer`, `finance_summarizer`, `budget_analyzer`

**Deterministic Services**: `balance_calculator`, `budget_tracker`, `investment_return_calculator`, `currency_converter`

**Scheduled Jobs**:
- Evening expense reminder (daily, 8pm)
- Weekly finance review (Saturday, 10am)
- Monthly financial report (1st of month, 9am)

**Safety**: All calculations deterministic. Investment insights labeled as informational. No real transaction execution.

### 24.3 Tutor Domain (Language Learning)

**Purpose**: Support language learning (Dutch and others) through vocabulary practice, grammar exercises, reading practice, and spaced repetition.

**Entities**: Languages, Vocabulary Items, Vocabulary Reviews, Grammar Topics, Lessons, Study Sessions, Reading Assignments

**Key Workflows**:
- `tutor.daily_vocab_quiz` — Generate and run a spaced repetition vocabulary quiz
- `tutor.explain_grammar` — Explain a grammar concept with examples
- `tutor.practice_conversation` — Conversational practice in target language
- `tutor.assign_reading` — Suggest a reading from captured knowledge
- `tutor.review_progress` — Study progress summary

**Agents**: `quiz_generator`, `grammar_explainer`, `conversation_partner`, `reading_recommender`, `progress_analyzer`

**Deterministic Services**: `spaced_repetition_scheduler` (SM-2 algorithm), `progress_tracker`, `difficulty_adjuster`

**Scheduled Jobs**:
- Daily vocabulary practice (daily, 8am)
- Spaced repetition reviews (per-item, calculated by SM-2)
- Weekly study progress report (Sunday, 6pm)

**Cross-Domain**: Reads from knowledge memory for reading practice material. Listens to `rl.document_processed` events to detect new content in the target language.

### 24.4 Education / Study Planning Domain

**Purpose**: Plan and track study activities across subjects. Manage learning goals, study sessions, and progress.

**Entities**: Subjects, Study Plans, Study Sessions, Learning Goals, Resources, Progress Records

**Key Workflows**:
- `education.log_study_session` — Log time spent studying
- `education.create_study_plan` — Generate a study plan for a subject/goal
- `education.track_progress` — View progress toward learning goals
- `education.get_recommendations` — Suggest next study topics

**Agents**: `study_plan_generator`, `progress_analyzer`, `resource_recommender`

**Deterministic Services**: `study_time_tracker`, `goal_progress_calculator`, `schedule_optimizer`

### 24.5 Return-Later / Link Capture Domain

**Purpose**: Capture, process, organize, and surface captured links, articles, and documents.

**Entities**: Captured Items, Reading Queue, Annotations, Collections, Tags

**Key Workflows**:
- `return_later.capture` — Capture a URL or document (triggers ingestion pipeline)
- `return_later.get_reading_list` — Show reading queue with recommendations
- `return_later.search_knowledge` — Search captured knowledge
- `return_later.summarize` — Get a summary of a captured item
- `return_later.annotate` — Add a note to a captured item

**Agents**: `reading_recommender`, `summary_presenter`, `knowledge_searcher`

**Deterministic Services**: `queue_manager`, `tag_manager`, `collection_manager`

**Scheduled Jobs**:
- Evening reading digest (daily, 7pm)
- Stale items reminder (monthly, 1st)

**Cross-Domain**: This domain primarily **produces** knowledge that other domains consume. It owns the ingestion trigger and reading queue, while the knowledge storage itself is a shared kernel service.

---

## 25. Example Workflows

### 25.1 Health Message on WhatsApp

```
User sends via WhatsApp: "Had a chicken caesar salad for lunch, about 350g"

1. CHANNEL ADAPTER (WhatsApp)
   → Webhook received from Meta Cloud API
   → Signature verified
   → Parsed into NormalizedInboundEvent:
     {
       channel_type: "whatsapp",
       channel_user_id: "+31612345678",
       content_type: "text",
       text: "Had a chicken caesar salad for lunch, about 350g",
       idempotency_key: "wamid.xxx_1711234567"
     }

2. COMMUNICATION SERVICE
   → Dedup check (idempotency_key not seen) ✓
   → Resolve ChannelIdentity → platform_user_id: "user_abc"
   → Find or create Conversation
   → Store Message in DB
   → Publish event: system.user_message_received

3. GLOBAL ORCHESTRATOR
   → Load session state from Redis (no active workflow)
   → Load user profile: {name: "Yash", timezone: "Europe/Amsterdam", health_goals: [...]}

4. DOMAIN ROUTER (LLM call)
   → Input: message text + registered domain capabilities
   → Output: {primary_domain: "health", intent: "health.log_meal", confidence: 0.95}

5. MEMORY ASSEMBLER
   → Load today's meals (structured memory): [breakfast: 2 eggs + toast, 380 cal]
   → Load health goals: [daily_calories: 2000, protein: 120g]
   → Load recent semantic memory: "User prefers concise meal confirmations"
   → Assemble MemoryPacket (within token budget)

6. HEALTH DOMAIN ORCHESTRATOR
   → Select workflow: health.log_meal
   → Execute step 1: PARSE (LLM)
     Agent: health.meal_parser
     Input: "Had a chicken caesar salad for lunch, about 350g" + context
     Output: {
       meal_type: "lunch",
       items: [
         {name: "chicken caesar salad", quantity: 350, unit: "g"}
       ]
     }
   → Execute step 2: VALIDATE (deterministic)
     Normalize units, check for sanity
   → Execute step 3: CALCULATE NUTRITION (deterministic)
     Lookup nutrition database
     Output: {calories: 520, protein: 38, carbs: 15, fat: 32}
   → Execute step 4: CHECK GOALS (deterministic)
     Today's total: 380 + 520 = 900 cal
     Goal: 2000 cal → remaining: 1100 cal
     Status: on_track
   → Execute step 5: STORE (deterministic)
     Insert into health_meals table
     Emit event: health.meal_logged

7. RESPONSE SYNTHESIZER (LLM)
   → Input: meal data + nutrition + goal status + user preference for brevity
   → Output: "Logged your chicken caesar salad (520 cal, 38g protein).
              You're at 900/2000 cal today — 1100 remaining. 👍"

8. OUTBOUND DISPATCH
   → Route to WhatsApp adapter
   → Send via Meta Cloud API
   → Store outbound message + delivery receipt

9. EVENTS EMITTED
   → system.user_message_received
   → health.meal_logged {meal_type: "lunch", calories: 520, ...}
   → system.response_sent
   → system.workflow_completed {workflow: "health.log_meal", duration_ms: 1800}
```

### 25.2 Finance Question on Telegram

```
User sends via Telegram: "How much have I spent on dining out this month?"

1. CHANNEL ADAPTER (Telegram)
   → Webhook received
   → Token verified
   → NormalizedInboundEvent created

2. COMMUNICATION SERVICE
   → Resolve user, store message, publish event

3. GLOBAL ORCHESTRATOR
   → Load session state, user profile

4. DOMAIN ROUTER
   → {primary_domain: "finance", intent: "finance.check_spending", confidence: 0.92}

5. MEMORY ASSEMBLER
   → Load current month's dining transactions (structured query)
   → Load budget for "dining" category: €200/month
   → Load semantic memory: "User tracks dining spending closely"

6. FINANCE DOMAIN ORCHESTRATOR
   → Select workflow: finance.check_spending
   → Execute step 1: QUERY TRANSACTIONS (deterministic)
     SQL: SELECT SUM(amount) FROM fin_transactions
          WHERE category = 'dining' AND month = current_month
     Result: €187.50, 12 transactions
   → Execute step 2: COMPARE TO BUDGET (deterministic)
     Budget: €200, Spent: €187.50, Remaining: €12.50
     Status: warning (93.75% used)
   → Execute step 3: TOP EXPENSES (deterministic)
     Top 3: Restaurant A (€45), Restaurant B (€38), Delivery C (€32)

7. RESPONSE SYNTHESIZER
   → "You've spent €187.50 on dining out this month across 12 transactions.
      That's 93.75% of your €200 budget — only €12.50 remaining.
      
      Top spots: Restaurant A (€45), Restaurant B (€38), Delivery C (€32).
      
      ⚠️ You're close to your dining budget. Want me to alert you before
      you exceed it?"

8. OUTBOUND DISPATCH → Telegram
```

### 25.3 Link Captured on WhatsApp, Used Later by Education

```
=== Phase 1: Link Capture ===

User sends via WhatsApp: "Save this for later: https://arxiv.org/abs/2301.xxxxx"

1. COMMUNICATION → ORCHESTRATOR → DOMAIN ROUTER
   → {primary_domain: "return_later", intent: "return_later.capture"}

2. RETURN-LATER DOMAIN ORCHESTRATOR
   → Execute workflow: return_later.capture
   → Step 1: Extract URL from message
   → Step 2: Quick acknowledge ("Captured! I'll process it shortly.")
   → Step 3: Queue ingestion job (async)

3. INGESTION WORKER (background)
   → Fetch arxiv page
   → Extract paper: "Attention-Based Learning for Long Sequences"
   → Parse PDF → extract text
   → Chunk (23 chunks)
   → Embed chunks
   → Tag: {domains: ["education", "ai"], topics: ["attention", "transformers", "ML"]}
   → Summarize: "This paper proposes a new attention mechanism for..."
   → Store in know_documents + know_chunks
   → Emit: rl.document_processed {domains: ["education", "ai"]}

4. EVENT CONSUMER: Education domain
   → Sees rl.document_processed with domain "education"
   → Adds to study resources for ML subject

=== Phase 2: Education Usage (days later) ===

User sends via Telegram: "What do I know about attention mechanisms?"

1. DOMAIN ROUTER → {primary_domain: "education", intent: "education.search_knowledge"}

2. MEMORY ASSEMBLER
   → Semantic search: "attention mechanisms"
   → Retrieves chunks from the captured arxiv paper
   → Also retrieves study session notes about transformers

3. EDUCATION ORCHESTRATOR
   → Synthesize response using retrieved knowledge
   → "Based on a paper you saved (Attention-Based Learning for Long
      Sequences, arxiv 2301.xxxxx):
      - Key idea: [summary of main contribution]
      - Relevance: Extends the transformer attention you studied last week
      - Suggested next step: Read sections 3-4 on the novel mechanism
      
      Want me to create a study session for this paper?"
```

### 25.4 Dutch Tutor Daily Exercise on Telegram

```
=== Scheduled Job Trigger (8:00 AM, user's timezone) ===

1. SCHEDULER
   → Job: tutor.daily_vocab_quiz fires
   → Load tenant context for user
   → Dispatch to Tutor domain orchestrator

2. MEMORY ASSEMBLER
   → Load vocabulary items due for review (SM-2 algorithm)
   → Load recent performance: "85% accuracy last 3 days"
   → Load semantic memory: "User struggles with irregular verbs"

3. TUTOR DOMAIN ORCHESTRATOR
   → Select workflow: tutor.daily_vocab_quiz
   → Step 1: SELECT REVIEW ITEMS (deterministic)
     SM-2 scheduler selects 10 words due for review
     Bias toward irregular verbs (user weakness)
   → Step 2: GENERATE QUIZ (LLM)
     Agent: tutor.quiz_generator
     Input: 10 vocabulary items + user level + preferred format
     Output: Interactive quiz with context sentences

4. OUTBOUND MESSAGE (Telegram)
   → "🇳🇱 Good morning! Time for your Dutch vocabulary practice.
   
      1/10: What does 'vergeten' mean?
      (hint: it's an irregular verb)
      
      Reply with your answer!"

5. USER REPLIES: "to forget"

6. TUTOR ORCHESTRATOR (continuing workflow)
   → Step 3: EVALUATE ANSWER (deterministic)
     Correct! "vergeten" = "to forget"
   → Step 4: UPDATE SR SCHEDULE (deterministic)
     Mark as correct, extend interval (SM-2: ease_factor 2.6, next in 4 days)
   → Step 5: NEXT QUESTION or FINISH
     → Continue with question 2/10...

7. AFTER QUIZ COMPLETE:
   → Score: 8/10
   → Missed: "hebben" conjugation, "geweest" context
   → Schedule missed items for review tomorrow
   → Emit: tutor.vocab_reviewed {words: 10, correct: 8, language: "dutch"}
   → "Great job! 8/10 today. Keep it up! 🎯
      I'll review 'hebben' and 'geweest' again tomorrow."
```

### 25.5 Cross-Domain Retrieval: Life Tracker + Health + Education

```
User sends: "I've been feeling unproductive lately. What's going on?"

1. DOMAIN ROUTER
   → Multi-domain: {primary: "health" (mood/energy), secondary: ["education", "finance"]}
   → Intent: cross_domain.life_analysis

2. MEMORY ASSEMBLER (cross-domain retrieval)
   → Health events (last 14 days):
     - Mood: declining trend (avg 7→5 over 2 weeks)
     - Sleep: irregular (varied 5-9 hours)
     - Workouts: 1 this week (usually 3)
     - Meals: irregular timing, more takeout
   → Education events (last 14 days):
     - Study sessions: 2 (usually 5)
     - Dutch practice: skipped 4 of last 7 days
   → Finance events (last 14 days):
     - Food delivery spending: +40% vs. previous 2 weeks
   → Semantic memory:
     - "User's productivity correlates with regular sleep and exercise"
     - "User tends to skip workouts when stressed about work"
   → Event log:
     - 8 days ago: "mood_logged: stressed, reason: project deadline"

3. GLOBAL ORCHESTRATOR
   → Invokes cross-domain analysis agent
   → Agent synthesizes across all retrieved data

4. RESPONSE:
   → "Looking at your last two weeks, I can see some patterns:

      📊 **What's changed:**
      - Your mood has trended down (7→5 avg)
      - Sleep has been irregular (5-9 hours, vs. your usual 7-8)
      - You've only worked out once (usually 3x/week)
      - Study sessions dropped from 5 to 2
      - You skipped Dutch practice 4 times
      - Food delivery spending is up 40%

      🔍 **Possible pattern:**
      About 8 days ago you mentioned stress about a project deadline.
      In the past, I've noticed your workouts and study habits slip
      when you're under work pressure, and that tends to compound
      (less exercise → lower energy → less studying → lower mood).

      💡 **Small steps that have worked before:**
      1. A short 20-min walk (you've said this helps reset your mood)
      2. Getting back to your regular 11pm sleep time
      3. Even a 5-min Dutch vocab review to maintain the streak

      Want me to set up gentle reminders for any of these?"
```

---

## 26. Implementation Phases

### Phase 0: Kernel Foundation (Weeks 1-3)

**Goal**: Runnable skeleton with core infrastructure.

**Deliverables:**
- Project scaffolding (repo structure, Docker Compose, CI)
- PostgreSQL + pgvector + Redis setup
- SQLAlchemy base models with tenant_id, timestamps
- Alembic migration framework
- FastAPI app skeleton with health check
- Pydantic Settings configuration
- Core entities: Tenant, User, TenantUser (single tenant seeded)
- Event bus (in-process)
- Event persistence (evt_events table)
- Structured logging with structlog
- Basic LLM client abstraction (LiteLLM wrapper)
- Prompt registry (file-based, versioned)
- Tool registry (code-based)

**Validation**: `docker-compose up` starts all services. Health check returns 200. Events can be published and persisted.

---

### Phase 1: Communication + Memory + Health + Return-Later (Weeks 4-8)

**Goal**: First working end-to-end flow — user sends a message on WhatsApp, gets an intelligent response.

**Deliverables:**

*Communication:*
- WhatsApp adapter (Meta Cloud API webhooks)
- Normalized message schema
- Conversation and message persistence
- Identity resolution (channel identity → platform user)
- Outbound message dispatch
- Idempotency handling

*Kernel:*
- Global orchestrator (LangGraph state machine)
- Domain router (intent classification)
- Memory assembler (basic version)
- Response synthesizer
- Basic policy/guardrail layer

*Memory:*
- Short-term memory (Redis session state)
- Long-term structured memory (user profile, domain entities)
- Event / life log (append-only event table)

*Knowledge:*
- Ingestion pipeline (URL → fetch → parse → chunk → embed → store)
- Embedding service (OpenAI text-embedding-3-small)
- Basic retrieval (semantic search via pgvector)

*Domains:*
- Health domain (meal logging, mood logging, basic summary)
- Return-later domain (link capture, reading queue, basic search)

*Scheduling:*
- Basic scheduler (cron jobs via arq)
- Health daily check-in job

**Validation**: Send "I had pasta for lunch" on WhatsApp → get meal logged response with calories. Send a URL → get "captured" confirmation → search for it later.

---

### Phase 2: Telegram + Tutor + Education + Retrieval (Weeks 9-13)

**Goal**: Second channel, two more domains, and improved retrieval.

**Deliverables:**

*Communication:*
- Telegram adapter (webhook mode)
- Cross-channel identity linking

*Retrieval:*
- Hybrid retrieval (semantic + keyword + structured)
- Reranking with multi-signal scoring
- Domain-filtered retrieval
- Recency-aware retrieval

*Memory:*
- Long-term semantic memory (conversation summaries, patterns)
- Memory consolidation background jobs (session summary, daily patterns)

*Domains:*
- Tutor domain (Dutch vocabulary, spaced repetition, quiz generation)
- Education domain (study session logging, progress tracking)

*Scheduling:*
- Spaced repetition scheduling (SM-2 algorithm)
- Tutor daily practice job
- Education study reminders

**Validation**: Daily Dutch quiz arrives on Telegram at 8am. Spaced repetition adjusts intervals based on answers. Study sessions tracked across subjects.

---

### Phase 3: Finance + REST API + Connectors (Weeks 14-18)

**Goal**: Financial domain, API access, and external data integrations.

**Deliverables:**

*Communication:*
- REST API adapter (full CRUD API for all domains)
- API authentication (JWT)

*Domains:*
- Finance domain (expense logging, transaction import, budgets, reports)

*Connectors:*
- Connector framework (interface, runtime, credential management)
- Bank CSV import connector
- Apple Health import connector (optional)

*Scheduling:*
- Finance daily expense reminder
- Weekly and monthly finance reports

*Knowledge:*
- Improved tagging and entity extraction
- Knowledge graph relationships

**Validation**: Import bank CSV → transactions auto-categorized → budget tracking works. Weekly finance report generated and sent.

---

### Phase 4: Cross-Domain Intelligence (Weeks 19-24)

**Goal**: The system becomes smarter by connecting data across domains.

**Deliverables:**

*Memory:*
- Cross-domain pattern detection (background consolidation jobs)
- Behavioral insight generation
- Proactive suggestions based on patterns

*Retrieval:*
- Relationship-aware retrieval (follow entity/topic links)
- Importance-aware retrieval (adaptive scoring based on user engagement)

*Kernel:*
- Cross-domain workflows (life review, cross-domain analysis)
- Multi-domain intent handling (single message → multiple domains)
- Proactive outreach (system-initiated messages based on patterns)

*Observability:*
- Prometheus metrics
- OpenTelemetry tracing
- Structured dashboard data exports

**Validation**: "Why am I unproductive?" triggers cross-domain analysis pulling from health, education, finance, and mood data. Weekly life review synthesizes across all domains.

---

### Phase 5: Multi-Tenant Hardening + Scale (Weeks 25-32)

**Goal**: Platform is ready for multiple users.

**Deliverables:**

*Multi-Tenancy:*
- Tenant provisioning API
- User registration and invitation
- Workspace management
- PostgreSQL Row-Level Security enforcement
- Per-tenant configuration overrides
- RBAC enforcement

*Security:*
- Full auth flow (registration, login, token refresh, password reset)
- API rate limiting per tenant
- PII handling audit
- Data deletion workflow

*Scale:*
- Horizontal worker scaling
- PgBouncer connection pooling
- Redis caching layer
- Performance benchmarking

*Dashboard:*
- Next.js admin dashboard (basic)
- User settings, domain configuration
- Usage analytics

**Validation**: Two separate tenants with different users, domains, and data. No data leakage between tenants (verified by test suite). System handles 50 concurrent users without degradation.

---

## 27. Risks and Tradeoffs

### 27.1 Technical Risks

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| **LLM API reliability** | High | Medium | Fallback models (OpenAI → Anthropic). Graceful degradation for non-critical LLM calls. Queue-based retry. |
| **LLM cost escalation** | High | High | Model routing (cheap models for simple tasks). Token budgets per workflow. Caching common responses. Usage monitoring and alerts. |
| **pgvector scale limits** | Medium | Low (MVP) | Abstract behind interface. Migration path to Qdrant documented. Threshold monitoring. |
| **Prompt quality drift** | Medium | Medium | Versioned prompt registry. A/B testing framework. Regression detection via output quality scoring. |
| **Hallucination in critical domains** | High | Medium | Deterministic services for calculations and state mutations. Output validation. Mandatory disclaimers for health/finance. |
| **Schema evolution complexity** | Medium | High | Alembic migrations. JSONB for extensible fields. Domain-namespaced tables to reduce coupling. |
| **Ingestion pipeline failures** | Medium | Medium | Async processing with retry. Dead letter queue. Partial success tracking. User notification on failure. |
| **Memory bloat over time** | Medium | Medium | Retention policies. Memory consolidation (summarize and archive). Importance-based pruning. Partition old data. |

### 27.2 Architectural Tradeoffs

| Decision | Tradeoff | Rationale |
|----------|----------|-----------|
| **Modular monolith over microservices** | Harder to scale individual components independently. | Solo/small team. Avoids distributed system complexity (networking, deployment, consistency). Clean module boundaries allow future extraction. |
| **PostgreSQL for everything (SQL + vector + full-text)** | No specialized optimization for any one workload. | Operational simplicity. One database to manage, backup, monitor. pgvector and tsvector are "good enough" for moderate scale. |
| **Redis for everything (cache + queue + session + pub/sub)** | Redis is a SPOF. Data loss on restart for non-persisted data. | Session state is ephemeral (acceptable loss). Queues use Redis persistence. Cache is rebuilable. Simplicity over redundancy for MVP. |
| **LangGraph for orchestration** | Vendor dependency. Learning curve. May be overkill for simple workflows. | Provides state machines, checkpointing, human-in-the-loop for free. Building equivalent from scratch is months of work. Well-maintained, active community. |
| **Shared memory fabric over domain-isolated data** | Domains can potentially access data they shouldn't. More complex access control. | Cross-domain intelligence is a core value proposition. Isolation enforced by policy and scoping rules, not physical separation. |
| **Event-driven architecture** | Eventual consistency for cross-domain reactions. Debugging can be harder. | Decouples domains. Enables auditability and replay. Essential for cross-domain intelligence. In-process bus for MVP limits consistency issues. |
| **LLM for intent classification over rule-based** | Slower, costs money, non-deterministic. | Handles ambiguity, new domains, and natural language variation. Rule-based fast-path for obvious cases mitigates latency. |
| **Multi-tenant schema from day 1** | Slightly more complex queries (tenant_id everywhere). Overhead for a single user. | Avoids painful schema migration later. tenant_id column is near-zero overhead. Enables family/multi-user without redesign. |

### 27.3 Product Risks

| Risk | Mitigation |
|------|------------|
| **User adoption friction** | Start with the simplest possible interaction: send a WhatsApp message, get value. No app install, no login flow. |
| **Too many domains, none polished** | Phase implementation. Each phase fully polishes 1-2 domains before moving on. Health and Return-Later first. |
| **Users don't trust AI with sensitive data** | Transparent about what data is stored. PII handling documented. Deletion capability. Open source option for self-hosting. |
| **Cross-domain intelligence is creepy, not helpful** | Opt-in cross-domain insights. User controls what domains can see. Clear explanation of why a connection was made. |
| **Notification fatigue** | Conservative defaults for scheduled jobs. User-configurable frequency. Adaptive scheduling based on engagement patterns. |

### 27.4 Operational Risks

| Risk | Mitigation |
|------|------------|
| **Channel API changes (WhatsApp, Telegram)** | Adapter pattern isolates changes. Only the adapter needs updating. |
| **LLM provider pricing changes** | LiteLLM abstraction allows model swaps. Budget monitoring and alerts. |
| **Data loss** | PostgreSQL backups (daily). WAL archiving. Object storage versioning. Redis persistence for queue data. |
| **Single developer bus factor** | Team handoff doc (this document). Clean architecture with conventions. Comprehensive test suite. |

---

*End of System Design Document*

*Companion document: [SCHEMA_DESIGN.md](./SCHEMA_DESIGN.md) — Full database schema definitions*
