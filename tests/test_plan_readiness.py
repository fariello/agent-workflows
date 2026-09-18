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

Most of this file is TABLE-DRIVEN. The subject is a handful of pure predicates over plan text, so
nearly every test was one row of a truth table written out as its own method, asserting a single bool
or polarity. Tabulating them buys two things a per-row test cannot. First, these predicates implement
DECISION ORDERS (field before prose; newest review record before older ones; a valid field before a
corrupt one) and an order is a relationship between rows, so the rows that establish it are adjacent
and share a fixture. Second, the two gates here deliberately DISAGREE about some inputs, and the
disagreement is a designed asymmetry rather than a bug; a column carrying the other gate's answer
makes that visible as a pattern instead of a footnote.

Where two old tests made DIFFERENT KINDS of claim about one input, the row carries a check-mode
column rather than being weakened to one assertion: `newest_verdict` rows state a polarity, a
substring the source record must contain, AND what the stricter auto-approve rule says;
`approval_refusals` rows state an exact refusal count, required and forbidden substrings, AND what
`is_plan_review_approved` answers about identical text.

Tests that are NOT rows carry a one-line docstring saying why. The recurring reasons: the input is
not plan text (a nonexistent path, a line the record grammar cannot match); the subject is the real
plan tree rather than a fixture; the claim is structural (set membership, enum exhaustiveness, a dead
attribute's absence); or the setup is materially different (a locally reimplemented algorithm, a
patched collaborator).
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


BOUNDED_PLAN = textwrap.dedent(
    """\
    # IPD: Bounded

    ## Workflow history
    - 2026-08-29 reviewed (aw set): status set to reviewed

    ## Later section
    - a bullet that is NOT history
    - 2099-12-31 a bullet that even LOOKS like a record
    """
)
ORDERED_PLAN = textwrap.dedent(
    """\
    # IPD: Ordering

    ## Workflow history
    - 2026-08-30 approved (aw set): status set to approved
    - 2026-08-28 draft (opencode/test): created.

    ## Goal
    """
)
NOISY_PLAN = textwrap.dedent(
    """\
    # IPD: Noise

    ## Workflow history
    - a stray undated bullet
    - 2026-08-30 approved (aw set): status set to approved

    ## Goal
    """
)


