#!/usr/bin/env python3
"""Isolated tests for the AW physical-layout planning evidence tools."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any, Dict


TOOLS_DIR = Path(__file__).resolve().parent


def load_tool(name: str) -> ModuleType:
    """Load one sibling planning tool without requiring package installation."""

    path = TOOLS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


INVENTORY = load_tool("aw_layout_inventory")
COMPARE = load_tool("aw_layout_compare")
POSTCHECK = load_tool("aw_layout_postcheck")


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run Git for a disposable fixture and fail the test on command failure."""

    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


class InventoryTests(unittest.TestCase):
    """Verify complete, deterministic, and symlink-safe inventory behavior."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "fixture@example.invalid")
        git(self.repo, "config", "user.name", "Fixture")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_inventory_classifies_tracked_untracked_and_ignored(self) -> None:
        """Inventory records Git state and conservative legacy classes."""

        workflow = self.repo / ".agents/workflows/example/body.md"
        workflow.parent.mkdir(parents=True)
        workflow.write_text("workflow\n", encoding="utf-8")
        plan = self.repo / ".agents/plans/pending/plan.md"
        plan.parent.mkdir(parents=True)
        plan.write_text("plan\n", encoding="utf-8")
        ignored = self.repo / "workflow-artifacts/run/output.txt"
        ignored.parent.mkdir(parents=True)
        ignored.write_text("evidence\n", encoding="utf-8")
        (self.repo / ".gitignore").write_text("workflow-artifacts/\n", encoding="utf-8")
        git(self.repo, "add", ".agents/workflows/example/body.md", ".gitignore")

        result = INVENTORY.inventory(
            self.repo,
            [
                ("agents", self.repo / ".agents"),
                ("workflow-artifacts", self.repo / "workflow-artifacts"),
            ],
            include_paths=False,
        )

        self.assertTrue(result["valid"], result["errors"])
        by_path = {
            (item["source_root"], item["source_relpath"]): item
            for item in result["items"]
        }
        self.assertEqual(
            by_path[("agents", "workflows/example/body.md")]["git_state"], "tracked"
        )
        self.assertEqual(
            by_path[("agents", "plans/pending/plan.md")]["git_state"], "untracked"
        )
        self.assertEqual(
            by_path[("workflow-artifacts", "run/output.txt")]["git_state"], "ignored"
        )
        self.assertEqual(
            by_path[("agents", "workflows/example/body.md")]["legacy_class"], "system"
        )
        self.assertEqual(
            by_path[("agents", "plans/pending/plan.md")]["legacy_class"], "records"
        )

    def test_inventory_does_not_follow_symlink(self) -> None:
        """An escaping symlink is recorded as a link without hashing its target."""

        external = Path(self.temp.name) / "external-secret.txt"
        external.write_text("not inventory content\n", encoding="utf-8")
        agents = self.repo / ".agents"
        agents.mkdir()
        os.symlink(external, agents / "outside")

        result = INVENTORY.inventory(
            self.repo, [("agents", agents)], include_paths=False
        )
        item = next(
            item for item in result["items"] if item["source_relpath"] == "outside"
        )
        self.assertEqual(item["kind"], "symlink")
        self.assertIsNone(item["sha256"])
        self.assertEqual(item["symlink_target"], str(external))

    def test_git_classification_is_closed_and_deterministic(self) -> None:
        """External, exact unmerged, and mixed states use stable spellings."""

        self.assertEqual(
            INVENTORY._git_state(None, set(), set(), set(), set()), "external"
        )
        self.assertEqual(
            INVENTORY._git_state(
                "conflict.md", {"conflict.md"}, set(), set(), {"conflict.md"}
            ),
            "unmerged",
        )
        self.assertEqual(
            INVENTORY._git_state("tree", {"tree/a"}, set(), {"tree/b"}, set()),
            "mixed:ignored,tracked",
        )


class CompareTests(unittest.TestCase):
    """Verify complete map accounting and byte comparison."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.source = root / "source"
        self.destination = root / "destination"
        self.source.mkdir()
        self.destination.mkdir()
        (self.source / "plan.md").write_text("same bytes\n", encoding="utf-8")
        (self.destination / "plans").mkdir()
        (self.destination / "plans/plan.md").write_text(
            "same bytes\n", encoding="utf-8"
        )
        digest = COMPARE.sha256_file(self.source / "plan.md")
        self.inventory: Dict[str, Any] = {
            "schema_version": 1,
            "inventory_id": "inventory-1",
            "items": [
                {
                    "item_id": "item-1",
                    "source_root": "legacy",
                    "source_relpath": "plan.md",
                    "kind": "file",
                    "sha256": digest,
                    "symlink_target": None,
                }
            ],
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_complete_copy_map_passes(self) -> None:
        """Matching retained source and destination bytes produce a valid report."""

        migration_map = {
            "schema_version": 1,
            "inventory_id": "inventory-1",
            "items": [
                {
                    "item_id": "item-1",
                    "disposition": "copy",
                    "destination_root": "records",
                    "destination_relpath": "plans/plan.md",
                }
            ],
        }
        report = COMPARE.compare(
            self.inventory,
            migration_map,
            {"legacy": self.source},
            {"records": self.destination},
        )
        self.assertTrue(report["valid"], report["findings"])
        self.assertEqual(report["counts"]["checked"], 1)

    def test_missing_and_unapproved_items_fail(self) -> None:
        """A missing map row or an unapproved exclusion is never green."""

        missing = COMPARE.compare(
            self.inventory,
            {"inventory_id": "inventory-1", "items": []},
            {"legacy": self.source},
            {},
        )
        self.assertFalse(missing["valid"])
        self.assertIn(
            "missing-map-item", {item["rule"] for item in missing["findings"]}
        )

        excluded_map = {
            "inventory_id": "inventory-1",
            "items": [{"item_id": "item-1", "disposition": "exclude", "reason": ""}],
        }
        excluded = COMPARE.compare(
            self.inventory, excluded_map, {"legacy": self.source}, {}
        )
        self.assertFalse(excluded["valid"])
        self.assertIn(
            "unapproved-exclusion", {item["rule"] for item in excluded["findings"]}
        )


class PostcheckTests(unittest.TestCase):
    """Verify physical-root and route assertions without migration prose."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.target = base / "target"
        self.target.mkdir()
        external = base / "external"
        authority = base / "authority.json"
        authority.write_text(
            '{"authoritative_layout":"physical-aw-v2"}\n', encoding="utf-8"
        )
        receipt = base / "receipt.json"
        receipt.write_text(
            '{"phase":"verified","legacy_writer_enabled":false,"rollback_ready":true}\n',
            encoding="utf-8",
        )
        adapter = base / "adapter.md"
        adapter.write_text("Read .aw/system/workflows/example.md\n", encoding="utf-8")
        adapter_manifest = base / "adapters.json"
        adapter_manifest.write_text(
            json.dumps({"adapters": [str(adapter)]}), encoding="utf-8"
        )
        plan_output = self.target / ".aw/records/plans/plan.md"
        plan_output.parent.mkdir(parents=True)
        plan_output.write_text("plan\n", encoding="utf-8")
        action_output = self.target / ".aw/state/durable/actions/setup.json"
        action_output.parent.mkdir(parents=True)
        action_output.write_text("{}\n", encoding="utf-8")
        self.context: Dict[str, Any] = {
            "target_repo": str(self.target),
            "authority_file": str(authority),
            "transaction_receipt": str(receipt),
            "adapter_manifest": str(adapter_manifest),
            "roots": {
                "system": {
                    "path": str(self.target / ".aw/system"),
                    "git_policy": "tracked",
                },
                "config_project": {
                    "path": str(self.target / ".aw/config"),
                    "git_policy": "tracked",
                },
                "config_local": {
                    "path": str(external / "config/local.json"),
                    "git_policy": "untracked",
                },
                "state_durable": {
                    "path": str(self.target / ".aw/state/durable"),
                    "git_policy": "tracked",
                },
                "state_runtime": {
                    "path": str(external / "state/runtime"),
                    "git_policy": "untracked",
                },
                "records": {
                    "path": str(self.target / ".aw/records"),
                    "git_policy": "tracked",
                },
            },
            "migration": {
                "phase": "verified",
                "legacy_writer_enabled": False,
                "rollback_ready": True,
            },
            "producer_routes": [
                {
                    "producer": "plans",
                    "logical_destination": "records/plans",
                    "verified": True,
                    "observed_path": str(plan_output),
                },
                {
                    "producer": "actions",
                    "logical_destination": "state/durable/actions",
                    "verified": True,
                    "observed_path": str(action_output),
                },
            ],
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_clean_context_passes(self) -> None:
        """A separated authoritative context with verified routes is valid."""

        report = POSTCHECK.check_context(self.context)
        self.assertTrue(report["valid"], report["findings"])
        self.assertRegex(report["postcheck_id"], r"^[0-9a-f]{64}$")
        reordered = dict(reversed(list(self.context.items())))
        self.assertEqual(
            report["postcheck_id"], POSTCHECK.check_context(reordered)["postcheck_id"]
        )

    def test_fabricated_clean_context_fails_without_external_evidence(self) -> None:
        """Self-reported clean fields cannot replace authority and receipt artifacts."""

        self.context.pop("authority_file")
        self.context.pop("transaction_receipt")
        self.context["authoritative_layout"] = "physical-aw-v2"
        self.context["migration"] = {
            "phase": "verified",
            "legacy_writer_enabled": False,
            "rollback_ready": True,
        }
        report = POSTCHECK.check_context(self.context)
        rules = {item["rule"] for item in report["findings"]}
        self.assertFalse(report["valid"])
        self.assertIn("authority-evidence-missing", rules)
        self.assertIn("migration-evidence-missing", rules)

    def test_copied_adapter_logic_and_wrong_git_owner_fail(self) -> None:
        """Postcheck reads adapter bytes and actual Git ownership."""

        manifest = Path(self.context["adapter_manifest"])
        adapter = Path(json.loads(manifest.read_text())["adapters"][0])
        adapter.write_text("# Workflow:\n" + "copied\n" * 90, encoding="utf-8")
        self.context["producer_routes"][0]["git_owner"] = str(self.target)
        report = POSTCHECK.check_context(self.context)
        rules = {item["rule"] for item in report["findings"]}
        self.assertIn("adapter-copied-logic", rules)
        self.assertIn("wrong-git-index", rules)

    def test_tracked_runtime_and_legacy_route_fail(self) -> None:
        """Prohibited tracking and legacy writes produce stable failures."""

        self.context["roots"]["state_runtime"]["git_policy"] = "tracked"
        self.context["producer_routes"].append(
            {
                "producer": "bad-plan-writer",
                "logical_destination": ".agents/plans/pending",
                "verified": True,
                "observed_path": str(self.target / ".aw/records/plans/plan.md"),
            }
        )
        report = POSTCHECK.check_context(self.context)
        self.assertFalse(report["valid"])
        rules = {item["rule"] for item in report["findings"]}
        self.assertIn("prohibited-tracking-policy", rules)
        self.assertIn("producer-legacy-write", rules)


class ScenarioCatalogTests(unittest.TestCase):
    """Keep the initial acceptance catalog machine-readable and citation-safe."""

    def test_scenario_ids_are_unique_and_complete(self) -> None:
        """Every scenario has required routing fields and a unique stable ID."""

        payload = json.loads(
            (TOOLS_DIR / "migration-scenarios.json").read_text(encoding="utf-8")
        )
        scenarios = payload["scenarios"]
        ids = [item["id"] for item in scenarios]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 44)
        for item in scenarios:
            self.assertTrue(item["name"])
            self.assertTrue(item["preset"])
            self.assertTrue(item["expected"])
            self.assertTrue(item["orders"])

    def test_legacy_crosswalk_assertions_bind_to_scenarios(self) -> None:
        """Every retained old behavior has a concrete expected-token assertion."""

        payload = json.loads(
            (TOOLS_DIR / "migration-scenarios.json").read_text(encoding="utf-8")
        )
        by_id = {item["id"]: item for item in payload["scenarios"]}
        crosswalk = payload["legacy_crosswalk"]
        self.assertEqual([row["legacy_id"] for row in crosswalk], list(range(1, 26)))
        for row in crosswalk:
            tokens = {
                token
                for scenario_id in row["scenarios"]
                for token in by_id[scenario_id]["expected"]
            }
            self.assertTrue(set(row["assertions"]).issubset(tokens), row)


if __name__ == "__main__":
    unittest.main()
