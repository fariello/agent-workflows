"""Tests for awoptimize Order 14 (`h1d5aa`): migration disposition inventory + shared families.

Covers the E-04 acceptance:
  * E-01: the completeness tool proves EVERY manifest row (command + lens + persona) and the
    non-invokable conformance package has EXACTLY ONE reviewed disposition + a valid canonical
    target, with ZERO silent omissions, and aliases distinguishable from independent workflows.
    Falsifiable: injecting an omission / a duplicate / an invalid target / an alias-that-targets-
    itself each makes a named assertion fail.
  * E-02: every assess lens resolves through the ONE assess harness and every advise persona through
    the ONE advise harness; a lens/persona that forks the harness lifecycle/evidence is REJECTED;
    the rollup requires explicit scope/cost confirmation and de-duplicates its members.
  * E-03: `plan-review` and `plan-review-long` compile from ONE package, share the semantic digest +
    arguments, both names are aliases, and a mutation of EITHER generated view is detected as drift.

Stdlib `unittest`, matching the repository convention.
"""

from __future__ import annotations

import copy
import unittest
from pathlib import Path

from agent_workflows import migration_inventory as MI
from agent_workflows import workflow_loader as LOADER
from tests.support import SOURCE_WORKFLOWS

FIXTURE_PKG = (
    Path(__file__).resolve().parent / "fixtures" / "workflow-src" / "plan-review"
)


# ==================================================================================================
# E-01: disposition inventory + completeness tool
# ==================================================================================================


