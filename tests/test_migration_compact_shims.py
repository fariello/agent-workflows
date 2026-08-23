"""Tests for awoptimize Order 16 (`g6zjao`): compact-workflow migration, shims, promotion gates.

Covers the E-04 acceptance with FALSIFIABLE fixtures that assert DETECTION/REJECTION, never mere
smoke:

  * E-01 compact workflows: every one of the nine compact commands is a live manifest row, resolves
    its body dir via the manifest (research -> research-prompt/, NOT dir==command), carries a valid
    typed input/output + read/write-boundary + interaction contract, and needs NO subagent. A NEGATIVE
    fixture proves a package flagged needs_subagent=True is REJECTED (needless orchestration).
  * E-02 shims/skills: every compatibility command resolves the correct package + canonical digest;
    argument golden parity holds; a HAND-EDITED generated shim FAILS the drift check; a selected
    skill resolves the correct package/digest; old invocations still work.
  * E-03 promotion gates: a family meeting its risk threshold is ADVERTISED as migrated; a family
    FAILING its gate records a legacy fallback + a corrective backlog item and is NOT advertised.
    A NEGATIVE fixture proves the gate cannot be weakened to force a pass (invariant-guarded).

Stdlib `unittest`, matching the repository convention.
"""

from __future__ import annotations

import unittest

from agent_workflows import engine as ENGINE
from agent_workflows import host_adapters as ADAPTERS
from agent_workflows import migration_compact as MCC
from agent_workflows.benchmark_metrics import MetricSummary
from agent_workflows.benchmark_thresholds import (
    RiskThresholds,
    ThresholdError,
    ThresholdPolicy,
)
from tests.support import SOURCE_WORKFLOWS


# ==================================================================================================
# E-01: compact workflows -- typed contract, boundary, interaction, negative (no needless subagent)
# ==================================================================================================


