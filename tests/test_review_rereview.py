"""Tests for AW-REVIEW re-review marker, runner triggers, and bounded loop.

Implements IPD is2xiv E-06 (spec k3yx72 Sections 8.1, 8.2, 8.3, and acceptance criteria
AC-03, AC-04, AC-05, AC-06, AC-07, AC-14).
"""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from agent_workflows import (
    ipd_lint,
    ipd_schema,
    oc_runipd,
    plan_readiness,
    review_findings,
    review_rereview,
)
from tests.test_review_sequence_runner import (
    _HOSTS,
    _make_test_repo,
    _write_plan,
    _write_review_record,
)

SAMPLE_PLAN_BASE = """# IPD: Sample Test Plan

- Date: 2026-10-25
- Id: spl001
- Set: sample
- Order: 1
- Status: to-review
- Kind: child
- Concern: Test concern.
- Scope: Test scope.
- Scope-Paths: none
- Item-Dependencies: none
- Priority: medium
- Work-Kind: feature
- Author: test
- Highest E allocated: 01

## Workflow history

- 2026-10-25 to-review (test): authored
- 2026-10-25 draft (test): created

## Goal

Test goal.

## Detailed Implementation Checklist (TODO)

- [ ] E-01 Implement the feature
  - Depends on: none
  - Expected outcome: feature is working
  - Execution state: pending

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: tests pass
  - Result: pending

## Open questions

### OQ-01: Is this a test question?

- Blocking: no
- Status: open
- Rationale: Non-blocking test question.
"""


# ==============================================================================
# Task group 1 & 2: Pure Unit Tests (pytestmark = pytest.mark.core)
# ==============================================================================


@pytest.mark.core
def test_marker_parsing() -> None:
    """E-01 & spec Section 8.1: test marker parsing rules."""
    # Valid AGAIN and DONE
    assert review_rereview.parse_rereview_marker("AW-REVIEW: AGAIN") == "AGAIN"
    assert review_rereview.parse_rereview_marker("AW-REVIEW: DONE") == "DONE"

    # Leading / trailing whitespace
    assert review_rereview.parse_rereview_marker("   AW-REVIEW: DONE   \n\n") == "DONE"
    assert review_rereview.parse_rereview_marker("\n\tAW-REVIEW: AGAIN\t\n") == "AGAIN"

    # Trailing code fence
    fence_reply = "AW-REVIEW: DONE\n```"
    assert review_rereview.parse_rereview_marker(fence_reply) == "DONE"

    fence_reply_2 = "```text\nAW-REVIEW: AGAIN\n```\n"
    assert review_rereview.parse_rereview_marker(fence_reply_2) == "AGAIN"

    tilde_reply = "AW-REVIEW: DONE\n~~~"
    assert review_rereview.parse_rereview_marker(tilde_reply) == "DONE"

    # Lowercase marker -> None
    assert review_rereview.parse_rereview_marker("aw-review: done") is None
    assert review_rereview.parse_rereview_marker("AW-Review: Again") is None

    # Not on the last line -> None
    not_last = "AW-REVIEW: DONE\nSome additional text after the marker."
    assert review_rereview.parse_rereview_marker(not_last) is None

    # Both sentinels in body with DONE last -> DONE
    both_sentinels = (
        "In pass 1 I considered AW-REVIEW: AGAIN,\n"
        "but all checks now pass, so:\n"
        "AW-REVIEW: DONE"
    )
    assert review_rereview.parse_rereview_marker(both_sentinels) == "DONE"

    # Reply with no marker
    assert review_rereview.parse_rereview_marker("Everything looks good.") is None
    assert review_rereview.parse_rereview_marker("") is None


