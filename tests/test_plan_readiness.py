"""Tests for the shared plan-readiness predicate (Set fullauto, Order 01 / plan 97df1z).

Covers, in the order the plan requires:

1. The EXTRACTOR (E-06/V-06). `extract_newest_history_entry` must return the NEWEST record of the
   BOUNDED ``## Workflow history`` section. The shipped driver-local helper
   (``extract_last_history_entry``) was doubly broken: it sliced ``rfind("## Workflow history")`` to
   END OF FILE (so the slice spanned every later section) and then took the LAST bullet, which is
   the OLDEST record because ``status_set.py`` PREPENDS new records under the heading. Both defects
   are pinned here, including a CHARACTERIZATION test of the old behavior so the fix is provably a
   behavior change and not a no-op, and a REAL-PLAN sweep over ``.aw/records/plans/pending/``.
2. The SCHEMA field (E-01/V-01 partial). ``- Readiness:`` is recognized-but-optional.
3. The PREDICATE truth table (E-02/V-02), including the adversarial row (structured field beats
   prose) and the real-plan rows.

Stdlib unittest, no third-party dependencies (house convention).
"""

from __future__ import annotations

import textwrap
import unittest
from pathlib import Path

from agent_workflows import ipd_schema as S
from agent_workflows import plan_readiness as PR
from agent_workflows.attention_contract import HISTORY_RECORD_RE
from tests.support import REPO_ROOT

PENDING_DIR = REPO_ROOT / ".aw" / "records" / "plans" / "pending"
EXECUTED_DIR = REPO_ROOT / ".aw" / "records" / "plans" / "executed"


# A plan shaped like a REAL one: a bounded history section with several records NEWEST-FIRST,
# followed by later sections that also end in `- ` bullets. The `- Cohesion rationale:` trailer is
# verbatim the shape the shipped helper actually returned for 35 of 35 pending plans.
REAL_SHAPED_PLAN = textwrap.dedent(
    """\
    # IPD: A plan shaped like the real ones

    - Date: 2026-08-29
    - Kind: child
    - Concern: x
    - Scope: y
    - Status: approved
    - Author: opencode test
    - Id: shp001

    ## Workflow history
    - 2026-08-30 approved (aw set): status set to approved
    - 2026-08-29 /plan-review (opencode/test): APPROVE WITH REVISIONS APPLIED; PR-001..PR-003.
    - 2026-08-29 reviewed (aw set): status set to reviewed
    - 2026-08-29 to-review (aw set): status set to to-review

    - 2026-08-28 draft (opencode/test): created.

    ## Goal

    Something.

    ## Approval and execution gate

    - Size assessment: standard
    - Cohesion rationale: one concern (a trailing bullet in the FINAL section, which the broken
      rfind-to-EOF reader returned instead of a history record)
    """
)


def _plan(
    *,
    readiness: str | None = None,
    history: str,
    open_questions: str = "",
    status: str = "reviewed",
) -> str:
    """Build a minimal but realistically-shaped plan body for the predicate tests."""
    meta = [
        "- Date: 2026-08-29",
        "- Kind: child",
        "- Concern: x",
        "- Scope: y",
        f"- Status: {status}",
        "- Author: opencode test",
        "- Id: tst001",
    ]
    if readiness is not None:
        meta.insert(5, f"- Readiness: {readiness}")
    parts = [
        "# IPD: Fixture",
        "",
        *meta,
        "",
        "## Workflow history",
        history,
        "",
        "## Goal",
        "",
        "Do the thing.",
        "",
    ]
    if open_questions:
        parts += ["## Open questions", "", open_questions, ""]
    parts += [
        "## Approval and execution gate",
        "",
        "- Size assessment: small",
        "- Cohesion rationale: a trailing bullet in the final section",
        "",
    ]
    return "\n".join(parts)


APPROVE_REVISIONS = (
    "- 2026-08-29 /plan-review (opencode/test): APPROVE WITH REVISIONS APPLIED; PR-001."
)
APPROVE_PLAIN = "- 2026-08-29 /plan-review (opencode/test): APPROVE; no defects."
OPEN_QUESTIONS_VERDICT = (
    "- 2026-08-29 /plan-review (opencode/test): REVIEWED - OPEN QUESTIONS; PR-001."
)
OLD_PROSE = (
    "- 2026-08-29 /plan-review (opencode/test): APPROVE; no defects. "
    "Readiness: GO - PENDING HUMAN APPROVAL."
)

