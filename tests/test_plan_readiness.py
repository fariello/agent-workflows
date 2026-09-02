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
