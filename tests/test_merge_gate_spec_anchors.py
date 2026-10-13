#!/usr/bin/env python3
"""Tests for merge-time spec line-anchor citation gate (IPD mnwkqu, Set cihealth).

Validates E-01 through E-05 and V-01 through V-05:
- (a) the lane edits the spec so an existing pointer goes stale: held, correction turn issued with the pointer named;
- (b) the scripted agent then fixes the pointer: merged;
- (c) the lane adds a new stale pointer: held;
- (d) a stale pointer already on the base: merged, not held;
- (e) a lane that only moves lines in a non-spec file: merged;
- (f) the detector raises: merged with a spec-anchor-check-unknown event;
- (g) the budget is exhausted (budget 0, or the scripted agent never fixes it): item ends fail-merge with cause spec-anchor-new-stale, and main did not advance;
- (h) a direct call of new_stale_anchors on a lane that changed no spec and no scanned .py returns none without scanning.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared, spec_citations
from tests import support
from tests.test_oc_runipd import _CONFORMING_PLAN

BOTH = ("oc_runipd", "agy_runipd")
_MODULES = {
    "oc_runipd": oc_runipd,
    "agy_runipd": agy_runipd,
    "runner_shared": runner_shared,
}

_SPEC_CONTENT = """\
# Test Spec
- Id: demo01
- Status: approved

## 1. Introduction

Line 7 content for intro.

## 2. Details

