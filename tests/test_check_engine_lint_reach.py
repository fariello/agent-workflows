"""Tests for lintreach Order 01 (`k9awrq`): `check.ipd-lint-diagnostic`.

THE DEFECT UNDER TEST. `aw check plans` did not run `ipd_lint`, so the ENTIRE `IPD-*` diagnostic family
was invisible to the repo-wide sweep and therefore to CI. `check_engine` called `ipd_lint.parse` in
three places but never `lint_file`, so a defect the per-file verb REFUSES could be committed and would
sit in the tree until someone linted that exact file or tried to execute it. The motivating case is
`IPD-M107`: a fabricated `- Readiness:` asserting a review that never happened, which the auto-approve
predicate reads FIRST, so the sweep's blindness sat directly upstream of the `reviewed -> approved`
promotion gate.

Covers:
* V-01/V-02 - the sweep calls the REAL `ipd_lint.lint_file` at the `author` checkpoint, proved by
  DRIVING it (a spy observes the call and its keyword) rather than by reading source text.
* V-02 - the emitted code is REGISTERED, carries `info` severity, and therefore cannot move an exit
  code, with the `warning`-is-not-advisory trap asserted directly against `drift_exit_code`.
* V-03 - the covered set is the PENDING lane, and `aw check`-shaped and `aw doctor`-shaped traversals
  lint an IDENTICAL FILE COUNT (not merely produce identical findings, which a zero-finding tree would
  satisfy vacuously).
* V-04 - the motivating fabricated-`Readiness` case is reported by the sweep AFTER the change and was
  SILENT before it, with the before state asserted rather than assumed.
* V-05 - the sweep adds no finding on a conformant tree, and one plan yields at most one Drift.

EVERY fixture is an ISOLATED tmp repo built under `tempfile.mkdtemp`. No assertion reads this
repository's live plans: injecting a fabricated `- Readiness:` into a tracked plan would forge an
attestation and would (correctly) trip the corpus guard in `tests/test_ipd_lint.py`.

WHY THE "BEFORE" STATE IS SIMULATED BY DELETION RATHER THAN BY A GIT CHECKOUT. The contrast V-04 wants
is "the sweep was silent before this change and reports now". A test cannot run the pre-change code, so
`PreChangeContrastTests` establishes the equivalent CONTEMPORARY fact, which is strictly stronger than a
historical claim: with `check_ipd_lint_reach` removed from the plans content path, `check_content`
reports NOTHING about a plan that `aw ipd lint` refuses; with it wired, it reports. That is the same
inversion the defect describes and it is measured against the shipped code, so it keeps failing if
someone unwires the call site later, which a snapshot of history would not.

NO `inspect.getsource` PIN IS USED ANYWHERE HERE, following the reasoning recorded in
`tests/test_durable_capture.py`: a substring search for `lint_file` is satisfied by a COMMENT naming it
(this module's own docstrings name it repeatedly), and its negation is satisfied in the wrong direction
by the same code reached under an alias. Both directions are therefore proved by OBSERVING behavior -
the spy sees the real call, and the sentinel's own text must surface in the finding.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from typing import List, Optional
from unittest import mock

from agent_workflows import artifact_core as core
from agent_workflows import check_engine as ce
from agent_workflows import ipd_lint

RULE = "check.ipd-lint-diagnostic"


# --------------------------------------------------------------------------------------
# Isolated fixture builders
# --------------------------------------------------------------------------------------


def _mkrepo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="aw_lintreach_"))
    for lane in ("pending", "executed", "superseded", "not-executed"):
        (d / ".aw" / "records" / "plans" / lane).mkdir(parents=True)
    return d


def _plan(
    repo: Path,
    *,
    id6: str = "fab001",
    lane: str = "pending",
    readiness: Optional[str] = None,
    history_review: bool = False,
) -> Path:
    """A minimal CONFORMANT plan, optionally carrying a fabricated `- Readiness:`.

    With `readiness` set and `history_review` False the ONLY `author`-phase diagnostic is `IPD-M107`
    (verified by :meth:`FixtureIsolationTests.test_the_fixture_isolates_exactly_one_diagnostic`), so
    every assertion below is about THIS rule's reachability and not about incidental metadata gaps.
    """
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / lane
        / "20260901-lreach-01-{0}-fabricated-readiness.ipd.md".format(id6)
    )
    readiness_line = (
        "- Readiness: {0}\n".format(readiness) if readiness is not None else ""
    )
    history = "- 2026-09-01 to-review (t): created.\n"
    if history_review:
        history += "- 2026-09-02 reviewed (t): /plan-review complete: APPROVE.\n"
    status = "executed" if lane != "pending" else "to-review"
    p.write_text(
        "# IPD: lint-reach fixture {0}\n\n"
        "- Date: 2026-09-01\n- Kind: child\n"
        "- Concern: a fixture isolating the fabricated-Readiness rule\n"
        "- Scope: nothing; this is a test fixture\n"
        "- Scope-Paths: x.py\n- Item-Dependencies: none\n"
        "- Status: {1}\n{2}- Set: lreach\n- Order: 1\n"
        "- Highest E allocated: 01\n- Author: fixture\n- Id: {0}\n\n"
        "## Workflow history\n{3}\n"
        "## Goal\n\ng\n\n"
        "## Detailed Implementation Checklist (TODO)\n\n"
        "### Task group 1: do the thing\n\n"
        "- [ ] E-01 DO THE THING.\n"
        "  - Depends on: none\n"
        "  - Expected outcome: the thing is done\n"
        "  - Execution state: pending\n\n"
        "## Project conventions discovered (Step 0)\n\n- none\n\n"
        "## Findings\n\n| Id | Severity | Area | What | Evidence |\n|---|---|---|---|---|\n"
        "| F-1 | LOW | x | y | z |\n\n"
        "## Proposed changes (ordered, validatable)\n\n1. do the thing\n\n"
        "## Deferred / out of scope (with reason)\n\n"
        "- nothing deferred.\n  - Carrier-Declined: not a defect.\n\n"
        "## Scope check\n\n- Over-scope: none\n- Under-scope: none\n\n"
        "## Required tests / validation\n\nthe suite\n\n"
        "## Spec / documentation sync\n\nnone\n\n"
        "## Open questions\n\nnone\n\n"
        "## Validation and cross-check (verify before reporting done)\n\n"
        "- [ ] V-01 validates E-01\n"
        "  - Required evidence: paste it\n"
        "  - Observed evidence:\n"
        "  - Result: pending\n\n"
        "## Approval and execution gate\n\n- Size assessment: standard\n"
        "- Cohesion rationale: not required\n".format(
            id6, status, readiness_line, history
        ),
        encoding="utf-8",
    )
    return p


def _rule_findings(drift) -> List[core.Drift]:
    return [d for d in drift if d.rule == RULE]


class _RepoCase(unittest.TestCase):
    def setUp(self):
        self.repo = _mkrepo()

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)


# --------------------------------------------------------------------------------------
# The fixture's own isolation (so every later assertion is about THIS rule)
# --------------------------------------------------------------------------------------


class FixtureIsolationTests(_RepoCase):
    def test_the_fixture_isolates_exactly_one_diagnostic(self):
        """A fabricated-`Readiness` fixture yields `IPD-M107` and NOTHING ELSE at `author`.

        Asserted rather than assumed because an earlier draft of this fixture omitted `Concern`,
        `Scope` and `Author` and produced three extra `IPD-M101` diagnostics, which would have let
        every assertion below pass for the wrong reason.
        """
        p = _plan(self.repo, readiness="go-pending-approval")
        res = ipd_lint.lint_file(p, checkpoint="author")
        self.assertEqual([d.code for d in res.diagnostics], ["IPD-M107"])

    def test_the_same_fixture_without_the_fabrication_is_conformant(self):
        """The control. Without `- Readiness:` the fixture lints clean, so a finding below is caused
        by the fabrication and not by the fixture's shape."""
        p = _plan(self.repo, readiness=None)
        res = ipd_lint.lint_file(p, checkpoint="author")
        self.assertEqual(res.diagnostics, [])
        self.assertTrue(res.passing)

    def test_an_attested_readiness_is_accepted(self):
        """`IPD-M107` refuses an UNATTESTED value, not the field. With a review verdict in the history
        the same `Readiness` is fine, which is what makes the rule a forgery check rather than a ban."""
        p = _plan(self.repo, readiness="go-pending-approval", history_review=True)
        res = ipd_lint.lint_file(p, checkpoint="author")
        self.assertEqual(res.diagnostics, [])


