"""Tests for runner action derivation parity with run_selection_policy action table.

Covers artdispatch 7icz68 E-09 and E-10 (spec z7nbn1 1.2, 2.2, 5.6).
BEHAVIORAL ONLY: no inspect.getsource, no read_text of files under agent_workflows/, no AST.
Reading the run's own state.json is the required mechanism.
"""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


from agent_workflows import (
    agy_runipd,
    oc_runipd,
    run_selection_policy,
    runner_shared,
    runner_stop,
)

_HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))


def _make_test_repo(path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=path, check=True)
    return path


def _write_plan(
    repo: Path,
    *,
    id6: str,
    setid: str,
    order: int,
    status: str,
    kind: str | None = None,
    incomplete: bool = False,
    dependencies: list[str] | None = None,
) -> Path:
    bucket = "pending"
    if status in ("executed", "superseded", "not-executed", "reusable"):
        bucket = status
    dir_path = repo / ".aw" / "records" / "plans" / bucket
    dir_path.mkdir(parents=True, exist_ok=True)
    if kind == "orchestrator":
        order = 0
    file_path = dir_path / f"20260927-{setid}-{order:02d}-{id6}-test.ipd.md"

    lines = [
        f"# IPD: Test {id6}",
        "",
        "- Date: 2026-09-27",
        f"- Id: {id6}",
        f"- Set: {setid}",
        f"- Order: {order}",
        f"- Status: {status}",
    ]
    if kind:
        lines.append(f"- Kind: {kind}")
    lines.append("- Concern: Test concern for parity tests.")
    lines.append("- Scope: Parity test scope.")
    lines.append("- Scope-Paths: none")
    lines.append("- Priority: medium")
    if incomplete:
        lines.append("- Work-Kind: unresolved")
    else:
        lines.append("- Work-Kind: feature")
    lines.append("- Author: test")
    lines.append("- Highest E allocated: 01")
    if status == "approved":
        lines.append("- Approval: 2026-09-27, test approved")
    if dependencies:
        lines.append(f"- Item-Dependencies: {', '.join(dependencies)}")
    else:
        lines.append("- Item-Dependencies: none")
    lines.append("")
    lines.append("## Workflow history")
    lines.append("")
    lines.append(f"- 2026-09-27 {status} (test): created.")
    lines.append("")
    lines.append("## Goal")
    lines.append("")
    lines.append("A synthetic plan for parity tests.")
    lines.append("")
    lines.append("## Detailed Implementation Checklist (TODO)")
    lines.append("")
    if kind == "orchestrator":
        c_ord = 9 if setid == "parset" else 1
        c_id = f"p{c_ord:03d}cc" if setid == "parset" else "chld01"
        lines.extend(
            [
                f"- [ ] E-01 CONFIRM {c_id} REACHED executed",
                "  - Depends on: none",
                "  - Expected outcome: done",
                "  - Execution state: pending",
                "",
                "## Child IPDs, sequence, and dependencies",
                "",
                "| Order | Id | Status | Plan | Depends on |",
                "|---|---|---|---|---|",
                f"| {c_ord:02d} | {c_id} | pending | .aw/records/plans/pending/20260927-{setid}-{c_ord:02d}-{c_id}-test.ipd.md | none |",
                "",
                "## Completion criteria (the whole Set is done only when)",
                "",
                "- None.",
                "",
                "## Cross-IPD validation",
                "",
                "- None.",
            ]
        )
    else:
        lines.extend(
            [
                "- [ ] E-01 Test item.",
                "  - Depends on: none",
                "  - Expected outcome: done",
                "  - Execution state: pending",
                "",
                "## Project conventions discovered (Step 0)",
                "",
                "- None.",
                "",
                "## Findings",
                "",
                "- None.",
                "",
                "## Proposed changes (ordered, validatable)",
                "",
                "- None.",
            ]
        )
    lines.extend(
        [
            "",
            "## Deferred / out of scope (with reason)",
            "",
            "- None.",
            "",
            "## Scope check",
            "",
            "- None.",
            "",
            "## Required tests / validation",
            "",
            "- None.",
        ]
    )
    if kind != "orchestrator":
        lines.extend(
            [
                "",
                "## Spec / documentation sync",
                "",
                "- None.",
            ]
        )
    val_header = (
        "## Validation and cross-check (verify before reporting the Set complete)"
        if kind == "orchestrator"
        else "## Validation and cross-check (verify before reporting done)"
    )
    lines.extend(
        [
            "",
            "## Open questions",
            "",
            "- None.",
            "",
            val_header,
            "",
            "- [ ] V-01 validates E-01",
            "  - Required evidence: check.",
            "  - Observed evidence:",
            "  - Result: pending",
            "",
            "## Approval and execution gate",
            "",
            "- None.",
            "",
        ]
    )
    file_path.write_text("\n".join(lines), encoding="utf-8")
    if kind == "orchestrator":
        from agent_workflows import coverage_record

        coverage_record.write(file_path, "pass", model="fixture", tool="test")
    return file_path


