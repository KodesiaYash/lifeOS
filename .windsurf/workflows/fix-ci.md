---
description: Fix CI failures iteratively until all checks pass
---

# Fix CI Workflow

Use this workflow when CI is failing on your branch. It will analyze failures, fix them, and push commits until CI passes.

## Prerequisites
- GitHub CLI installed: `brew install gh`
- Authenticated: `gh auth login`

## Steps

### 1. Check current CI status
// turbo
```bash
gh pr checks 2>/dev/null || gh run list --branch $(git branch --show-current) -L 1
```

### 2. View failed workflow logs
// turbo
```bash
gh run view --log-failed 2>/dev/null | head -300
```

### 3. Analyze the failure type and fix

**Lint errors (ruff):**
```bash
source .venv/bin/activate && ruff check --fix . && ruff format .
```

**Unit test failures:**
- Read the failing test file
- Check the assertion and expected vs actual values
- Fix the source code or test as appropriate

**Integration test failures:**
- Check database/Redis connectivity
- Verify migrations are up to date
- Check for missing environment variables

**Migration check failures:**
- Run `alembic revision --autogenerate -m "description"`
- Commit the new migration file

**Type errors:**
- Check imports
- Add missing type annotations
- Fix incompatible types

### 4. Verify fix locally before pushing
// turbo
```bash
./scripts/pre_push.sh
```

### 5. Commit and push the fix
```bash
git add -A && git commit -m "fix: <describe what was fixed>" && git push
```

### 6. Watch CI run
// turbo
```bash
gh run watch
```

### 7. If still failing, repeat from step 2

---

## Quick Commands Reference

| Command | Purpose |
|---------|---------|
| `gh pr checks` | Show CI status for current PR |
| `gh run list -L 5` | List recent workflow runs |
| `gh run view --log-failed` | Show logs from failed jobs |
| `gh run watch` | Watch CI in real-time |
| `./scripts/pre_push.sh` | Run all CI checks locally |
| `ruff check --fix .` | Auto-fix lint errors |
| `ruff format .` | Format code |
| `pytest tests/unit -x` | Run unit tests, stop on first failure |