# --------------------------------------------------------------------------------------
# V-04: the motivating case is now reachable from the sweep, and was not before
# --------------------------------------------------------------------------------------


class MotivatingCaseTests(_RepoCase):
    def test_the_sweep_reports_the_fabricated_readiness_plan(self):
        """THE WHOLE POINT. `aw check plans`' content path now reports a plan whose `- Readiness:`
        asserts a review that never happened."""
        p = _plan(self.repo, readiness="go-pending-approval")
        found = _rule_findings(ce.check_content(self.repo, "plans"))
        self.assertEqual(len(found), 1, "expected exactly one umbrella finding")
        self.assertEqual(found[0].location, str(p))
        self.assertIn("IPD-M107", found[0].detail)
        self.assertIn("Readiness", found[0].detail)

    def test_the_sweep_is_silent_on_a_conformant_plan(self):
        """The contrast that makes the test above evidence: an identical plan WITHOUT the fabrication
        produces no finding, so the rule is not simply reporting every plan."""
        _plan(self.repo, readiness=None)
        self.assertEqual(_rule_findings(ce.check_content(self.repo, "plans")), [])

    def test_the_finding_names_the_per_file_verb_that_explains_it(self):
        """The umbrella-code decision (plan OQ-01) is only honest if an operator can get the detail.
        The recovery command must be the per-file verb AT THE SAME CHECKPOINT."""
        p = _plan(self.repo, readiness="go-pending-approval")
        found = _rule_findings(ce.check_ipd_lint_reach(self.repo))
        self.assertEqual(len(found), 1)
        self.assertIn("aw ipd lint", found[0].recovery)
        self.assertIn(str(p), found[0].recovery)
        self.assertIn("--phase author", found[0].recovery)

    def test_the_two_surfaces_agree_on_the_same_fixture(self):
        """One implementation, so `aw ipd lint` and the sweep cannot disagree about conformance.

        Both directions are asserted on the SAME fixture file, mutated in place, because agreement in
        only the failing direction would also be satisfied by a sweep that reports everything.
        """
        p = _plan(self.repo, readiness="go-pending-approval")
        self.assertFalse(ipd_lint.lint_file(p, checkpoint="author").passing)
        self.assertEqual(len(_rule_findings(ce.check_ipd_lint_reach(self.repo))), 1)

        p.unlink()
        _plan(self.repo, readiness=None)
        self.assertTrue(ipd_lint.lint_file(p, checkpoint="author").passing)
        self.assertEqual(_rule_findings(ce.check_ipd_lint_reach(self.repo)), [])