class CompactContractTests(unittest.TestCase):
    def test_all_nine_compact_commands_are_live_manifest_rows(self) -> None:
        """Completeness: none of the nine compact commands is invented or dropped."""
        findings = MCC.check_compact_completeness(SOURCE_WORKFLOWS)
        self.assertEqual(
            findings, [], "compact completeness must be clean: {0}".format(findings)
        )
        self.assertEqual(len(MCC.COMPACT_COMMANDS), 9)

    def test_research_body_dir_is_research_prompt_not_command_name(self) -> None:
        """PR-001: research resolves to research-prompt/ via the manifest, NOT dir==command."""
        self.assertEqual(
            MCC.resolve_body_dir("research", SOURCE_WORKFLOWS), "research-prompt"
        )
        pkg = MCC.build_compact_package("research", SOURCE_WORKFLOWS)
        self.assertIn("research-prompt/research-prompt.md", pkg.body)
        # A dir==command assumption would resolve to "research"; prove we did not do that.
        self.assertNotEqual(
            MCC.resolve_body_dir("research", SOURCE_WORKFLOWS), "research"
        )

    def test_every_compact_package_has_valid_typed_contract(self) -> None:
        """Typed input/output + read/write-boundary + interaction contract validity for all nine."""
        packages = MCC.build_all_compact_packages(SOURCE_WORKFLOWS)
        self.assertEqual(sorted(packages), sorted(MCC.COMPACT_COMMANDS))
        for cmd, pkg in packages.items():
            self.assertEqual(
                pkg.contract.validate(), [], "{0} contract invalid".format(cmd)
            )
            self.assertIn(pkg.contract.mode, MCC.COMPACT_MODES)
            self.assertIn(pkg.contract.write_boundary, MCC.WRITE_BOUNDARIES)
            self.assertIn(pkg.contract.interaction, MCC.INTERACTIONS)
            self.assertTrue(pkg.contract.input_kind)
            self.assertTrue(pkg.contract.output_kind)

    def test_deterministic_first_packages_name_a_reusable_script(self) -> None:
        """A deterministic-first package must name the script doing its load-bearing work."""
        packages = MCC.build_all_compact_packages(SOURCE_WORKFLOWS)
        for cmd, pkg in packages.items():
            if pkg.contract.mode == MCC.MODE_DETERMINISTIC_FIRST:
                self.assertTrue(
                    pkg.contract.script,
                    "{0} deterministic-first names no script".format(cmd),
                )

    def test_no_compact_package_needs_a_subagent(self) -> None:
        """The no-needless-orchestration invariant: not one compact package needs a subagent."""
        for cmd in MCC.COMPACT_COMMANDS:
            pkg = MCC.build_compact_package(cmd, SOURCE_WORKFLOWS)
            self.assertFalse(pkg.contract.needs_subagent)
            MCC.assert_no_needless_subagent(pkg)  # must not raise

    def test_negative_needless_subagent_is_rejected(self) -> None:
        """NEGATIVE: a compact contract that declares needs_subagent=True is REJECTED."""
        bad = MCC.TypedContract(
            command="getting-started",
            mode=MCC.MODE_SINGLE_CONTEXT,
            input_kind="context",
            output_kind="recommendation",
            write_boundary=MCC.WRITE_READ_ONLY,
            interaction="optional",
            needs_subagent=True,
        )
        problems = bad.validate()
        self.assertTrue(
            any("needless orchestration" in p for p in problems),
            "a needs_subagent contract must be flagged: {0}".format(problems),
        )
        pkg = MCC.CompactPackage(
            command="getting-started",
            canonical_package="getting-started",
            body=".aw/system/workflows/getting-started/getting-started.md",
            contract=bad,
            semantic_digest="deadbeef",
        )
        with self.assertRaises(MCC.CompactMigrationError):
            MCC.assert_no_needless_subagent(pkg)

    def test_negative_non_compact_command_is_refused(self) -> None:
        """NEGATIVE: building a compact package for a non-compact command fails closed."""
        with self.assertRaises(MCC.CompactMigrationError):
            MCC.build_compact_package("release-review", SOURCE_WORKFLOWS)

    def test_negative_bad_vocabulary_is_flagged(self) -> None:
        """NEGATIVE: an out-of-vocabulary mode/boundary/interaction is detected."""
        bad = MCC.TypedContract(
            command="x",
            mode="orchestrated-fanout",
            input_kind="",
            output_kind="",
            write_boundary="wipe-repo",
            interaction="chatty",
        )
        problems = bad.validate()
        self.assertTrue(any("bad mode" in p for p in problems))
        self.assertTrue(any("bad write_boundary" in p for p in problems))
        self.assertTrue(any("bad interaction" in p for p in problems))


# ==================================================================================================
# E-02: shim/skill resolution + argument parity + drift + old invocations
# ==================================================================================================


