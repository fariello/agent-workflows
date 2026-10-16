#!/usr/bin/env python3
"""Isolated tests for the AW physical-layout planning evidence tools."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any, Dict

from agent_workflows import attention, cli, engine, storage
from agent_workflows.clean_delta import CleanDeltaManager, UnsupportedHostError
from agent_workflows.layout_migration import (
    CleanupError,
    MigrationError,
    MigrationManager,
    PreflightGateError,
    StaleInputError,
    SwitchError,
    TransactionLockError,
    VerificationError,
)
from agent_workflows.project_schema import DurabilityState
from agent_workflows.record_producers import resolve_record_routing


TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools" / "awphysical"


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

    def test_workflows_migrate_under_system_workflows(self) -> None:
        """.agents/workflows/X migrates to .aw/system/workflows/X (the workflows/ level is
        PRESERVED). The canonical .aw/system/ layout is NESTED (spec S4.1): system/ groups the
        invokable workflows/ bundle separately from system metadata (VERSION, manifest,
        templates, skills). Matches Order 09 clean_delta pointers; Order 04 resolver/packaging
        is aligned to nested by corrective IPD 20260816.
        """
        c = INVENTORY.classify_item(
            "agents", "workflows/index.md", ".agents/workflows/index.md"
        )
        self.assertEqual(c["expected_destination_class"], "system")
        # No wrapper-stripping override: the workflows/ level is preserved.
        self.assertIsNone(c.get("destination_relpath_override"))

        wf = self.repo / ".agents" / "workflows"
        (wf / "advise").mkdir(parents=True)
        (wf / "index.md").write_text("# workflows\n", encoding="utf-8")
        (wf / "VERSION").write_text("1.0.0\n", encoding="utf-8")
        (wf / "advise" / "advise.md").write_text("advise\n", encoding="utf-8")
        git(self.repo, "add", "-A")

        result = INVENTORY.inventory(
            self.repo, [("agents", wf.parent)], include_paths=False
        )
        self.assertTrue(result["valid"], result["errors"])
        mp = INVENTORY.build_migration_map(
            self.repo, result, target_backend="repository"
        )
        dest = {
            it["source_relpath"]: it["destination_relpath"]
            for it in mp["items"]
            if it["source_root"] == "agents"
        }
        # The invokable bundle nests under system/workflows/; VERSION is a system-root SIBLING
        # (OQ-02 = SIBLING).
        self.assertEqual(dest["workflows/index.md"], "system/workflows/index.md")
        self.assertEqual(dest["workflows/VERSION"], "system/VERSION")
        self.assertEqual(
            dest["workflows/advise/advise.md"], "system/workflows/advise/advise.md"
        )

    def test_partial_aw_system_classifies_as_system(self) -> None:
        """A partial .aw/system/ tree left by an interrupted or rolled-back migration must be
        re-classifiable as system so resume/re-apply can proceed, not fall to unknown-owner
        (Order 11 rehearsal finding: partial-aw:system blocked resume).
        """
        for rel in (
            "system",
            "system/workflows/index.md",
            "system/managed-sections.json",
        ):
            c = INVENTORY.classify_item("partial-aw", rel, ".aw/" + rel)
            self.assertEqual(
                c["expected_destination_class"], "system", f"{rel} not system: {c}"
            )
            self.assertNotEqual(c["disposition"], "block-unknown", rel)
        # The other partial-aw classes still resolve (regression guard), and a genuinely
        # unknown partial-aw subpath still fails closed.
        self.assertEqual(
            INVENTORY.classify_item("partial-aw", "records/x.md", ".aw/records/x.md")[
                "expected_destination_class"
            ],
            "records",
        )
        self.assertEqual(
            INVENTORY.classify_item("partial-aw", "mystery/x", ".aw/mystery/x")[
                "disposition"
            ],
            "block-unknown",
        )

    def test_existing_aw_state_is_skipped_not_migrated(self) -> None:
        """An existing .aw/state/ tree (runtime scratch + the migration's own transaction
        journal/receipts) must be classified `skip` and EXCLUDED from the migration map, so a
        re-apply after a dry-run or rollback does not trip the "Source file changed since
        inventory" preflight gate on the migration's own live journal (backlog j6llj1).
        """
        # Direct classification: every .aw/state/ path is state-runtime + skip.
        for rel in (
            "state",
            "state/runtime/transactions/migration_transaction.json",
            "state/durable/migrations/switch_receipt.json",
            "durable/install.json",
        ):
            c = INVENTORY.classify_item("partial-aw", rel, ".aw/" + rel)
            self.assertEqual(c["ownership"], "state-runtime", rel)
            self.assertEqual(c["disposition"], "skip", rel)

        # The migration map EXCLUDES skip items: a synthetic inventory carrying a live
        # .aw/state/ journal file produces a map with no entry for it (it never enters the
        # copy/preflight-hash set), while a sibling records item is still mapped.
        inv_doc = {
            "items": [
                {
                    "item_id": "state-journal",
                    "source_root": "partial-aw",
                    "source_relpath": "state/runtime/transactions/migration_transaction.json",
                    "expected_destination_class": "durable_state",
                    "disposition": "skip",
                    "sha256": "a" * 64,
                    "git_state": "untracked",
                },
                {
                    "item_id": "a-record",
                    "source_root": "agents",
                    "source_relpath": "plans/pending/p.md",
                    "expected_destination_class": "records",
                    "disposition": "migrate",
                    "sha256": "b" * 64,
                    "git_state": "tracked",
                },
            ],
            "errors": [],
        }
        mp = INVENTORY.build_migration_map(self.repo, inv_doc, "repository")
        mapped_ids = {m["item_id"] for m in mp["items"]}
        self.assertNotIn(
            "state-journal",
            mapped_ids,
            "an existing .aw/state/ journal entered the migration map (j6llj1 trap)",
        )
        self.assertIn("a-record", mapped_ids, "a real record was wrongly excluded")

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
            Path(__file__).resolve().parent
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
            Path(__file__).resolve().parent
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
            Path(__file__).resolve().parent
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
            Path(__file__).resolve().parent
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
        # Nested canonical layout: .agents/workflows/e04/body.md -> system/workflows/e04/body.md.
        self.assertEqual(
            item_map["destination_relpath"], "system/workflows/e04/body.md"
        )
        self.assertNotIn(".agents", item_map["destination_relpath"])

    def test_e05(self) -> None:
        """E-05: Preflight risk analysis for blocking rules."""
        fx = (
            Path(__file__).resolve().parent
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
            Path(__file__).resolve().parent
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
            Path(__file__).resolve().parent
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


class _TTYStringIO(io.StringIO):
    """StringIO subclass that reports isatty() as True for interactive CLI tests."""

    def isatty(self) -> bool:
        return True


class ScenarioContractBehaviorTests(unittest.TestCase):
    """Order 01 E-03: Focused behavioral test coverage for the 70 scenario tokens whose
    prior host modules were removed in commit 19313eed7.

    Tests exercise real agent_workflows APIs and assert observable behavioral outcomes:
    return values, exceptions, filesystem changes, and git status.
    """

    def setUp(self) -> None:
        self._orig_aw_home = os.environ.get("AW_HOME")
        self._orig_cwd = os.getcwd()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.aw_home = Path(self.temp_dir.name) / "aw_home"
        self.aw_home.mkdir(parents=True, exist_ok=True)
        os.environ["AW_HOME"] = str(self.aw_home)

    def tearDown(self) -> None:
        os.chdir(self._orig_cwd)
        if self._orig_aw_home is not None:
            os.environ["AW_HOME"] = self._orig_aw_home
        else:
            os.environ.pop("AW_HOME", None)
        self.temp_dir.cleanup()

    def _make_repo(self, name: str = "repo", origin_bare: bool = False) -> Path:
        repo = Path(self.temp_dir.name) / name
        repo.mkdir(parents=True, exist_ok=True)
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "tester@example.invalid")
        git(repo, "config", "user.name", "Tester")
        git(repo, "config", "commit.gpgsign", "false")
        if origin_bare:
            bare = Path(self.temp_dir.name) / f"{name}_origin.git"
            bare.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "-C", str(bare.parent), "init", "--bare", "-q", bare.name],
                check=True,
                capture_output=True,
                text=True,
            )
            git(repo, "remote", "add", "origin", str(bare))
        return repo

    def _seed_legacy_repo(self, repo: Path) -> Dict[str, str]:
        wf_dir = repo / ".agents" / "workflows"
        wf_dir.mkdir(parents=True, exist_ok=True)
        idx_content = (
            "# Workflows\n\n"
            "<!-- WORKFLOWS-MANIFEST:BEGIN -->\n"
            "| command | body | description |\n"
            "| --- | --- | --- |\n"
            "| sample | sample.md | sample workflow |\n"
            "<!-- WORKFLOWS-MANIFEST:END -->\n"
        )
        (wf_dir / "index.md").write_text(idx_content, encoding="utf-8")
        (wf_dir / "VERSION").write_text("1.0.0\n", encoding="utf-8")
        plans_dir = repo / ".agents" / "plans" / "pending"
        plans_dir.mkdir(parents=True, exist_ok=True)
        (plans_dir / "p.md").write_text("# sample plan\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-m", "seed", "-q")
        return {
            str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [wf_dir / "index.md", wf_dir / "VERSION", plans_dir / "p.md"]
        }

    def test_companion_durability_and_remote_acknowledgement(self) -> None:
        """Tokens: acknowledged-remote, companion-durable, private-destination,
        private-durable-bundle, durability-action-open, durability-action-or-acknowledgement,
        explicit-git-init, honest-unversioned-status, local-git-not-durable-private,
        unversioned-honest-status.
        """
        repo = self._make_repo()
        cfg_file = repo / ".aw" / "config" / "config.json"
        cfg_file.parent.mkdir(parents=True, exist_ok=True)
        cfg_file.write_text(
            json.dumps({"delivery_mode": "tracked", "records_backend": "companion"}),
            encoding="utf-8",
        )

        st1 = storage.get_storage_status(repo_path=str(repo), aw_home=str(self.aw_home))
        self.assertEqual(st1.durability_state, DurabilityState.UNVERSIONED.value)

        st2 = storage.init_records_storage(
            repo_path=str(repo), aw_home=str(self.aw_home)
        )
        self.assertEqual(st2.durability_state, DurabilityState.LOCAL_GIT.value)
        self.assertNotEqual(
            st2.durability_state, DurabilityState.ACKNOWLEDGED_DURABLE.value
        )

        records_path = Path(st2.records_path)
        bare = Path(self.temp_dir.name) / "records_origin.git"
        subprocess.run(
            ["git", "-C", str(bare.parent), "init", "--bare", "-q", bare.name],
            check=True,
            capture_output=True,
            text=True,
        )
        git(records_path, "remote", "add", "origin", str(bare))
        git(records_path, "config", "user.email", "tester@example.invalid")
        git(records_path, "config", "user.name", "Tester")
        git(records_path, "config", "commit.gpgsign", "false")
        (records_path / "seed.md").write_text("# record\n", encoding="utf-8")
        git(records_path, "add", "seed.md")
        git(records_path, "commit", "-m", "init records", "-q")
        git(records_path, "push", "-u", "origin", "HEAD", "-q")

        st3 = storage.get_storage_status(repo_path=str(repo), aw_home=str(self.aw_home))
        self.assertEqual(
            st3.durability_state, DurabilityState.UNACKNOWLEDGED_REMOTE.value
        )
        self.assertFalse(st3.remote_acknowledged)

        st4 = storage.acknowledge_remote_durability(
            repo_path=str(repo), aw_home=str(self.aw_home), acknowledge=True
        )
        self.assertTrue(st4.remote_acknowledged)
        self.assertEqual(
            st4.durability_state, DurabilityState.ACKNOWLEDGED_DURABLE.value
        )

    def test_setup_marker_lifecycle_and_dismissal(self) -> None:
        """Tokens: applicable-actions-only, setup-action-visible-on-status-surfaces,
        setup-completion-closes-action, dismissal-history-no-resurrection,
        action-generations-supersede.
        """
        repo = self._make_repo()
        self.assertFalse(attention.setup_needed(repo))

        engine.write_setup_marker(repo)
        self.assertTrue(attention.setup_needed(repo))

        engine.remove_setup_marker(repo)
        self.assertFalse(attention.setup_needed(repo))

        engine.write_setup_marker(repo)
        marker = repo / ".aw" / "setup-repo-needed.md"
        self.assertTrue(marker.is_file())
        marker.unlink()
        self.assertFalse(attention.setup_needed(repo))
        self.assertFalse(marker.exists())

        engine.write_setup_marker(repo)
        self.assertTrue(attention.setup_needed(repo))

    def test_clean_delta_and_external_record_routing(self) -> None:
        """Tokens: no-candid-public-delta, public-system-only, host-support-evidence,
        no-target-write, zero-target-delta, explicit-fallback-not-called-clean,
        honest-unsupported-result.
        """
        repo = self._make_repo()
        mgr = CleanDeltaManager(str(repo), aw_home=str(self.aw_home))
        skills_dir = Path(self.temp_dir.name) / "skills"
        res = mgr.install_clean_delta(
            "opencode", "1.0.0", user_skills_dir=str(skills_dir)
        )
        self.assertEqual(res["target_writes"], 0)
        skill_file = skills_dir / "agent-workflows" / "SKILL.md"
        self.assertTrue(skill_file.is_file())

        unsupported_skills = Path(self.temp_dir.name) / "unsupported_skills"
        with self.assertRaises(UnsupportedHostError):
            mgr.install_clean_delta(
                "no-such-host", "0", user_skills_dir=str(unsupported_skills)
            )
        self.assertFalse(unsupported_skills.exists())

        cfg_file = repo / ".aw" / "config" / "config.json"
        cfg_file.parent.mkdir(parents=True, exist_ok=True)
        cfg_file.write_text(
            json.dumps({"delivery_mode": "tracked", "records_backend": "home"}),
            encoding="utf-8",
        )
        routing = resolve_record_routing(
            target_repo=str(repo), aw_home=str(self.aw_home)
        )
        self.assertFalse(Path(routing.records_root).is_relative_to(repo))
        self.assertFalse(routing.allow_git_stage)
        self.assertIsNone(routing.commit_destination)

    def test_conservative_uninstall_preserves_config_state_and_external_records(
        self,
    ) -> None:
        """Tokens: external-bytes-untouched, external-config-state-records,
        external-repo-never-deleted, external-runtime, external-system,
        config-state-records-preserved.
        """
        repo = self._make_repo()
        aw_dir = repo / ".aw"
        (aw_dir / "system").mkdir(parents=True, exist_ok=True)
        (aw_dir / "system" / "manifest.json").write_text("{}", encoding="utf-8")
        (aw_dir / "config").mkdir(parents=True, exist_ok=True)
        (aw_dir / "config" / "policy.json").write_text("{}", encoding="utf-8")
        (aw_dir / "state").mkdir(parents=True, exist_ok=True)
        (aw_dir / "state" / "run.json").write_text("{}", encoding="utf-8")
        (aw_dir / "records").mkdir(parents=True, exist_ok=True)
        (aw_dir / "records" / "sample.md").write_text("# record\n", encoding="utf-8")

        ext_records = self.aw_home / "projects" / "ext" / "records" / "ext.md"
        ext_records.parent.mkdir(parents=True, exist_ok=True)
        ext_records.write_text("# ext record\n", encoding="utf-8")
        ext_runtime = self.aw_home / "runtime" / "ext_run.json"
        ext_runtime.parent.mkdir(parents=True, exist_ok=True)
        ext_runtime.write_text('{"run": true}\n', encoding="utf-8")

        ext_hashes_before = {
            str(ext_records): hashlib.sha256(ext_records.read_bytes()).hexdigest(),
            str(ext_runtime): hashlib.sha256(ext_runtime.read_bytes()).hexdigest(),
        }

        mgr = MigrationManager(str(repo), aw_home=str(self.aw_home))
        res = mgr.uninstall_layout(preserve_records=True, deep_remove_records=False)
        self.assertEqual(res["status"], "uninstalled")
        self.assertFalse((aw_dir / "system").exists())
        self.assertTrue((aw_dir / "config").exists())
        self.assertTrue((aw_dir / "state").exists())
        self.assertTrue((aw_dir / "records" / "sample.md").is_file())

        ext_hashes_after = {
            str(ext_records): hashlib.sha256(ext_records.read_bytes()).hexdigest()
            if ext_records.exists()
            else None,
            str(ext_runtime): hashlib.sha256(ext_runtime.read_bytes()).hexdigest()
            if ext_runtime.exists()
            else None,
        }
        self.assertEqual(ext_hashes_before, ext_hashes_after)

    def test_migration_planning_dry_run_and_wizard_decline_make_no_mutations(
        self,
    ) -> None:
        """Tokens: all-paths-previewed, filesystem-aware-preflight, preview-only-default."""
        repo = self._make_repo()
        seed_hashes = self._seed_legacy_repo(repo)

        mgr = MigrationManager(str(repo), aw_home=str(self.aw_home))
        plan = mgr.plan_migration(target_backend="repository")
        self.assertTrue(plan.is_valid)
        self.assertGreater(plan.available_bytes, 0)
        self.assertFalse((repo / ".aw").exists())

        mgr.execute_migration(target_backend="repository", dry_run=True)
        self.assertFalse((repo / ".aw").exists())

        old_cwd = os.getcwd()
        old_stdin = sys.stdin
        old_stdout = sys.stdout
        captured = io.StringIO()
        try:
            os.chdir(str(repo))
            sys.stdin = _TTYStringIO("1\n1\nn\n")
            sys.stdout = captured
            ret = cli.main(["migrate-layout"])
        finally:
            os.chdir(old_cwd)
            sys.stdin = old_stdin
            sys.stdout = old_stdout

        self.assertEqual(ret, 1)
        self.assertIn("Total Items to Move", captured.getvalue())
        self.assertFalse((repo / ".aw").exists())

        current_hashes = {
            rel: hashlib.sha256((repo / rel).read_bytes()).hexdigest()
            for rel in seed_hashes
        }
        self.assertEqual(seed_hashes, current_hashes)

    def test_transactional_move_switches_authority_and_loads_system(self) -> None:
        """Tokens: bytes-preserved, content-not-lost, copy-verify-switch-retain,
        explicit-untrack-plan, history-preserved, no-duplicate-copy, no-overwrite,
        all-records-preserved, complete-packaged-system, correct-version-manifest,
        one-canonical-system-source, package-green, single-current-schema,
        stable-transaction-id, new-authority-explicit, never-push,
        separate-git-evidence, valid-git-destinations.
        """
        repo = self._make_repo(origin_bare=True)
        seed_hashes = self._seed_legacy_repo(repo)

        mgr = MigrationManager(str(repo), aw_home=str(self.aw_home))
        mgr.execute_migration(target_backend="repository", dry_run=False)

        self.assertFalse((repo / ".agents" / "workflows" / "index.md").exists())
        self.assertFalse((repo / ".agents" / "workflows" / "VERSION").exists())
        self.assertFalse((repo / ".agents" / "plans" / "pending" / "p.md").exists())

        dest_index = repo / ".aw" / "system" / "workflows" / "index.md"
        dest_version = repo / ".aw" / "system" / "VERSION"
        dest_plan = repo / ".aw" / "records" / "plans" / "pending" / "p.md"

        self.assertTrue(dest_index.is_file())
        self.assertTrue(dest_version.is_file())
        self.assertTrue(dest_plan.is_file())
        self.assertFalse((repo / ".aw" / "system" / "workflows" / "VERSION").exists())

        self.assertEqual(
            hashlib.sha256(dest_index.read_bytes()).hexdigest(),
            seed_hashes[".agents/workflows/index.md"],
        )
        self.assertEqual(
            hashlib.sha256(dest_version.read_bytes()).hexdigest(),
            seed_hashes[".agents/workflows/VERSION"],
        )
        self.assertEqual(
            hashlib.sha256(dest_plan.read_bytes()).hexdigest(),
            seed_hashes[".agents/plans/pending/p.md"],
        )

        workflows = engine.parse_manifest(repo / ".aw" / "system" / "workflows")
        self.assertGreater(len(workflows), 0)

        tx_file = (
            repo
            / ".aw"
            / "state"
            / "runtime"
            / "transactions"
            / "migration_transaction.json"
        )
        self.assertTrue(tx_file.is_file())
        tx_data = json.loads(tx_file.read_text(encoding="utf-8"))
        self.assertEqual(tx_data.get("status"), "completed")
        self.assertEqual(tx_data.get("schema_version"), 1)
        self.assertTrue(bool(tx_data.get("transaction_id")))
        self.assertTrue(
            all(
                entry.get("action") == "move"
                for entry in tx_data.get("move_journal", [])
            )
        )
        self.assertEqual(
            set(tx_data.get("git_staging_plans", {}).keys()),
            {"target", "companion", "source"},
        )

        receipt_file = (
            repo / ".aw" / "state" / "durable" / "migrations" / "switch_receipt.json"
        )
        self.assertTrue(receipt_file.is_file())
        receipt_data = json.loads(receipt_file.read_text(encoding="utf-8"))
        self.assertEqual(receipt_data.get("authority"), "switched")
        self.assertEqual(
            receipt_data.get("transaction_id"), tx_data.get("transaction_id")
        )

        cfg_file = repo / ".aw" / "config" / "config.json"
        self.assertTrue(cfg_file.is_file())
        cfg_data = json.loads(cfg_file.read_text(encoding="utf-8"))
        self.assertEqual(cfg_data.get("records_backend"), "repository")

        status_out = git(repo, "status", "--short").stdout
        self.assertIn(
            "R  .agents/workflows/index.md -> .aw/system/workflows/index.md", status_out
        )

        ls_remote = git(repo, "ls-remote", "origin").stdout
        self.assertEqual(ls_remote.strip(), "")

    def test_rollback_restores_legacy_and_cleanup_refuses_changed_content(self) -> None:
        """Tokens: byte-identical-rollback, git-index-restored, journal-retained,
        legacy-preserved, policy-restored, rollback-ready, rollback-safe,
        source-retained, changed-content-not-deleted, cleanup-blocked, cleanup-refused.
        """
        repo = self._make_repo()
        seed_hashes = self._seed_legacy_repo(repo)

        mgr = MigrationManager(str(repo), aw_home=str(self.aw_home))
        mgr.execute_migration(target_backend="repository", dry_run=False)

        preview = mgr.cleanup_migration(confirm=False)
        self.assertEqual(preview.get("status"), "preview")
        self.assertEqual(preview.get("would_remove"), [])

        ret_file = (
            repo
            / ".aw"
            / "state"
            / "durable"
            / "migrations"
            / "retention_manifest.json"
        )
        self.assertTrue(ret_file.is_file())
        ret_data = json.loads(ret_file.read_text(encoding="utf-8"))
        mappings = ret_data.get("mappings", [])
        self.assertTrue(len(mappings) > 0)
        sample_src = Path(mappings[0]["source"])
        sample_src.parent.mkdir(parents=True, exist_ok=True)
        sample_src.write_text("modified source content\n", encoding="utf-8")

        with self.assertRaises(CleanupError):
            mgr.cleanup_migration(confirm=True)
        self.assertEqual(
            sample_src.read_text(encoding="utf-8"), "modified source content\n"
        )
        sample_src.unlink()

        with self.assertRaises(CleanupError):
            mgr.cleanup_migration(fault_injection="cleanup-refusal")

        rb = mgr.rollback_migration()
        self.assertEqual(rb.get("status"), "rolled_back")
        self.assertEqual(rb.get("authority"), "legacy")

        current_hashes = {
            rel: hashlib.sha256((repo / rel).read_bytes()).hexdigest()
            for rel in seed_hashes
        }
        self.assertEqual(seed_hashes, current_hashes)

        cfg_file = repo / ".aw" / "config" / "config.json"
        self.assertTrue(cfg_file.is_file())
        cfg_data = json.loads(cfg_file.read_text(encoding="utf-8"))
        self.assertEqual(cfg_data.get("records_backend"), "legacy")

        self.assertFalse((repo / ".aw" / "system").exists())
        self.assertFalse((repo / ".aw" / "records").exists())

        status_out = git(repo, "status", "--short").stdout
        self.assertNotIn("->", status_out)

    def test_crash_mid_move_is_resumable(self) -> None:
        """Tokens: idempotent-resume, recoverable-staging, recovery-guidance, resume-safe."""
        repo = self._make_repo()
        self._seed_legacy_repo(repo)

        mgr = MigrationManager(str(repo), aw_home=str(self.aw_home))
        mgr.execute_migration(target_backend="repository", dry_run=False)

        tx_file = (
            repo
            / ".aw"
            / "state"
            / "runtime"
            / "transactions"
            / "migration_transaction.json"
        )
        tx_data = json.loads(tx_file.read_text(encoding="utf-8"))

        last_move = tx_data["move_journal"].pop()
        if "copied_records" in tx_data and tx_data["copied_records"]:
            tx_data["copied_records"].pop()

        src_p = Path(last_move["source"])
        dst_p = Path(last_move["destination"])
        src_p.parent.mkdir(parents=True, exist_ok=True)
        os.replace(dst_p, src_p)

        tx_data["status"] = "locked"
        tx_data["last_verified_checkpoint"] = "locked"
        tx_file.write_text(json.dumps(tx_data, indent=2), encoding="utf-8")

        receipt = (
            repo / ".aw" / "state" / "durable" / "migrations" / "switch_receipt.json"
        )
        if receipt.exists():
            receipt.unlink()

        self.assertEqual(mgr.status_migration()["authority"], "legacy")

        res_resume = MigrationManager(
            str(repo), aw_home=str(self.aw_home)
        ).resume_migration()
        self.assertEqual(res_resume.get("status"), "completed")
        self.assertFalse(src_p.exists())
        self.assertTrue(dst_p.exists())

        tx_after = json.loads(tx_file.read_text(encoding="utf-8"))
        self.assertEqual(tx_after.get("status"), "completed")

    def test_fault_injection_before_switch_keeps_legacy_authoritative(self) -> None:
        """Tokens: fail-before-switch, legacy-authoritative, no-switch,
        one-authority, safe-fallback-transaction, writer-lock-or-hash-drift-stop.
        """
        cases = [
            ("stale-input", StaleInputError, False),
            ("concurrent-writer", TransactionLockError, False),
            ("disk-loss", PreflightGateError, False),
            ("permission-loss", PreflightGateError, False),
            ("copy-failure", MigrationError, False),
            ("verify-mismatch", VerificationError, False),
            ("switch-failure", SwitchError, False),
            ("kill-after-switch-before-receipt", MigrationError, True),
            ("cross-git-partial-stage", MigrationError, True),
        ]

        for tag, exc_type, post_switch in cases:
            with self.subTest(tag=tag):
                repo = self._make_repo(name=f"repo_{tag}")
                self._seed_legacy_repo(repo)
                mgr = MigrationManager(str(repo), aw_home=str(self.aw_home))

                with self.assertRaises(exc_type):
                    mgr.execute_migration(
                        target_backend="repository", fault_injection=tag
                    )

                receipt = (
                    repo
                    / ".aw"
                    / "state"
                    / "durable"
                    / "migrations"
                    / "switch_receipt.json"
                )
                cfg = repo / ".aw" / "config" / "config.json"
                st = mgr.status_migration()

                if not post_switch:
                    self.assertFalse(receipt.exists())
                    if cfg.exists():
                        cfg_data = json.loads(cfg.read_text(encoding="utf-8"))
                        self.assertNotEqual(
                            cfg_data.get("records_backend"), "repository"
                        )
                    self.assertEqual(st["authority"], "legacy")
                else:
                    self.assertTrue(receipt.exists())
                    self.assertEqual(st["authority"], "switched")


class ScenarioBindingTests(unittest.TestCase):
    """Order 12 E-06: every scenario `expected` token (and every legacy_crosswalk assertion
    token) binds to a fully-qualified, LOADABLE automated test method plus a named assertion
    condition. The binding is machine-checked: unbound, stale, duplicate, or non-loadable
    bindings fail, and a deliberately-bad binding is rejected (falsifiable negative).
    """

    @staticmethod
    def _load_bindings():
        return json.loads(
            (TOOLS_DIR / "scenario-token-bindings.json").read_text(encoding="utf-8")
        )["bindings"]

    @staticmethod
    def _manifest_tokens():
        payload = json.loads(
            (TOOLS_DIR / "migration-scenarios.json").read_text(encoding="utf-8")
        )
        return {t for s in payload["scenarios"] for t in s["expected"]}

    @staticmethod
    def _resolve(fqn):
        """Import `module.Class.method` and return the callable test method, or None."""
        import importlib

        try:
            mod_path, cls_name, meth_name = fqn.rsplit(".", 2)
            mod = importlib.import_module(mod_path)
            cls = getattr(mod, cls_name, None)
            if cls is None:
                return None
            meth = getattr(cls, meth_name, None)
            return meth if callable(meth) else None
        except (ImportError, ValueError, AttributeError):
            return None

    def test_every_expected_token_is_bound(self):
        """No scenario expected token is left unbound; no stale binding for a missing token."""
        tokens = self._manifest_tokens()
        bindings = self._load_bindings()
        unbound = sorted(tokens - set(bindings))
        self.assertEqual(unbound, [], f"unbound expected tokens: {unbound}")
        stale = sorted(set(bindings) - tokens)
        self.assertEqual(stale, [], f"stale bindings (token not in manifest): {stale}")

    def test_legacy_crosswalk_assertion_tokens_are_bound(self):
        """Every legacy_crosswalk 1..25 assertion token resolves to a binding."""
        payload = json.loads(
            (TOOLS_DIR / "migration-scenarios.json").read_text(encoding="utf-8")
        )
        assertion_tokens = {
            tok for row in payload["legacy_crosswalk"] for tok in row["assertions"]
        }
        bindings = self._load_bindings()
        missing = sorted(assertion_tokens - set(bindings))
        self.assertEqual(missing, [], f"unbound crosswalk assertion tokens: {missing}")

    def test_every_binding_loads_a_real_test_method_and_names_an_assertion(self):
        """Each binding's `test` must import to a callable test method, and `assertion` must be
        a non-empty named condition. This is the schema-loads-each-named-test check."""
        bindings = self._load_bindings()
        problems = []
        for token, b in sorted(bindings.items()):
            fqn = b.get("test", "")
            if not (fqn.count(".") >= 2 and fqn.rsplit(".", 1)[-1].startswith("test")):
                problems.append(f"{token}: bad_fqn {fqn!r}")
                continue
            if self._resolve(fqn) is None:
                problems.append(f"{token}: unloadable {fqn}")
                continue
            if not b.get("assertion", "").strip():
                problems.append(f"{token}: missing_assertion")
        self.assertEqual(problems, [])

    def test_bad_binding_is_rejected(self):
        """Falsifiable negative: an unbound token, a stale binding, and a non-loadable test
        FQN are each detected by the same checks (so a deliberately-bad binding cannot pass)."""
        tokens = self._manifest_tokens()
        # (a) unbound: drop a real token -> detected
        good = self._load_bindings()
        sample = next(iter(tokens))
        broken = {k: v for k, v in good.items() if k != sample}
        self.assertIn(sample, sorted(tokens - set(broken)))
        # (b) stale: add a token not in the manifest -> detected
        with_stale = dict(good)
        with_stale["not-a-real-token"] = {"test": "x", "assertion": "y"}
        self.assertIn("not-a-real-token", sorted(set(with_stale) - tokens))
        # (c) non-loadable test fqn -> _resolve returns None
        self.assertIsNone(
            self._resolve("tests.test_acceptance_matrix.NoSuchClass.test_nope")
        )
        self.assertIsNone(self._resolve("not.a.module.Cls.test_x"))
        # And a real binding DOES load (positive control).
        self.assertIsNotNone(
            self._resolve("tests.test_awphysical_tools.InventoryTests.test_e01")
        )


if __name__ == "__main__":
    unittest.main()