BLOCKING_OPEN_OQ = textwrap.dedent(
    """\
    ### OQ-01: Something undecided

    - Blocking: yes
    - Status: open
    - Owner: none
    - Resolution or deferral rationale: pending"""
)
BLOCKING_RESOLVED_OQ = textwrap.dedent(
    """\
    ### OQ-01: Something decided

    - Blocking: yes
    - Status: resolved
    - Owner: maintainer
    - Resolution or deferral rationale: decided in review"""
)
UNPARSEABLE_OQ = textwrap.dedent(
    """\
    ### OQ-01: A question with no machine-readable fields

    We simply wrote prose here and never declared Blocking or Status, so the block cannot be
    parsed and must be treated as blocking (fail closed)."""
)


class ExtractorTests(unittest.TestCase):
    """E-06 / V-06: the extractor is the PRIMARY bug the plan fixes."""

    def test_returns_newest_bounded_history_record_not_a_later_section_bullet(self):
        entry = PR.extract_newest_history_entry(REAL_SHAPED_PLAN)
        self.assertIsNotNone(entry)
        assert entry is not None  # for type checkers
        # It must be a genuine history RECORD, not the final section's trailing bullet.
        self.assertRegex(entry, r"^- \d{4}-\d{2}-\d{2} ")
        self.assertIsNotNone(HISTORY_RECORD_RE.match(entry))
        self.assertNotIn("Cohesion rationale", entry)
        # And it must be the NEWEST record (history is newest-first), not the oldest.
        self.assertIn("approved (aw set)", entry)
        self.assertNotIn("draft", entry)

    def test_characterizes_the_old_broken_behavior(self):
        """The shipped rfind-to-EOF + last-bullet algorithm returned a NON-history bullet.

        This pins the OLD behavior so the fix is provably a change, not a no-op. It reproduces the
        old algorithm locally (the driver-local copies are deleted by E-03).
        """

        def old_algorithm(text: str) -> str:
            idx = text.rfind("## Workflow history")
            if idx == -1:
                return text
            bullets = [
                line.strip()
                for line in text[idx:].splitlines()
                if line.strip().startswith("- ")
            ]
            return bullets[-1] if bullets else text[idx:]

        old = old_algorithm(REAL_SHAPED_PLAN)
        self.assertIn("Cohesion rationale", old)
        self.assertIsNone(HISTORY_RECORD_RE.match(old))
        # The fixed reader disagrees with it, which is the point.
        self.assertNotEqual(PR.extract_newest_history_entry(REAL_SHAPED_PLAN), old)

    def test_section_is_bounded_at_the_next_h2(self):
        text = textwrap.dedent(
            """\
            # IPD: Bounded

            ## Workflow history
            - 2026-08-29 reviewed (aw set): status set to reviewed

            ## Later section
            - a bullet that is NOT history
            - 2099-12-31 a bullet that even LOOKS like a record
            """
        )
        entry = PR.extract_newest_history_entry(text)
        self.assertEqual(
            entry, "- 2026-08-29 reviewed (aw set): status set to reviewed"
        )

    def test_newest_first_selection(self):
        text = textwrap.dedent(
            """\
            # IPD: Ordering

            ## Workflow history
            - 2026-08-30 approved (aw set): status set to approved
            - 2026-08-28 draft (opencode/test): created.

            ## Goal
            """
        )
        entry = PR.extract_newest_history_entry(text)
        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertIn("approved", entry)
        self.assertNotIn("draft", entry)

    def test_non_record_bullets_inside_history_are_skipped(self):
        text = textwrap.dedent(
            """\
            # IPD: Noise

            ## Workflow history
            - a stray undated bullet
            - 2026-08-30 approved (aw set): status set to approved

            ## Goal
            """
        )
        self.assertEqual(
            PR.extract_newest_history_entry(text),
            "- 2026-08-30 approved (aw set): status set to approved",
        )

    def test_absent_history_section_returns_none(self):
        self.assertIsNone(
            PR.extract_newest_history_entry("# IPD: No history\n\n## Goal\n")
        )

    def test_empty_history_section_returns_none(self):
        text = "# IPD: Empty history\n\n## Workflow history\n\n## Goal\n"
        self.assertIsNone(PR.extract_newest_history_entry(text))

    def test_every_pending_plan_yields_a_real_history_record(self):
        """The REAL-PLAN sweep. Baseline measured pre-fix: 0 of 35 matched."""
        plans = sorted(PENDING_DIR.glob("*.ipd.md"))
        self.assertGreater(len(plans), 0, "no pending plans found to sweep")
        offenders = []
        for p in plans:
            entry = PR.extract_newest_history_entry(p.read_text(encoding="utf-8"))
            if entry is None or not HISTORY_RECORD_RE.match(entry):
                offenders.append((p.name, entry))
        self.assertEqual(offenders, [], f"{len(offenders)}/{len(plans)} plans misread")


