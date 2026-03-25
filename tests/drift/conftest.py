"""
Drift test conftest — nightly real-LLM tests to catch prompt/model drift.

Drift tests:
  - Use REAL LLM calls (gpt-4o-mini at temperature=0)
  - Run nightly in CI, NOT on every push
  - Assert on structure/behaviour, not exact wording
  - Require OPENAI_API_KEY in environment
  - Marked with @pytest.mark.drift — skip by default

Usage:
    pytest tests/drift/ -m drift          # run drift tests only
    pytest -m "not drift"                 # skip drift tests (default)
"""
import os

import pytest

# Skip all drift tests unless explicitly opted in
DRIFT_ENABLED = os.environ.get("RUN_DRIFT_TESTS", "0") == "1"

skip_unless_drift = pytest.mark.skipif(
    not DRIFT_ENABLED,
    reason="Drift tests disabled. Set RUN_DRIFT_TESTS=1 to enable.",
)

skip_unless_api_key = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set — cannot run real LLM drift tests.",
)


def drift_test(fn):
    """Decorator combining drift skip markers."""
    return pytest.mark.drift(skip_unless_drift(skip_unless_api_key(fn)))
