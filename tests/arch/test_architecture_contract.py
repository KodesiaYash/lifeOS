"""
Architecture test: enforce the presence of the architecture contract document.

This keeps architecture-affecting changes anchored to one shared contract file.
"""

from pathlib import Path

CONTRACT_PATH = Path(__file__).parent.parent.parent / "docs" / "ARCHITECTURE_CONTRACT.md"


def test_architecture_contract_exists():
    assert CONTRACT_PATH.exists(), "Missing docs/ARCHITECTURE_CONTRACT.md"


def test_architecture_contract_has_required_sections():
    content = CONTRACT_PATH.read_text()
    required_sections = [
        "## 1. Source Of Truth",
        "## 2. Inbound Flow Contract",
        "## 3. Orchestrator Contract",
        "## 4. Event Contract",
        "## 5. Memory Contract",
        "## 6. Domain-Routed Channel Contract",
        "## 7. Product-Driven Contract",
        "## 8. Change Template",
        "## 9. Test Expectations",
    ]
    for section in required_sections:
        assert section in content, f"Architecture contract missing section: {section}"
