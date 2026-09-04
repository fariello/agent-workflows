"""Adversarial and functional test suite for isolation hierarchy, concurrency eligibility, and merge revalidation.

awoptimize Order 09 (`1m5ob8`) E-01..E-04, validating V-01..V-04.

Covers:
  * E-01 / V-01: Portable isolation hierarchy (fresh session/subagent preferred for verifier,
                 fork strictly rejected for verifier and allowed only for read-only side work,
                 same-session audit strictly non-authoritative diagnostic, two-process fallback).
  * E-02 / V-02: Concurrency eligibility analyzer (independent read-only parallel allowed,
                 mutations serialized by default, parallel mutation only with disjoint worktrees,
                 disjoint file ownership, dependency independence, no shared generated files,
                 and deterministic merge order + serial fallback plan).
  * E-03 / V-03: Merge-and-revalidate gates (stale-base detection, conflict-resolution authority,
                 combined-diff review, generated-file ownership, and full post-integration revalidation;
                 per-lane-green + combined-red strictly fails).
  * E-04 / V-04: Seeded orchestration adversarial suite (executor/verifier identity collision,
                 leaked executor summary, verifier mutation attempt, shared-worktree conflict,
                 stale branch, overlapping ownership, lane timeout, missing result, unsafe background
                 completion, and correction invalidation).
"""

from __future__ import annotations

import unittest

from agent_workflows import orchestrate_isolation as iso
from agent_workflows import verify_roles as vr