class SchemaFieldTests(unittest.TestCase):
    """E-01 / V-01: `Readiness` is recognized but OPTIONAL."""

    BASE = {
        "Date": "2026-08-29",
        "Kind": "child",
        "Concern": "x",
        "Scope": "y",
        "Status": "reviewed",
        "Author": "opencode test",
        "Id": "tst001",
    }

    def test_readiness_is_recognized_but_not_required(self):
        self.assertIn(S.META_READINESS, S.META_RECOGNIZED)
        self.assertNotIn(S.META_READINESS, S.META_REQUIRED)

    def test_readiness_values_are_the_closed_lowercase_enum(self):
        self.assertEqual(
            S.READINESS_VALUES, frozenset(("go", "go-pending-approval", "no-go"))
        )

    def test_recognized_field_does_not_trigger_unknown_field(self):
        lines = [f"- {k}: {v}" for k, v in self.BASE.items()]
        lines.append("- Readiness: go-pending-approval")
        fields, errors = S.parse_metadata_block(lines)
        self.assertEqual(errors, [])
        self.assertEqual(fields["Readiness"], "go-pending-approval")
        self.assertEqual(S.validate_metadata(fields, directory="pending"), [])

    def test_absent_readiness_is_conforming(self):
        lines = [f"- {k}: {v}" for k, v in self.BASE.items()]
        fields, errors = S.parse_metadata_block(lines)
        self.assertEqual(errors, [])
        self.assertNotIn("Readiness", fields)
        self.assertEqual(S.validate_metadata(fields, directory="pending"), [])

    def test_reader_returns_none_for_absent_and_for_unparseable(self):
        self.assertIsNone(S.read_readiness("# IPD: x\n\n- Status: reviewed\n"))
        self.assertIsNone(S.read_readiness("# IPD: x\n\n- Readiness: bogus\n"))
        self.assertEqual(
            S.read_readiness("# IPD: x\n\n- Readiness: go-pending-approval\n"),
            "go-pending-approval",
        )

    def test_reader_is_case_insensitive_on_the_value_only(self):
        self.assertEqual(S.read_readiness("- Readiness: GO\n"), "go")
        self.assertEqual(
            S.read_readiness("- Readiness: NO-GO\n"),
            "no-go",
        )


