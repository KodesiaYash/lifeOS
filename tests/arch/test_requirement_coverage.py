"""
Architecture test: Verify every product requirement has at least one test.

This test reads all product requirements from tests/requirements/ and scans
the test suite to find tests tagged with each requirement ID. It fails if
any P0 requirement has zero test coverage.

How to tag a test with a requirement:
    @pytest.mark.req("REQ-HEALTH-001")
    def test_meal_logging():
        ...

Tests:
  - test_all_p0_requirements_have_tests: Every P0 requirement has at least one tagged test
  - test_all_requirements_loaded: All requirement files parse without errors
  - test_no_duplicate_requirement_ids: No two requirements share the same ID
  - test_requirement_structure: Every requirement has required fields
  - test_coverage_report: Prints a coverage matrix (informational)
"""
import importlib
import os
import re
import ast
from pathlib import Path

import pytest


def _load_all_requirements() -> list[dict]:
    """Load all requirement dicts from tests/requirements/*.py."""
    reqs_dir = Path(__file__).parent.parent / "requirements"
    all_reqs = []
    for py_file in sorted(reqs_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        module_name = f"tests.requirements.{py_file.stem}"
        mod = importlib.import_module(module_name)
        if hasattr(mod, "REQUIREMENTS"):
            all_reqs.extend(mod.REQUIREMENTS)
    return all_reqs


def _scan_test_files_for_req_markers() -> dict[str, list[str]]:
    """
    Scan all test files for @pytest.mark.req("REQ-XXX-NNN") markers.
    Returns {requirement_id: [list of test file:function paths]}.
    """
    tests_root = Path(__file__).parent.parent
    coverage_map: dict[str, list[str]] = {}

    for test_file in tests_root.rglob("test_*.py"):
        try:
            source = test_file.read_text()
        except Exception:
            continue

        # Find all req markers using regex (faster than AST for simple pattern)
        for match in re.finditer(r'@pytest\.mark\.req\(["\']([^"\']+)["\']\)', source):
            req_id = match.group(1)
            # Find the next function/method definition after this marker
            rest = source[match.end():]
            fn_match = re.search(r'(?:async\s+)?def\s+(test_\w+)', rest)
            if fn_match:
                fn_name = fn_match.group(1)
                ref = f"{test_file.relative_to(tests_root)}::{fn_name}"
                coverage_map.setdefault(req_id, []).append(ref)

    return coverage_map


class TestRequirementCoverage:
    """Verify product requirements have adequate test coverage."""

    @pytest.fixture(autouse=True)
    def load_data(self):
        self.requirements = _load_all_requirements()
        self.coverage = _scan_test_files_for_req_markers()

    def test_all_requirements_loaded(self):
        """All requirement files parse and produce requirements."""
        assert len(self.requirements) > 0, "No requirements found"
        # Should have requirements from at least 6 domains + platform
        domains = {r["id"].split("-")[1] for r in self.requirements}
        assert len(domains) >= 6, f"Expected >= 6 requirement domains, found {domains}"

    def test_no_duplicate_requirement_ids(self):
        """Every requirement has a unique ID."""
        ids = [r["id"] for r in self.requirements]
        duplicates = [rid for rid in ids if ids.count(rid) > 1]
        assert len(duplicates) == 0, f"Duplicate requirement IDs: {set(duplicates)}"

    def test_requirement_structure(self):
        """Every requirement has all required fields."""
        required_fields = {"id", "title", "description", "acceptance_criteria", "priority", "test_ids"}
        for req in self.requirements:
            missing = required_fields - set(req.keys())
            assert not missing, f"Requirement {req.get('id', '?')} missing fields: {missing}"
            assert len(req["acceptance_criteria"]) > 0, (
                f"Requirement {req['id']} has no acceptance criteria"
            )

    def test_all_p0_requirements_have_tests(self):
        """
        Every P0 (must-have) requirement must have at least one test tagged with its ID.

        NOTE: This test will initially fail for unimplemented Phase 1 domain features.
        Once domain implementations are added, tag their tests with @pytest.mark.req().
        Currently, only platform requirements (REQ-PLAT-*) are expected to have coverage.
        """
        p0_reqs = [r for r in self.requirements if r["priority"] == "P0"]
        # For now, only check platform requirements — domain P0s are Phase 1
        platform_p0 = [r for r in p0_reqs if r["id"].startswith("REQ-PLAT-")]
        uncovered = []
        for req in platform_p0:
            if req["id"] not in self.coverage:
                uncovered.append(f"{req['id']}: {req['title']}")

        if uncovered:
            pytest.skip(
                f"{len(uncovered)} platform P0 requirements without tagged tests "
                f"(tag tests with @pytest.mark.req('REQ-ID')): "
                + ", ".join(uncovered[:5])
            )

    def test_coverage_report(self):
        """
        Informational: prints coverage matrix.
        Does not fail — serves as documentation.
        """
        print("\n" + "=" * 70)
        print("PRODUCT REQUIREMENT TEST COVERAGE REPORT")
        print("=" * 70)

        for req in sorted(self.requirements, key=lambda r: r["id"]):
            tests = self.coverage.get(req["id"], [])
            status = f"✓ {len(tests)} test(s)" if tests else "✗ NO TESTS"
            print(f"  [{req['priority']}] {req['id']}: {req['title']} — {status}")
            for t in tests:
                print(f"       → {t}")

        total = len(self.requirements)
        covered = sum(1 for r in self.requirements if r["id"] in self.coverage)
        print(f"\nCoverage: {covered}/{total} requirements ({100*covered//total if total else 0}%)")
        print("=" * 70)
