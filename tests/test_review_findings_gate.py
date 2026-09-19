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

WHY TABLES: almost every test here was the SAME shape - build an isolated repo, vary ONE knob (a
severity, a threshold, a decision, one open-question spelling, one lane, one artifact shape), call the
evaluator, assert one rule id appeared or did not. Those are data rows, and the realistic regression
is in the SHARED evaluator every row funnels through, so a broken threshold comparison or a lost
escalation match moves MANY rows at once and is only diagnosable as one cause when the rows are
reported together. What used to be a CLASS per concern (thresholds, current rounds, failure modes,
naming convention) is now a COLUMN, because the property worth asserting is that ONE evaluator gives
different answers as each knob moves, which no single-knob test can state.

THE EXHAUSTIVE `is_gating` TRUTH TABLE IS NOT DUPLICATED HERE. `tests/test_review_findings.py` owns a
21-cell severity x threshold grid over the PURE predicate `rf.is_gating`. Re-tabulating those cells
here would be a second copy that could disagree with the first. This file instead asserts what that
grid CANNOT see: that a threshold written into a repo's `project.json` is RESOLVED from config and
actually reaches this rule end to end. So the severity/threshold rows below are chosen for END-TO-END
plumbing coverage, not truth-table completeness: for EVERY active threshold there is an AT-threshold
row (which must gate, since the comparison is `>=`, not `>`) and a just-below row, plus the `off`
opt-out and the absent-key default. If a row here fails but the `is_gating` grid passes, the defect is
in config resolution or in this rule's wiring, NOT in the predicate.

Tests that are NOT rows carry a one-line docstring saying why they stay separate. The recurring
reasons: the subject is the real repository rather than a fixture; the setup is materially different
(a bulk corpus, a multi-step mutation of one file); or the assertion is a single structural claim
about a registry object rather than a gate outcome.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import NamedTuple

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
        subject_id=id6,
        subject_type="ipd",
        reviewed_at="2026-08-29",
        reviewer="test",
        verdict="REVIEWED - OPEN QUESTIONS",
        rounds=rounds,
    )


def _review_path(repo: Path, id6: str = "aaa111") -> Path:
    return (
        repo / ".aw" / "records" / "reviews" / f"20260829-demo-01-{id6}-gate.review.md"
    )


def _rules(drift) -> list:
    return [d.rule for d in drift if d.rule == RULE]


class _RepoCase(unittest.TestCase):
    def setUp(self):
        self.repo = _mkrepo()

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)


# --------------------------------------------------------------------------------------
# The gate outcome table: one evaluator, every knob that changes its answer.
# --------------------------------------------------------------------------------------


class _Case(NamedTuple):
    """One row of the gate-outcome table.

    `case` and `why` are REQUIRED and positional; every knob below them carries the default that
    describes the canonical gating fixture (one round, one `high`/`open` finding named `F-1`, a
    pending-lane plan with no open questions, and NO `project.json`, so the gate resolves its
    documented `high` default). A row therefore names ONLY what it varies, which is what keeps a
    10-column table readable and makes the varied knob the visible subject of the row.
    """

    #: Short label naming the input, used verbatim in the failure report.
    case: str
    #: The RULE this row encodes, not a restatement of the data.
    why: str
    #: Per-round findings: a tuple of rounds, each a tuple of (id, severity, decision).
    rounds: tuple[tuple[tuple[str, str, str], ...], ...] = ((("F-1", "high", "open"),),)
    #: `review_findings_gate.block_at`; None writes NO project.json (default resolution).
    threshold: str | None = None
    #: The plan's `## Open questions` block ("" = the plan has none).
    oq: str = ""
    #: Which plans lane the plan file lives in.
    lane: str = "pending"
    #: "writer" | "malformed" | "absent" | "retired-field" - the review artifact's shape.
    artifact: str = "writer"
    #: Must the rule fire?
    expect: bool = True
    #: Which path a firing drift must name: "plan" (the plan to escalate in) or "review" (to repair).
    loc: str = "plan"
    #: Substrings the drift's `detail` must contain.
    detail_needles: tuple[str, ...] = ()
    #: Substrings the drift's `required` field must contain.
    required_needles: tuple[str, ...] = ()
    #: Substrings the drift's `recovery` field must contain.
    recovery_needles: tuple[str, ...] = ()


#: A review artifact that EXISTS but carries no rounds at all: the writer cannot produce this shape,
#: so it is hand-written. Used by the "present but malformed" rows.
_MALFORMED_BODY = (
    "# review\n\n- Subject-Id: aaa111\n- Subject-Type: ipd\n- Reviewed-At: 2026-08-29\n"
    "- Reviewer: test\n- Verdict: v\n\nthis file has no rounds at all\n"
)


def _build(case: _Case) -> tuple[Path, Path, Path | None]:
    """Materialize one row's isolated repo. Returns (repo, plan path, review path or None)."""
    repo = _mkrepo()
    plan = _plan(repo, lane=case.lane, open_questions=case.oq)
    review: Path | None = None
    if case.artifact in ("writer", "retired-field"):
        rounds = [
            rf.Round(n, tuple(_finding(*f) for f in findings), ())
            for n, findings in enumerate(case.rounds, 1)
        ]
        review = _review(repo, rounds=rounds)
        if case.artifact == "retired-field":
            review.write_text(
                review.read_text(encoding="utf-8").replace(
                    "- Subject-Id: aaa111", "- Plan-Id: aaa111"
                ),
                encoding="utf-8",
            )
    elif case.artifact == "malformed":
        review = _review_path(repo)
        review.write_text(_MALFORMED_BODY, encoding="utf-8")
    elif case.artifact != "absent":  # pragma: no cover - guards a table typo
        raise AssertionError(f"unknown artifact shape {case.artifact!r}")
    _set_threshold(repo, case.threshold)
    return repo, plan, review


