"""
E2E test conftest — full pipeline tests with VCR cassettes for LLM calls.

E2E tests:
  - Use FastAPI TestClient for HTTP-level testing
  - Record/replay LLM API calls via respx (httpx mock)
  - Test complete user scenarios: message in → response out
  - Cassettes stored in tests/cassettes/
"""
import json
from pathlib import Path

import pytest

CASSETTES_DIR = Path(__file__).parent.parent / "cassettes"


class CassetteManager:
    """
    Simple VCR-like cassette recorder/replayer for LLM API calls.

    Usage in tests:
        with cassette("test_name") as responses:
            # If cassette file exists → replay mode
            # If not → record mode (requires RECORD_CASSETTES=1)
    """

    def __init__(self, cassette_name: str):
        self.name = cassette_name
        self.file = CASSETTES_DIR / f"{cassette_name}.json"
        self.responses: list[dict] = []
        self._call_index = 0

    def load(self) -> bool:
        """Load cassette from file. Returns True if file exists."""
        if self.file.exists():
            self.responses = json.loads(self.file.read_text())
            return True
        return False

    def save(self):
        """Save recorded responses to cassette file."""
        CASSETTES_DIR.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(self.responses, indent=2, default=str))

    def next_response(self) -> dict:
        """Get next recorded response for replay."""
        if self._call_index >= len(self.responses):
            raise RuntimeError(
                f"Cassette '{self.name}' exhausted: {self._call_index} calls "
                f"but only {len(self.responses)} recorded."
            )
        resp = self.responses[self._call_index]
        self._call_index += 1
        return resp

    def record(self, response: dict):
        """Record a response during record mode."""
        self.responses.append(response)


@pytest.fixture
def cassette():
    """
    Fixture that returns a CassetteManager factory.

    Example:
        def test_something(cassette):
            cm = cassette("my_test")
            if cm.load():
                # replay mode
            else:
                # record mode (or use mock)
    """
    def _factory(name: str) -> CassetteManager:
        return CassetteManager(name)
    return _factory


@pytest.fixture
def mock_llm_for_e2e():
    """
    Mock LLM that returns canned responses for E2E pipeline testing.
    Simulates the full orchestrator flow without hitting a real LLM.
    """
    responses = {
        "intent_classification": {
            "intent": "health.log_meal",
            "domain": "health",
            "confidence": 0.95,
        },
        "agent_response": "I've logged your breakfast: eggs and toast. That's approximately 350 calories, 21g protein.",
        "tool_call_response": {
            "content": None,
            "tool_calls": [{
                "id": "call_001",
                "function": {
                    "name": "health.log_meal",
                    "arguments": '{"meal_type": "breakfast", "items": ["eggs", "toast"]}',
                },
            }],
            "usage": {"prompt_tokens": 200, "completion_tokens": 50},
        },
        "final_response": "Logged your breakfast! Eggs and toast — approximately 350 calories (21g protein, 15g carbs, 18g fat). You're at 350/2000 calories for today.",
    }
    return responses