class TestIsolationHierarchy(unittest.TestCase):
    """Test portable isolation hierarchy, role rules, diagnostics, and fallbacks (E-01 / V-01)."""

    def test_all_isolation_modes_defined(self) -> None:
        """Verify all isolation modes are registered."""
        self.assertIn(iso.ISOLATION_FRESH_SESSION, iso.ALL_ISOLATION_MODES)
        self.assertIn(iso.ISOLATION_INDEPENDENT_SUBAGENT, iso.ALL_ISOLATION_MODES)
        self.assertIn(iso.ISOLATION_FORK, iso.ALL_ISOLATION_MODES)
        self.assertIn(iso.ISOLATION_SAME_SESSION_DIAGNOSTIC, iso.ALL_ISOLATION_MODES)
        self.assertIn(iso.ISOLATION_TWO_PROCESS_FALLBACK, iso.ALL_ISOLATION_MODES)

    def test_fresh_session_and_subagent_preferred_for_verifier(self) -> None:
        """Verifier is permitted to run under fresh_session or independent_subagent."""
        res1 = iso.check_isolation_policy(
            actor_role=vr.ROLE_VERIFIER,
            work_shape=iso.WORK_SHAPE_VERIFICATION,
            isolation_mode=iso.ISOLATION_FRESH_SESSION,
        )
        self.assertTrue(res1.allowed)
        self.assertTrue(res1.is_authoritative)

        res2 = iso.check_isolation_policy(
            actor_role=vr.ROLE_VERIFIER,
            work_shape=iso.WORK_SHAPE_VERIFICATION,
            isolation_mode=iso.ISOLATION_INDEPENDENT_SUBAGENT,
        )
        self.assertTrue(res2.allowed)
        self.assertTrue(res2.is_authoritative)

    def test_forked_verifier_strictly_rejected(self) -> None:
        """A forked context is strictly rejected for the verifier (fork is read-only side work only)."""
        res = iso.check_isolation_policy(
            actor_role=vr.ROLE_VERIFIER,
            work_shape=iso.WORK_SHAPE_VERIFICATION,
            isolation_mode=iso.ISOLATION_FORK,
        )
        self.assertFalse(res.allowed)
        self.assertIn("fork", res.message.lower())

        with self.assertRaises(iso.ForkedVerifierForbiddenError):
            iso.enforce_isolation_policy(
                actor_role=vr.ROLE_VERIFIER,
                work_shape=iso.WORK_SHAPE_VERIFICATION,
                isolation_mode=iso.ISOLATION_FORK,
            )

    def test_fork_allowed_for_readonly_side_work(self) -> None:
        """Fork is allowed only for read-only side work that benefits from inherited context."""
        res = iso.check_isolation_policy(
            actor_role=vr.ROLE_INVESTIGATOR,
            work_shape=iso.WORK_SHAPE_READ_ONLY_INVENTORY,
            isolation_mode=iso.ISOLATION_FORK,
        )
        self.assertTrue(res.allowed)
        self.assertFalse(res.can_mutate_product)

        # Mutating work shape with fork is rejected
        res_mut = iso.check_isolation_policy(
            actor_role=vr.ROLE_EXECUTOR,
            work_shape=iso.WORK_SHAPE_BOUNDED_IMPLEMENTATION,
            isolation_mode=iso.ISOLATION_FORK,
        )
        self.assertFalse(res_mut.allowed)
        with self.assertRaises(iso.IsolationPolicyViolationError):
            iso.enforce_isolation_policy(
                actor_role=vr.ROLE_EXECUTOR,
                work_shape=iso.WORK_SHAPE_BOUNDED_IMPLEMENTATION,
                isolation_mode=iso.ISOLATION_FORK,
            )

    def test_same_session_audit_strictly_non_authoritative(self) -> None:
        """Same-session audit is allowed ONLY as non-authoritative diagnostic and cannot write decisions."""
        res = iso.check_isolation_policy(
            actor_role=vr.ROLE_INVESTIGATOR,
            work_shape=iso.WORK_SHAPE_SAME_SESSION_AUDIT,
            isolation_mode=iso.ISOLATION_SAME_SESSION_DIAGNOSTIC,
        )
        self.assertTrue(res.allowed)
        self.assertFalse(res.is_authoritative)

        ctx = iso.create_isolation_context(
            mode=iso.ISOLATION_SAME_SESSION_DIAGNOSTIC,
            actor_role=vr.ROLE_INVESTIGATOR,
            work_shape=iso.WORK_SHAPE_SAME_SESSION_AUDIT,
        )
        self.assertFalse(ctx.is_authoritative)

        # Cannot author verifier decision
        with self.assertRaises(iso.NonAuthoritativeDiagnosticError) as ex:
            iso.enforce_authoritative_decision(ctx, decision_kind="verifier_decision")
        self.assertIn("diagnostic", str(ex.exception).lower())

        # Cannot author completion transaction
        with self.assertRaises(iso.NonAuthoritativeDiagnosticError):
            iso.enforce_authoritative_decision(
                ctx, decision_kind="terminal_transaction"
            )

    def test_host_capabilities_fallback_to_two_process(self) -> None:
        """Hosts lacking native subagents fall back to a two-process session with handoff packet."""
        # Host with subagent support
        cap_native = iso.HostIsolationCapabilities(
            supports_subagent=True,
            supports_fork=True,
            supports_worktree=True,
            supports_multi_process=True,
        )
        mode = iso.resolve_isolation_mode(
            requested_mode=iso.ISOLATION_INDEPENDENT_SUBAGENT,
            capabilities=cap_native,
        )
        self.assertEqual(mode, iso.ISOLATION_INDEPENDENT_SUBAGENT)

        # Host without subagent support -> falls back to two_process_fallback
        cap_fallback = iso.HostIsolationCapabilities(
            supports_subagent=False,
            supports_fork=False,
            supports_worktree=True,
            supports_multi_process=True,
        )
        mode_fb = iso.resolve_isolation_mode(
            requested_mode=iso.ISOLATION_INDEPENDENT_SUBAGENT,
            capabilities=cap_fallback,
        )
        self.assertEqual(mode_fb, iso.ISOLATION_TWO_PROCESS_FALLBACK)

    def test_two_process_fallback_with_handoff_packet(self) -> None:
        """Handoff packet correctly packages state and passes validation in two-process fallback."""
        packet = iso.build_handoff_packet(
            run_id="run-20260822-test01",
            workflow_id="wf-test",
            step_id="S-01",
            actor_role=vr.ROLE_VERIFIER,
            base_commit="c001",
            head_commit="c002",
            worktree_path="/tmp/worktree-verifier",
            requirements={"R-01": "Must be isolated"},
            declared_scope={"files": ["agent_workflows/core.py"]},
            actual_diff="diff --git a/agent_workflows/core.py",
        )
        self.assertEqual(packet.run_id, "run-20260822-test01")
        self.assertEqual(packet.actor_role, vr.ROLE_VERIFIER)
        self.assertTrue(len(packet.packet_digest) > 0)

        # Validation passes
        val_res = iso.validate_handoff_packet(packet)
        self.assertTrue(val_res.ok)

        # Test double execution
        result = iso.run_isolated_session_double(
            isolation_mode=iso.ISOLATION_TWO_PROCESS_FALLBACK,
            packet=packet,
            runner_fn=lambda p: {
                "status": "success",
                "verified_digest": p.packet_digest,
            },
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["verified_digest"], packet.packet_digest)


