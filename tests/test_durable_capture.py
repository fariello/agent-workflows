"""Tests for durablecapture Order 01 (`rnkqrc`): `check.ipd-uncarried-obligation`.

An outstanding obligation an IPD records (a `## Deferred / out of scope` row, or an `open`/`deferred`
question) must name a DURABLE CARRIER before that plan may claim `executed`, because
`attention_contract._PLANS_MAP` maps `executed` to the `done` class and an uncarried obligation then
disappears from every attention view with no record that anything was dropped.

Covers:
* V-01 - the typed carrier vocabulary is declared in the schema and is behavior-neutral on its own.
* V-02 - the shared predicate's THREE ESCAPES (handoff / satisfied / declined), and its FOUR REFUSALS
  (no carrier, dangling carrier, terminal-directory carrier, prose-only). Plus the malformed case
  producing a FINDING rather than a traceback, and the `CloseVerdict` shape being mirrored.
* V-03 - the rule blocks at the `pre-transition` lint checkpoint, is silent at every other checkpoint,
  and `lint_text` stays PURE (it resolves nothing, so it can never report the rule).
* V-04 - `aw check` and `aw ipd lint --phase pre-transition` agree on identical fixtures, from ONE
  predicate.
* V-05 - staged severity: a PRE-cutover plan yields a non-failing advisory and a POST-cutover plan
  yields a fail-closed error, demonstrated by running the rule.

EVERY fixture is an ISOLATED tmp repo built under `tmp_path`. No assertion reads this repository's
live plans, live backlog, or live `.aw/records/runs/` (which is gitignored with ZERO tracked files, so
a test reading it would pass on a maintainer's machine and fail in CI or in a lane worktree).
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Optional

from agent_workflows import artifact_core as core
from agent_workflows import check_engine as ce
from agent_workflows import ipd_lint
from agent_workflows import ipd_schema as S

RULE = "check.ipd-uncarried-obligation"

# A date strictly BEFORE the cutover (grandfathered) and one strictly AT it (fail-closed). Both are
# derived FROM the constant, so the fixtures cannot drift from the shipped boundary.
_CUT = ce.CARRIER_CUTOVER_DATE
_POST_DATE = "{0}-{1}-{2}".format(_CUT[:4], _CUT[4:6], _CUT[6:])
_PRE_DATE = "2026-09-01"


# --------------------------------------------------------------------------------------
# Isolated fixture builders
# --------------------------------------------------------------------------------------


def _mkrepo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="aw_durablecapture_"))
    for lane in ("pending", "executed", "superseded", "not-executed"):
        (d / ".aw" / "records" / "plans" / lane).mkdir(parents=True)
    for status in ("open", "graduated", "done", "parked", "blocked"):
        (d / ".aw" / "records" / "backlog" / status).mkdir(parents=True)
    (d / ".aw" / "records" / "specs").mkdir(parents=True)
    return d


def _backlog_item(repo: Path, *, id6: str = "car111", status: str = "open") -> Path:
    p = (
        repo
        / ".aw"
        / "records"
        / "backlog"
        / status
        / "20260901-{0}-01-{0}-carrier-fixture.md".format(id6)
    )
    p.write_text(
        "# Carrier fixture {0}\n\n"
        "- Id: {0}\n- Status: {1}\n- Priority: medium\n- Work-Kind: bug\n"
        "- Summary: the durable home for the defect under test\n".format(id6, status),
        encoding="utf-8",
    )
    return p


def _carrier_plan(repo: Path, *, id6: str = "carpln", lane: str = "pending") -> Path:
    """A plan used only as a CARRIER TARGET (never the subject under test)."""
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / lane
        / "20260901-carry-01-{0}-carrier-target.ipd.md".format(id6)
    )
    p.write_text(
        "# IPD: carrier target {0}\n\n"
        "- Date: 2026-09-01\n- Kind: child\n- Scope-Paths: x.py\n"
        "- Item-Dependencies: none\n- Status: {1}\n- Set: carry\n- Order: 1\n"
        "- Id: {0}\n\n## Workflow history\n- 2026-09-01 draft (t): created.\n\n"
        "## Goal\ng\n".format(id6, "executed" if lane == "executed" else "approved"),
        encoding="utf-8",
    )
    return p


def _plan(
    repo: Path,
    *,
    id6: str = "subj01",
    lane: str = "pending",
    date: str = _PRE_DATE,
    status: str = "approved",
    deferred_rows: Optional[str] = None,
    open_questions: str = "",
    performed: bool = True,
) -> Path:
    """The SUBJECT plan. `performed=True` makes its E/V rows satisfy the pre-transition E/V checkpoint,
    so a pre-transition lint isolates THIS rule instead of tripping on unrelated state."""
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / lane
        / "20260901-durable-01-{0}-subject-fixture.ipd.md".format(id6)
    )
    if deferred_rows is None:
        deferred_rows = (
            "- a genuinely out-of-scope note.\n  - Carrier-Declined: not a defect.\n"
        )
    exec_state = "performed" if performed else "pending"
    valid_state = "pass" if performed else "pending"
    body = (
        "# IPD: durable-carrier subject {0}\n\n"
        "- Date: {1}\n- Kind: child\n- Scope-Paths: x.py\n"
        "- Item-Dependencies: none\n- Status: {2}\n- Set: durable\n- Order: 1\n"
        "- Highest E allocated: 01\n- Id: {0}\n\n"
        "## Workflow history\n- {1} draft (t): created.\n\n"
        "## Goal\n\ng\n\n"
        "## Detailed Implementation Checklist (TODO)\n\n"
        "### Task group 1: do the thing\n\n"
        "- [x] E-01 DO THE THING.\n"
        "  - Depends on: none\n"
        "  - Expected outcome: the thing is done\n"
        "  - Execution state: {3}\n\n"
        "## Project conventions discovered (Step 0)\n\n- none\n\n"
        "## Findings\n\n| Id | Severity | Area | What | Evidence |\n|---|---|---|---|---|\n"
        "| F-1 | LOW | x | y | z |\n\n"
        "## Proposed changes (ordered, validatable)\n\n1. do the thing\n\n"
        "## Deferred / out of scope (with reason)\n\n{4}\n"
        "## Scope check\n\n- Over-scope: none\n- Under-scope: none\n\n"
        "## Required tests / validation\n\nthe suite\n\n"
        "## Spec / documentation sync\n\nnone\n\n"
        "## Open questions\n\n{5}\n"
        "## Validation and cross-check (verify before reporting done)\n\n"
        "- [x] V-01 validates E-01\n"
        "  - Required evidence: paste it\n"
        "  - Observed evidence: pasted output here\n"
        "  - Result: {6}\n\n"
        "## Approval and execution gate\n\n- Size assessment: standard\n"
        "- Cohesion rationale: not required\n".format(
            id6,
            date,
            status,
            exec_state,
            deferred_rows,
            open_questions,
            valid_state,
        )
    )
    p.write_text(body, encoding="utf-8")
    return p


def _oq(*, status: str = "open", extra: str = "") -> str:
    lines = [
        "### OQ-01: does the uncarried obligation survive?",
        "",
        "- Blocking: no",
        "- Status: {0}".format(status),
        "- Owner: maintainer",
        "- Resolution or deferral rationale: recorded for the test",
    ]
    if extra:
        lines.append(extra)
    return "\n".join(lines) + "\n"


def _rules(drift) -> list:
    return [d.rule for d in drift if d.rule == RULE]


def _obligation(**fields) -> ce.CarrierObligation:
    return ce.CarrierObligation("deferred", "deferred row 1", 1, dict(fields))


class _RepoCase(unittest.TestCase):
    def setUp(self):
        self.repo = _mkrepo()

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)


# --------------------------------------------------------------------------------------
# V-01: the typed vocabulary, and its behavior-neutrality on its own
# --------------------------------------------------------------------------------------


class SchemaVocabularyTests(unittest.TestCase):
    def test_carrier_fields_are_declared_in_the_oq_vocabulary(self):
        """The `Finding` precedent: a typed field, declared beside it, matched structurally."""
        for field in S.CARRIER_FIELDS:
            self.assertIn(field, S.OQ_FIELDS)

    def test_carrier_field_names_are_the_three_escapes(self):
        self.assertEqual(
            S.CARRIER_FIELDS,
            (S.CARRIER_FIELD, S.CARRIER_EVIDENCE_FIELD, S.CARRIER_DECLINED_FIELD),
        )

    def test_parse_carrier_ids_splits_good_from_bad_without_raising(self):
        good, bad = S.parse_carrier_ids("car111, badtoken, , abc123")
        self.assertEqual(good, ("car111", "abc123"))
        self.assertEqual(bad, ("badtoken",))

    def test_parse_carrier_ids_tolerates_empty_and_none(self):
        self.assertEqual(S.parse_carrier_ids(""), ((), ()))
        self.assertEqual(S.parse_carrier_ids(None), ((), ()))

    def test_carrier_fields_present_is_presence_only(self):
        self.assertFalse(S.carrier_fields_present({}))
        self.assertFalse(S.carrier_fields_present({"Carrier": "   "}))
        self.assertTrue(S.carrier_fields_present({"Carrier": "car111"}))
        # Presence does NOT mean resolvable: a dangling id6 is still "present".
        self.assertTrue(S.carrier_fields_present({"Carrier": "zzzzzz"}))

    def test_deferred_subfield_pattern_matches_only_the_typed_fields(self):
        self.assertIsNotNone(S.DEFERRED_SUBFIELD_RE.match("  - Carrier: car111"))
        self.assertIsNotNone(
            S.DEFERRED_SUBFIELD_RE.match("  - Carrier-Evidence: .aw/records/x.md")
        )
        self.assertIsNotNone(S.DEFERRED_SUBFIELD_RE.match("  - Carrier-Declined: why"))
        # An arbitrary indented bullet is NOT a carrier declaration.
        self.assertIsNone(S.DEFERRED_SUBFIELD_RE.match("  - Reason: tracked somewhere"))
        # A TOP-level bullet is a ROW, not a subfield.
        self.assertIsNone(S.DEFERRED_SUBFIELD_RE.match("- Carrier: car111"))


class SchemaIsBehaviorNeutralTests(_RepoCase):
    """V-01: E-01 alone changes no lint result; E-02 is what gives the vocabulary meaning."""

    def test_adding_the_vocabulary_changes_no_existing_lint_result(self):
        # A plan carrying NO carrier field at all lints exactly as it would have: the pure text lint
        # never consults the vocabulary, because presence is only read by the repo-aware predicate.
        plan = _plan(
            self.repo, deferred_rows="- a bare prose row with no typed field.\n"
        )
        text = plan.read_text(encoding="utf-8")
        for checkpoint in (
            "author",
            "review-finalize",
            "pre-execution",
            "pre-transition",
        ):
            res = ipd_lint.lint_text(text, checkpoint=checkpoint, directory="pending")
            self.assertEqual(
                [d.code for d in res.diagnostics if d.code == RULE],
                [],
                "lint_text must never report the repo-aware rule at {0}".format(
                    checkpoint
                ),
            )


# --------------------------------------------------------------------------------------
# V-02: three escapes, four refusals, the malformed case, and the mirrored verdict shape
# --------------------------------------------------------------------------------------


class ThreeEscapesTests(_RepoCase):
    def test_handoff_to_an_open_backlog_item_is_accepted(self):
        _backlog_item(self.repo, id6="car111", status="open")
        v = ce.evaluate_carrier_obligation(self.repo, _obligation(Carrier="car111"))
        self.assertTrue(v.legitimate)
        self.assertEqual(v.path, "HANDOFF")
        self.assertEqual(v.severity, "ok")

    def test_handoff_to_a_nonterminal_plan_is_accepted(self):
        _carrier_plan(self.repo, id6="carpln", lane="pending")
        v = ce.evaluate_carrier_obligation(self.repo, _obligation(Carrier="carpln"))
        self.assertTrue(v.legitimate)
        self.assertEqual(v.path, "HANDOFF")

    def test_handoff_to_a_graduated_backlog_item_is_accepted(self):
        """`graduated` maps to the ACTIVE attention class, so it is still revisited."""
        _backlog_item(self.repo, id6="car222", status="graduated")
        v = ce.evaluate_carrier_obligation(self.repo, _obligation(Carrier="car222"))
        self.assertTrue(v.legitimate)
        self.assertEqual(v.path, "HANDOFF")

    def test_satisfied_by_resolvable_evidence_is_accepted(self):
        ev = (
            self.repo
            / ".aw"
            / "records"
            / "specs"
            / "20260901-aaaaaa-01-aaaaaa-x.spec.md"
        )
        ev.write_text("# spec\n", encoding="utf-8")
        v = ce.evaluate_carrier_obligation(
            self.repo,
            _obligation(**{"Carrier-Evidence": ".aw/records/specs/" + ev.name}),
        )
        self.assertTrue(v.legitimate)
        self.assertEqual(v.path, "SATISFIED")

    def test_declined_with_a_reason_is_accepted(self):
        v = ce.evaluate_carrier_obligation(
            self.repo,
            _obligation(**{"Carrier-Declined": "this is a scope note, not a defect"}),
        )
        self.assertTrue(v.legitimate)
        self.assertEqual(v.path, "DECLINED")

    def test_declined_with_an_empty_reason_declines_nothing(self):
        v = ce.evaluate_carrier_obligation(
            self.repo, _obligation(**{"Carrier-Declined": "   "})
        )
        self.assertFalse(v.legitimate)


class FourRefusalsTests(_RepoCase):
    def test_no_carrier_at_all_is_refused(self):
        v = ce.evaluate_carrier_obligation(self.repo, _obligation())
        self.assertFalse(v.legitimate)
        self.assertEqual(v.severity, "error")
        self.assertIsNone(v.path)
        self.assertIn("NO durable carrier", v.reason)

    def test_a_dangling_carrier_is_refused(self):
        """Exactly as `check.from-backlog-dangling` fails a `From-Backlog` pointing at nothing."""
        v = ce.evaluate_carrier_obligation(self.repo, _obligation(Carrier="zzzzzz"))
        self.assertFalse(v.legitimate)
        self.assertIn("resolves to no backlog item or plan", v.reason)

    def test_a_carrier_in_executed_is_refused_because_that_is_the_hiding_place(self):
        """THE LOAD-BEARING CASE. An executed plan classes `done` in `aw attention`, so handing an
        obligation to one hides it in the very place this rule exists to close."""
        _carrier_plan(self.repo, id6="carexe", lane="executed")
        v = ce.evaluate_carrier_obligation(self.repo, _obligation(Carrier="carexe"))
        self.assertFalse(v.legitimate)
        self.assertIn("terminal/hidden", v.reason)

    def test_a_done_backlog_item_is_refused(self):
        _backlog_item(self.repo, id6="cardon", status="done")
        v = ce.evaluate_carrier_obligation(self.repo, _obligation(Carrier="cardon"))
        self.assertFalse(v.legitimate)
        self.assertIn("terminal/hidden", v.reason)

    def test_a_parked_backlog_item_is_refused(self):
        """`parked` maps to the PARKED class, which the default board hides."""
        _backlog_item(self.repo, id6="carprk", status="parked")
        v = ce.evaluate_carrier_obligation(self.repo, _obligation(Carrier="carprk"))
        self.assertFalse(v.legitimate)

    def test_unresolvable_evidence_is_refused(self):
        v = ce.evaluate_carrier_obligation(
            self.repo, _obligation(**{"Carrier-Evidence": ".aw/records/nope.md"})
        )
        self.assertFalse(v.legitimate)
        self.assertIn("does not resolve", v.reason)

    def test_a_spec_is_never_a_sufficient_carrier(self):
        """OQ-01, ruled by the maintainer: the carrier set is a backlog item or a plan, NEVER a spec."""
        spec = (
            self.repo
            / ".aw"
            / "records"
            / "specs"
            / "20260901-carspc-01-carspc-x.spec.md"
        )
        spec.write_text(
            "# spec\n\n- Id: carspc\n- Status: approved\n", encoding="utf-8"
        )
        v = ce.evaluate_carrier_obligation(self.repo, _obligation(Carrier="carspc"))
        self.assertFalse(v.legitimate)
        self.assertIn("resolves to no backlog item or plan", v.reason)


class MalformedIsAFindingTests(_RepoCase):
    """A gate that crashes on bad input is a gate that gets disabled."""

    def test_a_malformed_carrier_token_yields_a_finding_not_an_exception(self):
        v = ce.evaluate_carrier_obligation(
            self.repo, _obligation(Carrier="see the backlog")
        )
        self.assertFalse(v.legitimate)
        self.assertIn("malformed", v.reason)
        self.assertEqual(v.severity, "error")

    def test_a_good_token_beside_a_bad_one_still_reports_the_malformed_one(self):
        _backlog_item(self.repo, id6="car111", status="open")
        v = ce.evaluate_carrier_obligation(
            self.repo, _obligation(Carrier="car111, NOT-AN-ID6")
        )
        self.assertFalse(v.legitimate)
        self.assertIn("NOT-AN-ID6", v.reason)

    def test_an_unparseable_plan_yields_no_traceback(self):
        p = self.repo / ".aw" / "records" / "plans" / "pending" / "junk.ipd.md"
        p.write_text("\x00 not markdown at all \x00", encoding="utf-8")
        drift = ce.evaluate_durable_carrier(
            self.repo, plan_path=p, plan_text=p.read_text(encoding="utf-8")
        )
        self.assertEqual(_rules(drift), [])

    def test_the_predicate_never_raises_on_an_absent_repo(self):
        v = ce.evaluate_carrier_obligation(
            Path("/nonexistent/repo/root"), _obligation(Carrier="car111")
        )
        self.assertFalse(v.legitimate)


class VerdictShapeIsMirroredTests(_RepoCase):
    """E-02: mirror `CloseVerdict`, do not invent a fourth verdict type."""

    def test_the_verdict_is_a_CloseVerdict(self):
        v = ce.evaluate_carrier_obligation(self.repo, _obligation())
        self.assertIsInstance(v, ce.CloseVerdict)
        self.assertEqual(
            v._fields, ("legitimate", "severity", "reason", "fixes", "path")
        )

    def test_a_refusal_carries_the_three_actionable_fixes(self):
        v = ce.evaluate_carrier_obligation(self.repo, _obligation())
        self.assertEqual(len(v.fixes), 3)
        joined = " ".join(v.fixes)
        for field in S.CARRIER_FIELDS:
            self.assertIn(field, joined)

    def test_the_paths_are_the_proven_escape_names(self):
        _backlog_item(self.repo, id6="car111", status="open")
        self.assertEqual(
            ce.evaluate_carrier_obligation(
                self.repo, _obligation(Carrier="car111")
            ).path,
            "HANDOFF",
        )
        self.assertEqual(
            ce.evaluate_carrier_obligation(
                self.repo, _obligation(**{"Carrier-Declined": "x"})
            ).path,
            "DECLINED",
        )


class QuestionObligationsTests(_RepoCase):
    """An `open`/`deferred` question owes a carrier; a `resolved` one owes nothing."""

    def test_an_open_question_with_no_carrier_is_reported(self):
        plan = _plan(self.repo, date=_POST_DATE, open_questions=_oq(status="open"))
        drift = ce.evaluate_durable_carrier(
            self.repo, plan_path=plan, plan_text=plan.read_text(encoding="utf-8")
        )
        self.assertEqual(_rules(drift), [RULE])
        self.assertIn("OQ-01", drift[0].detail)

    def test_a_resolved_question_owes_nothing(self):
        plan = _plan(self.repo, date=_POST_DATE, open_questions=_oq(status="resolved"))
        drift = ce.evaluate_durable_carrier(
            self.repo, plan_path=plan, plan_text=plan.read_text(encoding="utf-8")
        )
        self.assertEqual(_rules(drift), [])

    def test_an_open_question_naming_a_carrier_is_accepted(self):
        _backlog_item(self.repo, id6="car111", status="open")
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            open_questions=_oq(status="open", extra="- Carrier: car111"),
        )
        drift = ce.evaluate_durable_carrier(
            self.repo, plan_path=plan, plan_text=plan.read_text(encoding="utf-8")
        )
        self.assertEqual(_rules(drift), [])

    def test_a_deferred_question_owes_a_carrier(self):
        plan = _plan(self.repo, date=_POST_DATE, open_questions=_oq(status="deferred"))
        drift = ce.evaluate_durable_carrier(
            self.repo, plan_path=plan, plan_text=plan.read_text(encoding="utf-8")
        )
        self.assertEqual(_rules(drift), [RULE])


class ProseDoesNotSatisfyTests(_RepoCase):
    """THE SPOOFABILITY CASE, and the one the corpus proves is normal: 2225 deferred rows exist today
    and every one is prose, several literally saying "tracked as `<id6>`"."""

    def test_a_prose_row_claiming_backlog_tracking_is_still_refused(self):
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows="- THE WALKTHROUGH GAP: tracked in the backlog as `car111`.\n",
        )
        _backlog_item(self.repo, id6="car111", status="open")
        drift = ce.evaluate_durable_carrier(
            self.repo, plan_path=plan, plan_text=plan.read_text(encoding="utf-8")
        )
        self.assertEqual(
            _rules(drift),
            [RULE],
            "prose naming a REAL id6 must NOT satisfy the rule; only a typed field may",
        )

    def test_the_same_row_with_a_typed_field_is_accepted(self):
        _backlog_item(self.repo, id6="car111", status="open")
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows=(
                "- THE WALKTHROUGH GAP: tracked in the backlog.\n  - Carrier: car111\n"
            ),
        )
        drift = ce.evaluate_durable_carrier(
            self.repo, plan_path=plan, plan_text=plan.read_text(encoding="utf-8")
        )
        self.assertEqual(_rules(drift), [])

    def test_a_carrier_inside_a_code_fence_does_not_count(self):
        """The section walk is fence-aware, so a documented EXAMPLE cannot satisfy the gate."""
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows=(
                "- THE GAP: see the example below.\n\n"
                "```\n  - Carrier: car111\n```\n"
            ),
        )
        _backlog_item(self.repo, id6="car111", status="open")
        drift = ce.evaluate_durable_carrier(
            self.repo, plan_path=plan, plan_text=plan.read_text(encoding="utf-8")
        )
        self.assertEqual(_rules(drift), [RULE])


# --------------------------------------------------------------------------------------
# V-03: the lint checkpoint, its placement, and the purity corollary
# --------------------------------------------------------------------------------------


class LintCheckpointTests(_RepoCase):
    def test_pre_transition_reports_the_rule_from_lint_file(self):
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
        )
        res = ipd_lint.lint_file(plan, checkpoint="pre-transition")
        self.assertIn(RULE, [d.code for d in res.diagnostics])
        self.assertEqual(res.disposition, S.DISPOSITION_ERROR)
        self.assertFalse(res.passing)

    def test_pre_transition_conforms_once_a_carrier_is_named(self):
        _backlog_item(self.repo, id6="car111", status="open")
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows="- AN UNCARRIED DEFECT: handed off.\n  - Carrier: car111\n",
        )
        res = ipd_lint.lint_file(plan, checkpoint="pre-transition")
        self.assertEqual(
            [d.code for d in res.diagnostics if d.code == RULE],
            [],
            "diagnostics: {0}".format([d.render(str(plan)) for d in res.diagnostics]),
        )

    def test_the_rule_is_silent_at_every_other_checkpoint(self):
        """Firing earlier would demand a carrier for a row a plan is still drafting."""
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            status="to-review",
            deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
            performed=False,
        )
        for checkpoint in ("author", "review-finalize"):
            res = ipd_lint.lint_file(plan, checkpoint=checkpoint)
            self.assertEqual(
                [d.code for d in res.diagnostics if d.code == RULE],
                [],
                "the rule must not fire at {0}".format(checkpoint),
            )

    def test_lint_text_can_never_report_the_rule(self):
        """F-10's corollary: `lint_text` is PURE ("Pure: no I/O"), and resolving a carrier is I/O. A
        test that got this rule out of `lint_text` would prove it was wired into the pure path."""
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
        )
        text = plan.read_text(encoding="utf-8")
        res = ipd_lint.lint_text(text, checkpoint="pre-transition", directory="pending")
        self.assertEqual([d.code for d in res.diagnostics if d.code == RULE], [])
        self.assertEqual([d.code for d in res.advisories if d.code == RULE], [])

    def test_the_merge_is_wired_into_lint_file_and_not_check_checkpoint(self):
        """PROVE THE PLACEMENT by symbol, so a later refactor into the pure path fails here."""
        import inspect

        self.assertIn("_merge_durable_carrier", inspect.getsource(ipd_lint.lint_file))
        self.assertNotIn(
            "_merge_durable_carrier", inspect.getsource(ipd_lint.check_checkpoint)
        )
        self.assertNotIn(
            "_merge_durable_carrier", inspect.getsource(ipd_lint.lint_text)
        )

    def test_the_carrier_checkpoint_set_diverges_from_the_review_escalation_set(self):
        """The asymmetry is deliberate: one set EXCLUDES `pre-transition` (blocking there would strand
        a completed plan); this one REQUIRES it (that is when the obligation vanishes)."""
        self.assertIn("pre-transition", ipd_lint._CARRIER_CHECKPOINTS)
        self.assertNotIn("pre-transition", ipd_lint._REVIEW_ESCALATION_CHECKPOINTS)

    def test_a_terminal_dir_plan_keeps_its_grandfathered_disposition(self):
        plan = _plan(
            self.repo,
            lane="executed",
            date=_POST_DATE,
            status="executed",
            deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
        )
        res = ipd_lint.lint_file(plan, checkpoint="pre-transition")
        self.assertEqual(res.disposition, S.DISPOSITION_LEGACY)
        self.assertEqual([d.code for d in res.diagnostics if d.code == RULE], [])


class PreExecutionGateIsUntouchedTests(_RepoCase):
    """E-03: do NOT move or widen the existing `pre-execution` blocking-OQ check."""

    def test_the_blocking_oq_check_still_fires_at_pre_execution(self):
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            open_questions=(
                "### OQ-01: unanswered?\n\n- Blocking: yes\n- Status: open\n"
                "- Owner: maintainer\n- Resolution or deferral rationale: pending\n"
            ),
        )
        res = ipd_lint.lint_file(plan, checkpoint="pre-execution")
        codes = [d.code for d in res.diagnostics]
        self.assertIn(ipd_lint.C_CHECKPOINT, codes)
        self.assertIn(
            "unresolved blocking question at pre-execution",
            " ".join(d.message for d in res.diagnostics),
        )

    def test_the_carrier_rule_does_not_fire_at_pre_execution(self):
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
        )
        res = ipd_lint.lint_file(plan, checkpoint="pre-execution")
        self.assertEqual([d.code for d in res.diagnostics if d.code == RULE], [])


# --------------------------------------------------------------------------------------
# V-04: ONE predicate, TWO surfaces
# --------------------------------------------------------------------------------------


class CrossSurfaceAgreementTests(_RepoCase):
    def _both(self, plan: Path):
        sweep = [
            d for d in ce.check_durable_carrier(self.repo) if d.location == str(plan)
        ]
        lint = [
            d
            for d in ipd_lint.lint_file(plan, checkpoint="pre-transition").diagnostics
            if d.code == RULE
        ]
        return sweep, lint

    def test_both_surfaces_fire_on_the_same_failing_fixture(self):
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
        )
        sweep, lint = self._both(plan)
        self.assertEqual(len(sweep), 1)
        self.assertEqual(len(lint), 1)
        self.assertEqual(sweep[0].detail, lint[0].message)

    def test_both_surfaces_are_silent_on_the_same_passing_fixture(self):
        _backlog_item(self.repo, id6="car111", status="open")
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows="- HANDED OFF.\n  - Carrier: car111\n",
        )
        sweep, lint = self._both(plan)
        self.assertEqual(sweep, [])
        self.assertEqual(lint, [])

    def test_one_predicate_backs_both_surfaces(self):
        """Assert by SYMBOL, since a second implementation that agrees today will disagree later."""
        import inspect

        self.assertIn(
            "evaluate_durable_carrier", inspect.getsource(ce.check_durable_carrier)
        )
        self.assertIn(
            "evaluate_durable_carrier",
            inspect.getsource(ipd_lint._merge_durable_carrier),
        )

    def test_the_rule_is_reached_by_the_plans_type_path(self):
        _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
        )
        self.assertIn(RULE, [d.rule for d in ce.check_types(self.repo, ["plans"])])

    def test_the_rule_is_reported_exactly_once_by_the_full_sweep(self):
        _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
        )
        hits = [d for d in ce.check_types(self.repo, ["all"]) if d.rule == RULE]
        self.assertEqual(len(hits), 1, "the rule must not be double-reported")

    def test_a_terminal_lane_plan_is_grandfathered_by_the_sweep(self):
        """527 executed plans must never be retroactively litigated."""
        for lane in ("executed", "superseded", "not-executed"):
            with self.subTest(lane=lane):
                repo = _mkrepo()
                try:
                    _plan(
                        repo,
                        lane=lane,
                        date=_POST_DATE,
                        status="executed",
                        deferred_rows="- AN UNCARRIED DEFECT.\n",
                    )
                    self.assertEqual(_rules(ce.check_durable_carrier(repo)), [])
                finally:
                    shutil.rmtree(repo, ignore_errors=True)


class RuleRegistrationTests(unittest.TestCase):
    def test_the_rule_id_resolves_to_a_registered_spec_not_the_default(self):
        self.assertIn(RULE, ce.RULE_REGISTRY)
        spec = ce.rule_spec(RULE)
        self.assertEqual(spec.severity, "error")
        self.assertEqual(spec.assurance, ce.ASSURANCE_REPOSITORY)
        self.assertEqual(spec.determinism, ce.DET_DETERMINISTIC)
        self.assertEqual(spec.invariant, "I-07")


# --------------------------------------------------------------------------------------
# V-05: staged severity, demonstrated rather than asserted
# --------------------------------------------------------------------------------------


class StagedSeverityTests(_RepoCase):
    def test_a_pre_cutover_plan_warns_without_failing_the_gate(self):
        plan = _plan(
            self.repo,
            date=_PRE_DATE,
            deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
        )
        drift = ce.evaluate_durable_carrier(
            self.repo, plan_path=plan, plan_text=plan.read_text(encoding="utf-8")
        )
        self.assertEqual(_rules(drift), [RULE], "an old plan is still REPORTED")
        self.assertEqual(drift[0].severity, ce._CARRIER_LEGACY_SEVERITY)
        self.assertEqual(
            core.drift_exit_code(drift),
            0,
            "the grandfathered tier must NOT fail the gate (`drift_exit_code` exempts only `info`)",
        )

    def test_a_post_cutover_plan_errors_and_fails_the_gate(self):
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
        )
        drift = ce.evaluate_durable_carrier(
            self.repo, plan_path=plan, plan_text=plan.read_text(encoding="utf-8")
        )
        self.assertEqual(_rules(drift), [RULE])
        self.assertEqual(drift[0].severity, "error")
        self.assertEqual(core.drift_exit_code(drift), 1)

    def test_the_cutover_is_strictly_after_every_plan_that_exists_today(self):
        """The `SPEC_ID6_CUTOVER_DATE` precedent's rule: grandfather the whole existing corpus."""
        self.assertGreater(ce.CARRIER_CUTOVER_DATE, "20260917")

    def test_a_pre_cutover_plan_lints_conforming_at_pre_transition(self):
        """The rollout guarantee: the 106 pending plans that predate this rule are NOT blocked."""
        plan = _plan(
            self.repo,
            date=_PRE_DATE,
            deferred_rows="- AN UNCARRIED DEFECT: nothing tracks this.\n",
        )
        res = ipd_lint.lint_file(plan, checkpoint="pre-transition")
        self.assertEqual(
            [d.code for d in res.diagnostics if d.code == RULE],
            [],
            "a grandfathered plan must not be BLOCKED: {0}".format(
                [d.render(str(plan)) for d in res.diagnostics]
            ),
        )
        self.assertIn(
            RULE,
            [d.code for d in res.advisories],
            "but it must still be VISIBLE as an advisory",
        )

    def test_a_plan_with_no_date_is_grandfathered_not_punished(self):
        """The metadata linter owns the missing-Date complaint; this rule must not invent a second one."""
        self.assertEqual(
            ce.carrier_severity_for_plan("# IPD: no date\n\n- Id: aaa111\n"),
            ce._CARRIER_LEGACY_SEVERITY,
        )

    def test_the_severity_boundary_reads_the_plans_own_date(self):
        self.assertEqual(
            ce.carrier_severity_for_plan("- Date: {0}\n".format(_POST_DATE)), "error"
        )
        self.assertEqual(
            ce.carrier_severity_for_plan("- Date: {0}\n".format(_PRE_DATE)),
            ce._CARRIER_LEGACY_SEVERITY,
        )