class InventoryCompletenessTests(unittest.TestCase):
    def setUp(self):
        self.result = MI.build_inventory(SOURCE_WORKFLOWS)

    def test_inventory_is_complete_and_valid(self):
        self.assertTrue(self.result.ok, self.result.findings)

    def test_every_manifest_row_dispositioned_exactly_once(self):
        from agent_workflows import engine

        workflows = engine.parse_manifest(Path(SOURCE_WORKFLOWS))
        manifest_subjects = [w.command for w in workflows]
        # exactly one: no duplicates, no omissions among the manifest rows.
        self.assertEqual(len(manifest_subjects), len(set(manifest_subjects)))
        for cmd in manifest_subjects:
            self.assertIn(
                cmd, self.result.dispositions, "no disposition for {0}".format(cmd)
            )
        # plus the conformance package == manifest rows + 1.
        self.assertEqual(len(self.result.dispositions), len(manifest_subjects) + 1)

    def test_conformance_package_dispositioned_once_as_non_invokable(self):
        d = self.result.dispositions[MI.CONFORMANCE_TARGET]
        self.assertEqual(d.kind, "conformance")
        self.assertEqual(d.execution_mode, "non-invokable")

    def test_lenses_and_personas_present(self):
        lenses = [d for d in self.result.dispositions.values() if d.kind == "lens"]
        personas = [d for d in self.result.dispositions.values() if d.kind == "persona"]
        self.assertGreaterEqual(len(lenses), 30)
        self.assertEqual(len(personas), 7)
        # every lens resolves to the ONE `assess` package; every persona to the ONE `advise` package.
        self.assertTrue(all(d.canonical_package == "assess" for d in lenses))
        self.assertTrue(all(d.canonical_package == "advise" for d in personas))

    def test_aliases_distinguishable_from_independent_workflows(self):
        aliases = {s for s, d in self.result.dispositions.items() if d.is_alias}
        self.assertIn("plan-review-long", aliases)
        self.assertIn("release-review-plan", aliases)
        # an alias targets ANOTHER subject's canonical package (not its own id).
        for s in aliases:
            d = self.result.dispositions[s]
            self.assertNotEqual(d.canonical_package, s)
        # an independent workflow targets its OWN id.
        indep = self.result.dispositions["setup-repo"]
        self.assertFalse(indep.is_alias)
        self.assertEqual(indep.canonical_package, "setup-repo")

    # ---- falsifiable: the tool DETECTS omission / duplication / invalid target ----

    def test_detects_silent_omission(self):
        from agent_workflows import engine

        workflows = engine.parse_manifest(Path(SOURCE_WORKFLOWS))
        dispositions = dict(self.result.dispositions)
        # drop one disposition -> a silent omission the tool must catch.
        del dispositions["setup-repo"]
        findings = MI.check_completeness(dispositions, workflows, SOURCE_WORKFLOWS)
        self.assertTrue(
            any("setup-repo" in f and "NO disposition" in f for f in findings)
        )

    def test_detects_disposition_for_nonexistent_row(self):
        from agent_workflows import engine

        workflows = engine.parse_manifest(Path(SOURCE_WORKFLOWS))
        dispositions = dict(self.result.dispositions)
        dispositions["ghost-workflow"] = MI.Disposition(
            subject="ghost-workflow",
            kind="command",
            family="scaffold",
            canonical_package="ghost-workflow",
            execution_mode="deterministic",
            interaction="optional",
            risk="low",
            skill_decision="no-skill",
            orchestration_decision="single-context",
            evidence_level="inspection",
            migration_owner="order-16",
        )
        findings = MI.check_completeness(dispositions, workflows, SOURCE_WORKFLOWS)
        self.assertTrue(
            any("ghost-workflow" in f and "does not correspond" in f for f in findings)
        )

    def test_detects_alias_targeting_own_id(self):
        from agent_workflows import engine

        workflows = engine.parse_manifest(Path(SOURCE_WORKFLOWS))
        dispositions = dict(self.result.dispositions)
        bad = MI.Disposition(
            subject="plan-review-long",
            kind="command",
            family="plan review aliases",
            canonical_package="plan-review-long",  # alias points at itself: not distinguishable
            execution_mode="shared-harness",
            interaction="interactive",
            risk="low",
            skill_decision="skill",
            orchestration_decision="bounded-runtime",
            evidence_level="inspection",
            migration_owner="order-14",
            is_alias=True,
        )
        dispositions["plan-review-long"] = bad
        findings = MI.check_completeness(dispositions, workflows, SOURCE_WORKFLOWS)
        self.assertTrue(
            any("plan-review-long" in f and "own id" in f for f in findings)
        )

    def test_detects_invalid_vocabulary(self):
        d = MI.Disposition(
            subject="x",
            kind="command",
            family="scaffold",
            canonical_package="x",
            execution_mode="bogus-mode",  # invalid
            interaction="optional",
            risk="low",
            skill_decision="no-skill",
            orchestration_decision="single-context",
            evidence_level="inspection",
        )
        self.assertTrue(any("execution_mode" in p for p in d.validate()))

    def test_order14_ownership_fence_detects_out_of_scope_claim(self):
        from agent_workflows import engine

        workflows = engine.parse_manifest(Path(SOURCE_WORKFLOWS))
        dispositions = dict(self.result.dispositions)
        # scaffold is Order-16 scope; claiming order-14 for it must be flagged.
        d = dispositions["scaffold"]
        dispositions["scaffold"] = MI.Disposition(
            subject=d.subject,
            kind=d.kind,
            family=d.family,
            canonical_package=d.canonical_package,
            execution_mode=d.execution_mode,
            interaction=d.interaction,
            risk=d.risk,
            skill_decision=d.skill_decision,
            orchestration_decision=d.orchestration_decision,
            evidence_level=d.evidence_level,
            aliases=d.aliases,
            migration_owner="order-14",
            is_alias=d.is_alias,
        )
        findings = MI.check_completeness(dispositions, workflows, SOURCE_WORKFLOWS)
        self.assertTrue(any("out of Order-14 scope" in f for f in findings))

    def test_agent_report_is_json(self):
        import json

        report = MI.render_agent_report(SOURCE_WORKFLOWS)
        obj = json.loads(report)
        self.assertTrue(obj["ok"])
        self.assertEqual(obj["count"], len(self.result.dispositions))


# ==================================================================================================
# E-02: shared assess/advise harness resolution + no-fork parity + rollup
# ==================================================================================================