class GateOutcomeTests(unittest.TestCase):
    """`check_review_finding_unescalated`: every input that changes whether the gate FIRES.

    Twenty-one tests across five classes became this one table. They were one shape with one knob
    turned: `RuleFiresTests` varied the decision and the lane, `ThresholdTests` varied the configured
    threshold, `CurrentRoundTests` varied the ROUND a decision lands in, `FailureModeTests` varied the
    artifact's shape, and `FindingNamingConventionTests` varied the open question's spelling. Each
    asserted one rule id present or absent.

    WHY THE TABLE BEATS THE TWENTY-ONE, specifically for a GATE: all five knobs are read by ONE
    evaluator (`check_engine.evaluate_review_finding_escalation`), so the realistic regression is in
    that shared body - a flipped comparison, a lost `off` short-circuit, a broken `- Finding:` match,
    a dropped current-round filter. Any of those moves a WHOLE FAMILY of rows at once. Twenty-one
    tests report that as up to twenty-one red lines that each say `[] != ['check...']`; the table
    reports one failure naming every moved row, and the SHAPE of the moved set is what identifies the
    cause (see the FIX hints in the failure message).

    THE POSITIVE AND NEGATIVE ROWS SHARE THE TABLE DELIBERATELY, because for a gate they are each
    other's control. An evaluator that returned a drift for EVERY input satisfies every
    must-fire row on its own, and one that returned nothing satisfies every must-not-fire row; only
    the two together are evidence. The failure message therefore counts the two kinds separately and
    says plainly when the must-fire rows are broken, since at that moment every must-not-fire row is
    VACUOUS.

    SILENCE IS THE DANGEROUS FAILURE, so rows do not stop at a boolean. A firing row also asserts
    WHICH PATH the drift names (the plan to escalate in, or, for a malformed artifact, the review file
    to repair) and that `detail`/`required`/`recovery` name the finding id, because a gate that fires
    with an unactionable message is a gate an operator cannot clear.
    """

    CASES: tuple[_Case, ...] = (
        # -- The canonical case, and the message contract it must carry. ------------------
        _Case(
            "an unescalated high/open finding",
            "THE BASE CASE the whole rule exists for: an unfixed finding at the default "
            "threshold with no blocking question naming it must be REPORTED, against the PLAN, "
            "naming the finding and its severity, with a recovery an operator can act on",
            detail_needles=("F-1", "high"),
            required_needles=("Blocking: yes", "F-1"),
            recovery_needles=("Finding: F-1",),
        ),
        _Case(
            "an escalated high/open finding",
            "the ESCALATION ACTUALLY SATISFIES the gate. Without this row the rule could be a "
            "constant `fire` and every must-fire row above would still pass",
            oq=_oq(finding="F-1"),
            expect=False,
            loc="",
        ),
        # -- The decision axis: what counts as UNFIXED. -----------------------------------
        _Case(
            "a finding marked fixed",
            "`fixed` is the ONLY decision the reviewer can use to close a finding, so it is the "
            "only one that may silence the gate",
            rounds=((("F-1", "high", "fixed"),),),
            expect=False,
            loc="",
        ),
        _Case(
            "a finding marked deferred",
            "`deferred` is a deliberate decision NOT to fix, so it must gate exactly like `open`; "
            "treating a deferral as a resolution would let any finding be waved through",
            rounds=((("F-1", "high", "deferred"),),),
            detail_needles=("deferred",),
        ),
        _Case(
            "a finding marked replan",
            "MEASURED, and deliberate: `replan` is in `rf.DECISIONS` but is EXCLUDED from "
            "check_engine._UNFIXED_DECISIONS, because a replanned plan is not heading for "
            "execution in its current form. This row pins that documented carve-out, so nobody "
            "'fixes' it by widening the set without deciding to",
            rounds=((("F-1", "high", "replan"),),),
            expect=False,
            loc="",
        ),
        # -- Current-round semantics: WHICH round a decision lands in. --------------------
        _Case(
            "round 1 open, then round 2 fixed",
            "current-round semantics (15zvu6 E-03): a finding superseded by a later round is NOT "
            "live, so the gate must read the CURRENT round only",
            rounds=((("F-1", "high", "open"),), (("F-1", "high", "fixed"),)),
            expect=False,
            loc="",
        ),
        _Case(
            "round 1 fixed, then round 2 open",
            "the CONVERSE, and the row that stops 'read the current round' from degrading into "
            "'any round said fixed': a finding REOPENED by the current round is live again",
            rounds=((("F-1", "high", "fixed"),), (("F-1", "high", "open"),)),
            detail_needles=("F-1",),
        ),
        # -- The threshold axis. Chosen for END-TO-END coverage, not truth-table -----------
        # -- completeness: the exhaustive is_gating grid lives in test_review_findings.py. -
        _Case(
            "medium finding at threshold medium",
            "BOUNDARY for `medium`: AT the threshold MUST gate, because the comparison is >=, not "
            "> . This is the row a 'strictly greater' refactor breaks",
            rounds=((("F-1", "medium", "open"),),),
            threshold="medium",
        ),
        _Case(
            "low finding at threshold medium",
            "just BELOW `medium`: the row that proves the boundary above is a real comparison and "
            "not a constant `fire`",
            rounds=((("F-1", "low", "open"),),),
            threshold="medium",
            expect=False,
            loc="",
        ),
        _Case(
            "high finding at threshold high",
            "BOUNDARY for `high`, and the single most load-bearing cell of the whole gate, since "
            "`high` is what an unconfigured repo resolves to",
            threshold="high",
        ),
        _Case(
            "medium finding at threshold high",
            "just BELOW `high`: a configured stricter threshold must actually let a medium pass",
            rounds=((("F-1", "medium", "open"),),),
            threshold="high",
            expect=False,
            loc="",
        ),
        _Case(
            "blocker finding at threshold blocker",
            "BOUNDARY for `blocker`, the strictest threshold: AT it must still gate",
            rounds=((("F-1", "blocker", "open"),),),
            threshold="blocker",
        ),
        _Case(
            "high finding at threshold blocker",
            "just BELOW `blocker`: the threshold deliberately lets a HIGH pass, which is the whole "
            "reason a repo would configure it",
            threshold="blocker",
            expect=False,
            loc="",
        ),
        _Case(
            "blocker finding at threshold medium",
            "ABOVE the threshold: severities above the bar gate too, so the comparison is an "
            "ordering and not an equality test",
            rounds=((("F-1", "blocker", "open"),),),
            threshold="medium",
        ),
        _Case(
            "high finding with NO project.json",
            "the ABSENT-KEY DEFAULT is fail-CLOSED at `high`: an unconfigured repo still gates. A "
            "default that resolved to `off` would silently disable the gate for every repo that "
            "never set the key",
            threshold=None,
        ),
        _Case(
            "medium finding with NO project.json",
            "and the default is `high` SPECIFICALLY, not `medium`: this row is what pins WHICH "
            "default, since the row above passes for any default at or below high",
            rounds=((("F-1", "medium", "open"),),),
            threshold=None,
            expect=False,
            loc="",
        ),
        _Case(
            "a blocker finding at threshold off",
            "`off` DISABLES EVEN A BLOCKER, which is the entire meaning of the documented opt-out "
            "and the row an over-eager 'blockers always gate' fix would break",
            rounds=((("F-1", "blocker", "open"),),),
            threshold="off",
            expect=False,
            loc="",
        ),
        # -- The artifact axis: the three E-07 failure modes. -----------------------------
        _Case(
            "no review artifact at all",
            "(a) ABSENT is SILENT, and this is a safety requirement rather than laziness: zero "
            "`.review.md` files exist against 400+ plans, so a fail-closed absent case would "
            "mass-fail the entire corpus on day one",
            artifact="absent",
            expect=False,
            loc="",
        ),
        _Case(
            "a review artifact with no rounds",
            "(b) PRESENT BUT MALFORMED FAILS CLOSED, reported against the REVIEW file, because a "
            "file that exists but cannot be trusted is an error and not an absence. Treating it as "
            "an absence is the evasion path F-8 identified",
            artifact="malformed",
            loc="review",
            detail_needles=("malformed",),
        ),
        _Case(
            "a finding whose severity is a typo",
            "the same fail-closed branch reached via an UNRECOGNIZED SEVERITY: a `HGIH` typo has no "
            "position in the ordering, so it would slip past `is_gating` silently. The parser "
            "diagnostic is what gates instead",
            rounds=((("F-1", "hgih", "open"),),),
            loc="review",
            detail_needles=("malformed",),
        ),
        _Case(
            "a review artifact carrying the RETIRED subject field",
            "revsweep `eyh1fu`: a record spelling its subject `- Plan-Id:` is NOT indexed (no "
            "dual-field reader exists, by design) and the consequence is SILENCE. Pinned as the "
            "CONTRAST to the rows above, because this failure mode looks exactly like compliance; "
            "the corpus-level guard that keeps it hypothetical is "
            "`test_no_review_record_in_the_tree_carries_the_retired_field`",
            artifact="retired-field",
            expect=False,
            loc="",
        ),
        # -- The lane axis: grandfathering. -----------------------------------------------
        _Case(
            "a plan in executed/",
            "the 400+ TERMINAL plans must never be retroactively litigated: their reviews predate "
            "this rule, so the sweep is scoped to the pending lane",
            lane="executed",
            expect=False,
            loc="",
        ),
        _Case(
            "a plan in superseded/",
            "same grandfathering, second terminal lane: the scope is 'not pending', not "
            "'not executed'",
            lane="superseded",
            expect=False,
            loc="",
        ),
        _Case(
            "a plan in not-executed/",
            "same grandfathering, third terminal lane, so a lane added to the terminal set without "
            "being added to the scope check is visible here",
            lane="not-executed",
            expect=False,
            loc="",
        ),
        # -- The escalation axis: the `- Finding:` convention, matched PER FINDING. --------
        _Case(
            "a blocking question naming a DIFFERENT finding",
            "escalation is PER-FINDING (OQ-01). An any-blocking-question-will-do match would be "
            "trivially defeatable and would produce false confidence",
            oq=_oq(finding="F-9"),
            detail_needles=("F-1",),
        ),
        _Case(
            "a blocking question with NO Finding subfield",
            "the subfield is what BINDS a question to a finding; without it the question makes no "
            "claim about F-1 at all",
            oq=_oq(finding=None),
        ),
        _Case(
            "a NON-blocking question naming the finding",
            "`Blocking: yes` is the load-bearing half: a non-blocking question does not stop "
            "execution, so it cannot discharge a gating finding",
            oq=_oq(blocking="no", status="resolved"),
        ),
        _Case(
            "a question whose PROSE mentions the finding",
            "the match must be a TYPED FIELD, not a substring search over the rationale, which any "
            "incidental mention of `F-1` would spoof",
            oq=(
                "### OQ-01: about the finding\n\n"
                "- Blocking: yes\n- Status: open\n- Owner: maintainer\n"
                "- Resolution or deferral rationale: this concerns F-1 but names no Finding field\n"
            ),
        ),
        _Case(
            "one question naming SEVERAL findings",
            "a single question may discharge more than one finding, so the field is a LIST and not "
            "a single id",
            rounds=((("F-1", "high", "open"), ("F-2", "high", "open")),),
            oq=_oq(finding="F-1, F-2"),
            expect=False,
            loc="",
        ),
        _Case(
            "a question naming the finding in lowercase",
            "the id match is CASE-INSENSITIVE, so a hand-typed `f-1` still escalates; requiring "
            "exact case would fail an operator who did the right thing",
            oq=_oq(finding="f-1"),
            expect=False,
            loc="",
        ),
    )

    def test_the_gate_fires_exactly_when_it_should(self) -> None:
        wrong = []
        must_fire_broken = 0
        must_not_fire_broken = 0
        for case in self.CASES:
            repo, plan, review = _build(case)
            try:
                drift = ce.check_review_finding_unescalated(repo)
                hits = [d for d in drift if d.rule == RULE]
                problems = []
                if bool(hits) is not case.expect:
                    if case.expect:
                        must_fire_broken += 1
                        problems.append(
                            "expected the gate to FIRE, but it reported NOTHING (a gate that "
                            "fell silent lets the finding through every surface that consumes it)"
                        )
                    else:
                        must_not_fire_broken += 1
                        problems.append(
                            "expected SILENCE, but the gate fired: "
                            f"{[d.detail for d in hits]!r}"
                        )
                elif len(hits) > 1:
                    problems.append(
                        f"fired {len(hits)} times for ONE finding; a duplicated report trains "
                        f"operators to ignore it: {[d.detail for d in hits]!r}"
                    )
                elif hits:
                    d = hits[0]
                    expected_path = {"plan": plan, "review": review}.get(case.loc)
                    if expected_path is not None and d.location != str(expected_path):
                        problems.append(
                            f"named {d.location!r}; this row must name the {case.loc.upper()} "
                            f"path {str(expected_path)!r}, which is the file to edit"
                        )
                    for field, needles in (
                        ("detail", case.detail_needles),
                        ("required", case.required_needles),
                        ("recovery", case.recovery_needles),
                    ):
                        text = getattr(d, field, "") or ""
                        for needle in needles:
                            if needle not in text:
                                problems.append(
                                    f"{field} does not mention {needle!r}; it said {text!r}"
                                )
                if problems:
                    wrong.append(
                        f"  {case.case}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {case.why}"
                    )
            finally:
                shutil.rmtree(repo, ignore_errors=True)

        vacuity = ""
        if must_fire_broken:
            vacuity = (
                f" {must_fire_broken} MUST-FIRE row(s) are among the failures, and while any of "
                "those is broken every must-not-fire row here is VACUOUS: an evaluator that "
                "reports nothing at all satisfies all of them."
            )
        elif must_not_fire_broken:
            vacuity = (
                f" {must_not_fire_broken} MUST-NOT-FIRE row(s) failed while every must-fire row "
                "passed, which is the over-blocking direction: the gate is refusing work it "
                "should let through."
            )
        self.assertEqual(
            wrong,
            [],
            f"check.review-finding-unescalated is wrong on {len(wrong)} of {len(self.CASES)} "
            f"inputs.{vacuity} This rule decides whether an unfixed review finding BLOCKS a plan, "
            "so a row that fell silent lets a real finding reach execution unescalated. READ THE "
            "FAILURES TOGETHER, because the shape of the moved set names the cause: if the "
            "AT-threshold rows moved, the comparison changed between >= and >; if a whole "
            "threshold column moved, config resolution of `review_findings_gate.block_at` broke; "
            "if the `off` row moved, the documented opt-out is gone; if the ROUND rows moved, "
            "`current_findings()` stopped filtering by round; if the open-question rows moved, the "
            "`- Finding:` subfield match broke; if the LANE rows moved, the pending-lane scoping "
            "that grandfathers the terminal corpus is gone. FIX: a row reporting NOTHING is worse "
            "than one reporting the wrong path, because silence is indistinguishable from "
            "compliance at every surface downstream. If the severity/threshold rows fail but "
            "tests/test_review_findings.py's `is_gating` grid passes, the predicate is fine and "
            "the defect is in this rule's config resolution or wiring.\n"
            + "\n".join(wrong),
        )