class PreChangeContrastTests(_RepoCase):
    def test_removing_the_call_site_restores_the_original_silence(self):
        """V-04's BEFORE state, established against the shipped code rather than against history.

        With `check_ipd_lint_reach` neutralized, `check_content`'s plans path reports NOTHING about a
        plan `aw ipd lint` refuses, which is precisely the defect this plan closes: the per-file verb
        errors while the tree-wide verdict is silent. Wired, it reports. Because the assertion is
        driven through `check_content` (the real call site) rather than through the sweep function, it
        also fails if someone later deletes the wiring while leaving the function behind.
        """
        p = _plan(self.repo, readiness="go-pending-approval")
        self.assertFalse(
            ipd_lint.lint_file(p, checkpoint="author").passing,
            "precondition: the per-file verb must refuse this plan",
        )
        with mock.patch.object(ce, "check_ipd_lint_reach", return_value=[]):
            before = ce.check_content(self.repo, "plans")
        self.assertEqual(
            _rule_findings(before),
            [],
            "BEFORE: the sweep was blind to a lint-refusable defect",
        )
        after = ce.check_content(self.repo, "plans")
        self.assertEqual(
            len(_rule_findings(after)),
            1,
            "AFTER: the sweep reports what the per-file verb refuses",
        )


# --------------------------------------------------------------------------------------
# V-02: the real linter is called, at the right checkpoint, with no rule re-implemented
# --------------------------------------------------------------------------------------