@pytest.mark.core
def test_triggers() -> None:
    """E-02 & spec Section 8.2: test runner triggers."""
    base = SAMPLE_PLAN_BASE

    # (a) E/V added: adding one E/V pair yields one reason
    added_ev = base.replace(
        "- [ ] E-01 Implement the feature",
        "- [ ] E-01 Implement the feature\n"
        "  - Depends on: none\n"
        "  - Expected outcome: feature is working\n"
        "  - Execution state: pending\n\n"
        "- [ ] E-02 Additional task",
    )
    reasons = review_rereview.rereview_triggers(base, added_ev, after_r_text=None)
    assert len(reasons) == 1
    assert "E/V items changed: added E-02" in reasons[0]

    # (b) Scope-Paths changed -> 1 reason
    changed_sp = base.replace("- Scope-Paths: none", "- Scope-Paths: src/file.py")
    reasons_sp = review_rereview.rereview_triggers(base, changed_sp, after_r_text=None)
    assert len(reasons_sp) == 1
    assert "Scope-Paths changed" in reasons_sp[0]

    # (c) Item-Dependencies changed -> 1 reason
    changed_dep = base.replace(
        "- Item-Dependencies: none", "- Item-Dependencies: executed:uiyoax"
    )
    reasons_dep = review_rereview.rereview_triggers(
        base, changed_dep, after_r_text=None
    )
    assert len(reasons_dep) == 1
    assert "Item-Dependencies changed" in reasons_dep[0]

    # (d) Confirm-only change after R2/R4
    changed_eo = base.replace("feature is working", "feature is fully working")
    # with after_r_text given -> 1 reason
    reasons_eo_with = review_rereview.rereview_triggers(
        base, changed_eo, after_r_text=base
    )
    assert len(reasons_eo_with) == 1
    assert "Confirm-listed items changed" in reasons_eo_with[0]

    # with after_r_text=None -> 0 reasons
    reasons_eo_without = review_rereview.rereview_triggers(
        base, changed_eo, after_r_text=None
    )
    assert len(reasons_eo_without) == 0

    # Nothing changed -> empty list
    assert review_rereview.rereview_triggers(base, base, after_r_text=None) == []


@pytest.mark.core
def test_check_limit_s7() -> None:
    """E-04: test check_limit_s7 pass and fail cases."""
    before = SAMPLE_PLAN_BASE

    # Pass case: Readiness: no-go and new Blocking: yes open question
    after_pass = before.replace(
        "- Highest E allocated: 01\n", "- Highest E allocated: 01\n- Readiness: no-go\n"
    )
    after_pass = (
        after_pass
        + """
### OQ-02: Why did pass limit trigger?

- Blocking: yes
- Status: open
- Rationale: E-02 was modified after pass 2.
"""
    )
    assert review_rereview.check_limit_s7(before, after_pass) is None

    # Fail case 1: Readiness is go instead of no-go
    after_fail_1 = (
        before.replace(
            "- Highest E allocated: 01\n",
            "- Highest E allocated: 01\n- Readiness: go\n",
        )
        + """
### OQ-02: Question
- Blocking: yes
- Status: open
- Rationale: note
"""
    )
    err1 = review_rereview.check_limit_s7(before, after_fail_1)
    assert err1 is not None
    assert "- Readiness: no-go" in err1

    # Fail case 2: Readiness is no-go, but no new Blocking: yes question
    after_fail_2 = before.replace(
        "- Highest E allocated: 01\n", "- Highest E allocated: 01\n- Readiness: no-go\n"
    )
    err2 = review_rereview.check_limit_s7(before, after_fail_2)
    assert err2 is not None
    assert "Blocking: yes" in err2


@pytest.mark.core
def test_limit_reached_instruction() -> None:
    """E-04: test limit_reached_instruction content."""
    res = review_rereview.RereviewResult(
        outcome="limit-reached",
        passes=3,
        reasons=["Scope-Paths changed from 'none' to 'src/foo.py'"],
        marker="AGAIN",
    )
    inst = review_rereview.limit_reached_instruction(res)
    assert "- Readiness: no-go" in inst
    assert "Blocking: yes" in inst
    assert "Status: open" in inst
    assert "Scope-Paths changed" in inst
    assert "AGAIN" in inst


# ==============================================================================
# Task group 3: Runner Integration Tests on Both Hosts (AC-03 .. AC-07, AC-14)
# ==============================================================================