class SharedHarnessTests(unittest.TestCase):
    def setUp(self):
        self.assess = MI.build_assess_harness(SOURCE_WORKFLOWS)
        self.advise = MI.build_advise_harness(SOURCE_WORKFLOWS)

    def test_every_lens_resolves_through_one_harness(self):
        digests = set()
        for concern in self.assess.lenses:
            hid, lens = self.assess.resolve_lens(concern)
            self.assertEqual(hid, "assess")
            self.assertEqual(lens.concern, concern)
            digests.add(self.assess.harness.semantic_digest())
        # ONE harness => ONE semantic digest across every lens resolution.
        self.assertEqual(len(digests), 1)

    def test_every_persona_resolves_through_one_harness(self):
        for persona in self.advise.personas:
            hid, mod = self.advise.resolve_persona(persona)
            self.assertEqual(hid, "advise")
            self.assertEqual(mod.persona, persona)

    def test_catalog_rows_all_bound_to_one_digest(self):
        rows = self.assess.catalog_rows()
        self.assertTrue(rows)
        self.assertEqual(len({r["semantic_digest"] for r in rows}), 1)

    def test_lens_fork_of_lifecycle_is_rejected(self):
        # A lens/persona contribution redefining a harness-reserved key is a fork.
        for key in (
            "lifecycle",
            "evidence",
            "steps",
            "validations",
            "mutation_boundary",
        ):
            with self.assertRaises(MI.HarnessForkError):
                MI.assert_no_lens_fork({key: "override"})

    def test_registering_forking_lens_is_rejected(self):
        class _ForkingLens(MI.LensModule):
            def contribution(self):  # type: ignore[override]
                base = dict(super().contribution())
                base["evidence"] = ["command"]  # attempt to fork the evidence contract
                return base

        fork = _ForkingLens(concern="rogue", lens_body="x", rubric_focus="y")
        with self.assertRaises(MI.HarnessForkError):
            self.assess.register_lens(fork)

    def test_clean_lens_contribution_has_no_reserved_keys(self):
        hid, lens = self.assess.resolve_lens(next(iter(self.assess.lenses)))
        self.assertFalse(set(lens.contribution().keys()) & MI.HARNESS_RESERVED_KEYS)

    def test_rollup_requires_explicit_confirmation(self):
        with self.assertRaises(MI.RollupConfirmationError):
            MI.plan_rollup(self.assess, ["security", "bugs"])

    def test_rollup_confirmed_dedups_members(self):
        plan = MI.plan_rollup(
            self.assess, ["security", "security", "bugs", "bugs"], confirmed=True
        )
        self.assertEqual(plan.members, ("security", "bugs"))
        self.assertEqual(plan.estimated_cost_units, 2)
        self.assertTrue(plan.confirmed)

    def test_rollup_all_defaults_to_full_lens_set(self):
        plan = MI.plan_rollup(self.assess, None, confirmed=True)
        self.assertEqual(set(plan.members), set(self.assess.lenses))

    def test_rollup_unknown_member_rejected(self):
        with self.assertRaises(MI.InventoryError):
            MI.plan_rollup(self.assess, ["no-such-lens"], confirmed=True)


# ==================================================================================================
# E-03: plan-review one source -> two views -> parity + drift detection
# ==================================================================================================


class PlanReviewCollapseTests(unittest.TestCase):
    def setUp(self):
        self.views = MI.compile_plan_review(FIXTURE_PKG)

    def test_both_names_compile_from_one_package(self):
        parity = MI.plan_review_parity(self.views)
        self.assertTrue(parity.ok, parity.reason)
        self.assertTrue(parity.aliases_ok)
        self.assertIn(MI.PLAN_REVIEW_ALIAS, self.views.aliases)

    def test_both_views_share_the_semantic_digest(self):
        # Both the single-file view and the long step-packet view derive from the SAME compiled
        # projection, so there is ONE semantic digest covering both (they cannot diverge).
        parity = MI.plan_review_parity(self.views)
        self.assertEqual(parity.semantic_digest, self.views.semantic_digest())
        # re-compiling the same package yields the same semantic digest (stable).
        again = MI.compile_plan_review(FIXTURE_PKG)
        self.assertEqual(again.semantic_digest(), self.views.semantic_digest())

    def test_views_share_arguments(self):
        descriptor = self.views.compiled["command_descriptor"]
        self.assertIsNotNone(descriptor.get("takes_argument"))

    def test_mutation_of_single_file_view_detected_as_drift(self):
        mutated = copy.deepcopy(self.views)
        object.__setattr__(
            mutated, "single_file", self.views.single_file + "\n<!-- tampered -->\n"
        )
        self.assertTrue(MI.detect_view_drift(self.views, mutated, "single_file"))
        # the long view is unchanged, so no drift there.
        self.assertFalse(MI.detect_view_drift(self.views, mutated, "long"))

    def test_mutation_of_long_view_detected_as_drift(self):
        mutated = copy.deepcopy(self.views)
        long_list = list(copy.deepcopy(self.views.long))
        long_list[0] = dict(long_list[0])
        long_list[0]["action"] = long_list[0]["action"] + " TAMPERED"
        object.__setattr__(mutated, "long", tuple(long_list))
        self.assertTrue(MI.detect_view_drift(self.views, mutated, "long"))

    def test_identical_views_show_no_drift(self):
        again = MI.compile_plan_review(FIXTURE_PKG)
        self.assertFalse(MI.detect_view_drift(self.views, again, "single_file"))
        self.assertFalse(MI.detect_view_drift(self.views, again, "long"))

    def test_from_ir_seam_matches_compile(self):
        ir = LOADER.load_package(FIXTURE_PKG).ir
        assert ir is not None
        views = MI.plan_review_views_from_ir(ir)
        self.assertEqual(views.semantic_digest(), self.views.semantic_digest())


if __name__ == "__main__":
    unittest.main()