class TestConcurrencyEligibilityAnalyzer(unittest.TestCase):
    """Test concurrency eligibility analyzer, conflict detection, and serial fallback (E-02 / V-02)."""

    def test_parallel_read_only_lanes_allowed(self) -> None:
        """Independent read-only investigations are allowed to run concurrently in parallel."""
        lane1 = iso.LaneRequest(
            lane_id="lane-inv-01",
            actor_role=vr.ROLE_INVESTIGATOR,
            lane_kind=iso.LANE_KIND_READ_ONLY,
            files_targeted=("agent_workflows/a.py",),
            worktree_path="/tmp/wt-shared",
        )
        lane2 = iso.LaneRequest(
            lane_id="lane-inv-02",
            actor_role=vr.ROLE_INVESTIGATOR,
            lane_kind=iso.LANE_KIND_READ_ONLY,
            files_targeted=("agent_workflows/b.py",),
            worktree_path="/tmp/wt-shared",
        )
        res = iso.analyze_concurrency_eligibility((lane1, lane2))
        self.assertTrue(res.is_eligible_parallel)
        self.assertEqual(res.execution_mode, iso.EXEC_MODE_PARALLEL_READ_ONLY)
        self.assertEqual(len(res.conflicts), 0)

    def test_serial_mutations_by_default(self) -> None:
        """Mutations default to serial execution when not configured with separate worktrees."""
        lane1 = iso.LaneRequest(
            lane_id="lane-mut-01",
            actor_role=vr.ROLE_EXECUTOR,
            lane_kind=iso.LANE_KIND_MUTATING,
            files_targeted=("agent_workflows/a.py",),
            worktree_path="/tmp/wt-single",
        )
        res = iso.analyze_concurrency_eligibility((lane1,))
        self.assertTrue(res.is_eligible_parallel)  # Single lane is trivially runnable
        self.assertEqual(res.execution_mode, iso.EXEC_MODE_SERIAL_MUTATING)
        self.assertEqual(res.merge_order, ("lane-mut-01",))

    def test_parallel_mutation_allowed_with_disjoint_worktrees_and_files(self) -> None:
        """Parallel mutation is allowed ONLY with disjoint worktrees, disjoint files, no deps, no shared generated files."""
        lane1 = iso.LaneRequest(
            lane_id="lane-mut-01",
            actor_role=vr.ROLE_EXECUTOR,
            lane_kind=iso.LANE_KIND_MUTATING,
            files_targeted=("agent_workflows/a.py",),
            generated_files=("docs/a.md",),
            worktree_path="/tmp/wt-lane-1",
        )
        lane2 = iso.LaneRequest(
            lane_id="lane-mut-02",
            actor_role=vr.ROLE_EXECUTOR,
            lane_kind=iso.LANE_KIND_MUTATING,
            files_targeted=("agent_workflows/b.py",),
            generated_files=("docs/b.md",),
            worktree_path="/tmp/wt-lane-2",
        )
        res = iso.analyze_concurrency_eligibility((lane1, lane2))
        self.assertTrue(res.is_eligible_parallel)
        self.assertEqual(res.execution_mode, iso.EXEC_MODE_PARALLEL_MUTATING)
        self.assertEqual(len(res.conflicts), 0)
        self.assertEqual(res.merge_order, ("lane-mut-01", "lane-mut-02"))

    def test_shared_worktree_conflict_refused_with_serial_fallback(self) -> None:
        """Two mutating lanes sharing the same worktree are refused for parallel execution."""
        lane1 = iso.LaneRequest(
            lane_id="lane-mut-01",
            actor_role=vr.ROLE_EXECUTOR,
            lane_kind=iso.LANE_KIND_MUTATING,
            files_targeted=("agent_workflows/a.py",),
            worktree_path="/tmp/wt-shared",
        )
        lane2 = iso.LaneRequest(
            lane_id="lane-mut-02",
            actor_role=vr.ROLE_EXECUTOR,
            lane_kind=iso.LANE_KIND_MUTATING,
            files_targeted=("agent_workflows/b.py",),
            worktree_path="/tmp/wt-shared",
        )
        res = iso.analyze_concurrency_eligibility((lane1, lane2))
        self.assertFalse(res.is_eligible_parallel)
        self.assertEqual(res.execution_mode, iso.EXEC_MODE_SERIAL_FALLBACK)
        self.assertTrue(
            any(c.conflict_type == iso.CONFLICT_SHARED_WORKTREE for c in res.conflicts)
        )
        self.assertEqual(res.serial_fallback_plan, ("lane-mut-01", "lane-mut-02"))

    def test_overlapping_file_ownership_refused_with_serial_fallback(self) -> None:
        """Two mutating lanes targeting overlapping files are refused and given a serial fallback plan."""
        lane1 = iso.LaneRequest(
            lane_id="lane-mut-01",
            actor_role=vr.ROLE_EXECUTOR,
            lane_kind=iso.LANE_KIND_MUTATING,
            files_targeted=("agent_workflows/common.py", "agent_workflows/a.py"),
            worktree_path="/tmp/wt-lane-1",
        )
        lane2 = iso.LaneRequest(
            lane_id="lane-mut-02",
            actor_role=vr.ROLE_EXECUTOR,
            lane_kind=iso.LANE_KIND_MUTATING,
            files_targeted=("agent_workflows/common.py", "agent_workflows/b.py"),
            worktree_path="/tmp/wt-lane-2",
        )
        res = iso.analyze_concurrency_eligibility((lane1, lane2))
        self.assertFalse(res.is_eligible_parallel)
        self.assertEqual(res.execution_mode, iso.EXEC_MODE_SERIAL_FALLBACK)
        self.assertTrue(
            any(
                c.conflict_type == iso.CONFLICT_OVERLAPPING_FILES for c in res.conflicts
            )
        )
        self.assertEqual(res.serial_fallback_plan, ("lane-mut-01", "lane-mut-02"))

    def test_dependent_lanes_refused_with_serial_fallback(self) -> None:
        """Mutating lanes with dependencies cannot run concurrently and must follow topological serial order."""
        lane1 = iso.LaneRequest(
            lane_id="lane-mut-01",
            actor_role=vr.ROLE_EXECUTOR,
            lane_kind=iso.LANE_KIND_MUTATING,
            files_targeted=("agent_workflows/a.py",),
            worktree_path="/tmp/wt-lane-1",
            depends_on=(),
        )
        lane2 = iso.LaneRequest(
            lane_id="lane-mut-02",
            actor_role=vr.ROLE_EXECUTOR,
            lane_kind=iso.LANE_KIND_MUTATING,
            files_targeted=("agent_workflows/b.py",),
            worktree_path="/tmp/wt-lane-2",
            depends_on=("lane-mut-01",),
        )
        res = iso.analyze_concurrency_eligibility(
            (lane2, lane1)
        )  # provided out of order
        self.assertFalse(res.is_eligible_parallel)
        self.assertEqual(res.execution_mode, iso.EXEC_MODE_SERIAL_FALLBACK)
        self.assertTrue(
            any(c.conflict_type == iso.CONFLICT_DEPENDENT_LANES for c in res.conflicts)
        )
        # Serial fallback must order dependencies first: lane-mut-01 before lane-mut-02
        self.assertEqual(res.serial_fallback_plan, ("lane-mut-01", "lane-mut-02"))

    def test_shared_generated_files_refused_with_serial_fallback(self) -> None:
        """Mutating lanes with shared generated files are refused for parallel execution."""
        lane1 = iso.LaneRequest(
            lane_id="lane-mut-01",
            actor_role=vr.ROLE_EXECUTOR,
            lane_kind=iso.LANE_KIND_MUTATING,
            files_targeted=("agent_workflows/a.py",),
            generated_files=("build/output.json",),
            worktree_path="/tmp/wt-lane-1",
        )
        lane2 = iso.LaneRequest(
            lane_id="lane-mut-02",
            actor_role=vr.ROLE_EXECUTOR,
            lane_kind=iso.LANE_KIND_MUTATING,
            files_targeted=("agent_workflows/b.py",),
            generated_files=("build/output.json",),
            worktree_path="/tmp/wt-lane-2",
        )
        res = iso.analyze_concurrency_eligibility((lane1, lane2))
        self.assertFalse(res.is_eligible_parallel)
        self.assertEqual(res.execution_mode, iso.EXEC_MODE_SERIAL_FALLBACK)
        self.assertTrue(
            any(
                c.conflict_type == iso.CONFLICT_SHARED_GENERATED_FILES
                for c in res.conflicts
            )
        )