class PredicateTruthTableTests(unittest.TestCase):
    """E-02 / V-02: the core truth table, field-first with a bounded prose fallback."""

    def _write(self, text: str) -> Path:
        import tempfile

        d = Path(tempfile.mkdtemp())
        p = d / "plan.ipd.md"
        p.write_text(text, encoding="utf-8")
        self.addCleanup(lambda: (p.unlink(missing_ok=True), d.rmdir()))
        return p

    def test_go_pending_approval_is_approvable(self):
        p = self._write(
            _plan(readiness="go-pending-approval", history=OPEN_QUESTIONS_VERDICT)
        )
        self.assertTrue(PR.is_plan_review_approved(p))

    def test_go_is_approvable(self):
        p = self._write(_plan(readiness="go", history=OPEN_QUESTIONS_VERDICT))
        self.assertTrue(PR.is_plan_review_approved(p))

    def test_no_go_is_refused(self):
        p = self._write(_plan(readiness="no-go", history=APPROVE_REVISIONS))
        self.assertFalse(PR.is_plan_review_approved(p))

    def test_unrecognized_readiness_value_fails_closed(self):
        p = self._write(_plan(readiness="bogus", history=APPROVE_REVISIONS))
        self.assertFalse(PR.is_plan_review_approved(p))

    def test_absent_field_with_approve_with_revisions_applied_is_approvable(self):
        p = self._write(_plan(history=APPROVE_REVISIONS))
        self.assertTrue(PR.is_plan_review_approved(p))

    def test_absent_field_with_plain_approve_is_approvable(self):
        p = self._write(_plan(history=APPROVE_PLAIN))
        self.assertTrue(PR.is_plan_review_approved(p))

    def test_absent_field_with_open_questions_verdict_is_refused(self):
        p = self._write(_plan(history=OPEN_QUESTIONS_VERDICT))
        self.assertFalse(PR.is_plan_review_approved(p))

    def test_absent_field_with_approving_verdict_but_blocking_open_question_is_refused(
        self,
    ):
        p = self._write(
            _plan(history=APPROVE_REVISIONS, open_questions=BLOCKING_OPEN_OQ)
        )
        self.assertFalse(PR.is_plan_review_approved(p))

    def test_absent_field_with_approving_verdict_and_resolved_blocking_oq_is_approvable(
        self,
    ):
        p = self._write(
            _plan(history=APPROVE_REVISIONS, open_questions=BLOCKING_RESOLVED_OQ)
        )
        self.assertTrue(PR.is_plan_review_approved(p))

    def test_absent_field_with_unparseable_open_question_fails_closed(self):
        p = self._write(_plan(history=APPROVE_REVISIONS, open_questions=UNPARSEABLE_OQ))
        self.assertFalse(PR.is_plan_review_approved(p))

    def test_history_record_naming_no_go_is_refused_even_with_a_verdict_word(self):
        hist = (
            "- 2026-08-29 /plan-review (opencode/test): APPROVE; readiness NO-GO until "
            "OQ-01 is decided."
        )
        p = self._write(_plan(history=hist))
        self.assertFalse(PR.is_plan_review_approved(p))

    def test_history_record_naming_conditional_go_is_refused(self):
        hist = (
            "- 2026-08-29 /plan-review (opencode/test): APPROVE; readiness CONDITIONAL-GO "
            "pending a decision."
        )
        p = self._write(_plan(history=hist))
        self.assertFalse(PR.is_plan_review_approved(p))

    def test_adversarial_structured_field_beats_old_prose(self):
        """The point of the plan: `Readiness: no-go` wins over the old GO prose phrase."""
        p = self._write(_plan(readiness="no-go", history=OLD_PROSE))
        self.assertFalse(PR.is_plan_review_approved(p))

    def test_structured_go_wins_over_a_negative_prose_record(self):
        hist = "- 2026-08-29 /plan-review (opencode/test): REVIEWED - OPEN QUESTIONS; NO-GO."
        p = self._write(_plan(readiness="go-pending-approval", history=hist))
        self.assertTrue(PR.is_plan_review_approved(p))

    def test_missing_history_and_missing_field_fails_closed(self):
        p = self._write("# IPD: bare\n\n- Status: reviewed\n\n## Goal\n")
        self.assertFalse(PR.is_plan_review_approved(p))

    def test_unreadable_path_fails_closed(self):
        self.assertFalse(PR.is_plan_review_approved(Path("/nonexistent/plan.ipd.md")))


class RealPlanIntegrationTests(unittest.TestCase):
    """V-02's REAL-PLAN rows: a fixture-only suite can pass while the gate stays broken."""

    def _find(self, directory: Path, id6: str) -> Path:
        matches = [p for p in directory.glob("*.ipd.md") if f"-{id6}-" in p.name]
        if not matches:
            self.skipTest(f"plan {id6} not present in {directory.name}/")
        return matches[0]

    def test_g7hljt_carries_the_old_prose_and_is_now_read_correctly(self):
        """g7hljt DOES carry `readiness GO - PENDING HUMAN APPROVAL` in a history record.

        Pre-fix the extractor returned `- Lifecycle move: ...` so the predicate was False for the
        wrong reason. Post-fix the reader reaches the real newest record; the plan is now
        `executed`, and its newest record is the terminal transition, so the fallback correctly
        declines to treat it as an approvable review verdict. What this test pins is that the
        EXTRACTOR now returns a genuine history record for it.
        """
        p = self._find(EXECUTED_DIR, "g7hljt")
        text = p.read_text(encoding="utf-8")
        entry = PR.extract_newest_history_entry(text)
        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertIsNotNone(HISTORY_RECORD_RE.match(entry))
        self.assertNotIn("Lifecycle move", entry)
        # The old prose phrase IS in the file, proving the phrase was never the operative cause.
        self.assertIn("GO - PENDING HUMAN APPROVAL", text)

    def test_predicate_over_every_pending_plan_never_raises_and_respects_no_go(self):
        for p in sorted(PENDING_DIR.glob("*.ipd.md")):
            result = PR.is_plan_review_approved(p)
            self.assertIsInstance(result, bool)
            if S.read_readiness(p.read_text(encoding="utf-8")) == "no-go":
                self.assertFalse(result, f"{p.name}: no-go must never auto-approve")


# --------------------------------------------------------------------------------------------------
# Set apprvguard, Order 01 (plan d7bnhc): the APPROVAL gate.
#
# These are the cases the approval gate ADDS. The cases above belong to the auto-approve gate (plan
# 97df1z) and are deliberately NOT re-asserted here: duplicating a case doubles the maintenance
# surface and invites the two copies to drift apart in opposite directions. Already present and
# therefore not re-added: the section-bounding fix, the newest-first ordering fix, the old-behavior
# characterization, blocking-question refusal and its resolved counterpart, and the `NO-GO` /
# `CONDITIONAL-GO` refusals.
# --------------------------------------------------------------------------------------------------

