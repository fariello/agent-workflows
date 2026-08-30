"""Tests for revgate Order 02 (plqjt7): `check.review-finding-unescalated`.

An unfixed review finding at or above the configured severity threshold must carry a matching
`Blocking: yes` open question, on both host surfaces (`aw check` and phased `aw ipd lint`).

Covers:
* V-01 - the rule fires on an unescalated gating finding and is silent on an escalated one; it is
  reached by BOTH the plans-type path and the full `aw check all` sweep; a terminal-dir plan is
  grandfathered; the rule id resolves to a REGISTERED RuleSpec rather than the conservative default.
* V-02 - the same rule blocks at the `review-finalize` and `pre-execution` lint checkpoints, and
  `lint_text` stays PURE (it cannot see the separate artifact, so it never reports the rule).
* V-06 - threshold matrix (`medium`/`high`/`blocker`/`off`), `fixed` never fires, and current-round
  semantics (round 1 `open` -> round 2 `fixed` does NOT fire); plus the END-TO-END chain proving an
  escalated question is then caught by the PRE-EXISTING pre-execution gate.
* V-07 - the three E-07 failure modes: absent artifact is SILENT, malformed artifact is REPORTED,
  threshold `off` disables the rule.
* V-08 - the `- Finding: <F-id>` convention is matched as a TYPED subfield, per-finding, and a
  question naming a DIFFERENT id does not satisfy the requirement.

EVERY fixture is an ISOLATED tmp repo. No assertion reads this repository's live plans or live
`.aw/config/project.json`: asserting against live state is a known defect class here (see pending plan
`i79rgh`, Order testinvoke-02), and a threshold test that read the live config would be
order-dependent and would break the moment a maintainer set the key.

Workflow-body PARITY assertions deliberately live in `tests/test_plan_review_parity.py`, which already
owns single-file-vs-long parity for this pair; duplicating that harness here would be drift.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import ipd_lint
from agent_workflows import ipd_schema as S
from agent_workflows import review_findings as rf

RULE = "check.review-finding-unescalated"


# --------------------------------------------------------------------------------------
# Isolated fixture builders
# --------------------------------------------------------------------------------------


def _mkrepo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="aw_revgate02_"))
    for lane in ("pending", "executed", "superseded", "not-executed"):
        (d / ".aw" / "records" / "plans" / lane).mkdir(parents=True)
    (d / ".aw" / "records" / "reviews").mkdir(parents=True)
    (d / ".aw" / "config").mkdir(parents=True)
    return d


def _set_threshold(repo: Path, value: str | None) -> None:
    """Write (or remove) the `review_findings_gate` key in the FIXTURE's project.json."""
    pj = repo / ".aw" / "config" / "project.json"
    if value is None:
        if pj.exists():
            pj.unlink()
        return
    pj.write_text(
        json.dumps({"review_findings_gate": {"block_at": value}}), encoding="utf-8"
    )


def _oq(
    *, blocking: str = "yes", status: str = "open", finding: str | None = "F-1"
) -> str:
    lines = [
        "### OQ-01: does the gating finding stop execution?",
        "",
        f"- Blocking: {blocking}",
        f"- Status: {status}",
        "- Owner: maintainer",
    ]
    if finding is not None:
        lines.append(f"- Finding: {finding}")
    lines.append("- Resolution or deferral rationale: pending a maintainer decision")
    return "\n".join(lines) + "\n"


def _plan(
    repo: Path,
    *,
    id6: str = "aaa111",
    lane: str = "pending",
    open_questions: str = "",
    status: str = "approved",
) -> Path:
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / lane
        / f"20260829-demo-01-{id6}-gate-fixture.ipd.md"
    )
    body = (
        f"# IPD: gate fixture {id6}\n\n"
        f"- Date: 2026-08-29\n- Kind: child\n- Scope-Paths: x.py\n"
        f"- Item-Dependencies: none\n- Status: {status}\n- Set: demo\n- Order: 1\n"
        f"- Id: {id6}\n\n"
        f"## Workflow history\n- 2026-08-29 draft (t): created.\n\n## Goal\ng\n"
    )
    if open_questions:
        body += f"\n## Open questions\n\n{open_questions}"
    p.write_text(body, encoding="utf-8")
    return p


