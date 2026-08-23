"""Unit tests for aw set and typed status transition verbs (ipd/spec/prompt/backlog set)."""

from __future__ import annotations

import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflows import cli


class StatusSetTestBase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aw_test_status_set_")
        self.repo_root = Path(self.temp_dir)
        # Create standard layout
        (self.repo_root / ".aw" / "records" / "plans" / "pending").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo_root / ".aw" / "records" / "plans" / "executed").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo_root / ".aw" / "records" / "prompts" / "pending").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo_root / ".aw" / "records" / "prompts" / "executed").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo_root / ".aw" / "records" / "specs").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo_root / ".aw" / "records" / "backlog" / "open").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo_root / ".aw" / "records" / "backlog" / "done").mkdir(
            parents=True, exist_ok=True
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_plan(
        self,
        filename: str,
        id6: str,
        set_id: str,
        status: str = "draft",
        disposition: str = "pending",
    ) -> Path:
        p = self.repo_root / ".aw" / "records" / "plans" / disposition / filename
        content = f"""# IPD: Test Plan {id6}

- Date: 2026-08-22
- Kind: child
- Status: {status}
- Set: {set_id}
- Order: 1
- Id: {id6}

## Workflow history

- 2026-08-22 draft (author): initial draft.

## Goal
Test goal.
"""
        p.write_text(content, encoding="utf-8")
        return p

    def create_spec(
        self, filename: str, id6: str, set_id: str, status: str = "draft"
    ) -> Path:
        p = self.repo_root / ".aw" / "records" / "specs" / filename
        content = f"""# Spec: Test Spec {id6}

- Date: 2026-08-22
- Status: {status}
- Set: {set_id}
- Id: {id6}

## Workflow history

- 2026-08-22 draft (author): initial spec draft.

## Goal
Test spec goal.
"""
        p.write_text(content, encoding="utf-8")
        return p

    def create_prompt(
        self,
        filename: str,
        id6: str,
        set_id: str,
        status: str = "draft",
        disposition: str = "pending",
    ) -> Path:
        p = self.repo_root / ".aw" / "records" / "prompts" / disposition / filename
        content = f"""# Prompt: Test Prompt {id6}

- Date: 2026-08-22
- Status: {status}
- Set: {set_id}
- Id: {id6}

## Workflow history

- 2026-08-22 draft (author): initial prompt.
"""
        p.write_text(content, encoding="utf-8")
        return p

    def create_backlog(
        self, filename: str, id6: str, set_id: str, status: str = "open"
    ) -> Path:
        p = self.repo_root / ".aw" / "records" / "backlog" / status / filename
        content = f"""# Backlog Item {id6}

- Id: {id6}
- Status: {status}
- Set: {set_id}
- Priority: medium
- Kind: chore
- Summary: Test backlog item

## Workflow history

- 2026-08-22 created: created.
"""
        p.write_text(content, encoding="utf-8")
        return p


class TestStatusSetCommands(StatusSetTestBase):
    def test_set_plan_status_by_id6(self):
        plan = self.create_plan(
            "20260822-testset-01-pl0001-test-plan.ipd.md", "pl0001", "testset", "draft"
        )
        rc = cli.main(
            ["set", "approved", "pl0001", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 0)
        text = plan.read_text(encoding="utf-8")
        self.assertIn("- Status: approved", text)
        self.assertIn("approved (aw set)", text)

    def test_set_plan_status_to_executed_moves_file(self):
        plan = self.create_plan(
            "20260822-testset-01-pl0002-test-plan.ipd.md",
            "pl0002",
            "testset",
            "approved",
        )
        rc = cli.main(
            ["set", "executed", "pl0002", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 0)
        self.assertFalse(plan.exists())
        executed_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "20260822-testset-01-pl0002-test-plan.ipd.md"
        )
        self.assertTrue(executed_path.exists())
        text = executed_path.read_text(encoding="utf-8")
        self.assertIn("- Status: executed", text)

    def test_set_plan_status_from_executed_to_pending_moves_file_back(self):
        plan = self.create_plan(
            "20260822-testset-01-pl0020-test-plan.ipd.md",
            "pl0020",
            "testset",
            "executed",
            disposition="executed",
        )
        rc = cli.main(
            ["set", "to-review", "pl0020", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 0)
        self.assertFalse(plan.exists())
        pending_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260822-testset-01-pl0020-test-plan.ipd.md"
        )
        self.assertTrue(pending_path.exists())
        text = pending_path.read_text(encoding="utf-8")
        self.assertIn("- Status: to-review", text)

    def test_ipd_set_command(self):
        plan = self.create_plan(
            "20260822-testset-01-pl0003-test-plan.ipd.md", "pl0003", "testset", "draft"
        )
        rc = cli.main(
            ["ipd", "set", "approved", "pl0003", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 0)
        text = plan.read_text(encoding="utf-8")
        self.assertIn("- Status: approved", text)

    def test_set_with_explicit_type_noun_syntax(self):
        plan = self.create_plan(
            "20260822-testset-01-pl0021-test-plan.ipd.md", "pl0021", "testset", "draft"
        )
        rc = cli.main(
            [
                "set",
                "plans",
                "approved",
                "pl0021",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("- Status: approved", plan.read_text(encoding="utf-8"))

        spec = self.create_spec(
            "20260822-0021-01-test-spec.spec.md", "sp0021", "specset", "draft"
        )
        rc2 = cli.main(
            [
                "set",
                "specs",
                "to-review",
                "sp0021",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc2, 0)
        self.assertIn("- Status: to-review", spec.read_text(encoding="utf-8"))

    def test_spec_set_by_filename_and_id6(self):
        spec = self.create_spec(
            "20260822-0001-01-test-spec.spec.md", "sp0001", "specset", "draft"
        )
        rc = cli.main(
            [
                "spec",
                "set",
                "to-review",
                "20260822-0001-01-test-spec.spec.md",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        text = spec.read_text(encoding="utf-8")
        self.assertIn("- Status: to-review", text)

    def test_specs_set_dual_compatibility(self):
        spec = self.create_spec(
            "20260822-0002-01-test-spec.spec.md", "sp0002", "specset", "draft"
        )
        # Legacy syntax with --status and --message
        rc = cli.main(
            [
                "specs",
                "set",
                str(spec),
                "--status",
                "to-review",
                "--message",
                "legacy test message",
                "--yes",
            ]
        )
        self.assertEqual(rc, 0)
        text = spec.read_text(encoding="utf-8")
        self.assertIn("- Status: to-review", text)
        self.assertIn("legacy test message", text)

    def test_prompt_set(self):
        prompt = self.create_prompt(
            "20260822-testset-01-pr0001-test-prompt.prompt.md",
            "pr0001",
            "testset",
            "draft",
        )
        rc = cli.main(
            [
                "set",
                "prompts",
                "approved",
                "pr0001",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        text = prompt.read_text(encoding="utf-8")
        self.assertIn("- Status: approved", text)

    def test_backlog_set_and_directory_move(self):
        bk = self.create_backlog(
            "20260822-testset-01-bk0001-test-item.backlog.md",
            "bk0001",
            "testset",
            "open",
        )
        rc = cli.main(
            ["backlog", "set", "done", "bk0001", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 0)
        self.assertFalse(bk.exists())
        done_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "backlog"
            / "done"
            / "20260822-testset-01-bk0001-test-item.backlog.md"
        )
        self.assertTrue(done_path.exists())
        text = done_path.read_text(encoding="utf-8")
        self.assertIn("- Status: done", text)

    def test_set_multiple_mixed_types(self):
        plan = self.create_plan(
            "20260822-setmix-01-pl0005-test-plan.ipd.md",
            "pl0005",
            "setmix",
            "to-review",
        )
        spec = self.create_spec(
            "20260822-0003-01-test-spec.spec.md", "sp0003", "setmix", "to-review"
        )
        prompt = self.create_prompt(
            "20260822-setmix-01-pr0002-test-prompt.prompt.md",
            "pr0002",
            "setmix",
            "to-review",
        )

        # Set all 3 to reviewed in one command
        rc = cli.main(
            [
                "set",
                "reviewed",
                "pl0005",
                "sp0003",
                "pr0002",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)

        self.assertIn("- Status: reviewed", plan.read_text(encoding="utf-8"))
        self.assertIn("- Status: reviewed", spec.read_text(encoding="utf-8"))
        self.assertIn("- Status: reviewed", prompt.read_text(encoding="utf-8"))

    def test_set_by_setid_all_members_updated(self):
        plan1 = self.create_plan(
            "20260822-setgrp-01-pl0006-plan1.ipd.md", "pl0006", "setgrp", "draft"
        )
        plan2 = self.create_plan(
            "20260822-setgrp-02-pl0007-plan2.ipd.md", "pl0007", "setgrp", "draft"
        )

        rc = cli.main(
            ["set", "to-review", "setgrp", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 0)

        self.assertIn("- Status: to-review", plan1.read_text(encoding="utf-8"))
        self.assertIn("- Status: to-review", plan2.read_text(encoding="utf-8"))

    def test_type_mismatch_refuses_execution_before_changes(self):
        plan = self.create_plan(
            "20260822-testmismatch-01-pl0008-plan.ipd.md",
            "pl0008",
            "testmismatch",
            "draft",
        )
        spec = self.create_spec(
            "20260822-0004-01-test-spec.spec.md", "sp0004", "testmismatch", "draft"
        )

        # Targeting spec sp0004 with `aw ipd set` should fail with type mismatch
        rc = cli.main(
            ["ipd", "set", "approved", "sp0004", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertNotEqual(rc, 0)

        # Assert NO files changed
        self.assertIn("- Status: draft", plan.read_text(encoding="utf-8"))
        self.assertIn("- Status: draft", spec.read_text(encoding="utf-8"))

    def test_set_with_mixed_types_scoped_command_refuses(self):
        plan = self.create_plan(
            "20260822-mixedset-01-pl0009-plan.ipd.md", "pl0009", "mixedset", "draft"
        )
        spec = self.create_spec(
            "20260822-0005-01-test-spec.spec.md", "sp0005", "mixedset", "draft"
        )

        # Scoped command targeting a mixed set must refuse
        rc = cli.main(
            [
                "ipd",
                "set",
                "approved",
                "mixedset",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertNotEqual(rc, 0)

        self.assertIn("- Status: draft", plan.read_text(encoding="utf-8"))
        self.assertIn("- Status: draft", spec.read_text(encoding="utf-8"))

    def test_target_not_found_refuses_execution_before_changes(self):
        plan = self.create_plan(
            "20260822-notfound-01-pl0010-plan.ipd.md", "pl0010", "notfound", "draft"
        )

        # Second target does not exist; whole operation must refuse atomically
        rc = cli.main(
            [
                "set",
                "approved",
                "pl0010",
                "nonexistent999",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertNotEqual(rc, 0)

        # First plan MUST NOT be modified
        self.assertIn("- Status: draft", plan.read_text(encoding="utf-8"))

    def test_invalid_status_for_artifact_type_refuses(self):
        bk = self.create_backlog(
            "20260822-invstat-01-bk0002-item.backlog.md", "bk0002", "invstat", "open"
        )

        # Backlog does not support "approved" status
        rc = cli.main(
            ["set", "approved", "bk0002", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertNotEqual(rc, 0)

        self.assertIn("- Status: open", bk.read_text(encoding="utf-8"))

    def test_custom_message_and_by_human_attestation(self):
        plan = self.create_plan(
            "20260822-custommsg-01-pl0022-plan.ipd.md", "pl0022", "custommsg", "draft"
        )
        rc = cli.main(
            [
                "set",
                "approved",
                "pl0022",
                "--message",
                "explicit maintainer signoff",
                "--by-human",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        text = plan.read_text(encoding="utf-8")
        self.assertIn("- Status: approved", text)
        self.assertIn("explicit maintainer signoff", text)
        self.assertIn("--by-human", text)

    def test_dry_run_mode(self):
        plan = self.create_plan(
            "20260822-dryrun-01-pl0011-plan.ipd.md", "pl0011", "dryrun", "draft"
        )
        rc = cli.main(
            ["set", "approved", "pl0011", "--dry-run", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 0)
        # File unchanged
        self.assertIn("- Status: draft", plan.read_text(encoding="utf-8"))

    def test_json_output_mode(self):
        self.create_plan(
            "20260822-json-01-pl0012-plan.ipd.md", "pl0012", "jsonset", "draft"
        )
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                ["set", "approved", "pl0012", "--json", "--dir", str(self.repo_root)]
            )
        self.assertEqual(rc, 2)  # confirmation required in non-interactive/json mode
        rec = json.loads(buf.getvalue())
        self.assertEqual(rec["status"], "cannot-run")

        buf2 = io.StringIO()
        with patch("sys.stdout", buf2):
            rc2 = cli.main(
                [
                    "set",
                    "approved",
                    "pl0012",
                    "--yes",
                    "--json",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc2, 0)
        rec2 = json.loads(buf2.getvalue())
        self.assertEqual(rec2["status"], "clean")

    def test_agent_output_mode(self):
        self.create_plan(
            "20260822-agent-01-pl0013-plan.ipd.md", "pl0013", "agentset", "draft"
        )
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                ["set", "approved", "pl0013", "--agent", "--dir", str(self.repo_root)]
            )
        self.assertEqual(rc, 2)  # confirmation required in non-interactive/agent mode

        buf2 = io.StringIO()
        with patch("sys.stdout", buf2):
            rc2 = cli.main(
                [
                    "set",
                    "approved",
                    "pl0013",
                    "--yes",
                    "--agent",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc2, 0)
        rec2 = json.loads(buf2.getvalue().strip())
        self.assertEqual(rec2["schema"], "aw.agent/v1")
        self.assertEqual(rec2["outcome"], "clean")


if __name__ == "__main__":
    unittest.main()