# A successor plan in the exact shape of the real `6lu3rq`: its newest record is a `to-review` entry
# that NARRATES the RETIRED predecessor's rejection. A naive "newest entry contains REJECT" gate
# refuses this, which would block precisely the plan that correctly replaced the rejected one.
SUCCESSOR_NARRATING_REJECT = (
    "- 2026-08-30 to-review (opencode/test): SUPERSEDES `kaygwo`, which was "
    "REJECT - NEEDS REPLAN twice, inheriting only the residue its own review left standing."
)
# The genuine article: a REVIEW record stating its OWN rejection.
REJECT_VERDICT = (
    "- 2026-08-30 /plan-review pass 2 (opencode/test): REJECT - NEEDS REPLAN reaffirmed; "
    "PR-301..PR-307."
)
# A POSITIVE verdict whose rationale NARRATES a readiness transition, so the record contains the
# word `NO-GO` while saying the opposite. Measured: 6 real records in this repository take this shape.
APPROVE_NARRATING_NO_GO = (
    "- 2026-09-04 reviewed (opencode/test): APPROVE WITH REVISIONS APPLIED; PR-024..PR-030 all "
    "FIXED. The spec gate is satisfied and readiness moves NO-GO -> GO - PENDING HUMAN APPROVAL."
)


class VerdictVocabularyTests(unittest.TestCase):
    """E-02 / V-02: ONE encoding of the two closed vocabularies, with longest-match ordering."""

    def test_verdict_keys_are_exactly_the_documented_four(self):
        self.assertEqual(
            sorted(PR.VERDICTS),
            [
                "APPROVE",
                "APPROVE WITH REVISIONS APPLIED",
                "REJECT - NEEDS REPLAN",
                "REVIEWED - OPEN QUESTIONS",
            ],
        )

    def test_polarities_match_the_workflow_vocabulary(self):
        self.assertEqual(PR.VERDICTS["APPROVE"], PR.POSITIVE)
        self.assertEqual(PR.VERDICTS["APPROVE WITH REVISIONS APPLIED"], PR.POSITIVE)
        self.assertEqual(PR.VERDICTS["REVIEWED - OPEN QUESTIONS"], PR.NEUTRAL)
        self.assertEqual(PR.VERDICTS["REJECT - NEEDS REPLAN"], PR.NEGATIVE)

    def test_longest_match_wins_so_the_approve_prefix_cannot_shadow(self):
        """THE ordering bug this vocabulary is derived (not hand-written) to prevent."""
        token, polarity = PR.classify_verdict("APPROVE WITH REVISIONS APPLIED; PR-001.")
        self.assertEqual(token, "APPROVE WITH REVISIONS APPLIED")
        self.assertEqual(polarity, PR.POSITIVE)

    def test_readiness_vocabulary_including_the_undocumented_token(self):
        self.assertEqual(PR.READINESS_TOKENS["NO-GO"], PR.NEGATIVE)
        # `CONDITIONAL-GO` is in NEITHER documented vocabulary (F-4) but the shipped gate has always
        # treated it as not-ready; kept negative for backward compatibility.
        self.assertEqual(PR.READINESS_TOKENS["CONDITIONAL-GO"], PR.NEGATIVE)
        self.assertEqual(
            PR.READINESS_TOKENS["GO - PENDING HUMAN APPROVAL"], PR.POSITIVE
        )

    def test_spacing_variation_does_not_change_classification(self):
        self.assertEqual(
            PR.classify_verdict("REVIEWED  -  OPEN   QUESTIONS; PR-1.")[0],
            "REVIEWED - OPEN QUESTIONS",
        )

    def test_no_verdict_token_yields_no_classification(self):
        self.assertEqual(
            PR.classify_verdict("plan-review round 1 complete."), (None, None)
        )

    def test_there_is_only_one_encoding_of_the_vocabulary(self):
        """V-02's anti-fork requirement: the replaced private regexes must be GONE, not shadowed."""
        for dead in (
            "_VERDICT_APPROVE_RE",
            "_VERDICT_NEGATIVE_RE",
            "_NEGATIVE_READINESS_RE",
        ):
            self.assertFalse(
                hasattr(PR, dead),
                f"{dead} survived: two independent encodings of one vocabulary",
            )