class ExtractorTests(unittest.TestCase):
    """E-06 / V-06: the extractor is the PRIMARY bug the plan fixes.

    ONE table replaces six tests that were the same shape: hand a plan body to
    ``extract_newest_history_entry`` and compare the one string it returns. The table is better than
    the six for a reason specific to this function, namely that its THREE rules interact and no
    single row can show that. The rules are: bound the section at the next ``## `` heading, take the
    FIRST record because the section is newest-first, and require the ``- YYYY-MM-DD`` record
    grammar so a stray bullet is skipped. Each of the six old tests exercised one rule and was
    satisfied by an implementation that got the other two wrong; the historical bug got TWO of the
    three wrong at once (unbounded slice plus last-instead-of-first), which is precisely the failure
    a single accumulated report makes legible. Rows failing TOGETHER says a shared rule moved: all
    the multi-record rows returning the OLDEST entry is the newest-first rule regressing, while only
    the bounded row failing is the section boundary regressing.

    Every row with a non-None expectation is ALSO checked against ``HISTORY_RECORD_RE``, which is
    the claim the old REAL_SHAPED_PLAN test made separately: whatever comes back must be a genuine
    history record, not a trailing bullet from a later section that merely starts with ``- ``.

    The two None rows (no section, empty section) live in the same table deliberately: an extractor
    that returned the whole text, or the heading itself, on an empty section would satisfy every
    positive row while feeding the gate a string no verdict can be read from.
    """

    #: (case, plan text, the exact record expected or None for "no record at all", why this row
    #: exists)
    EXTRACTIONS = (
        (
            "a plan shaped like the real ones",
            REAL_SHAPED_PLAN,
            "- 2026-08-30 approved (aw set): status set to approved",
            "THE MEASURED BUG, verbatim: the shipped reader sliced rfind(heading) to END OF FILE and "
            "took the LAST bullet, so for 35 of 35 pending plans it returned this fixture's final "
            "`- Cohesion rationale:` trailer instead of a history record. This row fails if either "
            "half of that bug returns",
        ),
        (
            "a later section whose bullets LOOK like records",
            BOUNDED_PLAN,
            "- 2026-08-29 reviewed (aw set): status set to reviewed",
            "BOUNDING: the later section's `- 2099-12-31 ...` bullet matches the record grammar and "
            "is NEWER, so only the section boundary keeps it out. An unbounded reader returns it",
        ),
        (
            "several records under one heading",
            ORDERED_PLAN,
            "- 2026-08-30 approved (aw set): status set to approved",
            "NEWEST-FIRST: `aw set` PREPENDS each record, so the current state is the FIRST one. A "
            "reader taking the last returns the 2026-08-28 draft, i.e. the plan's oldest state",
        ),
        (
            "a stray undated bullet above a real record",
            NOISY_PLAN,
            "- 2026-08-30 approved (aw set): status set to approved",
            "GRAMMAR: the first BULLET is not the first RECORD. A reader taking the first bullet "
            "returns prose no verdict can be read from, which fails closed and looks like a plan "
            "that was never reviewed",
        ),
        (
            "no history section at all",
            "# IPD: No history\n\n## Goal\n",
            None,
            "absence must be reported as None rather than as the whole document, which would let "
            "any verdict word anywhere in the plan be read as its newest review",
        ),
        (
            "a history heading with nothing under it",
            "# IPD: Empty history\n\n## Workflow history\n\n## Goal\n",
            None,
            "an EMPTY section is also None, not the heading text; distinguishing it from the row "
            "above is what proves the boundary logic does not depend on there being a record",
        ),
    )

    def test_every_history_shape_yields_its_newest_bounded_record(self):
        wrong = []
        for case, text, expected, why in self.EXTRACTIONS:
            got = PR.extract_newest_history_entry(text)
            problem = None
            if got != expected:
                problem = f"expected {expected!r}\n      got      {got!r}"
            elif expected is not None and not HISTORY_RECORD_RE.match(got or ""):
                problem = (
                    f"returned {got!r}, which does not match HISTORY_RECORD_RE, so it is not a "
                    "genuine history record even though the string compared equal"
                )
            if problem:
                wrong.append(
                    f"  {case}:\n      {problem}\n    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"extract_newest_history_entry misread {len(wrong)} of {len(self.EXTRACTIONS)} history "
            "shapes. Three rules produce every row (bound the section at the next `## `, take the "
            "FIRST record because `aw set` prepends, require the `- YYYY-MM-DD` grammar), so read "
            "the grouping rather than the rows. If the MULTI-RECORD rows all returned the oldest "
            "entry, the newest-first rule regressed and every gate now reads a stale state. If only "
            "the bounded row failed, the section boundary regressed. FIX: the historical bug got "
            "two rules wrong at once (unbounded slice plus last-instead-of-first) and made the "
            "auto-approve gate return False for all 35 pending plans regardless of what any review "
            f"had written, so several rows failing together is the shape to expect:\n"
            + "\n".join(wrong),
        )

    def test_characterizes_the_old_broken_behavior(self):
        """Kept out of the table: it asserts over a LOCALLY REIMPLEMENTED algorithm, not the shipped one.

        The shipped rfind-to-EOF + last-bullet algorithm returned a NON-history bullet. This pins the
        OLD behavior so the fix is provably a change, not a no-op. It reproduces the old algorithm
        locally (the driver-local copies are deleted by E-03), so its subject is a function defined
        in this test body, which no row of a table over `extract_newest_history_entry` can express.
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

    def test_every_pending_plan_yields_a_real_history_record(self):
        """Kept separate: sweeps every REAL pending plan, so it has no fixture and no rows.

        THE REAL-PLAN SWEEP, and the check that would have caught the original bug: baseline measured
        pre-fix, 0 of 35 plans yielded a history record. A fixture table can be made to pass by a
        reader that happens to handle the shapes someone thought to write down; this cannot.
        """
        plans = sorted(PENDING_DIR.glob("*.ipd.md"))
        self.assertGreater(len(plans), 0, "no pending plans found to sweep")
        offenders = []
        for p in plans:
            entry = PR.extract_newest_history_entry(p.read_text(encoding="utf-8"))
            if entry is None or not HISTORY_RECORD_RE.match(entry):
                offenders.append((p.name, entry))
        self.assertEqual(offenders, [], f"{len(offenders)}/{len(plans)} plans misread")


class SchemaFieldTests(unittest.TestCase):
    """E-01 / V-01: `Readiness` is recognized but OPTIONAL, and its reader folds case.

    TWO tables replace four tests here, split along the line that actually matters: one over the
    METADATA BLOCK (does declaring the field keep a plan conforming?) and one over the READER (what
    does a given spelling resolve to?). They are not merged into one because their subjects differ in
    kind, not in data: the first calls `parse_metadata_block` plus `validate_metadata` over a field
    dict, the second calls `read_readiness` over whole plan text.

    Why each table beats the tests it replaced: both old metadata tests made the SAME three claims
    (no parse error, the field is present-or-absent as expected, no validation error) and differed
    only in whether the line was there, so the presence of the field is a column. Both old reader
    tests were already runs of sequential `assertEqual`s that stopped at the first wrong value.

    The reader table's rows are ADJACENT ON PURPOSE. `read_readiness` collapses ABSENT and
    OUT-OF-VOCAB to the same None, and the callers then distinguish them by a separate
    field-presence probe (absent falls back to prose, corrupt refuses outright). Those two rows
    sitting together is what documents that the collapse is deliberate, so nobody "fixes" the
    out-of-vocab row to return its raw value and silently turns a corrupt signal into a usable one.
    """

    BASE = {
        "Date": "2026-08-29",
        "Kind": "child",
        "Concern": "x",
        "Scope": "y",
        "Status": "reviewed",
        "Author": "opencode test",
        "Id": "tst001",
    }

    #: (case, the `- Readiness:` value to declare or None to omit the line, why this row exists)
    META_BLOCKS = (
        (
            "the field declared with a valid value",
            "go-pending-approval",
            "E-01: the field is RECOGNIZED, so declaring it must not raise the unknown-field error "
            "that would make every reviewed plan nonconforming the day reviews start writing it",
        ),
        (
            "the field omitted entirely",
            None,
            "and it is OPTIONAL, so absence is equally conforming. This row is what stops the field "
            "from becoming required, which would invalidate every plan authored before it existed",
        ),
    )

    def test_declaring_or_omitting_readiness_is_equally_conforming(self):
        wrong = []
        for case, value, why in self.META_BLOCKS:
            lines = [f"- {k}: {v}" for k, v in self.BASE.items()]
            if value is not None:
                lines.append(f"- Readiness: {value}")
            fields, errors = S.parse_metadata_block(lines)
            problems = []
            if errors:
                problems.append(f"parse_metadata_block reported errors {errors!r}")
            if value is None and "Readiness" in fields:
                problems.append(
                    f"no line was written yet the parse produced Readiness={fields['Readiness']!r}"
                )
            if value is not None and fields.get("Readiness") != value:
                problems.append(
                    f"expected the parse to carry Readiness={value!r}, got "
                    f"{fields.get('Readiness')!r}"
                )
            meta_errors = S.validate_metadata(fields, directory="pending")
            if meta_errors:
                problems.append(f"validate_metadata refused it with {meta_errors!r}")
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the Readiness metadata contract is wrong for {len(wrong)} of {len(self.META_BLOCKS)} "
            "blocks. Two membership decisions produce both rows (the field is in META_RECOGNIZED, "
            "and it is NOT in META_REQUIRED), so read which row broke. FIX: the DECLARED row failing "
            "on an unknown-field error means the field left META_RECOGNIZED and every plan a review "
            "touches is now nonconforming; the OMITTED row failing on a validation error means it "
            "became REQUIRED and every plan authored before the field existed is now nonconforming. "
            f"Both are tree-wide breakages, which is why both rows are here:\n"
            + "\n".join(wrong),
        )

    #: (case, plan text handed to `read_readiness`, expected value or None, why this row exists)
    READER_VALUES = (
        (
            "no Readiness line at all",
            "# IPD: x\n\n- Status: reviewed\n",
            None,
            "absence reads as None. The CALLER distinguishes this from the corrupt row below with a "
            "separate field-presence probe, and falls back to the history prose only here",
        ),
        (
            "a value outside the enum",
            "# IPD: x\n\n- Readiness: bogus\n",
            None,
            "an out-of-vocab value ALSO reads as None rather than passing the raw string through. "
            "Deliberately indistinguishable here: the reader's job is to answer with a vocabulary "
            "member or nothing, and returning `bogus` would let a caller compare it against the "
            "approvable set and get a quiet False that looks like a considered refusal",
        ),
        (
            "the canonical lowercase spelling",
            "# IPD: x\n\n- Readiness: go-pending-approval\n",
            "go-pending-approval",
            "the spelling reviews actually write passes through unchanged",
        ),
        (
            "an UPPERCASE go",
            "- Readiness: GO\n",
            "go",
            "CASE IS FOLDED ON THE VALUE: the enum is lowercase, and a review typing the workflow's "
            "own uppercase `GO` must not be read as a corrupt value and refused outright",
        ),
        (
            "an UPPERCASE no-go",
            "- Readiness: NO-GO\n",
            "no-go",
            "the same folding for the REFUSING value, which is the direction that matters: a "
            "`NO-GO` mis-read as corrupt still refuses, but a fold that dropped the hyphen would "
            "make it absent and fall through to prose that may say APPROVE",
        ),
    )

    def test_the_reader_resolves_every_spelling_to_its_enum_member(self):
        wrong = []
        for case, text, expected, why in self.READER_VALUES:
            got = S.read_readiness(text)
            if got != expected:
                wrong.append(
                    f"  {case}:\n    expected {expected!r}\n    got      {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"ipd_schema.read_readiness resolved {len(wrong)} of {len(self.READER_VALUES)} spellings "
            "wrongly. One read-then-normalize-then-validate path produces all of them, so read the "
            "grouping: both UPPERCASE rows failing together is the case fold, while the two None "
            "rows diverging means the reader started distinguishing absent from corrupt, which is a "
            "decision that belongs to the CALLER and not here. FIX: this reader feeds the "
            "auto-approve gate's first branch, so a spelling that reads as None when it should read "
            f"`no-go` sends the gate to the prose fallback instead of refusing:\n"
            + "\n".join(wrong),
        )

    def test_readiness_is_recognized_but_not_required(self):
        """Kept separate: asserts SET MEMBERSHIP over module constants, not a per-input mapping.

        The table above proves the CONSEQUENCE (declaring or omitting the field both lint clean);
        this proves the CAUSE directly, so a refactor that made both tables pass by removing the
        field from the schema entirely is still caught.
        """
        self.assertIn(S.META_READINESS, S.META_RECOGNIZED)
        self.assertNotIn(S.META_READINESS, S.META_REQUIRED)

    def test_readiness_values_are_the_closed_lowercase_enum(self):
        """Kept separate: pins the whole enum as a SET, an exhaustiveness claim no row can make.

        A table row can only show that one value is handled; this shows that no FOURTH value exists.
        """
        self.assertEqual(
            S.READINESS_VALUES, frozenset(("go", "go-pending-approval", "no-go"))
        )


class PredicateTruthTableTests(unittest.TestCase):
    """E-02 / V-02: the core truth table, field-first with a bounded prose fallback.

    ONE table replaces fifteen tests, and this is the merge the file most wanted: every one of the
    fifteen wrote a plan fixture to a temp file and asserted a single bool out of
    `is_plan_review_approved`. What they were collectively describing is a THREE-WAY DECISION ORDER
    (a valid `- Readiness:` field is authoritative; an ABSENT field falls back to the newest history
    record; an OUT-OF-VOCAB field refuses outright with no fallback), and no single test can show an
    order. Adjacent rows can, which is why the field rows and the fallback rows are deliberately
    interleaved by the SAME history prose: `Readiness: no-go` over an approving record and an absent
    field over that identical record must disagree, and that disagreement IS the contract.

    Why the table beats the fifteen: one decision order plus one fallback predicate produces all
    sixteen answers, so a regression moves a whole class of rows at once. All the FIELD rows moving
    together means the field branch broke; all the ABSENT rows moving means the prose fallback did;
    a single row moving means one vocabulary token changed. Fifteen tests report any of those as
    scattered red lines that each say only `False is not true`.

    THE APPROVABLE ROWS ARE IN THE SAME TABLE deliberately, and they are not decoration. This
    predicate FAILS CLOSED by design, so an implementation that returned False unconditionally would
    satisfy every refusing row here; only the approvable rows make the refusals meaningful. The
    failure message says so.

    `status` IS A COLUMN, not a separate test. The predicate answers ONLY "has review cleared this
    plan", and deliberately does NOT read `- Status:`; gating on `Status: reviewed` stays with the
    caller so this module cannot widen what `--full-auto` may approve. That claim used to be its own
    class (NoWideningTests) asserting the same bool over the same fixture with one field changed,
    which is a column by any reading. Its row is the `draft` one below.
    """

    def _write(self, text: str) -> Path:
        import tempfile

        d = Path(tempfile.mkdtemp())
        p = d / "plan.ipd.md"
        p.write_text(text, encoding="utf-8")
        self.addCleanup(lambda: (p.unlink(missing_ok=True), d.rmdir()))
        return p

    #: (case, whole plan text, expected `is_plan_review_approved` answer, why this row exists)
    TRUTH_TABLE = (
        # --- The FIELD branch: a valid value is authoritative and prose is never consulted. ---
        (
            "field `go-pending-approval`, prose says OPEN QUESTIONS",
            _plan(readiness="go-pending-approval", history=OPEN_QUESTIONS_VERDICT),
            True,
            "the normal approvable value, over prose that the FALLBACK would refuse. That "
            "disagreement is the point: it proves the field short-circuits rather than being ANDed "
            "with the prose",
        ),
        (
            "field `go`, prose says OPEN QUESTIONS",
            _plan(readiness="go", history=OPEN_QUESTIONS_VERDICT),
            True,
            "`go` is the SECOND approvable member of a three-value enum, so it needs its own row; a "
            "membership test written against one literal would pass the row above and fail this one",
        ),
        (
            "field `no-go`, prose APPROVES",
            _plan(readiness="no-go", history=APPROVE_REVISIONS),
            False,
            "the mirror image: the field refuses over prose the fallback would ACCEPT. Together with "
            "the two rows above this pins the direction of authority in both directions, which "
            "either row alone leaves ambiguous",
        ),
        (
            "field `no-go`, prose carries the old GO phrase",
            _plan(readiness="no-go", history=OLD_PROSE),
            False,
            "THE ADVERSARIAL ROW the plan was written for: the record literally says `Readiness: GO "
            "- PENDING HUMAN APPROVAL` in prose while the structured field says no-go. A reader that "
            "scanned text rather than branching on the field approves a plan review refused",
        ),
        (
            "field `go-pending-approval`, prose states NO-GO",
            _plan(
                readiness="go-pending-approval",
                history="- 2026-08-29 /plan-review (opencode/test): REVIEWED - OPEN QUESTIONS; NO-GO.",
            ),
            True,
            "the adversarial row inverted, so the field's authority is not quietly one-sided "
            "(refusals honored, clearances second-guessed)",
        ),
        (
            "field present but OUT OF VOCAB, prose APPROVES",
            _plan(readiness="bogus", history=APPROVE_REVISIONS),
            False,
            "A CORRUPT SIGNAL IS NOT AN ABSENT ONE. Absence means nothing was recorded and may fall "
            "back to prose; a bad value means the review TRIED to record a readiness and we cannot "
            "tell what it meant, so falling back could approve a plan whose author meant `no-go`. "
            "The approving prose here is what makes the distinction observable",
        ),
        # --- The ABSENT-field branch: the bounded prose fallback over the newest history record. ---
        (
            "no field, newest record says APPROVE WITH REVISIONS APPLIED",
            _plan(history=APPROVE_REVISIONS),
            True,
            "the back-compat path for a plan reviewed before the field existed. Without this row the "
            "whole fallback could be deleted and every refusing row below would still pass",
        ),
        (
            "no field, newest record says plain APPROVE",
            _plan(history=APPROVE_PLAIN),
            True,
            "both POSITIVE verdicts clear the plan. `APPROVE` is a strict prefix of the longer "
            "verdict, so a first-match-wins scan in the wrong order recognizes one and not the other",
        ),
        (
            "no field, newest record says REVIEWED - OPEN QUESTIONS",
            _plan(history=OPEN_QUESTIONS_VERDICT),
            False,
            "the NEUTRAL verdict is not a clearance. Collapsing the vocabulary to a bool would have "
            "to choose, and choosing `positive` here auto-approves plans whose review explicitly "
            "left questions open",
        ),
        (
            "no field, APPROVE but the record also says NO-GO",
            _plan(
                history=(
                    "- 2026-08-29 /plan-review (opencode/test): APPROVE; readiness NO-GO until "
                    "OQ-01 is decided."
                )
            ),
            False,
            "THE ANY-MENTION RULE, which is specific to this predicate: a negative readiness token "
            "ANYWHERE in the record disqualifies it, even beside an approving verdict. Deliberately "
            "stricter than the approval gate's first-token rule, because a false negative here just "
            "defers to a human",
        ),
        (
            "no field, APPROVE but the record says CONDITIONAL-GO",
            _plan(
                history=(
                    "- 2026-08-29 /plan-review (opencode/test): APPROVE; readiness CONDITIONAL-GO "
                    "pending a decision."
                )
            ),
            False,
            "`CONDITIONAL-GO` is in NEITHER documented vocabulary (F-4) yet the shipped gate has "
            "always treated it as not-ready. Kept negative for back-compat, and pinned here so the "
            "compat behavior is a recorded decision rather than an accident of one regex",
        ),
        (
            "no field, APPROVE, an unresolved BLOCKING question",
            _plan(history=APPROVE_REVISIONS, open_questions=BLOCKING_OPEN_OQ),
            False,
            "the fallback is a CONJUNCTION: an approving verdict is necessary and not sufficient. "
            "Read mechanically (`Blocking: yes` and `Status` not resolved), never as prose judgement",
        ),
        (
            "no field, APPROVE, a RESOLVED blocking question",
            _plan(history=APPROVE_REVISIONS, open_questions=BLOCKING_RESOLVED_OQ),
            True,
            "the other half of that conjunction, and the row that keeps it from degenerating into "
            "`any Blocking: yes block refuses forever`, which would make resolving a question "
            "pointless",
        ),
        (
            "no field, APPROVE, an UNPARSEABLE question block",
            _plan(history=APPROVE_REVISIONS, open_questions=UNPARSEABLE_OQ),
            False,
            "FAIL CLOSED on an unreadable block: a question we cannot parse is not a question we may "
            "assume was answered. The block here declares neither Blocking nor Status",
        ),
        # --- Neither signal present, and the deliberate non-reading of `Status`. ---
        (
            "neither a field nor any history",
            "# IPD: bare\n\n- Status: reviewed\n\n## Goal\n",
            False,
            "absence of evidence is never evidence of approval. This is the row an empty or "
            "unparseable plan lands on, and it must refuse rather than crash",
        ),
        (
            "field `go-pending-approval` on a DRAFT plan",
            _plan(
                readiness="go-pending-approval", history=APPROVE_PLAIN, status="draft"
            ),
            True,
            "STATUS IS NOT THIS PREDICATE'S BUSINESS. It answers only `has review cleared this`, and "
            "the drivers refuse a draft by gating on `Status: reviewed` BEFORE calling in. If this "
            "row ever flips to False the predicate has started reading Status, which silently moves "
            "a safety decision out of the callers that are supposed to own it",
        ),
    )

    def test_the_whole_decision_order_answers_every_plan_shape(self):
        wrong = []
        approvable_broken = 0
        for case, text, expected, why in self.TRUTH_TABLE:
            got = PR.is_plan_review_approved(self._write(text))
            if got is not expected:
                if expected:
                    approvable_broken += 1
                wrong.append(
                    f"  {case}:\n    expected {expected}, got {got}\n"
                    f"    this row exists because: {why}"
                )
        vacuity = ""
        if approvable_broken:
            vacuity = (
                f" NOTE: {approvable_broken} of the failing rows are APPROVABLE rows, and while any "
                "of those is broken every refusing row in this table is VACUOUS: this predicate "
                "fails closed, so an implementation that returned False unconditionally satisfies "
                "all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"is_plan_review_approved answered {len(wrong)} of {len(self.TRUTH_TABLE)} plan shapes "
            f"wrongly.{vacuity} One three-way decision order produces every row (valid field is "
            "authoritative / absent field falls back to the newest history record / out-of-vocab "
            "field refuses outright), so read the grouping. FIELD rows failing together means the "
            "field branch broke; ABSENT rows failing together means the prose fallback did; a "
            "SINGLE row means one vocabulary token moved. FIX: the direction of the error decides "
            "how bad it is. A row that should refuse and now approves is a route from unreviewed to "
            "executing, because this predicate is what `--full-auto` consults before promoting a "
            "plan to approved. A row that should approve and now refuses only defers that plan to a "
            "human.\n" + "\n".join(wrong),
        )

    def test_unreadable_path_fails_closed(self):
        """Kept separate: the input is a PATH THAT DOES NOT EXIST, not plan text.

        Every row of the table writes its fixture to a real temp file, so none of them can express
        "the read itself raises". The claim is that the OSError is swallowed into a refusal rather
        than propagating, since a crashing gate is a disabled gate.
        """
        self.assertFalse(PR.is_plan_review_approved(Path("/nonexistent/plan.ipd.md")))


class RealPlanIntegrationTests(unittest.TestCase):
    """V-02's REAL-PLAN rows: a fixture-only suite can pass while the gate stays broken.

    NOT TABULATED, and deliberately so: neither test has a fixture to vary. One resolves a specific
    plan by id6 and asserts against that plan's actual bytes; the other sweeps every pending plan and
    accumulates offenders, which is already the accumulate-then-assert shape the tables use.
    """

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
    """E-02 / V-02: ONE encoding of the two closed vocabularies, with longest-match ordering.

    TWO tables replace five tests, split by subject: one over the two vocabulary DICTS (which token
    carries which polarity) and one over `classify_verdict` (what a record's message resolves to).
    They stay apart because a dict lookup and a regex scan fail for unrelated reasons, and merging
    them would hide which of the two moved.

    THE MAPPING IS A COLUMN in the first table, which is the whole reason it is one table rather than
    two. `VERDICTS` and `READINESS_TOKENS` are deliberately SEPARATE vocabularies over a SHARED
    polarity set, and the invariant that matters spans both: every token in either must resolve to
    one of the same three labels. A per-dict test cannot state that, and the polarity labels are
    three rather than a bool precisely because `REVIEWED - OPEN QUESTIONS` is neither a clearance nor
    a rejection.

    Why the tables beat the five: both vocabularies are CLOSED SETS consumed by two different gates,
    and the realistic failure is a token's polarity being flipped or the scan order being changed, in
    which case several rows move together in a legible pattern. Three of the five old tests were
    already runs of sequential `assertEqual`s that stopped at their first wrong value, so a flipped
    polarity hid every later one.
    """

    #: (mapping name on the module, token, expected polarity constant, why this row exists)
    POLARITIES = (
        (
            "VERDICTS",
            "APPROVE",
            PR.POSITIVE,
            "the plainest clearance, and the token the longest-match ordering below must not let "
            "shadow its own superstring",
        ),
        (
            "VERDICTS",
            "APPROVE WITH REVISIONS APPLIED",
            PR.POSITIVE,
            "a review that fixed what it found still CLEARS the plan; treating revisions as a "
            "reservation would refuse the most common real approval shape",
        ),
        (
            "VERDICTS",
            "REVIEWED - OPEN QUESTIONS",
            PR.NEUTRAL,
            "NEITHER a clearance nor a rejection, which is why the polarity set is three labels and "
            "not a bool. Collapsing it to positive auto-approves plans with open questions; "
            "collapsing it to negative refuses a human's own approval with no override",
        ),
        (
            "VERDICTS",
            "REJECT - NEEDS REPLAN",
            PR.NEGATIVE,
            "the one verdict that must make `approved` UNREACHABLE. On 2026-08-30 a blanket approval "
            "swept five plans carrying this verdict into the state that licenses execution",
        ),
        (
            "READINESS_TOKENS",
            "GO",
            PR.POSITIVE,
            "the readiness vocabulary is SEPARATE from the verdict one, and this is its bare "
            "clearance token",
        ),
        (
            "READINESS_TOKENS",
            "GO - PENDING HUMAN APPROVAL",
            PR.POSITIVE,
            "the spelling reviews actually write. Note it CONTAINS no negative token, which matters "
            "because the any-mention rule scans for those across a whole record",
        ),
        (
            "READINESS_TOKENS",
            "NO-GO",
            PR.NEGATIVE,
            "the refusing token both gates scan for. A flip here is the single most dangerous edit "
            "in this module: it turns every refusal in the corpus into a clearance",
        ),
        (
            "READINESS_TOKENS",
            "CONDITIONAL-GO",
            PR.NEGATIVE,
            "UNDOCUMENTED (F-4): it appears in NEITHER workflow vocabulary, but the shipped gate has "
            "always treated it as not-ready, so it is kept negative for back-compat. Pinned as a "
            "recorded decision rather than an accident of one regex nobody re-derived",
        ),
    )

    def test_every_vocabulary_token_carries_its_documented_polarity(self):
        wrong = []
        by_mapping = {}
        for mapping, token, expected, why in self.POLARITIES:
            got = getattr(PR, mapping).get(token, "<TOKEN ABSENT FROM THE MAPPING>")
            if got != expected:
                by_mapping[mapping] = by_mapping.get(mapping, 0) + 1
                wrong.append(
                    f"  {mapping}[{token!r}]\n    expected {expected!r}\n    got      {got!r}\n"
                    f"    this row exists because: {why}"
                )
        summary = ", ".join(f"{name} ({n})" for name, n in sorted(by_mapping.items()))
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(self.POLARITIES)} vocabulary tokens carry the wrong polarity, "
            f"across {len(by_mapping)} mapping(s): {summary}. These are two CLOSED SETS over one "
            "shared polarity set, both read by the auto-approve gate and the approval gate, so read "
            "the grouping: failures confined to one mapping are that vocabulary's own edit, while "
            "failures across both mean the POLARITY CONSTANTS themselves were renamed or collapsed. "
            "FIX: a token reported as ABSENT FROM THE MAPPING was deleted or respelled, and every "
            "record in the corpus stating it now classifies as no verdict at all, which reads as "
            "`never reviewed` and fails closed. A token whose polarity FLIPPED from negative to "
            f"positive is the opposite and far worse: refusals in the corpus become clearances.\n"
            + "\n".join(wrong),
        )

    #: (case, the record MESSAGE to classify, expected (token, polarity), why this row exists)
    CLASSIFICATIONS = (
        (
            "the long verdict, stated head-first",
            "APPROVE WITH REVISIONS APPLIED; PR-001.",
            ("APPROVE WITH REVISIONS APPLIED", PR.POSITIVE),
            "THE ORDERING BUG the scan regex is DERIVED rather than hand-written to prevent: "
            "Python's `|` is first-match-wins, so with `APPROVE` listed ahead of its own superstring "
            "this message classifies as plain `APPROVE` and the longer verdict can never be "
            "recognized as itself",
        ),
        (
            "the neutral verdict with mangled spacing",
            "REVIEWED  -  OPEN   QUESTIONS; PR-1.",
            ("REVIEWED - OPEN QUESTIONS", PR.NEUTRAL),
            "SPACING IS NORMALIZED, both the double spaces and the padding around the hyphen. A "
            "reviewer's whitespace must not change a classification, because the alternative is a "
            "gate whose answer depends on a typo no linter flags",
        ),
        (
            "a message stating no verdict token at all",
            "plan-review round 1 complete.",
            (None, None),
            "the NEGATIVE row: `plan-review` appears in the text yet no VERDICT does, so the answer "
            "is (None, None) and not a guess. Without this row a scan that matched the workflow's "
            "own name would pass every positive row above",
        ),
        (
            "a plain APPROVE",
            "APPROVE; no defects.",
            ("APPROVE", PR.POSITIVE),
            "the short verdict must still be recognized as ITSELF once the long one is ordered "
            "ahead of it, which is the other half of the longest-match claim",
        ),
        (
            "a rejection",
            "REJECT - NEEDS REPLAN; unsound.",
            ("REJECT - NEEDS REPLAN", PR.NEGATIVE),
            "the refusing verdict classifies from prose, since this scan is what the approval gate "
            "consults when no structured field is present",
        ),
    )

    def test_classify_verdict_reads_the_leading_token_of_every_message(self):
        wrong = []
        for case, message, expected, why in self.CLASSIFICATIONS:
            got = PR.classify_verdict(message)
            if got != expected:
                wrong.append(
                    f"  {case} ({message!r})\n    expected {expected!r}\n    got      {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"classify_verdict misread {len(wrong)} of {len(self.CLASSIFICATIONS)} messages. One "
            "derived scan regex produces all of them (longest alternative first, internal whitespace "
            "relaxed), so read the grouping. If BOTH `APPROVE` rows now report the short token, the "
            "longest-first ordering was lost and the two verdicts have collapsed into one. If only "
            "the mangled-spacing row failed, the whitespace relaxation did. FIX: the (None, None) "
            "row turning into a real token means the scan started matching something that is not a "
            "verdict, and every history record mentioning review would then carry a verdict it never "
            f"stated.\n" + "\n".join(wrong),
        )

    def test_verdict_keys_are_exactly_the_documented_four(self):
        """Kept separate: an EXHAUSTIVENESS claim over the whole key set, which no row can make.

        A table row shows that one token is handled; this shows that no FIFTH token exists. The
        vocabulary is copied verbatim from the plan-review workflow's verdict list, so an addition
        here means the workflow and this module have drifted.
        """
        self.assertEqual(
            sorted(PR.VERDICTS),
            [
                "APPROVE",
                "APPROVE WITH REVISIONS APPLIED",
                "REJECT - NEEDS REPLAN",
                "REVIEWED - OPEN QUESTIONS",
            ],
        )

    def test_there_is_only_one_encoding_of_the_vocabulary(self):
        """Kept separate: asserts the ABSENCE OF MODULE ATTRIBUTES, not any value mapping.

        V-02's anti-fork requirement: the three private regexes this vocabulary replaced must be GONE,
        not shadowed. Two independent encodings of one vocabulary is how two gates end up giving two
        answers about the same plan, and only a `hasattr` check can state that.
        """
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
    """E-03 / V-03: a verdict may be read ONLY from a record that is itself a review record.

    TWO tables replace eleven tests. The first is over the DISCRIMINATOR
    (`is_review_history_entry`: is this record a review record at all?), the second over the reader
    built on it (`newest_verdict`: which record is consulted, and what does it say?). They stay
    apart because the first answers a bool about ONE LINE and the second walks a whole plan's
    history; a shared table would carry an unused column for every row.

    THE MIDDLE IS A COLUMN in the first table, not a reason for two tables. The old pair split the
    same claim into "these middles ARE review records" and "these middles are NOT", each a loop that
    reported only its first wrong middle. Keeping the accepted and rejected middles ADJACENT is the
    point: the rule is a prefix test on `/plan-review` plus a small word set, and the pair that
    decides whether it is right is `to-review` versus `reviewed`, which differ by three characters
    and must classify OPPOSITELY. Split across two tests, a rule that accepted both looked correct
    in one file and wrong in another.

    THE SECOND TABLE CARRIES A CHECK-MODE COLUMN instead of weakening to one assertion. Two old
    tests made DIFFERENT KINDS of claim about one history: that the polarity is such-and-such, and
    that the record it was read FROM is the expected one (the successor case is only meaningful if
    the reader skipped BACKWARDS past the narration, which the polarity alone does not show). A
    third made a claim about a DIFFERENT function on the same input, namely that the strict
    auto-approve rule disagrees. So each row states the expected polarity, a substring the source
    record must contain, and what `history_verdict_approves` says about the newest record. That last
    column is the documented ASYMMETRY between the two gates, and having it in the table is what
    makes the asymmetry visible as a pattern rather than a footnote on one test: the approval gate
    reads the FIRST verdict token, while the auto-approve gate disqualifies a record on ANY mention
    of a negative readiness token.

    Why the tables beat the eleven: the discriminator is one prefix-plus-word-set rule and the
    reader is one backwards walk over it, so a regression in either moves a whole class of rows. The
    historical failure was total: a parenthesized actor made the record unparseable, so the
    discriminator said False, so the reader returned None, so the approval gate emitted ZERO
    refusals for a plan whose own review said REJECT. That is many rows failing at once for one
    cause, which is exactly what an accumulated report names and eleven red lines do not.
    """

    #: (the record's MIDDLE, whether it is a review record, why this row exists)
    MIDDLES = (
        (
            "reviewed",
            True,
            "the status `aw set` writes when a review finishes, and the most common review-bearing "
            "middle in the corpus",
        ),
        (
            "/plan-review",
            True,
            "the workflow's own name, written by the workflow itself",
        ),
        (
            "/plan-review pass 2",
            True,
            "a SUFFIXED form. Reviewers keep inventing suffixes, so the rule is a PREFIX test rather "
            "than an enumeration; this row is what forces that",
        ),
        (
            "/plan-review RE-REVIEW",
            True,
            "another real suffix, upper-cased, so the match must fold case",
        ),
        (
            "reviewed /plan-review",
            True,
            "TWO tokens in one middle, which is why the middle is split on whitespace rather than "
            "compared whole",
        ),
        (
            "re-reviewed /plan-review",
            True,
            "a hyphenated word form beside the workflow name",
        ),
        (
            "/plan-review-long",
            True,
            "the prefix test accepts a longer word too. Deliberate: this is the cost of not "
            "enumerating suffixes, and it is recorded rather than discovered later",
        ),
        (
            "to-review",
            False,
            "THE PAIR THAT DECIDES THE RULE, against `reviewed` above. A plan AWAITING review has "
            "recorded no verdict, and a rule loose enough to accept it reads a successor plan's "
            "narration of its predecessor's rejection as that successor's own verdict (F-5)",
        ),
        ("draft", False, "an authoring transition states no verdict"),
        (
            "approved",
            False,
            "and neither does an APPROVAL: the approval is the CONSEQUENCE of a review, so treating "
            "it as review evidence would let a plan's own approval attest to itself",
        ),
        ("executed", False, "a terminal transition is not a review"),
        ("superseded", False, "nor is a retirement"),
    )

    def test_only_a_review_bearing_middle_marks_a_record_as_a_review_record(self):
        wrong = []
        for mid, expected, why in self.MIDDLES:
            # A review-shaped message for the accepted middles and a status-set message for the
            # rejected ones, so no row can pass on its MESSAGE rather than its middle.
            entry = (
                f"- 2026-09-04 {mid} (opencode/test): APPROVE."
                if expected
                else f"- 2026-09-04 {mid} (aw set): status set to {mid}."
            )
            got = PR.is_review_history_entry(entry)
            if got is not expected:
                wrong.append(
                    f"  middle {mid!r}: expected is_review_history_entry to be {expected}, got "
                    f"{got}\n    record: {entry!r}\n    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"is_review_history_entry misclassified {len(wrong)} of {len(self.MIDDLES)} middles. One "
            "rule decides all of them (split the middle on whitespace, then accept a word in "
            "`_REVIEW_WORDS` or anything prefixed `/plan-review`), so read the grouping. ALL rows "
            "failing means the record regex stopped matching at all, which is how a formatting "
            "accident once disabled the approval gate entirely. FIX: the two DIRECTIONS are not "
            "equally bad. A review middle read as NOT-review makes the gate blind, so a plan its own "
            "review rejected becomes approvable. A non-review middle read AS review makes the gate "
            "read a narrating record's quoted verdict as that record's own, which refuses exactly "
            f"the successor plans that correctly replaced the rejected ones (F-5).\n"
            + "\n".join(wrong),
        )

    #: (case, the history body, expected polarity, a substring the SOURCE record must contain (or
    #: None to skip that check), what the STRICTER auto-approve rule says about the newest record,
    #: why this row exists)
    VERDICT_READS = (
        (
            "a successor whose newest record NARRATES its predecessor's rejection",
            SUCCESSOR_NARRATING_REJECT + "\n" + APPROVE_PLAIN,
            PR.POSITIVE,
            "/plan-review",
            False,
            "THE CENTRAL CASE (F-5), in the exact shape of the real `6lu3rq`. The newest record is a "
            "`to-review` entry quoting a REJECT, so a naive 'newest entry contains REJECT' gate "
            "refuses precisely the plan that correctly replaced the rejected one. The SOURCE column "
            "is what proves the reader skipped BACKWARDS to the real review record rather than "
            "merely failing to find the word",
        ),
        (
            "a review record stating its OWN rejection",
            REJECT_VERDICT,
            PR.NEGATIVE,
            "REJECT",
            False,
            "the genuine article, and the row that keeps the F-5 fix from degenerating into 'never "
            "refuse anything'. The source column pins that the refusal quotes the record it read",
        ),
        (
            "an older REJECT superseded by a newer APPROVE",
            APPROVE_REVISIONS + "\n" + REJECT_VERDICT,
            PR.POSITIVE,
            "APPROVE",
            True,
            "ONLY THE NEWEST review record is consulted. A re-review that cleared a previously "
            "rejected plan must not be outvoted by its own history, or a plan could never recover "
            "from one rejection. Note this is the one row where BOTH gates agree",
        ),
        (
            "a positive verdict NARRATING a readiness transition through NO-GO",
            APPROVE_NARRATING_NO_GO,
            PR.POSITIVE,
            "APPROVE",
            False,
            "THE MEASURED ASYMMETRY (D2): 6 real records say APPROVE and also contain `NO-GO` while "
            "narrating `NO-GO -> GO`. The approval gate reads the FIRST verdict token and clears "
            "them, because ITS false positive is an unoverridable lockout; the auto-approve rule "
            "disqualifies on ANY mention and declines them, because ITS false negative costs one "
            "deferral to a human. Both columns of this row are deliberate, and a change that made "
            "them agree would be a change to which risk we accept",
        ),
        (
            "a review record with a readiness token and NO verdict token",
            "- 2026-09-04 reviewed (opencode/test): readiness NO-GO; spec is unapproved.",
            PR.NEGATIVE,
            "NO-GO",
            False,
            "a negative READINESS decides only when no verdict competes with it, which is exactly "
            "why it is unambiguous here and ignored in the row above",
        ),
        (
            "the NEUTRAL verdict",
            OPEN_QUESTIONS_VERDICT,
            PR.NEUTRAL,
            "OPEN QUESTIONS",
            False,
            "neutral is NOT negative: the approval gate must not refuse a human approving over "
            "questions it named, which is what the overridable open-question half is for",
        ),
        (
            "a history with only a non-review record",
            "- 2026-09-04 draft (aw set): created.",
            None,
            "",
            False,
            "no review record at all yields no verdict AND an EMPTY source string, so a caller "
            "quoting the evidence in its refusal has nothing to quote and emits no refusal. The "
            "empty-string expectation is the claim here",
        ),
        (
            "a review record whose ACTOR contains a verdict word",
            "- 2026-09-04 reviewed (bot-approve-9000): REJECT - NEEDS REPLAN; unsound.",
            PR.NEGATIVE,
            "REJECT",
            False,
            "the verdict is read from the MESSAGE only. An actor named `bot-approve-9000` must not "
            "contribute the word APPROVE, or the gate's answer depends on who ran the review",
        ),
    )

    def test_the_newest_review_records_verdict_is_read_from_every_history_shape(self):
        wrong = []
        disagreements = 0
        for case, history, polarity, source_needle, strict, why in self.VERDICT_READS:
            text = _plan(history=history)
            got_polarity, got_entry = PR.newest_verdict(text)
            got_strict = PR.history_verdict_approves(
                PR.extract_newest_history_entry(text)
            )
            problems = []
            if got_polarity != polarity:
                problems.append(f"polarity expected {polarity!r}, got {got_polarity!r}")
            if source_needle is not None and source_needle not in got_entry:
                problems.append(
                    f"the record it read from should contain {source_needle!r}; it read "
                    f"{got_entry!r}"
                )
            if got_strict is not strict:
                disagreements += 1
                problems.append(
                    f"the STRICTER auto-approve rule (history_verdict_approves) should say "
                    f"{strict}, and said {got_strict}"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if disagreements:
            note = (
                f" {disagreements} of the failures are in the STRICT column, which is the "
                "deliberate disagreement between the two gates rather than either one's own "
                "answer: changing it changes WHICH risk we accept (an unoverridable lockout versus "
                "one deferral to a human), so it is a policy edit and not a bug fix."
            )
        self.assertEqual(
            wrong,
            [],
            f"newest_verdict misread {len(wrong)} of {len(self.VERDICT_READS)} history shapes."
            f"{note} One backwards walk produces every row (skip records that are not review "
            "records, then classify the FIRST verdict token of the first one that is, falling back "
            "to a negative readiness token only when no verdict is stated), so read the grouping. "
            "ALL rows losing their polarity means the discriminator or the record regex broke and "
            "the gate is now blind. FIX: a row that should be POSITIVE reading NEGATIVE is an "
            "unoverridable lockout on a legitimately reviewed plan, which is the failure the F-5 "
            "row exists to prevent; a row that should be NEGATIVE reading anything else licenses "
            f"execution of a plan its own review rejected.\n" + "\n".join(wrong),
        )

    def test_unparseable_record_is_not_a_review_record(self):
        """Kept separate: the input is not a RECORD, so it has no middle for the table's column.

        Every row above supplies a well-formed `- <date> <middle> (<actor>): <msg>` line and varies
        the middle. This asserts the safe answer for a line the record regex cannot match at all,
        which is False: an unreadable record states no verdict, so no refusal is derived from it.
        """
        self.assertFalse(PR.is_review_history_entry("- not a record at all"))

    def test_a_plan_with_no_history_section_yields_no_verdict(self):
        """Kept separate: the input is a plan with NO `## Workflow history` section at all.

        The table's rows are all built by `_plan(history=...)`, which always emits the section, so
        none of them can exercise the walk finding nothing to walk. The empty SOURCE string matters
        as much as the None polarity: a caller quotes it into its refusal message.
        """
        self.assertEqual(PR.newest_verdict("# IPD: bare\n\n## Goal\n"), (None, ""))


class ApprovalRefusalsTests(unittest.TestCase):
    """E-03/E-04 / V-03/V-04: the composed approval gate, its decision order, and its override ASYMMETRY.

    ONE table replaces ten tests spread over two classes (`FieldVersusProseOrderingTests` and the
    rest of this one). Every one of them wrote a plan fixture, called `approval_refusals` on it, and
    asserted one thing about the returned list. Splitting them by class was arbitrary: both halves
    were describing the SAME function, and the split actively hid the property that matters most,
    namely that the field-versus-prose order here MATCHES the one `is_plan_review_approved`
    implements. Two gates disagreeing about the same plan is worse than either rule alone.

    `allow_open_questions` IS A COLUMN, not a second table, and this is the clearest case for that in
    the file. THE OVERRIDE ASYMMETRY IS THE DESIGN'S CORE: the flag clears open-question refusals and
    NEVER a verdict, because no flag should be able to turn "do not build this" into "executable". An
    asymmetry is a RELATIONSHIP between two runs over the same input, so it cannot be stated by
    either run alone. The table puts those runs on ADJACENT ROWS: the REJECT fixture appears with the
    flag off and on and must refuse BOTH times, while the blocking-question fixture appears with the
    flag off and on and must refuse only once.

    EACH ROW CARRIES THREE KINDS OF CLAIM rather than being weakened to one assertion, because the
    old tests made three kinds and dropping any of them would lose substance: the exact NUMBER of
    refusals (the both-halves row is only meaningful as a count), SUBSTRINGS the message must and must
    not contain (a refusal that does not name its cause is the failure this area exists to remove,
    and the out-of-vocab row's whole point is the ABSENCE of the prose-fallback wording), and what
    `is_plan_review_approved` says about the identical text (the cross-gate agreement).

    Why the table beats the ten: one three-way decision order plus one override rule produces every
    row. A regression in the order moves the field rows together; a regression in the override moves
    the flag-on rows together; a change to a message moves one row's needles while its count stays
    right. Ten tests report any of these as scattered `[] is not true` lines.
    """

    def _write(self, text: str) -> Path:
        import tempfile

        d = Path(tempfile.mkdtemp())
        p = d / "plan.ipd.md"
        p.write_text(text, encoding="utf-8")
        self.addCleanup(lambda: (p.unlink(missing_ok=True), d.rmdir()))
        return p

    #: (case, plan text, allow_open_questions, expected refusal COUNT, substrings that must appear
    #: somewhere in the refusals, substrings that must NOT appear, what `is_plan_review_approved`
    #: must say about the same text (None to not cross-check), why this row exists)
    REFUSALS = (
        # --- The field-versus-prose decision order, which must match the auto-approve predicate. ---
        (
            "field `no-go` over APPROVING prose",
            _plan(readiness="no-go", history=APPROVE_REVISIONS),
            False,
            1,
            ("no-go", "NO override"),
            ("newest review record",),
            False,
            "A VALID FIELD IS AUTHORITATIVE and the prose is never consulted, which the FORBIDDEN "
            "substring is what proves: if the prose-fallback wording appears, the gate read both and "
            "happened to agree, so the next plan where they disagree decides by accident",
        ),
        (
            "field `go-pending-approval` over a REJECT verdict",
            _plan(readiness="go-pending-approval", history=REJECT_VERDICT),
            False,
            0,
            (),
            (),
            True,
            "the field's authority runs in BOTH directions, so a plan a re-review cleared is not "
            "held back by the rejection still recorded in its history",
        ),
        (
            "NO field, a REJECT verdict in the newest review record",
            _plan(history=REJECT_VERDICT),
            False,
            1,
            ("newest review record", "NO override"),
            (),
            False,
            "an ABSENT field falls back to prose. THE INCIDENT THIS GATE EXISTS FOR: on 2026-08-30 a "
            "blanket approval swept five plans whose own newest review said REJECT into `approved`, "
            "the state that licenses execution, because the setter read STATUS ALONE",
        ),
        (
            "the SAME REJECT verdict, with --allow-open-questions",
            _plan(history=REJECT_VERDICT),
            True,
            1,
            ("NO override",),
            (),
            None,
            "THE ASYMMETRY, stated as the pair of this row and the one above it: the override does "
            "NOT clear a verdict, and the message says so in the same breath. A flag that could "
            "would make the whole gate advisory",
        ),
        (
            "field PRESENT but out of vocab, over approving prose",
            _plan(readiness="bogus", history=APPROVE_REVISIONS),
            False,
            1,
            ("not one of",),
            ("newest review record",),
            False,
            "A CORRUPT SIGNAL IS NOT AN ABSENT ONE, and the forbidden substring is the entire claim: "
            "it must NOT fall back to the approving prose, which would have cleared the plan. "
            "Absence means no signal was recorded; a bad value means the review tried to record one "
            "and we cannot tell what it meant",
        ),
        # --- The open-question half, the ONLY overridable one. ---
        (
            "an unresolved BLOCKING question under an approving verdict",
            _plan(history=APPROVE_REVISIONS, open_questions=BLOCKING_OPEN_OQ),
            False,
            1,
            ("OQ-01", "--allow-open-questions"),
            (),
            False,
            "the refusal NAMES THE QUESTION ID and names its own override. A refusal that says only "
            "`a blocking question` sends a human hunting through the plan, which is the failure mode "
            "this whole area exists to remove",
        ),
        (
            "the SAME blocking question, with --allow-open-questions",
            _plan(history=APPROVE_REVISIONS, open_questions=BLOCKING_OPEN_OQ),
            True,
            0,
            (),
            (),
            None,
            "the other half of the asymmetry: THIS refusal IS cleared by the flag. Without this row "
            "the override could be a no-op and every flag-on row would still pass",
        ),
        (
            "a RESOLVED blocking question under an approving verdict",
            _plan(history=APPROVE_REVISIONS, open_questions=BLOCKING_RESOLVED_OQ),
            False,
            0,
            (),
            (),
            True,
            "resolving a question needs NO override, or resolving one would be pointless and every "
            "plan that ever had a blocking question would need the flag forever",
        ),
        (
            "an UNPARSEABLE question block under an approving verdict",
            _plan(history=APPROVE_REVISIONS, open_questions=UNPARSEABLE_OQ),
            False,
            1,
            ("OQ-01",),
            (),
            False,
            "FAIL CLOSED on a block whose Blocking/Status cannot be read: a question we cannot parse "
            "is not one we may assume was answered. Safe precisely BECAUSE this half is overridable, "
            "so the override is where an unreadable question gets a human's attention",
        ),
        # --- Composition: absence is silent, and both halves report together. ---
        (
            "a plan with NO review record at all",
            _plan(history="- 2026-09-04 draft (aw set): created."),
            False,
            0,
            (),
            (),
            False,
            "ABSENT REVIEW IS SILENT, NOT BLOCKING, or the author-then-approve flow every small plan "
            "uses would be impossible. Note the predicate column DISAGREES on this row, which is the "
            "documented difference between the two gates rather than an inconsistency: automation "
            "must refuse on no evidence, while a HUMAN approving a plan nobody reviewed is allowed",
        ),
        (
            "BOTH a REJECT verdict and a blocking question",
            _plan(history=REJECT_VERDICT, open_questions=BLOCKING_OPEN_OQ),
            False,
            2,
            ("newest review record", "OQ-01"),
            (),
            False,
            "EVERY reason is reported, not just the first. A gate that stops at one refusal makes a "
            "human fix it, re-run, and discover the next, which is how a two-problem plan takes "
            "three rounds instead of one",
        ),
    )

    def test_every_plan_shape_yields_exactly_its_refusals(self):
        wrong = []
        override_rows_broken = 0
        predicate_disagreements = 0
        for (
            case,
            text,
            allow,
            count,
            needles,
            forbidden,
            predicate,
            why,
        ) in self.REFUSALS:
            path = self._write(text)
            refusals = PR.approval_refusals(
                path.parent, path, text, allow_open_questions=allow
            )
            joined = " ".join(refusals)
            problems = []
            if len(refusals) != count:
                problems.append(
                    f"expected {count} refusal(s), got {len(refusals)}: {refusals!r}"
                )
            missing = [n for n in needles if n not in joined]
            if missing:
                problems.append(f"the refusals never mention {missing!r}: {refusals!r}")
            leaked = [f for f in forbidden if f in joined]
            if leaked:
                problems.append(
                    f"the refusals mention {leaked!r}, which this row requires them NOT to: "
                    f"{refusals!r}"
                )
            if predicate is not None:
                got = PR.is_plan_review_approved(path)
                if got is not predicate:
                    predicate_disagreements += 1
                    problems.append(
                        f"is_plan_review_approved should say {predicate} about the same text, and "
                        f"said {got}, so the two gates now disagree about this plan"
                    )
            if problems:
                if allow:
                    override_rows_broken += 1
                wrong.append(
                    f"  {case} (allow_open_questions={allow}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        notes = []
        if override_rows_broken:
            notes.append(
                f"{override_rows_broken} of the failing rows have the OVERRIDE ON, so suspect the "
                "asymmetry rather than the individual checks: the flag must clear open-question "
                "refusals and never a verdict"
            )
        if predicate_disagreements:
            notes.append(
                f"{predicate_disagreements} row(s) failed on the CROSS-GATE column, meaning this "
                "gate and `is_plan_review_approved` now answer differently about identical text, "
                "which is worse than either rule being wrong on its own"
            )
        note = (" " + "; ".join(notes) + ".") if notes else ""
        self.assertEqual(
            wrong,
            [],
            f"approval_refusals was wrong for {len(wrong)} of {len(self.REFUSALS)} plan shapes."
            f"{note} One three-way decision order plus one override rule produces every row, so read "
            "the grouping: FIELD rows failing together means the order changed, flag-on rows failing "
            "together means the override did, and a row whose COUNT is right while its needles are "
            "wrong is only a message edit. FIX: the direction matters. A row that should refuse and "
            "now returns [] makes `approved` reachable for a plan its own review rejected, which is "
            "the exact 2026-08-30 incident this gate was built after. A row that should return [] "
            "and now refuses is a LOCKOUT no flag can clear, since the verdict half has no override "
            f"by design.\n" + "\n".join(wrong),
        )

    def test_unreadable_path_yields_no_refusals(self):
        """Kept separate: the input is a PATH THAT DOES NOT EXIST, not plan text.

        Every table row writes its fixture to a real temp file and passes the text in, so no row can
        exercise the read itself raising. A crashing gate is a disabled gate; one that refuses
        everything is worse than none.
        """
        self.assertEqual(
            PR.approval_refusals(Path("/nonexistent"), Path("/nonexistent/p.ipd.md")),
            [],
        )

    def test_it_calls_the_shipped_typed_gate_rather_than_forking_the_severity_rule(
        self,
    ):
        """Kept separate: PATCHES a collaborator and asserts on the CALL, not on the return value.

        V-04's anti-fork requirement, asserted mechanically rather than by eyeball: the one severity
        comparison must be reused, not reimplemented. The subject is `mock` call bookkeeping (called
        once, with this plan's id6), which is a different kind of claim from any row's refusal list.
        """
        import unittest.mock as mock

        text = _plan(history=APPROVE_REVISIONS)
        p = self._write(text)
        with mock.patch(
            "agent_workflows.review_findings.subject_gating_blocks", return_value=()
        ) as spy:
            PR.approval_refusals(p.parent, p, text)
        self.assertEqual(spy.call_count, 1)
        self.assertEqual(spy.call_args[0][1], "tst001")

    def test_a_typed_gating_finding_refuses_and_has_no_override(self):
        """Kept separate: needs materially different setup, a PATCHED review tree.

        The third refusal source is a typed `.review.md` artifact, which no plan fixture carries: the
        block has to be injected by patching `subject_gating_blocks`. A row would need a whole extra
        column of mock machinery that every other row leaves unused.
        """
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
            "agent_workflows.review_findings.subject_gating_blocks",
            return_value=(block,),
        ):
            refusals = PR.approval_refusals(
                p.parent, p, text, allow_open_questions=True
            )
        self.assertTrue(refusals)
        self.assertIn("PR-001", refusals[0])


class ApprovalGateRealCorpusTests(unittest.TestCase):
    """V-03/V-04's REAL-PLAN rows: a fixture-only suite can pass while the gate misjudges reality.

    NOT TABULATED: every test here resolves real plans by id6 and each carries its own SKIP condition
    for a different precondition (a plan having moved disposition, or the five incident plans having
    been deleted). Merging them would make one row's skip silence the others, which is exactly the
    vacuous pass these tests are written to avoid.
    """

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


class AParenthesizedActorDoesNotDisableTheApprovalGate(unittest.TestCase):
    """Plan fn2l1u E-08a / V-08: THE GATE USED TO FAIL OPEN ON A FORMATTING ACCIDENT.

    `_HISTORY_RECORD_PARTS_RE` carried the bound `(?P<actor>[^)]*)`, which stops at the FIRST `)`.
    A review record whose ACTOR contained parentheses - the shape 274 of 638 tracked plans carry in
    the `- Author:` field agents copy into `--actor` - therefore did not match at all, so
    `is_review_history_entry` returned False, so `newest_verdict` returned None, so
    `approval_refusals` emitted ZERO refusals for a plan whose own newest review said
    `REJECT - NEEDS REPLAN`.

    Reproduced end to end through the real CLI before the fix: `aw set approved <id6> --by-human`
    EXITED 0 and wrote `- Status: approved` with a parenthesized actor, while the identical command
    with a slash-form actor EXITED 1 and refused with "This refusal has NO override." That is
    precisely the failure the approval gate was built after, reachable by a typo.
    """

    PAREN_REJECT = (
        "- 2026-09-08 reviewed (opencode (its_direct/some-model)): "
        "/plan-review: REJECT - NEEDS REPLAN; unsound."
    )
    SLASH_REJECT = (
        "- 2026-09-08 reviewed (opencode/its_direct/some-model): "
        "/plan-review: REJECT - NEEDS REPLAN; unsound."
    )
    # A real corpus middle (`/plan-review pass 2`) beside a parenthesized actor: the `mid` capture
    # widened in the same edit, so both lazy captures can fight over the same `(`.
    MULTI_WORD_MIDDLE = (
        "- 2026-08-30 /plan-review pass 2 (opencode (some-model)): "
        "REJECT - NEEDS REPLAN reaffirmed."
    )
    # THE HAZARD that decides lazy-versus-greedy: a `):` inside the MESSAGE.
    PAREN_IN_MESSAGE = "- 2026-09-08 reviewed (opencode/model): fixed foo(bar): APPROVE"
    # A narration, not a verdict: it parses fully and must still not be a review record (F-5).
    NARRATING_PAREN = (
        "- 2026-09-08 to-review (opencode (some-model)): supersedes a plan whose "
        "review said REJECT - NEEDS REPLAN."
    )

    def _refusals(self, text: str) -> list:
        import tempfile

        d = Path(tempfile.mkdtemp())
        p = d / "plan.ipd.md"
        p.write_text(text, encoding="utf-8")
        self.addCleanup(lambda: (p.unlink(missing_ok=True), d.rmdir()))
        return PR.approval_refusals(d, p, text)

    #: (case, the history RECORD, expected (mid, actor, msg) captures, why this row exists)
    CAPTURES = (
        (
            "an actor containing parentheses",
            PAREN_REJECT,
            (
                "reviewed",
                "opencode (its_direct/some-model)",
                "/plan-review: REJECT - NEEDS REPLAN; unsound.",
            ),
            "THE BUG: the old `(?P<actor>[^)]*)` stopped at the FIRST `)`, so this record did not "
            "match AT ALL. The actor must come back WHOLE, inner parentheses included",
        ),
        (
            "the slash-form actor, unchanged",
            SLASH_REJECT,
            (
                "reviewed",
                "opencode/its_direct/some-model",
                "/plan-review: REJECT - NEEDS REPLAN; unsound.",
            ),
            "the widening is strictly ADDITIVE: measured over all 3073 tracked records, ZERO "
            "previously-parsing records had any capture change. This row is that claim, and without "
            "it the fix could be a regression dressed as a widening",
        ),
        (
            "a MULTI-WORD middle beside a parenthesized actor",
            MULTI_WORD_MIDDLE,
            (
                "/plan-review pass 2",
                "opencode (some-model)",
                "REJECT - NEEDS REPLAN reaffirmed.",
            ),
            "the `mid` capture widened from `[^(]*?` to `.*?` in the same edit, so BOTH captures are "
            "lazy now and can fight over the same `(`. This row is where that fight would show",
        ),
        (
            "a MESSAGE containing `):`",
            PAREN_IN_MESSAGE,
            ("reviewed", "opencode/model", "fixed foo(bar): APPROVE"),
            "WHY THE CAPTURE IS LAZY AND NOT GREEDY. A greedy `(?P<actor>.*)` anchors on the LAST "
            "`):` and captures actor `opencode/model): fixed foo(bar`, corrupting a record that "
            "parses correctly today. This row fails under that alternative, which is what makes the "
            "choice evidenced rather than asserted",
        ),
        (
            "a NARRATING record with a parenthesized actor",
            NARRATING_PAREN,
            (
                "to-review",
                "opencode (some-model)",
                "supersedes a plan whose review said REJECT - NEEDS REPLAN.",
            ),
            "the record PARSES (all three captures are right) and is still NOT a review record, "
            "which is the pair of claims that keeps the widening from turning a narration into a "
            "verdict-bearing record (d7bnhc F-5). The gate table below asserts the second half",
        ),
    )

    def test_every_actor_spelling_parses_into_its_three_captures(self):
        """One table over `_HISTORY_RECORD_PARTS_RE`, replacing two tests and a third's precondition.

        THE ACTOR SPELLING IS A COLUMN, which is the reason this is one table: the parenthesized and
        slash forms must produce IDENTICAL `mid` and `msg` captures, and "identical" is a relationship
        between two rows that neither row alone can state. The old tests asserted the two forms in
        two places, so a change that shifted the boundary for one and not the other read as one
        unrelated failure.

        Why the table beats the tests it replaces: one regex with two LAZY captures produces every
        row, and the lazy-versus-greedy choice trades the rows off against each other. Greedy fixes
        nothing and breaks the `):`-in-message row; a bound like `[^)]*` fixes that row and breaks
        both parenthesized rows. Seeing which rows move together is therefore the whole diagnosis.
        """
        wrong = []
        for case, record, expected, why in self.CAPTURES:
            match = PR._HISTORY_RECORD_PARTS_RE.match(record)
            if match is None:
                wrong.append(
                    f"  {case}: DID NOT MATCH AT ALL, so every capture is unavailable\n"
                    f"    record: {record!r}\n    this row exists because: {why}"
                )
                continue
            got = (match.group("mid"), match.group("actor"), match.group("msg"))
            if got != expected:
                labels = ("mid", "actor", "msg")
                diffs = [
                    f"      {label}: expected {e!r}, got {g!r}"
                    for label, e, g in zip(labels, expected, got)
                    if e != g
                ]
                wrong.append(
                    f"  {case}:\n"
                    + "\n".join(diffs)
                    + f"\n    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"_HISTORY_RECORD_PARTS_RE mis-split {len(wrong)} of {len(self.CAPTURES)} records. One "
            "regex with two LAZY captures produces every row, and the rows trade off against each "
            "other, so read WHICH moved. If the PARENTHESIZED rows stopped matching, someone "
            "re-bounded the actor to `[^)]*` and the gate has failed OPEN again (a record it cannot "
            "parse states no verdict, so it yields no refusal). If the `):`-in-message row is "
            "corrupted into actor `opencode/model): fixed foo(bar`, someone made a capture GREEDY. "
            "FIX: do not chase one row at a time; both failures above are one character of regex, "
            f"and fixing either the wrong way breaks the other.\n" + "\n".join(wrong),
        )

    #: (case, the history RECORD, whether it is a review record, expected verdict polarity, expected
    #: refusal count, why this row exists)
    GATE_READS = (
        (
            "a parenthesized REJECT",
            PAREN_REJECT,
            True,
            PR.NEGATIVE,
            1,
            "THE REGRESSION THAT MATTERS, end to end: reproduced through the real CLI before the fix, "
            "`aw set approved <id6> --by-human` EXITED 0 and wrote `- Status: approved` for a plan "
            "whose own newest review said REJECT, purely because the actor had parentheses",
        ),
        (
            "the SAME rejection with a slash-form actor",
            SLASH_REJECT,
            True,
            PR.NEGATIVE,
            1,
            "the identical command with this actor EXITED 1 and refused. The actor's SPELLING must "
            "not change the verdict read, and asserting both forms in one table is what makes "
            "`must not change` checkable rather than a hope",
        ),
        (
            "a parenthesized actor with a multi-word middle",
            MULTI_WORD_MIDDLE,
            True,
            PR.NEGATIVE,
            1,
            "the review-word family must survive the `mid` widening: `/plan-review pass 2` is a real "
            "middle from the corpus, not a constructed one",
        ),
        (
            "a NARRATING record with a parenthesized actor",
            NARRATING_PAREN,
            False,
            None,
            0,
            "THE NEGATIVE ROW, and the one that makes the three above non-vacuous: the widening must "
            "NOT turn a `to-review` record quoting a predecessor's rejection into a verdict-bearing "
            "one. A rule that refused this would lock out exactly the successor plans that correctly "
            "replaced the rejected ones (F-5)",
        ),
    )

    def test_the_gate_reads_the_same_verdict_whatever_the_actor_spelling(self):
        """One table over the whole chain the parse feeds, replacing three tests.

        The chain is `is_review_history_entry` -> `newest_verdict` -> `approval_refusals`, and the
        bug's signature was that ALL THREE went quiet together: the record did not parse, so it was
        not a review record, so there was no verdict, so there were no refusals. Each old test
        checked one link. Checking all three per row is what makes the failure legible as one cause
        rather than three, and it is why each row states three expectations instead of being weakened
        to one.

        THE NEGATIVE ROW IS IN THE SAME TABLE deliberately. Every positive row here asserts a
        REFUSAL, and a gate that refused everything would satisfy all of them; the narrating row is
        the only thing standing between "the parenthesized actor is read" and "the widening broke the
        F-5 discriminator". The failure message says as much when it is the row that broke.
        """
        wrong = []
        negative_row_broken = False
        for case, record, is_review, polarity, count, why in self.GATE_READS:
            text = _plan(history=record)
            problems = []
            got_is_review = PR.is_review_history_entry(record)
            if got_is_review is not is_review:
                problems.append(
                    f"is_review_history_entry expected {is_review}, got {got_is_review}"
                )
            got_polarity, _ = PR.newest_verdict(text)
            if got_polarity != polarity:
                problems.append(
                    f"newest_verdict polarity expected {polarity!r}, got {got_polarity!r}"
                )
            refusals = self._refusals(text)
            if len(refusals) != count:
                problems.append(
                    f"approval_refusals expected {count} refusal(s), got {len(refusals)}: "
                    f"{refusals!r}"
                )
            elif count and not any("NO override" in r for r in refusals):
                problems.append(
                    f"the refusal must be the UN-OVERRIDABLE verdict one; got {refusals!r}"
                )
            if problems:
                if not is_review:
                    negative_row_broken = True
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if negative_row_broken:
            note = (
                " NOTE: the NARRATING row is among the failures, so the widening has gone too far "
                "and every refusing row above is now suspect rather than reassuring: a gate that "
                "refuses narrating records satisfies them while locking out the successor plans that "
                "correctly replaced the rejected ones."
            )
        self.assertEqual(
            wrong,
            [],
            f"the approval gate misread {len(wrong)} of {len(self.GATE_READS)} records.{note} One "
            "chain produces every row (parse the record, decide whether it is a review record, "
            "classify its verdict, emit the refusal), and the historical bug made ALL of it go quiet "
            "at once, so rows failing together at the SAME LINK is the signal. FIX: refusals "
            "dropping to zero on the parenthesized rows is fn2l1u returning, which means a "
            "formatting accident in an actor name has again disabled the one refusal that has no "
            f"override.\n" + "\n".join(wrong),
        )


if __name__ == "__main__":
    unittest.main()