class SharedImplementationTests(_RepoCase):
    def test_the_sweep_calls_the_real_lint_file_at_the_author_checkpoint(self):
        """Proved by DRIVING the call, not by reading source text.

        The keyword is asserted explicitly because `lint_file`'s API keyword is `checkpoint` while the
        CLI flag is `--phase`: a call using `phase=` raises, and inside a broad `except` (which this
        sweep deliberately has, for fail-isolation) it would report ZERO for every file - which looks
        exactly like a clean tree. This test is what makes that failure mode impossible to ship
        silently.
        """
        _plan(self.repo, readiness="go-pending-approval")
        real = ipd_lint.lint_file
        seen = []

        def spy(path, **kwargs):
            seen.append(kwargs)
            return real(path, **kwargs)

        with mock.patch.object(ipd_lint, "lint_file", side_effect=spy):
            ce.check_ipd_lint_reach(self.repo)
        self.assertEqual(
            len(seen), 1, "the one pending plan must be linted exactly once"
        )
        self.assertEqual(seen[0].get("checkpoint"), "author")
        self.assertNotIn(
            "phase", seen[0], "the API keyword is `checkpoint`, not `phase`"
        )

    def test_one_implementation_backs_both_surfaces(self):
        """A sentinel diagnostic invented in `ipd_lint` must surface through `aw check`'s sweep.

        This is the property that makes the two surfaces unable to drift: the sweep has no rules of its
        own, so whatever `lint_file` reports is what it reports. Stated as a fact about OUTPUT rather
        than about spelling, so an alias or a re-implementation under another name cannot satisfy it.
        """
        _plan(
            self.repo, readiness=None
        )  # a CONFORMANT plan, so only the sentinel can fire
        sentinel = ipd_lint.LintResult(
            "error",
            [ipd_lint.Diagnostic(0, 0, "IPD-SENTINEL", "invented by the test")],
            [],
        )
        with mock.patch.object(ipd_lint, "lint_file", return_value=sentinel):
            found = _rule_findings(ce.check_ipd_lint_reach(self.repo))
        self.assertEqual(len(found), 1)
        self.assertIn("IPD-SENTINEL", found[0].detail)
        self.assertIn("invented by the test", found[0].detail)

    def test_a_lint_failure_never_breaks_the_sweep(self):
        """Fail-isolation, matching every neighbouring plans-type rule. A linter that raises must cost
        this rule's finding, never the whole `aw check` run."""
        _plan(self.repo, readiness="go-pending-approval")
        with mock.patch.object(ipd_lint, "lint_file", side_effect=RuntimeError("boom")):
            drift = ce.check_content(self.repo, "plans")
        self.assertEqual(_rule_findings(drift), [])

    def test_the_sweep_checkpoint_constant_is_author(self):
        """The phase is a CONSTANT, not a parameter of the sweep. `pre-transition` was measured at 1199
        diagnostics across all 76 pending plans (1196 `IPD-S404`, the correct state of an unexecuted
        plan), so a configurable phase is a mass-failure waiting to be 'improved' into existence."""
        self.assertEqual(ce._IPD_LINT_SWEEP_CHECKPOINT, "author")


# --------------------------------------------------------------------------------------
# V-02: the rule id is registered, and its severity is advisory IN BEHAVIOR
# --------------------------------------------------------------------------------------


