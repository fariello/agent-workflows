"""Tests for RUN finding code reachability prover, validation, and accessors (f7z10q).

OBEYS P16 AND THE AGENT CONTRACT:
- No inspection of production source code via inspect, ast, regex, or substring search.
- No assertions on caller counts, symbol censuses, or comment banners.
- Call graph prover behavior is tested against synthesized fixtures in tmp_path.
- Predicate resolution is tested by importlib and getattr runtime resolution.
- Enforces observable behavior and outcomes.
"""

from __future__ import annotations

import importlib
from pathlib import Path
import re
import tempfile
import unittest

from agent_workflows import run_evidence
from agent_workflows.run_evidence import (
    BOUND,
    REACHABLE,
    UNREACHABLE,
    UNRESOLVED,
    bound_run_finding_codes,
    bound_run_finding_codes_reachability,
    predicate_verdicts_for,
    prove_predicate_reachability,
    validate_finding_table,
)


class TestRunFindingReachability(unittest.TestCase):
    """Behavioral outcome tests for reachability prover, table validator, and partition accessors."""

    def test_prover_behavior_on_synthesized_fixtures(self) -> None:
        """Case (a): Prover returns reachable, unreachable, and unresolved on synthesized modules."""
        with tempfile.TemporaryDirectory() as td:
            pkg = Path(td)
            entry_py = pkg / "synth_entry.py"
            target_py = pkg / "synth_target.py"

            entry_py.write_text(
                "import synth_target\n\n"
                "def top_level_runner():\n"
                "    synth_target.reachable_action()\n",
                encoding="utf-8",
            )
            target_py.write_text(
                "def reachable_action():\n"
                "    return True\n\n"
                "def uncalled_action():\n"
                "    return False\n\n"
                "class TargetService:\n"
                "    def active_method(self):\n"
                "        return 1\n",
                encoding="utf-8",
            )

            # Reachable target
            v_reachable = prove_predicate_reachability(
                "synth_target.reachable_action",
                entrypoints=("synth_entry",),
                package_dir=pkg,
            )
            self.assertEqual(v_reachable, REACHABLE)

            # Uncalled target
            v_uncalled = prove_predicate_reachability(
                "synth_target.uncalled_action",
                entrypoints=("synth_entry",),
                package_dir=pkg,
            )
            self.assertEqual(v_uncalled, UNREACHABLE)

            # Uncalled class method
            v_uncalled_method = prove_predicate_reachability(
                "synth_target.TargetService.active_method",
                entrypoints=("synth_entry",),
                package_dir=pkg,
            )
            self.assertEqual(v_uncalled_method, UNREACHABLE)

            # Unresolved target in existing module
            v_unresolved_sym = prove_predicate_reachability(
                "synth_target.nonexistent_symbol",
                entrypoints=("synth_entry",),
                package_dir=pkg,
            )
            self.assertEqual(v_unresolved_sym, UNRESOLVED)

            # Unresolved module
            v_unresolved_mod = prove_predicate_reachability(
                "nonexistent_module.some_fn",
                entrypoints=("synth_entry",),
                package_dir=pkg,
            )
            self.assertEqual(v_unresolved_mod, UNRESOLVED)

    def test_every_bound_code_has_resolving_predicate_anti_rot(self) -> None:
        """Case (b): Every BOUND row has at least one predicate that resolves (anti-rot property)."""
        bound_codes_found = 0
        for row in run_evidence.RUN_FINDING_CODES:
            if row.binding != BOUND:
                continue
            bound_codes_found += 1
            self.assertTrue(
                row.predicates,
                f"BOUND row {row.code} must declare at least one predicate",
            )
            resolving_count = 0
            for pred in row.predicates:
                base = re.sub(r"\[.*\]$", "", pred)
                mod_name, _, attr_path = base.partition(".")
                if not mod_name.startswith("agent_workflows."):
                    full_mod_name = f"agent_workflows.{mod_name}"
                else:
                    full_mod_name = mod_name
                try:
                    module = importlib.import_module(full_mod_name)
                    obj = module
                    for part in attr_path.split("."):
                        obj = getattr(obj, part)
                    if obj is not None:
                        resolving_count += 1
                except (ImportError, AttributeError):
                    pass
            self.assertGreater(
                resolving_count,
                0,
                f"BOUND row {row.code} has no resolving predicate; binding has rotted",
            )
        self.assertGreater(bound_codes_found, 0)

    def test_validate_finding_table_clean_on_shipped_table(self) -> None:
        """Case (c): validate_finding_table returns no findings on the shipped table."""
        res = validate_finding_table()
        self.assertTrue(res.ok)
        self.assertEqual(res.findings, ())

    def test_unreachable_binding_refusal_fires_under_perturbation(self) -> None:
        """Case (d): RC-UNREACHABLE-BINDING fires when a BOUND row has no reachable predicates."""
        orig = run_evidence.RUN_FINDING_CODES
        try:
            # Perturb a row to name only unreachable predicates
            # worktree_lease.LeaseTable.held_by is unreachable
            perturbed_rows = []
            target_code = "RUN-HOST-CAPABILITY"
            for row in orig:
                if row.code == target_code:
                    perturbed_rows.append(
                        row._replace(predicates=("worktree_lease.LeaseTable.held_by",))
                    )
                else:
                    perturbed_rows.append(row)
            run_evidence.RUN_FINDING_CODES = tuple(perturbed_rows)

            res = validate_finding_table()
            self.assertFalse(res.ok)
            finding_codes = [f.code for f in res.findings]
            self.assertIn("RC-UNREACHABLE-BINDING", finding_codes)

            unreachable_finding = next(
                f for f in res.findings if f.code == "RC-UNREACHABLE-BINDING"
            )
            self.assertEqual(unreachable_finding.where, target_code)
            self.assertIn(target_code, unreachable_finding.message)
            self.assertIn(
                "worktree_lease.LeaseTable.held_by", unreachable_finding.message
            )

            # Second perturbation: BOUND row with one reachable predicate beside unreachable ones passes
            mixed_rows = []
            for row in orig:
                if row.code == target_code:
                    mixed_rows.append(
                        row._replace(
                            predicates=(
                                "host_sandbox_profile.preflight_host_capabilities",  # reachable
                                "worktree_lease.LeaseTable.held_by",  # unreachable
                            )
                        )
                    )
                else:
                    mixed_rows.append(row)
            run_evidence.RUN_FINDING_CODES = tuple(mixed_rows)
            res_mixed = validate_finding_table()
            self.assertTrue(res_mixed.ok)
            self.assertEqual(res_mixed.findings, ())

        finally:
            run_evidence.RUN_FINDING_CODES = orig

        # Restored table validates clean
        res_restored = validate_finding_table()
        self.assertTrue(res_restored.ok)
        self.assertEqual(res_restored.findings, ())

    def test_partition_accessor_agrees_with_per_row_verdicts(self) -> None:
        """Case (e): Partition accessor agrees with per-row verdicts for every BOUND row."""
        partition = bound_run_finding_codes_reachability()
        bound_codes = bound_run_finding_codes()

        # Completeness and disjointness
        self.assertEqual(
            set(partition.reachable) | set(partition.unreachable),
            set(bound_codes),
        )
        self.assertEqual(
            set(partition.reachable) & set(partition.unreachable),
            set(),
        )

        # Agreement with per-row verdicts
        for row in run_evidence.RUN_FINDING_CODES:
            if row.binding != BOUND:
                continue
            verdicts = predicate_verdicts_for(row)
            if any(v == REACHABLE for v in verdicts.values()):
                self.assertIn(row.code, partition.reachable)
                self.assertNotIn(row.code, partition.unreachable)
            else:
                self.assertIn(row.code, partition.unreachable)
                self.assertNotIn(row.code, partition.reachable)


if __name__ == "__main__":
    unittest.main()
