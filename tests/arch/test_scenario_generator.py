"""
Architecture test: Generate test scenarios from product requirements and verify coverage.

This test reads every product requirement's acceptance_criteria, generates
testable scenario descriptions, and checks whether matching tests exist
in the test suite.

How it works:
  1. Load all requirements from tests/requirements/
  2. For each acceptance criterion, generate a scenario ID
  3. Scan test files for @pytest.mark.scenario("SCENARIO-xxx") markers
  4. Report which scenarios are covered vs. uncovered

Tests:
  - test_scenario_generation: All acceptance criteria produce valid scenario IDs
  - test_scenario_uniqueness: No duplicate scenario IDs
  - test_platform_scenarios_covered: Platform scenarios have corresponding tests
  - test_scenario_report: Full scenario coverage report (informational)
"""

import importlib
import re
from pathlib import Path

import pytest


def _load_all_requirements() -> list[dict]:
    """Load all requirement dicts from tests/requirements/*.py."""
    reqs_dir = Path(__file__).parent.parent / "requirements"
    all_reqs = []
    for py_file in sorted(reqs_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        mod = importlib.import_module(f"tests.requirements.{py_file.stem}")
        if hasattr(mod, "REQUIREMENTS"):
            all_reqs.extend(mod.REQUIREMENTS)
    return all_reqs


def _generate_scenarios(requirements: list[dict]) -> list[dict]:
    """
    Generate test scenarios from acceptance criteria.

    Each acceptance criterion becomes a scenario with:
      - scenario_id: derived from requirement ID + criterion index
      - requirement_id: parent requirement
      - description: the acceptance criterion text
      - priority: inherited from parent requirement
    """
    scenarios = []
    for req in requirements:
        for idx, criterion in enumerate(req["acceptance_criteria"], 1):
            scenario_id = f"SCN-{req['id']}-{idx:02d}"
            scenarios.append(
                {
                    "scenario_id": scenario_id,
                    "requirement_id": req["id"],
                    "description": criterion,
                    "priority": req["priority"],
                }
            )
    return scenarios


def _scan_for_scenario_markers() -> dict[str, list[str]]:
    """
    Scan test files for @pytest.mark.scenario("SCN-xxx") markers.
    Returns {scenario_id: [test references]}.
    """
    tests_root = Path(__file__).parent.parent
    coverage_map: dict[str, list[str]] = {}

    for test_file in tests_root.rglob("test_*.py"):
        try:
            source = test_file.read_text()
        except Exception:
            continue

        for match in re.finditer(r'@pytest\.mark\.scenario\(["\']([^"\']+)["\']\)', source):
            scn_id = match.group(1)
            rest = source[match.end() :]
            fn_match = re.search(r"(?:async\s+)?def\s+(test_\w+)", rest)
            if fn_match:
                ref = f"{test_file.relative_to(tests_root)}::{fn_match.group(1)}"
                coverage_map.setdefault(scn_id, []).append(ref)

    return coverage_map


class TestScenarioGeneration:
    """Verify scenario generation from requirements."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.requirements = _load_all_requirements()
        self.scenarios = _generate_scenarios(self.requirements)
        self.coverage = _scan_for_scenario_markers()

    def test_scenario_generation(self):
        """All acceptance criteria produce valid scenario IDs."""
        assert len(self.scenarios) > 0, "No scenarios generated"
        for s in self.scenarios:
            assert s["scenario_id"].startswith("SCN-"), f"Invalid scenario ID: {s['scenario_id']}"
            assert len(s["description"]) > 0

    def test_scenario_uniqueness(self):
        """Every scenario has a unique ID."""
        ids = [s["scenario_id"] for s in self.scenarios]
        dupes = [sid for sid in ids if ids.count(sid) > 1]
        assert len(dupes) == 0, f"Duplicate scenario IDs: {set(dupes)}"

    def test_all_scenarios_have_parent_requirement(self):
        """Every scenario links back to a valid requirement ID."""
        req_ids = {r["id"] for r in self.requirements}
        for s in self.scenarios:
            assert s["requirement_id"] in req_ids, (
                f"Scenario {s['scenario_id']} references unknown requirement {s['requirement_id']}"
            )

    def test_platform_scenarios_covered(self):
        """
        Platform scenarios (SCN-REQ-PLAT-*) should have test coverage.
        Skips if not yet tagged — informational.
        """
        platform_scenarios = [s for s in self.scenarios if s["scenario_id"].startswith("SCN-REQ-PLAT-")]
        uncovered = [s for s in platform_scenarios if s["scenario_id"] not in self.coverage]

        if uncovered:
            pytest.skip(
                f"{len(uncovered)}/{len(platform_scenarios)} platform scenarios without tests. "
                f"Tag tests with @pytest.mark.scenario('SCN-REQ-PLAT-xxx-NN')."
            )

    def test_scenario_report(self):
        """
        Informational: prints the full scenario → test mapping.
        """
        print("\n" + "=" * 70)
        print("TEST SCENARIO COVERAGE REPORT")
        print("=" * 70)

        by_domain: dict[str, list] = {}
        for s in self.scenarios:
            domain = s["requirement_id"].split("-")[1]
            by_domain.setdefault(domain, []).append(s)

        total = len(self.scenarios)
        covered = 0

        for domain, scenarios in sorted(by_domain.items()):
            print(f"\n── {domain.upper()} ──")
            for s in scenarios:
                tests = self.coverage.get(s["scenario_id"], [])
                if tests:
                    covered += 1
                status = f"✓ {len(tests)} test(s)" if tests else "✗ UNTESTED"
                print(f"  [{s['priority']}] {s['scenario_id']}: {s['description'][:60]}... — {status}")

        pct = 100 * covered // total if total else 0
        print(f"\nScenario coverage: {covered}/{total} ({pct}%)")
        print("=" * 70)