class RuleRegistrationTests(unittest.TestCase):
    def test_the_rule_is_registered_and_not_falling_back_to_the_default(self):
        """An UNREGISTERED code silently inherits `_DEFAULT_RULESPEC`, which is `error` with an EMPTY
        invariant - so omitting the registration would give the STRICTEST behavior by accident, which
        is the worst outcome available. Asserted by identity against the fallback, not just by value."""
        self.assertIn(RULE, ce.RULE_REGISTRY)
        spec = ce.rule_spec(RULE)
        self.assertIsNot(spec, ce._DEFAULT_RULESPEC)
        self.assertEqual(spec.severity, "info")
        self.assertEqual(spec.assurance, ce.ASSURANCE_REPOSITORY)
        self.assertEqual(spec.determinism, ce.DET_DETERMINISTIC)
        self.assertEqual(spec.invariant, "I-05")

    def test_info_is_the_only_severity_that_is_actually_advisory(self):
        """THE TRAP THIS RULE'S SEVERITY EXISTS TO AVOID, asserted against the real exit-code function.

        `artifact_core.drift_exit_code` exempts ONLY `info`. So registering `warning` would have
        satisfied the word 'advisory' while still driving a nonzero findings exit, which is why this
        rule is `info`. If a future change promotes the severity, THIS test is the one that must be
        deliberately updated, which is the intent.
        """
        for sev, expected in (("error", 1), ("warning", 1), ("info", 0), ("", 1)):
            with self.subTest(severity=sev):
                d = core.Drift("p", RULE, "d", severity=sev)
                self.assertEqual(core.drift_exit_code([d]), expected)

    def test_the_rules_own_findings_cannot_move_an_exit_code(self):
        """The composition of the two facts above, on a REAL finding rather than a hand-made one."""
        repo = _mkrepo()
        try:
            _plan(repo, readiness="go-pending-approval")
            found = _rule_findings(ce.check_ipd_lint_reach(repo))
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0].severity, "info")
            self.assertEqual(core.drift_exit_code(found), 0)
        finally:
            shutil.rmtree(repo, ignore_errors=True)


# --------------------------------------------------------------------------------------
# V-03: which dispositions are covered, and the check/doctor agreement
# --------------------------------------------------------------------------------------


class CoveredDispositionTests(_RepoCase):
    def test_only_the_pending_lane_is_swept(self):
        """The covered set, asserted by placing the SAME defective plan in each lane in turn."""
        for lane, expect in (
            ("pending", 1),
            ("executed", 0),
            ("superseded", 0),
            ("not-executed", 0),
        ):
            with self.subTest(lane=lane):
                p = _plan(self.repo, lane=lane, readiness="go-pending-approval")
                try:
                    self.assertEqual(
                        len(_rule_findings(ce.check_ipd_lint_reach(self.repo))), expect
                    )
                finally:
                    p.unlink()

    def test_excluding_terminal_plans_costs_no_coverage(self):
        """WHY the pending-lane scope is free rather than a compromise: `lint_text` returns
        `DISPOSITION_LEGACY` with NO diagnostics for a terminal-directory plan at `author`, so linting
        the terminal corpus could not produce a finding even if the sweep did traverse it."""
        p = _plan(self.repo, lane="executed", readiness="go-pending-approval")
        res = ipd_lint.lint_file(p, checkpoint="author")
        self.assertEqual(res.diagnostics, [])
        self.assertEqual(res.disposition, "legacy/not evaluated")

    def test_check_and_doctor_lint_an_identical_file_set(self):
        """OQ-02's REAL constraint, and the reason it is asserted on COUNTS rather than on findings.

        `_iter_type_files` skips retired paths unless `include_retired=True`; `executed/` counts as
        retired; `doctor.py` passes `include_retired=True` UNCONDITIONALLY while `check_engine` defaults
        it to False. That asymmetry already produced a measured zero-versus-one disagreement between
        the two surfaces on `check.id6-collision`. A findings comparison would pass vacuously on a
        clean tree, so the linted FILE SET is compared instead, on a tree deliberately holding plans in
        every lane.
        """
        _plan(self.repo, id6="pend01", lane="pending", readiness="go-pending-approval")
        _plan(self.repo, id6="exec01", lane="executed", readiness="go-pending-approval")
        _plan(
            self.repo, id6="supe01", lane="superseded", readiness="go-pending-approval"
        )

        def linted_paths(**kwargs) -> List[str]:
            seen: List[str] = []
            real = ipd_lint.lint_file

            def spy(path, **kw):
                seen.append(str(path))
                return real(path, **kw)

            with mock.patch.object(ipd_lint, "lint_file", side_effect=spy):
                ce.check_ipd_lint_reach(self.repo, **kwargs)
            return sorted(seen)

        as_check = linted_paths()  # `aw check` default
        as_doctor = linted_paths(include_untracked=True)  # `aw doctor`-shaped call
        self.assertEqual(as_check, as_doctor)
        self.assertEqual(
            len(as_check), 1, "exactly the one pending plan, under both surfaces"
        )
        self.assertIn("pending", as_check[0])


