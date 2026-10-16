"""Regression and integration tests for IPD review staleness advisory (IPD ygngc2).

Tests the pure predicate, bulk git index resolver, and all four advisory surfaces:
1. Pure predicate: review_staleness_from_texts
2. Bulk git index: review_staleness_index
3. check.ipd-review-may-be-stale diagnostic in `aw check plans`
4. Passing advisory in `aw ipd lint`
5. Non-refusing warning in `aw ipd set approved` (human mode stderr and agent mode warnings)
6. `review_stale` field and `[stale-review]` board marker in `aw attention` (schema_version 5)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from agent_workflows import artifact_core
from agent_workflows import check_engine
from agent_workflows.plan_readiness import (
    review_staleness_from_texts,
    review_staleness_index,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

BASE_PLAN_TEMPLATE = """# IPD: Test {id6}

- Date: 2026-10-15
- Kind: child
- Concern: Test concern for {id6}.
- Scope: Test scope for {id6}.
- Status: {status}
- Work-Kind: chore
- Priority: medium
- Set: test
- Order: 1
- Id: {id6}
- Scope-Paths: README.md
- Highest E allocated: 01
- Author: test
- Item-Dependencies: none
{readiness_field}
## Workflow history

{history_entry}

## Goal
Goal for {id6}.

## Detailed Implementation Checklist (TODO)
### Task group 1: work
- [ ] E-01 Work item for {id6}
{e01_extra}  - Depends on: none
  - Expected outcome: done
  - Execution state: pending

## Project conventions discovered (Step 0)
None.