class ReviewEntryDiscriminatorTests(unittest.TestCase):
    """E-03 / V-03: a verdict may be read ONLY from a record that is itself a review record."""

    def test_review_records_are_recognized_across_the_real_middles(self):
        for mid in (
            "reviewed",
            "/plan-review",
            "/plan-review pass 2",
            "/plan-review RE-REVIEW",
            "reviewed /plan-review",
            "re-reviewed /plan-review",
            "/plan-review-long",
        ):
            entry = f"- 2026-09-04 {mid} (opencode/test): APPROVE."
            self.assertTrue(PR.is_review_history_entry(entry), mid)

    def test_non_review_records_are_not_review_records(self):
        for mid in ("to-review", "draft", "approved", "executed", "superseded"):
            entry = f"- 2026-09-04 {mid} (aw set): status set to {mid}."
            self.assertFalse(PR.is_review_history_entry(entry), mid)

    def test_unparseable_record_is_not_a_review_record(self):
        self.assertFalse(PR.is_review_history_entry("- not a record at all"))

    def test_successor_narrating_a_predecessors_reject_is_not_refused(self):
        """THE central case (F-5). The newest record is `to-review` and merely QUOTES a REJECT."""
        text = _plan(history=SUCCESSOR_NARRATING_REJECT + "\n" + APPROVE_PLAIN)
        polarity, entry = PR.newest_verdict(text)
        self.assertNotEqual(polarity, PR.NEGATIVE)
        # It skipped BACKWARDS past the narration to the real review record.
        self.assertIn("/plan-review", entry)

    def test_newest_review_record_stating_reject_is_negative(self):
        polarity, entry = PR.newest_verdict(_plan(history=REJECT_VERDICT))
        self.assertEqual(polarity, PR.NEGATIVE)
        self.assertIn("REJECT", entry)

    def test_older_reject_superseded_by_a_newer_approve_is_not_refused(self):
        text = _plan(history=APPROVE_REVISIONS + "\n" + REJECT_VERDICT)
        polarity, _ = PR.newest_verdict(text)
        self.assertEqual(polarity, PR.POSITIVE)

    def test_positive_verdict_narrating_a_no_go_readiness_is_not_refused(self):
        """The measured false-refusal risk (D2): 6 real records say APPROVE and also say NO-GO."""
        polarity, _ = PR.newest_verdict(_plan(history=APPROVE_NARRATING_NO_GO))
        self.assertEqual(polarity, PR.POSITIVE)
        # And the STRICTER auto-approve predicate deliberately still declines it, which is the
        # documented asymmetry between the two gates rather than an inconsistency.
        self.assertFalse(PR.history_verdict_approves(APPROVE_NARRATING_NO_GO))

    def test_no_go_alone_with_no_verdict_token_is_negative(self):
        hist = "- 2026-09-04 reviewed (opencode/test): readiness NO-GO; spec is unapproved."
        polarity, _ = PR.newest_verdict(_plan(history=hist))
        self.assertEqual(polarity, PR.NEGATIVE)

    def test_open_questions_verdict_is_neutral_not_negative(self):
        polarity, _ = PR.newest_verdict(_plan(history=OPEN_QUESTIONS_VERDICT))
        self.assertEqual(polarity, PR.NEUTRAL)

    def test_no_history_and_no_review_record_yield_no_verdict(self):
        self.assertEqual(PR.newest_verdict("# IPD: bare\n\n## Goal\n"), (None, ""))
        polarity, entry = PR.newest_verdict(
            _plan(history="- 2026-09-04 draft (aw set): created.")
        )
        self.assertIsNone(polarity)
        self.assertEqual(entry, "")

    def test_verdict_is_read_from_the_message_not_the_actor_or_middle(self):
        """An actor string containing a verdict word must not be mistaken for the verdict."""
        hist = (
            "- 2026-09-04 reviewed (bot-approve-9000): REJECT - NEEDS REPLAN; unsound."
        )
        polarity, _ = PR.newest_verdict(_plan(history=hist))
        self.assertEqual(polarity, PR.NEGATIVE)