# --------------------------------------------------------------------------------------
# F-6/F-7: the rule's REACH across `aw check` entry points
# --------------------------------------------------------------------------------------


class GateReachTests(unittest.TestCase):
    """The rule must be REACHED by every `aw check` entry point, and counted exactly once.

    Three tests became one table whose MODE COLUMN is the entry point. Reach is a different claim
    from the outcome table above: a rule can be perfectly correct and still be unwired from the
    fan-out that users actually invoke, and the failure then looks like a clean tree. Keeping the
    entry points in one table means a registration lost from one path is reported beside the paths
    that still have it, which is what identifies it as a wiring change rather than a logic change.

    The `all` fan-out is exercised on the rows where DOUBLE-REPORTING is possible (a rule reached
    through both the plans type and the sweep) rather than on every row, because the full sweep costs
    roughly 150ms against 8ms for the direct evaluator and buys nothing on the silent rows.
    """

    #: (entry point label, the `check_types` targets, escalated?, threshold, expected hit count, why)
    REACH = (
        (
            "direct evaluator",
            None,
            False,
            None,
            1,
            "the function under test, as the control the other rows are compared against",
        ),
        (
            "aw check plans",
            ["plans"],
            False,
            None,
            1,
            "F-6: the plans-type path must reach the rule, since `aw check plans` is what CI runs "
            "fail-closed; a rule absent from this registration is a rule CI never enforces",
        ),
        (
            "aw check all",
            ["all"],
            False,
            None,
            1,
            "F-7: the full sweep must surface the rule EXACTLY ONCE. Two registrations would "
            "double-report every finding, which trains operators to ignore the output",
        ),
        (
            "aw check plans, escalated",
            ["plans"],
            True,
            None,
            0,
            "the clean control for the plans path: without it a path that reported the rule "
            "unconditionally would satisfy the must-fire row above",
        ),
        (
            "aw check all, escalated",
            ["all"],
            True,
            None,
            0,
            "the clean control for the sweep, so a green `aw check all` on a compliant tree is "
            "asserted rather than assumed",
        ),
        (
            "aw check plans, threshold off",
            ["plans"],
            False,
            "off",
            0,
            "the `off` opt-out must hold at the ENTRY POINT too, not only in the evaluator: a "
            "threshold honored by one and ignored by the other is a gate a repo cannot disable",
        ),
    )

    def test_every_entry_point_reaches_the_rule_and_counts_it_once(self) -> None:
        wrong = []
        for label, targets, escalated, threshold, expected, why in self.REACH:
            repo = _mkrepo()
            try:
                _plan(repo, open_questions=_oq(finding="F-1") if escalated else "")
                _review(repo)
                _set_threshold(repo, threshold)
                if targets is None:
                    drift = ce.check_review_finding_unescalated(repo)
                else:
                    drift = ce.check_types(repo, targets)
                got = len([d for d in drift if d.rule == RULE])
                if got != expected:
                    wrong.append(
                        f"  {label}: expected {expected} hit(s), got {got}\n"
                        f"    this row exists because: {why}"
                    )
            finally:
                shutil.rmtree(repo, ignore_errors=True)
        self.assertEqual(
            wrong,
            [],
            f"the rule's reach is wrong at {len(wrong)} of {len(self.REACH)} entry points. These "
            "rows are about WIRING, not logic: the evaluator can be entirely correct while an "
            "entry point never calls it, and that failure presents as a CLEAN tree. Read them "
            "together: if only the `all` row moved, the fan-out lost (or duplicated) the "
            "registration while the type path kept it; if both `plans` and `all` went to 0 while "
            "the direct row still reports 1, the rule was unregistered from `check_types` "
            "altogether; if a count rose above 1, the rule is registered twice. FIX: compare "
            "against `check_engine.check_types`' dispatch table rather than against the evaluator, "
            "which these rows prove is still working.\n" + "\n".join(wrong),
        )