class TestMergeAndRevalidateGates(unittest.TestCase):
    """Test merge-and-revalidate gates, stale-base detection, combined diff, and post-integration validation (E-03 / V-03)."""

    def test_successful_clean_merge_and_revalidation(self) -> None:
        """Clean isolated lanes merge sequentially, review combined diff, and pass full validation."""
        lane1 = iso.LaneOutcome(
            lane_id="lane-01",
            actor_role=vr.ROLE_EXECUTOR,
            base_commit="c000",
            head_commit="c001",
            worktree_path="/tmp/wt-1",
            changed_files=("agent_workflows/mod_a.py",),
            generated_files=("docs/a.md",),
            diff="diff --git a/agent_workflows/mod_a.py\n+def foo(): pass\n",
            per_lane_validation_passed=True,
            status=iso.STATUS_COMPLETED,
        )
        lane2 = iso.LaneOutcome(
            lane_id="lane-02",
            actor_role=vr.ROLE_EXECUTOR,
            base_commit="c000",
            head_commit="c002",
            worktree_path="/tmp/wt-2",
            changed_files=("agent_workflows/mod_b.py",),
            generated_files=("docs/b.md",),
            diff="diff --git a/agent_workflows/mod_b.py\n+def bar(): pass\n",
            per_lane_validation_passed=True,
            status=iso.STATUS_COMPLETED,
        )

        res = iso.execute_merge_and_revalidate_gate(
            integration_base_commit="c000",
            lane_outcomes=(lane1, lane2),
            merge_order=("lane-01", "lane-02"),
            full_validation_runner=lambda diff, files: True,
            declared_scope=("agent_workflows/*.py", "docs/*.md"),
        )
        self.assertTrue(res.passed)
        self.assertEqual(res.status, iso.INTEGRATED_PASSED)
        self.assertTrue(res.revalidation_passed)
        self.assertIn("mod_a.py", res.combined_diff)
        self.assertIn("mod_b.py", res.combined_diff)

    def test_stale_base_detection(self) -> None:
        """Integration fixture detects when a lane base commit does not match target integration base."""
        lane1 = iso.LaneOutcome(
            lane_id="lane-01",
            actor_role=vr.ROLE_EXECUTOR,
            base_commit="c_old_outdated",  # stale base vs integration target c000
            head_commit="c001",
            worktree_path="/tmp/wt-1",
            changed_files=("agent_workflows/mod_a.py",),
            diff="diff --git a/agent_workflows/mod_a.py\n+def foo(): pass\n",
            per_lane_validation_passed=True,
            status=iso.STATUS_COMPLETED,
        )
        res = iso.execute_merge_and_revalidate_gate(
            integration_base_commit="c000",
            lane_outcomes=(lane1,),
            merge_order=("lane-01",),
            full_validation_runner=lambda diff, files: True,
        )
        self.assertFalse(res.passed)
        self.assertEqual(res.status, iso.INTEGRATION_FAILED_STALE_BASE)
        self.assertTrue(any(f.check_name == "stale_base_check" for f in res.findings))

    def test_conflict_markers_detected(self) -> None:
        """Git conflict markers in lane diffs are detected and rejected."""
        lane1 = iso.LaneOutcome(
            lane_id="lane-01",
            actor_role=vr.ROLE_EXECUTOR,
            base_commit="c000",
            head_commit="c001",
            worktree_path="/tmp/wt-1",
            changed_files=("agent_workflows/mod_a.py",),
            diff="<<<<<<< HEAD\nfoo\n=======\nbar\n>>>>>>>",
            per_lane_validation_passed=True,
            status=iso.STATUS_COMPLETED,
        )
        res = iso.execute_merge_and_revalidate_gate(
            integration_base_commit="c000",
            lane_outcomes=(lane1,),
            merge_order=("lane-01",),
            full_validation_runner=lambda diff, files: True,
        )
        self.assertFalse(res.passed)
        self.assertEqual(res.status, iso.INTEGRATION_FAILED_CONFLICT)
        self.assertTrue(
            any(f.check_name == "conflict_marker_check" for f in res.findings)
        )

    def test_pasted_test_output_is_not_a_conflict_marker(self) -> None:
        """A lane pasting pytest output must still integrate (regression, measured 2026-09-04).

        THE BUG: this check was `any(marker in outcome.diff for marker in ("<<<<<<<", "=======",
        ">>>>>>>"))`, an unanchored substring scan over the WHOLE lane diff, which includes every
        ADDED LINE of content. pytest's own summary separator contains `=======`, so lane
        `aw/lane/prpipy` - verified, finalized, ZERO real markers - was refused integration with
        "unresolved git conflict markers".

        This is the perverse case worth pinning: the execution contract REQUIRES pasting the actual
        runner output as V-item evidence, so the gate punished a plan for obeying the rule, and every
        future plan pasting pytest output would hit the same wall.
        """
        diff = (
            "+## Validation and cross-check\n"
            "+  - Observed evidence: bare `python3 -m pytest` at HEAD `abc1234`:\n"
            "+========================= 3 failed, 3 passed in 0.20s ==========================\n"
            "+====================== 11 passed, 45 deselected in 0.26s =======================\n"
            "+  - Result: pass\n"
        )
        lane1 = iso.LaneOutcome(
            lane_id="lane-01",
            actor_role=vr.ROLE_EXECUTOR,
            base_commit="c000",
            head_commit="c001",
            worktree_path="/tmp/wt-1",
            changed_files=("agent_workflows/mod_a.py",),
            diff=diff,
            per_lane_validation_passed=True,
            status=iso.STATUS_COMPLETED,
        )
        res = iso.execute_merge_and_revalidate_gate(
            integration_base_commit="c000",
            lane_outcomes=(lane1,),
            merge_order=("lane-01",),
            full_validation_runner=lambda diff, files: True,
        )
        self.assertTrue(
            res.passed,
            f"pasted pytest output must not read as a conflict marker; got {res.status}: {res.message}",
        )
        self.assertFalse(
            any(f.check_name == "conflict_marker_check" for f in res.findings)
        )

    def test_conflict_marker_predicate_is_line_anchored(self) -> None:
        """The predicate matches only a REAL marker: seven chars at line start, then space or EOL."""
        # REAL markers, in the exact forms git writes.
        for real in (
            "<<<<<<< HEAD",
            "<<<<<<< ours\nfoo",
            "=======",
            "=======\n",
            ">>>>>>> aw/lane/x",
            "context\n=======\nmore",  # mid-diff, still line-anchored
        ):
            self.assertTrue(
                iso.diff_has_conflict_markers(real), f"should detect: {real!r}"
            )
        # NOT markers: pasted output, ASCII rules, prose, and near-misses on length/position.
        for benign in (
            "========================= 3 failed in 0.20s ==========================",
            "====================== 11 passed, 45 deselected =======================",
            "-------------------------------",
            "the gate scans for ======= in the diff",
            "======",  # six, not seven
            "  =======",  # indented, so not a marker git wrote
            "=======x",  # seven then a non-space
            "",
        ):
            self.assertFalse(
                iso.diff_has_conflict_markers(benign), f"should NOT detect: {benign!r}"
            )

    def test_combined_diff_scope_fence_enforcement(self) -> None:
        """Out-of-scope files in merged diff cause integration failure."""
        lane1 = iso.LaneOutcome(
            lane_id="lane-01",
            actor_role=vr.ROLE_EXECUTOR,
            base_commit="c000",
            head_commit="c001",
            worktree_path="/tmp/wt-1",
            changed_files=("unauthorized_dir/evil.py",),
            diff="diff --git a/unauthorized_dir/evil.py\n+malicious\n",
            per_lane_validation_passed=True,
            status=iso.STATUS_COMPLETED,
        )
        res = iso.execute_merge_and_revalidate_gate(
            integration_base_commit="c000",
            lane_outcomes=(lane1,),
            merge_order=("lane-01",),
            full_validation_runner=lambda diff, files: True,
            declared_scope=("agent_workflows/*.py",),
        )
        self.assertFalse(res.passed)
        self.assertEqual(res.status, iso.INTEGRATION_FAILED_SCOPE_VIOLATION)

    def test_per_lane_green_but_combined_red_fails(self) -> None:
        """Key invariant: per-lane green never implies integrated green; post-integration failure fails gate."""
        lane1 = iso.LaneOutcome(
            lane_id="lane-01",
            actor_role=vr.ROLE_EXECUTOR,
            base_commit="c000",
            head_commit="c001",
            worktree_path="/tmp/wt-1",
            changed_files=("agent_workflows/mod_a.py",),
            diff="diff --git a/agent_workflows/mod_a.py\n+def foo(): pass\n",
            per_lane_validation_passed=True,  # Passed locally in lane 1!
            status=iso.STATUS_COMPLETED,
        )
        lane2 = iso.LaneOutcome(
            lane_id="lane-02",
            actor_role=vr.ROLE_EXECUTOR,
            base_commit="c000",
            head_commit="c002",
            worktree_path="/tmp/wt-2",
            changed_files=("agent_workflows/mod_b.py",),
            diff="diff --git a/agent_workflows/mod_b.py\n+def bar(): pass\n",
            per_lane_validation_passed=True,  # Passed locally in lane 2!
            status=iso.STATUS_COMPLETED,
        )

        # Full validation runner fails on combined diff (combined-red)
        res = iso.execute_merge_and_revalidate_gate(
            integration_base_commit="c000",
            lane_outcomes=(lane1, lane2),
            merge_order=("lane-01", "lane-02"),
            full_validation_runner=lambda diff, files: (
                False
            ),  # Combined revalidation FAILS!
            declared_scope=("agent_workflows/*.py",),
        )
        self.assertFalse(res.passed)
        self.assertEqual(res.status, iso.INTEGRATION_FAILED_COMBINED_RED)
        self.assertFalse(res.revalidation_passed)
        self.assertTrue(
            any(f.check_name == "full_revalidation_check" for f in res.findings)
        )

    def test_timed_out_lane_fails_integration(self) -> None:
        """A background lane that timed out is strictly a failure, never treated as success."""
        lane1 = iso.LaneOutcome(
            lane_id="lane-01",
            actor_role=vr.ROLE_EXECUTOR,
            base_commit="c000",
            head_commit="c001",
            worktree_path="/tmp/wt-1",
            changed_files=("agent_workflows/mod_a.py",),
            diff="",
            per_lane_validation_passed=False,
            status=iso.STATUS_TIMED_OUT,
        )
        res = iso.execute_merge_and_revalidate_gate(
            integration_base_commit="c000",
            lane_outcomes=(lane1,),
            merge_order=("lane-01",),
            full_validation_runner=lambda diff, files: True,
        )
        self.assertFalse(res.passed)
        self.assertEqual(res.status, iso.INTEGRATION_FAILED_LANE_FAILURE)

    def test_missing_lane_fails_integration(self) -> None:
        """A missing lane in merge order causes immediate failure."""
        res = iso.execute_merge_and_revalidate_gate(
            integration_base_commit="c000",
            lane_outcomes=(),
            merge_order=("lane-missing-01",),
            full_validation_runner=lambda diff, files: True,
        )
        self.assertFalse(res.passed)
        self.assertEqual(res.status, iso.INTEGRATION_FAILED_MISSING_LANE)