class FieldVersusProseOrderingTests(unittest.TestCase):
    """E-03 / V-03: the three-way order must MATCH `is_plan_review_approved` on the same inputs."""

    def _refusals(self, text: str) -> list:
        import tempfile

        d = Path(tempfile.mkdtemp())
        p = d / "plan.ipd.md"
        p.write_text(text, encoding="utf-8")
        self.addCleanup(lambda: (p.unlink(missing_ok=True), d.rmdir()))
        return PR.approval_refusals(d, p, text)

    def test_valid_field_is_authoritative_and_beats_prose(self):
        """`Readiness: no-go` refuses even though the prose verdict says APPROVE."""
        text = _plan(readiness="no-go", history=APPROVE_REVISIONS)
        refusals = self._refusals(text)
        self.assertTrue(refusals)
        self.assertIn("no-go", refusals[0])
        self.assertFalse(PR.is_plan_review_approved(self._write(text)))

    def test_valid_positive_field_beats_a_negative_prose_verdict(self):
        text = _plan(readiness="go-pending-approval", history=REJECT_VERDICT)
        self.assertEqual(self._refusals(text), [])
        self.assertTrue(PR.is_plan_review_approved(self._write(text)))

    def test_absent_field_falls_back_to_prose(self):
        text = _plan(history=REJECT_VERDICT)
        refusals = self._refusals(text)
        self.assertTrue(refusals)
        self.assertIn("newest review record", refusals[0])
        self.assertFalse(PR.is_plan_review_approved(self._write(text)))

    def test_out_of_vocab_field_refuses_outright_with_no_prose_fallback(self):
        """Absence means 'no signal'; a bad value means 'the signal is corrupt'. Not the same."""
        text = _plan(readiness="bogus", history=APPROVE_REVISIONS)
        refusals = self._refusals(text)
        self.assertTrue(refusals)
        self.assertIn("not one of", refusals[0])
        # It did NOT fall back to the approving prose, which would have cleared it.
        self.assertNotIn("newest review record", " ".join(refusals))
        self.assertFalse(PR.is_plan_review_approved(self._write(text)))

    def _write(self, text: str) -> Path:
        import tempfile

        d = Path(tempfile.mkdtemp())
        p = d / "plan.ipd.md"
        p.write_text(text, encoding="utf-8")
        self.addCleanup(lambda: (p.unlink(missing_ok=True), d.rmdir()))
        return p


class ApprovalRefusalsTests(unittest.TestCase):
    """E-04 / V-04: the composed predicate and its deliberate override ASYMMETRY."""

    def _write(self, text: str) -> Path:
        import tempfile

        d = Path(tempfile.mkdtemp())
        p = d / "plan.ipd.md"
        p.write_text(text, encoding="utf-8")
        self.addCleanup(lambda: (p.unlink(missing_ok=True), d.rmdir()))
        return p

    def test_verdict_refusal_survives_allow_open_questions(self):
        """THE asymmetry: the override clears questions, NEVER a verdict."""
        text = _plan(history=REJECT_VERDICT)
        p = self._write(text)
        refusals = PR.approval_refusals(p.parent, p, text, allow_open_questions=True)
        self.assertTrue(refusals)
        self.assertIn("NO override", refusals[0])

    def test_blocking_question_refusal_names_the_question_id(self):
        text = _plan(history=APPROVE_REVISIONS, open_questions=BLOCKING_OPEN_OQ)
        p = self._write(text)
        refusals = PR.approval_refusals(p.parent, p, text)
        self.assertTrue(refusals)
        self.assertIn("OQ-01", refusals[0])

    def test_blocking_question_refusal_is_cleared_by_the_override(self):
        text = _plan(history=APPROVE_REVISIONS, open_questions=BLOCKING_OPEN_OQ)
        p = self._write(text)
        self.assertEqual(
            PR.approval_refusals(p.parent, p, text, allow_open_questions=True), []
        )

    def test_resolved_blocking_question_needs_no_override(self):
        text = _plan(history=APPROVE_REVISIONS, open_questions=BLOCKING_RESOLVED_OQ)
        p = self._write(text)
        self.assertEqual(PR.approval_refusals(p.parent, p, text), [])

    def test_clean_plan_with_no_review_is_permitted(self):
        """Absent review is SILENT, not blocking: gating on absence would block author-then-approve."""
        text = _plan(history="- 2026-09-04 draft (aw set): created.")
        p = self._write(text)
        self.assertEqual(PR.approval_refusals(p.parent, p, text), [])

    def test_both_halves_are_reported_together_not_just_the_first(self):
        text = _plan(history=REJECT_VERDICT, open_questions=BLOCKING_OPEN_OQ)
        p = self._write(text)
        refusals = PR.approval_refusals(p.parent, p, text)
        self.assertEqual(len(refusals), 2)

    def test_unreadable_path_yields_no_refusals(self):
        """A crashing gate is a disabled gate; one that refuses everything is worse than none."""
        self.assertEqual(
            PR.approval_refusals(Path("/nonexistent"), Path("/nonexistent/p.ipd.md")),
            [],
        )

    def test_it_calls_the_shipped_typed_gate_rather_than_forking_the_severity_rule(
        self,
    ):
        """V-04's anti-fork requirement, asserted mechanically rather than by eyeball."""
        import unittest.mock as mock

        text = _plan(history=APPROVE_REVISIONS)
        p = self._write(text)
        with mock.patch(
            "agent_workflows.review_findings.plan_gating_blocks", return_value=()
        ) as spy:
            PR.approval_refusals(p.parent, p, text)
        self.assertEqual(spy.call_count, 1)
        self.assertEqual(spy.call_args[0][1], "tst001")

    def test_a_typed_gating_finding_refuses_and_has_no_override(self):
        import unittest.mock as mock

        from agent_workflows.review_findings import GatingBlock

        block = GatingBlock(
            plan_id6="tst001",
            finding_id="PR-001",
            severity="BLOCKER",
            decision="open",
            kind="finding",
            review_path="r.review.md",
            detail="",
        )
        text = _plan(history=APPROVE_REVISIONS)
        p = self._write(text)
        with mock.patch(
            "agent_workflows.review_findings.plan_gating_blocks", return_value=(block,)
        ):
            refusals = PR.approval_refusals(
                p.parent, p, text, allow_open_questions=True
            )
        self.assertTrue(refusals)
        self.assertIn("PR-001", refusals[0])


