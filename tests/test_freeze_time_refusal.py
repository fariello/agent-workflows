"""Tests for freeze-time whole-run refusal gate (spec z7nbn1 1.3, 1.4, 1.7; plan jdn790).

Validates:
E-07 / V-07: The three refusal classes (5.1 undetermined, 5.2 malformed, 5.3 unsatisfiable dep)
             and the two preserved-behavior cases (5.3a failure cascade and in-batch proceed).
E-08 / V-08: The three predicate-boundary cases (a, b, c) and review-consumer relaxation.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests import support

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
    pending = repo / ".aw" / "records" / "plans" / "pending"
    plan_path = pending / f"20260927-{setid}-{order:02d}-{id6}-plan.ipd.md"
    if raw_content is not None:
        plan_path.write_text(raw_content, encoding="utf-8")
        return plan_path

    deps_line = (
        f"- Item-Dependencies: {', '.join(dependencies)}\n" if dependencies else ""
    )
    # rdyreq (`fhinri`, IPD-M113): a reviewed/ready-to-execute plan must carry `- Readiness:`, so a
    # gated status defaults to the review output, attested by a /plan-review history line (IPD-M107).
    gated = status in ("reviewed", "approved", "auto-approved")
    if readiness is None and gated:
        readiness = "go-pending-approval"
    readiness_line = f"- Readiness: {readiness}\n" if readiness else ""
    review_line = "- 2026-09-27 /plan-review (tester): APPROVE\n" if gated else ""
    if approval is None:
        approval_line = "- Approval: 2026-09-27, test\n" if status == "approved" else ""
    else:
        approval_line = f"- Approval: {approval}\n" if approval else ""

    text = f"""# IPD: Plan {id6}

- Date: 2026-09-27
- Kind: child
- Concern: test
- Scope: test
- Scope-Paths: README.md, src/demo.txt
- Status: {status}
{readiness_line}- Set: {setid}
- Order: {order}
- Highest E allocated: 01
- Author: tester
- Priority: medium
- Work-Kind: feature
- Id: {id6}
{deps_line}{approval_line}
## Workflow history
- 2026-09-27 {status} (tester): {status if status != "reviewed" else "APPROVE"}
{review_line}
## Goal
Goal for {id6}.

## Detailed Implementation Checklist (TODO)
### Task group 1: work
- [ ] E-01 Step 1
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending

## Project conventions discovered (Step 0)
None.

## Findings
None.

## Proposed changes (ordered, validatable)
None.

## Deferred / out of scope (with reason)
None.

## Scope check
None.

## Required tests / validation
None.

## Spec / documentation sync
None.

## Open questions
None.

## Validation and cross-check (verify before reporting done)
- [ ] V-01 validates E-01
  - Required evidence: done
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- Size assessment: standard
- Cohesion rationale: not required
"""
    plan_path.write_text(text, encoding="utf-8")
    return plan_path


def _write_spec(
    repo: Path,
    id6: str,
    *,
    status: str = "implementing",
    malformed: bool = False,
) -> Path:
    target_dir = repo / ".aw" / "records" / "specs" / status
    target_dir.mkdir(parents=True, exist_ok=True)
    spec_path = target_dir / f"20260927-{id6}-01-{id6}-spec.spec.md"
    if malformed:
        text = f"""# SPEC: Malformed spec {id6}

- Date: 2026-09-27
- Status: {status}
- Id: {id6}
"""
    else:
        text = f"""# SPEC: Spec {id6}

- Date: 2026-09-27
- Status: {status}
- Title: Spec {id6}
- Slug: spec-{id6}
- Id: {id6}

## Workflow history
- 2026-09-27 {status} (tester): set status

## 1. Overview
Overview of spec {id6}.
"""
    spec_path.write_text(text, encoding="utf-8")
    return spec_path


def _write_backlog(
    repo: Path,
    id6: str,
    *,
    status: str = "open",
    malformed: bool = False,
) -> Path:
    target_dir = repo / ".aw" / "records" / "backlog" / status
    target_dir.mkdir(parents=True, exist_ok=True)
    item_path = target_dir / f"20260927-demo-01-{id6}-item.backlog.md"
    if malformed:
        text = f"""- Id: {id6}
- Status: {status}
"""
    else:
        text = f"""- Id: {id6}
- Status: {status}
- Set: demo
- Priority: medium
- Work-Kind: feature
- Summary: Summary for {id6}

## Workflow history
- 2026-09-27 {status} (tester): created
"""
    item_path.write_text(text, encoding="utf-8")
    return item_path


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
                _write_spec(repo, "spc001", status="implementing")
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
                bad_content = "# IPD: Bad plan\n\n- Date: 2026-09-27\n- Status: approved\n- Id: bad001\n"
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
                _write_spec(repo, "badspc", status="draft", malformed=True)
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
                _write_backlog(repo, "badbkg", status="open", malformed=True)
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
                _write_spec(repo, "spc001", status="to-review")
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
                _write_spec(repo, "spc001", status="to-review")
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


if __name__ == "__main__":
    unittest.main()
