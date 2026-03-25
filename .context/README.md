# Contextual Development System

This directory is the **development memory** of AI Life OS. It exists so that any developer — human or AI — can resume work with full context, regardless of which LLM, IDE, or session they're in.

---

## Problem

LLM conversations are ephemeral. When you start a new session (new chat, different LLM, different machine), all context is lost. The developer has to re-explain the project, architecture, conventions, and current status every time. This wastes tokens, introduces inconsistency, and slows development.

## Solution

A structured `.context/` directory that stores the project's development history in two formats:

1. **`manifest.yml`** — machine-readable project map (~200 tokens). Always include this.
2. **Topic files** — human-readable markdown, chunked by concern. Include on-demand.

Together they give any LLM enough context to be productive immediately.

---

## Files

| File | Purpose | When to include |
|------|---------|----------------|
| **`manifest.yml`** | Structured project map: modules, domains, tools, agents, totals, key files | **Always** — every session |
| **`overview.md`** | Project identity, tech stack, codebase map | **Always** — every session |
| **`architecture.md`** | Domain plugin system, auto-wiring, internal APIs, naming conventions | Working on domains, plugins, kernel |
| **`domains.md`** | Per-domain reference: tools, agents, events, memory, pending models | Working on any domain |
| **`tests.md`** | Test tiers, running tests, requirement tagging, CI pipeline | Writing or debugging tests |
| **`conventions.md`** | Naming rules, important gotchas, code style | Any session (short, low cost) |
| **`pending.md`** | What's done (Phase 0) and what's next (Phase 1) | Planning or starting new work |
| **`changelog.md`** | Session-by-session development history | Resuming after a break |
| **`TODO.md`** | TODOs for the .context system itself (incl. vector embedding plan) | Improving the context system |

---

## How to Use

### Starting a new LLM session

**Minimum context (any task):**
```
Paste: manifest.yml + overview.md
```

**Domain work:**
```
Paste: manifest.yml + overview.md + architecture.md + domains.md
```

**Test work:**
```
Paste: manifest.yml + overview.md + tests.md + conventions.md
```

**Full cold start (new LLM, no history):**
```
Paste: LLM_CONTEXT.md (project root) — monolithic version of everything
```

### After a development session

1. Update `changelog.md` with a summary of what was built/changed
2. If domains/tools/agents changed, update `manifest.yml`
3. If Phase 1 items were completed, update `pending.md`

### Adding a new topic file

If a new area of the project becomes complex enough to need its own context (e.g., `deployment.md`, `integrations.md`), create it in `.context/` and add it to this README's file table.

---

## Design Principles

- **Chunked, not monolithic** — include only what's relevant to the current task
- **Machine-readable manifest** — structured YAML that any LLM parses efficiently
- **Human-readable topic files** — Markdown that developers can also read directly
- **Session changelog** — never lose the history of what was built and why
- **Low maintenance** — update manifest.yml and changelog.md, everything else is stable

---

## Future: Vector Embeddings

When the project grows past ~50K tokens of context, we'll add a semantic retrieval layer:

```bash
python scripts/context_retrieve.py "I'm working on health domain meal parsing"
# → Returns only the relevant context chunks
```

See `TODO.md` for the full plan. Current system works well at this scale.

---

## Relationship to Other Docs

| Document | Location | Purpose |
|----------|----------|---------|
| `.context/` | This directory | LLM session context injection |
| `LLM_CONTEXT.md` | Project root | Monolithic cold-start dump (all context in one file) |
| `ARCHITECTURE.md` | Project root | Full architecture doc for humans |
| `src/domains/README.md` | Domains dir | Domain developer guide |
| `tests/README.md` | Tests dir | Test suite architecture |
| `README.md` | Project root | Project overview + quickstart |