class ShimAndSkillTests(unittest.TestCase):
    def test_every_compact_command_generates_a_shim(self) -> None:
        """Interaction/evidence: the generator emits a shim for every compact command per host."""
        projection = MCC.generate_compact_projection(SOURCE_WORKFLOWS)
        for cmd in MCC.COMPACT_COMMANDS:
            matches = projection.shim_for(cmd)
            self.assertTrue(matches, "no shim generated for '{0}'".format(cmd))
            # one per shim dir (opencode + claude at minimum).
            self.assertGreaterEqual(len(matches), 2)

    def test_shim_resolves_correct_package_and_digest(self) -> None:
        """Every compatibility command resolves the correct body + canonical digest."""
        for cmd in MCC.COMPACT_COMMANDS:
            pkg = MCC.build_compact_package(cmd, SOURCE_WORKFLOWS)
            res = MCC.resolve_shim(cmd, SOURCE_WORKFLOWS)
            self.assertEqual(res.command, cmd)
            self.assertIn(
                cmd if cmd != "research" else "research-prompt", res.body_target
            )
            self.assertEqual(res.semantic_digest, pkg.semantic_digest)

    def test_argument_golden_parity_holds_for_every_compact_command(self) -> None:
        """Argument golden parity: generated shim's $ARGUMENTS matches the manifest arg behavior."""
        for cmd in MCC.COMPACT_COMMANDS:
            self.assertTrue(
                MCC.argument_parity(cmd, SOURCE_WORKFLOWS),
                "argument parity failed for '{0}'".format(cmd),
            )

    def test_hand_edited_shim_fails_drift_check(self) -> None:
        """NEGATIVE/drift: a HAND-EDITED generated shim is DETECTED as drift."""
        by_command = {w.command: w for w in ENGINE.parse_manifest(SOURCE_WORKFLOWS)}
        w = by_command["getting-started"]
        baseline = ENGINE.shim_body(
            "getting-started", w, "opencode", target_layout="aw"
        )
        # A regeneration of the identical shim is NOT drift.
        regenerated = ENGINE.shim_body(
            "getting-started", w, "opencode", target_layout="aw"
        )
        self.assertFalse(MCC.detect_shim_drift(baseline, regenerated))
        # A hand-edit (append a stray line) IS drift.
        tampered = baseline + "\nHAND EDIT: do something sneaky.\n"
        self.assertTrue(MCC.detect_shim_drift(baseline, tampered))

    def test_selected_skill_resolves_correct_package_and_digest(self) -> None:
        """Every selected skill entry point resolves its package's canonical digest (no silent drift)."""
        projection = MCC.generate_compact_projection(SOURCE_WORKFLOWS)
        packages = MCC.build_all_compact_packages(SOURCE_WORKFLOWS)
        self.assertTrue(
            projection.skill_packages, "expected at least one selected skill"
        )
        for cmd, skill in projection.skill_packages.items():
            self.assertIn(cmd, packages)
            self.assertTrue(
                MCC.skill_resolves_package(packages[cmd], skill),
                "skill '{0}' does not resolve its package/digest".format(cmd),
            )
            # falsifiable: the skill carries valid YAML frontmatter + the canonical digest, and is
            # disable-safe (its explicit invocation points at the canonical body).
            findings = ADAPTERS.validate_skill_package(skill)
            self.assertNotIn(
                "router does not carry the canonical semantic digest", findings
            )
            self.assertTrue(ADAPTERS.disabled_skill_still_invocable(skill))

    def test_negative_skill_bound_to_wrong_digest_is_detected(self) -> None:
        """NEGATIVE: a skill carrying the wrong digest does NOT resolve its package."""
        projection = MCC.generate_compact_projection(SOURCE_WORKFLOWS)
        packages = MCC.build_all_compact_packages(SOURCE_WORKFLOWS)
        cmd, skill = next(iter(projection.skill_packages.items()))
        # Point the package at a different digest than the skill carries.
        drifted = MCC.CompactPackage(
            command=packages[cmd].command,
            canonical_package=packages[cmd].canonical_package,
            body=packages[cmd].body,
            contract=packages[cmd].contract,
            semantic_digest="0" * 64,
        )
        self.assertFalse(MCC.skill_resolves_package(drifted, skill))

    def test_old_invocations_still_work(self) -> None:
        """Old invocations MUST keep working: each compact command's legacy shim is valid + points."""
        for cmd in MCC.COMPACT_COMMANDS:
            self.assertTrue(
                MCC.old_invocation_still_works(cmd, SOURCE_WORKFLOWS),
                "old invocation broke for '{0}'".format(cmd),
            )

    def test_generator_is_reused_not_forked(self) -> None:
        """The module REUSES engine.generate_shim_members; the shims match the engine generator's."""
        workflows = ENGINE.parse_manifest(SOURCE_WORKFLOWS)
        direct = ENGINE.generate_shim_members(
            workflows, SOURCE_WORKFLOWS, target_layout="aw"
        )
        projection = MCC.generate_compact_projection(SOURCE_WORKFLOWS)
        self.assertEqual(projection.shims, direct)
        # And the re-exported symbol IS the engine's function object.
        self.assertIs(MCC.generate_shim_members, ENGINE.generate_shim_members)
        self.assertIs(MCC.shim_body, ENGINE.shim_body)


# ==================================================================================================
# E-03: per-family promotion gates -- pass -> advertised; fail -> legacy fallback + corrective item
# ==================================================================================================


