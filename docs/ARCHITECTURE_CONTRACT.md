# Architecture Contract

This document is the implementation contract for all new interactive features in AI Life OS.

It exists to keep future changes aligned with the intended platform shape:

`channel adapter -> communication persistence -> orchestrator -> event bus -> outbound dispatcher`

## 1. Source Of Truth

When there is a conflict between local implementation convenience and platform structure, the platform structure wins.

Interactive features must follow:

1. Normalize inbound traffic inside a communication adapter.
2. Persist identities, conversations, and inbound messages in the communication layer.
3. Hand off the request to the global orchestrator with conversation and session context.
4. Let the orchestrator resolve the target domain, assemble memory, retrieve context, and generate a response.
5. Emit lifecycle events through the event bus.
6. Dispatch outbound replies through the channel dispatcher.
7. Persist outbound messages after dispatch.

Direct route-to-LLM or route-to-memory shortcuts are not allowed.

## 2. Inbound Flow Contract

Every inbound interaction must pass through these stages in order:

1. `ChannelAdapter.normalize_inbound`
2. `CommunicationService.process_inbound`
3. `GlobalOrchestrator.process`
4. `event_bus.publish(...)`
5. `dispatch_message(...)`
6. `CommunicationService.store_outbound`

Required invariants:

- The orchestrator receives a persisted conversation ID.
- The orchestrator receives a stable session ID.
- The outbound dispatcher receives the original channel type.
- Duplicate inbound messages are dropped before orchestration.

## 3. Orchestrator Contract

The orchestrator is the only component allowed to turn an inbound message into an assistant reply.

The orchestrator must own:

- intent classification
- memory assembly
- retrieval
- response generation
- orchestration lifecycle events

The orchestrator may use domain-specific helpers or plugin hooks, but helpers must not bypass the orchestrator.

Deterministic direct-tool shortcuts are allowed only when:

- the domain plugin declares the resolution logic
- the orchestrator remains the component that decides to invoke the tool
- the resulting reply still emits the normal lifecycle events

## 4. Event Contract

The event bus carries lifecycle events, not raw transport ownership.

Required event types for message flows:

- `communication.message_received`
- `system.message_processed`
- `<domain>.message_processed` when a domain is resolved
- `communication.message_sent` after a reply is dispatched

Required invariants:

- All lifecycle events in a single interaction share the same `correlation_id`.
- Communication events use `event_category="communication"`.
- Domain events use `event_category="domain"`.
- Event emission must not replace persistence or orchestration.

## 5. Memory Contract

Memory usage must be explicit and namespaced.

Rules:

- Short-term memory stores active session state and recent turns.
- General structured or semantic memory stores durable cross-domain user facts.
- Domain-scoped memory stores durable facts that belong only to that domain.
- Not every message becomes long-term memory.
- Only explicit, stable, or consolidated facts should be promoted into structured or semantic memory.

When a channel-specific bot identity exists, it should map to a real domain namespace rather than inventing a separate memory silo.

## 6. Domain-Routed Channel Contract

Some channels expose a specific bot identity, such as a Telegram tutor bot. That channel identity is transport metadata, not a replacement for the domain scaffold.

A routed channel bot must declare:

- `bot_id`
- `channel_type`
- `target_domain`

Routed channel bots must:

- enter through the normal communication layer
- hand off to the global orchestrator with an explicit `target_domain`
- use shared `general` memory plus the real domain namespace
- emit architecture-compliant lifecycle events
- keep domain logic inside `src/domains/<domain>/`

Routed channel bots must not:

- bypass the domain plugin system
- call the LLM directly from the communication layer
- create a second long-term namespace that diverges from the domain namespace

## 7. Product-Driven Contract

Every architecture-affecting feature must ship with:

1. a requirement in `tests/requirements/`
2. acceptance criteria
3. tests tagged with `@pytest.mark.req(...)`
4. scenario tags with `@pytest.mark.scenario(...)` for platform or routed-domain flows
5. at least one unit or integration test for the main path

## 8. Change Template

Any new architecture-affecting change should document these sections in the PR or implementation notes:

1. Requirement
2. Inbound Path
3. Orchestrator Handoff
4. Events Emitted
5. Memory Touched
6. Tests Added
7. Follow-up Risks

## 9. Test Expectations

At minimum, architecture-affecting changes should add:

- unit tests for intent or orchestration logic
- integration tests for persisted message flow
- architecture tests for contract or requirement enforcement when relevant

If a change introduces a new event type or namespace, tests should verify it explicitly.