_run_counter = 0


def _build_queue_for_selector(
    module,
    repo: Path,
    selector: str,
    *,
    action: str | None = None,
    with_dependencies: bool = False,
    allow_drafts: bool = False,
) -> dict:
    global _run_counter
    _run_counter += 1
    cmd = [
        "start",
        selector,
        "--repo",
        str(repo),
        "--prepare-only",
        "--run-id",
        f"run-test-{_run_counter:06d}",
    ]
    if action:
        cmd.extend(["--action", action])
    if with_dependencies:
        cmd.append("--with-dependencies")
    if allow_drafts:
        cmd.append("--allow-drafts")
    args = module.build_parser().parse_args(cmd)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        run_dir = module.initialize_run(args)
    state_file = Path(run_dir) / "state.json"
    data = json.loads(state_file.read_text(encoding="utf-8"))
    data["run_dir"] = str(run_dir)
    return data


class TestActionTableRunnerParity(unittest.TestCase):
    """Behavioral equality tests proving runner action derivation equals the action table."""

    def test_executed_maps_to_skip_on_both_hosts(self):
        """Spec z7nbn1 5.6: A queue built over an executed plan carries action: skip on both hosts."""
        for label, mod in _HOSTS:
            with self.subTest(host=label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_plan(
                        repo,
                        id6="exe001",
                        setid="s1",
                        order=1,
                        status="executed",
                        kind="child",
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "init"], cwd=repo, check=True
                    )

                    state = _build_queue_for_selector(mod, repo, "exe001")
                    entry = next(it for it in state["queue"] if it["id6"] == "exe001")
                    self.assertEqual(entry["action"], "skip")
                    self.assertEqual(entry["status"], "executed")

    def test_parity_matrix_across_all_statuses_and_kinds(self):
        """For each (status, kind) combination, runner derived action matches runner_action and table."""
        statuses = [
            ("draft", True),  # complete draft
            ("draft", False),  # incomplete draft
            ("to-review", True),
            ("reviewed", True),
            ("approved", True),
            ("auto-approved", True),
            ("reusable", True),
            ("executed", True),
        ]
        kinds = ["child", "orchestrator"]

        for label, mod in _HOSTS:
            with tempfile.TemporaryDirectory() as td:
                repo = _make_test_repo(Path(td))
                plan_meta = {}
                order = 0
                for st, complete in statuses:
                    for k in kinds:
                        order += 1
                        suffix = "c" if complete else "i"
                        k_sfx = (
                            "k"
                            if k == "orchestrator"
                            else ("c" if k == "child" else "n")
                        )
                        id6 = f"p{order:03d}{k_sfx}{suffix}"[:6]
                        _write_plan(
                            repo,
                            id6=id6,
                            setid="parset",
                            order=order,
                            status=st,
                            kind=k,
                            incomplete=not complete,
                        )
                        plan_meta[id6] = (st, k, complete)

                subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)

                state = _build_queue_for_selector(
                    mod, repo, "parset", allow_drafts=True
                )
                queue_by_id = {it["id6"]: it for it in state["queue"]}

                for id6, (st, k, complete) in plan_meta.items():
                    with self.subTest(
                        host=label, id6=id6, status=st, kind=k, complete=complete
                    ):
                        entry = queue_by_id[id6]
                        derived_action = entry["action"]

                        expected = run_selection_policy.runner_action(
                            "ipd",
                            st,
                            kind=k,
                            authoring_complete=complete,
                        )
                        self.assertEqual(
                            derived_action,
                            expected,
                            f"Derived action {derived_action!r} != runner_action {expected!r} for ({st}, {k})",
                        )

                        table_action = run_selection_policy.action_for_status("ipd", st)
                        if table_action != run_selection_policy.ACTION_UNDETERMINED:
                            expected_table = (
                                "orchestrate"
                                if k == "orchestrator" and table_action == "execute"
                                else table_action
                            )
                            self.assertEqual(
                                derived_action,
                                expected_table,
                                f"Derived action {derived_action!r} != table {expected_table!r} for ({st}, {k})",
                            )

    def test_retired_statuses_parity_direct(self):
        """Retired plans (superseded, not-executed) are refused by expand_selectors at queue-build time;

        their status-to-action derivation matches the table (skip) on both runner_action and action_for.
        """
        for st in ("superseded", "not-executed"):
            for k in ("child", "orchestrator", None):
                with self.subTest(status=st, kind=k):
                    act_runner = run_selection_policy.runner_action("ipd", st, kind=k)
                    act_table = run_selection_policy.action_for_status("ipd", st)
                    act_shared = runner_shared.action_for(k, st)
                    self.assertEqual(act_runner, "skip")
                    self.assertEqual(act_table, "skip")
                    self.assertEqual(act_shared, "skip")

    def test_four_draft_cases_agreement(self):
        """Four draft cases (complete/incomplete x named/swept) show runner_action and needs_review agree."""
        # 1. Complete draft named
        self.assertEqual(
            run_selection_policy.runner_action("ipd", "draft", authoring_complete=True),
            "review",
        )
        self.assertTrue(
            run_selection_policy.needs_review("ipd", "draft", authoring_complete=True)
        )

        # 2. Complete draft swept
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _write_plan(
                repo,
                id6="dcom01",
                setid="swp",
                order=1,
                status="draft",
                kind="child",
                incomplete=False,
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)
            state = _build_queue_for_selector(
                oc_runipd, repo, "reviews", allow_drafts=True
            )
            ids = [it["id6"] for it in state["queue"]]
            self.assertIn("dcom01", ids)

        # 3. Incomplete draft named
        self.assertEqual(
            run_selection_policy.runner_action(
                "ipd", "draft", authoring_complete=False
            ),
            "skip",
        )
        self.assertFalse(
            run_selection_policy.needs_review("ipd", "draft", authoring_complete=False)
        )

        # 4. Incomplete draft swept
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _write_plan(
                repo,
                id6="dinc01",
                setid="swp",
                order=1,
                status="draft",
                kind="child",
                incomplete=True,
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)
            with self.assertRaises(oc_runipd.DriverError):
                # EmptyStatusSelection raised because incomplete draft is excluded by review sweep
                _build_queue_for_selector(oc_runipd, repo, "reviews", allow_drafts=True)

    def test_execute_item_core_guard_raises_on_skip_action(self):
        """E-06: execute_item_core raises DriverError if handed an action outside review/execute;

        spawn is patched to fail if called, proving no agent turn is launched.
        """
        item = {
            "id6": "skp001",
            "action": "skip",
            "status": "queued",
            "configured_file": "",
        }
        state = {"repo": "."}

        def mock_spawn(*args, **kwargs):
            self.fail("Spawn must not be called for an item with action skip")

        with self.assertRaises(runner_shared.DriverError) as ctx:
            runner_shared.execute_item_core(
                Path("."),
                state,
                item,
                recovery=False,
                host_labels=runner_shared.OC_HOST_LABELS,
                spawn_executor=mock_spawn,
                spawn_verifier=mock_spawn,
                raw_launcher=mock_spawn,
                run_suite_check=lambda p, s: None,
                process_backlog_close=lambda *a, **k: None,
            )
        self.assertIn("Cannot execute item skp001", str(ctx.exception))
        self.assertIn("invalid action 'skip'", str(ctx.exception))