## Findings
None.
{findings_extra}
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
{open_questions}
## Validation and cross-check (verify before reporting done)
- [ ] V-01 validates E-01
  - Required evidence: check.
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- Size assessment: standard
- Cohesion rationale: not required
"""


def _make_plan_text(
    id6: str = "test01",
    status: str = "reviewed",
    e01_extra: str = "",
    findings_extra: str = "",
    open_questions: str = "None.\n",
    readiness: str | None = None,
) -> str:
    if readiness is None:
        readiness_field = (
            "- Readiness: go-pending-approval\n"
            if status in ("reviewed", "approved")
            else ""
        )
    elif readiness:
        readiness_field = f"- Readiness: {readiness}\n"
    else:
        readiness_field = ""

    if status in ("reviewed", "approved"):
        history_entry = f"- 2026-10-15 {status} (reviewer): /plan-review APPROVE."
    else:
        history_entry = f"- 2026-10-15 {status} (author): created."

    return BASE_PLAN_TEMPLATE.format(
        id6=id6,
        status=status,
        readiness_field=readiness_field,
        history_entry=history_entry,
        e01_extra=e01_extra,
        findings_extra=findings_extra,
        open_questions=open_questions,
    )


class TestPurePredicate(unittest.TestCase):
    """Test pure predicate review_staleness_from_texts."""

    def test_answered_blocking_question(self):
        oq_open = (
            "### OQ-01: Should we do X?\n"
            "- Blocking: yes\n"
            "- Status: open\n"
            "- Owner: author\n"
            "- Resolution or deferral rationale: pending.\n"
        )
        oq_resolved = (
            "### OQ-01: Should we do X?\n"
            "- Blocking: yes\n"
            "- Status: resolved\n"
            "- Owner: author\n"
            "- Resolution or deferral rationale: resolved 2026-10-15.\n"
        )
        t_rev = _make_plan_text(open_questions=oq_open)
        t_cur = _make_plan_text(open_questions=oq_resolved)

        res = review_staleness_from_texts(t_rev, t_cur, "a" * 40)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertEqual(res.reasons, ("answered-blocking-question",))
        self.assertEqual(res.reviewed_commit, "a" * 40)
        self.assertEqual(res.question_ids, ("OQ-01",))

    def test_substantive_edit_frozen_region(self):
        t_rev = _make_plan_text(e01_extra="")
        t_cur = _make_plan_text(e01_extra="  continuation line requirement details\n")

        res = review_staleness_from_texts(t_rev, t_cur, "b" * 40)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertEqual(res.reasons, ("substantive-edit",))
        self.assertEqual(res.reviewed_commit, "b" * 40)
        self.assertEqual(res.question_ids, ())

    def test_both_reasons(self):
        oq_open = (
            "### OQ-01: Should we do X?\n"
            "- Blocking: yes\n"
            "- Status: open\n"
            "- Owner: author\n"
            "- Resolution or deferral rationale: pending.\n"
        )
        oq_resolved = (
            "### OQ-01: Should we do X?\n"
            "- Blocking: yes\n"
            "- Status: resolved\n"
            "- Owner: author\n"
            "- Resolution or deferral rationale: resolved.\n"
        )
        t_rev = _make_plan_text(open_questions=oq_open, e01_extra="")
        t_cur = _make_plan_text(
            open_questions=oq_resolved, e01_extra="  continuation line extra\n"
        )

        res = review_staleness_from_texts(t_rev, t_cur, "c" * 40)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertEqual(
            res.reasons, ("answered-blocking-question", "substantive-edit")
        )
        self.assertEqual(res.question_ids, ("OQ-01",))

    def test_non_blocking_oq_answered_is_not_stale(self):
        oq_open = (
            "### OQ-01: Non-blocking question\n"
            "- Blocking: no\n"
            "- Status: open\n"
            "- Owner: author\n"
            "- Resolution or deferral rationale: pending.\n"
        )
        oq_resolved = (
            "### OQ-01: Non-blocking question\n"
            "- Blocking: no\n"
            "- Status: resolved\n"
            "- Owner: author\n"
            "- Resolution or deferral rationale: resolved.\n"
        )
        t_rev = _make_plan_text(open_questions=oq_open)
        t_cur = _make_plan_text(open_questions=oq_resolved)

        res = review_staleness_from_texts(t_rev, t_cur, "d" * 40)
        self.assertIsNone(res)

    def test_non_substantive_edits_not_stale(self):
        # 1. Workflow history addition
        t_rev = _make_plan_text()
        t_cur_hist = t_rev.replace(
            "## Workflow history\n\n- 2026-10-15 reviewed (reviewer): /plan-review APPROVE.\n",
            "## Workflow history\n\n- 2026-10-15 reviewed (reviewer): /plan-review APPROVE.\n- 2026-10-16 note (human): note.\n",
        )
        self.assertIsNone(review_staleness_from_texts(t_rev, t_cur_hist, "e" * 40))

        # 2. Checkbox-only edit
        t_cur_cb = t_rev.replace("- [ ] E-01", "- [x] E-01")
        self.assertIsNone(review_staleness_from_texts(t_rev, t_cur_cb, "e" * 40))

        # 3. Execution state-only edit
        t_cur_st = t_rev.replace(
            "Execution state: pending", "Execution state: performed"
        )
        self.assertIsNone(review_staleness_from_texts(t_rev, t_cur_st, "e" * 40))

        # 4. Findings-only edit
        t_cur_find = _make_plan_text(findings_extra="| F-1 | Finding | Evidence |\n")
        self.assertIsNone(review_staleness_from_texts(t_rev, t_cur_find, "e" * 40))

        # 5. Exact same text
        self.assertIsNone(review_staleness_from_texts(t_rev, t_rev, "e" * 40))


class TestBulkIndexResolver(unittest.TestCase):
    """Test review_staleness_index against a git repo and non-git directory."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aw_test_staleness_index_")
        self.root = Path(self.temp_dir)
        subprocess.run(
            ["git", "init", "-b", "main", str(self.root)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test Author"], cwd=self.root, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.root,
            check=True,
        )

        self.pending_dir = self.root / ".aw" / "records" / "plans" / "pending"
        self.pending_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_stale_plan_detected_and_options(self):
        # Plan 1: reviewed with open blocking OQ
        oq_open = (
            "### OQ-01: Blocking question\n"
            "- Blocking: yes\n"
            "- Status: open\n"
            "- Owner: author\n"
            "- Resolution or deferral rationale: pending.\n"
        )
        plan1_path = self.pending_dir / "20261015-test-01-stale1-test-plan.ipd.md"
        plan1_path.write_text(
            _make_plan_text(id6="stale1", status="reviewed", open_questions=oq_open)
        )

        # Plan 2: to-review plan (should be omitted)
        plan2_path = self.pending_dir / "20261015-test-02-torev1-test-plan.ipd.md"
        plan2_path.write_text(
            _make_plan_text(id6="torev1", status="to-review", open_questions=oq_open)
        )

        # Commit initial versions of plan1 and plan2 with plan-review: subject prefix
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "plan-review: harden stale1 and torev1"],
            cwd=self.root,
            check=True,
        )

        # Plan 3: reviewed but commit subject does NOT start with 'plan-review:'
        plan3_path = self.pending_dir / "20261015-test-03-norev1-test-plan.ipd.md"
        plan3_path.write_text(
            _make_plan_text(id6="norev1", status="reviewed", open_questions=oq_open)
        )
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: add unreviewed plan norev1"],
            cwd=self.root,
            check=True,
        )

        # Now answer OQ-01 in plan1 and plan3
        oq_resolved = (
            "### OQ-01: Blocking question\n"
            "- Blocking: yes\n"
            "- Status: resolved\n"
            "- Owner: author\n"
            "- Resolution or deferral rationale: resolved.\n"
        )
        plan1_path.write_text(
            _make_plan_text(id6="stale1", status="reviewed", open_questions=oq_resolved)
        )
        plan3_path.write_text(
            _make_plan_text(id6="norev1", status="reviewed", open_questions=oq_resolved)
        )
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "resolve OQs"], cwd=self.root, check=True
        )

        # Query index
        idx = review_staleness_index(self.root, [plan1_path, plan2_path, plan3_path])

        # plan1 must be flagged
        key1 = ".aw/records/plans/pending/20261015-test-01-stale1-test-plan.ipd.md"
        self.assertIn(key1, idx)
        self.assertEqual(idx[key1].reasons, ("answered-blocking-question",))
        self.assertEqual(idx[key1].question_ids, ("OQ-01",))

        # plan2 (to-review) must be omitted
        key2 = ".aw/records/plans/pending/20261015-test-02-torev1-test-plan.ipd.md"
        self.assertNotIn(key2, idx)

        # plan3 (no plan-review commit) must be omitted
        key3 = ".aw/records/plans/pending/20261015-test-03-norev1-test-plan.ipd.md"
        self.assertNotIn(key3, idx)

    def test_renamed_plan_omitted(self):
        # A plan renamed since review has no plan-review: commit under its current path
        # without --follow, so it is omitted.
        oq_open = (
            "### OQ-01: Blocking question\n"
            "- Blocking: yes\n"
            "- Status: open\n"
            "- Owner: author\n"
            "- Resolution or deferral rationale: pending.\n"
        )
        old_path = self.pending_dir / "20261015-test-01-renam1-old-name.ipd.md"
        old_path.write_text(
            _make_plan_text(id6="renam1", status="reviewed", open_questions=oq_open)
        )
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "plan-review: harden renam1"],
            cwd=self.root,
            check=True,
        )

        new_path = self.pending_dir / "20261015-test-01-renam1-new-name.ipd.md"
        subprocess.run(
            ["git", "mv", str(old_path), str(new_path)], cwd=self.root, check=True
        )

        # Resolve OQ
        oq_resolved = (
            "### OQ-01: Blocking question\n"
            "- Blocking: yes\n"
            "- Status: resolved\n"
            "- Owner: author\n"
            "- Resolution or deferral rationale: resolved.\n"
        )
        new_path.write_text(
            _make_plan_text(id6="renam1", status="reviewed", open_questions=oq_resolved)
        )
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "rename and resolve"], cwd=self.root, check=True
        )

        idx = review_staleness_index(self.root, [new_path])
        key = ".aw/records/plans/pending/20261015-test-01-renam1-new-name.ipd.md"
        self.assertNotIn(key, idx)

    def test_non_git_directory_returns_empty_dict(self):
        with tempfile.TemporaryDirectory() as td:
            non_git = Path(td)
            plan_path = (
                non_git
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20261015-test-01-nogit1-test.ipd.md"
            )
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(_make_plan_text(id6="nogit1", status="reviewed"))
            idx = review_staleness_index(non_git, [plan_path])
            self.assertEqual(idx, {})