# --------------------------------------------------------------------------------------
# V-05: the report stays bounded, and a clean tree stays clean
# --------------------------------------------------------------------------------------


class ReportShapeTests(_RepoCase):
    def test_one_plan_yields_at_most_one_finding(self):
        """The bounded-report decision (mirroring `evaluate_durable_carrier`'s DECISION 07-rnkqrc-D4).
        A plan with many diagnostics must not add many lines to every `aw check plans`."""
        _plan(self.repo, readiness=None)
        many = ipd_lint.LintResult(
            "error",
            [
                ipd_lint.Diagnostic(0, 0, "IPD-X{0:03d}".format(i), "m{0}".format(i))
                for i in range(12)
            ],
            [],
        )
        with mock.patch.object(ipd_lint, "lint_file", return_value=many):
            found = _rule_findings(ce.check_ipd_lint_reach(self.repo))
        self.assertEqual(len(found), 1)
        self.assertIn("12 lint diagnostic(s)", found[0].detail)
        self.assertIn("(and 7 more)", found[0].detail)
        self.assertIn("IPD-X000", found[0].detail)
        self.assertNotIn("IPD-X011", found[0].detail)

    def test_an_empty_plans_tree_yields_nothing(self):
        self.assertEqual(ce.check_ipd_lint_reach(self.repo), [])

    def test_advisories_are_not_reported_as_diagnostics(self):
        """`LintResult.advisories` is the PASSING channel (`check.ipd-draft-ready-to-review`,
        `check_citation_anchors`, the density nudges). It already has its own reporting path, and it
        does not make a plan non-conforming, so this rule must read `diagnostics` only. Otherwise the
        sweep would newly report every plan carrying a nudge."""
        _plan(self.repo, readiness=None)
        advisory_only = ipd_lint.LintResult(
            "conforming",
            [],
            [ipd_lint.Diagnostic(0, 0, "IPD-ADVISORY", "just a nudge")],
        )
        with mock.patch.object(ipd_lint, "lint_file", return_value=advisory_only):
            self.assertEqual(_rule_findings(ce.check_ipd_lint_reach(self.repo)), [])

    def test_the_finding_carries_the_full_observed_required_recovery_shape(self):
        """The registry promises a machine-readable finding shape; an un-enriched Drift would serialize
        with empty `observed`/`required`, which is what makes a finding unactionable."""
        _plan(self.repo, readiness="go-pending-approval")
        found = _rule_findings(ce.check_ipd_lint_reach(self.repo))[0]
        self.assertIn("IPD-M107", found.observed)
        self.assertTrue(found.required)
        self.assertTrue(found.recovery)
        self.assertEqual(found.severity, "info")
        self.assertEqual(found.assurance, ce.ASSURANCE_REPOSITORY)
        self.assertEqual(found.determinism, ce.DET_DETERMINISTIC)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