def _finding(
    fid: str = "F-1", severity: str = "high", decision: str = "open"
) -> rf.Finding:
    return rf.Finding(
        fid,
        severity,
        "IN-SCOPE",
        "rubric",
        "x.py:1",
        "the finding text",
        "Overall:Low",
        decision,
        "the resolution",
    )


def _review(repo: Path, *, id6: str = "aaa111", rounds=None) -> Path:
    if rounds is None:
        rounds = [rf.Round(1, (_finding(),), ())]
    return rf.write_review(
        repo / ".aw" / "records" / "reviews" / f"20260829-demo-01-{id6}-gate.review.md",
        plan_id=id6,
        reviewed_at="2026-08-29",
        reviewer="test",
        verdict="REVIEWED - OPEN QUESTIONS",
        rounds=rounds,
    )


def _rules(drift) -> list:
    return [d.rule for d in drift if d.rule == RULE]


class _RepoCase(unittest.TestCase):
    def setUp(self):
        self.repo = _mkrepo()

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)


# --------------------------------------------------------------------------------------
# V-01: the rule itself, its reach, its grandfathering, and its registration
# --------------------------------------------------------------------------------------


class RuleFiresTests(_RepoCase):
    def test_unescalated_gating_finding_is_reported(self):
        plan = _plan(self.repo)
        _review(self.repo)
        drift = ce.check_review_finding_unescalated(self.repo)
        self.assertEqual(_rules(drift), [RULE])
        self.assertEqual(drift[0].location, str(plan))
        self.assertIn("F-1", drift[0].detail)
        self.assertIn("high", drift[0].detail)

    def test_escalated_gating_finding_is_not_reported(self):
        _plan(self.repo, open_questions=_oq(finding="F-1"))
        _review(self.repo)
        self.assertEqual(_rules(ce.check_review_finding_unescalated(self.repo)), [])

    def test_finding_marked_fixed_never_fires(self):
        _plan(self.repo)
        _review(self.repo, rounds=[rf.Round(1, (_finding(decision="fixed"),), ())])
        self.assertEqual(_rules(ce.check_review_finding_unescalated(self.repo)), [])

    def test_deferred_is_unfixed_and_fires(self):
        """`deferred` is a deliberate decision NOT to fix, so it must gate exactly like `open`."""
        _plan(self.repo)
        _review(self.repo, rounds=[rf.Round(1, (_finding(decision="deferred"),), ())])
        drift = ce.check_review_finding_unescalated(self.repo)
        self.assertEqual(_rules(drift), [RULE])
        self.assertIn("deferred", drift[0].detail)

    def test_terminal_dir_plan_is_grandfathered(self):
        """The 400+ terminal plans must never be retroactively litigated."""
        for lane in ("executed", "superseded", "not-executed"):
            with self.subTest(lane=lane):
                repo = _mkrepo()
                try:
                    _plan(repo, lane=lane)
                    _review(repo)
                    self.assertEqual(
                        _rules(ce.check_review_finding_unescalated(repo)),
                        [],
                        f"a plan in {lane}/ must be grandfathered",
                    )
                finally:
                    shutil.rmtree(repo, ignore_errors=True)

    def test_drift_carries_actionable_recovery(self):
        _plan(self.repo)
        _review(self.repo)
        d = ce.check_review_finding_unescalated(self.repo)[0]
        self.assertIn("Blocking: yes", d.required)
        self.assertIn("F-1", d.required)
        self.assertIn("Finding: F-1", d.recovery)


class RuleReachTests(_RepoCase):
    """F-6/F-7: the rule must be reached by BOTH `aw check plans` and the `aw check all` fan-out."""

    def test_reported_by_plans_type_path(self):
        _plan(self.repo)
        _review(self.repo)
        drift = ce.check_types(self.repo, ["plans"])
        self.assertIn(RULE, [d.rule for d in drift])

    def test_reported_by_full_sweep_exactly_once(self):
        _plan(self.repo)
        _review(self.repo)
        drift = ce.check_types(self.repo, ["all"])
        hits = [d for d in drift if d.rule == RULE]
        self.assertEqual(
            len(hits),
            1,
            "the full sweep must surface the rule exactly once (no double-report)",
        )

    def test_clean_tree_passes_both_surfaces(self):
        _plan(self.repo, open_questions=_oq(finding="F-1"))
        _review(self.repo)
        for target in (["plans"], ["all"]):
            with self.subTest(target=target):
                self.assertEqual(
                    [
                        d.rule
                        for d in ce.check_types(self.repo, target)
                        if d.rule == RULE
                    ],
                    [],
                )