class TestSeededOrchestrationAdversaries(unittest.TestCase):
    """Seeded adversarial suite covering all 10 role/isolation attack vectors (E-04 / V-04)."""

    def test_adv_01_executor_verifier_identity_collision(self) -> None:
        """Adversary 1: Executor attempts to self-verify or author verifier decision."""
        with self.assertRaises(vr.SelfVerificationForbiddenError):
            vr.enforce_role_action(vr.ROLE_EXECUTOR, "author_verifier_decision")

        with self.assertRaises(vr.SelfVerificationForbiddenError):
            vr.check_self_verification(
                verifier_role=vr.ROLE_EXECUTOR,
                author_role=vr.ROLE_EXECUTOR,
                requirement_id="R-01",
            )

    def test_adv_02_leaked_executor_summary(self) -> None:
        """Adversary 2: Executor conclusion prose leaked into packet is detected and rejected/stripped."""
        leaky_payload = {
            "run_id": "run-20260822-test",
            "workflow_id": "wf-test",
            "base_commit": "c001",
            "head_commit": "c002",
            "worktree_path": "/tmp/wt",
            "frozen_requirements": {"R-01": "req"},
            "declared_scope": {"files": ["a.py"]},
            "actual_diff": "diff",
            "executor_prose": "I have thoroughly verified and believe this is 100% complete and perfect.",
        }
        findings = vr._detect_executor_prose_leak(leaky_payload)
        self.assertTrue(len(findings) > 0)
        self.assertEqual(findings[0].code, "VP-PROSE-LEAK")

        # Building packet strips forbidden prose
        packet = vr.build_verifier_packet(
            run_id="run-20260822-test",
            workflow_id="wf-test",
            base_commit="c001",
            head_commit="c002",
            worktree_path="/tmp/wt",
            frozen_requirements={"R-01": "req"},
            declared_scope={"files": ["a.py"]},
            actual_diff="diff",
            raw_evidence_manifest=[{"id": "ev-1", "conclusion_prose": "Trust me"}],
        )
        self.assertNotIn("conclusion_prose", packet.raw_evidence_manifest[0])

    def test_adv_03_verifier_mutation_attempt(self) -> None:
        """Adversary 3: Verifier attempts product code write in isolated workspace."""
        with self.assertRaises(vr.ProductMutationForbiddenError):
            vr.check_code_mutation_allowed(
                actor_role=vr.ROLE_VERIFIER,
                file_path="agent_workflows/orchestrate_isolation.py",
                is_product_code=True,
            )

        with self.assertRaises(vr.ProductMutationForbiddenError):
            vr.enforce_role_action(vr.ROLE_VERIFIER, "mutate_product_code")

    def test_adv_04_shared_worktree_conflict(self) -> None:
        """Adversary 4: Two concurrent mutating lanes attempt to share the same worktree."""
        lane1 = iso.LaneRequest(
            "lane-1",
            vr.ROLE_EXECUTOR,
            iso.LANE_KIND_MUTATING,
            ("a.py",),
            worktree_path="/tmp/wt",
        )
        lane2 = iso.LaneRequest(
            "lane-2",
            vr.ROLE_EXECUTOR,
            iso.LANE_KIND_MUTATING,
            ("b.py",),
            worktree_path="/tmp/wt",
        )
        res = iso.analyze_concurrency_eligibility((lane1, lane2))
        self.assertFalse(res.is_eligible_parallel)
        self.assertTrue(
            any(c.conflict_type == iso.CONFLICT_SHARED_WORKTREE for c in res.conflicts)
        )

    def test_adv_05_stale_branch_integration(self) -> None:
        """Adversary 5: Lane based on stale commit attempts integration."""
        lane = iso.LaneOutcome(
            lane_id="lane-1",
            actor_role=vr.ROLE_EXECUTOR,
            base_commit="c_stale_base",
            head_commit="c_head",
            worktree_path="/tmp/wt",
            changed_files=("a.py",),
            diff="diff",
            per_lane_validation_passed=True,
            status=iso.STATUS_COMPLETED,
        )
        res = iso.execute_merge_and_revalidate_gate(
            integration_base_commit="c_fresh_base",
            lane_outcomes=(lane,),
            merge_order=("lane-1",),
            full_validation_runner=lambda diff, files: True,
        )
        self.assertFalse(res.passed)
        self.assertEqual(res.status, iso.INTEGRATION_FAILED_STALE_BASE)

    def test_adv_06_overlapping_ownership(self) -> None:
        """Adversary 6: Two mutating lanes with overlapping file ownership."""
        lane1 = iso.LaneRequest(
            "lane-1",
            vr.ROLE_EXECUTOR,
            iso.LANE_KIND_MUTATING,
            ("common.py",),
            worktree_path="/tmp/wt1",
        )
        lane2 = iso.LaneRequest(
            "lane-2",
            vr.ROLE_EXECUTOR,
            iso.LANE_KIND_MUTATING,
            ("common.py",),
            worktree_path="/tmp/wt2",
        )
        res = iso.analyze_concurrency_eligibility((lane1, lane2))
        self.assertFalse(res.is_eligible_parallel)
        self.assertTrue(
            any(
                c.conflict_type == iso.CONFLICT_OVERLAPPING_FILES for c in res.conflicts
            )
        )

    def test_adv_07_lane_timeout_treated_as_failure(self) -> None:
        """Adversary 7: Background lane times out; must be treated as failure, never success."""
        lane = iso.LaneOutcome(
            lane_id="lane-timeout",
            actor_role=vr.ROLE_EXECUTOR,
            base_commit="c0",
            head_commit="c1",
            worktree_path="/tmp/wt",
            changed_files=(),
            diff="",
            per_lane_validation_passed=False,
            status=iso.STATUS_TIMED_OUT,
        )
        res = iso.execute_merge_and_revalidate_gate(
            integration_base_commit="c0",
            lane_outcomes=(lane,),
            merge_order=("lane-timeout",),
            full_validation_runner=lambda diff, files: True,
        )
        self.assertFalse(res.passed)
        self.assertEqual(res.status, iso.INTEGRATION_FAILED_LANE_FAILURE)

    def test_adv_08_missing_result_treated_as_failure(self) -> None:
        """Adversary 8: Missing lane result causes integration refusal."""
        res = iso.execute_merge_and_revalidate_gate(
            integration_base_commit="c0",
            lane_outcomes=(),
            merge_order=("lane-missing",),
            full_validation_runner=lambda diff, files: True,
        )
        self.assertFalse(res.passed)
        self.assertEqual(res.status, iso.INTEGRATION_FAILED_MISSING_LANE)

    def test_adv_09_unsafe_background_completion(self) -> None:
        """Adversary 9: Background worker role attempts to author terminal completion transaction."""
        with self.assertRaises(vr.TerminalAuthorityError):
            vr.enforce_role_action(vr.ROLE_EXECUTOR, "author_terminal_transaction")

        with self.assertRaises(vr.TerminalAuthorityError):
            vr.enforce_role_action(vr.ROLE_INVESTIGATOR, "author_terminal_transaction")

    def test_adv_10_correction_invalidation_and_rerun(self) -> None:
        """Adversary 10: Correction mutates files, invalidating previous evidence and requiring full revalidation."""
        ev_manifest = (
            {
                "evidence_id": "ev-01",
                "bound_files": ["agent_workflows/orchestrate_isolation.py"],
                "exit_code": 0,
            },
            {"evidence_id": "ev-02", "bound_files": ["unrelated.py"], "exit_code": 0},
        )
        updated = vr.invalidate_evidence_on_correction(
            ev_manifest,
            changed_files=["agent_workflows/orchestrate_isolation.py"],
            invalidated_evidence_ids=["ev-02"],
        )

        self.assertTrue(updated[0].get("invalidated"))
        self.assertTrue(updated[0].get("stale"))
        self.assertEqual(updated[0].get("invalidation_reason"), "source_file_modified")

        self.assertTrue(updated[1].get("invalidated"))
        self.assertTrue(updated[1].get("stale"))
        self.assertEqual(
            updated[1].get("invalidation_reason"), "explicit_verifier_invalidation"
        )


if __name__ == "__main__":
    unittest.main()