class ApprovalGateRealCorpusTests(unittest.TestCase):
    """V-03/V-04's REAL-PLAN rows: a fixture-only suite can pass while the gate misjudges reality."""

    def _find(self, id6: str) -> Path:
        for name in ("pending", "executed", "superseded", "not-executed", "reusable"):
            directory = REPO_ROOT / ".aw" / "records" / "plans" / name
            if not directory.is_dir():
                continue
            for candidate in directory.glob(f"*-{id6}-*.ipd.md"):
                return candidate
        self.skipTest(f"plan {id6} not present in any disposition")

    def test_the_three_item_13_successors_are_not_refused(self):
        """Their `REJECT` mention belongs to a RETIRED predecessor (F-5). Resolved by id6, since
        two of the three have since moved from pending/ to executed/."""
        for id6 in ("6lu3rq", "m73aet", "wlxkoz"):
            path = self._find(id6)
            polarity, _ = PR.newest_verdict(path.read_text(encoding="utf-8"))
            self.assertNotEqual(polarity, PR.NEGATIVE, f"{id6} falsely refused")

    def test_no_pending_plan_is_refused_on_a_verdict_today(self):
        """A gate that refuses live, legitimately-reviewed plans is a lockout, not a safeguard."""
        pending = sorted(PENDING_DIR.glob("*.ipd.md"))
        self.assertGreater(len(pending), 0)
        refused = [
            p.name
            for p in pending
            if PR.newest_verdict(p.read_text(encoding="utf-8"))[0] == PR.NEGATIVE
        ]
        self.assertEqual(refused, [], "pending plans falsely refused on their verdict")

    def test_the_incident_plans_are_refused(self):
        """The five plans a blanket approval swept up on 2026-08-30 must all now refuse.

        They were retired to `superseded/` afterwards, which is where they are resolved from. If this
        ever passes vacuously because they were deleted, the skip below says so rather than lying.
        """
        checked = 0
        for id6 in ("bmh754", "a54m79", "kaygwo", "k7o7el", "7f7782"):
            directory = REPO_ROOT / ".aw" / "records" / "plans" / "superseded"
            matches = list(directory.glob(f"*-{id6}-*.ipd.md"))
            if not matches:
                continue
            polarity, entry = PR.newest_verdict(matches[0].read_text(encoding="utf-8"))
            self.assertEqual(polarity, PR.NEGATIVE, f"{id6} would have been approvable")
            self.assertIn("REJECT", entry)
            checked += 1
        if checked == 0:
            self.skipTest("none of the five incident plans remain in superseded/")
        self.assertGreaterEqual(checked, 1)


class NoWideningTests(unittest.TestCase):
    """The predicate answers ONLY 'is this review-clear'; status gating stays with the caller."""

    def test_predicate_does_not_read_status(self):
        import tempfile

        d = Path(tempfile.mkdtemp())
        p = d / "plan.ipd.md"
        self.addCleanup(lambda: (p.unlink(missing_ok=True), d.rmdir()))
        # A DRAFT plan with a clean readiness value: the predicate may say True, but the drivers
        # must still refuse it because they gate on `Status: reviewed` BEFORE calling in.
        p.write_text(
            _plan(
                readiness="go-pending-approval", history=APPROVE_PLAIN, status="draft"
            ),
            encoding="utf-8",
        )
        self.assertTrue(PR.is_plan_review_approved(p))


if __name__ == "__main__":
    unittest.main()