class RuleRegistrationTests(unittest.TestCase):
    def test_rule_id_resolves_to_a_registered_rulespec(self):
        """An UNREGISTERED id silently falls back to `_DEFAULT_RULESPEC` with an EMPTY invariant,
        which would leave the finding unclassified while the module claims none are."""
        spec = ce.rule_spec(RULE)
        self.assertIn(RULE, ce.RULE_REGISTRY)
        self.assertIsNot(spec, ce._DEFAULT_RULESPEC)
        self.assertEqual(spec.severity, "error")
        self.assertEqual(spec.assurance, ce.ASSURANCE_REPOSITORY)
        self.assertEqual(spec.determinism, ce.DET_DETERMINISTIC)

    def test_severity_comparison_is_delegated_not_reimplemented(self):
        """E-01 forbids a local severity comparison: it must call the shared `is_gating` predicate."""
        src = Path(ce.__file__).read_text(encoding="utf-8")
        start = src.index("def evaluate_review_finding_escalation")
        end = src.index("def check_review_finding_unescalated")
        body = src[start:end]
        self.assertIn(
            "is_gating(",
            body,
            "the evaluator must delegate to review_findings.is_gating",
        )
        for forbidden in ("_SEVERITY_RANK", "SEVERITIES.index", '"blocker"'):
            self.assertNotIn(
                forbidden,
                body,
                f"the evaluator must not re-implement severity ranking ({forbidden})",
            )


# --------------------------------------------------------------------------------------
# V-06: threshold matrix + current-round semantics
# --------------------------------------------------------------------------------------


class ThresholdTests(_RepoCase):
    def test_medium_ignored_at_high_but_caught_at_medium(self):
        _plan(self.repo)
        _review(self.repo, rounds=[rf.Round(1, (_finding(severity="medium"),), ())])

        _set_threshold(self.repo, "high")
        self.assertEqual(
            _rules(ce.check_review_finding_unescalated(self.repo)),
            [],
            "a medium finding must not gate at threshold high",
        )

        _set_threshold(self.repo, "medium")
        self.assertEqual(
            _rules(ce.check_review_finding_unescalated(self.repo)),
            [RULE],
            "a medium finding must gate at threshold medium",
        )

    def test_high_ignored_at_blocker(self):
        _plan(self.repo)
        _review(self.repo)
        _set_threshold(self.repo, "blocker")
        self.assertEqual(_rules(ce.check_review_finding_unescalated(self.repo)), [])

    def test_blocker_caught_at_every_active_threshold(self):
        _plan(self.repo)
        _review(self.repo, rounds=[rf.Round(1, (_finding(severity="blocker"),), ())])
        for thr in ("medium", "high", "blocker"):
            with self.subTest(threshold=thr):
                _set_threshold(self.repo, thr)
                self.assertEqual(
                    _rules(ce.check_review_finding_unescalated(self.repo)), [RULE]
                )

    def test_absent_key_defaults_to_high_and_gates(self):
        """The default is fail-CLOSED at `high`, so a fixture with NO key still gates."""
        _plan(self.repo)
        _review(self.repo)
        _set_threshold(self.repo, None)
        self.assertFalse((self.repo / ".aw" / "config" / "project.json").exists())
        self.assertEqual(_rules(ce.check_review_finding_unescalated(self.repo)), [RULE])


class CurrentRoundTests(_RepoCase):
    def test_round1_open_then_round2_fixed_does_not_fire(self):
        """Current-round semantics (15zvu6 E-03): a superseded finding is not live."""
        _plan(self.repo)
        _review(
            self.repo,
            rounds=[
                rf.Round(1, (_finding(decision="open"),), ()),
                rf.Round(2, (_finding(decision="fixed"),), ()),
            ],
        )
        self.assertEqual(_rules(ce.check_review_finding_unescalated(self.repo)), [])

    def test_round1_fixed_then_round2_open_does_fire(self):
        """The converse: a finding REOPENED by the current round is live again."""
        _plan(self.repo)
        _review(
            self.repo,
            rounds=[
                rf.Round(1, (_finding(decision="fixed"),), ()),
                rf.Round(2, (_finding(decision="open"),), ()),
            ],
        )
        self.assertEqual(_rules(ce.check_review_finding_unescalated(self.repo)), [RULE])