class PromotionGateTests(unittest.TestCase):
    def _passing_metrics(self) -> MetricSummary:
        return MCC.build_metric_summary(
            requirement_recall=1.0,
            task_correctness=1.0,
            evidence_validity=1.0,
            test_integrity=1.0,
            critical_escapes=0,
            scope_violations=0,
        )

    def _failing_metrics(self) -> MetricSummary:
        return MCC.build_metric_summary(
            requirement_recall=0.5,
            task_correctness=0.4,
            evidence_validity=1.0,
            test_integrity=1.0,
            critical_escapes=0,
            scope_violations=0,
        )

    def test_passing_family_is_advertised_as_migrated(self) -> None:
        """A family meeting its risk threshold passes -> advertised as migrated, no corrective item."""
        d = MCC.evaluate_promotion_gate(
            "list-workflows/verify", self._passing_metrics(), "low"
        )
        self.assertTrue(d.passed)
        self.assertEqual(d.migration_path, MCC.PATH_MIGRATED)
        self.assertTrue(d.advertised)
        self.assertIsNone(d.corrective_item)
        self.assertIn("list-workflows/verify", MCC.advertised_families([d]))

    def test_failing_family_falls_back_to_legacy_with_corrective_item(self) -> None:
        """A failing family stays legacy with a corrective backlog item and is NOT advertised."""
        d = MCC.evaluate_promotion_gate(
            "whatnext/handoff", self._failing_metrics(), "high"
        )
        self.assertFalse(d.passed)
        self.assertEqual(d.migration_path, MCC.PATH_LEGACY_FALLBACK)
        self.assertFalse(d.advertised)
        item = d.corrective_item
        self.assertIsNotNone(item)
        assert item is not None
        self.assertEqual(item.family, "whatnext/handoff")
        self.assertEqual(item.status, "open")
        self.assertTrue(item.findings)
        self.assertNotIn("whatnext/handoff", MCC.advertised_families([d]))
        self.assertIn("whatnext/handoff", MCC.legacy_fallback_families([d]))

    def test_mixed_families_partition_correctly(self) -> None:
        """A passing + a failing family partition into advertised vs legacy-fallback sets."""
        passing = MCC.evaluate_promotion_gate("f-pass", self._passing_metrics(), "low")
        failing = MCC.evaluate_promotion_gate(
            "f-fail", self._failing_metrics(), "medium"
        )
        decisions = [passing, failing]
        self.assertEqual(MCC.advertised_families(decisions), ("f-pass",))
        self.assertEqual(list(MCC.legacy_fallback_families(decisions)), ["f-fail"])

    def test_gate_reuses_order13_and_cannot_be_weakened(self) -> None:
        """NEGATIVE: the Order-13 policy REJECTS weakening a non-negotiable invariant (no force-pass)."""
        # Attempting to relax the zero-critical-escapes invariant must raise, so no agent can weaken
        # the threshold to force a family to pass.
        weakened = RiskThresholds(
            risk_class="low",
            min_requirement_recall=0.0,
            min_task_correctness=0.0,
            min_test_integrity=0.0,
            max_critical_escapes=5,  # forbidden: must be 0
            min_evidence_validity=1.0,
            max_scope_violations=99,
            max_unconfirmed_assumptions=0,
        )
        with self.assertRaises(ThresholdError):
            ThresholdPolicy(thresholds_by_risk={"low": weakened})

    def test_critical_escape_fails_gate_even_with_perfect_quality(self) -> None:
        """A single critical seeded escape fails the gate regardless of other metrics (invariant)."""
        m = MCC.build_metric_summary(
            requirement_recall=1.0,
            task_correctness=1.0,
            evidence_validity=1.0,
            critical_escapes=1,
        )
        d = MCC.evaluate_promotion_gate("f", m, "low")
        self.assertFalse(d.passed)
        self.assertFalse(d.advertised)


# ==================================================================================================
# Agent-facing report
# ==================================================================================================


class ReportTests(unittest.TestCase):
    def test_report_is_deterministic_json_and_clean(self) -> None:
        report = MCC.render_agent_report(SOURCE_WORKFLOWS)
        again = MCC.render_agent_report(SOURCE_WORKFLOWS)
        self.assertEqual(report, again)
        import json

        data = json.loads(report)
        self.assertEqual(data["compact_completeness_findings"], [])
        self.assertEqual(sorted(data["packages"]), sorted(MCC.COMPACT_COMMANDS))


if __name__ == "__main__":
    unittest.main()