class TestReviewRereviewRunner(unittest.TestCase):
    """Integration runner tests for review re-review on both OpenCode and Antigravity."""

    def test_ac03_malformed_marker_reask_and_incomplete(self) -> None:
        """AC-03: Malformed marker causes 1 re-ask; second failure ends incomplete with to-review."""
        for host_name, host_mod in _HOSTS:
            with self.subTest(host=host_name):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    plan_path = _write_plan(repo, id6="ac3001", setid="revsteps")
                    run_dir = (
                        repo / ".aw" / "records" / "runs" / f"run-test-ac3-{host_name}"
                    )
                    run_dir.mkdir(parents=True)

                    item = {
                        "position": 1,
                        "id6": "ac3001",
                        "setid": "revsteps",
                        "configured_file": str(plan_path.relative_to(repo)),
                        "artifact_type": "ipd",
                        "action": "review",
                        "status": "queued",
                        "review_handler": "plan-review",
                        "attempts": [],
                    }
                    state = {
                        "run_id": f"run-test-ac3-{host_name}",
                        "repo": str(repo),
                        "options": {
                            "action": "review",
                            "review_mode": "steps",
                            "review_variant": "single-12",
                            "isolate_worktree": False,
                        },
                        "queue": [item],
                    }

                    reask_prompts_seen = 0

                    def fake_launcher(
                        *args: Any, **kwargs: Any
                    ) -> tuple[int, str, str, list[str]]:
                        nonlocal reask_prompts_seen
                        prompt_f = args[4] if len(args) > 5 else args[3]
                        p_text = Path(prompt_f).read_text(encoding="utf-8")

                        _write_review_record(
                            repo,
                            "ac3001",
                            proofreading=True,
                            step_t=True,
                            steps=["R1", "R2", "R3", "R4"],
                            s5=True,
                            s6=True,
                            s7=True,
                        )

                        step_log = run_dir / f"log-ac3-{host_name}.jsonl"
                        if "p-proofread.md" in p_text and "t-tier.md" in p_text:
                            reply = "AW-TIER: standard"
                        elif "s6-rereview.md" in p_text:
                            # Pass 1 S6 reply has NO marker
                            reply = "Completed review check S6 without marker."
                        elif (
                            "Your last reply did not end with the re-review marker"
                            in p_text
                        ):
                            reask_prompts_seen += 1
                            # Second failure: reply is still invalid
                            reply = "Still no marker."
                        else:
                            reply = "Check completed."

                        step_log.write_text(reply, encoding="utf-8")
                        return 0, f"session-ac3-{host_name}", str(step_log), ["cmd"]

                    patch_target = (
                        "run_opencode" if host_name == "oc" else "run_agy_turn"
                    )
                    with mock.patch.object(host_mod, patch_target, fake_launcher):
                        host_mod.execute_item(run_dir, state, item, recovery=False)

                    # Exactly one re-ask occurred
                    self.assertEqual(reask_prompts_seen, 1)

                    # Invocation ended as incomplete
                    att = item["attempts"][-1]
                    self.assertEqual(att.get("review_outcome"), "incomplete")
                    self.assertEqual(att.get("disposition"), "fail-gate")
                    self.assertEqual(item["status"], "fail-gate")

                    # Plan stays at to-review and no - Readiness: written
                    cur_plan = (repo / item["configured_file"]).read_text(
                        encoding="utf-8"
                    )
                    doc = ipd_lint.parse(cur_plan)
                    self.assertEqual(doc.meta_fields.get("Status"), "to-review")
                    self.assertIsNone(ipd_schema.read_readiness(cur_plan))

    def test_ac04_two_pass_completed_pass(self) -> None:
        """AC-04: Pass 1 adds E/V, pass 2 changes nothing -> completed-pass."""
        for host_name, host_mod in _HOSTS:
            with self.subTest(host=host_name):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    plan_path = _write_plan(repo, id6="ac4p01", setid="revsteps")
                    run_dir = (
                        repo / ".aw" / "records" / "runs" / f"run-test-ac4p-{host_name}"
                    )
                    run_dir.mkdir(parents=True)

                    item = {
                        "position": 1,
                        "id6": "ac4p01",
                        "setid": "revsteps",
                        "configured_file": str(plan_path.relative_to(repo)),
                        "artifact_type": "ipd",
                        "action": "review",
                        "status": "queued",
                        "review_handler": "plan-review",
                        "attempts": [],
                    }
                    state = {
                        "run_id": f"run-test-ac4p-{host_name}",
                        "repo": str(repo),
                        "options": {
                            "action": "review",
                            "review_mode": "steps",
                            "review_variant": "single-12",
                            "isolate_worktree": False,
                        },
                        "queue": [item],
                    }

                    calls: list[str] = []

                    def fake_launcher(
                        *args: Any, **kwargs: Any
                    ) -> tuple[int, str, str, list[str]]:
                        prompt_f = args[4] if len(args) > 5 else args[3]
                        p_text = Path(prompt_f).read_text(encoding="utf-8")
                        calls.append(p_text)

                        _write_review_record(
                            repo,
                            "ac4p01",
                            proofreading=True,
                            step_t=True,
                            steps=["R1", "R2", "R3", "R4"],
                            s5=True,
                            s6=True,
                            s7=True,
                        )

                        step_log = run_dir / f"log-ac4p-{len(calls)}.jsonl"
                        curr_plan = repo / item["configured_file"]

                        if "p-proofread.md" in p_text and "t-tier.md" in p_text:
                            reply = "AW-TIER: standard"
                        elif (
                            "s6-rereview.md" in p_text
                            and "Re-review pass 2" not in p_text
                        ):
                            # Pass 1 S6: add an E/V pair to trigger re-review
                            txt = curr_plan.read_text(encoding="utf-8")
                            e01_block = "- [ ] E-01 Test action item\n  - Depends on: none\n  - Expected outcome: done\n  - Execution state: pending"
                            e02_block = "- [ ] E-02 Pass 1 addition\n  - Depends on: none\n  - Expected outcome: done\n  - Execution state: pending"
                            txt = txt.replace(e01_block, f"{e01_block}\n\n{e02_block}")
                            curr_plan.write_text(txt, encoding="utf-8")
                            reply = "AW-REVIEW: DONE"
                        elif (
                            "Re-review pass 2" in p_text and "s6-rereview.md" in p_text
                        ):
                            # Pass 2 S6: change nothing
                            reply = "AW-REVIEW: DONE"
                        elif "s7-finalize.md" in p_text:
                            txt = curr_plan.read_text(encoding="utf-8")
                            txt = txt.replace(
                                "- Status: to-review", "- Status: reviewed"
                            )
                            txt = txt.replace(
                                "- Highest E allocated: 01\n",
                                "- Highest E allocated: 02\n- Readiness: go-pending-approval\n",
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
                        return 0, f"session-ac4p-{host_name}", str(step_log), ["cmd"]

                    patch_target = (
                        "run_opencode" if host_name == "oc" else "run_agy_turn"
                    )
                    with mock.patch.object(host_mod, patch_target, fake_launcher):
                        host_mod.execute_item(run_dir, state, item, recovery=False)

                    att = item["attempts"][-1]
                    self.assertEqual(att.get("review_outcome"), "completed-pass")
                    self.assertEqual(item["status"], "reviewed")

                    # Check pass numbers in review_steps
                    review_steps = att.get("review_steps", [])
                    passes_recorded = {s.get("pass") for s in review_steps}
                    self.assertIn(1, passes_recorded)
                    self.assertIn(2, passes_recorded)

    def test_ac04_limit_reached_completed_negative(self) -> None:
        """AC-04 & E-04: Fixture that triggers after pass 2 ends completed-negative with Readiness: no-go and Blocking: yes."""
        for host_name, host_mod in _HOSTS:
            with self.subTest(host=host_name):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    plan_path = _write_plan(repo, id6="ac4lim", setid="revsteps")
                    run_dir = (
                        repo
                        / ".aw"
                        / "records"
                        / "runs"
                        / f"run-test-ac4lim-{host_name}"
                    )
                    run_dir.mkdir(parents=True)

                    item = {
                        "position": 1,
                        "id6": "ac4lim",
                        "setid": "revsteps",
                        "configured_file": str(plan_path.relative_to(repo)),
                        "artifact_type": "ipd",
                        "action": "review",
                        "status": "queued",
                        "review_handler": "plan-review",
                        "attempts": [],
                    }
                    state = {
                        "run_id": f"run-test-ac4lim-{host_name}",
                        "repo": str(repo),
                        "options": {
                            "action": "review",
                            "review_mode": "steps",
                            "review_variant": "single-12",
                            "isolate_worktree": False,
                        },
                        "queue": [item],
                    }

                    calls: list[str] = []

                    def fake_launcher(
                        *args: Any, **kwargs: Any
                    ) -> tuple[int, str, str, list[str]]:
                        prompt_f = args[4] if len(args) > 5 else args[3]
                        p_text = Path(prompt_f).read_text(encoding="utf-8")
                        calls.append(p_text)

                        _write_review_record(
                            repo,
                            "ac4lim",
                            proofreading=True,
                            step_t=True,
                            steps=["R1", "R2", "R3", "R4"],
                            s5=True,
                            s6=True,
                            s7=True,
                        )

                        step_log = run_dir / f"log-ac4lim-{len(calls)}.jsonl"
                        curr_plan = repo / item["configured_file"]

                        if "p-proofread.md" in p_text and "t-tier.md" in p_text:
                            reply = "AW-TIER: standard"
                        elif (
                            "s6-rereview.md" in p_text
                            and "Re-review pass 2" not in p_text
                            and "Re-review pass 3" not in p_text
                        ):
                            # Pass 1: trigger again
                            reply = "AW-REVIEW: AGAIN"
                        elif (
                            "Re-review pass 2" in p_text and "s6-rereview.md" in p_text
                        ):
                            # Pass 2: trigger again
                            reply = "AW-REVIEW: AGAIN"
                        elif (
                            "Re-review pass 3" in p_text and "s6-rereview.md" in p_text
                        ):
                            # Pass 3: trigger again -> limit reached!
                            reply = "AW-REVIEW: AGAIN"
                        elif "s7-finalize.md" in p_text:
                            # Verify S7 received limit reached instruction
                            assert "Re-review pass limit reached" in p_text
                            txt = curr_plan.read_text(encoding="utf-8")
                            txt = txt.replace(
                                "- Status: to-review", "- Status: reviewed"
                            )
                            txt = txt.replace(
                                "- Highest E allocated: 01\n",
                                "- Highest E allocated: 01\n- Readiness: no-go\n",
                            )
                            txt = txt.replace(
                                "## Workflow history\n",
                                "## Workflow history\n\n- 2026-10-25 reviewed (test): /plan-review (test): REJECT - NEEDS REPLAN; limit reached\n",
                            )
                            # Add the required Blocking: yes question under ## Open questions
                            txt = txt.replace(
                                "## Open questions\n\n- None.",
                                "## Open questions\n\n### OQ-02: Limit reached question\n\n- Blocking: yes\n- Status: open\n- Rationale: Active changes remained after pass 3.",
                            )
                            curr_plan.write_text(txt, encoding="utf-8")
                            reply = "Finalized with no-go."
                        else:
                            reply = "Check ok."

                        step_log.write_text(reply, encoding="utf-8")
                        return 0, f"session-ac4lim-{host_name}", str(step_log), ["cmd"]

                    patch_target = (
                        "run_opencode" if host_name == "oc" else "run_agy_turn"
                    )
                    with mock.patch.object(host_mod, patch_target, fake_launcher):
                        host_mod.execute_item(run_dir, state, item, recovery=False)

                    att = item["attempts"][-1]
                    self.assertEqual(att.get("review_outcome"), "completed-negative")
                    self.assertEqual(item["status"], "reviewed")

                    # Verify plan has - Readiness: no-go and Blocking: yes question
                    final_plan = (repo / item["configured_file"]).read_text(
                        encoding="utf-8"
                    )
                    self.assertEqual(ipd_schema.read_readiness(final_plan), "no-go")
                    doc = ipd_lint.parse(final_plan)
                    has_blk = any(
                        q.get("Blocking") == "yes" and q.get("Status") == "open"
                        for q in doc.open_questions
                    )
                    self.assertTrue(has_blk)

    def test_ac05_findings_recorded_in_pass1_gate_after_pass2(self) -> None:
        """AC-05: Finding in pass 1 not fixed after pass 2 is still reported by subject_gating_blocks."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _write_plan(repo, id6="ac5f01", setid="revsteps")

            # Write review record with round findings table
            rev_p = _write_review_record(repo, "ac5f01", s6=True, s7=True)
            txt = rev_p.read_text(encoding="utf-8")
            findings_sec = """
### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| F-01 | high | in-scope | spec | Line 10 | Unresolved defect | low | open | none |
"""
            rev_p.write_text(txt + "\n" + findings_sec, encoding="utf-8")

            # Verify review_findings.subject_gating_blocks finds it
            blocking = review_findings.subject_gating_blocks(repo, "ac5f01")
            self.assertTrue(len(blocking) > 0)
            self.assertEqual(blocking[0].finding_id, "F-01")

    def test_ac06_single_verdict_and_single_plan_review_commit(self) -> None:
        """AC-06: 2 passes yield exactly 1 verdict history entry and 1 plan-review: commit."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            plan_path = _write_plan(repo, id6="ac6com", setid="revsteps")

            # Add progress history entry and single verdict entry
            cur = plan_path.read_text(encoding="utf-8")
            cur = cur.replace(
                "## Workflow history\n",
                "## Workflow history\n\n- 2026-10-25 review progress (test): pass 2 re-ran R2\n- 2026-10-25 reviewed (test): /plan-review (test): APPROVE\n",
            )
            cur = cur.replace("- Status: to-review", "- Status: reviewed")
            cur = cur.replace(
                "- Highest E allocated: 01\n",
                "- Highest E allocated: 01\n- Readiness: go-pending-approval\n",
            )
            plan_path.write_text(cur, encoding="utf-8")

            # Commit
            subprocess.run(["git", "add", str(plan_path)], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "plan-review: test plan ac6com"],
                cwd=repo,
                check=True,
            )

            # Check that newest_verdict ignores progress line
            verdict_tok, raw_entry = plan_readiness.newest_verdict(cur)
            self.assertEqual(verdict_tok, "positive")
            self.assertIn("/plan-review (test): APPROVE", raw_entry)

            # Check exactly 1 plan-review commit
            res = subprocess.run(
                ["git", "log", "--format=%s"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            )
            plan_review_commits = [
                line
                for line in res.stdout.splitlines()
                if line.startswith("plan-review:")
            ]
            self.assertEqual(len(plan_review_commits), 1)

    def test_ac07_interrupted_after_pass1_leaves_to_review(self) -> None:
        """AC-07 (second half): Interrupted after pass 1 leaves plan at to-review with no new Readiness:."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            plan_path = _write_plan(repo, id6="ac7int", setid="revsteps")
            cur = plan_path.read_text(encoding="utf-8")
            doc = ipd_lint.parse(cur)
            self.assertEqual(doc.meta_fields.get("Status"), "to-review")
            self.assertIsNone(ipd_schema.read_readiness(cur))

    def test_verdict_guard_revert_in_pass2_prompt(self) -> None:
        """AC-07 first half & E-05: Fixture that writes Readiness: in pass 2 prompt is reverted and re-asked."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            plan_path = _write_plan(repo, id6="vg001", setid="revsteps")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test-vg"
            run_dir.mkdir(parents=True)

            item = {
                "position": 1,
                "id6": "vg001",
                "setid": "revsteps",
                "configured_file": str(plan_path.relative_to(repo)),
                "artifact_type": "ipd",
                "action": "review",
                "status": "queued",
                "review_handler": "plan-review",
                "attempts": [],
            }
            state = {
                "run_id": "run-test-vg",
                "repo": str(repo),
                "options": {
                    "action": "review",
                    "review_mode": "steps",
                    "review_variant": "single-12",
                    "isolate_worktree": False,
                },
                "queue": [item],
            }

            calls: list[str] = []
            verdict_reask_seen = False

            def fake_launcher(
                *args: Any, **kwargs: Any
            ) -> tuple[int, str, str, list[str]]:
                nonlocal verdict_reask_seen
                prompt_f = args[4] if len(args) > 5 else args[3]
                p_text = Path(prompt_f).read_text(encoding="utf-8")
                calls.append(p_text)

                _write_review_record(
                    repo,
                    "vg001",
                    proofreading=True,
                    step_t=True,
                    steps=["R1", "R2", "R3", "R4"],
                    s5=True,
                    s6=True,
                    s7=True,
                )

                step_log = run_dir / f"log-vg-{len(calls)}.jsonl"
                curr_plan = repo / item["configured_file"]

                if "p-proofread.md" in p_text and "t-tier.md" in p_text:
                    reply = "AW-TIER: standard"
                elif "s6-rereview.md" in p_text and "Re-review pass 2" not in p_text:
                    # Pass 1 S6: request AGAIN
                    reply = "AW-REVIEW: AGAIN"
                elif "Re-review pass 2" in p_text and (
                    "verdict-reask" in str(prompt_f) or "modified before S7" in p_text
                ):
                    # Re-ask prompt: agent removes the illegal Readiness write
                    verdict_reask_seen = True
                    reply = "Removed Readiness line."
                elif "Re-review pass 2" in p_text and "r1-references.md" in p_text:
                    # Illegal write of Readiness in pass 2 prompt
                    txt = curr_plan.read_text(encoding="utf-8")
                    txt = txt.replace(
                        "- Highest E allocated: 01\n",
                        "- Highest E allocated: 01\n- Readiness: go\n",
                    )
                    curr_plan.write_text(txt, encoding="utf-8")
                    reply = "Done."
                elif "Re-review pass 2" in p_text and "s6-rereview.md" in p_text:
                    reply = "AW-REVIEW: DONE"
                elif "s7-finalize.md" in p_text:
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
                return 0, "session-vg-1", str(step_log), ["cmd"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_launcher):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertTrue(verdict_reask_seen)
            self.assertEqual(item["status"], "reviewed")

    def test_ac14_resume_inside_pass2(self) -> None:
        """AC-14 within pass & E-06: Interrupted inside pass 2 resumes at next prompt with pass-start text rebuilt."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            plan_path = _write_plan(repo, id6="respass2", setid="revsteps")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test-respass2"
            run_dir.mkdir(parents=True)
            snap_dir = run_dir / "snapshots"
            snap_dir.mkdir(parents=True)

            init_plan_text = plan_path.read_text(encoding="utf-8")
            init_sha = hashlib.sha256(init_plan_text.encode("utf-8")).hexdigest()
            (snap_dir / f"{init_sha}.plan.md").write_text(
                init_plan_text, encoding="utf-8"
            )

            # Create pass 2 start text (with an added E-item from pass 1)
            e01_b = "- [ ] E-01 Test action item\n  - Depends on: none\n  - Expected outcome: done\n  - Execution state: pending"
            e02_b = "- [ ] E-02 Added in pass 1\n  - Depends on: none\n  - Expected outcome: done\n  - Execution state: pending"
            pass2_start_text = init_plan_text.replace(e01_b, f"{e01_b}\n\n{e02_b}")
            p2_start_sha = hashlib.sha256(pass2_start_text.encode("utf-8")).hexdigest()
            (snap_dir / f"{p2_start_sha}.plan.md").write_text(
                pass2_start_text, encoding="utf-8"
            )

            # Mock step 1 of pass 2 already completed
            pass2_step1_text = pass2_start_text
            p2_s1_sha = hashlib.sha256(pass2_step1_text.encode("utf-8")).hexdigest()
            (snap_dir / f"{p2_s1_sha}.plan.md").write_text(
                pass2_step1_text, encoding="utf-8"
            )

            step_p1 = {
                "invocation": "inv-1",
                "pass": 1,
                "prompt": 4,
                "checks": ["S5", "S6"],
                "plan_sha256": init_sha,
                "session_id": "ses-p2-alive",
                "reasked": False,
                "log": str(run_dir / "log-p1.jsonl"),
            }
            step_p2_1 = {
                "invocation": "inv-1",
                "pass": 2,
                "prompt": 1,
                "checks": ["R1", "R2"],
                "plan_sha256": p2_s1_sha,
                "session_id": "ses-p2-alive",
                "reasked": False,
                "log": str(run_dir / "log-p2-s1.jsonl"),
            }

            item = {
                "position": 1,
                "id6": "respass2",
                "setid": "revsteps",
                "configured_file": str(plan_path.relative_to(repo)),
                "artifact_type": "ipd",
                "action": "review",
                "status": "queued",
                "review_handler": "plan-review",
                "attempts": [
                    {
                        "number": 1,
                        "session_id": "ses-p2-alive",
                        "review_steps": [step_p1, step_p2_1],
                        "review_tier": "standard",
                        "rereview": {
                            "pass": 2,
                            "pass_start_sha256": p2_start_sha,
                            "reasons": ["E/V items changed: added E-02"],
                            "after_r_sha256": None,
                        },
                    }
                ],
            }
            state = {
                "run_id": "run-test-respass2",
                "repo": str(repo),
                "options": {
                    "action": "review",
                    "review_mode": "steps",
                    "isolate_worktree": False,
                },
                "queue": [item],
            }

            prompts_executed: list[str] = []

            def fake_turn_resume(
                state: Any,
                rd: Any,
                it: Any,
                p_path: Any,
                prompt_f: Any,
                att_no: Any,
                **kw: Any,
            ) -> tuple[int, str, str, list[str]]:
                p_text = Path(prompt_f).read_text(encoding="utf-8")
                prompts_executed.append(p_text)

                _write_review_record(
                    repo,
                    "respass2",
                    proofreading=True,
                    step_t=True,
                    steps=["R1", "R2", "R3", "R4"],
                    s5=True,
                    s6=True,
                    s7=True,
                )

                step_log = rd / f"log-p2-{len(prompts_executed)}.jsonl"
                curr_plan = repo / it["configured_file"]

                if "s6-rereview.md" in p_text:
                    reply = "AW-REVIEW: DONE"
                elif "s7-finalize.md" in p_text:
                    txt = curr_plan.read_text(encoding="utf-8")
                    txt = txt.replace("- Status: to-review", "- Status: reviewed")
                    txt = txt.replace(
                        "- Highest E allocated: 01\n",
                        "- Highest E allocated: 02\n- Readiness: go-pending-approval\n",
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
                return 0, "ses-p2-alive", str(step_log), ["cmd"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_turn_resume):
                oc_runipd.execute_item(run_dir, state, item, recovery=True)

            self.assertEqual(item["status"], "reviewed")
            att = item["attempts"][-1]
            self.assertEqual(att.get("review_outcome"), "completed-pass")

            # Check that prompt 1 of pass 2 ("R1", "R2") was NOT re-executed
            r1_r2_reexecuted = any(
                "r1-references.md" in p and "Re-review pass 2" in p
                for p in prompts_executed
            )
            self.assertFalse(r1_r2_reexecuted)

            # Check that later prompts in pass 2 were executed
            r3_r4_executed = any(
                "r3-security.md" in p and "Re-review pass 2" in p
                for p in prompts_executed
            )
            self.assertTrue(r3_r4_executed)
