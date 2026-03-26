# Overview

> Include this file for any LLM session. It gives the essential project identity.

## Project

- **Name:** AI Life OS
- **Repo:** `/Users/ykodesia/Desktop/github/lifeOS/`
- **GitHub:** https://github.com/KodesiaYash/lifeOS
- **Phase:** Phase 0 complete (kernel foundation). Phase 1 (domain implementations) pending.

## What It Is

An AI-powered **single-user** life management platform designed for self-hosting. Users interact via WhatsApp/Telegram/REST. The AI understands intent, routes to domain-specific agents (health, finance, productivity, relationships, learning, home), calls tools, remembers context across conversations, and provides personalised responses.

Built as a **modular monolith** — one deployable with clean module boundaries, event-driven communication, and a plugin architecture for domains. No tenant/user management needed — the app runs for whoever is running it.

## Tech Stack

Python 3.11+, FastAPI, SQLAlchemy 2.0 async, PostgreSQL 16 + pgvector, Redis 7, LiteLLM, structlog, Pydantic Settings, APScheduler, arq, Docker Compose.

## Core Ideology

**Product requirements drive everything.** Requirements live as Python dicts in `tests/requirements/`. Architecture tests auto-enforce that every requirement has tests, every domain is wired into every platform layer, and naming conventions are followed. A domain developer implements one Python class (`DomainPlugin`) — the kernel handles all wiring.

## Codebase Map

```
src/
├── config.py, main.py, dependencies.py     ← App entry, DI
├── shared/          ← DB, crypto, pagination, time
├── core/            ← Settings, domain registry
├── events/          ← Event bus (pub/sub + wildcard)
├── communication/   ← WhatsApp/Telegram/REST adapters
├── memory/          ← Short-term (Redis), structured (SQL), semantic (pgvector)
├── knowledge/       ← Document ingestion, chunking, embedding
├── retrieval/       ← Hybrid RAG + reranker
├── kernel/          ← LLM client, prompt/tool registries
├── orchestration/   ← Workflow engine
├── agents/          ← ReAct agent runtime + registry
├── scheduling/      ← APScheduler + arq
├── connectors/      ← External service framework
└── domains/         ← Plugin system: health, finance, productivity, relationships, learning, home
```