# --------------------------------------------------------------------------------------
# V-02: the lint checkpoints, and lint_text purity
# --------------------------------------------------------------------------------------


class LintCheckpointTests(unittest.TestCase):
    """The rule blocks at exactly two checkpoints, on the FILE route only.

    Four tests became one table over a two-axis grid: the lint PHASE and the ROUTE (`lint_file`, which
    may do I/O, versus `lint_text`, which is pure by contract). Both axes belong in one table because
    the property under test is a relationship between them: the same document must be gated through
    one route and never through the other, at the same phase. Two separate single-route tests cannot
    state that, and a route that started reading the review artifact would break the purity contract
    while every phase test stayed green.

    ON DISPOSITION, and why this table asserts the rule CODE rather than the verdict. The replaced
    tests also asserted `disposition == error` on the gated phases. That assertion is VACUOUS on this
    fixture and was measured to be: the minimal plan stub is a metadata/heading skeleton that already
    lints `error` for unrelated `IPD-M101`/`IPD-H202` complaints, at EVERY phase including the two
    that do not gate. So it would pass with this rule deleted. It is kept on the canonical gated row
    only, explicitly labelled as a weak co-assertion, and the load-bearing claim on every row is
    which phases and routes carry the rule CODE.
    """

    #: (phase, route, escalated?, expect the rule, why this row exists)
    PHASES = (
        (
            "review-finalize",
            "file",
            False,
            True,
            "the moment the reviewer is FINISHING is the moment to demand the escalation, so this "
            "is the earlier of the two gates",
        ),
        (
            "pre-execution",
            "file",
            False,
            True,
            "the LAST gate before work starts, and the one that actually stops a run",
        ),
        (
            "pre-transition",
            "file",
            False,
            False,
            "deliberately NOT gated: by the time a plan finalizes, execution already happened, so "
            "blocking here would only strand completed work instead of preventing anything",
        ),
        (
            "author",
            "file",
            False,
            False,
            "authoring precedes review entirely, so there is no review verdict to escalate yet; "
            "gating here would refuse every plan before it could be reviewed",
        ),
        (
            "review-finalize",
            "file",
            True,
            False,
            "the ESCALATED control at a gated phase: without it, a checkpoint that reported the "
            "rule unconditionally would satisfy the must-gate rows above",
        ),
        (
            "pre-execution",
            "file",
            True,
            False,
            "the escalated control at the second gated phase, proving the escalation clears the "
            "checkpoint and not merely the sweep",
        ),
        (
            "review-finalize",
            "text",
            False,
            False,
            "E-02's PURITY contract: the findings live in a SEPARATE file, so the pure text linter "
            "cannot see them and must never report this rule. A row here turning True means I/O "
            "was wired into `lint_text`",
        ),
        (
            "pre-execution",
            "text",
            False,
            False,
            "purity at the second gated phase too, so the contract is a property of the ROUTE "
            "rather than of one phase's implementation",
        ),
    )

    def test_the_rule_gates_exactly_two_phases_on_the_file_route(self) -> None:
        wrong = []
        gated_rows_broken = 0
        for phase, route, escalated, expect, why in self.PHASES:
            repo = _mkrepo()
            try:
                plan = _plan(
                    repo, open_questions=_oq(finding="F-1") if escalated else ""
                )
                _review(repo)
                if route == "file":
                    res = ipd_lint.lint_file(plan, checkpoint=phase)
                else:
                    res = ipd_lint.lint_text(
                        plan.read_text(encoding="utf-8"),
                        checkpoint=phase,
                        directory="pending",
                    )
                codes = [d.code for d in res.diagnostics]
                problems = []
                if (RULE in codes) is not expect:
                    if expect:
                        gated_rows_broken += 1
                        problems.append(
                            f"expected the rule at this checkpoint; diagnostics were {codes!r}"
                        )
                    else:
                        problems.append(
                            f"the rule must NOT be reported here; diagnostics were {codes!r}"
                        )
                # Weak co-assertion, kept only where it was made and labelled as weak: a gated row
                # must not lint conforming. This fixture errors for unrelated structural reasons at
                # every phase, so it is NOT evidence the rule blocks.
                if expect and res.disposition != S.DISPOSITION_ERROR:
                    problems.append(
                        f"a gated plan must not lint {res.disposition!r}; it must be "
                        f"{S.DISPOSITION_ERROR!r}"
                    )
                if problems:
                    wrong.append(
                        f"  phase={phase} route=lint_{route} "
                        f"{'escalated' if escalated else 'unescalated'}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
            finally:
                shutil.rmtree(repo, ignore_errors=True)
        vacuity = ""
        if gated_rows_broken:
            vacuity = (
                f" {gated_rows_broken} GATED row(s) failed, and while they are broken the "
                "not-gated and purity rows are VACUOUS: a checkpoint hook that reports nothing "
                "satisfies all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"the checkpoint wiring is wrong on {len(wrong)} of {len(self.PHASES)} phase/route "
            f"combinations.{vacuity} Read them together: if BOTH `file` gated rows went False, "
            "`ipd_lint._REVIEW_ESCALATION_CHECKPOINTS` lost its members or "
            "`_merge_review_escalation` is no longer called from `lint_file`; if a NOT-gated phase "
            "turned True, that frozenset gained a member and a finalizing plan will now be "
            "stranded after its work is already done; if a `text` row turned True, the documented "
            "purity of `lint_text` has been broken by wiring file I/O into it, which is a "
            "contract violation and not merely an extra diagnostic. FIX: change the checkpoint "
            "frozenset, never the route, and keep the read in `lint_file`.\n"
            + "\n".join(wrong),
        )


# --------------------------------------------------------------------------------------
# V-08: the `- Finding:` subfield is legal IPD structure
# --------------------------------------------------------------------------------------


class FindingSubfieldStructureTests(unittest.TestCase):
    """The escalation must be LEGAL IPD structure: the extra subfield parses and adds no diagnostic.

    Two tests became one table with the question's `Status:` as the column, which is what separates
    them: the `resolved` row is the clean one, and the `open` row is confounded because this fixture
    independently earns the askme gate's blocking-open complaint. The assertion is therefore narrowed
    the same way the replaced test narrowed it (by NAME: `IPD-Q501`, the code that blocking-open
    question owns), so a row asserts only what it can honestly claim - that the `Finding:` subfield
    contributes NOTHING of its own - rather than asserting the absence of an unrelated rule.
    """

    #: (question status, the codes this fixture independently earns, why this row exists)
    STATUSES = (
        (
            "resolved",
            (),
            "the UNCONFOUNDED row: a resolved question carrying `Finding:` lints FULLY clean, so a "
            "diagnostic emitted by the subfield itself has nowhere to hide",
        ),
        (
            "open",
            ("IPD-Q501",),
            "the shape an operator actually writes when escalating (blocking AND open). It earns "
            "IPD-Q501 from the askme gate on its own merits, independently of the subfield under "
            "test, so that one code is tolerated BY NAME and everything else must be absent",
        ),
    )

    def test_the_finding_subfield_parses_and_adds_no_diagnostic(self) -> None:
        wrong = []
        for status, tolerated, why in self.STATUSES:
            repo = _mkrepo()
            try:
                plan = _plan(
                    repo,
                    open_questions=_oq(blocking="yes", status=status, finding="F-1"),
                )
                parsed = ipd_lint.parse(plan.read_text(encoding="utf-8"))
                problems = []
                got = parsed.open_questions[0].get("Finding")
                if got != "F-1":
                    problems.append(
                        f"the parser did not surface the subfield: Finding={got!r}, expected "
                        "'F-1' (the whole convention is unreadable if this is None)"
                    )
                unexpected = [
                    (d.code, d.message)
                    for d in ipd_lint.check_open_questions(parsed)
                    if d.code not in tolerated
                ]
                if unexpected:
                    problems.append(
                        f"the subfield contributed diagnostics of its own: {unexpected!r} "
                        f"(only {tolerated or 'nothing'} is this fixture's own)"
                    )
                if problems:
                    wrong.append(
                        f"  Status: {status}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
            finally:
                shutil.rmtree(repo, ignore_errors=True)
        self.assertEqual(
            wrong,
            [],
            f"the `- Finding:` subfield is not clean IPD structure in {len(wrong)} of "
            f"{len(self.STATUSES)} question states. This matters because the rule's own recovery "
            "text TELLS an operator to add this subfield: if doing so earns a structural "
            "complaint, the only documented way to clear the gate makes the plan fail a different "
            "gate, and the plan is stuck. Read them together: if the parse assertion failed on "
            "both rows, `Finding` was dropped from `ipd_schema.OQ_FIELDS` and the subfield is now "
            "invisible to every consumer; if only the `resolved` row grew a diagnostic, a new "
            "open-questions check is firing on the subfield itself. FIX: the subfield must remain "
            "a declared OQ field that contributes no diagnostic.\n" + "\n".join(wrong),
        )

    def test_convention_is_declared_in_the_schema(self) -> None:
        """Kept separate: a one-line claim about a module-level vocabulary, not a fixture outcome.

        This is what makes `Finding` a DECLARED subfield rather than one this rule happens to read,
        so it is asserted against the schema directly.
        """
        self.assertIn(
            "Finding",
            S.OQ_FIELDS,
            "`Finding` must be a declared open-question subfield; an undeclared one is at risk of "
            "being stripped by any consumer that validates against OQ_FIELDS",
        )


# --------------------------------------------------------------------------------------
# revsweep `eyh1fu` E-05: the review index, whose failure mode is SILENCE
# --------------------------------------------------------------------------------------


class SubjectFieldIndexTests(unittest.TestCase):
    """`_review_index` keys reviews by the NEUTRAL subject id6, and the gate's fate follows it.

    Three tests became one table with the record's subject SPELLING as the column. `_review_index`
    backs four call sites, two of which implement this rule, and had the field been renamed without
    repointing the index the index would come back EMPTY, the evaluator would take its "nothing
    reviewed" early return, and an unfixed HIGH would gate NOTHING. A green `aw check` is therefore
    NOT evidence here: the regression looks exactly like compliance.

    That is why the two rows are in ONE table and why each asserts TWO kinds of claim about its input
    (the index CONTENTS and the resulting gate outcome) rather than being split into an index test and
    a gate test. The pairing is the point: it distinguishes "the gate passed" from "the gate saw
    nothing", which are indistinguishable in output, and the passing row is the control that keeps the
    silent row from being the only thing asserted.
    """

    #: (spelling, the field line as written in the record, expected index keys, gate fires, why)
    SPELLINGS = (
        (
            "the neutral subject field",
            "- Subject-Id: aaa111",
            {"aaa111"},
            True,
            "THE LOAD-BEARING ROW: with the shipped spelling the record IS indexed and the gate "
            "still FIRES. If this row goes silent the rule has stopped working while looking "
            "exactly like a clean tree",
        ),
        (
            "the retired plan-scoped field",
            "- Plan-Id: aaa111",
            set(),
            False,
            "the CONTRAST: no dual-field compatibility reader exists, by design, so a record "
            "carrying the retired spelling is not indexed and the consequence is SILENCE. This row "
            "documents the exact fail-open this item exists to rule out, which is why the "
            "migration has to be complete rather than best-effort",
        ),
    )

    def test_the_index_and_the_gate_agree_on_the_subject_spelling(self) -> None:
        wrong = []
        for label, field_line, expected_keys, expect_fires, why in self.SPELLINGS:
            repo = _mkrepo()
            try:
                plan = _plan(repo)
                review = _review(repo)
                review.write_text(
                    review.read_text(encoding="utf-8").replace(
                        "- Subject-Id: aaa111", field_line
                    ),
                    encoding="utf-8",
                )
                problems = []
                index = ce._review_index(repo)
                if set(index) != expected_keys:
                    problems.append(
                        f"index keys are {sorted(index)!r}, expected "
                        f"{sorted(expected_keys)!r}"
                    )
                elif expected_keys and index.get("aaa111") != [review]:
                    problems.append(
                        f"the key maps to {index.get('aaa111')!r}, expected [{review!r}]"
                    )
                drift = ce.check_review_finding_unescalated(repo)
                fired = bool(_rules(drift))
                if fired is not expect_fires:
                    problems.append(
                        f"the gate {'fell silent' if expect_fires else 'fired'} here; expected "
                        f"it to {'FIRE' if expect_fires else 'be SILENT'}"
                    )
                elif fired and drift[0].location != str(plan):
                    problems.append(
                        f"the drift named {drift[0].location!r} rather than the plan {str(plan)!r}"
                    )
                if problems:
                    wrong.append(
                        f"  {label}:\n"
                        + "".join(f"    - {p}\n" for p in problems)
                        + f"    this row exists because: {why}"
                    )
            finally:
                shutil.rmtree(repo, ignore_errors=True)
        self.assertEqual(
            wrong,
            [],
            f"the review index or its consequence is wrong on {len(wrong)} of "
            f"{len(self.SPELLINGS)} subject spellings. THE FAILURE MODE HERE IS SILENCE, not a "
            "loud error: an empty index makes every plan look like the 'no review artifact' case, "
            "so the gate reports nothing and the tree looks clean. Read the rows together: if the "
            "NEUTRAL row went silent, `_review_index` stopped recognizing `- Subject-Id:` and NO "
            "gating finding blocks anything anywhere; if the RETIRED row started firing, a "
            "compatibility reader was added, which is a real decision to make deliberately rather "
            "than a bug to fix here. FIX: repoint the index, never widen it silently, and keep "
            "`test_no_review_record_in_the_tree_carries_the_retired_field` green so the silent row "
            "stays hypothetical.\n" + "\n".join(wrong),
        )

    def test_no_review_record_in_the_tree_carries_the_retired_field(self):
        """Kept separate: measured over the REAL repository tree, not an isolated fixture.

        This is the corpus-level invariant that keeps the silent row above hypothetical. A single
        unmigrated record would make its plan's gating findings invisible, and (via
        `subject_gating_blocks` case (b)) a MALFORMED one would block that plan's approval with no
        override.
        """
        repo_root = Path(__file__).resolve().parent.parent
        offenders = []
        for path in rf.iter_review_files(repo_root):
            text = path.read_text(encoding="utf-8")
            doc = rf.parse_review_file(path)
            if "\n- Plan-Id:" in text or not doc.subject_id or not doc.subject_type:
                offenders.append(path.name)
        self.assertEqual(offenders, [])


# --------------------------------------------------------------------------------------
# Structural invariants read off the SOURCE (never behavior)
# --------------------------------------------------------------------------------------


class SourceInvariantTests(unittest.TestCase):
    """Claims about HOW the implementation is written, where behavior cannot express the property.

    Four tests became one table. Every one of them did the identical thing: read a module's source,
    slice out one function body, and assert that some substrings are present and others absent. Only
    the module, the slice bounds, and the two substring sets differed, which is a data row.

    These are NOT behavioral assertions and cannot be replaced by any: "the severity comparison is
    DELEGATED rather than reimplemented" and "`lint_text` performs no file I/O" are both satisfiable
    by an implementation that behaves correctly today and has been quietly forked or made impure, and
    each fork only shows up later as two surfaces disagreeing. Reading them together is also how a
    single refactor that renames a helper across several bodies reports as ONE failure.

    A slice that cannot be located is itself a failure and is reported as one, because a renamed
    function silently turns a vacuous pass into permanent green.
    """

    #: (label, module, start marker, end marker (or None for a fixed window), required, forbidden, why)
    INVARIANTS = (
        (
            "the escalation evaluator delegates severity ranking",
            ce,
            "def evaluate_review_finding_escalation",
            "def check_review_finding_unescalated",
            ("is_gating(",),
            ("_SEVERITY_RANK", "SEVERITIES.index", '"blocker"'),
            "E-01 forbids a LOCAL severity comparison: there must be exactly one ordering in the "
            "codebase, or this gate and the cascade can disagree about what `high` outranks. A "
            "literal severity name in this body is the signature of a hand-rolled comparison",
        ),
        (
            "the malformed case is an explicit branch",
            ce,
            "def evaluate_review_finding_escalation",
            "def check_review_finding_unescalated",
            ("if doc.diagnostics:",),
            (),
            "fail-closed on a malformed artifact must be a DELIBERATE branch on parser "
            "diagnostics, not a side effect of an enclosing `except Exception: pass`. An "
            "inherited one would silently become an absence (and therefore silent) the moment the "
            "surrounding code changed",
        ),
        (
            "lint_text performs no file I/O",
            ipd_lint,
            "def lint_text(",
            "def _draft_ready_advisory",
            (),
            ("read_text", "open(", "iter_review_files", "evaluate_review"),
            "`lint_text` is PURE by documented contract, and this rule's subject lives in a "
            "SEPARATE file. A read here would both break that contract and make the pure route "
            "silently disagree with `lint_file` depending on the caller's cwd",
        ),
        (
            "the checkpoint hook reuses the parsed open questions",
            ipd_lint,
            "def _merge_review_escalation",
            None,
            ("open_questions=",),
            (),
            "the hook must pass the ALREADY-PARSED open questions to the shared evaluator rather "
            "than re-parsing the plan, so the checkpoint and the sweep cannot disagree about what "
            "the plan asked and the parse is not paid for twice",
        ),
    )

    def test_every_structural_invariant_holds(self) -> None:
        wrong = []
        for label, module, start, end, required, forbidden, why in self.INVARIANTS:
            problems = []
            src = Path(str(module.__file__)).read_text(encoding="utf-8")
            if start not in src:
                problems.append(
                    f"could not find {start!r} in {module.__name__}: the function was renamed or "
                    "removed, so this invariant is no longer being checked AT ALL"
                )
            elif end is not None and end not in src:
                problems.append(
                    f"could not find the slice end {end!r} in {module.__name__}, so the body "
                    "under test cannot be isolated"
                )
            else:
                begin = src.index(start)
                body = src[begin : src.index(end)] if end else src[begin : begin + 4000]
                missing = [s for s in required if s not in body]
                if missing:
                    problems.append(f"the body no longer contains {missing!r}")
                leaked = [s for s in forbidden if s in body]
                if leaked:
                    problems.append(
                        f"the body now contains {leaked!r}, which it must not"
                    )
            if problems:
                wrong.append(
                    f"  {label} ({module.__name__}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.INVARIANTS)} structural invariants broke. These rows "
            "assert HOW the code is written because the corresponding defects are invisible to "
            "behavior: a forked severity ordering and an impure `lint_text` both pass every "
            "behavioral test on the day they are introduced and only surface later as two "
            "surfaces disagreeing. Read them together: several rows failing at once usually means "
            "one refactor moved or renamed a shared helper rather than several independent "
            "regressions. FIX: if a row failed because a SLICE could not be located, update the "
            "marker here, since a renamed function turns this check into a vacuous pass; if it "
            "failed on a forbidden substring, delete the duplicate logic rather than relaxing the "
            "row.\n" + "\n".join(wrong),
        )


class RuleRegistrationTests(unittest.TestCase):
    def test_rule_id_resolves_to_a_registered_rulespec(self):
        """Kept separate: several claims about ONE registry object, not a cluster of data rows.

        An UNREGISTERED id silently falls back to `_DEFAULT_RULESPEC` with an EMPTY invariant, which
        would leave the finding unclassified while the module claims none are.
        """
        spec = ce.rule_spec(RULE)
        self.assertIn(RULE, ce.RULE_REGISTRY)
        self.assertIsNot(spec, ce._DEFAULT_RULESPEC)
        self.assertEqual(spec.severity, "error")
        self.assertEqual(spec.assurance, ce.ASSURANCE_REPOSITORY)
        self.assertEqual(spec.determinism, ce.DET_DETERMINISTIC)


# --------------------------------------------------------------------------------------
# The END-TO-END chain: the reuse actually closes the loop
# --------------------------------------------------------------------------------------


class EndToEndReuseChainTests(_RepoCase):
    def test_escalation_is_then_caught_by_the_preexisting_pre_execution_gate(self):
        """Kept separate: a STATEFUL three-step mutation of one file, not a data row.

        The whole design rests on this: escalating a gating finding does not merely silence THIS rule,
        it hands the block to the gate that already existed. The claim is about the TRANSITION between
        two states of the same file, which a row asserting one outcome cannot express.
        """
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
        """Kept separate: asserts TWO different gates are simultaneously silent, not one outcome.

        A plan is not permanently stuck: fixing the finding clears both surfaces.
        """
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
        """Kept separate: a BULK corpus fixture (22 plans across three lanes), not a single-plan row.

        This is the live-corpus SHAPE (many plans, zero `.review.md`) as an isolated fixture, and the
        scale is the point: it is what proves the rule adds nothing to a real tree on day one.
        """
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
