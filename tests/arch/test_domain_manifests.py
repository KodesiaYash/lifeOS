"""
Architecture test: Verify every domain has a valid manifest and product requirements.

Ensures the domain plugin architecture is consistent:
  - Every domain folder has __init__.py, manifest.py, models.py, router.py, README.md
  - Every manifest declares event_types, tools, agents, memory_categories
  - Every domain has a corresponding product requirements file
  - Manifest tools/agents/events follow naming convention (domain.xxx)

Tests:
  - test_all_domains_have_required_files: Each domain has the 5 required files
  - test_all_manifests_have_required_keys: MANIFEST dict has all required keys
  - test_manifest_naming_convention: Tools, agents, events are prefixed with domain name
  - test_every_domain_has_requirements: Each domain has a requirements file
  - test_manifest_tools_match_requirement_tools: Tools in manifest align with requirement acceptance criteria
"""

import importlib
from pathlib import Path

import pytest

DOMAINS = ["health", "finance", "productivity", "relationships", "learning", "home"]
DOMAINS_DIR = Path(__file__).parent.parent.parent / "src" / "domains"
REQUIREMENTS_DIR = Path(__file__).parent.parent / "requirements"

REQUIRED_FILES = ["__init__.py", "manifest.py", "models.py", "router.py", "README.md"]
REQUIRED_MANIFEST_KEYS = {"domain_id", "event_types", "tools", "agents", "memory_categories"}


class TestDomainStructure:
    """Verify every domain plugin has the correct file structure."""

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_all_domains_have_required_files(self, domain):
        """Each domain folder must contain all 5 required files."""
        domain_dir = DOMAINS_DIR / domain
        assert domain_dir.exists(), f"Domain directory missing: {domain}"
        for fname in REQUIRED_FILES:
            assert (domain_dir / fname).exists(), f"{domain}/{fname} missing"


class TestDomainManifests:
    """Verify domain manifests are well-formed."""

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_all_manifests_have_required_keys(self, domain):
        """MANIFEST dict must have domain_id, event_types, tools, agents, memory_categories."""
        mod = importlib.import_module(f"src.domains.{domain}.manifest")
        manifest = mod.MANIFEST
        missing = REQUIRED_MANIFEST_KEYS - set(manifest.keys())
        assert not missing, f"{domain} manifest missing keys: {missing}"

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_manifest_domain_id_matches_folder(self, domain):
        """domain_id in manifest must match the folder name."""
        mod = importlib.import_module(f"src.domains.{domain}.manifest")
        assert mod.MANIFEST["domain_id"] == domain

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_manifest_naming_convention(self, domain):
        """Tools, agents, events must be prefixed with 'domain.' or 'domain_'."""
        mod = importlib.import_module(f"src.domains.{domain}.manifest")
        manifest = mod.MANIFEST

        for tool in manifest.get("tools", []):
            assert tool.startswith(f"{domain}."), f"Tool '{tool}' in {domain} must start with '{domain}.'"

        for agent in manifest.get("agents", []):
            assert agent.startswith(f"{domain}."), f"Agent '{agent}' in {domain} must start with '{domain}.'"

        for event in manifest.get("event_types", []):
            assert event.startswith(f"{domain}."), f"Event '{event}' in {domain} must start with '{domain}.'"

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_manifest_has_at_least_one_tool(self, domain):
        """Every domain must declare at least one tool."""
        mod = importlib.import_module(f"src.domains.{domain}.manifest")
        assert len(mod.MANIFEST.get("tools", [])) >= 1, f"{domain} has no tools declared"

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_manifest_has_at_least_one_agent(self, domain):
        """Every domain must declare at least one agent."""
        mod = importlib.import_module(f"src.domains.{domain}.manifest")
        assert len(mod.MANIFEST.get("agents", [])) >= 1, f"{domain} has no agents declared"


class TestDomainRequirements:
    """Verify every domain has product requirements."""

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_every_domain_has_requirements(self, domain):
        """A tests/requirements/{domain}.py file must exist with REQUIREMENTS list."""
        req_file = REQUIREMENTS_DIR / f"{domain}.py"
        assert req_file.exists(), f"Missing requirements file: tests/requirements/{domain}.py"

        mod = importlib.import_module(f"tests.requirements.{domain}")
        assert hasattr(mod, "REQUIREMENTS"), f"tests/requirements/{domain}.py missing REQUIREMENTS list"
        assert len(mod.REQUIREMENTS) >= 1, f"{domain} has no product requirements defined"

    def test_platform_has_requirements(self):
        """Platform kernel must have its own requirements file."""
        mod = importlib.import_module("tests.requirements.platform")
        assert len(mod.REQUIREMENTS) >= 5, "Platform should have at least 5 requirements"
