"""Tests for the unified aw router skill and Antigravity skill install coverage."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import engine, host_adapters, manifest
from agent_workflows.host_capability_registry import HostCapabilityRegistry
from tests.support import SOURCE_WORKFLOWS, init_repo


class AgySkillInstallTests(unittest.TestCase):
    """Test emission and properties of the unified aw router skill during install."""

    def test_install_emits_aw_router_skill(self) -> None:
        """A real install writes .agents/skills/aw/SKILL.md and records it in manifest."""
        with tempfile.TemporaryDirectory() as td:
            repo = init_repo(Path(td))
            engine.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)

            router_path = repo / ".agents" / "skills" / "aw" / "SKILL.md"
            self.assertTrue(router_path.is_file(), f"Router missing at {router_path}")

            content = router_path.read_text(encoding="utf-8")
            self.assertTrue(content.startswith("---"))
            self.assertIn("name: aw", content)
            self.assertIn(".aw/system/workflows/index.md", content)

            # Assert path is recorded in ownership manifest
            mf_path = manifest.resolve_manifest_path(repo)
            mf = manifest.load(mf_path)
            self.assertIsNotNone(
                mf.recorded_hash(".agents/skills/aw/SKILL.md"),
                "Expected .agents/skills/aw/SKILL.md to be recorded in manifest",
            )

    def test_install_idempotence(self) -> None:
        """A second install is idempotent and preserves identical router bytes."""
        with tempfile.TemporaryDirectory() as td:
            repo = init_repo(Path(td))
            engine.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)

            router_path = repo / ".agents" / "skills" / "aw" / "SKILL.md"
            initial_bytes = router_path.read_bytes()

            engine.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)
            second_bytes = router_path.read_bytes()

            self.assertEqual(initial_bytes, second_bytes)

    def test_router_lists_every_non_catalog_verb(self) -> None:
        """The router lists every non-catalog verb, re-derived at test time."""
        with tempfile.TemporaryDirectory() as td:
            repo = init_repo(Path(td))
            engine.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)

            router_path = repo / ".agents" / "skills" / "aw" / "SKILL.md"
            content = router_path.read_text(encoding="utf-8")

            workflows = engine.parse_manifest(SOURCE_WORKFLOWS)
            non_catalog = [w for w in workflows if not engine.is_concern_catalog_row(w)]

            for w in non_catalog:
                self.assertIn(
                    f"`{w.command}`",
                    content,
                    f"Workflow '{w.command}' missing from router verbs list",
                )

    def test_router_builder_contracts(self) -> None:
        """Unit test: verify E-01 contracts on build_aw_router_skill_package."""
        workflows = engine.parse_manifest(SOURCE_WORKFLOWS)
        pkg = host_adapters.build_aw_router_skill_package(workflows)

        self.assertEqual(pkg.main_file_path(), ".agents/skills/aw/SKILL.md")
        self.assertEqual(host_adapters.validate_skill_package(pkg), [])
        self.assertTrue(host_adapters.disabled_skill_still_invocable(pkg))
        self.assertTrue(pkg.within_budget())

        digest_all = pkg.semantic_digest
        digest_minus1 = host_adapters.build_aw_router_skill_package(
            workflows[:-1]
        ).semantic_digest
        self.assertNotEqual(digest_all, digest_minus1)

    def test_router_uniqueness_guard(self) -> None:
        """Unit test: verify E-02 package name uniqueness guard."""
        workflows = engine.parse_manifest(SOURCE_WORKFLOWS)
        packages = [
            host_adapters.build_skill_package(w)
            for w in workflows
            if host_adapters.classify_discovery_policy(w)
            == host_adapters.POLICY_SKILL_ENTRY_POINT
        ]
        router = host_adapters.build_aw_router_skill_package(workflows)
        packages.append(router)

        second_aw = host_adapters.SkillPackage(
            name="aw",
            skill_dir=host_adapters.SHARED_SKILLS_DIR,
            trigger_description="Use when x. Do not use for y.",
            semantic_digest="digest",
            explicit_invocation="read and execute .aw/system/workflows/index.md",
            main_file_content="",
        )
        packages.append(second_aw)

        with self.assertRaises(host_adapters.AdapterGenerationError) as ctx:
            host_adapters.guard_skill_package_collision(packages)
        self.assertIn("aw", str(ctx.exception))

    def test_antigravity_host_mapping(self) -> None:
        """Unit test: verify E-04 antigravity mapping to router and v1 hosts."""
        registry = HostCapabilityRegistry()
        adapter = host_adapters.build_host_adapter("antigravity", registry, "1.0.0")
        d = adapter.to_dict()

        self.assertEqual(d["role_map"].get("skill"), "router")
        self.assertTrue(d["is_v1"])
        self.assertIn("skill", d["unverified_features"])
        self.assertNotIn("skill", d["supported_features"])


if __name__ == "__main__":
    unittest.main()