class AggregationTests(_RepoCase):
    """DECISION 07-rnkqrc-D4: one finding per PLAN, naming the rows and the total count."""

    def test_many_failing_rows_yield_one_finding_naming_the_count(self):
        rows = "".join(
            "- UNCARRIED DEFECT {0}: nothing tracks this.\n".format(i)
            for i in range(1, 8)
        )
        plan = _plan(self.repo, date=_POST_DATE, deferred_rows=rows)
        drift = ce.evaluate_durable_carrier(
            self.repo, plan_path=plan, plan_text=plan.read_text(encoding="utf-8")
        )
        self.assertEqual(len(drift), 1)
        self.assertIn("7 obligation(s)", drift[0].detail)
        self.assertIn("and 2 more", drift[0].detail)

    def test_the_finding_carries_observed_required_and_recovery(self):
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows="- AN UNCARRIED DEFECT.\n",
        )
        d = ce.evaluate_durable_carrier(
            self.repo, plan_path=plan, plan_text=plan.read_text(encoding="utf-8")
        )[0]
        self.assertIn("Carrier", d.observed)
        self.assertIn("NON-TERMINAL plan", d.required)
        self.assertIn("aw backlog new", d.recovery)

    def test_a_plan_with_no_obligations_produces_nothing(self):
        plan = _plan(self.repo, date=_POST_DATE, deferred_rows="")
        drift = ce.evaluate_durable_carrier(
            self.repo, plan_path=plan, plan_text=plan.read_text(encoding="utf-8")
        )
        self.assertEqual(drift, [])