# --------------------------------------------------------------------------------------
# V-07: the three E-07 failure modes, none of them inherited from an exception swallow
# --------------------------------------------------------------------------------------


class FailureModeTests(_RepoCase):
    """Absent is SILENT, malformed is REPORTED, `off` DISABLES. Same plan fixture in all three."""

    def test_absent_artifact_is_silent(self):
        _plan(self.repo)
        self.assertEqual(list(rf.iter_review_files(self.repo)), [])
        self.assertEqual(_rules(ce.check_review_finding_unescalated(self.repo)), [])

    def test_malformed_artifact_is_reported(self):
        """A file that EXISTS but cannot be trusted is an error, not an absence. Treating it as an
        absence is the evasion path F-8 identified."""
        _plan(self.repo)
        bad = (
            self.repo
            / ".aw"
            / "records"
            / "reviews"
            / "20260829-demo-01-aaa111-gate.review.md"
        )
        bad.write_text(
            "# review\n\n- Plan-Id: aaa111\n- Reviewed-At: 2026-08-29\n"
            "- Reviewer: test\n- Verdict: v\n\nthis file has no rounds at all\n",
            encoding="utf-8",
        )
        drift = ce.check_review_finding_unescalated(self.repo)
        self.assertEqual(_rules(drift), [RULE])
        self.assertIn("malformed", drift[0].detail)
        self.assertEqual(
            drift[0].location,
            str(bad),
            "the malformed case reports the REVIEW path to repair",
        )

    def test_malformed_row_with_unknown_severity_is_reported(self):
        """A `HGIH` typo would slip past `is_gating` silently, so the parser diagnostic must gate."""
        _plan(self.repo)
        _review(self.repo, rounds=[rf.Round(1, (_finding(severity="hgih"),), ())])
        drift = ce.check_review_finding_unescalated(self.repo)
        self.assertEqual(_rules(drift), [RULE])
        self.assertIn("malformed", drift[0].detail)

    def test_threshold_off_disables_the_rule_entirely(self):
        _plan(self.repo)
        _review(self.repo)
        _set_threshold(self.repo, "off")
        self.assertEqual(_rules(ce.check_review_finding_unescalated(self.repo)), [])
        self.assertEqual(
            [d.rule for d in ce.check_types(self.repo, ["plans"]) if d.rule == RULE], []
        )

    def test_malformed_branch_is_explicit_not_an_exception_swallow(self):
        """The malformed finding must come from a deliberate branch on parser diagnostics."""
        src = Path(ce.__file__).read_text(encoding="utf-8")
        start = src.index("def evaluate_review_finding_escalation")
        end = src.index("def check_review_finding_unescalated")
        body = src[start:end]
        self.assertIn(
            "if doc.diagnostics:",
            body,
            "the malformed case must branch explicitly on parser diagnostics",
        )


# --------------------------------------------------------------------------------------
# V-02: the lint checkpoints, and lint_text purity
# --------------------------------------------------------------------------------------


