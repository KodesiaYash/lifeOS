# .context TODO

Tasks for improving the contextual development system itself.

---

## Active

- [ ] **Keep changelog.md updated** — add a section at the end of every development session summarising what changed

- [ ] **Keep manifest.yml updated** — when domains, tools, agents, or modules change, update the manifest to stay in sync

- [ ] **Keep pending.md updated** — as Phase 1 items are completed, move them to the changelog

---

## Future: Vector Embedding Index

**Goal:** When the project grows beyond ~50K tokens of context (likely mid-Phase 1), manual file selection becomes a bottleneck. At that point, build a semantic retrieval layer over the context files.

### Plan

1. **Chunking:** Split all `.context/*.md` files + key `.py` module docstrings + domain `__init__.py` files into ~200-token chunks with metadata (file, section, domain)

2. **Embedding:** Use `text-embedding-3-small` (OpenAI) or a local model like `all-MiniLM-L6-v2` (sentence-transformers) to embed each chunk

3. **Storage:** Store embeddings in a local vector DB:
   - **Option A:** ChromaDB (persistent, simple Python API, no server needed)
   - **Option B:** FAISS index (faster, but less metadata-friendly)
   - **Option C:** Use the project's own pgvector (already in the stack — dogfooding)

4. **Retrieval script:** Create `scripts/context_retrieve.py`:
   ```bash
   python scripts/context_retrieve.py "I'm working on health domain meal parsing"
   # → Returns top-20 relevant context chunks as a single text block
   # → Copy-paste into LLM session as the first message
   ```

5. **Index rebuild script:** Create `scripts/context_index.py`:
   ```bash
   python scripts/context_index.py
   # → Re-scans .context/ + src/ docstrings
   # → Rebuilds the embedding index
   # → Run after significant changes
   ```

6. **Integration with LLM workflow:**
   - Developer starts a new LLM session
   - Runs `python scripts/context_retrieve.py "my task description"`
   - Pastes the output as the first message
   - LLM has precisely the context it needs, nothing more

### When to Build This

- **Not now** — .context/ files with manual selection work fine at current scale
- **Trigger:** When you find yourself spending >30 seconds deciding which .context/ files to include, or when total context exceeds a single LLM context window
- **Estimated effort:** ~2-3 hours (script + ChromaDB setup + testing)

### Dependencies

- `chromadb` or `faiss-cpu` (add to dev dependencies)
- `sentence-transformers` (if using local embeddings) or `openai` (if using API)
- Existing `.context/` files as the source corpus

---

## Future: Auto-Update Hooks

- [ ] **Git pre-commit hook** that warns if `manifest.yml` is stale (e.g., new domain folder exists but isn't in manifest)
- [ ] **Post-session script** that prompts developer to update changelog.md
- [ ] **CI check** that validates `.context/manifest.yml` matches actual codebase structure