class TestCliSurfaces(unittest.TestCase):
    """Subprocess CLI tests for aw check plans, aw ipd lint, aw ipd set approved, aw attention."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aw_test_cli_surfaces_")
        self.root = Path(self.temp_dir)
        subprocess.run(
            ["git", "init", "-b", "main", str(self.root)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test Author"], cwd=self.root, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.root,
            check=True,
        )

        self.pending_dir = self.root / ".aw" / "records" / "plans" / "pending"
        self.pending_dir.mkdir(parents=True, exist_ok=True)

        self.env = dict(os.environ)
        self.env["PYTHONPATH"] = str(REPO_ROOT)
        self.env["AW_NO_REEXEC"] = "1"

        # Create two plans:
        # stale1: reviewed with open blocking OQ, then OQ resolved after review commit
        # twin01: non-stale twin, reviewed and untouched after review commit
        oq_open = (
            "### OQ-01: Blocking question\n"
            "- Blocking: yes\n"
            "- Status: open\n"
            "- Owner: author\n"
            "- Resolution or deferral rationale: pending.\n"
        )
        self.stale_path = self.pending_dir / "20261015-test-01-stale1-test-stale.ipd.md"
        self.stale_path.write_text(
            _make_plan_text(id6="stale1", status="reviewed", open_questions=oq_open)
        )

        self.twin_path = self.pending_dir / "20261015-test-02-twin01-test-twin.ipd.md"
        self.twin_path.write_text(
            _make_plan_text(id6="twin01", status="reviewed", open_questions="None.\n")
        )

        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "plan-review: harden stale1 and twin01"],
            cwd=self.root,
            check=True,
        )

        # Now answer OQ in stale1 and commit
        oq_resolved = (
            "### OQ-01: Blocking question\n"
            "- Blocking: yes\n"
            "- Status: resolved\n"
            "- Owner: author\n"
            "- Resolution or deferral rationale: resolved 2026-10-15.\n"
        )
        self.stale_path.write_text(
            _make_plan_text(id6="stale1", status="reviewed", open_questions=oq_resolved)
        )
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "resolve OQ in stale1"], cwd=self.root, check=True
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_check_plans_agent_diagnostic_and_contrastive_pair(self):
        # 1. Rule registration severity is info
        spec = check_engine.rule_spec("check.ipd-review-may-be-stale")
        self.assertEqual(spec.severity, "info")

        # 2. Run aw check plans --agent
        cmd = [sys.executable, "-m", "agent_workflows", "check", "plans", "--agent"]
        res = subprocess.run(
            cmd, cwd=self.root, env=self.env, capture_output=True, text=True
        )
        self.assertEqual(
            res.returncode, 0, f"check plans failed: {res.stderr}\nstdout: {res.stdout}"
        )

        # Parse json result
        res_data = json.loads(res.stdout)
        self.assertEqual(res_data.get("outcome"), "conforms")
        diags = res_data.get("diagnostics", [])

        stale_diags = [
            d for d in diags if d.get("rule") == "check.ipd-review-may-be-stale"
        ]
        self.assertTrue(len(stale_diags) >= 1)
        stale_diag = stale_diags[0]
        self.assertIn("stale1", stale_diag.get("location", ""))

        # Check recovery command via --json
        cmd_json = [sys.executable, "-m", "agent_workflows", "check", "plans", "--json"]
        res_json = subprocess.run(
            cmd_json, cwd=self.root, env=self.env, capture_output=True, text=True
        )
        self.assertEqual(res_json.returncode, 0)
        data_json = json.loads(res_json.stdout)
        json_stale = [
            d
            for d in data_json.get("diagnostics", [])
            if d.get("rule") == "check.ipd-review-may-be-stale"
        ]
        self.assertTrue(len(json_stale) >= 1)
        self.assertEqual(json_stale[0].get("fix"), "aw oc review stale1 --yes")

        # 3. Contrastive pair on artifact_core.drift_exit_code
        from agent_workflows.artifact_core import Drift

        real_drift = [
            Drift(
                rule=d.get("rule", ""),
                location=d.get("location", ""),
                detail=d.get("detail", ""),
                severity="info",
            )
            for d in diags
        ]
        drift_without_stale = [
            d for d in real_drift if d.rule != "check.ipd-review-may-be-stale"
        ]

        rc_with = artifact_core.drift_exit_code(real_drift)
        rc_without = artifact_core.drift_exit_code(drift_without_stale)
        self.assertEqual(rc_with, 0)
        self.assertEqual(rc_without, 0)
        self.assertEqual(rc_with, rc_without)

    def test_ipd_lint_author_phase_advisory(self):
        # 1. Programmatic lint_file API
        from agent_workflows import ipd_lint

        lint_res = ipd_lint.lint_file(self.stale_path, checkpoint="author")
        self.assertEqual(lint_res.disposition, "conforming")
        advs = [
            a for a in lint_res.advisories if a.code == "check.ipd-review-may-be-stale"
        ]
        self.assertTrue(len(advs) >= 1)
        self.assertIn("aw oc review stale1 --yes", advs[0].message)

        # 2. CLI subprocess in agent mode
        cmd = [
            sys.executable,
            "-m",
            "agent_workflows",
            "ipd",
            "lint",
            str(self.stale_path),
            "--phase",
            "author",
            "--agent",
            "--verbose",
        ]
        res = subprocess.run(
            cmd, cwd=self.root, env=self.env, capture_output=True, text=True
        )
        self.assertEqual(
            res.returncode, 0, f"ipd lint failed: {res.stderr}\nstdout: {res.stdout}"
        )

        data = json.loads(res.stdout)
        self.assertEqual(data.get("exit"), 0)
        self.assertIn(data.get("outcome"), ("clean", "conforms"))
        diags = data.get("diagnostics", [])
        stale_adv = [
            d for d in diags if d.get("rule") == "check.ipd-review-may-be-stale"
        ]
        self.assertTrue(len(stale_adv) >= 1)
        self.assertIn("aw oc review stale1 --yes", stale_adv[0].get("detail", ""))

    def test_ipd_set_approved_human_and_agent_modes(self):
        # Human mode on stale1: exits 0, stderr carries warning, status becomes approved
        cmd_stale = [
            sys.executable,
            "-m",
            "agent_workflows",
            "ipd",
            "set",
            "approved",
            "stale1",
            "--by-human",
        ]
        res_stale = subprocess.run(
            cmd_stale, cwd=self.root, env=self.env, capture_output=True, text=True
        )
        self.assertEqual(
            res_stale.returncode, 0, f"set approved failed: {res_stale.stderr}"
        )
        self.assertIn("review may be stale for stale1", res_stale.stderr)
        self.assertIn("aw oc review stale1 --yes", res_stale.stderr)
        self.assertIn("- Status: approved", self.stale_path.read_text())

        # Human mode on non-stale twin01: exits 0, stderr does NOT carry warning, status becomes approved
        cmd_twin = [
            sys.executable,
            "-m",
            "agent_workflows",
            "ipd",
            "set",
            "approved",
            "twin01",
            "--by-human",
        ]
        res_twin = subprocess.run(
            cmd_twin, cwd=self.root, env=self.env, capture_output=True, text=True
        )
        self.assertEqual(
            res_twin.returncode, 0, f"set approved twin failed: {res_twin.stderr}"
        )
        self.assertNotIn("review may be stale", res_twin.stderr)
        self.assertIn("- Status: approved", self.twin_path.read_text())

        # Agent mode on another stale plan (stale2):
        oq_open = (
            "### OQ-01: Blocking question\n"
            "- Blocking: yes\n"
            "- Status: open\n"
            "- Owner: author\n"
            "- Resolution or deferral rationale: pending.\n"
        )
        stale2_path = self.pending_dir / "20261015-test-03-stale2-test-stale2.ipd.md"
        stale2_path.write_text(
            _make_plan_text(id6="stale2", status="reviewed", open_questions=oq_open)
        )
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "plan-review: harden stale2"],
            cwd=self.root,
            check=True,
        )

        oq_resolved = (
            "### OQ-01: Blocking question\n"
            "- Blocking: yes\n"
            "- Status: resolved\n"
            "- Owner: author\n"
            "- Resolution or deferral rationale: resolved.\n"
        )
        stale2_path.write_text(
            _make_plan_text(id6="stale2", status="reviewed", open_questions=oq_resolved)
        )
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "resolve OQ in stale2"], cwd=self.root, check=True
        )

        cmd_agent = [
            sys.executable,
            "-m",
            "agent_workflows",
            "ipd",
            "set",
            "approved",
            "stale2",
            "--by-human",
            "--agent",
            "--verbose",
            "--yes",
        ]
        res_agent = subprocess.run(
            cmd_agent, cwd=self.root, env=self.env, capture_output=True, text=True
        )
        self.assertEqual(
            res_agent.returncode,
            0,
            f"agent set approved failed: {res_agent.stderr}\nstdout: {res_agent.stdout}",
        )
        agent_data = json.loads(res_agent.stdout)
        diags = agent_data.get("diagnostics", [])
        stale_diags = [
            d for d in diags if "review may be stale for stale2" in d.get("detail", "")
        ]
        self.assertTrue(len(stale_diags) >= 1)
        self.assertIn("- Status: approved", stale2_path.read_text())

    def test_attention_format_json_and_board(self):
        # 1. aw attention --format json
        cmd_json = [
            sys.executable,
            "-m",
            "agent_workflows",
            "attention",
            "--format",
            "json",
        ]
        res_json = subprocess.run(
            cmd_json, cwd=self.root, env=self.env, capture_output=True, text=True
        )
        self.assertEqual(
            res_json.returncode, 0, f"attention json failed: {res_json.stderr}"
        )
        data = json.loads(res_json.stdout)
        self.assertEqual(data.get("schema_version"), 5)

        items = data.get("items", [])
        stale_item = next((it for it in items if it.get("id") == "stale1"), None)
        twin_item = next((it for it in items if it.get("id") == "twin01"), None)

        self.assertIsNotNone(stale_item)
        assert stale_item is not None
        self.assertEqual(stale_item.get("review_stale"), ["answered-blocking-question"])

        self.assertIsNotNone(twin_item)
        assert twin_item is not None
        self.assertEqual(twin_item.get("review_stale"), [])

        # 2. aw attention board rendering
        cmd_board = [sys.executable, "-m", "agent_workflows", "attention"]
        res_board = subprocess.run(
            cmd_board, cwd=self.root, env=self.env, capture_output=True, text=True
        )
        self.assertEqual(
            res_board.returncode, 0, f"attention board failed: {res_board.stderr}"
        )
        self.assertIn("[stale-review]", res_board.stdout)


if __name__ == "__main__":
    unittest.main()
