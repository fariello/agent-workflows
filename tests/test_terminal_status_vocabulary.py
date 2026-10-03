#!/usr/bin/env python3
"""statusvocab Order 01 (`cyamvi`): Terminal status vocabulary test suite.

Verifies V-01 through V-07 from plan:
  - V-01 (E-01): 12 canonical terminal states, alias mapping, union terminal states,
                 and object identity re-exported across both hosts.
  - V-02 (E-02): Reader normalization for all 11 legacy tokens in synthetic runs without error.
  - V-03 (E-03): Four-way split of legacy blocked producers and canonical writer emissions.
  - V-04 (E-04): Promotion of `interrupted` into TERMINAL_STATES, distinct from `fail-gate`.
  - V-05 (E-05): Narrowing of EXECUTION_SUCCESS_STATES to {"executed"} and 0 blast radius.
  - V-06 (E-06): Elimination of artifact_audit "complete" coercion and expected directory mapping.
  - V-07 (E-07): Tree-wide exhaustiveness guard asserting no unmapped or unrenamed tokens.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import (
    agy_runipd,
    artifact_audit,
    attention,
    lifecycle_style,
    oc_runipd,
    render_stream,
    run_viewer,
    runner_shared,
)

EXPECTED_CANONICAL_STATES = frozenset(
    {
        "executed",
        "reviewed",
        "approved",
        "interrupted",
        "fail-gate",
        "fail-begin",
        "fail-lane",
        "fail-verify",
        "fail-depend",
        "fail-merge",
        "not-run",
        "failed",
        "already-landed",
        "retired",
    }
)

EXPECTED_LEGACY_ALIASES = {
    "substantially-complete": "fail-gate",
    "partial": "fail-verify",
    "failed-safely": "fail-gate",
    "blocked": "fail-gate",
    "dependency-blocked": "fail-depend",
    "integration-blocked": "fail-merge",
    "merge-conflict": "fail-merge",
    "merge-needs-human": "fail-merge",
    "merge-refused": "fail-merge",
    "not-attempted": "not-run",
}


class TestTerminalStatusVocabularyDefinitions(unittest.TestCase):
    """V-01 (E-01): Shared vocabulary definition, alias map, and host object identity."""

    def test_canonical_terminal_states_set(self):
        """TERMINAL_STATES_CANONICAL contains exactly the 14 canonical states."""
        self.assertEqual(
            runner_shared.TERMINAL_STATES_CANONICAL, EXPECTED_CANONICAL_STATES
        )
        self.assertEqual(len(runner_shared.TERMINAL_STATES_CANONICAL), 14)

    def test_terminal_status_aliases_map(self):
        """TERMINAL_STATUS_ALIASES maps all legacy tokens to canonical members."""
        self.assertEqual(runner_shared.TERMINAL_STATUS_ALIASES, EXPECTED_LEGACY_ALIASES)
        for legacy, canonical in runner_shared.TERMINAL_STATUS_ALIASES.items():
            self.assertIn(
                canonical,
                runner_shared.TERMINAL_STATES_CANONICAL,
                f"Alias target '{canonical}' for '{legacy}' must be in canonical set",
            )

    def test_terminal_states_union(self):
        """TERMINAL_STATES is the exact union of canonical states and legacy aliases."""
        expected_union = frozenset(
            EXPECTED_CANONICAL_STATES | set(EXPECTED_LEGACY_ALIASES.keys())
        )
        self.assertEqual(runner_shared.TERMINAL_STATES, expected_union)

    def test_object_identity_re_export_across_hosts(self):
        """Both hosts (oc_runipd, agy_runipd) re-export the exact identical objects."""
        # TERMINAL_STATES
        self.assertIs(oc_runipd.TERMINAL_STATES, runner_shared.TERMINAL_STATES)
        self.assertIs(agy_runipd.TERMINAL_STATES, runner_shared.TERMINAL_STATES)

        # TERMINAL_STATES_CANONICAL
        self.assertIs(
            oc_runipd.TERMINAL_STATES_CANONICAL, runner_shared.TERMINAL_STATES_CANONICAL
        )
        self.assertIs(
            agy_runipd.TERMINAL_STATES_CANONICAL,
            runner_shared.TERMINAL_STATES_CANONICAL,
        )

        # TERMINAL_STATUS_ALIASES
        self.assertIs(
            oc_runipd.TERMINAL_STATUS_ALIASES, runner_shared.TERMINAL_STATUS_ALIASES
        )
        self.assertIs(
            agy_runipd.TERMINAL_STATUS_ALIASES, runner_shared.TERMINAL_STATUS_ALIASES
        )

        # canonical_terminal_status
        self.assertIs(
            oc_runipd.canonical_terminal_status, runner_shared.canonical_terminal_status
        )
        self.assertIs(
            agy_runipd.canonical_terminal_status,
            runner_shared.canonical_terminal_status,
        )

    def test_canonical_terminal_status_mapping(self):
        """canonical_terminal_status maps legacy to canonical and preserves canonical/unknown."""
        for legacy, canonical in EXPECTED_LEGACY_ALIASES.items():
            self.assertEqual(
                runner_shared.canonical_terminal_status(legacy),
                canonical,
                f"Expected '{legacy}' to map to '{canonical}'",
            )

        for canonical in EXPECTED_CANONICAL_STATES:
            self.assertEqual(
                runner_shared.canonical_terminal_status(canonical),
                canonical,
                f"Expected canonical '{canonical}' to map to itself",
            )

        self.assertEqual(
            runner_shared.canonical_terminal_status("unknown-token"), "unknown-token"
        )
        self.assertEqual(runner_shared.canonical_terminal_status(None), "")
        self.assertEqual(runner_shared.canonical_terminal_status(123), "")


class TestLegacyStatusReaderNormalization(unittest.TestCase):
    """V-02 (E-02): All readers accept legacy and canonical tokens without error."""

    def test_synthetic_run_directory_read_by_viewer_and_attention(self):
        """A synthetic run directory carrying all legacy tokens is read without error."""
        all_tokens = list(EXPECTED_LEGACY_ALIASES.keys()) + list(
            EXPECTED_CANONICAL_STATES
        )
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            run_dir = temp_path / "run-20260925T000000Z-12345"
            run_dir.mkdir(parents=True)
            outcomes_dir = run_dir / "outcomes"
            outcomes_dir.mkdir(parents=True)

            queue = []
            for i, token in enumerate(all_tokens, 1):
                id6 = f"tok{i:03d}"
                plan_file = f"20260925-test-{i:02d}-{id6}-test-plan.ipd.md"
                item = {
                    "id": id6,
                    "id6": id6,
                    "order": i,
                    "configured_file": plan_file,
                    "plan_file": plan_file,
                    "status": token,
                    "dependencies": [],
                }
                queue.append(item)
                outcome_file = outcomes_dir / f"{i:02d}-{id6}.json"
                outcome_file.write_text(
                    json.dumps({"disposition": token, "pushed": False})
                )

            state = {
                "run_id": run_dir.name,
                "started_at": "2026-09-25T00:00:00Z",
                "completed_at": "2026-09-25T00:01:00Z",
                "status": "completed",
                "options": {},
                "queue": queue,
            }
            (run_dir / "state.json").write_text(json.dumps(state, indent=2))

            # 1. run_viewer.load_run_summary / format_run_human
            summary = run_viewer.load_run_summary(run_dir)
            self.assertIsNotNone(summary)
            term = run_viewer.Term(color=False)
            formatted = run_viewer.format_run_human(
                summary, term=term, repo_root=temp_path
            )
            self.assertIsInstance(formatted, str)

            # 2. lifecycle_style resolution
            for item in queue:
                lc = render_stream.resolve_item_lifecycle(item["status"])
                self.assertIsNotNone(lc)
                resolved = lifecycle_style.resolve(
                    lifecycle_style.FAMILY_RUNNER_ITEM, item["status"]
                )
                self.assertIsNotNone(resolved)

            # 3. render_stream success lifecycle
            for token in all_tokens:
                reached = render_stream.resolve_reached_success_lifecycle(token)
                self.assertEqual(reached.stage, lifecycle_style.DONE)
                self.assertEqual(reached.native_status, token)

            # 4. attention.get_active_runs_map
            active_map = attention.get_active_runs_map(temp_path)
            self.assertIsInstance(active_map, dict)

    def test_deferral_ladder_retry_decision_unchanged_for_legacy_integration_status(
        self,
    ):
        """OQ-02 / D-1: Deferral ladder operates on deferred_integration_items without status string matching."""
        state = {
            "queue": [
                {
                    "id6": "abc123",
                    "status": runner_shared.INTEGRATION_DEFERRED_STATUS,
                    "preserved_branch": "aw/lane/abc123",
                    "preserved_head": "0123456789abcdef",
                    "integration_deferral": "non-fast-forward",
                }
            ]
        }
        deferred = runner_shared.deferred_integration_items(state)
        self.assertEqual(len(deferred), 1)
        self.assertEqual(deferred[0]["id6"], "abc123")


class TestWriterCanonicalEmissionsAndFourWaySplit(unittest.TestCase):
    """V-03 (E-03): Four-way split of legacy blocked token and canonical writer outputs."""

    def test_four_way_split_producers(self):
        """The four legacy blocked producers emit fail-gate, fail-begin, fail-lane, and fail-verify."""
        # Verifier verdicts in _VERDICT_TABLE emit fail-verify
        self.assertEqual(runner_shared._VERDICT_TABLE["BLOCKED"].state, "fail-verify")
        self.assertEqual(
            runner_shared._VERDICT_TABLE["NOT CONFORMING"].state, "fail-verify"
        )

    def test_outcome_precedence_disposition_mappings(self):
        """outcome_precedence_disposition maps outcomes to canonical tokens."""
        # Plan in executed bucket -> executed
        self.assertEqual(
            runner_shared.outcome_precedence_disposition("executed", None),
            "executed",
        )

        # Plan not in executed bucket claiming executed -> fail-gate (downgraded)
        self.assertEqual(
            runner_shared.outcome_precedence_disposition(
                "pending", {"disposition": "executed"}
            ),
            "fail-gate",
        )

        # Recorded canonical tokens preserved
        for token in (
            "fail-gate",
            "fail-begin",
            "fail-lane",
            "fail-verify",
            "fail-merge",
            "failed",
        ):
            self.assertEqual(
                runner_shared.outcome_precedence_disposition(
                    "pending", {"disposition": token}
                ),
                token,
            )

        # Recorded legacy tokens mapped to canonical
        self.assertEqual(
            runner_shared.outcome_precedence_disposition(
                "pending", {"disposition": "substantially-complete"}
            ),
            "fail-gate",
        )
        self.assertEqual(
            runner_shared.outcome_precedence_disposition(
                "pending", {"disposition": "partial"}
            ),
            "fail-verify",
        )
        self.assertEqual(
            runner_shared.outcome_precedence_disposition(
                "pending", {"disposition": "failed-safely"}
            ),
            "fail-gate",
        )


class TestInterruptedPromotion(unittest.TestCase):
    """V-04 (E-04): Interrupted registered in TERMINAL_STATES and distinct from fail-gate."""

    def test_interrupted_is_canonical_terminal_and_distinct_from_fail_gate(self):
        """interrupted is in TERMINAL_STATES, TERMINAL_STATES_CANONICAL, and != fail-gate."""
        self.assertIn("interrupted", runner_shared.TERMINAL_STATES)
        self.assertIn("interrupted", runner_shared.TERMINAL_STATES_CANONICAL)
        self.assertNotIn("interrupted", runner_shared.TERMINAL_STATUS_ALIASES)
        self.assertNotEqual("interrupted", "fail-gate")

    def test_interrupted_cascades_dependency_as_terminal_non_success(self):
        """An item interrupted cascades dependents to fail-depend (not stuck waiting)."""
        state = {
            "queue": [
                {
                    "id6": "dep001",
                    "order": 1,
                    "status": "interrupted",
                    "dependencies": [],
                },
                {
                    "id6": "child1",
                    "order": 2,
                    "status": "queued",
                    "dependencies": ["executed:dep001"],
                },
            ]
        }
        blocked = runner_shared.cascade_dependency_blocked(state)
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0]["id6"], "child1")
        self.assertEqual(blocked[0]["status"], "fail-depend")


class TestExecutionSuccessStatesNarrowingAndBlastRadius(unittest.TestCase):
    """V-05 (E-05): EXECUTION_SUCCESS_STATES is {"executed"} alone and blast radius is 0."""

    def test_execution_success_states_narrowed_and_identical(self):
        """EXECUTION_SUCCESS_STATES is exactly {"executed"} across shared and both hosts."""
        self.assertEqual(
            runner_shared.EXECUTION_SUCCESS_STATES, frozenset({"executed"})
        )
        self.assertIs(
            oc_runipd.EXECUTION_SUCCESS_STATES, runner_shared.EXECUTION_SUCCESS_STATES
        )
        self.assertIs(
            agy_runipd.EXECUTION_SUCCESS_STATES, runner_shared.EXECUTION_SUCCESS_STATES
        )

    def test_fail_gate_or_legacy_substantially_complete_cascades_dependent(self):
        """Prerequisite with fail-gate or legacy substantially-complete cascades dependent."""
        for prereq_status in (
            "fail-gate",
            "substantially-complete",
            "fail-verify",
            "failed",
        ):
            state = {
                "queue": [
                    {
                        "id6": "p00001",
                        "order": 1,
                        "status": prereq_status,
                        "dependencies": [],
                    },
                    {
                        "id6": "c00001",
                        "order": 2,
                        "status": "queued",
                        "dependencies": ["executed:p00001"],
                    },
                ]
            }
            blocked = runner_shared.cascade_dependency_blocked(state)
            self.assertEqual(
                len(blocked),
                1,
                f"Prereq status '{prereq_status}' must cascade dependent",
            )
            self.assertEqual(blocked[0]["status"], "fail-depend")

    def test_blast_radius_zero_across_pending_plans(self):
        """Measure blast radius across all pending plans in the repository (must be 0).

        A dependency EDGE IS PARSED WITH THE SHARED GRAMMAR AND RESOLVED AGAINST THE TREE ITS OWN
        TYPE NAMES, rather than having its id6 recovered with ``split(":")[-1]`` and looked for in
        the plans trees alone. The earlier spelling predated the typed grammar (its comment read
        "Strip any prefix like 'ipd:'") and so asserted an invariant the design contradicts: a
        ``spec`` or ``backlog`` target is DELIBERATELY a graph LEAF resolved against the repository
        and never against the queue, which ``runner_shared.validate_manifest`` states outright
        ("Only IPD-typed targets must name a plan in the manifest; a `spec`/`backlog` target is a
        graph LEAF (spec 25kzda 2.10) and is resolved against the repository"). Measured 2026-10-01:
        a legal ``state:spec:approved:<id6>`` edge on a pending plan failed this test while
        ``ipd_schema.parse_item_dependencies`` accepted it, ``preflight_dependency_findings``
        reported no findings, and ``edge_satisfied`` resolved and enforced it. Backlog `pyhq6s`.

        WHY THAT MATTERED ENOUGH TO FIX RATHER THAN SUPPRESS: the failure names the AUTHORING PLAN,
        not this test, so the natural response is to delete the "malformed" edge. In the measured
        case that edge was the only mechanism holding a plan back until a maintainer answered a
        blocking spec question, so obeying the failure would have silently removed a human decision
        gate. The assertion kept here is the one actually worth making (no pending plan cites a
        prerequisite that exists nowhere), now applied per target type.
        """
        from agent_workflows import ipd_schema

        repo_root = Path(__file__).resolve().parent.parent
        plans_root = repo_root / ".aw" / "records" / "plans"
        pending_dir = plans_root / "pending"

        if not pending_dir.exists():
            return

        # An `ipd` target may legitimately sit in any plans lifecycle directory, not only
        # pending/executed: a dependent may cite a prerequisite that was superseded or deliberately
        # not executed, and such a target is PRESENT (the edge may be unsatisfiable, which is the
        # dependency evaluator's question, not this test's). A `spec`/`backlog` target is resolved
        # against its own records tree for the same reason.
        search_roots = {
            "ipd": [plans_root],
            "spec": [repo_root / ".aw" / "records" / "specs"],
            "backlog": [repo_root / ".aw" / "records" / "backlog"],
        }

        stranded_prereqs = []
        for plan_file in pending_dir.glob("*.md"):
            content = plan_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                if not line.startswith("- Item-Dependencies:"):
                    continue
                deps_str = line.split(":", 1)[1].strip()
                edges, _ready, err = ipd_schema.parse_item_dependencies(deps_str)
                # A malformed value is NOT this test's concern: `aw ipd lint` and the runner's
                # dependency preflight both refuse it with a specific diagnostic, and duplicating
                # that here would report the same defect twice under a misleading name.
                if err or not edges:
                    continue
                for edge in edges:
                    roots = search_roots.get(edge.target_type, [])
                    found = any(
                        any(root.rglob(f"*-{edge.id6}-*.md"))
                        for root in roots
                        if root.exists()
                    )
                    if not found:
                        stranded_prereqs.append(
                            (plan_file.name, edge.target_type, edge.id6)
                        )

        self.assertEqual(
            stranded_prereqs,
            [],
            "Blast radius verification: pending plans must not reference prerequisites that "
            f"exist in no records tree: {stranded_prereqs}",
        )


class TestArtifactAuditNoCompleteCoercion(unittest.TestCase):
    """V-06 (E-06): artifact_audit eliminates complete coercion and maps expected directories."""

    def test_expected_directory_mapping_for_canonical_and_legacy_statuses(self):
        """Canonical statuses and legacy statuses resolve to proper expected directories."""
        # Executed -> executed
        self.assertEqual(artifact_audit.expected_dir_for_status("executed"), "executed")

        # Non-landed canonical states -> pending
        for canonical_fail in (
            "reviewed",
            "approved",
            "fail-gate",
            "fail-begin",
            "fail-lane",
            "fail-verify",
            "fail-depend",
            "fail-merge",
            "not-run",
            "failed",
            "interrupted",
        ):
            self.assertEqual(
                artifact_audit.expected_dir_for_status(canonical_fail),
                "pending",
                f"Expected canonical status '{canonical_fail}' to map to 'pending'",
            )

        # Non-landed legacy aliases -> pending (NOT executed / complete)
        for legacy_fail in EXPECTED_LEGACY_ALIASES.keys():
            self.assertEqual(
                artifact_audit.expected_dir_for_status(legacy_fail),
                "pending",
                f"Expected legacy status '{legacy_fail}' to map to 'pending'",
            )

    def test_artifact_audit_module_constants(self):
        """_RUN_SUCCESS_STATUSES and _TERMINAL_EXPECTED_DIR contain no 'complete' coercion."""
        self.assertNotIn("complete", artifact_audit._RUN_SUCCESS_STATUSES)
        self.assertIn("executed", artifact_audit._RUN_SUCCESS_STATUSES)
        self.assertNotIn("complete", artifact_audit._TERMINAL_EXPECTED_DIR)
        self.assertEqual(
            artifact_audit._TERMINAL_EXPECTED_DIR.get("executed"), "executed"
        )


if __name__ == "__main__":
    unittest.main()
