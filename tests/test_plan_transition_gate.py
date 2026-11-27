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
from tests.record_builder import RecordBuilder, assert_field
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
            id6 = f"p0000{i}"
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
            assert_field(plan, "status", dst)

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
        assert_field(plan1, "status", "reviewed")

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
        assert_field(plan2, "status", "reviewed")

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
        assert_field(plan3, "status", "to-review")

    def test_case_d_ordinary_forward_edges_succeed(self):
        # draft -> to-review
        plan1 = self.create_plan(
            "20260901-testset-01-fw0001-plan.ipd.md",
            "fw0001",
            "testset",
            status="draft",
            readiness="go-pending-approval",
        )
        rc1 = cli.main(
            ["ipd", "set", "to-review", "fw0001", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc1, 0)
        assert_field(plan1, "status", "to-review")

        # to-review -> reviewed
        rc2 = cli.main(
            ["ipd", "set", "reviewed", "fw0001", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc2, 0)
        assert_field(plan1, "status", "reviewed")

        # reviewed -> approved
        rc3 = cli.main(
            ["ipd", "set", "approved", "fw0001", "--yes", "--dir", str(self.repo_root)]
        )
        self.assertEqual(rc3, 0)
        assert_field(plan1, "status", "approved")

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
        assert_field(found_specs[0], "status", "to-review")

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
            RecordBuilder().plan(
                title="Test Plan pl0001",
                when="2026-09-01",
                plan_role="child",
                status="to-review",
                work_kind="chore",
                priority="medium",
                set="testset",
                order=1,
                id6="pl0001",
                from_backlog="bkl001",
                scope_paths="README.md",
                highest_e_allocated="01",
                author="test",
                item_dependencies="none",
                history=["- 2026-09-01 to-review (test): created"],
                raw_fields={"Concern": "Test concern.", "Scope": "Test scope."},
                body=(
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
                    "- Cohesion rationale: not required\n"
                ),
                text_only=True,
            ),
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
        assert_field(plan, "status", "approved")

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


class TestUnreviewedPlanApprovalGate(StatusSetTestBase):
    """Behavioral tests for the unreviewed-plan approval gate (IPD 55tt85 E-01, E-02, E-04)."""

    def test_refuses_unreviewed_transitions_across_both_spellings_and_preserves_bytes(
        self,
    ):
        cases = [
            ("ur0001", "draft", "approved", ["set", "approved", "ur0001"]),
            ("ur0002", "draft", "approved", ["ipd", "set", "approved", "ur0002"]),
            ("ur0003", "to-review", "approved", ["set", "approved", "ur0003"]),
            ("ur0004", "to-review", "approved", ["ipd", "set", "approved", "ur0004"]),
            (
                "ur0005",
                "to-review",
                "auto-approved",
                ["ipd", "set", "auto-approved", "ur0005"],
            ),
            ("ur0006", "reviewed", "approved", ["set", "approved", "ur0006"]),
            ("ur0007", "reviewed", "approved", ["ipd", "set", "approved", "ur0007"]),
        ]
        for id6, src, dst, base_argv in cases:
            plan = self.create_plan(
                f"20261127-revgate-01-{id6}-plan.ipd.md",
                id6,
                "revgate",
                status=src,
            )
            before = plan.read_text(encoding="utf-8")
            out = io.StringIO()
            with patch("sys.stdout", out):
                rc = cli.main(base_argv + ["--yes", "--dir", str(self.repo_root)])
            self.assertEqual(
                rc,
                2,
                f"Expected exit 2 for {src} -> {dst} ({base_argv}), got {rc}: {out.getvalue()}",
            )
            self.assertEqual(plan.read_text(encoding="utf-8"), before)
            self.assertIn("IPD-M113", out.getvalue())

    def test_refuses_multi_plan_set_in_one_grouped_block_and_valid_json_agent_output(
        self,
    ):
        plans_list = []
        for idx, id6 in enumerate(("gu0001", "gu0002", "gu0003"), start=1):
            plans_list.append(
                self.create_plan(
                    f"20261127-grpux-0{idx}-{id6}-plan.ipd.md",
                    id6,
                    "grpux",
                    status="to-review",
                )
            )
        snapshots = {p: p.read_text(encoding="utf-8") for p in plans_list}

        # Human mode: ONE grouped FAIL block listing all 3 IDs and exact next commands.
        human_buf = io.StringIO()
        with patch("sys.stdout", human_buf):
            rc_human = cli.main(
                [
                    "set",
                    "plan",
                    "approved",
                    "grpux",
                    "--yes",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc_human, 2)
        human_out = human_buf.getvalue()
        self.assertEqual(human_out.count("Refusing to set 3 unreviewed plan(s)"), 1)
        for id6 in ("gu0001", "gu0002", "gu0003"):
            self.assertIn(id6, human_out)
        # Extract the ordered ID list from the grouped review hint so test does not depend on fs dir order
        rev_line = next(
            ln for ln in human_out.splitlines() if "Review first: aw agy review " in ln
        )
        ordered_ids = rev_line.split("aw agy review ", 1)[1].split(
            " (or aw oc review ", 1
        )[0]
        self.assertEqual(set(ordered_ids.split()), {"gu0001", "gu0002", "gu0003"})
        self.assertIn(f"aw agy review {ordered_ids}", human_out)
        self.assertIn(f"aw oc review {ordered_ids}", human_out)
        self.assertIn(f"aw agy run --full-auto {ordered_ids}", human_out)
        self.assertIn(f"aw oc run --full-auto {ordered_ids}", human_out)
        self.assertIn("--allow-unreviewed", human_out)

        # JSON mode: structured CommandResult with normalized repo-relative locations and NextActions.
        json_buf = io.StringIO()
        with patch("sys.stdout", json_buf):
            rc_json = cli.main(
                [
                    "ipd",
                    "set",
                    "approved",
                    "grpux",
                    "--yes",
                    "--json",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc_json, 2)
        payload = json.loads(json_buf.getvalue())
        self.assertEqual(payload["status"], "cannot-run")
        self.assertEqual(payload["exit_code"], 2)
        self.assertEqual(len(payload["diagnostics"]), 3)
        for diag in payload["diagnostics"]:
            self.assertEqual(diag["rule"], "status.unreviewed_approval_refused")
            self.assertFalse(diag["location"].startswith("/"))
            self.assertIn(".aw/records/plans/pending/", diag["location"])
        next_cmds = [na["command"] for na in payload["next_actions"]]
        self.assertTrue(
            any(
                c.startswith("aw agy review ")
                and set(c.split()[3:]) == {"gu0001", "gu0002", "gu0003"}
                for c in next_cmds
            ),
            next_cmds,
        )
        self.assertTrue(
            any(
                c.startswith("aw oc review ")
                and set(c.split()[3:]) == {"gu0001", "gu0002", "gu0003"}
                for c in next_cmds
            ),
            next_cmds,
        )
        self.assertTrue(
            any("--allow-unreviewed" in c and "--yes" in c for c in next_cmds),
            next_cmds,
        )

        # Agent mode with direct file path selector: valid JSONL with repo-path-free hint tokens.
        agent_buf = io.StringIO()
        with patch("sys.stdout", agent_buf):
            rc_agent = cli.main(
                [
                    "ipd",
                    "set",
                    "approved",
                    str(plans_list[0]),
                    "--yes",
                    "--agent",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc_agent, 2)
        agent_payload = json.loads(agent_buf.getvalue().strip())
        self.assertEqual(agent_payload["exit"], 2)
        self.assertEqual(agent_payload["outcome"], "cannot-run")
        self.assertEqual(
            agent_payload["diagnostics"][0]["rule"],
            "status.unreviewed_approval_refused",
        )
        next_cmd = agent_payload.get("next") or ""
        self.assertNotIn(str(self.repo_root), next_cmd)
        self.assertNotIn(".aw/records/", next_cmd)
        self.assertIn("gu0001", next_cmd)

        # JSON mode with direct file path selector: all three next_actions carry repo-path-free tokens.
        json_path_buf = io.StringIO()
        with patch("sys.stdout", json_path_buf):
            rc_json_path = cli.main(
                [
                    "ipd",
                    "set",
                    "approved",
                    str(plans_list[0]),
                    "--yes",
                    "--json",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc_json_path, 2)
        json_path_payload = json.loads(json_path_buf.getvalue())
        for na in json_path_payload["next_actions"]:
            self.assertNotIn(str(self.repo_root), na["command"])
            self.assertNotIn(".aw/records/", na["command"])
            self.assertIn("gu0001", na["command"])

        for p, before in snapshots.items():
            self.assertEqual(p.read_text(encoding="utf-8"), before)

    def test_force_flag_does_not_bypass_unreviewed_gate(self):
        plan = self.create_plan(
            "20261127-frcux-01-fr0001-plan.ipd.md",
            "fr0001",
            "frcux",
            status="to-review",
        )
        before = plan.read_text(encoding="utf-8")
        rc = cli.main(
            [
                "set",
                "approved",
                "fr0001",
                "--force",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(plan.read_text(encoding="utf-8"), before)

    def test_allow_unreviewed_does_not_bypass_step_a_negative_verdict_or_no_go(self):
        # 1. Negative review verdict in history
        rej_plan = self.create_plan(
            "20261127-negux-01-ng0001-plan.ipd.md",
            "ng0001",
            "negux",
            status="reviewed",
            history=[
                "- 2026-11-27 /plan-review (tester): REJECT - NEEDS REPLAN; unsound.",
                "- 2026-11-27 draft (author): initial draft.",
            ],
        )
        before_rej = rej_plan.read_text(encoding="utf-8")
        rc_rej = cli.main(
            [
                "ipd",
                "set",
                "approved",
                "ng0001",
                "--allow-unreviewed",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc_rej, 1)
        self.assertEqual(rej_plan.read_text(encoding="utf-8"), before_rej)

        # 2. Readiness: no-go
        nogo_plan = self.create_plan(
            "20261127-negux-02-ng0002-plan.ipd.md",
            "ng0002",
            "negux",
            status="reviewed",
            readiness="no-go",
        )
        before_nogo = nogo_plan.read_text(encoding="utf-8")
        rc_nogo = cli.main(
            [
                "ipd",
                "set",
                "approved",
                "ng0002",
                "--allow-unreviewed",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc_nogo, 1)
        self.assertEqual(nogo_plan.read_text(encoding="utf-8"), before_nogo)

    def test_allow_unreviewed_and_ignore_review_error_succeed_record_history_and_warn(
        self,
    ):
        # Human mode with --allow-unreviewed
        p1 = self.create_plan(
            "20261127-ovrux-01-ov0001-plan.ipd.md",
            "ov0001",
            "ovrux",
            status="to-review",
        )
        out1 = io.StringIO()
        err1 = io.StringIO()
        with patch("sys.stdout", out1), patch("sys.stderr", err1):
            rc1 = cli.main(
                [
                    "ipd",
                    "set",
                    "approved",
                    "ov0001",
                    "--allow-unreviewed",
                    "--yes",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc1, 0)
        assert_field(p1, "status", "approved")
        text1 = p1.read_text(encoding="utf-8")
        self.assertIn(", --allow-unreviewed)", text1)
        self.assertNotIn("- Readiness:", text1)
        combined1 = out1.getvalue() + err1.getvalue()
        self.assertIn("IPD-M113", combined1)
        self.assertIn("ov0001", combined1)
        self.assertIn("- Readiness:", combined1)

        # Alias --ignore-review-error
        p2 = self.create_plan(
            "20261127-ovrux-02-ov0002-plan.ipd.md",
            "ov0002",
            "ovrux",
            status="draft",
        )
        rc2 = cli.main(
            [
                "set",
                "approved",
                "ov0002",
                "--ignore-review-error",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc2, 0)
        assert_field(p2, "status", "approved")
        self.assertIn(", --allow-unreviewed)", p2.read_text(encoding="utf-8"))

        # Structured --json and --agent modes emit valid JSON/JSONL with warning diagnostic and data["warnings"]
        for mode_flag, id6 in (("--json", "ov0003"), ("--agent", "ov0004")):
            p = self.create_plan(
                f"20261127-ovrux-03-{id6}-plan.ipd.md",
                id6,
                "ovrux",
                status="to-review",
            )
            out_s = io.StringIO()
            with patch("sys.stdout", out_s):
                rc_s = cli.main(
                    [
                        "ipd",
                        "set",
                        "approved",
                        id6,
                        "--allow-unreviewed",
                        "--yes",
                        mode_flag,
                        "--dir",
                        str(self.repo_root),
                    ]
                )
            self.assertEqual(rc_s, 0)
            assert_field(p, "status", "approved")
            parsed = json.loads(out_s.getvalue().strip())
            diags = parsed.get("diagnostics", [])
            self.assertTrue(
                any(
                    d.get("rule") == "status.unreviewed_approval_overridden"
                    and (mode_flag == "--agent" or d.get("severity") == "warning")
                    for d in diags
                ),
                f"Missing warning diagnostic in {mode_flag}: {diags}",
            )
            if mode_flag == "--json":
                warnings = parsed.get("data", {}).get("warnings", [])
                self.assertTrue(
                    any("IPD-M113" in w and id6 in w for w in warnings),
                    f"Missing IPD-M113 warning in --json data.warnings: {warnings}",
                )
            else:
                self.assertEqual(
                    parsed.get("findings_by_severity", {}).get("warning"), 1
                )

    def test_schema2_log_format_plan_records_allow_unreviewed_in_event_overrides(self):
        import os
        import subprocess
        from agent_workflows import artifact_meta as meta

        # Initialize git repo + metadata_schema: 2 with repo records backend
        subprocess.run(["git", "init", "-q"], cwd=self.repo_root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=self.repo_root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=self.repo_root,
            check=True,
        )
        cfg = self.repo_root / ".aw" / "config"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "project.json").write_text(
            json.dumps({"metadata_schema": 2, "records_backend": "repository"}) + "\n",
            encoding="utf-8",
        )
        id6 = "lg0099"
        rel = f"plans/pending/20261127-logux-01-{id6}-plan.ipd.md"
        plan_path = self.repo_root / ".aw" / "records" / rel
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(
            meta.render_in_file_mirror(id6, "ipd", "to-review")
            + "# IPD: Log format plan\n\n## Goal\nGoal.\n",
            encoding="utf-8",
        )
        envelope = {
            "v": 1,
            "at": "2026-11-27T01:00:00Z",
            "actor": {"tool": "aw test"},
        }
        events = [
            dict(
                envelope,
                seq=1,
                append=1,
                op="create",
                path=rel,
                fields={
                    "id": id6,
                    "type": "ipd",
                    "status": "draft",
                    "set": "logux",
                    "order": 1,
                    "plan_role": "child",
                    "priority": "medium",
                    "work_kind": "chore",
                },
            ),
            dict(
                envelope,
                seq=2,
                append=2,
                op="transition",
                to="to-review",
                **{"from": "draft"},
            ),
        ]
        meta_dir = self.repo_root / ".aw" / "records" / "meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        log_path = meta_dir / f"{id6}.jsonl"
        log_path.write_bytes(
            "".join(meta.encode_event(e) for e in events).encode("utf-8")
        )
        before_log = log_path.read_bytes()

        with patch.dict(os.environ, {"AW_HOME": str(self.repo_root / "_aw_home")}):
            # Without override: refused exit 2, log untouched
            rc_ref = cli.main(
                [
                    "ipd",
                    "set",
                    "approved",
                    id6,
                    "--yes",
                    "--no-commit",
                    "--dir",
                    str(self.repo_root),
                ]
            )
            self.assertEqual(rc_ref, 2)
            self.assertEqual(log_path.read_bytes(), before_log)

            # With --allow-unreviewed: succeeds and records overrides: ["allow-unreviewed"]
            rc_ok = cli.main(
                [
                    "ipd",
                    "set",
                    "approved",
                    id6,
                    "--allow-unreviewed",
                    "--yes",
                    "--no-commit",
                    "--dir",
                    str(self.repo_root),
                ]
            )
            self.assertEqual(rc_ok, 0)
        written = [
            json.loads(ln)
            for ln in log_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        transition_ev = next(
            ev
            for ev in reversed(written)
            if ev.get("op") == "transition" and ev.get("to") == "approved"
        )
        self.assertEqual(transition_ev.get("overrides"), ["allow-unreviewed"])
        meta.validate_event(transition_ev, "ipd")

    def test_same_status_metadata_updates_and_skip_refused_in_mixed_batch(self):
        # Already-approved unreviewed plan allows same-status priority and dependencies updates
        ap_plan = self.create_plan(
            "20261127-sameux-01-sm0001-plan.ipd.md",
            "sm0001",
            "sameux",
            status="approved",
        )
        rc_prio = cli.main(
            [
                "ipd",
                "set",
                "approved",
                "sm0001",
                "--priority",
                "high",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc_prio, 0)
        assert_field(ap_plan, "priority", "high")
        assert_field(ap_plan, "status", "approved")

        rc_deps = cli.main(
            [
                "ipd",
                "dependencies",
                "set",
                "sm0001",
                "none",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc_deps, 0)

        # Mixed batch with --skip-refused: reviewed+readiness applies, unreviewed skipped
        ready_plan = self.create_plan(
            "20261127-mixux-01-mx0001-plan.ipd.md",
            "mx0001",
            "mixux",
            status="reviewed",
            readiness="go-pending-approval",
        )
        unrev_plan = self.create_plan(
            "20261127-mixux-02-mx0002-plan.ipd.md",
            "mx0002",
            "mixux",
            status="to-review",
        )
        rc_all = cli.main(
            [
                "ipd",
                "set",
                "approved",
                "mixux",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc_all, 2)
        assert_field(ready_plan, "status", "reviewed")
        assert_field(unrev_plan, "status", "to-review")

        rc_skip = cli.main(
            [
                "ipd",
                "set",
                "approved",
                "mixux",
                "--skip-refused",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc_skip, 1)
        assert_field(ready_plan, "status", "approved")
        assert_field(unrev_plan, "status", "to-review")

    def test_reviewed_with_readiness_passes_and_all_four_parsers_and_non_plans_clean(
        self,
    ):
        # 1. Reviewed plan with Readiness approves cleanly without any override flag
        plan = self.create_plan(
            "20261127-okux-01-ok0099-plan.ipd.md",
            "ok0099",
            "okux",
            status="reviewed",
            readiness="go-pending-approval",
        )
        out = io.StringIO()
        with patch("sys.stdout", out):
            rc = cli.main(
                [
                    "ipd",
                    "set",
                    "approved",
                    "ok0099",
                    "--yes",
                    "--dir",
                    str(self.repo_root),
                ]
            )
        self.assertEqual(rc, 0)
        assert_field(plan, "status", "approved")
        self.assertNotIn("--allow-unreviewed", plan.read_text(encoding="utf-8"))
        self.assertNotIn("IPD-M113", out.getvalue())

        # 2. All four set parsers accept both --allow-unreviewed and --ignore-review-error
        parser = cli._build_parser()
        for argv in (
            ["ipd", "set", "approved", "ok0099", "--allow-unreviewed"],
            ["ipd", "set", "approved", "ok0099", "--ignore-review-error"],
            ["set", "approved", "ok0099", "--allow-unreviewed"],
            ["set", "approved", "ok0099", "--ignore-review-error"],
            ["backlog", "set", "open", "bk0001", "--allow-unreviewed"],
            ["backlog", "set", "open", "bk0001", "--ignore-review-error"],
            ["specs", "set", "to-review", "sp0001", "--allow-unreviewed"],
            ["specs", "set", "to-review", "sp0001", "--ignore-review-error"],
        ):
            ns = parser.parse_args(argv)
            self.assertTrue(ns.allow_unreviewed, f"Failed for {argv}")

        # 3. Non-plan record types (specs, backlog) ignore the flag cleanly
        spec = self.create_spec(
            "20261127-npux-01-sp0099-spec.spec.md",
            "sp0099",
            "npux",
            status="draft",
        )
        rc_spec = cli.main(
            [
                "specs",
                "set",
                "to-review",
                "sp0099",
                "--allow-unreviewed",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc_spec, 0)
        moved_spec = (
            self.repo_root / ".aw" / "records" / "specs" / "to-review" / spec.name
        )
        assert_field(moved_spec, "status", "to-review")
        self.assertNotIn("--allow-unreviewed", moved_spec.read_text(encoding="utf-8"))

        backlog = self.create_backlog(
            "20261127-npux-01-bk0099-item.backlog.md",
            "bk0099",
            "npux",
            status="open",
        )
        rc_bk = cli.main(
            [
                "backlog",
                "set",
                "parked",
                "bk0099",
                "--ignore-review-error",
                "--yes",
                "--dir",
                str(self.repo_root),
            ]
        )
        self.assertEqual(rc_bk, 0)
        moved_bk = (
            self.repo_root / ".aw" / "records" / "backlog" / "parked" / backlog.name
        )
        assert_field(moved_bk, "status", "parked")
        self.assertNotIn("--allow-unreviewed", moved_bk.read_text(encoding="utf-8"))
