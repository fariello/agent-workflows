"""Tests for freeze-time whole-run refusal gate (spec z7nbn1 1.3, 1.4, 1.7; plan jdn790).

Validates:
E-07 / V-07: The three refusal classes (5.1 undetermined, 5.2 malformed, 5.3 unsatisfiable dep)
             and the two preserved-behavior cases (5.3a failure cascade and in-batch proceed).
E-08 / V-08: The three predicate-boundary cases (a, b, c) and review-consumer relaxation.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests import support
from tests.record_builder import RecordBuilder

BOTH_HOSTS = (
    ("oc", oc_runipd, "run_opencode"),
    ("agy", agy_runipd, "run_agy_turn"),
)


def _init_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
    )
    for d in (
        repo / ".aw" / "records" / "plans" / "pending",
        repo / ".aw" / "records" / "plans" / "executed",
        repo / ".aw" / "records" / "specs" / "approved",
        repo / ".aw" / "records" / "specs" / "draft",
        repo / ".aw" / "records" / "specs" / "to-review",
        repo / ".aw" / "records" / "specs" / "reviewed",
        repo / ".aw" / "records" / "specs" / "implementing",
        repo / ".aw" / "records" / "backlog" / "open",
    ):
        d.mkdir(parents=True, exist_ok=True)
    (repo / "README.md").write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
    return repo


def _write_plan(
    repo: Path,
    id6: str,
    *,
    status: str = "approved",
    dependencies: list[str] | None = None,
    order: int = 1,
    setid: str = "demo",
    readiness: str | None = None,
    approval: str | None = None,
    raw_content: str | None = None,
) -> Path:
    if raw_content is not None:
        pending = repo / ".aw" / "records" / "plans" / "pending"
        plan_path = pending / f"20260927-{setid}-{order:02d}-{id6}-plan.ipd.md"
        plan_path.write_text(raw_content, encoding="utf-8")
        return plan_path

    # rdyreq (`fhinri`, IPD-M113): a reviewed/ready-to-execute plan must carry `- Readiness:`, so a
    # gated status defaults to the review output, attested by a /plan-review history line (IPD-M107).
    gated = status in ("reviewed", "approved", "auto-approved")
    eff_readiness = (
        "go-pending-approval" if (readiness is None and gated) else readiness
    )
    if approval is None:
        eff_approval: str | None = "2026-09-27, test" if status == "approved" else None
    else:
        eff_approval = approval or None

    history = [
        f"- 2026-09-27 {status} (tester): {status if status != 'reviewed' else 'APPROVE'}"
    ]
    if gated:
        history.append("- 2026-09-27 /plan-review (tester): APPROVE")

    return Path(
        RecordBuilder(repo).plan(
            id6=id6,
            title=f"Plan {id6}",
            when="2026-09-27",
            set=setid,
            order=order,
            slug="plan",
            status=status,
            scope_paths="README.md, src/demo.txt",
            item_dependencies=", ".join(dependencies) if dependencies else "none",
            priority="medium",
            work_kind="feature",
            readiness=eff_readiness,
            approval=eff_approval,
            history=history,
            body=(
                f"## Goal\nGoal for {id6}.\n\n"
                "## Detailed Implementation Checklist (TODO)\n"
                "### Task group 1: work\n"
                "- [ ] E-01 Step 1\n"
                "  - Depends on: none\n"
                "  - Expected outcome: done\n"
                "  - Execution state: pending\n\n"
                "## Project conventions discovered (Step 0)\nNone.\n\n"
                "## Findings\nNone.\n\n"
                "## Proposed changes (ordered, validatable)\nNone.\n\n"
                "## Deferred / out of scope (with reason)\nNone.\n\n"
                "## Scope check\nNone.\n\n"
                "## Required tests / validation\nNone.\n\n"
                "## Spec / documentation sync\nNone.\n\n"
                "## Open questions\nNone.\n\n"
                "## Validation and cross-check (verify before reporting done)\n"
                "- [ ] V-01 validates E-01\n"
                "  - Required evidence: done\n"
                "  - Observed evidence:\n"
                "  - Result: pending\n\n"
                "## Approval and execution gate\n"
                "- Size assessment: standard\n"
                "- Cohesion rationale: not required"
            ),
        )
    )


def _assert_no_durable_state(
    test_case: unittest.TestCase, repo: Path, valid_plan_path: Path
) -> None:
    # 1. Zero run directories created under state_root
    state_dir = runner_shared.state_root(repo)
    if state_dir.exists():
        run_dirs = [
            d for d in state_dir.iterdir() if d.is_dir() and d.name.startswith("run-")
        ]
        test_case.assertEqual(run_dirs, [], f"Expected no run dir, found: {run_dirs}")

    # 2. No lane worktrees created
    proc = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    worktree_lines = [
        line for line in proc.stdout.splitlines() if line.startswith("worktree ")
    ]
    test_case.assertEqual(
        len(worktree_lines),
        1,
        f"Expected exactly 1 worktree (main repo), found: {worktree_lines}",
    )

    # 3. Valid plan in the same selection did not run
    text = valid_plan_path.read_text(encoding="utf-8")
    test_case.assertIn("Execution state: pending", text)


class TestRefusalClassCases(unittest.TestCase):
    """E-07 (1), (2), (3): The three freeze-time refusal classes on both hosts."""

    def test_5_1_undetermined_action_refuses_at_freeze(self):
        """5.1: an `implementing` spec (undetermined row) plus a valid plan refuses at freeze."""
        for label, module, _ in BOTH_HOSTS:
            with self.subTest(host=label), tempfile.TemporaryDirectory() as td:
                repo = _init_repo(Path(td))
                val_plan = _write_plan(repo, "val001", status="approved")
                RecordBuilder(repo).spec(
                    id6="spc001",
                    title="Spec spc001",
                    when="2026-09-27",
                    status="implementing",
                    slug="spec",
                    history=["- 2026-09-27 implementing (tester): set status"],
                    body="## 1. Overview\nOverview of spec spc001.",
                )
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "add artifacts"], cwd=repo, check=True
                )

                parser = module.build_parser()
                args = parser.parse_args(
                    [
                        "start",
                        "val001",
                        "spc001",
                        "--prepare-only",
                        "--repo",
                        str(repo),
                        "--allow-mixed",
                    ]
                )
                with self.assertRaises(runner_shared.DriverError) as cm:
                    module.initialize_run(args)

                exc_msg = str(cm.exception)
                self.assertIn("[RUN-UNDETERMINED-ACTION]", exc_msg)
                self.assertIn("spec spc001", exc_msg)
                self.assertIn(
                    "has status implementing, for which no action is defined", exc_msg
                )
                self.assertIn(
                    "No work started, and nothing durable was created.", exc_msg
                )

                _assert_no_durable_state(self, repo, val_plan)

    def test_5_2_malformed_plan_refuses_at_freeze(self):
        """5.2: a malformed plan plus a valid plan refuses at freeze."""
        for label, module, _ in BOTH_HOSTS:
            with self.subTest(host=label), tempfile.TemporaryDirectory() as td:
                repo = _init_repo(Path(td))
                val_plan = _write_plan(repo, "val001", status="approved")
                bad_content = RecordBuilder().plan(
                    title="Bad plan",
                    when="2026-09-27",
                    status="approved",
                    id6="bad001",
                    text_only=True,
                )
                _write_plan(repo, "bad001", raw_content=bad_content)
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "add artifacts"], cwd=repo, check=True
                )

                parser = module.build_parser()
                args = parser.parse_args(
                    ["start", "val001", "bad001", "--prepare-only", "--repo", str(repo)]
                )
                with self.assertRaises(runner_shared.DriverError) as cm:
                    module.initialize_run(args)

                exc_msg = str(cm.exception)
                self.assertIn("[RUN-STRUCTURE-PREFLIGHT]", exc_msg)
                self.assertIn("bad001", exc_msg)
                self.assertIn(
                    "No work started, and nothing durable was created.", exc_msg
                )

                _assert_no_durable_state(self, repo, val_plan)

    def test_5_2_malformed_spec_refuses_at_freeze(self):
        """5.2: a malformed spec plus a valid plan refuses at freeze (proves severity != 'info' fires, F-8)."""
        for label, module, _ in BOTH_HOSTS:
            with self.subTest(host=label), tempfile.TemporaryDirectory() as td:
                repo = _init_repo(Path(td))
                val_plan = _write_plan(repo, "val001", status="approved")
                RecordBuilder(repo).spec(
                    id6="badspc",
                    title="Malformed spec badspc",
                    when="2026-09-27",
                    status="draft",
                    slug="spec",
                    history=[],
                )
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "add artifacts"], cwd=repo, check=True
                )

                parser = module.build_parser()
                args = parser.parse_args(
                    [
                        "start",
                        "val001",
                        "badspc",
                        "--prepare-only",
                        "--repo",
                        str(repo),
                        "--allow-mixed",
                    ]
                )
                with self.assertRaises(runner_shared.DriverError) as cm:
                    module.initialize_run(args)

                exc_msg = str(cm.exception)
                self.assertIn("[RUN-STRUCTURE-PREFLIGHT]", exc_msg)
                self.assertIn("spec badspc", exc_msg)
                self.assertIn("attention.history-missing", exc_msg)
                self.assertIn(
                    "No work started, and nothing durable was created.", exc_msg
                )

                _assert_no_durable_state(self, repo, val_plan)

    def test_5_2_malformed_backlog_item_refuses_at_freeze(self):
        """5.2: a malformed backlog item plus a valid plan refuses at freeze (proves severity != 'info' fires, F-8)."""
        for label, module, _ in BOTH_HOSTS:
            with self.subTest(host=label), tempfile.TemporaryDirectory() as td:
                repo = _init_repo(Path(td))
                val_plan = _write_plan(repo, "val001", status="approved")
                RecordBuilder(repo).backlog(
                    id6="badbkg",
                    status="open",
                    when="2026-09-27",
                    set="demo",
                    slug="item",
                    raw_fields={"priority": None},
                )
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "add artifacts"], cwd=repo, check=True
                )

                parser = module.build_parser()
                args = parser.parse_args(
                    [
                        "start",
                        "val001",
                        "badbkg",
                        "--prepare-only",
                        "--repo",
                        str(repo),
                        "--allow-mixed",
                    ]
                )
                with self.assertRaises(runner_shared.DriverError) as cm:
                    module.initialize_run(args)

                exc_msg = str(cm.exception)
                self.assertIn("[RUN-STRUCTURE-PREFLIGHT]", exc_msg)
                self.assertIn("backlog badbkg", exc_msg)
                self.assertIn("backlog.priority-invalid", exc_msg)
                self.assertIn(
                    "No work started, and nothing durable was created.", exc_msg
                )

                _assert_no_durable_state(self, repo, val_plan)

    def test_5_3_unsatisfiable_dependency_refuses_at_freeze(self):
        """5.3: `efg456` + `ind789` refuses naming `executed:abc123` when abc123 is absent from run and not executed on disk."""
        for label, module, _ in BOTH_HOSTS:
            with self.subTest(host=label), tempfile.TemporaryDirectory() as td:
                repo = _init_repo(Path(td))
                _write_plan(repo, "abc123", status="approved", order=1)
                _write_plan(
                    repo,
                    "efg456",
                    status="approved",
                    dependencies=["executed:abc123"],
                    order=2,
                )
                ind_plan = _write_plan(repo, "ind789", status="approved", order=3)
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "add artifacts"], cwd=repo, check=True
                )

                parser = module.build_parser()
                args = parser.parse_args(
                    ["start", "efg456", "ind789", "--prepare-only", "--repo", str(repo)]
                )
                with self.assertRaises(runner_shared.DriverError) as cm:
                    module.initialize_run(args)

                exc_msg = str(cm.exception)
                self.assertIn("[RUN-DEPENDENCY-UNSATISFIABLE]", exc_msg)
                self.assertIn("efg456 requires executed:abc123", exc_msg)
                self.assertIn("abc123 is approved and is not in this run", exc_msg)
                self.assertIn(
                    "No work started, and nothing durable was created.", exc_msg
                )

                _assert_no_durable_state(self, repo, ind_plan)


class TestPreservedBehaviorCases(unittest.TestCase):
    """E-07 (4), (5): The two preserved-behavior cases on both hosts."""

    def test_5_3a_in_run_failure_cascades_fail_depend_and_independent_item_completes(
        self,
    ):
        """5.3a: abc123, efg456, ind789 all in batch; abc123 fails, efg456 ends fail-depend, ind789 completes."""
        for host, module, launcher_attr in BOTH_HOSTS:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as td:
                repo = _init_repo(Path(td))
                _write_plan(repo, "abc123", status="approved", order=1)
                _write_plan(
                    repo,
                    "efg456",
                    status="approved",
                    dependencies=["executed:abc123"],
                    order=2,
                )
                _write_plan(repo, "ind789", status="approved", order=3)
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "add plans"], cwd=repo, check=True
                )

                def make_fake_run():
                    def fake_run(*args, **kwargs):
                        rd = args[1]
                        itm = args[2]
                        work_dir = kwargs.get("work_dir") or repo
                        if itm["id6"] == "abc123":
                            # Force abc123 host spawn to exit nonzero
                            return 1, None, str(rd / "log"), [host]
                        elif itm["id6"] == "ind789":
                            if (
                                kwargs.get("fresh_session")
                                or kwargs.get("log_suffix") == "verify"
                            ):
                                (
                                    rd
                                    / "outcomes"
                                    / f"{itm['position']:02d}-{itm['id6']}-verification.json"
                                ).write_text(
                                    json.dumps(
                                        {
                                            "verdict": "VERIFIED",
                                            "tests_run": ["pytest tests/"],
                                        }
                                    ),
                                    encoding="utf-8",
                                )
                                return 0, "vses", str(rd / "vlog"), [host]
                            wt = Path(work_dir)
                            (wt / "src").mkdir(parents=True, exist_ok=True)
                            (wt / "src" / "demo.txt").write_text(
                                "demo\n", encoding="utf-8"
                            )
                            pfile = next(
                                wt.glob(".aw/records/plans/pending/*ind789*.ipd.md")
                            )
                            txt = pfile.read_text(encoding="utf-8")
                            txt = txt.replace(
                                "Execution state: pending", "Execution state: performed"
                            )
                            txt = txt.replace("- [ ] E-01", "- [x] E-01")
                            txt = txt.replace("Result: pending", "Result: pass")
                            txt = txt.replace("- [ ] V-01", "- [x] V-01")
                            txt = txt.replace(
                                "Observed evidence:", "Observed evidence: observed pass"
                            )
                            pfile.write_text(txt, encoding="utf-8")
                            subprocess.run(
                                ["git", "add", "src/demo.txt", str(pfile)],
                                cwd=wt,
                                check=True,
                            )
                            subprocess.run(
                                ["git", "commit", "-qm", "complete ind789"],
                                cwd=wt,
                                check=True,
                            )
                            (
                                rd
                                / "outcomes"
                                / f"{itm['position']:02d}-{itm['id6']}.json"
                            ).write_text(
                                json.dumps(
                                    {
                                        "disposition": "executed",
                                        "pushed": False,
                                        "defect_report": {
                                            "state": "none-found",
                                            "findings": [],
                                        },
                                    }
                                ),
                                encoding="utf-8",
                            )
                            return 0, "ses-ind", str(rd / "log"), [host]
                        return 0, "ses", str(rd / "log"), [host]

                    return fake_run

                with (
                    support.coordinator_role(),
                    mock.patch.object(module, launcher_attr, make_fake_run()),
                    mock.patch(
                        "agent_workflows.runner_shared.run_suite_check",
                        return_value=(True, "1 passed"),
                    ),
                ):
                    module.main(
                        [
                            "start",
                            "abc123",
                            "efg456",
                            "ind789",
                            "--repo",
                            str(repo),
                            "--unattended",
                            "--validate",
                        ]
                    )

                runs = list((runner_shared.state_root(repo)).glob("run-*"))
                self.assertEqual(len(runs), 1)
                st = runner_shared.load_state(runs[0])
                statuses = {itm["id6"]: itm["status"] for itm in st["queue"]}
                self.assertIn("fail", statuses["abc123"])
                self.assertEqual(statuses["efg456"], "fail-depend")
                self.assertEqual(statuses["ind789"], "executed")

    def test_5_in_batch_proceeds_with_dependency_ordered_first(self):
        """5: `efg456` + `abc123` in batch proceeds at freeze with `abc123` ordered first."""
        for label, module, _ in BOTH_HOSTS:
            with self.subTest(host=label), tempfile.TemporaryDirectory() as td:
                repo = _init_repo(Path(td))
                _write_plan(repo, "abc123", status="approved", order=1)
                _write_plan(
                    repo,
                    "efg456",
                    status="approved",
                    dependencies=["executed:abc123"],
                    order=2,
                )
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "add plans"], cwd=repo, check=True
                )

                parser = module.build_parser()
                # Pass efg456 before abc123 in command line
                args = parser.parse_args(
                    ["start", "efg456", "abc123", "--prepare-only", "--repo", str(repo)]
                )
                run_dir = module.initialize_run(args)
                self.assertTrue(run_dir.exists())

                st = runner_shared.load_state(run_dir)
                executed_order = st.get("run_order", {}).get("executed", [])
                self.assertEqual(executed_order, ["abc123", "efg456"])


class TestPredicateBoundaryCases(unittest.TestCase):
    """E-08: The three predicate-boundary cases (a, b, c) and review-consumer relaxation."""

    def test_boundary_a_in_batch_execute_target_frozen_in_terminal_status_refuses(self):
        """(a): in-batch execute-action target frozen in terminal status (reviewed) is refused at freeze."""
        for label, module, _ in BOTH_HOSTS:
            with self.subTest(host=label), tempfile.TemporaryDirectory() as td:
                repo = _init_repo(Path(td))
                # abc123 has Status: reviewed and Readiness: go-pending-approval, so action is execute,
                # but without --full-auto initial queue status is 'reviewed' (needs_input=True)
                _write_plan(
                    repo,
                    "abc123",
                    status="reviewed",
                    readiness="go-pending-approval",
                    order=1,
                )
                _write_plan(
                    repo,
                    "efg456",
                    status="approved",
                    dependencies=["executed:abc123"],
                    order=2,
                )
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "add plans"], cwd=repo, check=True
                )

                parser = module.build_parser()
                args = parser.parse_args(
                    ["start", "abc123", "efg456", "--prepare-only", "--repo", str(repo)]
                )
                with self.assertRaises(runner_shared.DriverError) as cm:
                    module.initialize_run(args)

                exc_msg = str(cm.exception)
                self.assertIn("[RUN-DEPENDENCY-UNSATISFIABLE]", exc_msg)
                self.assertIn("efg456 requires executed:abc123", exc_msg)
                self.assertIn(
                    "is frozen in status 'reviewed' awaiting approval and will not be dispatched",
                    exc_msg,
                )

    def test_boundary_b_in_batch_execute_target_promoted_under_full_auto_admits(self):
        """(b): the same selection with --full-auto promotes target to auto-approved and admits at freeze."""
        for label, module, _ in BOTH_HOSTS:
            with self.subTest(host=label), tempfile.TemporaryDirectory() as td:
                repo = _init_repo(Path(td))
                _write_plan(
                    repo,
                    "abc123",
                    status="reviewed",
                    readiness="go-pending-approval",
                    order=1,
                )
                _write_plan(
                    repo,
                    "efg456",
                    status="approved",
                    dependencies=["executed:abc123"],
                    order=2,
                )
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "add plans"], cwd=repo, check=True
                )

                parser = module.build_parser()
                args = parser.parse_args(
                    [
                        "start",
                        "abc123",
                        "efg456",
                        "--prepare-only",
                        "--repo",
                        str(repo),
                        "--full-auto",
                    ]
                )
                run_dir = module.initialize_run(args)
                self.assertTrue(run_dir.exists())

                st = runner_shared.load_state(run_dir)
                queue = st["queue"]
                self.assertEqual(len(queue), 2)
                self.assertEqual(queue[0]["id6"], "abc123")
                self.assertEqual(queue[0]["status"], "queued")
                self.assertEqual(queue[0]["initial_status"], "auto-approved")

    def test_boundary_c_in_batch_to_review_target_under_decision_a(self):
        """(c): an in-batch to-review target of an executed: edge behaves per Decision (A).

        Decision (A) treats a review-action in-batch target as satisfiable only under --full-auto,
        refusing otherwise. Motivated by live corpus edges: 2ptgds -> executed:jdn790,
        aeq7f8 -> executed:2ptgds, and y3p3p5 -> executed:aeq7f8.
        """
        for label, module, _ in BOTH_HOSTS:
            with self.subTest(host=label), tempfile.TemporaryDirectory() as td:
                repo = _init_repo(Path(td))
                # Target abc123 is to-review (action: review)
                _write_plan(repo, "abc123", status="to-review", order=1)
                # Dependent efg456 is approved (action: execute), requiring executed:abc123
                _write_plan(
                    repo,
                    "efg456",
                    status="approved",
                    dependencies=["executed:abc123"],
                    order=2,
                )
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "add plans"], cwd=repo, check=True
                )

                parser = module.build_parser()

                # Without --full-auto -> REFUSED
                args_no_auto = parser.parse_args(
                    ["start", "abc123", "efg456", "--prepare-only", "--repo", str(repo)]
                )
                with self.assertRaises(runner_shared.DriverError) as cm:
                    module.initialize_run(args_no_auto)

                exc_msg = str(cm.exception)
                self.assertIn("[RUN-DEPENDENCY-UNSATISFIABLE]", exc_msg)
                self.assertIn("efg456 requires executed:abc123", exc_msg)
                self.assertIn(
                    "is queued for review only and this run is not --full-auto", exc_msg
                )

                # With --full-auto -> ADMITTED
                args_auto = parser.parse_args(
                    [
                        "start",
                        "abc123",
                        "efg456",
                        "--prepare-only",
                        "--repo",
                        str(repo),
                        "--full-auto",
                    ]
                )
                run_dir = module.initialize_run(args_auto)
                self.assertTrue(run_dir.exists())

    def test_review_consumer_relaxation_admitted(self):
        """Review consumer relaxation: efg456 at to-review consuming executed:abc123 with abc123 at to-review is admitted."""
        for label, module, _ in BOTH_HOSTS:
            with self.subTest(host=label), tempfile.TemporaryDirectory() as td:
                repo = _init_repo(Path(td))
                _write_plan(repo, "abc123", status="to-review", order=1)
                _write_plan(
                    repo,
                    "efg456",
                    status="to-review",
                    dependencies=["executed:abc123"],
                    order=2,
                )
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "add plans"], cwd=repo, check=True
                )

                parser = module.build_parser()
                args = parser.parse_args(
                    ["start", "abc123", "efg456", "--prepare-only", "--repo", str(repo)]
                )
                run_dir = module.initialize_run(args)
                self.assertTrue(run_dir.exists())

    def test_review_consumer_relaxation_admitted_for_state_spec_edge(self):
        """Review consumer relaxation: efg456 at to-review consuming state:spec:approved:spc001 with spc001 at to-review is admitted."""
        for label, module, _ in BOTH_HOSTS:
            with self.subTest(host=label), tempfile.TemporaryDirectory() as td:
                repo = _init_repo(Path(td))
                RecordBuilder(repo).spec(
                    id6="spc001",
                    title="Spec spc001",
                    when="2026-09-27",
                    status="to-review",
                    slug="spec",
                    history=["- 2026-09-27 to-review (tester): set status"],
                    body="## 1. Overview\nOverview of spec spc001.",
                )
                _write_plan(
                    repo,
                    "efg456",
                    status="to-review",
                    dependencies=["state:spec:approved:spc001"],
                    order=1,
                )
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "add spec and plan"], cwd=repo, check=True
                )

                parser = module.build_parser()
                args = parser.parse_args(
                    ["start", "efg456", "--prepare-only", "--repo", str(repo)]
                )
                run_dir = module.initialize_run(args)
                self.assertTrue(run_dir.exists())

    def test_execute_consumer_refuses_unsatisfied_state_spec_edge(self):
        """Execute consumer: efg456 at approved consuming state:spec:approved:spc001 with spc001 at to-review refuses."""
        for label, module, _ in BOTH_HOSTS:
            with self.subTest(host=label), tempfile.TemporaryDirectory() as td:
                repo = _init_repo(Path(td))
                RecordBuilder(repo).spec(
                    id6="spc001",
                    title="Spec spc001",
                    when="2026-09-27",
                    status="to-review",
                    slug="spec",
                    history=["- 2026-09-27 to-review (tester): set status"],
                    body="## 1. Overview\nOverview of spec spc001.",
                )
                _write_plan(
                    repo,
                    "efg456",
                    status="approved",
                    dependencies=["state:spec:approved:spc001"],
                    order=1,
                )
                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "add spec and plan"], cwd=repo, check=True
                )

                parser = module.build_parser()
                args = parser.parse_args(
                    ["start", "efg456", "--prepare-only", "--repo", str(repo)]
                )
                with self.assertRaises(runner_shared.DriverError) as cm:
                    module.initialize_run(args)
                exc_msg = str(cm.exception)
                self.assertIn("[RUN-DEPENDENCY-UNSATISFIABLE]", exc_msg)
                self.assertIn("efg456 requires state:spec:approved:spc001", exc_msg)
                self.assertIn("spc001 is to-review", exc_msg)
                self.assertIn("needs exactly 'approved'", exc_msg)


class TestFreezeRefusalColorStyling(unittest.TestCase):
    """Verify that freeze-time refusals format id6 references in bold yellow when color is active."""

    def test_unsatisfiable_dependency_refusal_styles_id6_bold_yellow_when_color_active(
        self,
    ):
        queue = [
            {
                "id6": "36sifo",
                "artifact_type": "ipd",
                "status": "approved",
                "action": "execute",
                "dependencies": ["executed:nwcf8j"],
            }
        ]
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            with self.assertRaises(runner_shared.DriverError) as cm_colored:
                runner_shared.enforce_freeze_time_refusal(
                    queue, repo=repo, host="agy", color=True
                )
            msg_colored = str(cm_colored.exception)
            self.assertIn("[RUN-DEPENDENCY-UNSATISFIABLE]", msg_colored)
            self.assertIn(
                "\033[1;33m36sifo\033[0m requires executed:\033[1;36mnwcf8j\033[0m",
                msg_colored,
            )
            self.assertIn("\033[1;36mnwcf8j\033[0m is absent", msg_colored)
            self.assertIn("ipd \033[1;33m36sifo\033[0m at", msg_colored)
            self.assertIn("then: aw agy run \033[1;33m36sifo\033[0m", msg_colored)

            with self.assertRaises(runner_shared.DriverError) as cm_plain:
                runner_shared.enforce_freeze_time_refusal(
                    queue, repo=repo, host="agy", color=False
                )
            msg_plain = str(cm_plain.exception)
            self.assertIn("36sifo requires executed:nwcf8j", msg_plain)
            self.assertIn("nwcf8j is absent", msg_plain)
            self.assertNotIn("\033[", msg_plain)

    def test_undetermined_action_styles_id6_bold_yellow_when_color_active(self):
        queue = [
            {
                "id6": "und123",
                "artifact_type": "ipd",
                "status": "draft",
                "action": "undetermined",
            }
        ]
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            with self.assertRaises(runner_shared.DriverError) as cm:
                runner_shared.enforce_freeze_time_refusal(
                    queue, repo=repo, host="oc", color=True
                )
            msg = str(cm.exception)
            self.assertIn("[RUN-UNDETERMINED-ACTION]", msg)
            self.assertIn("ipd \033[1;33mund123\033[0m", msg)
            self.assertIn("then: aw oc run \033[1;33mund123\033[0m", msg)

    def test_structure_preflight_styles_id6_bold_yellow_when_color_active(self):
        queue = [
            {
                "id6": "notfnd",
                "artifact_type": "ipd",
                "status": "approved",
                "action": "execute",
                "configured_file": "missing.ipd.md",
            }
        ]
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            with self.assertRaises(runner_shared.DriverError) as cm:
                runner_shared.enforce_freeze_time_refusal(
                    queue, repo=repo, host="oc", color=True
                )
            msg = str(cm.exception)
            self.assertIn("[RUN-STRUCTURE-PREFLIGHT]", msg)
            self.assertIn("ipd \033[1;33mnotfnd\033[0m", msg)
            self.assertIn("run aw check all \033[1;33mnotfnd\033[0m", msg)
            self.assertIn("then: aw oc run \033[1;33mnotfnd\033[0m", msg)

    def test_structure_preflight_highlights_id6_inside_s408_and_omits_duplicate_remedy(
        self,
    ):
        from agent_workflows import ipd_lint, orchestrator_readiness

        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            plan = _write_plan(repo, "orc63i", status="approved", order=1)
            fake_readiness = orchestrator_readiness.ReviewReadiness(
                applies=True,
                ready=False,
                findings=(
                    orchestrator_readiness.Finding(
                        code=orchestrator_readiness.CODE_COVERAGE_STALE,
                        subject="orc63i",
                        detail="plan changed since the check on 2026-11-13 (fingerprint mismatch); run `aw ipd coverage orc63i`",
                        remedy=orchestrator_readiness.REMEDY_COVERAGE_RECORD,
                    ),
                ),
                id6="orc63i",
                setid="demo",
            )
            raw = plan.read_text(encoding="utf-8")
            if "- Kind: child" in raw:
                raw = raw.replace("- Kind: child", "- Kind: orchestrator")
            else:
                raw = raw.replace("- Date:", "- Kind: orchestrator\n- Date:")
            plan.write_text(raw, encoding="utf-8")
            with mock.patch(
                "agent_workflows.orchestrator_readiness.review_readiness",
                return_value=fake_readiness,
            ):
                merged = ipd_lint.lint_file(plan, checkpoint="pre-execution")
            s408_diags = [d for d in merged.diagnostics if d.code == "IPD-S408"]
            self.assertEqual(len(s408_diags), 1)
            self.assertNotIn(
                "remedy: run `aw ipd coverage <id6>`", s408_diags[0].message
            )
            self.assertIn("run `aw ipd coverage orc63i`", s408_diags[0].message)

            queue = [
                {
                    "id6": "orc63i",
                    "artifact_type": "ipd",
                    "status": "approved",
                    "action": "orchestrate",
                    "configured_file": str(plan.relative_to(repo)),
                }
            ]
            with mock.patch(
                "agent_workflows.orchestrator_readiness.review_readiness",
                return_value=fake_readiness,
            ):
                with self.assertRaises(runner_shared.DriverError) as cm:
                    runner_shared.enforce_freeze_time_refusal(
                        queue, repo=repo, host="agy", color=True
                    )
            msg = str(cm.exception)
            self.assertIn("[RUN-STRUCTURE-PREFLIGHT]", msg)
            self.assertIn("ipd \033[1;33morc63i\033[0m", msg)
            self.assertIn("coverage-record-stale (\033[1;33morc63i\033[0m)", msg)
            self.assertIn("aw ipd coverage \033[1;33morc63i\033[0m", msg)
            self.assertNotIn("remedy: run `aw ipd coverage <id6>`", msg)
            self.assertIn("run aw check plans \033[1;33morc63i\033[0m", msg)
            self.assertIn("then: aw agy run \033[1;33morc63i\033[0m", msg)

    def test_initialize_run_uses_color_override_not_raw_false_default(self):
        """Regression: default args.color=False must not disable TTY color on freeze-time refusal."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            bad_content = RecordBuilder().plan(
                title="Bad plan",
                when="2026-09-27",
                status="approved",
                id6="clr001",
                text_only=True,
            )
            _write_plan(repo, "clr001", raw_content=bad_content)
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "add bad plan"], cwd=repo, check=True
            )

            parser = agy_runipd.build_parser()
            args = parser.parse_args(
                ["start", "clr001", "--prepare-only", "--repo", str(repo)]
            )
            # Mirror cli.py's --color / --no-color store_true defaults (both False when omitted).
            args.color = False
            args.no_color = False
            with mock.patch(
                "agent_workflows.runner_shared.should_color", return_value=True
            ):
                with self.assertRaises(runner_shared.DriverError) as cm:
                    agy_runipd.initialize_run(args)
            self.assertIn("ipd \033[1;33mclr001\033[0m", str(cm.exception))

    def test_review_action_accepts_external_auto_approved_dependency(self):
        """Regression: review preflight accepts an external auto-approved dependency, while execute refuses it."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            _write_plan(
                repo,
                "depaa1",
                status="auto-approved",
                order=1,
            )
            consumer_path = _write_plan(
                repo,
                "rev001",
                status="to-review",
                dependencies=["executed:depaa1"],
                order=2,
            )
            exec_consumer_path = _write_plan(
                repo,
                "exe001",
                status="approved",
                dependencies=["executed:depaa1"],
                order=3,
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "add auto-approved dep and consumers"],
                cwd=repo,
                check=True,
            )

            review_queue = [
                {
                    "id6": "rev001",
                    "artifact_type": "ipd",
                    "status": "queued",
                    "initial_status": "to-review",
                    "action": "review",
                    "dependencies": ["executed:depaa1"],
                    "configured_file": str(consumer_path.relative_to(repo)),
                }
            ]
            # Must not raise DriverError: an auto-approved prerequisite satisfies a review consumer.
            runner_shared.enforce_freeze_time_refusal(
                review_queue, repo=repo, host="agy", color=False
            )

            exec_queue = [
                {
                    "id6": "exe001",
                    "artifact_type": "ipd",
                    "status": "queued",
                    "initial_status": "approved",
                    "action": "execute",
                    "dependencies": ["executed:depaa1"],
                    "configured_file": str(exec_consumer_path.relative_to(repo)),
                }
            ]
            with self.assertRaises(runner_shared.DriverError) as cm:
                runner_shared.enforce_freeze_time_refusal(
                    exec_queue, repo=repo, host="agy", color=False
                )
            msg = str(cm.exception)
            self.assertIn("[RUN-DEPENDENCY-UNSATISFIABLE]", msg)
            self.assertIn("exe001 requires executed:depaa1", msg)
            self.assertIn("depaa1 is auto-approved and is not in this run", msg)


class TestGroupedPreflightDiagnostics(unittest.TestCase):
    """Behavioral tests for grouped IPD-M113 and collapsed IPD-S408 freeze-time preflight (IPD 55tt85 E-03, E-04)."""

    @staticmethod
    def _strip_readiness_line(path: Path) -> None:
        lines = [
            ln
            for ln in path.read_text(encoding="utf-8").splitlines()
            if not ln.startswith("- Readiness:")
        ]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def _write_orchestrator(
        repo: Path,
        id6: str,
        *,
        setid: str,
        child_ids: list[str],
        with_readiness: bool = True,
    ) -> Path:
        rows = "\n".join(
            f"| {i:02d} | {cid} | pending | .aw/records/plans/pending/20260927-{setid}-{i:02d}-{cid}-plan.ipd.md | none |"
            for i, cid in enumerate(child_ids, start=1)
        )
        e_items = "\n".join(
            f"- [ ] E-{i:02d} CONFIRM {cid} REACHED executed\n"
            "  - Depends on: none\n"
            "  - Expected outcome: done\n"
            "  - Execution state: pending"
            for i, cid in enumerate(child_ids, start=1)
        )
        v_items = "\n\n".join(
            f"- [ ] V-{i:02d} validates E-{i:02d}\n"
            "  - Required evidence: done\n"
            "  - Observed evidence:\n"
            "  - Result: pending"
            for i, _cid in enumerate(child_ids, start=1)
        )
        body = (
            f"## Goal\nOrchestrate {setid}.\n\n"
            f"## Detailed Implementation Checklist (TODO)\n{e_items}\n\n"
            f"## Child IPDs, sequence, and dependencies\n"
            f"| Order | Id | Status | Plan | Depends on |\n"
            f"|---|---|---|---|---|\n{rows}\n\n"
            "## Completion criteria (the whole Set is done only when)\n- None.\n\n"
            "## Cross-IPD validation\n- None.\n\n"
            "## Deferred / out of scope (with reason)\n- None.\n\n"
            "## Scope check\n- None.\n\n"
            "## Required tests / validation\n- None.\n\n"
            "## Open questions\n- None.\n\n"
            f"## Validation and cross-check (verify before reporting the Set complete)\n{v_items}\n\n"
            "## Approval and execution gate\n"
            "- Size assessment: standard\n"
            "- Cohesion rationale: not required"
        )
        p = Path(
            RecordBuilder(repo).plan(
                id6=id6,
                plan_role="orchestrator",
                title=f"Orchestrator {id6}",
                when="2026-09-27",
                set=setid,
                order=0,
                slug="orch",
                status="approved",
                scope_paths="none",
                item_dependencies="none",
                priority="medium",
                work_kind="feature",
                readiness="go-pending-approval" if with_readiness else None,
                approval="2026-09-27, test",
                highest_e_allocated=f"{len(child_ids):02d}",
                history=[
                    "- 2026-09-27 approved (tester): approved",
                    "- 2026-09-27 /plan-review (tester): APPROVE",
                ],
                raw_fields={"Concern": "Test.", "Scope": "Test."},
                body=body,
            )
        )
        from agent_workflows import coverage_record

        coverage_record.write(p, "pass", model="fixture", tool="test")
        return p

    def test_multi_plan_ipd_m113_grouped_including_mixed_case_status(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            p1 = _write_plan(repo, "m11301", status="approved", order=1, setid="m113s")
            p2 = _write_plan(repo, "m11302", status="approved", order=2, setid="m113s")
            p3 = _write_plan(repo, "m11303", status="approved", order=3, setid="m113s")
            for p in (p1, p2, p3):
                self._strip_readiness_line(p)
            # Queue carries mixed-case APPROVED for p2 to prove grouping normalizes (code, status.lower()).
            queue = [
                {
                    "id6": "m11301",
                    "artifact_type": "ipd",
                    "status": "queued",
                    "initial_status": "approved",
                    "action": "execute",
                    "configured_file": str(p1.relative_to(repo)),
                },
                {
                    "id6": "m11302",
                    "artifact_type": "ipd",
                    "status": "queued",
                    "initial_status": "APPROVED",
                    "action": "execute",
                    "configured_file": str(p2.relative_to(repo)),
                },
                {
                    "id6": "m11303",
                    "artifact_type": "ipd",
                    "status": "queued",
                    "initial_status": "approved",
                    "action": "execute",
                    "configured_file": str(p3.relative_to(repo)),
                },
            ]
            for host in ("oc", "agy"):
                for color in (False, True):
                    with self.subTest(host=host, color=color):
                        with self.assertRaises(runner_shared.DriverError) as cm:
                            runner_shared.enforce_freeze_time_refusal(
                                queue, repo=repo, host=host, color=color
                            )
                        msg = str(cm.exception)
                        self.assertEqual(msg.count("[RUN-STRUCTURE-PREFLIGHT]"), 1)
                        self.assertIn(
                            "3 ipd plan(s) in status approved violate IPD-M113", msg
                        )
                        if color:
                            ids_csv = "\033[1;33mm11301\033[0m, \033[1;33mm11302\033[0m, \033[1;33mm11303\033[0m"
                            ids_cmd = "\033[1;33mm11301\033[0m \033[1;33mm11302\033[0m \033[1;33mm11303\033[0m"
                        else:
                            ids_csv = "m11301, m11302, m11303"
                            ids_cmd = "m11301 m11302 m11303"
                            self.assertNotIn("\033[", msg)
                        self.assertIn(f"Plans:   {ids_csv}", msg)
                        self.assertIn(
                            f'aw set plan to-review {ids_cmd} -m "needs /plan-review before approval"',
                            msg,
                        )
                        self.assertIn(f"aw {host} review {ids_cmd}", msg)
                        self.assertNotIn("fix the issue above", msg)

    def test_single_plan_ipd_m113_emits_actionable_recovery_commands(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            p1 = _write_plan(repo, "sg1131", status="approved", order=1, setid="sg113")
            self._strip_readiness_line(p1)
            queue = [
                {
                    "id6": "sg1131",
                    "artifact_type": "ipd",
                    "status": "queued",
                    "initial_status": "approved",
                    "action": "execute",
                    "configured_file": str(p1.relative_to(repo)),
                }
            ]
            for host in ("oc", "agy"):
                for color in (False, True):
                    with self.subTest(host=host, color=color):
                        with self.assertRaises(runner_shared.DriverError) as cm:
                            runner_shared.enforce_freeze_time_refusal(
                                queue, repo=repo, host=host, color=color
                            )
                        msg = str(cm.exception)
                        self.assertEqual(msg.count("[RUN-STRUCTURE-PREFLIGHT]"), 1)
                        tok = "\033[1;33msg1131\033[0m" if color else "sg1131"
                        self.assertIn(f"ipd {tok} (", msg)
                        self.assertIn("violates IPD-M113:", msg)
                        self.assertIn(
                            f'aw set plan to-review {tok} -m "needs /plan-review before approval"',
                            msg,
                        )
                        self.assertIn(f"aw {host} review {tok}", msg)
                        self.assertNotIn("fix the issue above", msg)

    def test_orchestrator_s408_child_lint_collapses_after_children_even_when_orch_first(
        self,
    ):
        from agent_workflows import orchestrator_readiness

        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = self._write_orchestrator(
                repo,
                "orc900",
                setid="clps1",
                child_ids=["chd901", "chd902"],
                with_readiness=False,
            )
            c1 = _write_plan(repo, "chd901", status="approved", order=1, setid="clps1")
            c2 = _write_plan(repo, "chd902", status="approved", order=2, setid="clps1")
            self._strip_readiness_line(c1)
            self._strip_readiness_line(c2)
            fake_readiness = orchestrator_readiness.ReviewReadiness(
                applies=True,
                ready=False,
                findings=(
                    orchestrator_readiness.Finding(
                        code=orchestrator_readiness.CODE_CHILD_LINT,
                        subject="chd901",
                        detail="child chd901 fails author lint: IPD-M113 missing Readiness",
                        remedy=orchestrator_readiness.REMEDY_CHILD_LINT,
                    ),
                    orchestrator_readiness.Finding(
                        code=orchestrator_readiness.CODE_CHILD_LINT,
                        subject="chd902",
                        detail="child chd902 fails author lint: IPD-M113 missing Readiness",
                        remedy=orchestrator_readiness.REMEDY_CHILD_LINT,
                    ),
                ),
                id6="orc900",
                setid="clps1",
            )
            # Place orchestrator FIRST in queue to verify collapsed summary still emits AFTER child findings.
            queue = [
                {
                    "id6": "orc900",
                    "artifact_type": "ipd",
                    "status": "queued",
                    "initial_status": "approved",
                    "action": "orchestrate",
                    "configured_file": str(orch.relative_to(repo)),
                },
                {
                    "id6": "chd901",
                    "artifact_type": "ipd",
                    "status": "queued",
                    "initial_status": "approved",
                    "action": "execute",
                    "configured_file": str(c1.relative_to(repo)),
                },
                {
                    "id6": "chd902",
                    "artifact_type": "ipd",
                    "status": "queued",
                    "initial_status": "approved",
                    "action": "execute",
                    "configured_file": str(c2.relative_to(repo)),
                },
            ]
            for color in (False, True):
                with self.subTest(color=color):
                    with mock.patch(
                        "agent_workflows.orchestrator_readiness.review_readiness",
                        return_value=fake_readiness,
                    ):
                        with self.assertRaises(runner_shared.DriverError) as cm:
                            runner_shared.enforce_freeze_time_refusal(
                                queue, repo=repo, host="agy", color=color
                            )
                    msg = str(cm.exception)
                    # Exactly 2 blocks total: 1 grouped IPD-M113 + 1 collapsed IPD-S408
                    self.assertEqual(msg.count("[RUN-STRUCTURE-PREFLIGHT]"), 2)
                    m113_pos = msg.index("violate IPD-M113")
                    s408_pos = msg.index("violates IPD-S408:")
                    self.assertLess(m113_pos, s408_pos)
                    if color:
                        self.assertIn(
                            "child-lint-failing for 2 child plan(s) already reported above (\033[1;33mchd901\033[0m, \033[1;33mchd902\033[0m).",
                            msg,
                        )
                        self.assertIn(
                            "resolve the child plan findings above, then re-run: aw agy run \033[1;33morc900\033[0m",
                            msg,
                        )
                    else:
                        self.assertIn(
                            "child-lint-failing for 2 child plan(s) already reported above (chd901, chd902).",
                            msg,
                        )
                        self.assertIn(
                            "resolve the child plan findings above, then re-run: aw agy run orc900",
                            msg,
                        )

    def test_standalone_s408_preserved_for_coverage_stale_and_out_of_queue_child(self):
        from agent_workflows import orchestrator_readiness

        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = self._write_orchestrator(
                repo,
                "orc910",
                setid="stnd1",
                child_ids=["inq911", "out912"],
                with_readiness=True,
            )
            in_q = _write_plan(
                repo, "inq911", status="approved", order=1, setid="stnd1"
            )
            self._strip_readiness_line(in_q)
            fake_readiness = orchestrator_readiness.ReviewReadiness(
                applies=True,
                ready=False,
                findings=(
                    orchestrator_readiness.Finding(
                        code=orchestrator_readiness.CODE_COVERAGE_STALE,
                        subject="orc910",
                        detail="plan changed since check; run `aw ipd coverage orc910`",
                        remedy=orchestrator_readiness.REMEDY_COVERAGE_RECORD,
                    ),
                    orchestrator_readiness.Finding(
                        code=orchestrator_readiness.CODE_CHILD_LINT,
                        subject="out912",
                        detail="child out912 fails author lint: IPD-M113 missing Readiness",
                        remedy=orchestrator_readiness.REMEDY_CHILD_LINT,
                    ),
                    orchestrator_readiness.Finding(
                        code=orchestrator_readiness.CODE_CHILD_LINT,
                        subject="inq911",
                        detail="child inq911 fails author lint: IPD-M113 missing Readiness",
                        remedy=orchestrator_readiness.REMEDY_CHILD_LINT,
                    ),
                ),
                id6="orc910",
                setid="stnd1",
            )
            queue = [
                {
                    "id6": "orc910",
                    "artifact_type": "ipd",
                    "status": "queued",
                    "initial_status": "approved",
                    "action": "orchestrate",
                    "configured_file": str(orch.relative_to(repo)),
                },
                {
                    "id6": "inq911",
                    "artifact_type": "ipd",
                    "status": "queued",
                    "initial_status": "approved",
                    "action": "execute",
                    "configured_file": str(in_q.relative_to(repo)),
                },
            ]
            with mock.patch(
                "agent_workflows.orchestrator_readiness.review_readiness",
                return_value=fake_readiness,
            ):
                with self.assertRaises(runner_shared.DriverError) as cm:
                    runner_shared.enforce_freeze_time_refusal(
                        queue, repo=repo, host="oc", color=False
                    )
            msg = str(cm.exception)
            # 4 blocks: standalone coverage-record-stale, standalone out912 child-lint-failing,
            # single inq911 IPD-M113, and collapsed IPD-S408 summary for inq911 last.
            self.assertEqual(msg.count("[RUN-STRUCTURE-PREFLIGHT]"), 4)
            self.assertIn("coverage-record-stale (orc910):", msg)
            self.assertIn("child-lint-failing (out912):", msg)
            self.assertIn(
                "child-lint-failing for 1 child plan(s) already reported above (inq911).",
                msg,
            )
            self.assertLess(
                msg.index("violates IPD-M113:"),
                msg.index("already reported above (inq911)"),
            )

    def test_other_identical_ipd_diagnostics_group_across_multiple_plans(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            p1 = _write_plan(repo, "grp801", status="approved", order=1, setid="grpd1")
            p2 = _write_plan(repo, "grp802", status="approved", order=2, setid="grpd1")
            for p in (p1, p2):
                p.write_text(
                    p.read_text(encoding="utf-8").replace(
                        "- Priority: medium\n", "", 1
                    ),
                    encoding="utf-8",
                )
            queue = [
                {
                    "id6": "grp801",
                    "artifact_type": "ipd",
                    "status": "queued",
                    "initial_status": "approved",
                    "action": "execute",
                    "configured_file": str(p1.relative_to(repo)),
                },
                {
                    "id6": "grp802",
                    "artifact_type": "ipd",
                    "status": "queued",
                    "initial_status": "approved",
                    "action": "execute",
                    "configured_file": str(p2.relative_to(repo)),
                },
            ]
            with self.assertRaises(runner_shared.DriverError) as cm:
                runner_shared.enforce_freeze_time_refusal(
                    queue, repo=repo, host="oc", color=False
                )
            msg = str(cm.exception)
            self.assertEqual(msg.count("[RUN-STRUCTURE-PREFLIGHT]"), 1)
            self.assertIn("2 ipd plan(s) in status approved violate IPD-M110:", msg)
            self.assertIn("Plans:   grp801, grp802", msg)
            self.assertIn(
                "fix the issue above, run aw check plans grp801 grp802, then: aw oc run grp801 grp802",
                msg,
            )


if __name__ == "__main__":
    unittest.main()
