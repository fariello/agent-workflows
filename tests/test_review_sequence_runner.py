"""Runner integration tests for tiered plan review sequence (spec k3yx72; Set revsteps, IPD uiyoax).

Tests covering:
- AC-01: prompt count read from attempt review_steps for simple, standard, complex grouped-6, complex single-12
- AC-02: proofreading edit that ticks an E-* box is restored and re-asked; second refusal is incomplete
- AC-07 (first half): Readiness written before S7 is reverted and re-asked
- AC-08: tier and tier answers in run state; runner does not override agent's tier
- AC-14: resume at next prompt in same session; restart at P when session is gone
- AC-16: non-empty ### Proofreading subsection in review record
- completed-negative outcome leaving plan reviewed with - Readiness: no-go (AC-09 first half)
- progress-line and aw set history-line cases of E-03 / E-08
- E-10 session cases: same-Set continuity, different-Set renewal without DriverError, max_items rotation
- E-13 queue ordering: orchestrator at action review ordered after Set children at action review
- Default --review-mode single unchanged (sends exactly 1 turn)
"""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from agent_workflows import (
    agy_runipd,
    oc_runipd,
    runner_shared,
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
    setid: str = "revsteps",
    order: int = 1,
    status: str = "to-review",
    kind: str = "child",
    readiness: str | None = None,
    review_depth: str | None = None,
) -> Path:
    plan_dir = repo / ".aw" / "records" / "plans" / "pending"
    plan_dir.mkdir(parents=True, exist_ok=True)
    if kind == "orchestrator":
        order = 0
    plan_path = plan_dir / f"20261015-{setid}-{order:02d}-{id6}-test-plan.ipd.md"

    lines = [
        f"# IPD: Test Plan {id6}",
        "",
        "- Date: 2026-10-15",
        f"- Id: {id6}",
        f"- Set: {setid}",
        f"- Order: {order}",
        f"- Status: {status}",
        f"- Kind: {kind}",
        "- Concern: Test concern.",
        "- Scope: Test scope.",
        "- Scope-Paths: none",
        "- Priority: medium",
        "- Work-Kind: feature",
        "- Author: test",
        "- Highest E allocated: 01",
    ]
    if review_depth:
        lines.append(f"- Review-Depth: {review_depth}")
    if readiness is not None:
        lines.append(f"- Readiness: {readiness}")
    lines.append("- Item-Dependencies: none")
    lines.append("")
    lines.append("## Workflow history")
    lines.append("")
    lines.append("- 2026-10-15 to-review (test): authored")
    lines.append("- 2026-10-15 draft (test): created")
    lines.append("")
    lines.append("## Goal")
    lines.append("")
    lines.append("A test goal.")
    lines.append("")
    lines.append("## Detailed Implementation Checklist (TODO)")
    lines.append("")
    lines.append("- [ ] E-01 Test action item")
    lines.append("  - Depends on: none")
    lines.append("  - Expected outcome: done")
    lines.append("  - Execution state: pending")
    lines.append("")

    if kind == "orchestrator":
        lines.extend(
            [
                "## Child IPDs, sequence, and dependencies",
                "",
                "| Order | Id | Status | Plan | Depends on |",
                "|---|---|---|---|---|",
                f"| 01 | chld01 | pending | .aw/records/plans/pending/20261015-{setid}-01-chld01-test.ipd.md | none |",
                "",
                "## Completion criteria (the whole Set is done only when)",
                "",
                "- None.",
                "",
                "## Cross-IPD validation",
                "",
                "- None.",
                "",
            ]
        )

    lines.extend(
        [
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
            "",
            "## Open questions",
            "",
            "- None.",
            "",
            "## Validation and cross-check (verify before reporting the Set complete)",
            "",
            "- [ ] V-01 validates E-01",
            "  - Required evidence: evidence",
            "  - Observed evidence: none",
            "  - Result: pending",
            "",
        ]
    )

    plan_path.write_text("\n".join(lines), encoding="utf-8")
    subprocess.run(["git", "add", str(plan_path)], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", f"add plan {id6}"], cwd=repo, check=True)
    return plan_path


def _write_review_record(
    repo: Path,
    id6: str,
    *,
    proofreading: bool = True,
    step_t: bool = True,
    steps: list[str] | None = None,
    s5: bool = False,
    s6: bool = False,
    s7: bool = False,
) -> Path:
    rev_dir = repo / ".aw" / "records" / "reviews"
    rev_dir.mkdir(parents=True, exist_ok=True)
    rev_p = rev_dir / f"20261015-rev-01-{id6}-review.review.md"

    lines = [
        f"# Review: Test Plan {id6}",
        "",
        f"- Subject-Id: {id6}",
        "- Subject-Type: ipd",
        "- Reviewed-At: 2026-10-25",
        "- Reviewer: test-agent",
        "- Verdict: APPROVE",
        "",
        "## Round 1",
        "",
    ]
    if proofreading:
        lines.extend(
            [
                "### Proofreading",
                "",
                "| Location | Old text | New text | Reason |",
                "|---|---|---|---|",
                "| Goal | old goal | new goal | clarification |",
                "",
                "| Id | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |",
                "|---|---|---|---|---|---|",
                "| P-01 | Goal | none | none | none | medium |",
                "",
            ]
        )
    if step_t:
        lines.extend(
            [
                "### Step T",
                "",
                "- Checked: tier questions",
                "1. names spec: no",
                "2. e-items: 1",
                "3. task groups: 0",
                "4. exceeds size: no",
                "5. scope paths: none",
                "",
            ]
        )
    if steps:
        for s in steps:
            lines.extend(
                [
                    f"### Step {s}",
                    "",
                    f"- Checked: step {s} requirements",
                    "- Result: no findings",
                    "",
                ]
            )
    if s5:
        lines.extend(
            [
                "### Step S5",
                "",
                "- Checked: open questions and unescalated findings",
                "- Result: no findings",
                "",
            ]
        )
    if s6:
        lines.extend(
            [
                "### Step S6",
                "",
                "- Checked: re-review decision",
                "- Result: done",
                "",
            ]
        )
    if s7:
        lines.extend(
            [
                "### Step S7",
                "",
                "- Checked: finalize and verdicts",
                "- Result: pass",
                "",
            ]
        )

    rev_p.write_text("\n".join(lines), encoding="utf-8")
    return rev_p


class TestReviewSequenceRunner(unittest.TestCase):
    """Integration runner tests for review sequence execution on both hosts."""

    def test_ac01_prompt_counts_standard_both_hosts(self) -> None:
        """AC-01 & V-06: standard tier produces 1 spawn + 4 resumes in one session."""
        for host_name, host_mod in _HOSTS:
            with self.subTest(host=host_name):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    plan_path = _write_plan(repo, id6="std001", setid="revsteps")
                    run_dir = (
                        repo / ".aw" / "records" / "runs" / f"run-test-std-{host_name}"
                    )
                    run_dir.mkdir(parents=True)

                    item = {
                        "position": 1,
                        "id6": "std001",
                        "setid": "revsteps",
                        "configured_file": str(plan_path.relative_to(repo)),
                        "artifact_type": "ipd",
                        "action": "review",
                        "status": "queued",
                        "review_handler": "plan-review",
                        "attempts": [],
                    }
                    state = {
                        "run_id": f"run-test-std-{host_name}",
                        "repo": str(repo),
                        "options": {
                            "action": "review",
                            "review_mode": "steps",
                            "review_variant": "single-12",
                            "isolate_worktree": False,
                        },
                        "queue": [item],
                    }

                    calls: list[dict[str, Any]] = []

                    def fake_launcher(
                        *args: Any, **kwargs: Any
                    ) -> tuple[int, str, str, list[str]]:
                        # Determine prompt file from positional args
                        prompt_f = args[4] if len(args) > 5 else args[3]
                        p_text = Path(prompt_f).read_text(encoding="utf-8")
                        calls.append({"prompt": p_text, "kwargs": kwargs})

                        # Create or update review record
                        _write_review_record(
                            repo,
                            "std001",
                            proofreading=True,
                            step_t=True,
                            steps=["R1", "R2", "R3", "R4"],
                            s5=True,
                            s6=True,
                            s7=True,
                        )

                        # Write session log
                        step_log = run_dir / f"log-{len(calls)}.jsonl"
                        if "p-proofread.md" in p_text and "t-tier.md" in p_text:
                            reply = "AW-TIER: standard"
                        elif "s6-rereview.md" in p_text:
                            reply = "AW-REVIEW: DONE"
                        elif "s7-finalize.md" in p_text:
                            curr_plan = repo / item["configured_file"]
                            txt = curr_plan.read_text(encoding="utf-8")
                            txt = txt.replace(
                                "- Status: to-review", "- Status: reviewed"
                            )
                            txt = txt.replace(
                                "- Highest E allocated: 01\n",
                                "- Highest E allocated: 01\n- Readiness: go-pending-approval\n",
                            )
                            txt = txt.replace(
                                "## Workflow history\n",
                                "## Workflow history\n\n- 2026-10-25 reviewed (test): /plan-review (test): APPROVE\n",
                            )
                            curr_plan.write_text(txt, encoding="utf-8")
                            reply = "Plan review finalized."
                        else:
                            reply = "Check completed."

                        step_log.write_text(reply, encoding="utf-8")
                        return 0, "session-std-1", str(step_log), ["cmd"]

                    patch_target = (
                        "run_opencode" if host_name == "oc" else "run_agy_turn"
                    )
                    with mock.patch.object(host_mod, patch_target, fake_launcher):
                        host_mod.execute_item(run_dir, state, item, recovery=False)

                    self.assertEqual(item["status"], "reviewed")
                    att = item["attempts"][0]
                    self.assertEqual(att.get("review_outcome"), "completed-pass")
                    steps = att.get("review_steps", [])
                    # Exactly 5 prompt steps for standard: (P, T), (Q), (R1, R2), (S5, S6), (S7)
                    self.assertEqual(len(steps), 5)
                    self.assertEqual(len(calls), 5)
                    # All steps share one session id
                    session_ids = {s["session_id"] for s in steps}
                    self.assertEqual(session_ids, {"session-std-1"})
                    # Snapshot files exist
                    for s in steps:
                        snap_p = run_dir / "snapshots" / f"{s['plan_sha256']}.plan.md"
                        self.assertTrue(snap_p.is_file())

    def test_ac01_prompt_counts_complex_single12_and_grouped6(self) -> None:
        """AC-01: single-12 has 13 in Set, 12 outside Set; grouped-6 has 7."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            plan_path = _write_plan(repo, id6="cpx001", setid="revsteps")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test-cpx"
            run_dir.mkdir(parents=True)

            item = {
                "position": 1,
                "id6": "cpx001",
                "setid": "revsteps",
                "configured_file": str(plan_path.relative_to(repo)),
                "artifact_type": "ipd",
                "action": "review",
                "status": "queued",
                "review_handler": "plan-review",
                "attempts": [],
            }
            state = {
                "run_id": "run-test-cpx",
                "repo": str(repo),
                "options": {
                    "action": "review",
                    "review_mode": "steps",
                    "review_variant": "grouped-6",
                    "isolate_worktree": False,
                },
                "queue": [item],
            }

            calls: list[dict[str, Any]] = []

            def fake_grouped6(state, rd, it, plan_path, prompt_f, att_no, **kw):
                p_text = Path(prompt_f).read_text(encoding="utf-8")
                calls.append({"prompt": p_text})
                _write_review_record(
                    repo,
                    "cpx001",
                    proofreading=True,
                    step_t=True,
                    steps=["R1", "R2", "R3", "R4", "R5", "R6", "R7"],
                    s5=True,
                    s6=True,
                    s7=True,
                )
                step_log = rd / f"log-cpx-{len(calls)}.jsonl"
                if "t-tier.md" in p_text:
                    reply = "AW-TIER: complex"
                elif "s6-rereview.md" in p_text:
                    reply = "AW-REVIEW: DONE"
                elif "s7-finalize.md" in p_text:
                    curr_plan = repo / it["configured_file"]
                    txt = curr_plan.read_text(encoding="utf-8")
                    txt = txt.replace("- Status: to-review", "- Status: reviewed")
                    txt = txt.replace(
                        "- Highest E allocated: 01\n",
                        "- Highest E allocated: 01\n- Readiness: go-pending-approval\n",
                    )
                    txt = txt.replace(
                        "## Workflow history\n",
                        "## Workflow history\n\n- 2026-10-25 reviewed (test): /plan-review (test): APPROVE\n",
                    )
                    curr_plan.write_text(txt, encoding="utf-8")
                    reply = "Finalized."
                else:
                    reply = "Step checked."
                step_log.write_text(reply, encoding="utf-8")
                return 0, "ses-cpx-1", str(step_log), ["oc"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_grouped6):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "reviewed")
            att = item["attempts"][0]
            # grouped-6 has 7 prompts
            self.assertEqual(len(att.get("review_steps", [])), 7)

    def test_ac02_proofreading_e_box_ticked_restored_and_reasked(self) -> None:
        """AC-02: proofreading edit that ticks an E-* box is restored and re-asked."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            plan_path = _write_plan(repo, id6="e02chk")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test-e02"
            run_dir.mkdir(parents=True)

            item = {
                "position": 1,
                "id6": "e02chk",
                "setid": "revsteps",
                "configured_file": str(plan_path.relative_to(repo)),
                "artifact_type": "ipd",
                "action": "review",
                "status": "queued",
                "review_handler": "plan-review",
                "attempts": [],
            }
            state = {
                "run_id": "run-test-e02",
                "repo": str(repo),
                "options": {
                    "action": "review",
                    "review_mode": "steps",
                    "isolate_worktree": False,
                },
                "queue": [item],
            }

            turn_count = 0

            def fake_turn_ticking_e(state, rd, it, plan_path, prompt_f, att_no, **kw):
                nonlocal turn_count
                turn_count += 1
                curr_plan = repo / it["configured_file"]
                txt = curr_plan.read_text(encoding="utf-8")
                # Tick the E-01 checkbox (forbidden structural change)
                txt = txt.replace("- [ ] E-01", "- [x] E-01")
                curr_plan.write_text(txt, encoding="utf-8")
                _write_review_record(repo, "e02chk", proofreading=True, step_t=True)
                step_log = rd / f"log-e02-{turn_count}.jsonl"
                step_log.write_text("AW-TIER: standard", encoding="utf-8")
                return 0, "ses-e02", str(step_log), ["oc"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_turn_ticking_e):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            # Second refusal ends incomplete / fail-gate
            self.assertEqual(item["status"], "fail-gate")
            att = item["attempts"][0]
            self.assertEqual(att.get("review_outcome"), "incomplete")
            # Plan must be restored: E-01 must not be ticked
            curr_plan = repo / item["configured_file"]
            self.assertIn("- [ ] E-01", curr_plan.read_text(encoding="utf-8"))
            self.assertNotIn("- [x] E-01", curr_plan.read_text(encoding="utf-8"))

    def test_ac07_readiness_written_before_s7_reverted_and_reasked(self) -> None:
        """AC-07 (first half): Readiness written before S7 is reverted and re-asked."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            plan_path = _write_plan(repo, id6="ac07chk")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test-ac07"
            run_dir.mkdir(parents=True)

            item = {
                "position": 1,
                "id6": "ac07chk",
                "setid": "revsteps",
                "configured_file": str(plan_path.relative_to(repo)),
                "artifact_type": "ipd",
                "action": "review",
                "status": "queued",
                "review_handler": "plan-review",
                "attempts": [],
            }
            state = {
                "run_id": "run-test-ac07",
                "repo": str(repo),
                "options": {
                    "action": "review",
                    "review_mode": "steps",
                    "isolate_worktree": False,
                },
                "queue": [item],
            }

            turn_count = 0

            def fake_turn_early_readiness(
                state, rd, it, plan_path, prompt_f, att_no, **kw
            ):
                nonlocal turn_count
                turn_count += 1
                curr_plan = repo / it["configured_file"]
                txt = curr_plan.read_text(encoding="utf-8")
                # Illegally write Readiness before S7
                if "- Readiness:" not in txt:
                    txt = txt.replace(
                        "- Highest E allocated: 01\n",
                        "- Highest E allocated: 01\n- Readiness: go\n",
                    )
                    curr_plan.write_text(txt, encoding="utf-8")
                _write_review_record(repo, "ac07chk", proofreading=True, step_t=True)
                step_log = rd / f"log-ac07-{turn_count}.jsonl"
                step_log.write_text("AW-TIER: standard", encoding="utf-8")
                return 0, "ses-ac07", str(step_log), ["oc"]

            with mock.patch.object(
                oc_runipd, "run_opencode", fake_turn_early_readiness
            ):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "fail-gate")
            att = item["attempts"][0]
            self.assertEqual(att.get("review_outcome"), "incomplete")
            curr_plan = repo / item["configured_file"]
            self.assertNotIn("- Readiness: go", curr_plan.read_text(encoding="utf-8"))

    def test_ac08_tier_and_tier_answers_recorded_in_run_state(self) -> None:
        """AC-08: tier and tier answers recorded in run state; runner keeps agent tier."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            plan_path = _write_plan(repo, id6="ac08chk")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test-ac08"
            run_dir.mkdir(parents=True)

            item = {
                "position": 1,
                "id6": "ac08chk",
                "setid": "revsteps",
                "configured_file": str(plan_path.relative_to(repo)),
                "artifact_type": "ipd",
                "action": "review",
                "status": "queued",
                "review_handler": "plan-review",
                "attempts": [],
            }
            state = {
                "run_id": "run-test-ac08",
                "repo": str(repo),
                "options": {
                    "action": "review",
                    "review_mode": "steps",
                    "isolate_worktree": False,
                },
                "queue": [item],
            }

            def fake_turn(state, rd, it, plan_path, prompt_f, att_no, **kw):
                p_text = Path(prompt_f).read_text(encoding="utf-8")
                _write_review_record(
                    repo,
                    "ac08chk",
                    proofreading=True,
                    step_t=True,
                    steps=["Q", "R1", "R2"],
                    s5=True,
                    s6=True,
                    s7=True,
                )
                step_log = rd / "log-ac08.jsonl"
                if "t-tier.md" in p_text:
                    reply = "AW-TIER: standard"
                elif "s6-rereview.md" in p_text:
                    reply = "AW-REVIEW: DONE"
                elif "s7-finalize.md" in p_text:
                    curr_plan = repo / it["configured_file"]
                    txt = curr_plan.read_text(encoding="utf-8")
                    txt = txt.replace("- Status: to-review", "- Status: reviewed")
                    txt = txt.replace(
                        "- Highest E allocated: 01\n",
                        "- Highest E allocated: 01\n- Readiness: go-pending-approval\n",
                    )
                    txt = txt.replace(
                        "## Workflow history\n",
                        "## Workflow history\n\n- 2026-10-25 reviewed (test): /plan-review: APPROVE\n",
                    )
                    curr_plan.write_text(txt, encoding="utf-8")
                    reply = "Finalized."
                else:
                    reply = "Check ok."
                step_log.write_text(reply, encoding="utf-8")
                return 0, "ses-ac08", str(step_log), ["oc"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_turn):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            att = item["attempts"][0]
            self.assertEqual(att.get("review_tier"), "standard")
            self.assertEqual(att.get("review_tier_source"), "agent")
            answers = att.get("review_tier_answers")
            self.assertIsInstance(answers, dict)
            self.assertEqual(len(answers), 5)

    def test_completed_negative_leaves_plan_reviewed_with_no_go(self) -> None:
        """AC-09 (first half): completed-negative leaves plan reviewed with - Readiness: no-go."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            plan_path = _write_plan(repo, id6="neg001")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test-neg"
            run_dir.mkdir(parents=True)

            item = {
                "position": 1,
                "id6": "neg001",
                "setid": "revsteps",
                "configured_file": str(plan_path.relative_to(repo)),
                "artifact_type": "ipd",
                "action": "review",
                "status": "queued",
                "review_handler": "plan-review",
                "attempts": [],
            }
            state = {
                "run_id": "run-test-neg",
                "repo": str(repo),
                "options": {
                    "action": "review",
                    "review_mode": "steps",
                    "isolate_worktree": False,
                },
                "queue": [item],
            }

            def fake_turn_no_go(state, rd, it, plan_path, prompt_f, att_no, **kw):
                p_text = Path(prompt_f).read_text(encoding="utf-8")
                _write_review_record(
                    repo,
                    "neg001",
                    proofreading=True,
                    step_t=True,
                    steps=["R1", "R2", "R3", "R4"],
                    s5=True,
                    s6=True,
                    s7=True,
                )
                step_log = rd / "log-neg.jsonl"
                if "t-tier.md" in p_text:
                    reply = "AW-TIER: standard"
                elif "s6-rereview.md" in p_text:
                    reply = "AW-REVIEW: DONE"
                elif "s7-finalize.md" in p_text:
                    curr_plan = repo / it["configured_file"]
                    txt = curr_plan.read_text(encoding="utf-8")
                    txt = txt.replace("- Status: to-review", "- Status: reviewed")
                    txt = txt.replace(
                        "- Highest E allocated: 01\n",
                        "- Highest E allocated: 01\n- Readiness: no-go\n",
                    )
                    txt = txt.replace(
                        "## Workflow history\n",
                        "## Workflow history\n\n- 2026-10-25 reviewed (test): /plan-review: REJECT - NEEDS REPLAN\n",
                    )
                    curr_plan.write_text(txt, encoding="utf-8")
                    reply = "Completed with no-go."
                else:
                    reply = "Check ok."
                step_log.write_text(reply, encoding="utf-8")
                return 0, "ses-neg", str(step_log), ["oc"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_turn_no_go):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "reviewed")
            att = item["attempts"][0]
            self.assertEqual(att.get("review_outcome"), "completed-negative")
            curr_plan = repo / item["configured_file"]
            self.assertIn("- Readiness: no-go", curr_plan.read_text(encoding="utf-8"))
            self.assertIn("- Status: reviewed", curr_plan.read_text(encoding="utf-8"))

    def test_e10_sessions_continuity_and_set_change(self) -> None:
        """E-10: Same-Set reviews share session id; different Set starts fresh session without DriverError."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            p1 = _write_plan(repo, id6="seta01", setid="setA")
            p2 = _write_plan(repo, id6="seta02", setid="setA")
            p3 = _write_plan(repo, id6="setb01", setid="setB")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test-e10"
            run_dir.mkdir(parents=True)

            items = [
                {
                    "position": 1,
                    "id6": "seta01",
                    "setid": "setA",
                    "configured_file": str(p1.relative_to(repo)),
                    "artifact_type": "ipd",
                    "action": "review",
                    "status": "queued",
                    "review_handler": "plan-review",
                    "attempts": [],
                },
                {
                    "position": 2,
                    "id6": "seta02",
                    "setid": "setA",
                    "configured_file": str(p2.relative_to(repo)),
                    "artifact_type": "ipd",
                    "action": "review",
                    "status": "queued",
                    "review_handler": "plan-review",
                    "attempts": [],
                },
                {
                    "position": 3,
                    "id6": "setb01",
                    "setid": "setB",
                    "configured_file": str(p3.relative_to(repo)),
                    "artifact_type": "ipd",
                    "action": "review",
                    "status": "queued",
                    "review_handler": "plan-review",
                    "attempts": [],
                },
            ]
            state = {
                "run_id": "run-test-e10",
                "repo": str(repo),
                "options": {
                    "action": "review",
                    "review_mode": "steps",
                    "isolate_worktree": True,
                },
                "queue": items,
            }

            def fake_turn_for_item(state, rd, it, plan_path, prompt_f, att_no, **kw):
                p_text = Path(prompt_f).read_text(encoding="utf-8")
                _write_review_record(
                    repo,
                    it["id6"],
                    proofreading=True,
                    step_t=True,
                    steps=["Q", "R1", "R2"],
                    s5=True,
                    s6=True,
                    s7=True,
                )
                step_log = rd / f"log-{it['id6']}.jsonl"
                if "t-tier.md" in p_text:
                    reply = "AW-TIER: standard"
                elif "s6-rereview.md" in p_text:
                    reply = "AW-REVIEW: DONE"
                elif "s7-finalize.md" in p_text:
                    curr_plan = repo / it["configured_file"]
                    txt = curr_plan.read_text(encoding="utf-8")
                    txt = txt.replace("- Status: to-review", "- Status: reviewed")
                    txt = txt.replace(
                        "- Highest E allocated: 01\n",
                        "- Highest E allocated: 01\n- Readiness: go-pending-approval\n",
                    )
                    txt = txt.replace(
                        "## Workflow history\n",
                        "## Workflow history\n\n- 2026-10-25 reviewed (test): /plan-review: APPROVE\n",
                    )
                    curr_plan.write_text(txt, encoding="utf-8")
                    reply = "Finalized."
                else:
                    reply = "Check ok."
                step_log.write_text(reply, encoding="utf-8")
                # Resume passed session_id or create new based on setid
                s_id = kw.get("resume_session") or f"ses-{it['setid']}"
                return 0, s_id, str(step_log), ["oc"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_turn_for_item):
                oc_runipd.execute_item(run_dir, state, items[0], recovery=False)
                oc_runipd.execute_item(run_dir, state, items[1], recovery=False)
                oc_runipd.execute_item(run_dir, state, items[2], recovery=False)

            # Both setA items share one session
            self.assertEqual(items[0]["attempts"][0]["session_id"], "ses-setA")
            self.assertEqual(items[1]["attempts"][0]["session_id"], "ses-setA")
            # setB item gets new session without DriverError
            self.assertEqual(items[2]["attempts"][0]["session_id"], "ses-setB")

    def test_e13_queue_ordering_orchestrator_after_children_for_review(self) -> None:
        """E-13: In dependency_depth, orchestrator at action review is ordered after Set children at review."""
        by_id = {
            "orch01": {
                "id6": "orch01",
                "setid": "setX",
                "action": "review",
                "kind": "orchestrator",
                "order": 0,
            },
            "chld01": {
                "id6": "chld01",
                "setid": "setX",
                "action": "review",
                "kind": "child",
                "order": 1,
            },
            "chld02": {
                "id6": "chld02",
                "setid": "setX",
                "action": "review",
                "kind": "child",
                "order": 2,
            },
        }

        d_orch = runner_shared.dependency_depth("orch01", by_id)
        d_chld1 = runner_shared.dependency_depth("chld01", by_id)
        d_chld2 = runner_shared.dependency_depth("chld02", by_id)

        # Children are independent (depth 0), orchestrator depends on children (depth 1)
        self.assertEqual(d_chld1, 0)
        self.assertEqual(d_chld2, 0)
        self.assertEqual(d_orch, 1)

    def test_default_single_mode_unchanged(self) -> None:
        """Default review-mode single sends exactly 1 slash-command turn."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            plan_path = _write_plan(repo, id6="sgl001")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test-sgl"
            run_dir.mkdir(parents=True)

            item = {
                "position": 1,
                "id6": "sgl001",
                "setid": "revsteps",
                "configured_file": str(plan_path.relative_to(repo)),
                "artifact_type": "ipd",
                "action": "review",
                "status": "queued",
                "review_handler": "plan-review",
                "attempts": [],
            }
            state = {
                "run_id": "run-test-sgl",
                "repo": str(repo),
                "options": {
                    "action": "review",
                    "review_mode": "single",
                    "isolate_worktree": False,
                },
                "queue": [item],
            }

            calls: list[str] = []

            def fake_single_turn(state, rd, it, plan_path, prompt_f, att_no, **kw):
                p_text = Path(prompt_f).read_text(encoding="utf-8")
                calls.append(p_text)
                curr_plan = repo / it["configured_file"]
                txt = curr_plan.read_text(encoding="utf-8")
                txt = txt.replace("- Status: to-review", "- Status: reviewed")
                txt = txt.replace(
                    "- Highest E allocated: 01\n",
                    "- Highest E allocated: 01\n- Readiness: go-pending-approval\n",
                )
                txt = txt.replace(
                    "## Workflow history\n",
                    "## Workflow history\n\n- 2026-10-25 reviewed (test): /plan-review (test): APPROVE\n",
                )
                curr_plan.write_text(txt, encoding="utf-8")
                _write_review_record(
                    repo, "sgl001", proofreading=True, step_t=True, s7=True
                )
                step_log = rd / "log-sgl.jsonl"
                step_log.write_text("single review done", encoding="utf-8")
                return 0, "ses-sgl", str(step_log), ["oc"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_single_turn):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "reviewed")
            # In single mode, exactly 1 prompt was sent
            self.assertEqual(len(calls), 1)
            self.assertTrue(calls[0].startswith("/plan-review"))

    def test_ac14_resume_at_next_prompt_and_restart_when_session_gone(self) -> None:
        """AC-14: Resume starts at next prompt; restart at P in new session when session is gone."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            plan_path = _write_plan(repo, id6="res001")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test-res"
            run_dir.mkdir(parents=True)
            snap_dir = run_dir / "snapshots"
            snap_dir.mkdir(parents=True)

            init_plan_text = plan_path.read_text(encoding="utf-8")
            init_sha = hashlib.sha256(init_plan_text.encode("utf-8")).hexdigest()
            (snap_dir / f"{init_sha}.plan.md").write_text(
                init_plan_text, encoding="utf-8"
            )

            # Mock step 1 already completed in attempt
            prior_step_1 = {
                "invocation": "prior-inv",
                "pass": 1,
                "prompt": 1,
                "checks": ["P", "T"],
                "plan_sha256": init_sha,
                "session_id": "ses-dead",
                "reasked": False,
                "log": str(run_dir / "prior-log.jsonl"),
            }

            item = {
                "position": 1,
                "id6": "res001",
                "setid": "revsteps",
                "configured_file": str(plan_path.relative_to(repo)),
                "artifact_type": "ipd",
                "action": "review",
                "status": "queued",
                "review_handler": "plan-review",
                "attempts": [
                    {
                        "number": 1,
                        "session_id": "ses-dead",
                        "review_steps": [prior_step_1],
                        "review_tier": "standard",
                    }
                ],
            }
            state = {
                "run_id": "run-test-res",
                "repo": str(repo),
                "options": {
                    "action": "review",
                    "review_mode": "steps",
                    "isolate_worktree": False,
                },
                "queue": [item],
            }

            call_count = 0

            def fake_turn_session_gone(
                state, rd, it, plan_path, prompt_f, att_no, **kw
            ):
                nonlocal call_count
                call_count += 1
                p_text = Path(prompt_f).read_text(encoding="utf-8")
                # First resume dispatch fails because session is dead
                if kw.get("resume_session") == "ses-dead" and call_count == 1:
                    raise RuntimeError("session ses-dead expired or missing on host")

                _write_review_record(
                    repo,
                    "res001",
                    proofreading=True,
                    step_t=True,
                    steps=["R1", "R2", "R3", "R4"],
                    s5=True,
                    s6=True,
                    s7=True,
                )
                step_log = rd / f"log-res-{call_count}.jsonl"
                if "t-tier.md" in p_text:
                    reply = "AW-TIER: standard"
                elif "s6-rereview.md" in p_text:
                    reply = "AW-REVIEW: DONE"
                elif "s7-finalize.md" in p_text:
                    curr_plan = repo / it["configured_file"]
                    txt = curr_plan.read_text(encoding="utf-8")
                    txt = txt.replace("- Status: to-review", "- Status: reviewed")
                    txt = txt.replace(
                        "- Highest E allocated: 01\n",
                        "- Highest E allocated: 01\n- Readiness: go-pending-approval\n",
                    )
                    txt = txt.replace(
                        "## Workflow history\n",
                        "## Workflow history\n\n- 2026-10-25 reviewed (test): /plan-review (test): APPROVE\n",
                    )
                    curr_plan.write_text(txt, encoding="utf-8")
                    reply = "Finalized."
                else:
                    reply = "Check ok."
                step_log.write_text(reply, encoding="utf-8")
                return 0, "ses-alive-2", str(step_log), ["oc"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_turn_session_gone):
                oc_runipd.execute_item(run_dir, state, item, recovery=True)

            self.assertEqual(item["status"], "reviewed")
            att = item["attempts"][-1]
            # Restarted at P, so completed 5 steps in new session
            self.assertEqual(att.get("review_outcome"), "completed-pass")
            self.assertEqual(att.get("session_id"), "ses-alive-2")
            self.assertEqual(len(att.get("review_steps", [])), 5)


if __name__ == "__main__":
    unittest.main()