Line 11 content for details.
"""


class MergeGateSpecAnchorsTests(unittest.TestCase):
    """Integration and unit tests for the merge-time spec anchor citation gate."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _setup_fixture(
        self, td: str, id6: str = "spc001", retry_budget: int = 2
    ) -> tuple[pathlib.Path, pathlib.Path, dict, dict]:
        repo = pathlib.Path(td) / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=repo,
            check=True,
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True
        )
        (repo / ".gitignore").write_text(
            ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
        )
        (repo / "base.txt").write_text("base\n", encoding="utf-8")

        # Create a spec in .aw/records/specs/approved/
        specs_dir = repo / ".aw" / "records" / "specs" / "approved"
        specs_dir.mkdir(parents=True, exist_ok=True)
        spec_path = specs_dir / "20260101-demo01-01-demo01-test.spec.md"
        spec_path.write_text(_SPEC_CONTENT, encoding="utf-8")

        # Create a python file citing line 7 of demo01 under agent_workflows/
        src_dir = repo / "agent_workflows"
        src_dir.mkdir(parents=True, exist_ok=True)
        foo_path = src_dir / "foo.py"
        foo_path.write_text(
            "# spec demo01 Section 1 :7\ndef foo():\n    pass\n",
            encoding="utf-8",
        )

        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True, exist_ok=True)
        plan_text = _CONFORMING_PLAN.format(id6=id6)
        plan_text = plan_text.replace(
            "Scope-Paths: src/",
            "Scope-Paths: agent_workflows/foo.py, agent_workflows/bar.py, "
            "agent_workflows/stale_base.py, "
            ".aw/records/specs/approved/20260101-demo01-01-demo01-test.spec.md",
        )
        plan = pending / f"20260828-demo-01-{id6}-demo.ipd.md"
        plan.write_text(plan_text, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        (run_dir / "sessions").mkdir(parents=True, exist_ok=True)

        item = {
            "position": 1,
            "id6": id6,
            "setid": "cihealth",
            "set": "cihealth",
            "action": "execute",
            "status": "pending",
            "plan_path": str(plan),
            "attempts": [],
        }
        state = {
            "run_id": "run-test",
            "repo": str(repo),
            "options": {
                "opencode": "/bin/true",
                "agy": "/bin/true",
                "model": "opus",
                "self_finalize": True,
                "isolate_worktree": True,
                "no_audit": True,
                "no_verify": True,
                "retry_budget": retry_budget,
            },
            "queue": [item],
        }
        return repo, run_dir, state, item

    def _passing_suite(self, repo: pathlib.Path) -> runner_shared.SuiteCheckResult:
        return runner_shared.SuiteCheckResult(
            passing=True,
            reason="ok",
            exit_code=0,
            summary="ok",
            cwd=str(repo),
            timeout_seconds=60.0,
            elapsed_seconds=0.1,
        )

    def test_case_a_and_b_lane_edits_spec_held_then_fixed_and_merged(self) -> None:
        """(a) Lane edits spec so existing pointer goes stale: held, correction issued.
        (b) Scripted agent fixes pointer: merged, main advances.
        """
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_fixture(td, retry_budget=2)
                initial_main = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()

                ask_count = 0
                prompts_delivered: list[str] = []

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    nonlocal ask_count
                    work_dir = kwargs.get("work_dir")
                    target_dir = pathlib.Path(work_dir)
                    log_suffix = kwargs.get("log_suffix", "")

                    if log_suffix == "spec-anchor":
                        ask_count += 1
                        prompt_path = None
                        if runner == "oc_runipd" and len(args) >= 2:
                            prompt_path = args[1]
                        elif runner == "agy_runipd" and len(args) >= 1:
                            prompt_path = args[0]
                        if prompt_path and pathlib.Path(prompt_path).is_file():
                            prompts_delivered.append(
                                pathlib.Path(prompt_path).read_text(encoding="utf-8")
                            )

                        # Fix turn: change citation to section heading instead of bare line number
                        foo_p = target_dir / "agent_workflows" / "foo.py"
                        foo_p.write_text(
                            "# spec demo01 Section 1\ndef foo():\n    pass\n",
                            encoding="utf-8",
                        )
                        subprocess.run(
                            ["git", "add", "agent_workflows/foo.py"],
                            cwd=target_dir,
                            check=True,
                        )
                        subprocess.run(
                            ["git", "commit", "-qm", "fix: cite by section heading"],
                            cwd=target_dir,
                            check=True,
                        )
                        return 0, "ses1", str(rd / "spec-anchor-log"), [runner]

                    # Initial execution turn: edit spec to shift line numbers
                    spec_p = (
                        target_dir
                        / ".aw"
                        / "records"
                        / "specs"
                        / "approved"
                        / "20260101-demo01-01-demo01-test.spec.md"
                    )
                    shifted = (
                        "# Test Spec\n\n# Extra line 1\n# Extra line 2\n# Extra line 3\n# Extra line 4\n# Extra line 5\n"
                        + _SPEC_CONTENT[len("# Test Spec\n") :]
                    )
                    spec_p.write_text(shifted, encoding="utf-8")
                    subprocess.run(
                        ["git", "add", str(spec_p)],
                        cwd=target_dir,
                        check=True,
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", "edit spec shifting lines"],
                        cwd=target_dir,
                        check=True,
                    )

                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
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
                    return 0, "ses1", str(rd / "log"), [runner]

                driver_mod = _MODULES[runner]
                launcher_target = (
                    "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
                )
                with mock.patch.object(
                    driver_mod, launcher_target, fake_launcher
                ), mock.patch.object(
                    driver_mod,
                    "run_suite_check",
                    lambda *a, **k: self._passing_suite(repo),
                ):
                    driver_mod.execute_item(run_dir, state, item, recovery=False)

                # Verification:
                # (a) lane was held, send-back was triggered
                self.assertEqual(ask_count, 1, "Expected exactly 1 fix-it turn")
                self.assertEqual(item.get(runner_shared.SPEC_ANCHOR_RETRY_COUNT_KEY), 1)
                self.assertTrue(len(prompts_delivered) >= 1)
                delivered_prompt = prompts_delivered[0]
                self.assertIn("agent_workflows/foo.py:1", delivered_prompt)
                self.assertIn("demo01", delivered_prompt)
                self.assertIn(
                    "cite by section heading or quoted string", delivered_prompt
                )

                # Check spec-anchor-sent-back event
                events_file = run_dir / "events.jsonl"
                self.assertTrue(events_file.exists())
                events = [
                    json.loads(line)
                    for line in events_file.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                sent_back_events = [
                    e for e in events if e.get("event") == "spec-anchor-sent-back"
                ]
                self.assertEqual(len(sent_back_events), 1)
                self.assertEqual(sent_back_events[0]["id6"], item["id6"])

                # (b) after agent fixed pointer, item merged and executed
                self.assertEqual(item["status"], "executed")
                final_main = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
                self.assertNotEqual(
                    initial_main, final_main, "Main must advance after fix and merge"
                )

    def test_case_c_lane_adds_new_stale_pointer_held(self) -> None:
        """(c) The lane adds a new stale pointer: held."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_fixture(td, retry_budget=0)
                initial_main = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    work_dir = kwargs.get("work_dir")
                    target_dir = pathlib.Path(work_dir)
                    bar_p = target_dir / "agent_workflows" / "bar.py"
                    bar_p.write_text(
                        "# spec demo01 Section 2 :7\ndef bar():\n    pass\n",
                        encoding="utf-8",
                    )
                    subprocess.run(
                        ["git", "add", "agent_workflows/bar.py"],
                        cwd=target_dir,
                        check=True,
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", "add new stale pointer"],
                        cwd=target_dir,
                        check=True,
                    )
                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
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
                    return 0, "ses1", str(rd / "log"), [runner]

                driver_mod = _MODULES[runner]
                launcher_target = (
                    "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
                )
                with mock.patch.object(
                    driver_mod, launcher_target, fake_launcher
                ), mock.patch.object(
                    driver_mod,
                    "run_suite_check",
                    lambda *a, **k: self._passing_suite(repo),
                ):
                    driver_mod.execute_item(run_dir, state, item, recovery=False)

                # Held: status must be fail-merge, cause spec-anchor-new-stale, main unmoved
                self.assertEqual(
                    item["status"],
                    "fail-merge",
                    "Lane with new stale pointer must be held (fail-merge on budget 0)",
                )
                ladder = item.get("integration_ladder") or {}
                self.assertEqual(
                    ladder.get("cause"),
                    runner_shared.INTEGRATION_CAUSE_SPEC_ANCHOR_NEW_STALE,
                    "Ladder cause must be spec-anchor-new-stale",
                )
                deferral_reason = item.get("integration_deferral") or ""
                self.assertIn(
                    "lane introduced 1 new stale spec line-anchor citation(s)",
                    deferral_reason,
                )
                final_main = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
                self.assertEqual(
                    initial_main, final_main, "Main must NOT advance when held"
                )

    def test_case_d_stale_pointer_already_on_base_merged(self) -> None:
        """(d) A stale pointer already on the base: merged, not held."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_fixture(td, retry_budget=0)

                # Add a pre-existing stale pointer to base commit
                stale_base = repo / "agent_workflows" / "stale_base.py"
                stale_base.write_text(
                    "# spec demo01 Section 2 :7\ndef stale():\n    pass\n",
                    encoding="utf-8",
                )
                subprocess.run(["git", "add", str(stale_base)], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "pre-existing stale anchor on base"],
                    cwd=repo,
                    check=True,
                )
                base_head = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    work_dir = kwargs.get("work_dir")
                    target_dir = pathlib.Path(work_dir)
                    foo_p = target_dir / "agent_workflows" / "foo.py"
                    foo_p.write_text(
                        "# spec demo01 Section 1 :7\ndef foo():\n    return 42\n",
                        encoding="utf-8",
                    )
                    subprocess.run(
                        ["git", "add", "agent_workflows/foo.py"],
                        cwd=target_dir,
                        check=True,
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", "clean change"],
                        cwd=target_dir,
                        check=True,
                    )
                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
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
                    return 0, "ses1", str(rd / "log"), [runner]

                driver_mod = _MODULES[runner]
                launcher_target = (
                    "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
                )
                with mock.patch.object(
                    driver_mod, launcher_target, fake_launcher
                ), mock.patch.object(
                    driver_mod,
                    "run_suite_check",
                    lambda *a, **k: self._passing_suite(repo),
                ):
                    driver_mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(
                    item["status"],
                    "executed",
                    "Pre-existing stale pointer must not hold lane",
                )
                final_main = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
                self.assertNotEqual(base_head, final_main, "Main must advance")

    def test_case_e_lane_only_moves_lines_in_non_spec_file_merged(self) -> None:
        """(e) A lane that only moves lines in a non-spec file: merged."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_fixture(td, retry_budget=0)

                # Add a stale pointer on base at line 2
                stale_file = repo / "agent_workflows" / "stale_base.py"
                stale_file.write_text(
                    "# Header\n# spec demo01 Section 2 :7\ndef stale():\n    pass\n",
                    encoding="utf-8",
                )
                subprocess.run(["git", "add", str(stale_file)], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "stale citation on base"],
                    cwd=repo,
                    check=True,
                )
                base_head = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    work_dir = kwargs.get("work_dir")
                    target_dir = pathlib.Path(work_dir)
                    target_stale = target_dir / "agent_workflows" / "stale_base.py"
                    # Move the comment down 5 lines without changing its text
                    target_stale.write_text(
                        "# Header\n# line 2\n# line 3\n# line 4\n# line 5\n# line 6\n# spec demo01 Section 2 :7\ndef stale():\n    pass\n",
                        encoding="utf-8",
                    )
                    subprocess.run(
                        ["git", "add", "agent_workflows/stale_base.py"],
                        cwd=target_dir,
                        check=True,
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", "shift lines down"],
                        cwd=target_dir,
                        check=True,
                    )
                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
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
                    return 0, "ses1", str(rd / "log"), [runner]

                driver_mod = _MODULES[runner]
                launcher_target = (
                    "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
                )
                with mock.patch.object(
                    driver_mod, launcher_target, fake_launcher
                ), mock.patch.object(
                    driver_mod,
                    "run_suite_check",
                    lambda *a, **k: self._passing_suite(repo),
                ):
                    driver_mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(
                    item["status"],
                    "executed",
                    "Moving citation line must not count as new stale pointer",
                )
                final_main = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
                self.assertNotEqual(base_head, final_main, "Main must advance")

    def test_case_f_detector_raises_merged_with_unknown_event(self) -> None:
        """(f) The detector raises: merged with a spec-anchor-check-unknown event."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_fixture(td, retry_budget=0)
                base_head = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    work_dir = kwargs.get("work_dir")
                    target_dir = pathlib.Path(work_dir)
                    foo_p = target_dir / "agent_workflows" / "foo.py"
                    foo_p.write_text(
                        "# spec demo01 Section 1 :7\ndef foo():\n    return 'changed'\n",
                        encoding="utf-8",
                    )
                    subprocess.run(
                        ["git", "add", "agent_workflows/foo.py"],
                        cwd=target_dir,
                        check=True,
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", "modify foo"],
                        cwd=target_dir,
                        check=True,
                    )
                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
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
                    return 0, "ses1", str(rd / "log"), [runner]

                driver_mod = _MODULES[runner]
                launcher_target = (
                    "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
                )
                with mock.patch.object(
                    driver_mod, launcher_target, fake_launcher
                ), mock.patch.object(
                    driver_mod,
                    "run_suite_check",
                    lambda *a, **k: self._passing_suite(repo),
                ), mock.patch.object(
                    spec_citations,
                    "stale_spec_anchors",
                    mock.Mock(side_effect=RuntimeError("simulated detector crash")),
                ):
                    driver_mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(
                    item["status"],
                    "executed",
                    "Detector failure must fail open and allow merge",
                )
                final_main = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
                self.assertNotEqual(
                    base_head, final_main, "Main must advance on fail-open"
                )

                # Check spec-anchor-check-unknown event in events.jsonl
                events_file = run_dir / "events.jsonl"
                self.assertTrue(events_file.exists())
                events = [
                    json.loads(line)
                    for line in events_file.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                unknown_events = [
                    e for e in events if e.get("event") == "spec-anchor-check-unknown"
                ]
                self.assertEqual(len(unknown_events), 1)
                self.assertEqual(unknown_events[0]["id6"], item["id6"])
                self.assertIn("simulated detector crash", unknown_events[0]["reason"])

    def test_case_g_budget_exhausted_fail_merge(self) -> None:
        """(g) Budget exhausted: item ends fail-merge with cause spec-anchor-new-stale, main unmoved."""
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as td:
                repo, run_dir, state, item = self._setup_fixture(td, retry_budget=1)
                initial_main = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()

                ask_count = 0

                def fake_launcher(state_arg, rd, itm, *args, **kwargs):
                    nonlocal ask_count
                    work_dir = kwargs.get("work_dir")
                    target_dir = pathlib.Path(work_dir)
                    log_suffix = kwargs.get("log_suffix", "")

                    if log_suffix == "spec-anchor":
                        ask_count += 1
                        # Scripted agent fails to fix it: commits another change keeping stale pointer
                        foo_p = target_dir / "agent_workflows" / "foo.py"
                        foo_p.write_text(
                            "# spec demo01 Section 2 :7\ndef foo():\n    pass # not fixed\n",
                            encoding="utf-8",
                        )
                        subprocess.run(
                            ["git", "add", "agent_workflows/foo.py"],
                            cwd=target_dir,
                            check=True,
                        )
                        subprocess.run(
                            ["git", "commit", "-qm", "retry commit still stale"],
                            cwd=target_dir,
                            check=True,
                        )
                        return 0, "ses1", str(rd / "spec-anchor-log"), [runner]

                    # Initial turn introduces stale pointer
                    foo_p = target_dir / "agent_workflows" / "foo.py"
                    foo_p.write_text(
                        "# spec demo01 Section 2 :7\ndef foo():\n    pass\n",
                        encoding="utf-8",
                    )
                    subprocess.run(
                        ["git", "add", "agent_workflows/foo.py"],
                        cwd=target_dir,
                        check=True,
                    )
                    subprocess.run(
                        ["git", "commit", "-qm", "introduce stale pointer"],
                        cwd=target_dir,
                        check=True,
                    )
                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
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
                    return 0, "ses1", str(rd / "log"), [runner]

                driver_mod = _MODULES[runner]
                launcher_target = (
                    "run_opencode" if runner == "oc_runipd" else "run_agy_turn"
                )
                with mock.patch.object(
                    driver_mod, launcher_target, fake_launcher
                ), mock.patch.object(
                    driver_mod,
                    "run_suite_check",
                    lambda *a, **k: self._passing_suite(repo),
                ):
                    driver_mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(ask_count, 1)
                self.assertEqual(
                    item["status"],
                    "fail-merge",
                    "Item must end in fail-merge when budget exhausted",
                )
                ladder = item.get("integration_ladder") or {}
                self.assertEqual(
                    ladder.get("cause"),
                    runner_shared.INTEGRATION_CAUSE_SPEC_ANCHOR_NEW_STALE,
                )
                deferral_reason = item.get("integration_deferral") or ""
                self.assertIn("correction budget is exhausted", deferral_reason)

                final_main = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
                self.assertEqual(
                    initial_main, final_main, "Main must NOT advance after exhaustion"
                )

    def test_case_h_direct_call_short_circuit(self) -> None:
        """(h) Direct call of new_stale_anchors on lane changing no spec and no scanned .py
        returns 'none' without scanning (detector not called).
        """
        with tempfile.TemporaryDirectory() as td:
            repo, run_dir, state, item = self._setup_fixture(td)
            base_head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            # Create lane branch modifying only README.md
            branch = "aw/lane/tst_short_circuit"
            subprocess.run(["git", "branch", branch], cwd=repo, check=True)
            wt = pathlib.Path(td) / "wt-tst"
            subprocess.run(
                ["git", "worktree", "add", "-q", str(wt), branch],
                cwd=repo,
                check=True,
            )
            (wt / "README.md").write_text("# Readme only\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=wt, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "touch readme only"], cwd=wt, check=True
            )
            lane_head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=wt,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(wt)], cwd=repo, check=True
            )

            mock_detector = mock.Mock(side_effect=RuntimeError("must not be called"))
            with mock.patch.object(spec_citations, "stale_spec_anchors", mock_detector):
                result = spec_citations.new_stale_anchors(repo, lane_head, base_head)

            self.assertEqual(result.status, "none")
            self.assertEqual(result.findings, [])
            mock_detector.assert_not_called()


if __name__ == "__main__":
    unittest.main()
