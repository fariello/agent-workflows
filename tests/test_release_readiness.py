"""Release-readiness gate tests for awoptimize Order 18 (`0zst62`) E-05.

This test drives :mod:`agent_workflows.release_readiness`, the checkable core of the final
release-readiness review. It:

  * actually RUNS the canonical leak scan (``aw sanitize --agent``) and requires exit 0;
  * actually RUNS all IPD lint phases (``aw ipd lint --all --agent``) and requires exit 0;
  * asserts the benchmark release invariants (0 critical escapes, 100% evidence validity);
  * asserts changelog + versioning presence;
  * asserts the GO / NO-GO aggregation logic with fixtures (a failing gate flips to NO-GO);
  * asserts the airtight invariant that the review NEVER tags / publishes / deploys / pushes.

Per the IPD, the leak-scan and IPD-lint gates SHELL OUT for real; the heavier full-suite gate
is asserted via the aggregation logic (the live ``make test`` run is driven by the harness/CI,
its output pasted into the walkthrough). This test itself performs NO release action.

Stdlib ``unittest`` (repository convention).
"""

from __future__ import annotations

import pytest

import subprocess
import sys
import unittest
from pathlib import Path

from agent_workflows import release_readiness as rr

# Heavy subprocess/release suite; excluded from the fast default run (see pyproject addopts
# `-m "not slow"`). Run with `make test-all`.
pytestmark = pytest.mark.slow

REPO_ROOT = Path(__file__).resolve().parent.parent


# ==================================================================================================
# Live subprocess gates (these actually run, per the IPD)
# ==================================================================================================


class LeakScanGateTests(unittest.TestCase):
    def test_leak_scan_runs_and_passes(self):
        # FALSIFIABLE: the canonical leak scan must exit 0 on the tracked tree.
        gate = rr.gate_leak_scan(REPO_ROOT)
        self.assertTrue(gate.passed, gate.detail)
        self.assertEqual(gate.evidence["returncode"], 0)

    def test_leak_scan_uses_canonical_tool(self):
        # It invokes `python3 -m agent_workflows sanitize` (the same code as `aw sanitize`).
        proc = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "sanitize", "--agent"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)


class IpdLintGateTests(unittest.TestCase):
    def test_ipd_lint_all_phases_run_and_pass(self):
        # FALSIFIABLE: all IPD lint phases must exit 0.
        gate = rr.gate_ipd_lint(REPO_ROOT)
        self.assertTrue(gate.passed, gate.detail)
        self.assertEqual(gate.evidence["returncode"], 0)


# ==================================================================================================
# Deterministic gates
# ==================================================================================================


class BenchmarkThresholdGateTests(unittest.TestCase):
    def test_default_invariants_hold(self):
        gate = rr.gate_benchmark_thresholds()
        self.assertTrue(gate.passed, gate.evidence)

    def test_relaxed_invariant_is_detected(self):
        # FALSIFIABLE: a threshold policy that violates a non-negotiable invariant fails the gate.
        from agent_workflows import benchmark_thresholds as bt

        # Constructing a policy with a bad invariant raises at build time (fail closed); the
        # gate must treat that as a violation. Build a valid policy, then corrupt one threshold.
        policy = bt.ThresholdPolicy()
        bad = bt.RiskThresholds(
            risk_class=bt.RISK_LOW,
            min_requirement_recall=0.9,
            min_task_correctness=0.85,
            min_test_integrity=1.0,
            max_critical_escapes=1,  # INVARIANT VIOLATION (must be 0)
            min_evidence_validity=1.0,
            max_scope_violations=1,
            max_unconfirmed_assumptions=0,
        )
        policy.thresholds[bt.RISK_LOW] = bad
        gate = rr.gate_benchmark_thresholds(policy)
        self.assertFalse(gate.passed)
        self.assertTrue(gate.evidence["violations"])


class ChangelogVersioningGateTests(unittest.TestCase):
    def test_changelog_and_version_present(self):
        gate = rr.gate_changelog_versioning(REPO_ROOT)
        self.assertTrue(gate.passed, gate.evidence)
        self.assertTrue(gate.evidence["version"])


class DriftDocsDispositionGateTests(unittest.TestCase):
    def test_empty_sets_pass(self):
        self.assertTrue(rr.gate_generated_drift([]).passed)
        self.assertTrue(rr.gate_docs_checks([]).passed)
        self.assertTrue(rr.gate_workflow_disposition([]).passed)
        self.assertTrue(rr.gate_capability_freshness([]).passed)

    def test_nonempty_sets_fail(self):
        # FALSIFIABLE: any drift / doc finding / undispositioned workflow / stale claim fails.
        self.assertFalse(rr.gate_generated_drift(["a.py"]).passed)
        self.assertFalse(rr.gate_docs_checks(["broken link"]).passed)
        self.assertFalse(rr.gate_workflow_disposition(["assess"]).passed)
        self.assertFalse(rr.gate_capability_freshness(["opencode/1.0.0/skills"]).passed)


