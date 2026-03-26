"""
Product requirements for the Platform Kernel (cross-cutting).

These requirements apply to the generic kernel, not any specific domain.
Each requirement has: id, title, description, acceptance_criteria, priority, test_ids.
"""

REQUIREMENTS = [
    {
        "id": "REQ-PLAT-001",
        "title": "Single-User Data Model",
        "description": "All data belongs to the single user running the application. No multi-tenancy overhead.",
        "acceptance_criteria": [
            "All SQLAlchemy models inherit TimestampedBase with standard columns",
            "No tenant_id or user_id filtering in repository queries",
            "Session-based context for conversation tracking",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-PLAT-002",
        "title": "Event Bus Decoupling",
        "description": "Modules communicate via events, not direct imports. Publishing an event triggers all subscribers.",
        "acceptance_criteria": [
            "EventBus supports exact and wildcard subscriptions",
            "Publishing fires all matching handlers",
            "Handler errors do not block other handlers",
            "All events are logged to EventLog for audit",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-PLAT-003",
        "title": "Three-Layer Memory System",
        "description": "AI has short-term (Redis), structured (SQL), and semantic (pgvector) memory layers.",
        "acceptance_criteria": [
            "Short-term memory stores current session context in Redis with TTL",
            "Structured memory stores key-value facts with categories and confidence",
            "Semantic memory stores vector embeddings for fuzzy recall",
            "MemoryAssembler combines all three into a MemoryPacket",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-PLAT-004",
        "title": "Hybrid RAG Retrieval",
        "description": "Retrieval module combines semantic, structured, and keyword search with reranking.",
        "acceptance_criteria": [
            "Semantic retriever uses pgvector cosine similarity",
            "Structured retriever queries SQL facts",
            "Keyword retriever uses PostgreSQL full-text search",
            "Reranker combines scores using relevance, recency, importance, diversity",
            "HYBRID strategy uses all three retrievers",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-PLAT-005",
        "title": "Agent ReAct Loop",
        "description": "Agents execute a ReAct loop: LLM call → tool call → repeat → response.",
        "acceptance_criteria": [
            "Agent runtime supports max 5 ReAct iterations",
            "Each iteration can call one or more tools",
            "Loop terminates when LLM returns text (no tool calls)",
            "Execution record persisted with token/duration metrics",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-PLAT-006",
        "title": "Workflow Engine",
        "description": "Orchestration module supports multi-step workflows with branching and pausing.",
        "acceptance_criteria": [
            "Supports step types: llm_call, tool_call, condition, emit_event, transform, wait_for_input",
            "wait_for_input pauses workflow until user responds",
            "Condition steps support branching based on previous output",
            "Workflow execution state is persisted",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-PLAT-007",
        "title": "Connector Framework",
        "description": "External services connect via a standard interface with encrypted credentials.",
        "acceptance_criteria": [
            "BaseConnector ABC defines authenticate, sync, handle_webhook",
            "Credentials are encrypted at rest (Fernet)",
            "Every sync operation produces a SyncLog record",
            "Connectors support OAuth2, API key, basic auth, webhook auth types",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-PLAT-008",
        "title": "Credential Encryption",
        "description": "All sensitive data (API keys, OAuth tokens) is encrypted at rest using Fernet.",
        "acceptance_criteria": [
            "encrypt() produces ciphertext different from plaintext",
            "decrypt(encrypt(x)) == x for all x",
            "Same plaintext encrypted twice produces different ciphertext (random IV)",
            "Corrupted ciphertext raises error on decrypt",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-PLAT-009",
        "title": "Domain Plugin Architecture",
        "description": "Each domain declares tools, agents, events, and memory categories via a manifest.",
        "acceptance_criteria": [
            "6 domains scaffolded: health, finance, productivity, relationships, learning, home",
            "Each domain has manifest.py with MANIFEST dict",
            "Manifest declares event_types, tools, agents, memory_categories",
            "Domains can be activated/deactivated via DomainRegistry",
        ],
        "priority": "P0",
        "test_ids": [],
    },
]
