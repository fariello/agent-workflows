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

    def create_research(
        self, filename: str, id6: str, set_id: str, status: str = "active"
    ) -> Path:
        """A research doc, needed because setidfix `w2y5ac`'s measured corpus shape spans research.

        Research carries YAML front matter rather than the `- Key: value` bullet dialect the other
        types use (`selectors.py` documents the split; 0 of 103 research files carry a `- Id:`
        bullet), so this helper must not be modelled on `create_plan`.
        """
        p = (
            self.repo_root
            / ".aw"
            / "records"
            / "research"
            / "reference"
            / "202609"
            / filename
        )
        p.parent.mkdir(parents=True, exist_ok=True)
        content = f"""---
id: {id6}
status: {status}
set: {set_id}
---

# Research: Test report {id6}

## Summary
Test research report.
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

    def test_set_plan_executed_delegates_and_refuses_ungated(self):
        # ipdgates Order wezhxg: the raw ungated plan->executed move is REMOVED. `aw set executed
        # <plan>` now delegates into the gated `aw ipd finalize`; without an attributed --actor it
        # fails closed (exit 2) naming the exact command and does NOT move the plan (no bypass).
        plan = self.create_plan(
            "20260822-testset-01-pl0002-test-plan.ipd.md",
            "pl0002",
            "testset",
            "approved",
        )
        rc = cli.main(
            ["set", "executed", "pl0002", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 2)
        # The plan was NOT moved to executed/ via any ungated path.
        self.assertTrue(plan.exists())
        executed_path = (
            self.repo_root
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "20260822-testset-01-pl0002-test-plan.ipd.md"
        )
        self.assertFalse(executed_path.exists())
        # And no generic `executed (aw set)` history entry was written.
        self.assertNotIn("executed (aw set)", plan.read_text(encoding="utf-8"))

    def test_set_plan_status_from_executed_to_pending_moves_file_back(self):
        """REOPENING AN EXECUTED PLAN NOW REQUIRES THE NAMED OVERRIDE (setterguard `4bc1nd` E-02).

        THIS TEST ASSERTED THE DEFECT. As written it pinned `aw set to-review <an executed plan>`
        succeeding at exit 0 and the file moving back to `pending/`, which is precisely the ungated
        backwards transition that reverted seven real executed plans on 2026-09-10 and which
        `AGENTS.md` forbids ("Do NOT add commits to a plan already in executed/; close a
        post-execution gap with a new corrective IPD"). So the CONTRACT changed deliberately and the
        test was updated to the new one rather than the guard being weakened to keep it green.

        WHAT IS STILL PINNED, because it is the part that was always legitimate: the MECHANICS of a
        backwards move still work correctly (the file moves between disposition directories and the
        status bullet is rewritten) when the caller states the intent with `--allow-terminal-reopen`.
        The bare form is now refused, and both halves are asserted here so neither can regress.
        """
        plan = self.create_plan(
            "20260822-testset-01-pl0020-test-plan.ipd.md",
            "pl0020",
            "testset",
            "executed",
            disposition="executed",
        )
        before = plan.read_text(encoding="utf-8")

        # Without the override: refused, and nothing on disk changed or moved.
        rc_refused = cli.main(
            ["set", "to-review", "pl0020", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc_refused, 2)
        self.assertTrue(plan.exists())
        self.assertEqual(plan.read_text(encoding="utf-8"), before)

        # With the override: performed, exactly as this test originally asserted.
        rc = cli.main(
            [
                "set",
                "to-review",
                "pl0020",
                "--yes",
                "--allow-terminal-reopen",
                "--dir",
                str(self.repo_root),
            ]
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

    def _write_spec_review_record(
        self, subject_id6: str, slug: str = "test-spec"
    ) -> Path:
        """A conforming spec-review record, so a spec may legally reach `reviewed`.

        revsweep `5slbpi` made `to-review -> reviewed` an ATTESTED transition for specs: it now requires
        a parseable review record naming the spec as its `- Subject-Id:`. Written through
        `review_findings` (the single writer) rather than as literal markdown, so this fixture cannot
        drift from the format the setter's predicate parses.
        """
        from agent_workflows import review_findings as rf

        rnd = rf.Round(
            number=1,
            findings=(
                rf.Finding(
                    id="SR-001",
                    severity="low",
                    scope="in-scope",
                    area="B",
                    evidence="spec.md:1",
                    finding="a fixture finding",
                    remediation_risk="Overall:Low",
                    decision="fixed",
                    resolution="handled",
                ),
            ),
            decisions=(),
        )
        p = (
            self.repo_root
            / ".aw"
            / "records"
            / "reviews"
            / rf.build_review_name(
                date="20260822",
                set_id="setmix",
                order=1,
                subject_id6=subject_id6,
                slug=slug,
            )
        )
        rf.write_review(
            p,
            subject_id=subject_id6,
            subject_type="spec",
            reviewed_at="2026-08-22",
            reviewer="fixture",
            verdict="APPROVE",
            rounds=[rnd],
        )
        return p

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
        # revsweep `5slbpi`: the spec member's `->reviewed` transition is now ATTESTED, so the batch
        # needs the spec's review record to exist. The plan and prompt members are unaffected (a
        # missing review stays deliberately silent for a plan).
        self._write_spec_review_record("sp0003")

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

    def test_mixed_batch_refuses_ALL_when_the_spec_member_is_unattested(self):
        """revsweep `5slbpi`: the attestation composes with the ATOMIC pre-flight, so a batch
        containing one unattested spec sets NOTHING rather than partially applying.

        This is the companion of the test directly above and the reason it needed a record: the
        pre-flight loop validates every matched record before any write, so the spec's refusal must
        leave the plan and prompt untouched too.
        """
        plan = self.create_plan(
            "20260822-setmix-02-pl0008-test-plan.ipd.md",
            "pl0008",
            "setmix2",
            "to-review",
        )
        spec = self.create_spec(
            "20260822-0004-01-test-spec.spec.md", "sp0004", "setmix2", "to-review"
        )
        # NO review record for sp0004.
        rc = cli.main(
            [
                "set",
                "reviewed",
                "pl0008",
                "sp0004",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 1)
        self.assertIn("- Status: to-review", spec.read_text(encoding="utf-8"))
        self.assertIn("- Status: to-review", plan.read_text(encoding="utf-8"))

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

    def test_set_with_mixed_types_scoped_command_limits_to_scoped_type(self):
        plan = self.create_plan(
            "20260822-mixedset-01-pl0009-plan.ipd.md", "pl0009", "mixedset", "draft"
        )
        spec = self.create_spec(
            "20260822-0005-01-test-spec.spec.md", "sp0005", "mixedset", "draft"
        )

        # Scoped command targeting a mixed set must ONLY affect the scoped type (plans)
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
        self.assertEqual(rc, 0)

        self.assertIn("- Status: approved", plan.read_text(encoding="utf-8"))
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

    def test_spec_approved_interactive_confirmation(self):
        spec = self.create_spec(
            "20260822-0033-01-interactive-spec.spec.md",
            "sp0033",
            "specinter",
            "reviewed",
        )
        with patch("sys.stdin.isatty", return_value=True):
            rc = cli.main(
                [
                    "set",
                    "approved",
                    "sp0033",
                    "--message",
                    "interactive human signoff",
                    "--yes",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc, 0)
        text = spec.read_text(encoding="utf-8")
        self.assertIn("- Status: approved", text)
        self.assertIn("interactive human signoff", text)
        self.assertIn("--by-human", text)

    def test_spec_approved_non_interactive_refused(self):
        spec = self.create_spec(
            "20260822-0035-01-interactive-spec.spec.md",
            "sp0035",
            "specinter",
            "reviewed",
        )
        with patch("sys.stdin.isatty", return_value=False):
            rc = cli.main(
                [
                    "set",
                    "approved",
                    "sp0035",
                    "--yes",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc, 1)
        text = spec.read_text(encoding="utf-8")
        self.assertIn("- Status: reviewed", text)

    def test_other_artifact_status_transition(self):
        other_dir = self.repo_root / ".aw" / "records" / "notes"
        other_dir.mkdir(parents=True, exist_ok=True)
        note = other_dir / "20260822-notes-01-nt0005-meeting.md"
        note.write_text(
            "# Meeting Note\n\n- Id: nt0005\n- Status: open\n- Set: notes\n\nNotes content.\n",
            encoding="utf-8",
        )

        # Unscoped aw set
        rc = cli.main(["set", "done", "nt0005", "--yes", "--dir", str(self.repo_root)])
        self.assertEqual(rc, 0)
        self.assertIn("- Status: done", note.read_text(encoding="utf-8"))

        # Explicitly scoped aw set other
        rc2 = cli.main(
            ["set", "other", "active", "nt0005", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc2, 0)
        self.assertIn("- Status: active", note.read_text(encoding="utf-8"))

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


class TestApprovedWritesApprovalField(StatusSetTestBase):
    """w6mqc0: 'aw ipd set approved' must write the schema-required Approval field
    so an approved plan does not fail 'aw ipd lint' (IPD-M104)."""

    def test_set_approved_inserts_approval_field(self):
        plan = self.create_plan(
            "20260822-apxset-01-ap0001-test-plan.ipd.md", "ap0001", "apxset", "reviewed"
        )
        rc = cli.main(
            [
                "set",
                "approved",
                "ap0001",
                "--by-human",
                "-m",
                "approved. go.",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        text = plan.read_text(encoding="utf-8")
        self.assertIn("- Status: approved", text)
        # The required Approval field is present and non-empty (IPD-M104 satisfied).
        approval = [ln for ln in text.splitlines() if ln.startswith("- Approval:")]
        self.assertEqual(len(approval), 1, "exactly one Approval field expected")
        self.assertTrue(approval[0][len("- Approval:") :].strip(), "Approval non-empty")
        # It sits in the front matter (before the first H2), right after Id.
        head = text.split("\n## ", 1)[0].splitlines()
        self.assertIn("- Approval:", "\n".join(head))

    def test_approval_field_stripped_when_leaving_approved(self):
        plan = self.create_plan(
            "20260822-apxset-01-ap0002-test-plan.ipd.md", "ap0002", "apxset", "reviewed"
        )
        cli.main(
            [
                "set",
                "approved",
                "ap0002",
                "--by-human",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertIn("- Approval:", plan.read_text(encoding="utf-8"))
        rc = cli.main(
            ["set", "reviewed", "ap0002", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 0)
        self.assertNotIn("- Approval:", plan.read_text(encoding="utf-8"))

    def test_auto_approved_does_not_get_approval_field(self):
        plan = self.create_plan(
            "20260822-apxset-01-ap0003-test-plan.ipd.md", "ap0003", "apxset", "reviewed"
        )
        rc = cli.main(
            ["set", "auto-approved", "ap0003", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 0)
        text = plan.read_text(encoding="utf-8")
        self.assertIn("- Status: auto-approved", text)
        self.assertNotIn("- Approval:", text)

    def test_scaffolded_ipd_set_approved_lints_conforming(self):
        """End-to-end: a real scaffolded IPD set to approved must lint conforming
        (no IPD-M104), proving the setter no longer produces an unexecutable plan.

        `ipd scaffold`/`ipd lint` resolve the repo root from cwd, so run from the
        temp repo; `set` takes --dir explicitly.
        """
        import os

        plan = (
            self.repo_root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260822-apxlint-01-apxlnt-approval-lint-probe.ipd.md"
        )
        old_cwd = os.getcwd()
        os.chdir(self.repo_root)
        try:
            rc_scaffold = cli.main(
                [
                    "ipd",
                    "scaffold",
                    "--kind",
                    "child",
                    "--title",
                    "Approval lint probe",
                    "--set",
                    "apxlint",
                    "--order",
                    "1",
                    "--author",
                    "tester",
                    "--path",
                    str(plan),
                    "--apply",
                ]
            )
            self.assertEqual(rc_scaffold, 0)
            id6 = "apxlnt"
            cli.main(["set", "reviewed", id6, "--yes", "--dir", str(self.repo_root)])
            rc_appr = cli.main(
                [
                    "set",
                    "approved",
                    id6,
                    "--by-human",
                    "-m",
                    "approved. go.",
                    "--yes",
                    "--dir",
                    str(self.repo_root),
                ]
            )
            self.assertEqual(rc_appr, 0)
            self.assertIn("- Approval:", plan.read_text(encoding="utf-8"))
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                rc_lint = cli.main(["ipd", "lint", "--agent", str(plan)])
            out = buf.getvalue()
        finally:
            os.chdir(old_cwd)
        self.assertNotIn("IPD-M104", out)
        self.assertEqual(rc_lint, 0, out)


class BlocksReleaseSetterTests(StatusSetTestBase):
    """IPD efnn74: --blocks-release persists for plans AND backlog via the shared path (bug 61qk4a),
    and the specs surface is unchanged after the hoist out of the specs-only guard."""

    def test_backlog_positional_status_persists_blocks_release_61qk4a(self):
        # 61qk4a: `aw backlog set open <id6> --blocks-release next` (positional status form,
        # unchanged status) routes through status_set.apply_status_change; before the E-01 hoist the
        # value was silently dropped for backlog. It must now persist.
        bk = self.create_backlog(
            "20260822-demo-01-bk0002-x.backlog.md", "bk0002", "demo", "open"
        )
        rc = cli.main(
            [
                "backlog",
                "set",
                "open",
                "bk0002",
                "--blocks-release",
                "next",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("- Blocks-Release: next", bk.read_text(encoding="utf-8"))

    def test_plans_set_writes_and_clears_blocks_release(self):
        plan = self.create_plan(
            "20260822-demo-01-pl0007-x.ipd.md", "pl0007", "demo", "draft"
        )
        rc = cli.main(
            [
                "ipd",
                "set",
                "draft",
                "pl0007",
                "--blocks-release",
                "next",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("- Blocks-Release: next", plan.read_text(encoding="utf-8"))
        # A workflow-history line is appended by the setter.
        self.assertIn("## Workflow history", plan.read_text(encoding="utf-8"))
        # Clear with '-'.
        rc2 = cli.main(
            [
                "ipd",
                "set",
                "draft",
                "pl0007",
                "--blocks-release",
                "-",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc2, 0)
        self.assertNotIn("Blocks-Release", plan.read_text(encoding="utf-8"))

    def test_specs_blocks_release_unchanged_after_hoist(self):
        # Anti-regression: widening the write path to plans/backlog must not change the specs
        # surface it was originally scoped to.
        spec = self.create_spec(
            "20260822-demo-01-sp0007-x.spec.md", "sp0007", "specset", "draft"
        )
        rc = cli.main(
            [
                "spec",
                "set",
                "draft",
                "sp0007",
                "--blocks-release",
                "next",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("- Blocks-Release: next", spec.read_text(encoding="utf-8"))

    def test_ipd_set_with_shared_setid_across_types(self):
        # A setid shared across plans, backlog, and specs
        shared_set = "sharedset"
        plan1 = self.create_plan(
            "20260822-sharedset-01-pl0101-p1.ipd.md", "pl0101", shared_set, "draft"
        )
        plan2 = self.create_plan(
            "20260822-sharedset-02-pl0102-p2.ipd.md", "pl0102", shared_set, "draft"
        )
        spec = self.create_spec(
            "20260822-0101-01-test-spec.spec.md", "sp0101", shared_set, "draft"
        )
        backlog = self.create_backlog(
            "20260822-sharedset-01-bk0101-item.backlog.md", "bk0101", shared_set, "open"
        )

        # `aw ipd set approved sharedset` must transition ONLY the plans to approved
        rc = cli.main(
            [
                "ipd",
                "set",
                "approved",
                shared_set,
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)

        # Plans are approved
        self.assertIn("- Status: approved", plan1.read_text(encoding="utf-8"))
        self.assertIn("- Status: approved", plan2.read_text(encoding="utf-8"))

        # Spec and backlog are untouched
        self.assertIn("- Status: draft", spec.read_text(encoding="utf-8"))
        self.assertIn("- Status: open", backlog.read_text(encoding="utf-8"))

    def test_status_set_att_style_output_format(self):
        plan = self.create_plan(
            "20260822-fmtset-01-pl0201-p1.ipd.md", "pl0201", "fmtset", "reviewed"
        )
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                [
                    "ipd",
                    "set",
                    "approved",
                    "pl0201",
                    "--blocks-release",
                    "next",
                    "--yes",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        # Output should be formatted like `aw att`: `- >  plan        20260822-fmtset-01-pl0201  [blocking]  reviewed -> approved`
        self.assertIn("- >", out)
        self.assertIn("plan", out)
        self.assertIn("20260822-fmtset-01-pl0201", out)
        self.assertIn("[blocking]", out)
        self.assertIn("reviewed", out)
        self.assertIn("approved", out)
        self.assertIn("- Status: approved", plan.read_text(encoding="utf-8"))

    def test_status_set_unchanged_idempotent_no_rewrite(self):
        plan = self.create_plan(
            "20260822-fmtset-02-pl0202-p2.ipd.md", "pl0202", "fmtset", "approved"
        )
        # Add approval line so plan is fully conformant
        orig_text = plan.read_text(encoding="utf-8")
        if "- Approval:" not in orig_text:
            orig_text = orig_text.replace(
                "- Status: approved",
                "- Status: approved\n- Approval: 2026-08-27, recorded: ok",
            )
            plan.write_text(orig_text, encoding="utf-8")

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                [
                    "ipd",
                    "set",
                    "approved",
                    "pl0202",
                    "--yes",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        # Output should say `unchanged` instead of `approved -> approved`
        self.assertIn("unchanged", out)
        self.assertNotIn("approved -> approved", out)
        self.assertNotIn("approved → approved", out)

        # File content must not have any duplicate history lines appended
        after_text = plan.read_text(encoding="utf-8")
        self.assertEqual(orig_text, after_text)


class TestGateFieldClearingOnStatusChange(StatusSetTestBase):
    """Bug 43p53n: leaving the gate-carrying status MUST clear `Gate-Kind`/`Gate-Ref`.

    The gate-clearing branch used to be guarded by `rec.record_type == "specs"`, so
    `aw backlog set open <id6>` moved a blocked item out of `blocked` while leaving its gate fields
    behind. `aw backlog check` then reported `backlog.gate-unexpected`, and the only remedy was the
    untooled hand-edit the house rules forbid. `backlog.run_set` cleared correctly, but the
    positional `aw backlog set <status> <selector>` form routes through `status_set` instead, so
    that correct code was unreachable. This is the same class of bug as 61qk4a (the Blocks-Release
    write trapped inside the same specs-only guard).
    """

    def create_blocked_backlog(
        self,
        filename: str,
        id6: str,
        set_id: str,
        gate_kind: str = "artifact",
        gate_ref: str = "path/to/x.md",
    ) -> Path:
        d = self.repo_root / ".aw" / "records" / "backlog" / "blocked"
        d.mkdir(parents=True, exist_ok=True)
        p = d / filename
        # Mirrors the real `aw backlog new` output exactly (no H1; gate bullets after Summary), so
        # the parser sees a conformant record and `backlog check` findings are about the gate alone.
        p.write_text(
            f"""- Id: {id6}
- Status: blocked
- Set: {set_id}
- Priority: high
- Kind: bug
- Summary: Test blocked backlog item
- Gate-Kind: {gate_kind}
- Gate-Ref: {gate_ref}

## Workflow history
- 2026-08-22 created (aw backlog): created.
""",
            encoding="utf-8",
        )
        return p

    def _moved_path(self, id6: str, status: str) -> Path:
        matches = list(
            (self.repo_root / ".aw" / "records" / "backlog" / status).glob(
                f"*{id6}*.md"
            )
        )
        self.assertEqual(
            len(matches), 1, f"expected exactly one {id6} item in {status}/"
        )
        return matches[0]

    def test_backlog_leaving_blocked_clears_gate_fields(self):
        """The exact reported repro: blocked-with-gate -> open must strip both gate lines."""
        self.create_blocked_backlog(
            "20260828-gateclear-01-bk0001-probe.backlog.md", "bk0001", "gateclear"
        )
        rc = cli.main(
            [
                "backlog",
                "set",
                "open",
                "bk0001",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        text = self._moved_path("bk0001", "open").read_text(encoding="utf-8")
        self.assertIn("- Status: open", text)
        self.assertNotIn("Gate-Kind", text)
        self.assertNotIn("Gate-Ref", text)

    def test_backlog_leaving_blocked_leaves_check_clean(self):
        """The HARM the bug caused: the setter left a record its own checker rejects."""
        self.create_blocked_backlog(
            "20260828-gateclear-01-bk0002-probe.backlog.md", "bk0002", "gateclear"
        )
        rc = cli.main(
            [
                "backlog",
                "set",
                "parked",
                "bk0002",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            check_rc = cli.main(["backlog", "check", "--dir", str(self.repo_root)])
        out = buf.getvalue()
        self.assertNotIn("gate-unexpected", out)
        self.assertEqual(check_rc, 0, f"backlog check was not clean: {out}")

    def test_backlog_staying_blocked_retains_gate_fields(self):
        """ADVERSARIAL: over-eager clearing would strip a gate that is still valid."""
        self.create_blocked_backlog(
            "20260828-gateclear-01-bk0003-probe.backlog.md",
            "bk0003",
            "gateclear",
            gate_kind="decision",
            gate_ref="D42",
        )
        rc = cli.main(
            [
                "backlog",
                "set",
                "blocked",
                "bk0003",
                "--gate-kind",
                "decision",
                "--gate-ref",
                "D42",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        text = self._moved_path("bk0003", "blocked").read_text(encoding="utf-8")
        self.assertIn("- Gate-Kind: decision", text)
        self.assertIn("- Gate-Ref: D42", text)

    def test_spec_leaving_deferred_still_clears_gate(self):
        """The pre-existing specs behaviour must survive being generalized."""
        spec = self.create_spec(
            "20260822-sp0001-01-sp0001-test-spec.spec.md", "sp0001", "specset"
        )
        spec.write_text(
            spec.read_text(encoding="utf-8").replace(
                "- Status: draft",
                "- Status: deferred\n- Gate-Kind: decision\n- Gate-Ref: D7",
            ),
            encoding="utf-8",
        )
        rc = cli.main(
            ["spec", "set", "draft", "sp0001", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 0)
        text = spec.read_text(encoding="utf-8")
        self.assertIn("- Status: draft", text)
        self.assertNotIn("Gate-Kind", text)
        self.assertNotIn("Gate-Ref", text)

    def test_plan_transition_is_unaffected_by_gate_clearing(self):
        """Plans carry no gate fields; the generalized branch must not touch their metadata."""
        plan = self.create_plan(
            "20260822-gateclear-01-pl0301-test-plan.ipd.md",
            "pl0301",
            "gateclear",
            "draft",
        )
        before = plan.read_text(encoding="utf-8")
        rc = cli.main(
            ["set", "to-review", "pl0301", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 0)
        after = plan.read_text(encoding="utf-8")
        self.assertIn("- Status: to-review", after)

        # Every metadata bullet other than Status is byte-identical.
        def bullets(t):
            return [
                ln
                for ln in t.splitlines()
                if ln.startswith("- ")
                and not ln.startswith("- Status:")
                and not ln.startswith("- 2026")
            ]

        self.assertEqual(bullets(before), bullets(after))


class ApprovalGateTests(StatusSetTestBase):
    """apprvguard Order 01 (d7bnhc) E-09 / V-05, V-06, V-09: the gate on the approval path itself.

    A bug here fails in one of two directions and BOTH are covered, because neither may be waived:
    too fail-closed blocks every legitimate approval (the non-regression cases below, plus the
    pre-existing `test_custom_message_and_by_human_attestation`), and too fail-open silently permits
    the exact 2026-08-30 accident this gate exists to prevent (the refusal cases).
    """

    REJECT_RECORD = (
        "- 2026-08-30 /plan-review pass 2 (opencode/test): REJECT - NEEDS REPLAN "
        "reaffirmed; the approach is unsound."
    )
    APPROVE_RECORD = "- 2026-08-30 /plan-review (opencode/test): APPROVE WITH REVISIONS APPLIED; PR-001."
    BLOCKING_OQ = (
        "\n## Open questions\n\n"
        "### OQ-03: A genuinely undecided blocking question\n\n"
        "- Blocking: yes\n"
        "- Status: open\n"
        "- Owner: maintainer\n"
        "- Resolution or deferral rationale: pending\n"
    )

    def create_reviewed_plan(
        self, id6: str, set_id: str, record: str, extra: str = ""
    ) -> Path:
        """A plan in `reviewed` whose history carries a real review record (newest-FIRST)."""
        plan = self.create_plan(
            f"20260830-{set_id}-01-{id6}-gate-probe.ipd.md", id6, set_id, "reviewed"
        )
        text = plan.read_text(encoding="utf-8").replace(
            "## Workflow history\n",
            "## Workflow history\n" + record + "\n",
        )
        plan.write_text(text + extra, encoding="utf-8")
        return plan

    def test_rejected_plan_refuses_and_leaves_the_file_unchanged(self):
        plan = self.create_reviewed_plan("rj0001", "gatea", self.REJECT_RECORD)
        before = plan.read_text(encoding="utf-8")
        rc = cli.main(
            ["set", "approved", "rj0001", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 1)
        # UNCHANGED on disk: not merely still `reviewed`, but byte-identical, so no history record
        # and no `- Approval:` line were written either.
        self.assertEqual(plan.read_text(encoding="utf-8"), before)
        self.assertNotIn("- Approval:", before)

    def test_refusal_is_not_defeated_by_by_human(self):
        """A human attesting approval cannot overrule the review's own verdict."""
        plan = self.create_reviewed_plan("rj0002", "gateb", self.REJECT_RECORD)
        before = plan.read_text(encoding="utf-8")
        rc = cli.main(
            [
                "set",
                "approved",
                "rj0002",
                "--by-human",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 1)
        self.assertEqual(plan.read_text(encoding="utf-8"), before)

    def test_refusal_is_not_defeated_by_allow_open_questions(self):
        """THE override asymmetry: the flag clears QUESTIONS, never a verdict."""
        plan = self.create_reviewed_plan("rj0003", "gatec", self.REJECT_RECORD)
        before = plan.read_text(encoding="utf-8")
        rc = cli.main(
            [
                "set",
                "approved",
                "rj0003",
                "--allow-open-questions",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 1)
        self.assertEqual(plan.read_text(encoding="utf-8"), before)

    def test_auto_approved_is_gated_too(self):
        """`ipd_schema.READY_TO_EXECUTE` holds BOTH tokens, so gating only `approved` leaves the
        automated tier ungated AT THE SETTER (d7bnhc D3)."""
        plan = self.create_reviewed_plan("rj0004", "gated", self.REJECT_RECORD)
        before = plan.read_text(encoding="utf-8")
        rc = cli.main(
            ["set", "auto-approved", "rj0004", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 1)
        self.assertEqual(plan.read_text(encoding="utf-8"), before)

    def test_batch_with_one_rejected_plan_approves_none(self):
        """The pre-flight loop makes a blanket multi-plan approval refuse WITHOUT partially applying.

        This is the shape of the actual 2026-08-30 incident: one instruction, many plans.
        """
        clean_a = self.create_reviewed_plan("bt0001", "batch", self.APPROVE_RECORD)
        clean_b = self.create_reviewed_plan("bt0002", "batch", self.APPROVE_RECORD)
        rejected = self.create_reviewed_plan("bt0003", "batch", self.REJECT_RECORD)
        befores = {
            p: p.read_text(encoding="utf-8") for p in (clean_a, clean_b, rejected)
        }
        rc = cli.main(
            [
                "set",
                "approved",
                "bt0001",
                "bt0002",
                "bt0003",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 1)
        for path, before in befores.items():
            self.assertEqual(path.read_text(encoding="utf-8"), before, path.name)

    def test_blocking_open_question_refuses_then_the_override_permits_and_is_recorded(
        self,
    ):
        plan = self.create_reviewed_plan(
            "oq0001", "gateoq", self.APPROVE_RECORD, extra=self.BLOCKING_OQ
        )
        before = plan.read_text(encoding="utf-8")

        rc_bare = cli.main(
            ["set", "approved", "oq0001", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc_bare, 1)
        self.assertEqual(plan.read_text(encoding="utf-8"), before)

        # --by-human MUST NOT imply the override (the backlog item is explicit about this).
        rc_human = cli.main(
            [
                "set",
                "approved",
                "oq0001",
                "--by-human",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc_human, 1)
        self.assertEqual(plan.read_text(encoding="utf-8"), before)

        rc_override = cli.main(
            [
                "set",
                "approved",
                "oq0001",
                "--allow-open-questions",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc_override, 0)
        text = plan.read_text(encoding="utf-8")
        self.assertIn("- Status: approved", text)
        # The override is auditable in the ARTIFACT, not only in a shell history.
        self.assertIn("--allow-open-questions", text)

    def test_the_override_is_not_recorded_when_it_had_no_effect(self):
        """A flag that changed nothing must not leave a false claim in history."""
        plan = self.create_reviewed_plan("oq0002", "gatenoop", self.APPROVE_RECORD)
        rc = cli.main(
            [
                "set",
                "to-review",
                "oq0002",
                "--allow-open-questions",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertNotIn("--allow-open-questions", plan.read_text(encoding="utf-8"))

    def test_reviewed_plan_with_an_approving_verdict_still_approves(self):
        """NON-REGRESSION: the gate must not have broken the legitimate approve path."""
        plan = self.create_reviewed_plan("ok0001", "gateok", self.APPROVE_RECORD)
        rc = cli.main(
            [
                "set",
                "approved",
                "ok0001",
                "--by-human",
                "--message",
                "maintainer signoff",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        text = plan.read_text(encoding="utf-8")
        self.assertIn("- Status: approved", text)
        self.assertIn("- Approval:", text)

    def test_plan_with_no_review_at_all_still_approves(self):
        """Absent review is SILENT by design: gating on absence would block author-then-approve."""
        plan = self.create_plan(
            "20260830-gatenorev-01-nr0001-plan.ipd.md", "nr0001", "gatenorev", "draft"
        )
        rc = cli.main(
            ["set", "approved", "nr0001", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 0)
        self.assertIn("- Status: approved", plan.read_text(encoding="utf-8"))

    def test_successor_narrating_a_predecessors_reject_still_approves(self):
        """The measured false-refusal case (F-5): the newest record is `to-review` QUOTING a REJECT."""
        plan = self.create_reviewed_plan(
            "sc0001",
            "gatesucc",
            "- 2026-08-30 to-review (opencode/test): SUPERSEDES `kaygwo`, which was "
            "REJECT - NEEDS REPLAN twice.\n" + self.APPROVE_RECORD,
        )
        rc = cli.main(
            ["set", "approved", "sc0001", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 0)
        self.assertIn("- Status: approved", plan.read_text(encoding="utf-8"))

    def test_spec_blocking_open_question_refuses_on_the_positional_spelling(self):
        """E-07: the POSITIONAL spec spelling routes HERE, so it must be gated here too or the
        spelling itself is the bypass. Caught as a real bypass during validation."""
        spec = self.create_spec(
            "20260830-0001-01-sq0001-gate-probe.spec.md",
            "sq0001",
            "gatespec",
            "reviewed",
        )
        spec.write_text(
            spec.read_text(encoding="utf-8") + self.BLOCKING_OQ, encoding="utf-8"
        )
        before = spec.read_text(encoding="utf-8")
        rc = cli.main(
            [
                "specs",
                "set",
                "approved",
                "sq0001",
                "--by-human",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 1)
        self.assertEqual(spec.read_text(encoding="utf-8"), before)

        rc_override = cli.main(
            [
                "specs",
                "set",
                "approved",
                "sq0001",
                "--by-human",
                "--allow-open-questions",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc_override, 0)
        text = spec.read_text(encoding="utf-8")
        self.assertIn("- Status: approved", text)
        self.assertIn("--allow-open-questions", text)

    def test_refusal_message_names_its_cause(self):
        """A refusal that does not say WHY sends the operator hunting; assert the cause is quoted."""
        self.create_reviewed_plan("rj0005", "gatemsg", self.REJECT_RECORD)
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                ["set", "approved", "rj0005", "--yes", "--dir", str(self.repo_root)]
            )
        self.assertEqual(rc, 1)
        out = buf.getvalue()
        self.assertIn("REJECT - NEEDS REPLAN", out)
        self.assertIn("NO override", out)

    def test_agent_mode_emits_the_invalid_transition_rule(self):
        self.create_reviewed_plan("rj0006", "gatejson", self.REJECT_RECORD)
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                [
                    "set",
                    "approved",
                    "rj0006",
                    "--yes",
                    "--agent",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc, 1)
        payload = "\n".join(
            line for line in buf.getvalue().splitlines() if line.strip()
        )
        self.assertIn("status.invalid_transition", payload)


class SharedLifecycleRenderingTests(StatusSetTestBase):
    """Spec `uonrjg` R10.3, Sections 9.1 / 9.4, criteria A10, A11 and A20 (plan `9zvl2w` E-02/E-05).

    WHAT THIS PINS THAT NOTHING PINNED BEFORE: measured at authoring, this file contained ZERO
    `38;5;` assertions, so the setter's echo line could have been restyled arbitrarily without a
    single test noticing. The four properties below are the ones the conversion can plausibly break.

    THE `unchanged` CASE IS THE TRAP, and it is the same class of mistake as the index modules'. The
    setter's THIRD `status_256` call renders the literal word `unchanged`, which is a no-op OUTCOME
    and not a lifecycle status: it appears in no spec Section 6 or 7 table and is not a value any
    `- Status:` line can hold. Converting BY CALL SITE rather than BY VALUE would send it to criterion
    A20's unknown path and print `?` for a SUCCESSFUL no-op.
    """

    def _echo(self, argv, *, force_color=True, confirm=True):
        import os
        from unittest.mock import patch as _patch

        buf = io.StringIO()
        env = {"FORCE_COLOR": "1"} if force_color else {}
        tail = (["--yes"] if confirm else []) + ["--dir", str(self.repo_root)]
        with _patch.dict(os.environ, env, clear=False):
            if not force_color:
                os.environ.pop("FORCE_COLOR", None)
            with _patch("sys.stdout", buf):
                rc = cli.main(argv + tail)
        return rc, buf.getvalue()

    def test_a_transition_renders_glyph_and_status_in_one_shared_color(self):
        self.create_plan("20260822-setalpha-01-aaa111-x.ipd.md", "aaa111", "setalpha")
        _rc, out = self._echo(["set", "to-review", "aaa111"])
        # `to-review` is spec Section 6.1 `review-queued`: glyph `◔`, index 39, NOT bold.
        self.assertIn(
            "\033[38;5;39m\u25d4\033[0m", out, f"glyph missing/miscolored: {out!r}"
        )
        self.assertIn(
            "\033[38;5;39mto-review\033[0m", out, f"status miscolored: {out!r}"
        )

    def test_the_setter_and_aw_find_render_one_identical_escape_for_one_status(self):
        """Criterion A17's whole point: two views, one vocabulary. Compared as RAW BYTES.

        USES A SPEC AND `implemented` RATHER THAN A PLAN AND `executed`, deliberately: a plan's
        `executed` transition delegates into the gated `aw ipd finalize` and refuses without an
        attributed `--actor`, so it never reaches the echo line this test is about. `implemented` is
        the SAME shared stage (`done`, index 46), so the cross-view identity claim is unweakened.
        """
        self.create_spec(
            "20260822-setbeta-01-bbb222-x.spec.md",
            "bbb222",
            "setbeta",
            status="implementing",
        )
        _rc, set_out = self._echo(["set", "implemented", "bbb222"])
        _rc2, find_out = self._echo(["find", "specs", "bbb222"], confirm=False)
        needle = "\033[1;38;5;46mimplemented\033[0m"
        self.assertIn(needle, set_out, f"aw set did not render {needle!r}: {set_out!r}")
        self.assertIn(
            needle,
            find_out,
            "aw set and aw find disagree about one status's rendered bytes, which is exactly the "
            f"drift criterion A17 forbids: {find_out!r}",
        )

    def test_the_no_op_word_unchanged_keeps_its_generic_color_and_is_not_a_question_mark(
        self,
    ):
        self.create_plan(
            "20260822-setgamma-01-ccc333-x.ipd.md",
            "ccc333",
            "setgamma",
            status="approved",
        )
        _rc, out = self._echo(["set", "approved", "ccc333"])
        self.assertIn(
            "\033[1;38;5;245munchanged\033[0m",
            out,
            "`unchanged` lost its generic gray. It is a no-op OUTCOME word, not a lifecycle status "
            "(spec `uonrjg` R10.3 keeps generic outcomes out of scope), so it must stay on "
            f"`Term.status_256` and must NOT be resolved: {out!r}",
        )
        self.assertNotIn(
            "?",
            out,
            "`unchanged` was routed through the lifecycle resolver and rendered criterion A20's "
            "unknown glyph for a SUCCESSFUL no-op. Convert by VALUE, not by call site.",
        )

    def test_the_artifact_type_word_carries_no_escape(self):
        """Criterion A10: only glyph, id6 and status are colored; the type is not."""
        self.create_plan("20260822-setdelta-01-ddd444-x.ipd.md", "ddd444", "setdelta")
        _rc, out = self._echo(["set", "to-review", "ddd444"])
        self.assertIn("plan", out)
        for escape in ("\033[1;38;5;33mplan", "\033[38;5;33mplan"):
            self.assertNotIn(
                escape,
                out,
                "the artifact TYPE word is lifecycle/tree-colored, which criterion A10 forbids "
                "('Titles and paths are not lifecycle-colored') and Section 11 item 5 limits to "
                "glyph, id6 and status. The `_TREE_COLOR_256` exemption covers a path SEGMENT, not "
                f"a bare type word: {out!r}",
            )

    def test_color_off_keeps_the_glyph_and_the_word_with_no_ansi(self):
        """Criterion A11: no escapes, but the state survives via glyph plus word."""
        self.create_plan("20260822-seteps-01-eee555-x.ipd.md", "eee555", "seteps")
        _rc, out = self._echo(["set", "to-review", "eee555"], force_color=False)
        self.assertNotIn("\033", out, f"ANSI leaked with color off: {out!r}")
        self.assertIn("\u25d4", out, f"the glyph vanished with color off: {out!r}")
        self.assertIn("to-review", out, f"the native word vanished: {out!r}")


class SharedSetidCrossTypeResolutionTests(StatusSetTestBase):
    """setidfix `w2y5ac` (spec `2lcqno` N1/N3/N4): a setid is a SHARED cross-type TOPIC label.

    THE CORPUS SHAPE IS THE MEASURED ONE, NOT A SIMPLIFIED ONE, because the simplified two-type
    version is what let a wrong diagnosis survive review: the fixture below carries one setid on
    plans AND a backlog item AND a research doc, mirroring the real `agentadhere` topic (7 plans +
    1 backlog + 5 research files).

    THE RESEARCH MEMBER IS PRESENT IN THE CORPUS AND DELIBERATELY ABSENT FROM THE RESOLUTION, and
    that is a MEASURED property of HEAD rather than a shortcut in this fixture. Research docs carry
    YAML front matter (`id:`/`status:`/`set:`), while `status_set.read_artifact_record` reads the
    BULLET dialect (`- Set:`), so a research doc's `set_id` parses as None and the setid rules never
    fire for it; a research file matches such a token only by the last-resort FILENAME substring
    rule, which the setid fast path takes precedence over. Measured at HEAD on the real tree:
    `match_selector('agentadhere')` returns 8 records across `['backlog', 'plans']`, while the five
    `agentadhere` research files resolve only as `kind='substring'`. That dialect gap is a separate
    defect owned by approved plan `xo3244` (Set `selfmdialect`); this fixture keeps the research
    member so the shape is the real one and asserts the CURRENT resolution honestly, and it will
    surface (not silently absorb) the change when `xo3244` lands.

    FOUR PROPERTIES ARE PINNED HERE, and nothing pinned any of them before:
      1. scoped SETID resolution narrows to the requested type;
      2. a scoped verb handed a FOREIGN-TYPE PATH refuses (the one case scoped resolution does NOT
         filter, and the only guard on a cross-type write);
      3. the UNTYPED verb reports candidates BY TYPE and writes nothing when one token spans types;
      4. a status VALID FOR SEVERAL matched types gets the same deliberate refusal rather than a
         silent multi-type write.
    """

    SETID = "shartop"

    def _build_shared_topic(self):
        """One setid across plans + backlog + research (the measured `agentadhere` shape)."""
        plan1 = self.create_plan(
            "20260921-shartop-01-sh0001-topic-plan-one.ipd.md",
            "sh0001",
            self.SETID,
            "reviewed",
        )
        plan2 = self.create_plan(
            "20260921-shartop-02-sh0002-topic-plan-two.ipd.md",
            "sh0002",
            self.SETID,
            "reviewed",
        )
        item = self.create_backlog(
            "20260921-shartop-01-sh0003-topic-item.backlog.md",
            "sh0003",
            self.SETID,
            "open",
        )
        report = self.create_research(
            "20260921-shartop-01-sh0004-topic-report.research-report.md",
            "sh0004",
            self.SETID,
            "active",
        )
        return plan1, plan2, item, report

    def _research_in_corpus(self):
        """The research members the inventory sees, regardless of whether a setid resolves to them."""
        from agent_workflows import status_set

        return [
            r
            for r in status_set.inventory_all_artifacts(
                self.repo_root, scoped_type="research"
            )
            if r.record_type == "research"
        ]

    # ---------------------------------------------------------------------------------- E-01

    def test_scoped_setid_resolution_returns_only_the_scoped_type(self):
        """E-01: scoped SETID resolution narrows to the requested type.

        SCOPE OF THIS PIN, STATED PRECISELY BECAUSE OVER-READING IT CAUSED REAL HARM: this asserts
        the SETID selector kind only. It does NOT prove scoped resolution is type-safe in general.
        The DIRECT-PATH kind is deliberately EXEMPT from the type narrowing (`selectors.resolve`'s
        first precedence rule matches an existing file regardless of the type requested, and the
        record's type is then read off the real path), and that exemption is pinned separately by
        `test_scoped_verb_refuses_a_foreign_type_path_and_writes_nothing`. Reading this test as
        "scoped resolution filters by type" is the over-generalization that produced an instruction
        to delete the `Type mismatch` refusal as dead code; it is not dead.

        Without this test, a change to `match_selector`'s `record_types` narrowing would silently
        reintroduce the original cross-type failure with nothing failing.
        """
        from agent_workflows import status_set

        self._build_shared_topic()
        root = self.repo_root

        unscoped = status_set.match_selector(
            self.SETID,
            status_set.inventory_all_artifacts(root, scoped_type=None),
            root,
            scoped_type=None,
        )
        self.assertEqual(
            sorted({r.record_type for r in unscoped}),
            ["backlog", "plans"],
            "the fixture no longer spans the types the measured `agentadhere` case resolves to. At "
            "HEAD a setid resolves across plans and backlog but NOT research (the YAML-versus-bullet "
            "front-matter dialect gap owned by plan `xo3244`), so this is the honest shape. If "
            "research now appears here, `xo3244` has landed: that is CORRECT, and the fix is to add "
            f"'research' to this expectation: {[(r.record_type, r.id6) for r in unscoped]}",
        )
        self.assertTrue(
            any(r.record_type == "research" for r in self._research_in_corpus()),
            "the research member vanished from the CORPUS, so the fixture no longer mirrors the "
            "measured three-type topic shape even though resolution reaches only two types",
        )

        # PASS THE FULL, UNNARROWED INVENTORY ON PURPOSE. Handing in
        # `inventory_all_artifacts(scoped_type="plans")` would pre-filter the candidates and the
        # assertion below would hold even with `match_selector`'s OWN narrowing removed, i.e. the pin
        # would pass vacuously (verified: with the narrowing mutated out, the pre-filtered form still
        # passed). `scoped_type` must be the ONLY thing doing the filtering here.
        scoped = status_set.match_selector(
            self.SETID,
            status_set.inventory_all_artifacts(root, scoped_type=None),
            root,
            scoped_type="plans",
        )
        self.assertEqual(
            sorted({r.record_type for r in scoped}),
            ["plans"],
            "scoped SETID resolution stopped filtering by type, which is the exact defect spec "
            f"`2lcqno` N3 requires to stay fixed: {[(r.record_type, r.id6) for r in scoped]}",
        )
        self.assertEqual(
            sorted(r.id6 or "" for r in scoped),
            ["sh0001", "sh0002"],
            "scoped resolution must return the whole within-type Set (IPD `laykok` E-07), so both "
            "plans and only the plans",
        )

    # ---------------------------------------------------------------------------------- E-02

    def test_scoped_verb_refuses_a_foreign_type_path_and_writes_nothing(self):
        """E-02: the `Type mismatch` refusal is LIVE, and this is the test that pins it.

        WHY IT IS REACHABLE at all, given that `match_selector` pre-filters by `scoped_type`: the
        pre-filter narrows which types the RESOLVER is QUERIED for, while the direct-PATH selector
        kind matches an existing file regardless. So `aw specs set <status> <a plan path>` resolves a
        `plans` record under a `specs`-scoped verb, and this refusal is the ONLY thing between it and
        a cross-type write.

        WHAT DELETING THE BRANCH WAS MEASURED TO PERMIT: the same command SUCCEEDING, writing the
        PLAN to `approved` AND appending a forged `- ... approved (aw set, --by-human): ...` line to
        that plan's own history, i.e. a machine-authored human-approval attestation. The whole suite
        was green with the branch removed, which is why this pin exists.
        """
        plan = self.create_plan(
            "20260921-fpath-01-fp0001-foreign-path-plan.ipd.md",
            "fp0001",
            "fpath",
            "reviewed",
        )
        before = plan.read_text(encoding="utf-8")

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                [
                    "specs",
                    "set",
                    "approved",
                    str(plan),
                    "--yes",
                    "--by-human",
                    "--message",
                    "cross-type write attempt",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(
            rc,
            2,
            "a type-scoped verb handed a FOREIGN-TYPE path must refuse at exit 2. If this now "
            "exits 0, the `Type mismatch` guard in `run_set_command` was removed and a cross-type "
            f"write is possible: {buf.getvalue()!r}",
        )
        self.assertIn("Type mismatch", buf.getvalue())
        self.assertEqual(
            plan.read_text(encoding="utf-8"),
            before,
            "the plan was MODIFIED by a `specs`-scoped verb. That is the cross-type write plus "
            "forged `--by-human` attestation this guard exists to prevent.",
        )
        self.assertNotIn("--by-human", plan.read_text(encoding="utf-8"))

    # ---------------------------------------------------------------------------------- E-03

    def test_untyped_setter_reports_candidates_by_type_instead_of_a_foreign_vocabulary(
        self,
    ):
        """E-03: the untyped verb reports per-type candidates rather than dying on a foreign type.

        BEFORE (measured): `aw set approved <shared setid>` reached the per-record
        `validate_transition_allowed` loop and failed on whichever artifact's vocabulary rejected the
        status, printing `Status 'approved' is not valid for backlog (valid: [...])` when the
        operator plainly meant the plan Set. Spec `2lcqno` N4 requires reporting the candidates BY
        TYPE with a way to disambiguate, and forbids guessing.

        The recommended command must be the SHIPPED leading-type-token spelling, not a new flag.
        """
        plan1, plan2, item, report = self._build_shared_topic()
        snapshot = {
            p: p.read_text(encoding="utf-8") for p in (plan1, plan2, item, report)
        }

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                [
                    "set",
                    "approved",
                    self.SETID,
                    "--yes",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        out = buf.getvalue()
        self.assertEqual(rc, 2, f"the untyped multi-type case must refuse: {out!r}")
        self.assertNotIn(
            "is not valid for backlog",
            out,
            "the untyped setter still reports a FOREIGN type's status vocabulary, which is the "
            f"measured defect: {out!r}",
        )
        # Only the types the setid actually RESOLVES to are reported; research is in the corpus but
        # not in the resolution at HEAD (the `xo3244` dialect gap documented on this class).
        for rtype in ("backlog", "plans"):
            self.assertIn(
                f"aw set {rtype} approved {self.SETID}",
                out,
                f"the report must print a runnable disambiguating command for {rtype}: {out!r}",
            )
        self.assertIn("2 artifact(s)", out, f"per-type counts are missing: {out!r}")
        for p, text in snapshot.items():
            self.assertEqual(
                p.read_text(encoding="utf-8"),
                text,
                f"a refusal wrote to {p.name}; the refusal must precede every change",
            )

    def test_the_printed_disambiguating_command_resolves_within_one_type(self):
        """E-03: the command the refusal prints must actually work (and needs no new flag)."""
        plan1, plan2, item, report = self._build_shared_topic()
        rc = cli.main(
            [
                "set",
                "plans",
                "approved",
                self.SETID,
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("- Status: approved", plan1.read_text(encoding="utf-8"))
        self.assertIn("- Status: approved", plan2.read_text(encoding="utf-8"))
        self.assertIn("- Status: open", item.read_text(encoding="utf-8"))
        self.assertIn("status: active", report.read_text(encoding="utf-8"))

    # ---------------------------------------------------------------------------------- E-04

    def test_a_status_valid_for_two_matched_types_refuses_instead_of_writing_both(self):
        """E-04: the multi-type-VALID case, which is the WIDER hole and was silent before.

        MEASURED BEFORE: 15 statuses in `TYPE_STATUSES` are valid for two or more types, and
        `aw set to-review <a setid shared by a plan and a spec> --yes` transitioned BOTH at exit 0,
        printing `plan ... draft -> to-review` and `spec ... draft -> to-review`. There is no
        vocabulary error to stop on in this case, so it was an unannounced cross-type write, which
        N4 forbids ("MUST NOT guess").

        The chosen outcome is REFUSE-AND-REQUIRE-A-TYPE, sharing E-03's one code path. Confirmation
        was the rejected alternative: plan `4bc1nd` (Set `setterguard`, carrying backlog `f5pttg`)
        owns confirmation-before-write for every setter, and implementing it here too would be a
        second implementation of that fix.
        """
        plan = self.create_plan(
            "20260921-bothok-01-bo0001-both-plan.ipd.md", "bo0001", "bothok", "draft"
        )
        spec = self.create_spec(
            "20260921-bothok-01-bo0002-both-spec.spec.md", "bo0002", "bothok", "draft"
        )

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                ["set", "to-review", "bothok", "--yes", "--dir", str(self.repo_root)]
            )
        out = buf.getvalue()
        self.assertEqual(
            rc,
            2,
            "a status valid for BOTH matched types silently wrote both, which is the wider hole "
            f"E-04 exists to close: {out!r}",
        )
        self.assertIn("aw set plans to-review bothok", out)
        self.assertIn("aw set specs to-review bothok", out)
        self.assertIn("- Status: draft", plan.read_text(encoding="utf-8"))
        self.assertIn("- Status: draft", spec.read_text(encoding="utf-8"))

    def test_within_type_setid_fanout_still_acts_on_the_whole_set(self):
        """E-04 boundary: only CROSS-type fan-out is refused; within-type fan-out is deliberate.

        IPD `laykok` E-07 made a bare setid transition a whole Set with no `--force`. Conflating that
        with the cross-type case would break every bulk Set transition, so it is pinned here.
        """
        plan1 = self.create_plan(
            "20260921-onlyplans-01-op0001-a.ipd.md", "op0001", "onlyplans", "draft"
        )
        plan2 = self.create_plan(
            "20260921-onlyplans-02-op0002-b.ipd.md", "op0002", "onlyplans", "draft"
        )
        rc = cli.main(
            ["set", "to-review", "onlyplans", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 0)
        self.assertIn("- Status: to-review", plan1.read_text(encoding="utf-8"))
        self.assertIn("- Status: to-review", plan2.read_text(encoding="utf-8"))


class FlaglessConfirmationRefusalTests(StatusSetTestBase):
    """setterguard `4bc1nd` E-04: the confirmation refusal reaches EVERY caller, not only a flagged one.

    THE FLAGGED CASES ARE ALREADY COVERED ELSEWHERE and are deliberately NOT duplicated here:
    `TestStatusSetCommands.test_json_output_mode` and `test_agent_output_mode` in this module assert
    the `--json` and `--agent` refusals, and `tests/test_cli_mutations_and_previews.py` covers the
    preview surface. What had NO coverage, and what let the measured incident happen, is the FLAGLESS
    call (neither `--agent` nor `--json`), which wrote immediately at exit 0.

    Built from the MEASURED 2026-09-10 incident: one flagless `aw ipd set approved <setid>` reverted
    seven plans out of `.aw/records/plans/executed/`. The fixture is the minimal isolated form of it
    (two plans sharing one setid) so it does not depend on this repository's corpus.
    """

    def _two_plan_set(self) -> tuple[Path, Path]:
        a = self.create_plan(
            "20260910-guardset-01-gd0001-a.ipd.md", "gd0001", "guardset", "to-review"
        )
        b = self.create_plan(
            "20260910-guardset-02-gd0002-b.ipd.md", "gd0002", "guardset", "to-review"
        )
        return a, b

    def test_a_flagless_call_refuses_and_writes_nothing(self):
        """Exit 2, and NOTHING on disk moved or changed.

        ASSERTS THE FILESYSTEM, not only the exit code: the original incident MOVED FILES between
        disposition directories, so a test checking only the status bullet would miss half the damage.
        """
        a, b = self._two_plan_set()
        before_a, before_b = (
            a.read_text(encoding="utf-8"),
            b.read_text(encoding="utf-8"),
        )

        rc = cli.main(
            ["ipd", "set", "approved", "guardset", "--dir", str(self.repo_root)]
        )

        self.assertEqual(rc, 2, "a flagless mutating set must REFUSE, not write")
        # The status bullet is untouched...
        self.assertEqual(a.read_text(encoding="utf-8"), before_a)
        self.assertEqual(b.read_text(encoding="utf-8"), before_b)
        # ...AND each file is still in its original disposition directory.
        self.assertTrue(a.is_file())
        self.assertTrue(b.is_file())
        self.assertEqual(a.parent.name, "pending")
        self.assertEqual(b.parent.name, "pending")

    def test_the_same_call_with_yes_performs_the_transition(self):
        """`--yes` behaves exactly as before: the speed bump is a bump, not a wall."""
        a, b = self._two_plan_set()
        rc = cli.main(
            [
                "ipd",
                "set",
                "approved",
                "guardset",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("- Status: approved", a.read_text(encoding="utf-8"))
        self.assertIn("- Status: approved", b.read_text(encoding="utf-8"))

    def test_dry_run_still_previews_without_writing(self):
        """`--dry-run` semantics are UNCHANGED by E-01: it still previews at exit 0."""
        a, b = self._two_plan_set()
        before_a = a.read_text(encoding="utf-8")
        rc = cli.main(
            [
                "ipd",
                "set",
                "approved",
                "guardset",
                "--dry-run",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0, "--dry-run previews and must NOT be refused")
        self.assertEqual(a.read_text(encoding="utf-8"), before_a)
        self.assertIn("- Status: to-review", b.read_text(encoding="utf-8"))

    def test_the_refusal_does_not_depend_on_stdout_being_a_tty(self):
        """THE FLAG-INDEPENDENCE PROPERTY, which is what the corrected diagnosis (F-7) turns on.

        `select_output` consults NO `isatty` for mode selection (ttyflags `yaxr4i` retracted the
        never-implemented non-TTY rule), so the refusal must fire identically whether stdout is a
        terminal or a pipe. Pinning it here guards against a future "fix" that reclassifies piped
        callers as AGENT, which would otherwise silently re-open the hole E-01 closes by routing them
        back to a path that only refused because it was flagged.
        """
        a, _b = self._two_plan_set()
        before = a.read_text(encoding="utf-8")
        piped = io.StringIO()  # a non-TTY stdout
        with patch("sys.stdout", piped):
            rc = cli.main(
                ["ipd", "set", "approved", "guardset", "--dir", str(self.repo_root)]
            )
        self.assertEqual(
            rc, 2, "a piped flagless call must refuse exactly as a TTY one does"
        )
        self.assertEqual(a.read_text(encoding="utf-8"), before)
        self.assertIn("confirmation required", piped.getvalue())


class TerminalReopenRefusalTests(StatusSetTestBase):
    """setterguard `4bc1nd` E-05: a plan may not be walked BACKWARDS out of a terminal disposition.

    There was a gate for entering `executed` and none for leaving it. `AGENTS.md` forbids re-opening
    an executed plan in place and directs a corrective IPD, so this pins the tool to the contract.
    """

    def test_executed_is_not_reverted_even_with_yes(self):
        """A SECOND, INDEPENDENT guard: `--yes` answers a different question and must not satisfy it."""
        plan = self.create_plan(
            "20260910-reopen-01-rp0001-done.ipd.md",
            "rp0001",
            "reopen",
            "executed",
            disposition="executed",
        )
        before = plan.read_text(encoding="utf-8")

        rc = cli.main(
            ["ipd", "set", "approved", "rp0001", "--yes", "--dir", str(self.repo_root)]
        )

        self.assertEqual(rc, 2)
        self.assertEqual(plan.read_text(encoding="utf-8"), before)
        self.assertTrue(plan.is_file())
        self.assertEqual(
            plan.parent.name, "executed", "the file must not move out of executed/"
        )

    def test_the_refusal_names_the_offending_plan_and_cites_the_corrective_route(self):
        self.create_plan(
            "20260910-reopen-02-rp0002-done.ipd.md",
            "rp0002",
            "reopen2",
            "executed",
            disposition="executed",
        )
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                [
                    "ipd",
                    "set",
                    "approved",
                    "rp0002",
                    "--yes",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        out = buf.getvalue()
        self.assertEqual(rc, 2)
        self.assertIn("20260910-reopen-02-rp0002-done.ipd.md", out)
        self.assertIn("CORRECTIVE IPD", out)
        self.assertIn("--allow-terminal-reopen", out)

    def test_an_uppercase_terminal_status_is_refused_identically(self):
        """THE CASE-FOLD, and it is correctness rather than tidiness.

        `read_artifact_record` captures the on-disk token VERBATIM, and 25 of 479 plans in
        `.aw/records/plans/executed/` carry `- Status: EXECUTED` or `- Status: DONE` from the
        pre-vocabulary era. A case-SENSITIVE guard would pass every other assertion in this class
        while leaving exactly those 25 files unprotected, which is a silent hole in the middle of the
        corpus the guard exists to protect.
        """
        plan = self.create_plan(
            "20260910-reopen-03-rp0003-shout.ipd.md",
            "rp0003",
            "reopen3",
            "EXECUTED",
            disposition="executed",
        )
        before = plan.read_text(encoding="utf-8")
        rc = cli.main(
            ["ipd", "set", "approved", "rp0003", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(plan.read_text(encoding="utf-8"), before)

    def test_the_done_alias_spelling_is_refused_identically(self):
        """`- Status: DONE` is the other pre-vocabulary terminal spelling in the corpus."""
        plan = self.create_plan(
            "20260910-reopen-07-rp0007-alias.ipd.md",
            "rp0007",
            "reopen7",
            "DONE",
            disposition="executed",
        )
        before = plan.read_text(encoding="utf-8")
        rc = cli.main(
            ["ipd", "set", "approved", "rp0007", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(plan.read_text(encoding="utf-8"), before)

    def test_superseded_to_draft_is_refused_too(self):
        """Guarding only `executed` would leave a second backwards route open.

        Measured on the pre-fix code, `superseded -> draft` succeeded silently at exit 0. It is the
        corrective un-supersede spelling a plan could be walked back through.
        """
        (self.repo_root / ".aw" / "records" / "plans" / "superseded").mkdir(
            parents=True, exist_ok=True
        )
        plan = self.create_plan(
            "20260910-reopen-04-rp0004-retired.ipd.md",
            "rp0004",
            "reopen4",
            "superseded",
            disposition="superseded",
        )
        before = plan.read_text(encoding="utf-8")
        rc = cli.main(
            ["ipd", "set", "draft", "rp0004", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(plan.read_text(encoding="utf-8"), before)

    def test_the_override_performs_it_and_records_itself_in_the_history(self):
        """The escape hatch exists (OQ-01) and is AUDITABLE IN THE FILE, not only in a shell history."""
        plan = self.create_plan(
            "20260910-reopen-05-rp0005-mistake.ipd.md",
            "rp0005",
            "reopen5",
            "executed",
            disposition="executed",
        )
        rc = cli.main(
            [
                "ipd",
                "set",
                "approved",
                "rp0005",
                "--yes",
                "--allow-terminal-reopen",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0)
        moved = self.repo_root / ".aw" / "records" / "plans" / "pending" / plan.name
        text = moved.read_text(encoding="utf-8")
        self.assertIn("- Status: approved", text)
        self.assertIn("--allow-terminal-reopen", text)

    # ---------------------------------------------------------------------------------
    # THE MUST-STILL-WORK HALF. This guard is the one most likely to OVER-refuse, and an
    # over-broad version would have blocked the very cleanup that discovered the bug,
    # which performed three retirements.
    # ---------------------------------------------------------------------------------

    def test_a_nonterminal_plan_still_advances(self):
        plan = self.create_plan(
            "20260910-fwd-01-fw0001-a.ipd.md", "fw0001", "fwd", "to-review"
        )
        self.assertEqual(
            cli.main(
                [
                    "ipd",
                    "set",
                    "reviewed",
                    "fw0001",
                    "--yes",
                    "--dir",
                    str(self.repo_root),
                ]
            ),
            0,
        )
        self.assertIn("- Status: reviewed", plan.read_text(encoding="utf-8"))
        self.assertEqual(
            cli.main(
                [
                    "ipd",
                    "set",
                    "approved",
                    "fw0001",
                    "--yes",
                    "--dir",
                    str(self.repo_root),
                ]
            ),
            0,
        )
        self.assertIn("- Status: approved", plan.read_text(encoding="utf-8"))

    def test_retirement_into_a_terminal_state_still_works(self):
        """`reviewed -> superseded` is terminal but FORWARD, so it must remain allowed."""
        self.create_plan(
            "20260910-fwd-02-fw0002-retire.ipd.md", "fw0002", "fwd2", "reviewed"
        )
        rc = cli.main(
            [
                "ipd",
                "set",
                "superseded",
                "fw0002",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0, "retirement must NOT be refused by the reopen guard")
        retired = (
            self.repo_root
            / ".aw"
            / "records"
            / "plans"
            / "superseded"
            / "20260910-fwd-02-fw0002-retire.ipd.md"
        )
        self.assertTrue(retired.is_file())
        self.assertIn("- Status: superseded", retired.read_text(encoding="utf-8"))

    def test_a_spec_transition_the_spec_table_permits_is_untouched(self):
        """SPECS ARE OUT OF SCOPE BY CONSTRUCTION, and that is required rather than incidental.

        `attention_contract.SPEC_TRANSITIONS` legitimately permits `superseded -> draft`, which the
        PLAN vocabulary would call backwards. E-02 keys on `record_type == "plans"`; this pins that so
        a later widening to "all types" cannot quietly break the shipped spec lifecycle.
        """
        spec = self.create_spec(
            "20260910-specok-01-sp0009-a.spec.md", "sp0009", "specok", "superseded"
        )
        rc = cli.main(
            ["specs", "set", "draft", "sp0009", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc, 0, "a permitted spec transition must not be refused")
        self.assertIn("- Status: draft", spec.read_text(encoding="utf-8"))

    def test_a_non_plan_artifact_transition_is_unaffected(self):
        """A PROMPT shares the `executed` token with plans and must NOT inherit the plan guard.

        This is why E-02 keys on the NORMALIZED target of a `plans` record rather than on the status
        token alone: `executed`/`done` are spellings prompts use too, and a token-keyed guard would
        have frozen every prompt in `executed/`. Driven through the UNTYPED `aw set other` spelling
        because `aw prompts set` is not a live parser surface (`aw prompts` accepts only `new`); the
        untyped verb is the shipped route to a prompt transition and reaches the same code.
        """
        prompt = self.create_prompt(
            "20260910-pr-01-pm0001-a.prompt.md",
            "pm0001",
            "prset",
            "executed",
            disposition="executed",
        )
        rc = cli.main(
            [
                "set",
                "prompts",
                "draft",
                "pm0001",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 0, "prompts are not governed by the plan terminal guard")
        moved = self.repo_root / ".aw" / "records" / "prompts" / "pending" / prompt.name
        self.assertIn("- Status: draft", moved.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