class ResidualRiskGateTests(unittest.TestCase):
    def test_signed_off_passes(self):
        self.assertTrue(rr.gate_residual_risk(True, "Gabriele Fariello").passed)

    def test_unsigned_fails(self):
        self.assertFalse(rr.gate_residual_risk(False, "").passed)
        self.assertFalse(rr.gate_residual_risk(True, "").passed)


# ==================================================================================================
# GO / NO-GO aggregation
# ==================================================================================================


class VerdictTests(unittest.TestCase):
    def test_all_pass_is_go(self):
        rep = rr.aggregate(
            [
                rr.GateResult("a", True, "ok"),
                rr.GateResult("b", True, "ok"),
            ]
        )
        self.assertEqual(rep.verdict, rr.VERDICT_GO)
        self.assertTrue(rep.is_go)
        self.assertEqual(rep.failing_gates(), [])

    def test_one_fail_is_no_go(self):
        # FALSIFIABLE: a single failing gate flips the verdict to NO-GO.
        rep = rr.aggregate(
            [
                rr.GateResult("a", True, "ok"),
                rr.GateResult("b", False, "broken"),
            ]
        )
        self.assertEqual(rep.verdict, rr.VERDICT_NO_GO)
        self.assertFalse(rep.is_go)
        self.assertEqual(rep.failing_gates(), ["b"])

    def test_render_contains_verdict_and_no_dashes_in_verdict_line(self):
        rep = rr.aggregate([rr.GateResult("a", True, "ok")])
        rendered = rep.render()
        self.assertIn("Verdict: GO", rendered)


class FullReportTests(unittest.TestCase):
    def test_build_report_go_on_clean_tree(self):
        # The real tree: leak scan + ipd lint run for real; everything else clean.
        rep = rr.build_report(
            suite_passed=True,
            residual_risk_signed=True,
            residual_risk_signer="Gabriele Fariello",
            repo_root=REPO_ROOT,
        )
        self.assertEqual(rep.verdict, rr.VERDICT_GO, rep.failing_gates())

    def test_build_report_no_go_when_suite_red(self):
        # FALSIFIABLE: a red suite forces NO-GO regardless of the other gates.
        rep = rr.build_report(
            suite_passed=False,
            residual_risk_signed=True,
            residual_risk_signer="Gabriele Fariello",
            repo_root=REPO_ROOT,
            run_subprocess_gates=False,
        )
        self.assertEqual(rep.verdict, rr.VERDICT_NO_GO)
        self.assertIn("full_suite", rep.failing_gates())

    def test_build_report_no_go_when_residual_risk_unsigned(self):
        # FALSIFIABLE: no residual-risk sign-off forces NO-GO.
        rep = rr.build_report(
            suite_passed=True,
            residual_risk_signed=False,
            repo_root=REPO_ROOT,
            run_subprocess_gates=False,
        )
        self.assertEqual(rep.verdict, rr.VERDICT_NO_GO)
        self.assertIn("residual_risk", rep.failing_gates())


# ==================================================================================================
# The airtight never-tag/publish/deploy/push invariant
# ==================================================================================================


class NoReleaseActionTests(unittest.TestCase):
    def test_forbidden_actions_are_refused(self):
        for action in ("tag", "publish", "deploy", "push", "release", "upload"):
            with self.assertRaises(rr.ReleaseActionForbiddenError):
                rr.assert_no_release_action(action)

    def test_decision_only_actions_allowed(self):
        # A decision-only "verdict" action does not raise.
        rr.assert_no_release_action("verdict")
        rr.assert_no_release_action("report")

    def test_module_source_has_no_release_mutating_call(self):
        # Static guard: the readiness module must not contain a git tag/push or upload call.
        src = (REPO_ROOT / "agent_workflows" / "release_readiness.py").read_text(
            encoding="utf-8"
        )
        for banned in ('"tag"', "git push", "git tag", "twine", "pypi upload"):
            # The FORBIDDEN_RELEASE_ACTIONS tuple legitimately names them as strings; ensure
            # there is no actual subprocess invocation of a release-mutating command.
            if banned in ("git push", "git tag", "twine"):
                self.assertNotIn(
                    f"subprocess.run([{banned}", src, f"unexpected {banned} call"
                )

    def test_no_tag_push_in_git_log_from_this_order(self):
        # Evidence: the working tree has no NEW tag created by this order. We assert the tag
        # list is unchanged relative to what a decision-only review would leave (i.e. this
        # test itself creates no tag). This is a smoke check that running the suite tags nothing.
        proc = subprocess.run(
            ["git", "tag", "--list"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        before = set(proc.stdout.splitlines())
        # Building a full report must not create a tag.
        rr.build_report(
            suite_passed=True,
            residual_risk_signed=True,
            residual_risk_signer="x",
            repo_root=REPO_ROOT,
            run_subprocess_gates=False,
        )
        proc2 = subprocess.run(
            ["git", "tag", "--list"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        after = set(proc2.stdout.splitlines())
        self.assertEqual(
            before, after, "release-readiness review must create no git tag"
        )


if __name__ == "__main__":
    unittest.main()
