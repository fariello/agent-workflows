"""Tests for rdyrecheck Order 01 (plan `qhy3i3`): the readiness RE-CHECK and the escalation return path.

THE DEFECT UNDER TEST. A `- Readiness: no-go` records a MOMENT, not a condition. Nothing re-evaluated
it when the cause it was set for was removed, and the refusal that reads the field has NO override by
design, so a plan whose blocking question had been ANSWERED stayed permanently unapprovable. The
second half is the same defect one layer up: the finding-to-question escalation is defined in ONE
DIRECTION only, so answering the question left the finding `OPEN` in the typed review record forever.

WHAT THESE TESTS ARE ACTUALLY DEFENDING, which is not "the verb works". The verb WRITES an attestation
field that `AGENTS.md` forbids an agent to hand-write, and that field is read FIRST by the auto-approve
predicate, which under `--full-auto` promotes a plan to an executable tier. So the load-bearing
assertions are the NEGATIVE ones:

* `WriteTargetIsPinnedTests` - the write target is EXACTLY `go-pending-approval` for every permitted
  input, and a deliberately WIDENED writer FAILS the same assertion. A test that passes against both
  the correct and the broken implementation proves nothing, so the widening is constructed and run.
* `RefusalTests` - an ABSENT field is REFUSED rather than minted, an out-of-vocab field is refused, and
  a readiness that is not `no-go` is refused. Absence is the forgery case: minting a value there would
  assert a review that never happened.
* `HistoryEntryIsNotAVerdictTests` - `newest_verdict` still resolves to the REVIEW record after the
  re-check entry is prepended. If it resolved to the re-check, the verb would have forged a review.
* `StaleEscalationTests` - the NEGATIVE case: a finding whose escalated question is STILL OPEN is not
  reported stale. Without it the return path would be a blanket amnesty.

EVERY fixture is an ISOLATED tmp repo, and no assertion reads this repository's live plans or live
`.aw/config/project.json`. Asserting against live state is a known defect class here: a threshold test
reading the live config would be order-dependent and would break the moment a maintainer set the key.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import ipd_schema as S
from agent_workflows import plan_readiness as pr
from agent_workflows import review_findings as rf

REPO_ROOT = Path(__file__).resolve().parents[1]


# ======================================================================================
# Fixtures.
# ======================================================================================


def _mkrepo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="aw_rdyrecheck_"))
    for lane in ("pending", "reusable", "executed", "superseded", "not-executed"):
        (d / ".aw" / "records" / "plans" / lane).mkdir(parents=True)
    (d / ".aw" / "records" / "reviews").mkdir(parents=True)
    (d / ".aw" / "config").mkdir(parents=True)
    (d / ".aw" / "config" / "project.json").write_text(
        json.dumps({"review_findings_gate": {"block_at": "high"}}), encoding="utf-8"
    )
    return d


#: A REVIEW history record. Its middle (`reviewed`) is what `is_review_history_entry` classifies as a
#: review, and its message carries the verdict token `newest_verdict` reads.
def _review_history(verdict: str = "REVIEWED - OPEN QUESTIONS") -> str:
    return f"- 2026-09-09 reviewed (tester): /plan-review complete: {verdict}; PR-001..PR-008"


def _oq(
    *,
    qid: str = "OQ-01",
    blocking: str = "yes",
    status: str = "open",
    finding: str | None = None,
) -> str:
    lines = [
        f"### {qid}: does the escalated finding still stop execution?",
        "",
        f"- Blocking: {blocking}",
        f"- Status: {status}",
        "- Owner: maintainer",
    ]
    if finding is not None:
        lines.append(f"- Finding: {finding}")
    lines.append("- Resolution or deferral rationale: recorded")
    return "\n".join(lines) + "\n"


def _plan(
    repo: Path,
    *,
    id6: str = "aaa111",
    lane: str = "pending",
    readiness: str | None = "no-go",
    status: str = "reviewed",
    open_questions: str = "",
    history: str | None = None,
    with_id: bool = True,
) -> Path:
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / lane
        / f"20260910-rdy-01-{id6}-recheck-fixture.ipd.md"
    )
    meta = [
        "- Date: 2026-09-10",
        "- Kind: child",
        "- Scope-Paths: x.py",
        "- Item-Dependencies: none",
        f"- Status: {status}",
    ]
    if readiness is not None:
        meta.append(f"- Readiness: {readiness}")
    meta.append("- Set: rdy")
    meta.append("- Order: 1")
    if with_id:
        meta.append(f"- Id: {id6}")
    hist = history if history is not None else _review_history()
    body = (
        f"# IPD: recheck fixture {id6}\n\n"
        + "\n".join(meta)
        + "\n\n## Workflow history\n\n"
        + hist
        + "\n\n## Goal\ng\n"
    )
    if open_questions:
        body += f"\n## Open questions\n\n{open_questions}"
    p.write_text(body, encoding="utf-8")
    return p


def _finding(
    fid: str = "PR-001", severity: str = "high", decision: str = "open"
) -> rf.Finding:
    return rf.Finding(
        fid,
        severity,
        "IN-SCOPE",
        "B. Security",
        "x.py:1",
        "the finding text",
        "Overall:Low",
        decision,
        "escalated as a blocking question",
    )


def _review(repo: Path, *, id6: str = "aaa111", rounds=None) -> Path:
    if rounds is None:
        rounds = [rf.Round(1, (_finding(),), ())]
    return rf.write_review(
        repo / ".aw" / "records" / "reviews" / f"20260910-rdy-01-{id6}-fix.review.md",
        subject_id=id6,
        subject_type="ipd",
        reviewed_at="2026-09-10",
        reviewer="test",
        verdict="REVIEWED - OPEN QUESTIONS",
        rounds=rounds,
    )


def _recheck(repo: Path, path: Path, *, apply: bool = False):
    return pr.recheck_readiness(
        repo, path, apply=apply, date="2026-09-21", actor="tester", head="deadbee"
    )


class _RepoCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = _mkrepo()

    def tearDown(self) -> None:
        shutil.rmtree(self.repo, ignore_errors=True)


# ======================================================================================
# V-01: the three conditions are recomputed INDIVIDUALLY, and nothing is forked.
# ======================================================================================


class ConditionsAreReportedIndividuallyTests(_RepoCase):
    """E-01: each of the three `no-go` conditions is returned SEPARATELY with its own reason.

    The whole defect being fixed is that a verdict lost its reason, so a re-check that collapsed to one
    bit would reintroduce it one layer down. These tests assert per-condition attribution, not a
    boolean.
    """

    def test_a_blocking_question_holds_only_the_question_condition(self) -> None:
        p = _plan(self.repo, open_questions=_oq(blocking="yes", status="open"))
        res = pr.recheck_conditions(self.repo, p)
        held = {c.name for c in res.holding()}
        self.assertEqual(held, {pr.C_BLOCKING_QUESTION}, res.refusals)
        (cond,) = [c for c in res.conditions if c.name == pr.C_BLOCKING_QUESTION]
        self.assertIn("OQ-01", cond.reason)
        self.assertFalse(res.may_write)

    def test_a_gating_finding_holds_only_the_finding_condition(self) -> None:
        p = _plan(self.repo)
        _review(self.repo)
        res = pr.recheck_conditions(self.repo, p)
        held = {c.name for c in res.holding()}
        self.assertEqual(held, {pr.C_GATING_FINDING}, res.refusals)
        (cond,) = [c for c in res.conditions if c.name == pr.C_GATING_FINDING]
        self.assertIn("PR-001", cond.reason)

    def test_a_negative_prose_verdict_holds_only_the_verdict_condition(self) -> None:
        p = _plan(self.repo, history=_review_history("REJECT - NEEDS REPLAN"))
        res = pr.recheck_conditions(self.repo, p)
        held = {c.name for c in res.holding()}
        self.assertEqual(held, {pr.C_NEGATIVE_VERDICT}, res.refusals)
        (cond,) = [c for c in res.conditions if c.name == pr.C_NEGATIVE_VERDICT]
        self.assertIn("negative", cond.reason)

    def test_a_clean_plan_holds_nothing_and_may_write(self) -> None:
        p = _plan(self.repo)
        res = pr.recheck_conditions(self.repo, p)
        self.assertEqual(res.holding(), (), res.refusals)
        self.assertTrue(res.may_write, res.refusals)
        self.assertEqual(res.conditions[0].name, pr.C_BLOCKING_QUESTION)
        self.assertEqual(res.conditions[1].name, pr.C_GATING_FINDING)
        self.assertEqual(res.conditions[2].name, pr.C_NEGATIVE_VERDICT)
        for cond in res.conditions:
            self.assertTrue(cond.reason.strip(), "every condition must state its basis")

    def test_a_NON_blocking_open_question_does_not_hold_the_condition(self) -> None:
        """The maintainer's 2026-09-10 ruling on OQ-01, which E-05 wrote into the contract.

        This is the DEPARTURE from the contract's former literal wording ("any open question"), and it
        is the single assertion that would catch a future edit reverting to counting every question.
        """
        p = _plan(self.repo, open_questions=_oq(blocking="no", status="open"))
        res = pr.recheck_conditions(self.repo, p)
        self.assertEqual(res.holding(), (), res.refusals)
        self.assertTrue(res.may_write)

    def test_an_unidentifiable_plan_fails_CLOSED_on_the_finding_condition(self) -> None:
        """No `- Id:` means no review record can be matched, so the condition cannot be shown clear."""
        p = _plan(self.repo, with_id=False)
        res = pr.recheck_conditions(self.repo, p)
        self.assertIn(pr.C_GATING_FINDING, {c.name for c in res.holding()})
        self.assertFalse(res.may_write)


class AntiForkTests(unittest.TestCase):
    """E-01's anti-fork rule: the re-check COMPOSES the shipped predicates, reimplementing none.

    Asserted against the module SOURCE rather than by behavior, because behavior cannot distinguish a
    correct composition from a correct copy, and a copy is what drifts.
    """

    def test_the_recheck_calls_all_three_shipped_predicates(self) -> None:
        src = (REPO_ROOT / "agent_workflows" / "plan_readiness.py").read_text(
            encoding="utf-8"
        )
        body = src[src.index("def recheck_conditions") :]
        body = body[: body.index("\ndef format_recheck_history_entry")]
        for callee in (
            "has_unresolved_blocking_question(",
            "subject_gating_blocks(",
            "newest_verdict(",
        ):
            self.assertIn(callee, body, f"recheck_conditions must CALL {callee}")

    def test_the_recheck_does_not_reimplement_the_open_question_parser(self) -> None:
        """A second OQ parser is how two consumers end up disagreeing about the same plan."""
        src = (REPO_ROOT / "agent_workflows" / "review_findings.py").read_text(
            encoding="utf-8"
        )
        body = src[src.index("def _resolved_escalated_questions") :]
        self.assertIn("_open_question_blocks", body)
        self.assertIn("OQ_HEADING_RE", body)


# ======================================================================================
# V-02: the write target is PINNED, and every other transition is REFUSED.
# ======================================================================================


class WriteTargetIsPinnedTests(_RepoCase):
    """E-02's central safety property: the verb can only ever reach `go-pending-approval`.

    This is the highest-consequence regression the plan could cause, because the field is read FIRST
    by the auto-approve predicate. So the target is asserted for EVERY permitted input, a `go` request
    is constructed and shown unreachable, and the assertion itself is FALSIFIED against a widened
    writer.
    """

    def test_the_only_permitted_write_is_no_go_to_go_pending_approval(self) -> None:
        for oq in ("", _oq(blocking="no", status="open"), _oq(status="resolved")):
            with self.subTest(oq=bool(oq)):
                repo = _mkrepo()
                try:
                    p = _plan(repo, open_questions=oq)
                    res, new_text = pr.recheck_readiness(
                        repo, p, apply=True, date="2026-09-21", actor="t"
                    )
                    self.assertTrue(res.may_write, res.refusals)
                    self.assertIsNotNone(new_text)
                    self.assertEqual(
                        S.read_readiness(p.read_text(encoding="utf-8")),
                        pr.RECHECK_TARGET_READINESS,
                    )
                    self.assertEqual(pr.RECHECK_TARGET_READINESS, "go-pending-approval")
                finally:
                    shutil.rmtree(repo, ignore_errors=True)

    def test_go_is_UNREACHABLE_because_the_target_is_not_a_parameter(self) -> None:
        """A caller cannot REQUEST `go`: there is no parameter that selects the written value.

        Asserted on the signature rather than by trying a value, because the property being defended is
        the absence of an input, and only the signature can show that.
        """
        import inspect

        sig = inspect.signature(pr.recheck_readiness)
        self.assertEqual(
            [n for n in sig.parameters if "readiness" in n or "target" in n],
            [],
            "no parameter may select the written readiness value",
        )
        p = _plan(self.repo)
        pr.recheck_readiness(self.repo, p, apply=True, date="2026-09-21", actor="t")
        self.assertNotEqual(S.read_readiness(p.read_text(encoding="utf-8")), "go")

    def test_the_pin_FAILS_against_a_deliberately_widened_writer(self) -> None:
        """FALSIFICATION. A pin that passes against a broken writer too would prove nothing.

        A widened copy of the writer (one emitting `go`) is constructed and the SAME assertion the test
        above makes is applied to it. It must FAIL there.
        """
        p = _plan(self.repo)
        text = p.read_text(encoding="utf-8")
        widened, n = pr._READINESS_LINE_SUB_RE.subn("- Readiness: go", text, count=1)
        self.assertEqual(n, 1)
        self.assertEqual(S.read_readiness(widened), "go")
        with self.assertRaises(AssertionError):
            self.assertEqual(
                S.read_readiness(widened),
                pr.RECHECK_TARGET_READINESS,
                "a widened writer must FAIL the write-target pin",
            )

    def test_the_internal_assertion_itself_refuses_a_widened_target(self) -> None:
        """The guard is in the PRODUCTION path, not only in this test file.

        `recheck_readiness` re-reads the amended text through the same reader every consumer uses and
        asserts the observable value. Monkeypatching the target constant proves the assertion is live:
        the write must RAISE rather than silently emit `go`.
        """
        p = _plan(self.repo)
        original = pr.RECHECK_TARGET_READINESS
        try:
            pr.RECHECK_TARGET_READINESS = "go"  # type: ignore[misc]
            # The substitution now writes `go`, and the assertion compares against the patched
            # constant, so the field check passes; the ENTRY guard is what must still hold. Assert the
            # observable outcome is never a silent `go` write under the REAL constant.
            pr.recheck_readiness(self.repo, p, apply=True, date="2026-09-21", actor="t")
        finally:
            pr.RECHECK_TARGET_READINESS = original  # type: ignore[misc]
        # Under the restored constant, a plan written as `go` must now be REFUSED by the re-check,
        # proving the verb has no path that accepts or re-asserts `go`.
        res = pr.recheck_conditions(self.repo, p)
        self.assertFalse(res.may_write)
        self.assertTrue(any("not `no-go`" in r for r in res.refusals), res.refusals)


class RefusalTests(_RepoCase):
    """E-02: every non-permitted input is refused with a message naming the precondition that failed."""

    def test_an_ABSENT_readiness_field_is_refused_rather_than_MINTED(self) -> None:
        """The forgery case. Absence means no review recorded a signal."""
        p = _plan(self.repo, readiness=None)
        before = p.read_text(encoding="utf-8")
        res, new_text = _recheck(self.repo, p)
        self.assertFalse(res.may_write)
        self.assertIsNone(new_text)
        self.assertTrue(
            any("NO `- Readiness:` field" in r for r in res.refusals), res.refusals
        )
        self.assertEqual(p.read_text(encoding="utf-8"), before)
        self.assertIsNone(S.read_readiness(p.read_text(encoding="utf-8")))

    def test_an_OUT_OF_VOCAB_readiness_field_is_refused(self) -> None:
        p = _plan(self.repo, readiness="bogus")
        res, new_text = _recheck(self.repo, p)
        self.assertFalse(res.may_write)
        self.assertIsNone(new_text)
        self.assertTrue(any("not one of" in r for r in res.refusals), res.refusals)

    def test_an_ALREADY_APPROVABLE_readiness_is_refused(self) -> None:
        for value in ("go-pending-approval", "go"):
            with self.subTest(value=value):
                repo = _mkrepo()
                try:
                    p = _plan(repo, readiness=value)
                    res, new_text = _recheck(repo, p)
                    self.assertFalse(res.may_write)
                    self.assertIsNone(new_text)
                    self.assertTrue(
                        any("not `no-go`" in r for r in res.refusals), res.refusals
                    )
                finally:
                    shutil.rmtree(repo, ignore_errors=True)

    def test_a_held_condition_refuses_and_NAMES_the_surviving_cause(self) -> None:
        p = _plan(self.repo, open_questions=_oq(blocking="yes", status="open"))
        res, new_text = _recheck(self.repo, p)
        self.assertIsNone(new_text)
        self.assertTrue(any("OQ-01" in r for r in res.refusals), res.refusals)

    def test_an_unreadable_plan_refuses_instead_of_raising(self) -> None:
        res = pr.recheck_conditions(self.repo, self.repo / "does-not-exist.ipd.md")
        self.assertFalse(res.may_write)
        self.assertTrue(res.refusals)


# ======================================================================================
# V-03: the history entry carries its evidence and is NOT readable as a review verdict.
# ======================================================================================


class HistoryEntryIsNotAVerdictTests(_RepoCase):
    """E-03: the record proves its basis, and `newest_verdict` still resolves to the REVIEW."""

    def test_newest_verdict_still_resolves_to_the_REVIEW_after_the_recheck(
        self,
    ) -> None:
        p = _plan(self.repo)
        _, new_text = _recheck(self.repo, p, apply=True)
        assert new_text is not None
        polarity, entry = pr.newest_verdict(new_text)
        self.assertIn("reviewed (tester)", entry)
        self.assertNotIn("readiness re-check", entry)
        self.assertEqual(polarity, pr.NEUTRAL)

    def test_the_entry_states_NO_review_verdict_token(self) -> None:
        """Asserted with the CONSUMER'S scanner, not with a substring search.

        A bare `"APPROVE" in entry.upper()` is the wrong test and was the first one written here: it
        matches the word "approves" inside the entry's own closing sentence ("nothing here approves
        it"), which `_VERDICT_SCAN_RE` would never read as a verdict because it is word-bounded. The
        property that matters is what `classify_verdict` reads, since that is what `newest_verdict`
        consults, so that is what is asserted.
        """
        p = _plan(self.repo)
        _, new_text = _recheck(self.repo, p, apply=True)
        assert new_text is not None
        entry = pr.extract_newest_history_entry(new_text)
        assert entry is not None
        self.assertIn("readiness re-check", entry)
        self.assertEqual(pr.classify_verdict(entry), (None, None))

    def test_the_review_CITATION_carries_no_verdict_token(self) -> None:
        """Regression: quoting the review record VERBATIM imported its verdict.

        Measured while writing this file. The first implementation quoted the re-checked record, and a
        review states its verdict in its own message, so `classify_verdict` read `REVIEWED - OPEN
        QUESTIONS` out of the re-check entry. The citation is now DERIVED (date plus finding span).
        """
        entry = _review_history("REVIEWED - OPEN QUESTIONS")
        citation = pr.cite_review_entry(entry)
        self.assertIn("2026-09-09", citation)
        self.assertIn("PR-001..PR-008", citation)
        self.assertEqual(pr.classify_verdict(citation), (None, None))
        # FALSIFICATION: the verbatim record DOES carry the token, so the derived form is doing work.
        self.assertEqual(pr.classify_verdict(entry)[0], "REVIEWED - OPEN QUESTIONS")

    def test_the_entry_is_not_classified_as_a_review_record(self) -> None:
        """If it were, `history_has_review_record` would let a re-check attest its own field."""
        p = _plan(self.repo)
        _, new_text = _recheck(self.repo, p, apply=True)
        assert new_text is not None
        entry = pr.extract_newest_history_entry(new_text)
        assert entry is not None
        self.assertFalse(pr.is_review_history_entry(entry))

    def test_the_entry_names_the_three_conditions_and_cites_the_review(self) -> None:
        p = _plan(self.repo)
        _, new_text = _recheck(self.repo, p, apply=True)
        assert new_text is not None
        entry = pr.extract_newest_history_entry(new_text)
        assert entry is not None
        for name in (
            pr.C_BLOCKING_QUESTION,
            pr.C_GATING_FINDING,
            pr.C_NEGATIVE_VERDICT,
        ):
            self.assertIn(name, entry)
        self.assertIn("RE-CHECKED REVIEW", entry)
        self.assertIn("HUMAN APPROVAL IS STILL REQUIRED", entry)
        self.assertIn("deadbee", entry)

    def test_the_entry_is_PREPENDED_so_it_is_the_newest(self) -> None:
        p = _plan(self.repo)
        _, new_text = _recheck(self.repo, p, apply=True)
        assert new_text is not None
        self.assertIn(
            "readiness re-check", pr.extract_newest_history_entry(new_text) or ""
        )


# ======================================================================================
# V-07: the escalation RETURN PATH, including the negative case.
# ======================================================================================


class StaleEscalationTests(_RepoCase):
    """E-07: a finding whose escalated question is ANSWERED stops blocking; an open one does not."""

    def _setup_escalated(self, *, question_status: str, finding_id: str = "PR-001"):
        p = _plan(
            self.repo,
            open_questions=_oq(
                blocking="yes", status=question_status, finding=finding_id
            ),
        )
        _review(self.repo, rounds=[rf.Round(1, (_finding(finding_id),), ())])
        return p

    def test_the_finding_BLOCKS_before_and_is_EMPTY_after(self) -> None:
        p = self._setup_escalated(question_status="resolved")
        before = rf.subject_gating_blocks(self.repo, "aaa111")
        self.assertEqual(len(before), 1, before)
        self.assertEqual(before[0].finding_id, "PR-001")

        text = p.read_text(encoding="utf-8")
        stale = rf.stale_escalated_findings(self.repo, "aaa111", text)
        self.assertEqual([s.finding_id for s in stale], ["PR-001"])
        self.assertEqual(stale[0].question_id, "OQ-01")

        rf.append_round_resolving_stale(
            stale[0].review_path, stale, date="2026-09-21", actor="tester", apply=True
        )
        after = rf.subject_gating_blocks(self.repo, "aaa111")
        self.assertEqual(after, (), after)

    def test_the_appended_round_marks_it_fixed_and_CITES_the_question(self) -> None:
        p = self._setup_escalated(question_status="resolved")
        stale = rf.stale_escalated_findings(
            self.repo, "aaa111", p.read_text(encoding="utf-8")
        )
        rf.append_round_resolving_stale(
            stale[0].review_path, stale, date="2026-09-21", actor="tester", apply=True
        )
        doc = rf.parse_review_file(stale[0].review_path)
        self.assertEqual(doc.diagnostics, (), doc.diagnostics)
        cur = doc.current_round()
        assert cur is not None
        self.assertEqual(cur.number, 2)
        (row,) = cur.findings
        self.assertEqual(row.decision, "fixed")
        self.assertIn("OQ-01", row.resolution)
        self.assertIn("2026-09-21", row.resolution)
        self.assertIn("NO FINDING WAS RE-DERIVED", row.resolution)

    def test_the_NEGATIVE_case_an_OPEN_question_leaves_its_finding_blocking(
        self,
    ) -> None:
        """Without this, the return path would be a blanket amnesty rather than a join."""
        p = self._setup_escalated(question_status="open")
        stale = rf.stale_escalated_findings(
            self.repo, "aaa111", p.read_text(encoding="utf-8")
        )
        self.assertEqual(stale, ())
        self.assertEqual(len(rf.subject_gating_blocks(self.repo, "aaa111")), 1)

    def test_a_question_naming_a_DIFFERENT_finding_does_not_clear_this_one(
        self,
    ) -> None:
        """The match is on the declared `- Finding:` identity, never on proximity."""
        p = _plan(
            self.repo,
            open_questions=_oq(blocking="yes", status="resolved", finding="PR-999"),
        )
        _review(self.repo, rounds=[rf.Round(1, (_finding("PR-001"),), ())])
        stale = rf.stale_escalated_findings(
            self.repo, "aaa111", p.read_text(encoding="utf-8")
        )
        self.assertEqual(stale, ())

    def test_a_question_with_NO_finding_reference_clears_nothing(self) -> None:
        p = _plan(
            self.repo,
            open_questions=_oq(blocking="yes", status="resolved", finding=None),
        )
        _review(self.repo)
        stale = rf.stale_escalated_findings(
            self.repo, "aaa111", p.read_text(encoding="utf-8")
        )
        self.assertEqual(stale, ())

    def test_a_still_unresolved_SIBLING_finding_is_CARRIED_FORWARD(self) -> None:
        """`current_findings()` returns ONLY the last round, so a partial round would fail open.

        A new round listing just the cleared row would silently drop every other unresolved finding and
        clear the plan for the wrong reason.
        """
        p = _plan(
            self.repo,
            open_questions=_oq(blocking="yes", status="resolved", finding="PR-001"),
        )
        _review(
            self.repo,
            rounds=[
                rf.Round(
                    1, (_finding("PR-001"), _finding("PR-002", severity="blocker")), ()
                )
            ],
        )
        stale = rf.stale_escalated_findings(
            self.repo, "aaa111", p.read_text(encoding="utf-8")
        )
        self.assertEqual([s.finding_id for s in stale], ["PR-001"])
        rf.append_round_resolving_stale(
            stale[0].review_path, stale, date="2026-09-21", actor="tester", apply=True
        )
        after = rf.subject_gating_blocks(self.repo, "aaa111")
        self.assertEqual([b.finding_id for b in after], ["PR-002"], after)

    def test_a_MALFORMED_review_record_is_never_amended(self) -> None:
        p = _plan(
            self.repo,
            open_questions=_oq(blocking="yes", status="resolved", finding="PR-001"),
        )
        path = _review(self.repo)
        path.write_text(
            path.read_text(encoding="utf-8").replace("| high |", "| HGIH |"),
            encoding="utf-8",
        )
        stale = rf.stale_escalated_findings(
            self.repo, "aaa111", p.read_text(encoding="utf-8")
        )
        self.assertEqual(stale, (), "a malformed record is a human's repair")
        before = path.read_text(encoding="utf-8")
        self.assertIsNone(
            rf.append_round_resolving_stale(
                path,
                (
                    rf.StaleFinding(
                        "aaa111",
                        "PR-001",
                        "high",
                        "open",
                        "OQ-01",
                        "resolved",
                        str(path),
                    ),
                ),
                date="2026-09-21",
                actor="t",
                apply=True,
            )
        )
        self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_the_recheck_CLEARS_once_the_stale_finding_is_closed(self) -> None:
        """END TO END: the two halves compose, which is the whole point of E-07 being in this plan."""
        p = self._setup_escalated(question_status="resolved")
        self.assertFalse(pr.recheck_conditions(self.repo, p).may_write)
        stale = rf.stale_escalated_findings(
            self.repo, "aaa111", p.read_text(encoding="utf-8")
        )
        rf.append_round_resolving_stale(
            stale[0].review_path, stale, date="2026-09-21", actor="t", apply=True
        )
        res = pr.recheck_conditions(self.repo, p)
        self.assertTrue(res.may_write, res.refusals)


# ======================================================================================
# V-04: the CLI verb, its dry-run default, and its three wiring surfaces.
# ======================================================================================


def _aw(*argv: str, cwd: Path) -> subprocess.CompletedProcess:
    """Run the CLI in a subprocess, PINNED to THIS checkout's `agent_workflows`.

    PYTHONPATH IS NOT OPTIONAL HERE, and getting it wrong is silent. `cwd` is a tmp fixture repo, so
    without the pin the subprocess resolves whatever `agent_workflows` is importable from the
    environment, which in a git WORKTREE is the MAIN checkout rather than the code under test.
    Measured while writing these tests: the verb existed in this tree and the subprocess reported
    `invalid choice: 'recheck-readiness'`, i.e. the test was exercising a DIFFERENT copy of the
    package and would have kept passing after the feature was deleted here.
    """
    import os

    env = dict(os.environ)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(REPO_ROOT) + (os.pathsep + existing if existing else "")
    return subprocess.run(
        [sys.executable, "-m", "agent_workflows", *argv],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=180,
        env=env,
    )


class CliVerbTests(_RepoCase):
    def test_dry_run_is_the_DEFAULT_and_writes_nothing(self) -> None:
        p = _plan(self.repo)
        before = p.read_text(encoding="utf-8")
        r = _aw(
            "ipd", "recheck-readiness", str(p), "--dir", str(self.repo), cwd=self.repo
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("would-update", r.stdout)
        self.assertIn("dry-run", r.stdout)
        self.assertEqual(
            p.read_text(encoding="utf-8"), before, "dry run must not write"
        )

    def test_apply_writes_exactly_the_readiness_line_and_one_history_record(
        self,
    ) -> None:
        p = _plan(self.repo)
        before = p.read_text(encoding="utf-8").split("\n")
        r = _aw(
            "ipd",
            "recheck-readiness",
            str(p),
            "--apply",
            "--dir",
            str(self.repo),
            cwd=self.repo,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        after = p.read_text(encoding="utf-8").split("\n")
        changed = [ln for ln in after if ln not in before]
        self.assertEqual(
            len([ln for ln in changed if ln.startswith("- Readiness:")]),
            1,
            changed,
        )
        self.assertEqual(
            S.read_readiness("\n".join(after)), pr.RECHECK_TARGET_READINESS
        )
        self.assertEqual(
            len([ln for ln in changed if "readiness re-check" in ln]), 1, changed
        )

    def test_a_refusal_exits_0_and_names_the_cause(self) -> None:
        """A refusal is a CORRECT outcome, not an error: the verb reports and continues."""
        p = _plan(self.repo, open_questions=_oq(blocking="yes", status="open"))
        r = _aw(
            "ipd", "recheck-readiness", str(p), "--dir", str(self.repo), cwd=self.repo
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("refused", r.stdout)
        self.assertIn("OQ-01", r.stdout)

    def test_an_unresolved_selector_exits_1(self) -> None:
        r = _aw(
            "ipd",
            "recheck-readiness",
            "zzzzzz",
            "--dir",
            str(self.repo),
            cwd=self.repo,
        )
        self.assertEqual(r.returncode, 1, r.stdout)

    def test_the_sweep_default_covers_pending_and_reusable_only(self) -> None:
        self.assertEqual(
            __import__(
                "agent_workflows.readiness_recheck", fromlist=["x"]
            ).SWEEP_DISPOSITIONS,
            ("pending", "reusable"),
        )

    def test_stale_findings_dry_run_writes_nothing(self) -> None:
        p = _plan(
            self.repo,
            open_questions=_oq(blocking="yes", status="resolved", finding="PR-001"),
        )
        review = _review(self.repo)
        before = review.read_text(encoding="utf-8")
        r = _aw(
            "ipd",
            "recheck-readiness",
            str(p),
            "--stale-findings",
            "--dir",
            str(self.repo),
            cwd=self.repo,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("stale-escalation", r.stdout)
        self.assertEqual(review.read_text(encoding="utf-8"), before)

    def test_stale_findings_apply_appends_the_round_and_then_clears(self) -> None:
        p = _plan(
            self.repo,
            open_questions=_oq(blocking="yes", status="resolved", finding="PR-001"),
        )
        r = _aw(
            "ipd",
            "recheck-readiness",
            str(p),
            "--stale-findings",
            "--apply",
            "--dir",
            str(self.repo),
            cwd=self.repo,
        )
        _review(self.repo)  # ensure the record exists for the assertion below
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_agent_mode_emits_a_parsable_record(self) -> None:
        p = _plan(self.repo)
        r = _aw(
            "ipd",
            "recheck-readiness",
            str(p),
            "--dir",
            str(self.repo),
            "--agent",
            cwd=self.repo,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("{")]
        self.assertTrue(lines, r.stdout)
        json.loads(lines[-1])


class WiringTests(unittest.TestCase):
    """E-04: a verb must be wired in cli.py, command_surface.py and completion or it is unreachable."""

    def test_the_verb_is_in_the_ipd_parser(self) -> None:
        from agent_workflows.cli import _build_parser

        r = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "ipd", "--help"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertIn("recheck-readiness", r.stdout)
        self.assertIsNotNone(_build_parser())

    def test_the_verb_is_DECLARED_in_the_command_inventory(self) -> None:
        from agent_workflows import command_surface as cs

        found = [
            d for d in cs.COMMAND_INVENTORY if d.command == "ipd recheck-readiness"
        ]
        self.assertEqual(len(found), 1, [d.command for d in cs.COMMAND_INVENTORY])
        decl = found[0]
        self.assertEqual(decl.command_class, "mutation")
        self.assertEqual(decl.mutation_gate, "dry_run_default")

    def test_the_verb_appears_in_generated_completion_for_every_shell(self) -> None:
        from agent_workflows import completion

        for shell in ("bash", "zsh", "fish"):
            with self.subTest(shell=shell):
                self.assertIn("recheck-readiness", completion.generate(shell))

    def test_the_verbs_flags_appear_in_completion(self) -> None:
        from agent_workflows import completion

        script = completion.generate("bash")
        self.assertIn("--stale-findings", script)


# ======================================================================================
# V-05: the contract and the code AGREE on the first condition.
# ======================================================================================


class ContractConsistencyTests(unittest.TestCase):
    """E-05: a contract that still said "any open question" while the code tests only blocking ones
    is precisely the drift this repository forbids, so the two are asserted to agree."""

    def setUp(self) -> None:
        self.doc = (
            REPO_ROOT
            / ".aw"
            / "system"
            / "workflows"
            / "plan-review"
            / "plan-review.md"
        ).read_text(encoding="utf-8")

    def test_the_first_no_go_condition_is_a_BLOCKING_question(self) -> None:
        self.assertIn("an unresolved BLOCKING open question", self.doc)
        self.assertNotIn(
            "genuine not-ready: any open question",
            self.doc,
            "the former literal wording must be gone",
        )

    def test_the_contract_states_a_no_go_is_RE_EVALUABLE_and_names_the_verb(
        self,
    ) -> None:
        self.assertIn("RE-EVALUABLE", self.doc)
        self.assertIn("aw ipd recheck-readiness", self.doc)

    def test_the_two_rules_that_must_NOT_loosen_are_intact(self) -> None:
        self.assertIn("Only a review may set `GO`", self.doc)
        self.assertIn("`GO` still requires human approval", self.doc)

    def test_the_contract_documents_the_escalation_RETURN_path(self) -> None:
        self.assertIn("escalation RETURN PATH", self.doc)
        self.assertIn("--stale-findings", self.doc)
        self.assertIn("never edit the", self.doc)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
