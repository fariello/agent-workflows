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

    def test_e02_inventory_prunes_gitignored_dependency_subtree(self) -> None:
        """E-02/V-02: an ignored dependency subtree (node_modules) is pruned, not enumerated.

        A non-ignored sibling under the same root is still inventoried. RED case: without the
        gitignored-dir pruning the thousands of node_modules files would appear.
        """
        # A host-adapter root with a gitignored node_modules subtree and a real shim.
        opencode = self.repo / ".opencode"
        (opencode / "commands").mkdir(parents=True)
        (opencode / "commands" / "assess.md").write_text("shim\n", encoding="utf-8")
        nm = opencode / "node_modules" / "somepkg"
        nm.mkdir(parents=True)
        for i in range(5):
            (nm / f"file{i}.js").write_text("dep\n", encoding="utf-8")
        (self.repo / ".gitignore").write_text(
            ".opencode/node_modules/\n", encoding="utf-8"
        )
        git(self.repo, "add", ".opencode/commands/assess.md", ".gitignore")

        result = INVENTORY.inventory(
            self.repo,
            [("opencode-adapters", self.repo / ".opencode")],
            include_paths=False,
        )
        rels = {item["source_relpath"] for item in result["items"]}
        # The gitignored dependency subtree is entirely absent (pruned, not hashed).
        self.assertFalse(
            any("node_modules" in r for r in rels),
            f"gitignored node_modules leaked into inventory: {sorted(r for r in rels if 'node_modules' in r)}",
        )
        # The real, non-ignored shim under the same root is still inventoried.
        self.assertIn("commands/assess.md", rels)

    def test_e03_infrastructure_files_get_explicit_dispositions(self) -> None:
        """E-03/V-03: README/leak-allowlist/self-install-manifest resolve to decided classes.

        Inventory is valid (no unknown-owner) and each infra file maps to its Order-11
        destination; a genuinely stray .agents file still fails closed as unknown-owner.
        """
        agents = self.repo / ".agents"
        (agents / "workflows").mkdir(parents=True)
        (agents / "workflows" / "index.md").write_text("wf\n", encoding="utf-8")
        (agents / "README.md").write_text("# .agents\n", encoding="utf-8")
        (agents / "local-leaks-allowlist.toml").write_text(
            "# allow\n", encoding="utf-8"
        )
        (agents / "local-leaks-hints.json.example").write_text("{}\n", encoding="utf-8")
        (agents / "agent-workflows").mkdir()
        (agents / "agent-workflows" / "managed-sections.json").write_text(
            "{}\n", encoding="utf-8"
        )
        (agents / "agent-workflows" / "README.md").write_text(
            "# manifest\n", encoding="utf-8"
        )
        git(self.repo, "add", "-A")

        result = INVENTORY.inventory(
            self.repo, [("agents", agents)], include_paths=False
        )
        self.assertTrue(result["valid"], result["errors"])
        mp = INVENTORY.build_migration_map(
            self.repo, result, target_backend="repository"
        )
        dest = {
            it["source_relpath"]: (
                it["destination_root_class"],
                it["destination_relpath"],
            )
            for it in mp["items"]
            if it["source_root"] == "agents"
        }
        self.assertEqual(dest["README.md"], ("doc", "README.md"))
        self.assertEqual(
            dest["local-leaks-allowlist.toml"],
            ("config", "config/local-leaks-allowlist.toml"),
        )
        self.assertEqual(
            dest["agent-workflows/managed-sections.json"],
            ("system", "system/managed-sections.json"),
        )

        # Falsifiable negative: a genuinely stray .agents file still fails closed.
        stray = INVENTORY.classify_item(
            "agents", "stray-thing.xyz", ".agents/stray-thing.xyz"
        )
        self.assertEqual(stray["disposition"], "block-unknown")

    def test_backlog_tree_classifies_as_records(self) -> None:
        """The attention-visible backlog tier (.agents/backlog/, added after the awphysical
        tooling was authored) must classify as records and migrate to records/backlog/, not
        fall through to unknown-owner (Order 11 rehearsal finding; matches artifact_core's
        .agents/backlog -> .aw/records/backlog mapping). A stray .agents subtree still blocks.
        """
        # Direct classification: every backlog path is a records-class migrate.
        for rel in (
            "backlog",
            "backlog/README.md",
            "backlog/open/20260815-x-01-x-thing.md",
            "backlog/done/20260815-y-01-y-thing.md",
            "backlog/parked/20260815-z-01-z-thing.md",
        ):
            c = INVENTORY.classify_item("agents", rel, ".agents/" + rel)
            self.assertEqual(
                c["expected_destination_class"],
                "records",
                f"{rel} did not classify as records: {c}",
            )
            self.assertEqual(c["disposition"], "migrate", rel)
        # _legacy_class agrees (used for conservative human-review classification).
        self.assertEqual(
            INVENTORY._legacy_class("agents", "backlog/open/x.md"), "records"
        )

        # End-to-end: a repo with a backlog tree inventories valid and maps under records/backlog/.
        agents = self.repo / ".agents"
        (agents / "workflows").mkdir(parents=True)
        (agents / "workflows" / "index.md").write_text("wf\n", encoding="utf-8")
        (agents / "backlog" / "open").mkdir(parents=True)
        item = agents / "backlog" / "open" / "20260815-x-01-x-thing.md"
        item.write_text("- Id: x\n- Status: open\n", encoding="utf-8")
        git(self.repo, "add", "-A")

        result = INVENTORY.inventory(
            self.repo, [("agents", agents)], include_paths=False
        )
        self.assertTrue(result["valid"], result["errors"])
        mp = INVENTORY.build_migration_map(
            self.repo, result, target_backend="repository"
        )
        dest = {
            it["source_relpath"]: (
                it["destination_root_class"],
                it["destination_relpath"],
            )
            for it in mp["items"]
            if it["source_root"] == "agents"
        }
        self.assertEqual(
            dest["backlog/open/20260815-x-01-x-thing.md"],
            ("records", "records/backlog/open/20260815-x-01-x-thing.md"),
        )

    def test_host_adapters_preserved_in_place_not_relocated(self) -> None:
        """Host-required discovery files (.claude/, .opencode/, AGENTS.md/CLAUDE.md/GEMINI.md)
        are PRESERVED IN PLACE, not relocated under .aw/adapters/ (spec 20260810-1447-01
        S3.1/S9). Two hosts carrying identically-named command shims must NOT collide, and each
        adapter's destination equals its source path. (Order 11 rehearsal finding.)
        """
        # Direct classification: adapters/pointers are preserve, not migrate.
        for label in ("claude-adapters", "opencode-adapters", "agents-pointer"):
            c = INVENTORY.classify_item(label, "commands/assess.md", None)
            self.assertEqual(c["disposition"], "preserve", f"{label} not preserve: {c}")
            self.assertEqual(
                c["expected_destination_class"], "host-adapter-in-place", label
            )
            # root-of-root case too
            c0 = INVENTORY.classify_item(label, ".", None)
            self.assertEqual(
                c0["disposition"], "preserve", f"{label} root not preserve"
            )

        # End-to-end: two hosts with the SAME command shim path must not collide, and each is
        # preserved at its source path (no adapters/ relocation).
        (self.repo / ".agents" / "workflows").mkdir(parents=True)
        (self.repo / ".agents" / "workflows" / "index.md").write_text(
            "wf\n", encoding="utf-8"
        )
        for host in (".claude", ".opencode"):
            d = self.repo / host / "commands"
            d.mkdir(parents=True)
            # Deliberately DIFFERENT bytes per host so a naive shared-destination map would
            # report a real (non-dedup) destination-collision.
            (d / "assess.md").write_text(f"shim for {host}\n", encoding="utf-8")
        git(self.repo, "add", "-A")

        roots = INVENTORY._default_roots(self.repo)
        result = INVENTORY.inventory(self.repo, roots, include_paths=False)
        self.assertTrue(result["valid"], result["errors"])
        mp = INVENTORY.build_migration_map(
            self.repo, result, target_backend="repository"
        )
        self.assertTrue(mp["valid"], mp["errors"])
        self.assertEqual(
            [e for e in mp["errors"] if e.get("rule") == "destination-collision"],
            [],
            "host adapters collided despite preserve-in-place",
        )
        # Each adapter shim's destination is its own source path (preserved), not adapters/.
        for it in mp["items"]:
            if it["source_root"].endswith("adapters") or it["source_root"].endswith(
                "pointer"
            ):
                self.assertEqual(
                    it["destination_relpath"],
                    it["source_relpath"],
                    f"{it['source_root']}:{it['source_relpath']} was relocated",
                )
                self.assertEqual(it["copy_method"], "preserve")

        # Falsifiable guard: a genuine records destination-collision (two different-byte files
        # mapping to one records path) still fails closed (the fix did not disable collision
        # detection for relocated classes).
        inv2 = {
            "items": [
                {
                    "item_id": "a",
                    "source_root": "agents",
                    "source_relpath": "plans/x.md",
                    "expected_destination_class": "records",
                    "disposition": "migrate",
                    "sha256": "a" * 64,
                    "git_state": "tracked",
                },
                {
                    "item_id": "b",
                    "source_root": "ext-old",
                    "source_relpath": "plans/x.md",
                    "expected_destination_class": "records",
                    "disposition": "migrate",
                    "sha256": "b" * 64,
                    "git_state": "tracked",
                },
            ],
            "errors": [],
        }
        mp2 = INVENTORY.build_migration_map(
            self.repo, inv2, target_backend="repository"
        )
        self.assertFalse(mp2["valid"])
        self.assertTrue(
            any(e.get("rule") == "destination-collision" for e in mp2["errors"])
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

    def test_e01(self) -> None:
        """E-01: Closed legacy-source catalog discovery and unknown owner blocking."""
        fx = (
            Path(__file__).resolve().parent.parent.parent
            / "tests"
            / "fixtures"
            / "awphysical"
            / "order06"
            / "e01-catalog.json"
        )
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        # 1. Positive case: valid legacy tree and external root
        wf = self.repo / ".agents/workflows/valid/body.md"
        wf.parent.mkdir(parents=True)
        wf.write_text("workflow body\n", encoding="utf-8")

        ext_dir = Path(self.temp.name) / "ext_records"
        ext_dir.mkdir()
        (ext_dir / "records/doc.md").parent.mkdir(parents=True)
        (ext_dir / "records/doc.md").write_text("ext record\n", encoding="utf-8")

        res = INVENTORY.inventory(
            self.repo,
            [
                ("agents", self.repo / ".agents"),
                ("ext-records", ext_dir),
            ],
            include_paths=False,
        )

        self.assertTrue(res["valid"], res.get("errors"))
        items = {item["source_relpath"]: item for item in res["items"]}
        self.assertEqual(items["workflows/valid/body.md"]["ownership"], "system")
        self.assertEqual(items["records/doc.md"]["ownership"], "records")

        # 2. Negative case: unknown item in .agents MUST block (valid=False)
        unknown_file = self.repo / ".agents/unknown_stuff.txt"
        unknown_file.write_text("unknown content\n", encoding="utf-8")

        res_bad = INVENTORY.inventory(
            self.repo,
            [("agents", self.repo / ".agents")],
            include_paths=False,
        )

        self.assertFalse(res_bad["valid"])
        err_rules = {e["rule"] for e in res_bad["errors"]}
        self.assertIn("unknown-owner", err_rules)

    def test_e02(self) -> None:
        """E-02: Content-stable inventory output and Git state classification."""
        fx = (
            Path(__file__).resolve().parent.parent.parent
            / "tests"
            / "fixtures"
            / "awphysical"
            / "order06"
            / "e02-stability.json"
        )
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        wf = self.repo / ".agents/workflows/v1/body.md"
        wf.parent.mkdir(parents=True)
        wf.write_text("workflow body\n", encoding="utf-8")

        res1 = INVENTORY.inventory(
            self.repo, [("agents", self.repo / ".agents")], include_paths=False
        )
        res2 = INVENTORY.inventory(
            self.repo, [("agents", self.repo / ".agents")], include_paths=False
        )

        # Content stability check
        self.assertEqual(res1["inventory_id"], res2["inventory_id"])

        # Symlink escape check: recorded as symlink, not followed into escape
        ext_target = Path(self.temp.name) / "outside.txt"
        ext_target.write_text("outside\n", encoding="utf-8")
        os.symlink(ext_target, self.repo / ".agents/sym_outside")

        res3 = INVENTORY.inventory(
            self.repo, [("agents", self.repo / ".agents")], include_paths=False
        )
        self.assertFalse(res3["valid"])
        err_rules = {e["rule"] for e in res3["errors"]}
        self.assertIn("unsafe-symlink", err_rules)

    def test_e03(self) -> None:
        """E-03: Content-aware classification and relative identity preservation."""
        fx = (
            Path(__file__).resolve().parent.parent.parent
            / "tests"
            / "fixtures"
            / "awphysical"
            / "order06"
            / "e03-classification.json"
        )
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        plan = self.repo / ".agents/plans/pending/20260810-test.md"
        plan.parent.mkdir(parents=True)
        plan.write_text("plan content\n", encoding="utf-8")

        res = INVENTORY.inventory(
            self.repo, [("agents", self.repo / ".agents")], include_paths=False
        )
        self.assertTrue(res["valid"])
        item = next(
            i for i in res["items"] if "20260810-test.md" in i["source_relpath"]
        )

        self.assertEqual(item["ownership"], "records")
        self.assertEqual(item["lifecycle_class"], "records")
        self.assertEqual(item["expected_destination_class"], "records")
        self.assertEqual(item["disposition"], "migrate")

    def test_e04(self) -> None:
        """E-04: Source-to-destination map generation and explicit collision handling."""
        fx = (
            Path(__file__).resolve().parent.parent.parent
            / "tests"
            / "fixtures"
            / "awphysical"
            / "order06"
            / "e04-mapping.json"
        )
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        wf = self.repo / ".agents/workflows/e04/body.md"
        wf.parent.mkdir(parents=True)
        wf.write_text("wf e04\n", encoding="utf-8")

        inv_res = INVENTORY.inventory(
            self.repo, [("agents", self.repo / ".agents")], include_paths=False
        )
        map_res = INVENTORY.build_migration_map(
            self.repo, inv_res, target_backend="repository"
        )

        self.assertTrue(map_res["valid"])
        item_map = next(i for i in map_res["items"] if "body.md" in i["source_relpath"])
        self.assertEqual(item_map["destination_root_class"], "system")
        self.assertEqual(
            item_map["destination_relpath"], "system/workflows/e04/body.md"
        )
        self.assertNotIn(".agents", item_map["destination_relpath"])

    def test_e05(self) -> None:
        """E-05: Preflight risk analysis for blocking rules."""
        fx = (
            Path(__file__).resolve().parent.parent.parent
            / "tests"
            / "fixtures"
            / "awphysical"
            / "order06"
            / "e05-risks.json"
        )
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        # Plant unknown owner
        bad_file = self.repo / ".agents/bad_owner.bin"
        bad_file.parent.mkdir(parents=True, exist_ok=True)
        bad_file.write_text("bad\n", encoding="utf-8")

        inv_res = INVENTORY.inventory(
            self.repo, [("agents", self.repo / ".agents")], include_paths=False
        )
        map_res = INVENTORY.build_migration_map(self.repo, inv_res)
        risk_res = INVENTORY.analyze_migration_risks(self.repo, inv_res, map_res)

        self.assertFalse(risk_res["valid"])
        err_rules = {e["rule"] for e in risk_res["errors"]}
        self.assertIn("unknown-owner", err_rules)

    def test_e06(self) -> None:
        """E-06: Human and JSON CLI surfaces with no-write proof."""
        fx = (
            Path(__file__).resolve().parent.parent.parent
            / "tests"
            / "fixtures"
            / "awphysical"
            / "order06"
            / "e06-preview.json"
        )
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        wf = self.repo / ".agents/workflows/e06/body.md"
        wf.parent.mkdir(parents=True, exist_ok=True)
        wf.write_text("wf e06\n", encoding="utf-8")

        out_path = Path(self.temp.name) / "out_plan.json"
        ret = INVENTORY.main(
            ["--repo", str(self.repo), "--plan", "--output", str(out_path)]
        )

        self.assertEqual(ret, 0)
        self.assertTrue(out_path.is_file())

        data = json.loads(out_path.read_text(encoding="utf-8"))
        self.assertTrue(data["valid"])
        self.assertIn("inventory", data)
        self.assertIn("migration_map", data)
        self.assertIn("risk_analysis", data)
        self.assertTrue(data["risk_analysis"]["no_write_proven"])

    def test_e07(self) -> None:
        """E-07: Closed matrix of expected vs actual items and set mismatch blocking."""
        fx = (
            Path(__file__).resolve().parent.parent.parent
            / "tests"
            / "fixtures"
            / "awphysical"
            / "order06"
            / "e07-matrix.json"
        )
        self.assertTrue(fx.is_file(), f"Fixture missing: {fx}")

        wf = self.repo / ".agents/workflows/e07/body.md"
        wf.parent.mkdir(parents=True, exist_ok=True)
        wf.write_text("wf e07\n", encoding="utf-8")

        inv_res = INVENTORY.inventory(
            self.repo, [("agents", self.repo / ".agents")], include_paths=False
        )
        self.assertTrue(inv_res["valid"])
        self.assertEqual(len(inv_res["items"]), 4)  # .agents, workflows, e07, body.md


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
        (external / "config").mkdir(parents=True, exist_ok=True)
        (external / "config" / "local.json").write_text("{}\n", encoding="utf-8")
        (external / "state" / "runtime").mkdir(parents=True, exist_ok=True)
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

    def test_e03(self) -> None:
        """E-03: Postcheck reads authority receipt, transaction receipt, producer paths, adapter bytes, and actual Git ownership."""
        report = POSTCHECK.check_context(self.context)
        self.assertTrue(report["valid"], report["findings"])
        self.assertRegex(report["postcheck_id"], r"^[0-9a-f]{64}$")

        # Fabricated context fails
        bad_ctx = dict(self.context)
        bad_ctx.pop("authority_file")
        bad_report = POSTCHECK.check_context(bad_ctx)
        self.assertFalse(bad_report["valid"])
        self.assertIn(
            "authority-evidence-missing", {f["rule"] for f in bad_report["findings"]}
        )

    def test_e07(self) -> None:
        """E-07: The eleven deceptive fixtures fail mapped rules; clean fixture passes."""
        # Clean passes
        report = POSTCHECK.check_context(self.context)
        self.assertTrue(report["valid"])

        # Test deceptive classes
        bad_adapter = self.target / "bad_adapter.md"
        bad_adapter.write_text("# Workflow:\n" + "copied\n" * 90, encoding="utf-8")
        manifest = self.target / "bad_manifest.json"
        manifest.write_text(
            json.dumps({"adapters": [str(bad_adapter)]}), encoding="utf-8"
        )
        deceptive_ctx = dict(self.context)
        deceptive_ctx["adapter_manifest"] = str(manifest)
        deceptive_report = POSTCHECK.check_context(deceptive_ctx)
        self.assertFalse(deceptive_report["valid"])
        self.assertIn(
            "adapter-copied-logic", {f["rule"] for f in deceptive_report["findings"]}
        )


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