class TestConsumerCases(unittest.TestCase):
    """Four consumer cases identified during review (artdispatch 7icz68 E-10)."""

    def test_consumer_exit_code(self):
        """(a) EXIT CODE: A run whose only non-success entry is a skip exits 0;

        a run with a genuinely failed execute item still exits nonzero.
        """
        skip_queue = [{"action": "skip", "status": "not-run"}]
        exit_code_skip = runner_stop.deliberate_stop_exit_code(
            runner_shared.exit_code_statuses(skip_queue),
            success_states={runner_shared.EXIT_SUCCESS_TOKEN},
            stopped=False,
        )
        self.assertEqual(exit_code_skip, 0)

        # Control case: execute action with failed status
        failed_queue = [{"action": "execute", "status": "failed"}]
        exit_code_failed = runner_stop.deliberate_stop_exit_code(
            runner_shared.exit_code_statuses(failed_queue),
            success_states={runner_shared.EXIT_SUCCESS_TOKEN},
            stopped=False,
        )
        self.assertNotEqual(exit_code_failed, 0)

        # Control case: execute action with substantially-complete
        sub_queue = [{"action": "execute", "status": "substantially-complete"}]
        exit_code_sub = runner_stop.deliberate_stop_exit_code(
            runner_shared.exit_code_statuses(sub_queue),
            success_states={runner_shared.EXIT_SUCCESS_TOKEN},
            stopped=False,
        )
        self.assertNotEqual(exit_code_sub, 0)

    def test_consumer_retry_incomplete_requeue_exclusion(self):
        """(b) REQUEUE: --retry-incomplete excludes a skip entry from requeue;

        verified with host spawn patched to fail if called, and control case confirmed requeued.
        """
        for label, mod in _HOSTS:
            with self.subTest(host=label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    # An incomplete draft queued with action: skip, status: not-run
                    _write_plan(
                        repo,
                        id6="skp001",
                        setid="s1",
                        order=1,
                        status="draft",
                        kind="child",
                        incomplete=True,
                    )
                    # A failed execute plan
                    _write_plan(
                        repo,
                        id6="fld001",
                        setid="s1",
                        order=2,
                        status="approved",
                        kind="child",
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "init"], cwd=repo, check=True
                    )

                    state = _build_queue_for_selector(mod, repo, "s1")
                    # Modify second item to failed
                    for it in state["queue"]:
                        if it["id6"] == "fld001":
                            it["status"] = "failed"
                    run_dir = Path(state["run_dir"])
                    (run_dir / "state.json").write_text(
                        json.dumps(state), encoding="utf-8"
                    )

                    dispatched = []

                    def fake_execute(run_dir, state, item, *args, **kwargs):
                        dispatched.append((item["id6"], kwargs.get("recovery")))
                        # Stop execution upon dispatching first runnable item
                        raise runner_shared.ToolIdentityError("stop dispatch")

                    with mock.patch.object(
                        mod, "execute_item", side_effect=fake_execute
                    ), contextlib.suppress(runner_shared.ToolIdentityError):
                        with mod.locked_run(run_dir):
                            mod.run_queue(run_dir, retry_incomplete=True)

                    updated_state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    skp_entry = next(
                        it for it in updated_state["queue"] if it["id6"] == "skp001"
                    )
                    fld_entry = next(
                        it for it in updated_state["queue"] if it["id6"] == "fld001"
                    )

                    # The requeue exclusion stop fired: skip entry remained not-run, not requeued
                    self.assertEqual(skp_entry["status"], "not-run")
                    self.assertNotIn("requeue_from_status", skp_entry)
                    self.assertNotIn("skp001", [d[0] for d in dispatched])

                    # Control case: failed entry was requeued and dispatched for recovery
                    self.assertEqual(fld_entry["status"], "queued")
                    self.assertEqual(fld_entry.get("requeue_from_status"), "failed")
                    self.assertEqual(dispatched, [("fld001", True)])

    def test_consumer_action_legality_on_incomplete_draft(self):
        """(c) --action LEGALITY: aw oc review on a named incomplete draft starts (no DriverError),

        its queue entry carries action: skip with 0 attempts, and a mixed sweep containing one
        incomplete draft is not refused.
        """
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _write_plan(
                repo,
                id6="drf001",
                setid="s1",
                order=1,
                status="draft",
                kind="child",
                incomplete=True,
            )
            _write_plan(
                repo,
                id6="com001",
                setid="s1",
                order=2,
                status="draft",
                kind="child",
                incomplete=False,
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)

            # Named incomplete draft with --action review starts cleanly
            state = _build_queue_for_selector(
                oc_runipd, repo, "drf001", action="review"
            )
            entry = state["queue"][0]
            self.assertEqual(entry["action"], "skip")
            self.assertEqual(entry["status"], "not-run")
            self.assertEqual(len(entry.get("attempts", [])), 0)

            # Mixed sweep with reviews selector admits complete draft without refusal
            state_sweep = _build_queue_for_selector(
                oc_runipd, repo, "reviews", action="review", allow_drafts=True
            )
            queued_ids = [it["id6"] for it in state_sweep["queue"]]
            self.assertEqual(queued_ids, ["com001"])

    def test_consumer_reviewed_orchestrator_order_sensitivity(self):
        """(d) The order-sensitive reviewed+orchestrator row derives orchestrate from real queue build."""
        for label, mod in _HOSTS:
            with self.subTest(host=label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_plan(
                        repo,
                        id6="revo01",
                        setid="s1",
                        order=0,
                        status="reviewed",
                        kind="orchestrator",
                    )
                    _write_plan(
                        repo,
                        id6="chd001",
                        setid="s1",
                        order=1,
                        status="approved",
                        kind="child",
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "init"], cwd=repo, check=True
                    )

                    state = _build_queue_for_selector(mod, repo, "s1")
                    revo_entry = next(
                        it for it in state["queue"] if it["id6"] == "revo01"
                    )
                    self.assertEqual(revo_entry["action"], "orchestrate")
                    self.assertEqual(revo_entry["status"], "reviewed")
                    self.assertTrue(revo_entry.get("needs_input"))
