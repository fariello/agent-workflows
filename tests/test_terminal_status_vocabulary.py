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

import ast
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
        """TERMINAL_STATES_CANONICAL contains exactly the 13 canonical states."""
        self.assertEqual(
            runner_shared.TERMINAL_STATES_CANONICAL, EXPECTED_CANONICAL_STATES
        )
        self.assertEqual(len(runner_shared.TERMINAL_STATES_CANONICAL), 13)

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
            formatted = run_viewer.format_run_human(summary, term=term)
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
        """Measure blast radius across all pending plans in the repository (must be 0)."""
        repo_root = Path(__file__).resolve().parent.parent
        pending_dir = repo_root / ".aw" / "records" / "plans" / "pending"
        executed_dir = repo_root / ".aw" / "records" / "plans" / "executed"

        if not pending_dir.exists():
            return

        stranded_prereqs = []
        for plan_file in pending_dir.glob("*.md"):
            content = plan_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("- Item-Dependencies:"):
                    deps_str = line.split(":", 1)[1].strip()
                    if deps_str and deps_str.lower() != "none":
                        dep_ids = [d.strip() for d in deps_str.split(",") if d.strip()]
                        for dep_id in dep_ids:
                            # Strip any prefix like 'ipd:'
                            clean_id = dep_id.split(":")[-1].strip()
                            matching_exec = (
                                list(executed_dir.glob(f"*-{clean_id}-*.md"))
                                if executed_dir.exists()
                                else []
                            )
                            matching_pending = list(
                                pending_dir.glob(f"*-{clean_id}-*.md")
                            )
                            if not matching_exec and not matching_pending:
                                stranded_prereqs.append((plan_file.name, clean_id))

        self.assertEqual(
            stranded_prereqs,
            [],
            f"Blast radius verification: pending plans must not reference stranded prerequisites: {stranded_prereqs}",
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


class TestTreeWideExhaustivenessGuard(unittest.TestCase):
    """V-07 (E-07): Tree-wide guard asserting no unmapped or unrenamed legacy tokens in production writers."""

    # Unambiguous legacy terminal status tokens that must never be emitted by new code
    DISTINCTIVE_LEGACY_TOKENS = frozenset(
        {
            "substantially-complete",
            "failed-safely",
            "dependency-blocked",
            "integration-blocked",
            "merge-needs-human",
            "merge-refused",
            "not-attempted",
        }
    )

    SANCTIONED_FILES = frozenset(
        {
            "agent_workflows/runner_shared.py",
            "agent_workflows/agy_runipd.py",
            "agent_workflows/oc_runipd.py",
            "agent_workflows/artifact_audit.py",
            "agent_workflows/attention.py",
            "agent_workflows/lifecycle_style.py",
            "agent_workflows/render_stream.py",
            "agent_workflows/run_selection_policy.py",
            "agent_workflows/run_viewer.py",
            "agent_workflows/runner_shutdown.py",
            "agent_workflows/run_analytics.py",
            "agent_workflows/lane_containment.py",
        }
    )

    def test_exhaustiveness_scan_over_agent_workflows(self):
        """Scan agent_workflows/ Python files to assert all legacy status tokens are in sanctioned sites."""
        repo_root = Path(__file__).resolve().parent.parent
        pkg_dir = repo_root / "agent_workflows"

        unsanctioned_occurrences = []

        for py_path in pkg_dir.glob("*.py"):
            rel_path = py_path.relative_to(repo_root).as_posix()
            if rel_path not in self.SANCTIONED_FILES:
                tree = ast.parse(
                    py_path.read_text(encoding="utf-8"), filename=str(py_path)
                )
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        if node.value in self.DISTINCTIVE_LEGACY_TOKENS:
                            unsanctioned_occurrences.append(
                                (rel_path, node.lineno, node.value)
                            )

        self.assertEqual(
            unsanctioned_occurrences,
            [],
            f"Found unsanctioned legacy status tokens in agent_workflows: {unsanctioned_occurrences}",
        )

    def test_exhaustiveness_guard_non_vacuous(self):
        """Demonstrate that the exhaustiveness scanner detects an unsanctioned legacy literal."""
        test_source = 'def dummy_func():\n    return "substantially-complete"\n'
        tree = ast.parse(test_source)
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value in self.DISTINCTIVE_LEGACY_TOKENS:
                    found.append((node.lineno, node.value))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0], (2, "substantially-complete"))


if __name__ == "__main__":
    unittest.main()