class SectionWalkTests(_RepoCase):
    def test_only_the_deferred_section_is_read(self):
        """A bullet in another section is not an obligation."""
        plan = _plan(self.repo, date=_POST_DATE, deferred_rows="")
        text = plan.read_text(encoding="utf-8")
        obligations = ce._deferred_section_obligations(text)
        self.assertEqual(obligations, [])

    def test_rows_are_numbered_in_source_order_with_their_subfields(self):
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows=(
                "- FIRST: uncarried.\n"
                "- SECOND: carried.\n  - Carrier: car111\n"
                "- THIRD: declined.\n  - Carrier-Declined: not a defect\n"
            ),
        )
        obs = ce._deferred_section_obligations(plan.read_text(encoding="utf-8"))
        self.assertEqual(
            [o.locator for o in obs],
            ["deferred row 1", "deferred row 2", "deferred row 3"],
        )
        self.assertEqual(obs[0].fields, {})
        self.assertEqual(obs[1].fields, {"Carrier": "car111"})
        self.assertEqual(obs[2].fields, {"Carrier-Declined": "not a defect"})

    def test_a_continuation_line_is_not_a_new_row(self):
        plan = _plan(
            self.repo,
            date=_POST_DATE,
            deferred_rows=(
                "- ONE ROW: with a long reason\n"
                "  that continues on the next line and says more.\n"
                "  - Carrier: car111\n"
            ),
        )
        obs = ce._deferred_section_obligations(plan.read_text(encoding="utf-8"))
        self.assertEqual(len(obs), 1)
        self.assertEqual(obs[0].fields, {"Carrier": "car111"})


if __name__ == "__main__":
    unittest.main()