class LintCheckpointTests(_RepoCase):
    def test_blocks_at_review_finalize_and_pre_execution(self):
        plan = _plan(self.repo)
        _review(self.repo)
        for phase in ("review-finalize", "pre-execution"):
            with self.subTest(phase=phase):
                res = ipd_lint.lint_file(plan, checkpoint=phase)
                self.assertEqual(res.disposition, S.DISPOSITION_ERROR)
                self.assertIn(RULE, [d.code for d in res.diagnostics])

    def test_escalated_plan_reports_no_escalation_diagnostic(self):
        plan = _plan(self.repo, open_questions=_oq(finding="F-1"))
        _review(self.repo)
        for phase in ("review-finalize", "pre-execution"):
            with self.subTest(phase=phase):
                res = ipd_lint.lint_file(plan, checkpoint=phase)
                self.assertNotIn(RULE, [d.code for d in res.diagnostics])

    def test_pre_transition_is_deliberately_not_gated(self):
        """By the time a plan finalizes, execution already happened; blocking there only strands it."""
        plan = _plan(self.repo)
        _review(self.repo)
        res = ipd_lint.lint_file(plan, checkpoint="pre-transition")
        self.assertNotIn(RULE, [d.code for d in res.diagnostics])

    def test_lint_text_stays_pure(self):
        """E-02's contract: the findings live in a SEPARATE file, so the pure text linter cannot and
        must not report this rule."""
        plan = _plan(self.repo)
        _review(self.repo)
        text = plan.read_text(encoding="utf-8")
        for phase in ("review-finalize", "pre-execution"):
            with self.subTest(phase=phase):
                res = ipd_lint.lint_text(text, checkpoint=phase, directory="pending")
                self.assertNotIn(
                    RULE,
                    [d.code for d in res.diagnostics],
                    "lint_text must not see the separate review artifact",
                )

    def test_lint_text_body_adds_no_file_read(self):
        src = Path(ipd_lint.__file__).read_text(encoding="utf-8")
        start = src.index("def lint_text(")
        end = src.index("def _draft_ready_advisory")
        body = src[start:end]
        for forbidden in ("read_text", "open(", "iter_review_files", "evaluate_review"):
            self.assertNotIn(
                forbidden, body, f"lint_text must remain pure (found {forbidden})"
            )

    def test_checkpoint_consumes_already_parsed_open_questions(self):
        src = Path(ipd_lint.__file__).read_text(encoding="utf-8")
        start = src.index("def _merge_review_escalation")
        body = src[start : start + 4000]
        self.assertIn(
            "open_questions=",
            body,
            "the checkpoint hook must pass the parsed open questions to the shared evaluator",
        )


# --------------------------------------------------------------------------------------
# V-08: the `- Finding: <F-id>` typed convention, matched per-finding
# --------------------------------------------------------------------------------------


class FindingNamingConventionTests(_RepoCase):
    def test_blocking_question_naming_a_different_finding_does_not_satisfy(self):
        """OQ-01: escalation is PER-FINDING. Any-blocking-question-will-do would be trivially
        defeatable and would produce false confidence."""
        _plan(self.repo, open_questions=_oq(finding="F-9"))
        _review(self.repo)
        drift = ce.check_review_finding_unescalated(self.repo)
        self.assertEqual(_rules(drift), [RULE])
        self.assertIn("F-1", drift[0].detail)

    def test_blocking_question_with_no_finding_subfield_does_not_satisfy(self):
        _plan(self.repo, open_questions=_oq(finding=None))
        _review(self.repo)
        self.assertEqual(_rules(ce.check_review_finding_unescalated(self.repo)), [RULE])

    def test_non_blocking_question_does_not_satisfy(self):
        _plan(self.repo, open_questions=_oq(blocking="no", status="resolved"))
        _review(self.repo)
        self.assertEqual(_rules(ce.check_review_finding_unescalated(self.repo)), [RULE])

    def test_one_question_may_name_several_findings(self):
        _plan(self.repo, open_questions=_oq(finding="F-1, F-2"))
        _review(
            self.repo,
            rounds=[
                rf.Round(
                    1,
                    (_finding("F-1"), _finding("F-2")),
                    (),
                )
            ],
        )
        self.assertEqual(_rules(ce.check_review_finding_unescalated(self.repo)), [])

    def test_match_is_case_insensitive_on_the_id(self):
        _plan(self.repo, open_questions=_oq(finding="f-1"))
        _review(self.repo)
        self.assertEqual(_rules(ce.check_review_finding_unescalated(self.repo)), [])

    def test_prose_mention_alone_does_not_satisfy(self):
        """The match must be a TYPED field, not a substring search over the rationale, which would be
        spoofable by any incidental mention."""
        oq = (
            "### OQ-01: about the finding\n\n"
            "- Blocking: yes\n- Status: open\n- Owner: maintainer\n"
            "- Resolution or deferral rationale: this concerns F-1 but names no Finding field\n"
        )
        _plan(self.repo, open_questions=oq)
        _review(self.repo)
        self.assertEqual(_rules(ce.check_review_finding_unescalated(self.repo)), [RULE])

    def test_convention_is_declared_in_the_schema(self):
        self.assertIn("Finding", S.OQ_FIELDS)

    def test_finding_subfield_does_not_break_structural_lint(self):
        """The escalation must be legal IPD structure: an extra subfield parses and does not error."""
        plan = _plan(self.repo, open_questions=_oq(finding="F-1"))
        text = plan.read_text(encoding="utf-8")
        parsed = ipd_lint.parse(text)
        self.assertEqual(parsed.open_questions[0].get("Finding"), "F-1")
        self.assertEqual(ipd_lint.check_open_questions(parsed), [])


