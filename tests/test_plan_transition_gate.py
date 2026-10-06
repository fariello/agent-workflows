"""Tests pinning plan status transition gate by outcome (IPD nvsz19).

Verifies that illegal plan lifecycle backwards transitions fail closed at the setter
while preserving legal backwards recovery edges, forward transitions, retirements,
other artifact types, agent JSON reporting, dry-run refusals, finalize delegations,
and case-folded uppercase statuses.
"""

from __future__ import annotations

import io
import json
from unittest.mock import patch

from agent_workflows import cli
from tests.test_status_set import StatusSetTestBase


class TestPlanTransitionGate(StatusSetTestBase):
    def setUp(self):
        super().setUp()
        (self.repo_root / ".aw" / "records" / "plans" / "superseded").mkdir(
            parents=True, exist_ok=True
        )
        (self.repo_root / ".aw" / "records" / "plans" / "not-executed").mkdir(
            parents=True, exist_ok=True
        )

    def test_case_a_illegal_nonterminal_backwards_edges_refuse_and_preserve_file(self):
        # Spec ipd-spec E.1 as amended by hm1h3l (26m1nb): every non-terminal backward move
        # requires an explicit --message. Without --message, the setter refuses with exit 2
        # and preserves the file; with --message, the transition succeeds (exit 0).
        edges = [
            ("approved", "draft"),
            ("approved", "to-review"),
            ("reviewed", "draft"),
            ("to-review", "draft"),
        ]
        for i, (src, dst) in enumerate(edges):
            id6 = f"p000{i}"
            filename = f"20260901-testset-01-{id6}-plan.ipd.md"
            plan = self.create_plan(filename, id6, "testset", status=src)
            before = plan.read_text(encoding="utf-8")

            # Refused without --message (rc=2)
            rc = cli.main(
                ["ipd", "set", dst, id6, "--yes", "--dir", str(self.repo_root)]
            )
            self.assertEqual(
                rc, 2, f"Expected rc=2 for backward edge without message {src} -> {dst}"
            )
            self.assertTrue(plan.exists())
            self.assertEqual(
                plan.read_text(encoding="utf-8"),
                before,
                f"File content must be byte-identical after refused transition {src} -> {dst}",
            )

            # Accepted with --message (rc=0)
            rc_with_msg = cli.main(
                [
                    "ipd",
                    "set",
                    dst,
                    id6,
                    "--message",
                    "demoting for rework",
                    "--yes",
                    "--dir",
                    str(self.repo_root),
                ]
            )
            self.assertEqual(
                rc_with_msg,
                0,
                f"Expected rc=0 for backward edge with message {src} -> {dst}",
            )
            self.assertIn(f"- Status: {dst}", plan.read_text(encoding="utf-8"))

    def test_case_b_refusal_across_both_real_spellings(self):
        # Spelling 1: aw set <status> <selector>
        plan1 = self.create_plan(
            "20260901-testset-01-sp0001-plan.ipd.md",
            "sp0001",
            "testset",
            status="approved",
        )
        before1 = plan1.read_text(encoding="utf-8")
        rc1 = cli.main(
            ["set", "draft", "sp0001", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc1, 2)
        self.assertEqual(plan1.read_text(encoding="utf-8"), before1)

        # Spelling 2: aw ipd set <status> <selector>
        plan2 = self.create_plan(
            "20260901-testset-01-sp0002-plan.ipd.md",
            "sp0002",
            "testset",
            status="approved",
        )
        before2 = plan2.read_text(encoding="utf-8")
        rc2 = cli.main(
            ["ipd", "set", "draft", "sp0002", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc2, 2)
        self.assertEqual(plan2.read_text(encoding="utf-8"), before2)

    def test_case_c_enumerated_legal_backward_recovery_edges_succeed(self):
        # Backward recovery edges require explicit --message and succeed:
        # 1. approved -> reviewed
        plan1 = self.create_plan(
            "20260901-testset-01-lg0001-plan.ipd.md",
            "lg0001",
            "testset",
            status="approved",
        )
        rc1 = cli.main(
            [
                "ipd",
                "set",
                "reviewed",
                "lg0001",
                "--message",
                "recovering",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc1, 0)
        self.assertIn("- Status: reviewed", plan1.read_text(encoding="utf-8"))

        # 2. auto-approved -> reviewed (prescribed by spec 25kzda IPD-AUTO-APPROVAL)
        plan2 = self.create_plan(
            "20260901-testset-01-lg0002-plan.ipd.md",
            "lg0002",
            "testset",
            status="auto-approved",
        )
        rc2 = cli.main(
            [
                "ipd",
                "set",
                "reviewed",
                "lg0002",
                "--message",
                "recovering",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc2, 0)
        self.assertIn("- Status: reviewed", plan2.read_text(encoding="utf-8"))

        # 3. reviewed -> to-review
        plan3 = self.create_plan(
            "20260901-testset-01-lg0003-plan.ipd.md",
            "lg0003",
            "testset",
            status="reviewed",
        )
        rc3 = cli.main(
            [
                "ipd",
                "set",
                "to-review",
                "lg0003",
                "--message",
                "recovering",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc3, 0)
        self.assertIn("- Status: to-review", plan3.read_text(encoding="utf-8"))

    def test_case_d_ordinary_forward_edges_succeed(self):
        # draft -> to-review
        plan1 = self.create_plan(
            "20260901-testset-01-fw0001-plan.ipd.md",
            "fw0001",
            "testset",
            status="draft",
        )
        rc1 = cli.main(
            ["ipd", "set", "to-review", "fw0001", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc1, 0)
        self.assertIn("- Status: to-review", plan1.read_text(encoding="utf-8"))

        # to-review -> reviewed
        rc2 = cli.main(
            ["ipd", "set", "reviewed", "fw0001", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc2, 0)
        self.assertIn("- Status: reviewed", plan1.read_text(encoding="utf-8"))

        # reviewed -> approved
        rc3 = cli.main(
            ["ipd", "set", "approved", "fw0001", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc3, 0)
        self.assertIn("- Status: approved", plan1.read_text(encoding="utf-8"))

    def test_case_e_retirement_into_superseded_and_not_executed_succeeds(self):
        # reviewed -> superseded
        self.create_plan(
            "20260901-testset-01-rt0001-plan.ipd.md",
            "rt0001",
            "testset",
            status="reviewed",
        )
        rc1 = cli.main(
            [
                "ipd",
                "set",
                "superseded",
                "rt0001",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc1, 0)
        superseded_path1 = (
            self.repo_root
            / ".aw"
            / "records"
            / "plans"
            / "superseded"
            / "20260901-testset-01-rt0001-plan.ipd.md"
        )
        self.assertTrue(superseded_path1.exists())
        self.assertIn(
            "- Status: superseded", superseded_path1.read_text(encoding="utf-8")
        )

        # approved -> not-executed
        self.create_plan(
            "20260901-testset-01-rt0002-plan.ipd.md",
            "rt0002",
            "testset",
            status="approved",
        )
        rc2 = cli.main(
            [
                "ipd",
                "set",
                "not-executed",
                "rt0002",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc2, 0)
        not_executed_path2 = (
            self.repo_root
            / ".aw"
            / "records"
            / "plans"
            / "not-executed"
            / "20260901-testset-01-rt0002-plan.ipd.md"
        )
        self.assertTrue(not_executed_path2.exists())
        self.assertIn(
            "- Status: not-executed", not_executed_path2.read_text(encoding="utf-8")
        )

    def test_case_f_non_plan_artifacts_are_untouched(self):
        # Spec transition permitted by its own table (draft -> to-review) succeeds
        spec = self.create_spec(
            "20260901-testset-01-spc001-spec.spec.md",
            "spc001",
            "testset",
            status="draft",
        )
        rc_spec = cli.main(
            [
                "specs",
                "set",
                "to-review",
                "spc001",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc_spec, 0)
        found_specs = list(self.repo_root.rglob(spec.name))
        self.assertTrue(found_specs, f"Expected {spec.name} to exist in repo")
        self.assertIn("- Status: to-review", found_specs[0].read_text(encoding="utf-8"))

        # Backlog transition (open -> graduated) succeeds
        backlog = self.create_backlog(
            "20260901-testset-01-bkl001-item.backlog.md",
            "bkl001",
            "testset",
            status="open",
        )
        plan_dir = self.repo_root / ".aw" / "records" / "plans" / "pending"
        plan_dir.mkdir(parents=True, exist_ok=True)
        (plan_dir / "20260901-testset-01-pl0001-plan.ipd.md").write_text(
            "# IPD: Test Plan pl0001\n\n"
            "- Date: 2026-09-01\n"
            "- Kind: child\n"
            "- Concern: Test concern.\n"
            "- Scope: Test scope.\n"
            "- Status: to-review\n"
            "- Work-Kind: chore\n"
            "- Priority: medium\n"
            "- Set: testset\n"
            "- Order: 1\n"
            "- Id: pl0001\n"
            "- From-Backlog: bkl001\n"
            "- Scope-Paths: README.md\n"
            "- Highest E allocated: 01\n"
            "- Author: test\n"
            "- Item-Dependencies: none\n\n"
            "## Workflow history\n"
            "- 2026-09-01 to-review (test): created\n\n"
            "## Goal\n"
            "Goal pl0001.\n\n"
            "## Detailed Implementation Checklist (TODO)\n"
            "### Task group 1: work\n"
            "- [ ] E-01 Work item\n"
            "  - Depends on: none\n"
            "  - Expected outcome: done\n"
            "  - Execution state: pending\n\n"
            "## Project conventions discovered (Step 0)\n"
            "None.\n\n"
            "## Findings\n"
            "None.\n\n"
            "## Proposed changes (ordered, validatable)\n"
            "1. E-01 do work.\n\n"
            "## Deferred / out of scope (with reason)\n"
            "- None.\n\n"
            "## Scope check\n"
            "- None.\n\n"
            "## Required tests / validation\n"
            "- None.\n\n"
            "## Spec / documentation sync\n"
            "- None.\n\n"
            "## Open questions\n"
            "- None.\n\n"
            "## Validation and cross-check (verify before reporting done)\n"
            "- [ ] V-01 validates E-01\n"
            "  - Required evidence: check.\n"
            "  - Observed evidence:\n"
            "  - Result: pending\n\n"
            "## Approval and execution gate\n"
            "- Size assessment: standard\n"
            "- Cohesion rationale: not required\n",
            encoding="utf-8",
        )
        rc_backlog = cli.main(
            [
                "backlog",
                "set",
                "graduated",
                "bkl001",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc_backlog, 0)
        found_backlog = list(self.repo_root.rglob(backlog.name))
        self.assertTrue(found_backlog, f"Expected {backlog.name} to exist in repo")
        self.assertIn(
            "- Status: graduated", found_backlog[0].read_text(encoding="utf-8")
        )

    def test_case_g_refusal_reported_in_agent_json_mode(self):
        self.create_plan(
            "20260901-testset-01-ag0001-plan.ipd.md",
            "ag0001",
            "testset",
            status="approved",
        )
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                [
                    "ipd",
                    "set",
                    "draft",
                    "ag0001",
                    "--yes",
                    "--agent",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc, 2)
        payload = json.loads(buf.getvalue().strip())
        self.assertEqual(payload.get("exit"), 2)
        self.assertEqual(payload.get("outcome"), "cannot-run")
        diagnostics = payload.get("diagnostics", [])
        self.assertTrue(
            any(
                d.get("rule") == "status.backward_plan_message_required"
                for d in diagnostics
            ),
            f"Expected rule 'status.backward_plan_message_required' in diagnostics: {diagnostics}",
        )

    def test_case_h_dry_run_on_illegal_edge_refuses_without_previewing(self):
        plan = self.create_plan(
            "20260901-testset-01-dr0001-plan.ipd.md",
            "dr0001",
            "testset",
            status="approved",
        )
        buf = io.StringIO()
        err_buf = io.StringIO()
        with patch("sys.stdout", buf), patch("sys.stderr", err_buf):
            rc = cli.main(
                [
                    "ipd",
                    "set",
                    "draft",
                    "dr0001",
                    "--dry-run",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc, 2)
        combined = buf.getvalue() + err_buf.getvalue()
        self.assertNotIn("dry-run", combined.lower().split("refusing")[0])
        self.assertIn("refusing before making changes", combined.lower())
        self.assertIn("- Status: approved", plan.read_text(encoding="utf-8"))

    def test_case_i_target_executed_path_is_undisturbed(self):
        # Naive gate was measured to break this (PR-801, F-06b), returning exit 1 transition error
        # on draft/to-review -> executed instead of reaching finalize delegation.
        sources = ["draft", "to-review", "reviewed", "approved"]
        for i, src in enumerate(sources):
            id6 = f"ex000{i}"
            filename = f"20260901-testset-01-{id6}-plan.ipd.md"
            self.create_plan(filename, id6, "testset", status=src)
            out_buf = io.StringIO()
            err_buf = io.StringIO()
            with patch("sys.stdout", out_buf), patch("sys.stderr", err_buf):
                rc = cli.main(
                    [
                        "ipd",
                        "set",
                        "executed",
                        id6,
                        "--yes",
                        "--dir",
                        str(self.repo_root),
                    ]
                )
            # Must exit 2 (cannot-run / usage from finalize delegation), NOT exit 1 (transition error)
            self.assertEqual(
                rc,
                2,
                f"Expected exit 2 from finalize delegation for {src} -> executed, got {rc}",
            )
            combined_text = out_buf.getvalue() + err_buf.getvalue()
            self.assertIn(
                "moving a plan to 'executed' now delegates into the gated `aw ipd finalize`",
                combined_text,
                f"Expected finalize delegation actor refusal message for {src} -> executed, got: {combined_text}",
            )
            self.assertIn(
                "REQUIRES an attributed --actor",
                combined_text,
            )

    def test_case_j_uppercase_status_is_gated_identically(self):
        # Naive unfolded gate was measured to pass uppercase statuses at exit 0 (PR-803, F-06c),
        # because read_artifact_record captures token verbatim and _status_rank is a bare dict lookup.
        upper_sources = ["APPROVED", "REVIEWED"]
        for i, st in enumerate(upper_sources):
            id6 = f"up000{i}"
            filename = f"20260901-testset-01-{id6}-plan.ipd.md"
            plan = self.create_plan(filename, id6, "testset", status=st)
            before = plan.read_text(encoding="utf-8")

            rc = cli.main(
                ["ipd", "set", "draft", id6, "--yes", "--dir", str(self.repo_root)]
            )
            self.assertEqual(rc, 2, f"Expected rc=2 for uppercase source {st} -> draft")
            self.assertTrue(plan.exists())
            self.assertEqual(
                plan.read_text(encoding="utf-8"),
                before,
                f"File content must be byte-identical after refused transition for {st} -> draft",
            )