# --------------------------------------------------------------------------------------
# The END-TO-END chain: the reuse actually closes the loop
# --------------------------------------------------------------------------------------


class EndToEndReuseChainTests(_RepoCase):
    def test_escalation_is_then_caught_by_the_preexisting_pre_execution_gate(self):
        """The whole design rests on this: escalating a gating finding does not merely silence THIS
        rule, it hands the block to the gate that already existed."""
        _review(self.repo)

        # Step 1: unescalated -> THIS rule reports it.
        unescalated = _plan(self.repo)
        before = ipd_lint.lint_file(unescalated, checkpoint="pre-execution")
        codes_before = [d.code for d in before.diagnostics]
        self.assertIn(RULE, codes_before)
        self.assertNotIn(ipd_lint.C_CHECKPOINT, codes_before)

        # Step 2: escalate it into a `Blocking: yes` open question naming the finding.
        unescalated.write_text(
            unescalated.read_text(encoding="utf-8")
            + "\n## Open questions\n\n"
            + _oq(finding="F-1"),
            encoding="utf-8",
        )

        # Step 3: THIS rule is satisfied, and the PRE-EXISTING gate now blocks instead.
        after = ipd_lint.lint_file(unescalated, checkpoint="pre-execution")
        codes_after = [d.code for d in after.diagnostics]
        self.assertNotIn(RULE, codes_after)
        self.assertIn(
            ipd_lint.C_CHECKPOINT,
            codes_after,
            "the escalated question must be caught by the pre-existing pre-execution gate",
        )
        self.assertTrue(
            any(
                "unresolved blocking question at pre-execution" in d.message
                for d in after.diagnostics
            ),
            "the block must come from the pre-existing unresolved-blocking-question gate",
        )
        self.assertEqual(after.disposition, S.DISPOSITION_ERROR)

    def test_the_loop_is_closable_by_resolving_the_question(self):
        """A plan is not permanently stuck: fixing the finding clears both surfaces."""
        _plan(
            self.repo,
            open_questions=_oq(blocking="yes", status="resolved", finding="F-1"),
        )
        _review(self.repo, rounds=[rf.Round(1, (_finding(decision="fixed"),), ())])
        plan = next(
            (self.repo / ".aw" / "records" / "plans" / "pending").glob("*.ipd.md")
        )
        res = ipd_lint.lint_file(plan, checkpoint="pre-execution")
        codes = [d.code for d in res.diagnostics]
        self.assertEqual(_rules(ce.check_review_finding_unescalated(self.repo)), [])
        self.assertNotIn(RULE, codes)
        # BOTH gates in the chain are now silent. Asserting on these two codes specifically, rather
        # than on a `conforming` disposition: this minimal fixture is intentionally a metadata/heading
        # stub, so it still carries unrelated IPD-M101/IPD-H202 structural complaints that have
        # nothing to do with this rule. Asserting `conforming` would make the test pass or fail on the
        # fixture's boilerplate completeness instead of on the behavior under test.
        self.assertNotIn(ipd_lint.C_CHECKPOINT, codes)


# --------------------------------------------------------------------------------------
# No-regression: the rule must add NOTHING to a corpus with no review artifacts
# --------------------------------------------------------------------------------------


class GrandfatheringTests(_RepoCase):
    def test_many_plans_with_no_reviews_produce_no_findings(self):
        """The live-corpus shape (many plans, zero `.review.md`), as an isolated fixture."""
        for i in range(12):
            _plan(self.repo, id6=f"b{i:05d}")
        for lane in ("executed", "superseded"):
            for i in range(5):
                _plan(self.repo, id6=f"c{lane[0]}{i:04d}", lane=lane)
        self.assertEqual(list(rf.iter_review_files(self.repo)), [])
        self.assertEqual(_rules(ce.check_review_finding_unescalated(self.repo)), [])
        self.assertEqual(
            [d.rule for d in ce.check_types(self.repo, ["plans"]) if d.rule == RULE], []
        )


if __name__ == "__main__":
    unittest.main()
