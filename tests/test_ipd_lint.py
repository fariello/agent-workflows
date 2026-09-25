"""Tests for the deterministic IPD linter (Set ipd-structure, Order 02).

Covers the spec Section 16 acceptance cases: parser exclusions, both heading orders, metadata
invariants, watermark + dependency grammar, state combinations, checkpoints (incl. pre/post-
transition), OQ + size boundaries, legacy + quarantine dispositions, repository aggregation,
process-exit vs disposition semantics, --agent output, and dash-only-in-prose. Stdlib unittest.

Most of this file is TABLE-DRIVEN, because most of it was one shape repeated: take the minimal
conforming IPD, break exactly one thing, assert one `IPD-*` code. The tables group by SUBJECT rather
than by which function in `ipd_lint.py` implements the check, so the closed sets this linter is built
on (the rule codes, the lifecycle phases, the dispositions) are browsable as sets and a renumbering
that moves several at once reports as ONE failure naming all of them rather than as N red lines.

Where a distinction is a MODE it is a COLUMN, not a second table: the lint PHASE, the plan's
DIRECTORY, the `--legacy` flag, and the `Scope-Paths` cutoff marker all appear as columns, because in
every case the property worth asserting is that the SAME document gets different answers in different
modes, which no single-mode test can state. Where an outcome is three-valued (blocking / advisory /
silent) the rows say which, rather than collapsing it to a bool.

Tests that are NOT rows carry a one-line docstring saying why they stay separate. The recurring
reasons: the subject is a real file or the whole tracked tree rather than a fixture; the claim is
structural (a module attribute's absence, an import allowlist, which layer a check lives in); the
setup is materially different (a throwaway repository on disk, a patched collaborator); or the
assertion is over CLI output rather than a `LintResult`.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agent_workflows import ipd_lint as L
from agent_workflows import ipd_schema as S
from tests.support import CONFORMING_ORCHESTRATOR, REPO_ROOT, SOURCE_DOCS, SOURCE_PLANS
from tests.support import SOURCE_WORKFLOWS as _SWF

CHILD_TEMPLATE = _SWF / "assess" / "templates" / "ipd.md"
SPEC = next(
    (SOURCE_DOCS / "specs").rglob("20260802-1904-01-ipd-structure-and-linting.spec.md")
)


# A minimal conforming CHILD IPD (author phase), built programmatically so tests can mutate it.
def _conforming_child() -> str:
    return """# IPD: sample (Set x, Order 1)

- Date: 2026-08-03
- Kind: child
- Concern: sample.
- Scope: sample.
- Status: to-review
- Work-Kind: chore
- Priority: medium
- Set: x
- Order: 1
- Highest E allocated: 01
- Author: tester
- Id: abc123

## Workflow history

- 2026-08-03 to-review (tester): created.

## Goal

Sample goal.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark performed only after doing it.

### Task group 1: t

- [ ] E-01 do a thing.
  - Depends on: none
  - Expected outcome: the thing exists.
  - Execution state: pending

## Project conventions discovered (Step 0)

- x

## Findings

- x

## Proposed changes (ordered, validatable)

- x

## Deferred / out of scope (with reason)

- x

## Scope check

- x

## Required tests / validation

- x

## Spec / documentation sync

- x

## Open questions

### OQ-01: a question

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: n/a

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence separately.

- [ ] V-01 validates E-01
  - Required evidence: the thing is present at path X.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Gate prose.
"""


def _executed_child(include_executed_history: bool = True) -> str:
    history = "- 2026-08-03 to-review (tester): created.\n"
    if include_executed_history:
        history += "- 2026-08-04 executed (tester): executed.\n"
    return (
        _conforming_child()
        .replace("- Status: to-review", "- Status: executed")
        .replace(
            "## Workflow history\n\n- 2026-08-03 to-review (tester): created.",
            f"## Workflow history\n\n{history.rstrip()}",
        )
        .replace(
            "- [ ] E-01 do a thing.\n  - Depends on: none\n  - Expected outcome: the thing exists.\n  - Execution state: pending",
            "- [x] E-01 do a thing.\n  - Depends on: none\n  - Expected outcome: the thing exists.\n  - Execution state: performed",
        )
        .replace(
            "- [ ] V-01 validates E-01\n  - Required evidence: the thing is present at path X.\n  - Observed evidence:\n  - Result: pending",
            "- [x] V-01 validates E-01\n  - Required evidence: the thing is present at path X.\n  - Observed evidence: verified at path X.\n  - Result: pass",
        )
    )


class ParserExclusionTests(unittest.TestCase):
    """What the parser must NOT see as document structure.

    ONE table replaces two tests. Both asked `parse` for `doc.h2` titles over text containing an H2
    that is NOT structure, and differed only in WHY it is not structure (inside a fenced code block
    versus inside YAML front matter) and in how they asserted it (absence of two titles versus the
    exact title list). The CHECK MODE is therefore a column rather than a reason for two tests: the
    real spec file has dozens of legitimate headings so only ABSENCE is assertable about it, while
    the synthetic fixture has exactly one so its whole list is pinnable.

    Why the table beats the two: both exclusions are implemented by the same skip-state machine
    inside one parse loop, so a regression in the state tracking breaks both at once while each old
    test reported it as an unrelated failure in a different class of input. Keeping them adjacent is
    also what documents that the rule is general (any H2 inside an excluded region is not structure)
    rather than two special cases.
    """

    #: (case, text to parse, the EXACT expected title list or None to skip that check, titles that
    #: must be ABSENT, why this row exists)
    EXCLUSIONS = (
        (
            "the real spec file's own FENCED examples",
            None,  # read from SPEC below; the file is large, so only absence is assertable
            None,
            ("Goal", "Detailed Implementation Checklist (TODO)"),
            "the spec document EXPLAINS the IPD format, so it quotes `## Goal` and `## Detailed "
            "Implementation Checklist (TODO)` inside code fences. Its own H2 are numbered "
            "(`1. Purpose ...`), so either title appearing here means fenced content is being read "
            "as structure and every document that documents the format lints as one",
        ),
        (
            "an H2 inside YAML front matter",
            "---\ntitle: x\n## Goal\n---\n# IPD: x\n\n- Kind: child\n\n## Goal\n\ny\n",
            ["Goal"],
            (),
            "front matter is metadata, not body. The fixture contains the SAME heading twice, once "
            "in the front matter and once for real, so the exact-list check is what proves the "
            "parser counted one and not two; a duplicate would trip the duplicate-heading rule on a "
            "conforming document",
        ),
    )

    def test_no_excluded_region_contributes_a_heading(self):
        wrong = []
        for case, text, exact, forbidden, why in self.EXCLUSIONS:
            body = SPEC.read_text(encoding="utf-8") if text is None else text
            titles = [h.title for h in L.parse(body).h2]
            problems = []
            if exact is not None and titles != exact:
                problems.append(f"expected titles {exact!r}, got {titles!r}")
            leaked = [t for t in forbidden if t in titles]
            if leaked:
                problems.append(
                    f"these titles were counted as real H2 and must not be: {leaked!r}"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the parser read structure out of {len(wrong)} of {len(self.EXCLUSIONS)} excluded "
            "regions. One skip-state machine inside a single parse loop implements both, so BOTH "
            "rows failing together means that state tracking broke rather than either exclusion "
            "being wrong on its own. FIX: a leaked heading does not merely add a title; it makes "
            "documents that DOCUMENT the IPD format lint as malformed IPDs, and it can synthesize a "
            f"duplicate-heading error on a document whose real headings are unique.\n"
            + "\n".join(wrong),
        )


class StructuralRuleTests(unittest.TestCase):
    """Each named structural rule fires on its own malformed plan, at the AUTHOR phase.

    ONE table replaces thirteen tests spread over five classes (`ConformingTests`, `HeadingTests`,
    `MetadataLintTests`, `IdBijectionTests`, `StateMachineTests`, `OpenQuestionAndSizeTests`). Every
    one of them had the identical shape: take the minimal conforming child IPD, break exactly one
    thing, assert one `IPD-*` code appears. The class boundaries tracked which SECTION of the linter
    implemented the rule, which is an implementation detail, not a property of the subject.

    Why the table beats the thirteen: these codes are a CLOSED SET that `aw ipd lint` prints to
    users and that `aw ipd begin` gates on, and the realistic failure is a renumbering or a refactor
    that makes one check return a DIFFERENT code than it used to. Thirteen tests report that as
    thirteen unrelated red lines, each saying only `False is not true`; the table reports one failure
    listing every code that moved, which is the shape of the actual problem. It also makes the set
    browsable as a set, so the next person adding a rule can see what already exists.

    THE POSITIVE ROWS ARE IN THE SAME TABLE deliberately, and they carry real weight here: a linter
    that flagged everything would satisfy every negative row on its own. The clean child is one, and
    the em/en dash plan is the other (dashes are a USER-FACING prose rule only, so an IPD containing
    them must still lint clean). Their failure message says the negatives are vacuous while they are
    broken.

    Two rows pin MORE than the tests they replace, which is what tabulating bought. The
    execution-placement row now names `IPD-H204` where the old test accepted any of three codes, and
    the auto-approved row now forbids `IPD-M104`/`IPD-M101` outright where the old test forbade them
    only in combination with an `Approval` substring. Both were verified against real output.
    """

    #: (case, the plan text, codes that MUST all be reported, message substrings that must appear on
    #: those codes' diagnostics, codes that must NOT be reported, why this row exists)
    #:
    #: THE CODES ARE LITERAL STRINGS, NOT `L.C_*` CONSTANTS, AND THAT IS DELIBERATE. Referencing the
    #: constants would make a RENUMBERING invisible, because the constant and the reported code move
    #: together: measured, renaming `C_HEADING_MISSING` to `IPD-H299` and `C_WATERMARK` to `IPD-I394`
    #: left a constant-referencing version of this table GREEN. Since these codes are a published
    #: interface (users read them in `aw ipd lint` output, the spec names them, and workflows cite
    #: them), a renumbering is a breaking change and must fail here. Do not "tidy" these into
    #: constants.
    RULES = (
        (
            "the minimal conforming child, unmodified",
            _conforming_child(),
            (),
            (),
            (),
            "THE POSITIVE ROW: it must lint CONFORMING and passing. Every negative row below is "
            "vacuous while this one is broken, because a linter that rejects everything satisfies "
            "all of them",
        ),
        (
            "an IPD containing an em dash and an en dash",
            _conforming_child().replace(
                "Sample goal.",
                "Sample goal \u2014 with an em dash \u2013 and an en dash.",
            ),
            (),
            (),
            (),
            "THE SECOND POSITIVE ROW, and a retired rule: the no-em/en-dash convention is a "
            "USER-FACING prose rule only (GUIDING_PRINCIPLES P13), and IPDs are internal/AI-facing "
            "artifacts. IPD-D701 was retired, so a dash must not affect linting at all",
        ),
        (
            "a required H2 deleted",
            _conforming_child().replace("## Scope check\n\n- x\n\n", ""),
            ("IPD-H202",),
            (),
            (),
            "the canonical section list is mandatory: a plan missing `## Scope check` has no place "
            "to record what it decided NOT to touch",
        ),
        (
            "the execution checklist moved out from under Goal",
            _conforming_child().replace(
                "## Goal\n\nSample goal.\n\n## Detailed Implementation Checklist (TODO)",
                "## Goal\n\nSample goal.\n\n## Findings\n\n- x\n\n## Detailed Implementation Checklist (TODO)",
            ),
            ("IPD-H204",),
            (),
            (),
            "PLACEMENT is its own rule, separate from ordering: the checklist must be the H2 "
            "IMMEDIATELY after Goal so an executing agent reads the work directly after the intent. "
            "The old test accepted any of H204/H201/H203, which passed even if placement stopped "
            "being checked and only the generic ordering rule fired; naming H204 fixes that",
        ),
        (
            "a duplicated H2",
            _conforming_child() + "\n## Goal\n\ndup\n",
            ("IPD-H203",),
            (),
            (),
            "two sections with one name make every later cross-reference ambiguous, and the linter's "
            "own section lookups would silently read whichever came first",
        ),
        (
            "an unrecognized metadata field",
            _conforming_child().replace(
                "- Author: tester", "- Author: tester\n- Bogus: y"
            ),
            ("IPD-M103",),
            (),
            (),
            "the metadata block is a CLOSED vocabulary. An unknown field is usually a typo in a real "
            "one, and a typo'd `- Status:` that lints clean is a plan whose state nothing can read",
        ),
        (
            "an orchestrator declaring a nonzero Order",
            _conforming_child().replace("- Kind: child", "- Kind: orchestrator"),
            ("IPD-M104",),
            ("Order",),
            (),
            "`00` is RESERVED for the orchestrator of a Set, so an orchestrator at Order 1 collides "
            "with a child. The message needle is asserted because this code covers every field "
            "constraint, so the code alone would not show that ORDER is what was rejected",
        ),
        (
            "Status: auto-approved",
            _conforming_child().replace(
                "- Status: to-review", "- Status: auto-approved"
            ),
            (),
            (),
            ("IPD-M104", "IPD-M101"),
            "auto-approved is a LEGAL status and does not require the human `- Approval:` field, "
            "which is the whole point of it existing. A forbidden-code row rather than a clean one "
            "because this fixture legitimately trips the ready-to-execute Scope-Paths rule",
        ),
        (
            "a watermark below the highest present E id",
            _conforming_child().replace(
                "- Highest E allocated: 01", "- Highest E allocated: 00"
            ),
            ("IPD-I304",),
            (),
            (),
            "the watermark is how a later session allocates a fresh id without re-reading the whole "
            "checklist; one that lags behind hands out an id that is already in use",
        ),
        (
            "a validation targeting an execution id that does not exist",
            _conforming_child().replace(
                "- [ ] V-01 validates E-01",
                "- [ ] V-01 validates E-01\n  - Required evidence: r\n  - Observed evidence:\n  - Result: pending\n- [ ] V-02 validates E-02",
            ),
            ("IPD-I303",),
            (),
            (),
            "the E/V bijection is what makes every step verifiable and every verification real. An "
            "orphan V claims to validate work no step performs",
        ),
        (
            "two execution items depending on each other",
            _conforming_child()
            .replace(
                "- [ ] E-01 do a thing.\n  - Depends on: none\n  - Expected outcome: the thing exists.\n  - Execution state: pending\n",
                "- [ ] E-01 a.\n  - Depends on: E-02\n  - Expected outcome: o.\n  - Execution state: pending\n"
                "- [ ] E-02 b.\n  - Depends on: E-01\n  - Expected outcome: o.\n  - Execution state: pending\n",
            )
            .replace(
                "- [ ] V-01 validates E-01\n  - Required evidence: the thing is present at path X.\n  - Observed evidence:\n  - Result: pending",
                "- [ ] V-01 validates E-01\n  - Required evidence: r.\n  - Observed evidence:\n  - Result: pending\n"
                "- [ ] V-02 validates E-02\n  - Required evidence: r.\n  - Observed evidence:\n  - Result: pending",
            ),
            ("IPD-I305",),
            ("cycle",),
            (),
            "a cycle makes the checklist unexecutable in ANY order, and it is the one dependency "
            "defect no amount of careful reading catches reliably. The needle distinguishes it from "
            "this code's other cause, a dependency on an id that does not exist",
        ),
        (
            "an item CHECKED while its state says pending",
            _conforming_child().replace(
                "- [ ] E-01 do a thing.", "- [x] E-01 do a thing."
            ),
            ("IPD-S401",),
            (),
            (),
            "the checkbox and the `Execution state:` line are TWO records of one fact, and they must "
            "agree. Disagreement is how a plan comes to claim work that was never performed",
        ),
        (
            "a validation marked pass with EMPTY observed evidence",
            _conforming_child().replace(
                "  - Observed evidence:\n  - Result: pending",
                "  - Observed evidence:\n  - Result: pass",
            ),
            ("IPD-S402", "IPD-S403"),
            (),
            (),
            "TWO codes fire and both are asserted: the checkbox disagrees with the result (S402) AND "
            "a pass requires its E item to be performed (S403). This is the single most important "
            "row in the table, because `pass` with no evidence is precisely the shape of a plan that "
            "claims success nobody demonstrated",
        ),
        (
            "a BLOCKING open question marked deferred",
            _conforming_child().replace(
                "- Blocking: no\n- Status: open",
                "- Blocking: yes\n- Status: deferred",
            ),
            ("IPD-Q501",),
            (),
            (),
            "`deferred` means we chose to proceed without the answer, which is a contradiction when "
            "the question BLOCKS. Resolve it or drop the blocking claim; do not do both",
        ),
        (
            "an out-of-vocabulary size assessment",
            _conforming_child().replace(
                "- Size assessment: standard", "- Size assessment: bogus"
            ),
            ("IPD-Z601",),
            (),
            (),
            "the size vocabulary is two values (`standard`, `exception`), and `exception` is what "
            "demands a cohesion rationale. A third value silently escapes that obligation",
        ),
    )

    def test_every_structural_rule_fires_on_its_own_violation(self):
        wrong = []
        positive_rows_broken = 0
        for case, text, codes, needles, forbidden, why in self.RULES:
            res = L.lint_text(text, checkpoint="author", directory="pending")
            reported = [d.code for d in res.diagnostics]
            problems = []
            if not codes and not forbidden:
                # A positive row: it must lint CONFORMING and passing.
                if res.disposition != S.DISPOSITION_CONFORMING or not res.passing:
                    positive_rows_broken += 1
                    problems.append(
                        f"must lint CONFORMING and passing; got disposition "
                        f"{res.disposition!r}, passing={res.passing}, diagnostics "
                        f"{[d.render('t') for d in res.diagnostics]!r}"
                    )
            missing = [c for c in codes if c not in reported]
            if missing:
                problems.append(
                    f"expected code(s) {missing!r}; the linter reported "
                    f"{reported or 'NOTHING AT ALL (it linted clean)'}"
                )
            for needle in needles:
                if not any(
                    needle in d.message for d in res.diagnostics if d.code in codes
                ):
                    problems.append(
                        f"no {codes!r} diagnostic mentions {needle!r}; messages were "
                        f"{[d.message for d in res.diagnostics if d.code in codes]!r}"
                    )
            leaked = [c for c in forbidden if c in reported]
            if leaked:
                problems.append(
                    f"reported {leaked!r}, which this row requires it NOT to; all diagnostics: "
                    f"{[d.render('t') for d in res.diagnostics]!r}"
                )
            if codes and res.disposition != S.DISPOSITION_ERROR:
                problems.append(
                    f"a flagged plan must have disposition {S.DISPOSITION_ERROR!r}; got "
                    f"{res.disposition!r}"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        vacuity = ""
        if positive_rows_broken:
            vacuity = (
                f" {positive_rows_broken} POSITIVE row(s) are among the failures, and while any of "
                "those is broken every negative row here is VACUOUS: a linter that rejects "
                "everything satisfies all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"the linter mishandled {len(wrong)} of {len(self.RULES)} structural rules.{vacuity} "
            "The `IPD-*` codes are a CLOSED SET that `aw ipd lint` prints to users and that "
            "`aw ipd begin` gates on, so SEVERAL ROWS MOVING TOGETHER usually means a renumbering "
            "or a refactor of one check family rather than several independent breakages: look at "
            "the code PREFIXES in the failures (`H2xx` headings, `M1xx` metadata, `I3xx` ids, "
            "`S4xx` states) and fix the family, not the rows. FIX: a row reporting NOTHING AT ALL is "
            "worse than one reporting the wrong code, because a rule that stopped firing lets the "
            f"malformed plan through every gate that consumes this linter.\n"
            + "\n".join(wrong),
        )

    def test_the_conforming_orchestrator_fixture_conforms(self):
        """Kept separate: lints a real FILE from the fixture tree, not a mutated string.

        Every table row is built by editing `_conforming_child()` in memory, so none of them
        exercises `lint_file` or the ORCHESTRATOR kind, whose canonical heading list differs from a
        child's. This is the only guard that the shipped fixture other tests build on is itself
        clean.
        """
        p = CONFORMING_ORCHESTRATOR
        res = L.lint_file(p, checkpoint="author")
        self.assertEqual(
            res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.render(str(p)) for d in res.diagnostics],
        )

    def test_the_dash_rule_code_is_gone_rather_than_merely_silent(self):
        """Kept separate: asserts the ABSENCE OF A MODULE ATTRIBUTE, not a lint result.

        The table's dash row proves the rule does not FIRE; this proves its code no longer EXISTS
        (IPD-D701 was retired), so the rule cannot be reinstated by flipping a condition back.
        """
        self.assertFalse(hasattr(L, "C_DASH"))


class ReadinessAttestationTests(unittest.TestCase):
    """rdattest: `- Readiness:` is a REVIEW OUTPUT and may not be written at authoring time.

    THE REGRESSION THIS PINS, measured 2026-09-06: an agent authoring a plan Set wrote
    `- Readiness: go-pending-approval` into four fresh plans having run no review.
    `plan_readiness.is_plan_review_approved` reads the FIELD FIRST and only falls back to the
    workflow history when the field is ABSENT, so all four asserted that review had cleared them and
    the predicate returned True for every one. Under `--full-auto` that predicate is what promotes a
    plan to approved and its queue action to `execute`, so a hand-typed field is a route from
    unreviewed to executing. The vocabulary was already policed (IPD-M104); the PROVENANCE was not.
    """

    ATTESTING_APPROVE = (
        "- 2026-09-06 reviewed (tester): /plan-review round 1: "
        "APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL."
    )
    ATTESTING_NO_GO = (
        "- 2026-09-06 reviewed (tester): /plan-review round 1: "
        "NO-GO, a blocking open question remains."
    )

    def _plan(self, readiness=None, review=None, approved=False) -> str:
        """The conforming child with an optional `- Readiness:` and an optional review record."""
        text = _conforming_child()
        meta = (
            "- Status: approved\n- Approval: 2026-09-06, probe"
            if approved
            else "- Status: to-review"
        )
        if readiness is not None:
            meta += f"\n- Readiness: {readiness}"
        text = text.replace("- Status: to-review", meta, 1)
        if review is not None:
            text = text.replace(
                "## Workflow history", f"## Workflow history\n\n{review}", 1
            )
        return text

    #: (case, the `- Readiness:` value or None to omit it, a review history record or None, whether
    #: the plan is made ready-to-execute, the lint PHASE, whether IPD-M107 must be reported as a
    #: BLOCKING diagnostic, why this row exists)
    ATTESTATIONS = (
        (
            "a hand-written Readiness with NO review in the history",
            "go-pending-approval",
            None,
            False,
            "author",
            True,
            "THE MEASURED REGRESSION, 2026-09-06: an agent authoring a four-plan Set wrote exactly "
            "this into all four having run no review, and `is_plan_review_approved` returned True for "
            "every one because it reads the FIELD FIRST. Under `--full-auto` that predicate promotes "
            "a plan to approved and its queue action to `execute`, so this row is the whole rule",
        ),
        (
            "no Readiness field at all",
            None,
            None,
            False,
            "author",
            False,
            "ABSENCE IS THE CORRECT AUTHORING STATE, so it must be SILENT: not flagged, and not "
            "nudged as an advisory either. A nudge here would teach agents to write the field, which "
            "is precisely the behavior the rule exists to stop",
        ),
        (
            "a Readiness attested by an APPROVING review",
            "go-pending-approval",
            ATTESTING_APPROVE,
            False,
            "author",
            False,
            "a real review writes the field in the SAME pass, and that must stay conforming. Without "
            "this row the rule could be `never allow the field`, which would make every genuine "
            "review output nonconforming",
        ),
        (
            "a NO-GO Readiness attested by a NO-GO review",
            "no-go",
            ATTESTING_NO_GO,
            False,
            "author",
            False,
            "A NO-GO VERDICT IS REVIEW EVIDENCE TOO. The rule polices PROVENANCE, not polarity, so it "
            "must not quietly require an APPROVE; a rule that did would refuse the field exactly when "
            "review had refused the plan, which is the one time it most needs recording",
        ),
        (
            "the same unattested field on a ready-to-execute plan",
            "go",
            None,
            True,
            "pre-execution",
            True,
            "THE RULE MUST BE BLOCKING, NOT ADVISORY, and the PHASE column is what shows it: "
            "`ipd_lifecycle.begin` refuses unless the `pre-execution` lint is CONFORMING, so an "
            "unattested Readiness has to make that lint error or the rule is cosmetic and the "
            "--full-auto route stays open",
        ),
    )

    def test_the_rule_fires_only_on_an_unattested_readiness_at_every_phase(self):
        """One table over the attestation rule, replacing five tests.

        THE PHASE IS A COLUMN, and that is the reason this is one table rather than an author-phase
        table plus a pre-execution test. The rule's whole value depends on being BLOCKING at the gate
        `ipd_lifecycle.begin` consults, so `author` and `pre-execution` rows must sit together: the
        author rows establish WHEN it fires, and the pre-execution row establishes that firing
        actually stops something. Split apart, a change that demoted the rule to an advisory would
        leave the author tests green and read as a cosmetic difference.

        Why the table beats the five: one predicate (`check_readiness_attestation`) decides every
        row by looking for a review verdict in the history, so a regression moves rows in a legible
        pattern. Both ATTESTED rows failing together means the review-detection half broke and the
        rule now refuses genuine review output; both UNATTESTED rows failing together means it stopped
        firing at all and the 2026-09-06 route from unreviewed to executing is open again.

        The SILENT row is in the same table deliberately and checks the ADVISORY channel too: a rule
        that flagged every plan would satisfy both firing rows, and a rule that merely nudged instead
        of blocking would satisfy them while gating nothing.
        """
        wrong = []
        for case, readiness, review, approved, phase, fires, why in self.ATTESTATIONS:
            res = L.lint_text(
                self._plan(readiness=readiness, review=review, approved=approved),
                checkpoint=phase,
                directory="pending",
            )
            blocking = [
                d for d in res.diagnostics if d.code == L.C_READINESS_UNATTESTED
            ]
            advisory = [d for d in res.advisories if d.code == L.C_READINESS_UNATTESTED]
            problems = []
            if fires and not blocking:
                problems.append(
                    "expected a BLOCKING IPD-M107 diagnostic; the linter reported "
                    + repr([d.render("t") for d in res.diagnostics] or "nothing at all")
                    + (
                        f" (it was reported as an ADVISORY instead, so the rule gates nothing: "
                        f"{[d.render('t') for d in advisory]!r})"
                        if advisory
                        else ""
                    )
                )
            if fires and blocking and res.disposition != S.DISPOSITION_ERROR:
                problems.append(
                    f"IPD-M107 fired but the disposition is {res.disposition!r}, not "
                    f"{S.DISPOSITION_ERROR!r}, so `aw ipd begin` would still let this plan through"
                )
            if not fires and blocking:
                problems.append(
                    f"IPD-M107 must NOT fire here; it did: {[d.render('t') for d in blocking]!r}"
                )
            if not fires and advisory:
                problems.append(
                    f"IPD-M107 must not appear as an ADVISORY either; it did: "
                    f"{[d.render('t') for d in advisory]!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (phase={phase}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"the Readiness attestation rule was wrong for {len(wrong)} of {len(self.ATTESTATIONS)} "
            "plans. ONE predicate decides every row by looking for a review verdict in the history, "
            "so read the grouping: both ATTESTED rows failing together means review detection broke "
            "and the rule now refuses genuine review output, while both UNATTESTED rows failing "
            "together means it stopped firing and a hand-typed field once again asserts that review "
            "cleared a plan nobody reviewed. FIX: a row that should fire and now reports an ADVISORY "
            "rather than a diagnostic is the most dangerous outcome, because it LOOKS enforced in "
            "`aw ipd lint` output while `aw ipd begin` sees a conforming plan and proceeds.\n"
            + "\n".join(wrong),
        )

    def test_every_readiness_carrying_plan_in_the_tree_is_attested(self):
        """Kept separate: sweeps the REAL tracked plan tree, so it has no fixture and no rows.

        Corpus guard: no tracked plan may carry a Readiness with no review behind it.

        This is the check that would have caught the original mistake at commit time, and it keeps
        catching it for any plan a future session authors.

        THE CHECKER NOW COVERS THIS RULE TOO, so do not read this test as the only line of defense
        (lintreach `k9awrq`). `aw check plans` runs the real `ipd_lint.lint_file` at the `author`
        checkpoint over every pending plan and reports any `IPD-*` diagnostic, `IPD-M107` included,
        under `check.ipd-lint-diagnostic`. This guard is deliberately KEPT rather than deleted as
        redundant: it is cheap, it sweeps the WHOLE tracked tree (the checker is scoped to the pending
        lane), and the sweep's rule is registered `info`, so it REPORTS without failing a gate while
        this test FAILS. Deleting a passing corpus test because a checker now overlaps it is how
        coverage silently narrows.
        """
        offenders = []
        for plan in sorted((REPO_ROOT / SOURCE_PLANS).rglob("*.ipd.md")):
            doc = L.parse(plan.read_text(encoding="utf-8"))
            if not L.check_readiness_attestation(doc):
                continue
            offenders.append(plan.name)
        self.assertEqual(offenders, [], f"unattested Readiness in: {offenders}")


class IdBijectionTests(unittest.TestCase):
    """What remains after the bijection RULES moved into `StructuralRuleTests`: the id GRAMMAR itself."""

    def test_more_than_99_ids_ok(self):
        """Kept separate: asserts over the ID GRAMMAR primitives, not over a lint result.

        The orphan-validation and dependency-cycle rows moved to `StructuralRuleTests`, which lints a
        whole document. This one calls `S.suffix_of` and `S.E_ID_STRICT` directly, because the claim
        is that the grammar admits three digits at all; no malformed-plan row can state that, since a
        plan with 100 items would be the fixture rather than the assertion.
        """
        self.assertEqual(S.suffix_of("E-100"), 100)
        self.assertTrue(S.E_ID_STRICT.match("E-100"))


class CheckpointPhaseTests(unittest.TestCase):
    """What each lifecycle PHASE additionally demands of a plan that is otherwise conforming.

    ONE table replaces three tests from two classes (`StateMachineTests`'s pre-transition case and
    both of `CheckpointTests`). All three linted a plan at a non-author phase and asserted that
    `IPD-S404` appeared, differing only in the phase and in what made the plan unready.

    THE PHASE IS A COLUMN and this is the clearest case for it in the file, because the checkpoint
    layer's entire purpose is that the SAME document is conforming at one phase and refused at
    another. The `author` row and the `pre-transition` row below are the SAME unmodified conforming
    child, and only having both in one table states the relationship: `author` is the permissive
    phase where a plan is still being written, while `pre-transition` demands every E performed and
    every V passed. Three separate tests can each assert one phase's answer and none can assert that
    the answers differ by phase alone.

    Why the table beats the three: one dispatch on `checkpoint` produces every row, and the realistic
    failure is a phase name being renamed or dropped from a gating set, in which case the demands
    silently vanish and the plan lints CLEAN. That failure looks identical in all three old tests
    (`False is not true`) and is legible here: every non-author row going clean at once means the
    phase dispatch broke, not that three rules regressed.

    The `author` row is the POSITIVE one and it is load-bearing rather than decorative: a checkpoint
    layer that demanded performed-and-passed at EVERY phase would satisfy all the refusing rows while
    making it impossible to lint a plan you are still authoring, which is the phase agents run most.
    """

    @staticmethod
    def _approved_with_blocking_question() -> str:
        return (
            _conforming_child()
            .replace(
                "- Blocking: no\n- Status: open\n- Owner: none\n- Resolution or deferral rationale: n/a",
                "- Blocking: yes\n- Status: open\n- Owner: someone\n- Resolution or deferral rationale:",
            )
            .replace("- Status: to-review", "- Status: approved")
            .replace(
                "- Author: tester",
                "- Approval: approved by x 2026-08-03\n- Author: tester",
            )
        )

    #: (case, plan text, phase, whether IPD-S404 must fire, message substrings required on the S404
    #: diagnostics (lower-cased comparison), why this row exists)
    PHASES = (
        (
            "the unmodified conforming child at the AUTHORING phase",
            _conforming_child(),
            "author",
            False,
            (),
            "THE POSITIVE ROW, and the same document as the pre-transition row below. A plan being "
            "written has every item pending BY DEFINITION, so `author` must impose none of the gate "
            "demands; a layer that imposed them everywhere would make the phase agents run most "
            "unusable while satisfying every refusing row here",
        ),
        (
            "the SAME all-pending plan at PRE-TRANSITION",
            _conforming_child(),
            "pre-transition",
            True,
            ("not 'performed'", "not 'pass'", "empty observed evidence"),
            "the terminal gate demands every E PERFORMED and every V PASSED WITH EVIDENCE, which is "
            "what stops a plan from reaching `executed` while claiming success nobody demonstrated. "
            "All three needles are asserted because a gate that checked only the checkbox would fire "
            "S404 and still let an evidence-free pass through",
        ),
        (
            "a to-review plan at PRE-EXECUTION",
            _conforming_child(),
            "pre-execution",
            True,
            ("status 'to-review' is incompatible",),
            "STATUS COMPATIBILITY: `pre-execution` is reached only by an approved plan, so a plan "
            "still awaiting review must be refused BY ITS STATUS before any of its contents matter",
        ),
        (
            "an APPROVED plan with an unresolved BLOCKING question at PRE-EXECUTION",
            _approved_with_blocking_question.__func__(),
            "pre-execution",
            True,
            ("unresolved blocking question",),
            "the status is now compatible, so this row isolates the OTHER pre-execution demand: a "
            "blocking question still open means the plan is about to be executed over a decision "
            "nobody made. Keeping it beside the status row is what shows the two demands are "
            "independent rather than one check with two messages",
        ),
    )

    def test_every_phase_imposes_exactly_its_own_demands(self):
        wrong = []
        author_row_broken = False
        for case, text, phase, fires, needles, why in self.PHASES:
            res = L.lint_text(text, checkpoint=phase, directory="pending")
            found = [d for d in res.diagnostics if d.code == L.C_CHECKPOINT]
            messages = " | ".join(d.message.lower() for d in found)
            problems = []
            if fires and not found:
                problems.append(
                    "expected an IPD-S404 checkpoint diagnostic; the linter reported "
                    + repr([d.render("t") for d in res.diagnostics] or "nothing at all")
                )
            if not fires and found:
                author_row_broken = True
                problems.append(
                    f"IPD-S404 must NOT fire at this phase; it did: "
                    f"{[d.render('t') for d in found]!r}"
                )
            missing = [n for n in needles if n not in messages]
            if missing:
                problems.append(
                    f"the S404 diagnostics never mention {missing!r}; they said "
                    f"{[d.message for d in found]!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (phase={phase}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if author_row_broken:
            note = (
                " NOTE: the AUTHOR row is among the failures, so the checkpoint layer is now "
                "imposing gate demands at every phase. That satisfies every refusing row here while "
                "making a plan impossible to lint while it is being written."
            )
        self.assertEqual(
            wrong,
            [],
            f"the checkpoint layer was wrong for {len(wrong)} of {len(self.PHASES)} phase/plan "
            f"combinations.{note} One dispatch on `checkpoint` produces every row, and the phase "
            "names are a CLOSED SET, so read the grouping: if EVERY non-author row went clean, a "
            "phase name was renamed or dropped from a gating set and the demands vanished silently "
            "rather than erroring. FIX: a row that should fire and now lints clean is the dangerous "
            "direction, because `aw ipd begin` and the finalize transaction both refuse only on a "
            "non-conforming lint, so a demand that stopped being imposed is a gate that stopped "
            f"existing.\n" + "\n".join(wrong),
        )


class PostTransitionExecutedHistoryTests(unittest.TestCase):
    """The POST-TRANSITION checks, which are the only ones that run on a terminal-directory plan.

    IPD-S405 (a plan claiming `executed` must carry the history entry proving it) is asserted in
    `DispositionTests`, where it sits beside the grandfathering rows that decide whether it runs at
    all. What lives here is IPD-S406, the ATTRIBUTION lint, plus the one real-file check.
    """

    # --- ipdgates Order wezhxg: post-transition attribution lint (IPD-S406) ---
    #: (case, the executed record's actor, its summary message, the Scope-Paths value or None to
    #: omit the field entirely, whether IPD-S406 must fire, why this row exists)
    ATTRIBUTIONS = (
        (
            "the `aw set` machine default on a post-cutoff plan",
            "aw set",
            "status set to executed",
            "agent_workflows/x.py",
            True,
            "THE RULE: a terminal move must say WHO executed the plan, and `aw set` is the setter's "
            "own default, so it names the tool rather than the agent. A tree of plans all "
            "`executed (aw set)` records that something transitioned them and nothing about who did "
            "the work",
        ),
        (
            "a real actor with an EMPTY summary, post-cutoff",
            "opencode/model",
            "",
            "agent_workflows/x.py",
            True,
            "the SECOND half of the rule, and independent of the first: naming the agent is not "
            "enough if the record says nothing about what was done. Without this row the check could "
            "be an actor allowlist and nothing more",
        ),
        (
            "a real actor with a real summary, post-cutoff",
            "opencode/its_direct/pt3",
            "did the work",
            "agent_workflows/x.py",
            False,
            "THE POSITIVE ROW: the shape a genuine `aw ipd finalize` writes. Every refusing row here "
            "is vacuous while this is broken, because a rule that rejected every terminal record "
            "satisfies them all and makes finalize impossible",
        ),
        (
            "a bare tool name",
            "Antigravity",
            "did it",
            "agent_workflows/x.py",
            False,
            "THE SCOPE IS PINNED NARROWLY: only the `aw set` machine default is generic. A rule that "
            "ballooned into judging whether a name looks specific enough would refuse the real actors "
            "agents and humans actually write",
        ),
        (
            "a bare human role name",
            "maintainer",
            "did it",
            "agent_workflows/x.py",
            False,
            "a HUMAN executing a plan is a legitimate actor, and `maintainer` is what they write. The "
            "rule must not require a model identifier",
        ),
        (
            "another agent's slash-form actor",
            "codex/gpt-5",
            "did it",
            "agent_workflows/x.py",
            False,
            "and the rule is not opencode-specific; a different agent's spelling is equally valid",
        ),
        (
            "the `aw set` default on a plan marked `grandfathered`",
            "aw set",
            "status set to executed",
            "grandfathered",
            False,
            "FORWARD-ONLY, keyed on the Order 02 cutoff marker: the historical tree was written "
            "before the rule existed and may not be retroactively failed. Same actor as the first "
            "row, opposite expectation, which is what makes the cutoff column the operative "
            "difference rather than a coincidence",
        ),
        (
            "the `aw set` default on a plan with NO Scope-Paths field at all",
            "aw set",
            "status set to executed",
            None,
            False,
            "the field's TOTAL ABSENCE is also pre-cutoff, which is the case the whole existing "
            "executed tree is in. A cutoff that keyed only on the literal `grandfathered` marker "
            "would fail hundreds of real plans that never carried the field",
        ),
    )

    def _executed_with(self, actor: str, msg: str, scope_paths) -> str:
        """An executed child whose newest history entry is `executed (<actor>): <msg>`.

        ``scope_paths`` declares a real (post-cutoff) or ``grandfathered`` (pre-cutoff) allowlist, or
        is None to omit the field entirely, which is also pre-cutoff.
        """
        text = _executed_child(include_executed_history=False)
        if scope_paths is not None:
            text = text.replace(
                "- Scope: sample.", f"- Scope: sample.\n- Scope-Paths: {scope_paths}", 1
            )
        # Insert the newest executed entry right after the Workflow history heading.
        text = text.replace(
            "## Workflow history\n\n- 2026-08-03 to-review (tester): created.",
            f"## Workflow history\n\n- 2026-08-05 executed ({actor}): {msg}\n"
            "- 2026-08-03 to-review (tester): created.",
            1,
        )
        return text

    def test_attribution_fires_only_on_a_generic_terminal_record_past_the_cutoff(self):
        """One table over IPD-S406, replacing six tests (ipdgates Order wezhxg).

        THE CUTOFF IS A COLUMN, and it is the reason this is one table. The rule is FORWARD-ONLY: the
        `Scope-Paths` field doubles as the cutoff marker, so the identical `executed (aw set)` record
        must be REFUSED on a plan declaring a real allowlist and ACCEPTED on one marked
        `grandfathered` or carrying no field at all. That is a relationship between rows sharing an
        actor and differing only in the marker, which no single test can state; split up, the three
        old tests each looked like an independent policy.

        Why the table beats the six: one predicate decides every row from two inputs (is the actor
        generic or the summary empty, and is this plan past the cutoff), so a regression moves a whole
        class of rows. Every ACCEPTED row failing at once means the generic-actor set ballooned and
        the rule now refuses the real actors agents write; every REFUSED row going clean means either
        the check stopped firing or the cutoff swallowed everything.

        Note this rule is POST-transition, so it fires AFTER the lifecycle commit. A false positive
        therefore lands on a plan already moved to `executed/`, which is why the accepted rows
        outnumber the refused ones and are stated so specifically.
        """
        wrong = []
        accepted_rows_broken = 0
        for case, actor, msg, scope_paths, fires, why in self.ATTRIBUTIONS:
            res = L.lint_text(
                self._executed_with(actor, msg, scope_paths),
                checkpoint="post-transition",
                directory="executed",
            )
            found = [d for d in res.diagnostics if d.code == L.C_EXEC_ATTRIBUTION]
            problems = []
            if fires and not found:
                problems.append(
                    "expected IPD-S406; the linter reported "
                    + repr([d.render("t") for d in res.diagnostics] or "nothing at all")
                )
            if not fires and found:
                accepted_rows_broken += 1
                problems.append(
                    f"IPD-S406 must NOT fire here; it did: "
                    f"{[d.render('t') for d in found]!r}"
                )
            if problems:
                marker = (
                    "no Scope-Paths field" if scope_paths is None else repr(scope_paths)
                )
                wrong.append(
                    f"  {case} (actor={actor!r}, summary={msg!r}, cutoff marker={marker}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if accepted_rows_broken:
            note = (
                f" {accepted_rows_broken} ACCEPTED row(s) are among the failures, so the rule is now "
                "refusing records it must permit, and every refusing row here is vacuous while that "
                "is true. Since IPD-S406 is POST-transition, each such refusal lands on a plan "
                "already committed to `executed/`, where nothing can be fixed by re-running."
            )
        self.assertEqual(
            wrong,
            [],
            f"IPD-S406 was wrong for {len(wrong)} of {len(self.ATTRIBUTIONS)} terminal records."
            f"{note} One predicate over two inputs decides every row (generic actor or empty summary, "
            "and past the cutoff or not), so read the grouping: if the three rows sharing the actor "
            "`aw set` no longer disagree, the CUTOFF column stopped being read and the rule is "
            "either retroactive or disabled. FIX: check `_GENERIC_ACTORS`, which is pinned "
            "deliberately NARROW to the two `aw set` spellings; widening it to judge whether a name "
            f"looks specific enough is how the accepted rows start failing.\n"
            + "\n".join(wrong),
        )

    def test_real_executed_plan_at_post_transition(self):
        """Kept separate: lints a REAL FILE from the executed tree via `lint_file`.

        The tables above all mutate `_executed_child()` in memory. This is the only check that the
        rules the fixtures encode actually hold for a plan the repository really contains, which a
        fixture-only suite can never establish.
        """
        real_executed = sorted((SOURCE_PLANS / "executed").glob("*.md"))
        self.assertTrue(len(real_executed) > 0)
        # Select the latest conforming executed plan
        sample_plan = real_executed[-1]
        res = L.lint_file(sample_plan, checkpoint="post-transition")
        self.assertNotIn(L.C_EXEC_HISTORY, [d.code for d in res.diagnostics])


class DispositionTests(unittest.TestCase):
    """Which DISPOSITION a plan lands in, given its directory and the phase it is linted at.

    ONE table replaces five tests from two classes (three from
    `PostTransitionExecutedHistoryTests` plus two of this class's own). All five called `lint_text`
    and asserted a disposition, a `passing` flag, and sometimes a code, differing only in the
    document, the directory, and the phase.

    BOTH THE DIRECTORY AND THE PHASE ARE COLUMNS, and that is the reason for one table rather than
    three. The disposition layer's whole job is to SHORT-CIRCUIT before the structural checks run,
    and which short-circuit applies depends on the combination: a terminal-directory plan is
    grandfathered to `legacy` at every phase EXCEPT `post-transition`, where it is evaluated for real
    because it has just been moved there. The two rows carrying the identical evidence-free executed
    child at `author` and at `post-transition` are the same document with opposite answers, which is
    precisely the invariant, and no single-row test can state it.

    Why the table beats the five: three short-circuits (terminal-dir grandfathering, quarantine, and
    the post-transition exception to the first) decide every row before any rule fires, so a
    regression there changes many answers at once and changes them SILENTLY: `legacy` is not a
    failure, it is `not evaluated`, so a short-circuit that widened makes plans stop being checked
    rather than start failing. That is the failure mode this accumulated report is written for.

    The CONFORMING row is the positive one: every other row asserts that something was NOT fully
    evaluated or NOT passing, and a layer that short-circuited everything would satisfy all of them.
    """

    #: (case, plan text, directory, phase, expected disposition, expected `passing`, a mapping of
    #: code -> (exact number of diagnostics with that code, a required message substring) that must
    #: be reported, whether the diagnostics list must be EMPTY, why this row exists)
    DISPOSITIONS = (
        (
            "an executed plan carrying its `executed` history entry, at post-transition",
            _executed_child(include_executed_history=True),
            "executed",
            "post-transition",
            S.DISPOSITION_CONFORMING,
            True,
            {},
            True,
            "THE POSITIVE ROW: the shape a completed lifecycle transaction leaves behind. It is fully "
            "evaluated (post-transition is the one phase that does not grandfather a terminal plan) "
            "and comes out clean, so every other row's claim that something was skipped or refused "
            "means something",
        ),
        (
            "the SAME plan with its `executed` history entry REMOVED, at post-transition",
            _executed_child(include_executed_history=False),
            "executed",
            "post-transition",
            S.DISPOSITION_ERROR,
            False,
            {
                L.C_EXEC_HISTORY: (
                    1,
                    "must carry an 'executed' ## Workflow history entry",
                )
            },
            False,
            "IPD-S405: a plan claiming `Status: executed` must carry the history entry recording that "
            "transition. Status and history are two records of one event, and a plan whose status says "
            "executed while its history never mentions it is a hand-edited status",
        ),
        (
            "that same evidence-free plan at the AUTHOR phase",
            _executed_child(include_executed_history=False),
            "executed",
            "author",
            S.DISPOSITION_LEGACY,
            False,
            {},
            True,
            "GRANDFATHERING, and the pair of the row above it: the identical document is ERROR at "
            "post-transition and NOT EVALUATED at every other phase. The whole existing terminal tree "
            "predates these rules, so linting it at author must not retroactively fail hundreds of "
            "plans; only the plan being moved RIGHT NOW is judged",
        ),
        (
            "a perfectly conforming CHILD plan sitting in a terminal directory",
            _conforming_child(),
            "executed",
            "author",
            S.DISPOSITION_LEGACY,
            False,
            {},
            True,
            "grandfathering keys on the DIRECTORY, not on the document: even a plan that would lint "
            "clean reports `legacy`. And `legacy` is NOT passing, which is the important half: it "
            "means `not evaluated`, so nothing may treat it as a clean bill of health",
        ),
        (
            "a plan whose metadata declares QUARANTINE",
            _conforming_child().replace(
                "- Author: tester",
                "- Quarantine: re-author later\n- Quarantine owner: maintainer\n"
                "- Quarantine follow-up: after the Set\n- Author: tester",
            ),
            "pending",
            "author",
            S.DISPOSITION_QUARANTINED,
            False,
            {},
            True,
            "a SECOND, independent short-circuit, and one that applies in a NON-terminal directory: a "
            "plan explicitly parked for re-authoring is reported rather than rule-checked, and it is "
            "not passing either. Keeping it beside the terminal rows is what shows the two "
            "short-circuits are separate mechanisms rather than one directory test",
        ),
    )

    def test_every_directory_and_phase_combination_lands_in_its_disposition(self):
        wrong = []
        conforming_row_broken = False
        for (
            case,
            text,
            directory,
            phase,
            disposition,
            passing,
            codes,
            empty,
            why,
        ) in self.DISPOSITIONS:
            res = L.lint_text(text, checkpoint=phase, directory=directory)
            reported = [d.code for d in res.diagnostics]
            problems = []
            if res.disposition != disposition:
                if disposition == S.DISPOSITION_CONFORMING:
                    conforming_row_broken = True
                problems.append(
                    f"expected disposition {disposition!r}, got {res.disposition!r}"
                )
            if res.passing is not passing:
                problems.append(f"expected passing={passing}, got {res.passing}")
            for code, (count, needle) in codes.items():
                found = [d for d in res.diagnostics if d.code == code]
                if len(found) != count:
                    problems.append(
                        f"expected exactly {count} {code} diagnostic(s), got {len(found)}; all "
                        f"codes reported were {reported!r}"
                    )
                if not any(needle in d.message for d in found):
                    problems.append(
                        f"no {code} diagnostic mentions {needle!r}; messages were "
                        f"{[d.message for d in found]!r}"
                    )
            if empty and res.diagnostics:
                problems.append(
                    f"the diagnostics list must be EMPTY (nothing was evaluated), and it holds "
                    f"{[d.render('t') for d in res.diagnostics]!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (directory={directory!r}, phase={phase!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if conforming_row_broken:
            note = (
                " NOTE: the CONFORMING row is among the failures, so every other row here is "
                "vacuous: a layer that short-circuited or refused everything satisfies all of them."
            )
        self.assertEqual(
            wrong,
            [],
            f"the disposition layer was wrong for {len(wrong)} of {len(self.DISPOSITIONS)} "
            f"directory/phase combinations.{note} Three short-circuits decide every row BEFORE any "
            "rule runs (terminal-directory grandfathering, quarantine, and the post-transition "
            "exception to the first), so read the grouping: if the two rows carrying the SAME "
            "evidence-free executed child stopped disagreeing, the post-transition exception broke "
            "and either the historical tree is being retroactively failed or a just-moved plan is no "
            "longer checked at all. FIX: a row that wrongly reports `legacy` is the quiet failure, "
            "because `legacy` means NOT EVALUATED rather than failed, so the plan stops being linted "
            f"without anything going red.\n" + "\n".join(wrong),
        )

    def test_conforming_is_the_only_pass(self):
        """Kept separate: asserts over the `LintResult` CONSTRUCTOR, not over a linted document.

        The table above reaches `passing` through real documents and can therefore only exercise the
        dispositions those documents produce. This enumerates the whole disposition set directly,
        which is what pins that CONFORMING is the ONLY passing one; a fourth disposition added as
        passing would slip past every row above.
        """
        self.assertTrue(L.LintResult(S.DISPOSITION_CONFORMING, []).passing)
        self.assertFalse(L.LintResult(S.DISPOSITION_LEGACY, []).passing)
        self.assertFalse(L.LintResult(S.DISPOSITION_QUARANTINED, []).passing)
        self.assertFalse(L.LintResult(S.DISPOSITION_ERROR, []).passing)


class DiagnosticShapeTests(unittest.TestCase):
    """The rendered diagnostic LINE FORMAT, which editors and CI parse. Not tabulated: one claim."""

    def test_diagnostic_renders_with_code_and_location(self):
        """Kept separate: constructs a `Diagnostic` directly and asserts its RENDERED form.

        Not a lint result at all: the subject is the `path:line:col CODE message` layout editors and
        CI parse, so no table row over a linted document expresses it.
        """
        d = L.Diagnostic(84, 1, L.C_ID_GRAMMAR, "duplicate execution id E-04")
        self.assertEqual(
            d.render("p.md"), "p.md:84:1 IPD-I301 duplicate execution id E-04"
        )


class ExitCodeTests(unittest.TestCase):
    """The PROCESS EXIT CODE, which is the whole of what a caller outside this process observes.

    The single-file invocations are one table (the codes are a closed set whose meanings are easy to
    collapse); the two `--all` invocations stay separate because each builds a throwaway repository.
    """

    def _run(self, **kw) -> int:
        ns = argparse.Namespace(
            phase="author", all=False, legacy=False, agent=False, path=None
        )
        for k, v in kw.items():
            setattr(ns, k, v)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = L.run_lint(ns)
        return rc

    #: (case, the kwargs to override on the namespace, the expected PROCESS EXIT CODE, why this row
    #: exists)
    EXITS = (
        (
            "a conforming plan file",
            {"path": str(CONFORMING_ORCHESTRATOR)},
            0,
            "THE POSITIVE ROW: a clean lint must exit 0, or every CI step and pre-commit hook that "
            "runs `aw ipd lint` fails on a correct tree. Every nonzero row is vacuous while this is "
            "broken",
        ),
        (
            "a path that does not exist",
            {"path": str(REPO_ROOT / "does-not-exist.md")},
            2,
            "USAGE errors exit 2, NOT 1: the distinction is the whole point of this table. 1 means "
            "`the plan is nonconforming`, 2 means `I could not evaluate anything`, and collapsing "
            "them makes a typo'd path indistinguishable from a real lint failure",
        ),
        (
            "an unknown --phase value",
            {"path": "x.md", "phase": "bogus"},
            2,
            "the second usage error, and it is checked BEFORE the path is read (this row's path does "
            "not exist either, yet the phase is what decides). A phase silently falling back to a "
            "default would lint at the wrong gate and report success for the wrong question",
        ),
    )

    def test_every_invocation_exits_with_its_documented_code(self):
        """One table over the process exit codes, replacing three tests.

        Each of the three built a namespace, called `run_lint`, and compared one integer.

        Why the table beats the three: the exit codes are a tiny CLOSED SET with a documented meaning
        (0 clean, 1 nonconforming, 2 could-not-evaluate), every caller outside this process sees ONLY
        this integer, and the realistic failure is 2 collapsing into 1 so that a usage mistake starts
        reading as a lint failure. That collapse moves both usage rows at once, which is exactly what
        the accumulated report shows and what three separate integer comparisons do not.

        The two `--all` cases stay separate below: they build a throwaway repository on disk rather
        than pointing at one file.
        """
        wrong = []
        clean_row_broken = False
        for case, kwargs, expected, why in self.EXITS:
            got = self._run(**kwargs)
            if got != expected:
                if expected == 0:
                    clean_row_broken = True
                wrong.append(
                    f"  {case}: expected exit {expected}, got {got}\n"
                    f"    this row exists because: {why}"
                )
        note = ""
        if clean_row_broken:
            note = (
                " NOTE: the CLEAN row is among the failures, so every nonzero row here is vacuous: a "
                "command that never exits 0 satisfies them while failing every CI step on a correct "
                "tree."
            )
        self.assertEqual(
            wrong,
            [],
            f"`aw ipd lint` returned the wrong exit code for {len(wrong)} of {len(self.EXITS)} "
            f"invocations.{note} The codes are a CLOSED SET with documented meanings (0 clean, 1 "
            "nonconforming, 2 could-not-evaluate) and they are the ONLY thing a caller outside this "
            "process sees, so read the grouping: BOTH usage rows moving to 1 means 2 was collapsed "
            "into 1 and a typo'd path or phase now reports as a lint failure, which sends a human "
            f"looking for a defect in a plan that was never read.\n" + "\n".join(wrong),
        )

    def test_all_exits_1_when_errors_present(self):
        """Kept separate: needs materially different setup, a whole throwaway REPOSITORY on disk.

        The table's rows point at one existing file. This builds a `.agents/plans/pending/` tree
        containing a structurally-erroneous IPD to exercise the AGGREGATING `--all` path, whose exit
        code is derived from many results rather than one.
        """
        import tempfile

        root = Path(tempfile.mkdtemp())
        pend = root / ".agents" / "plans" / "pending"
        pend.mkdir(parents=True)
        (pend / "bad.md").write_text(
            "# IPD: bad\n\n- Kind: child\n\n## Goal\n\nno checklist here\n"
        )
        self.assertEqual(self._run(all=True, path=str(root)), 1)

    def test_all_exits_0_when_no_errors(self):
        """Kept separate: the positive half of `--all`, and it also builds a repository.

        A repo whose only plan conforms must exit 0, which is what keeps the aggregation from
        reporting failure for a clean tree. It additionally depends on `ipd_authoring.build_skeleton`
        to produce that plan, so it pins the scaffolder and the linter agreeing.
        """
        import tempfile

        from agent_workflows import ipd_authoring as A

        root = Path(tempfile.mkdtemp())
        pend = root / ".agents" / "plans" / "pending"
        pend.mkdir(parents=True)
        # Use a grammar-conformant filename: aw ipd lint now name-checks plans (IPD-N001, awcheck-03).
        (pend / "20260803-x-01-aaa111-ok.ipd.md").write_text(
            A.build_skeleton(
                kind="child",
                title="ok (Set x, Order 1)",
                author="t",
                when="2026-08-03",
                set_name="x",
                order=1,
            )
        )
        self.assertEqual(self._run(all=True, path=str(root)), 0)


class AgentOutputTests(unittest.TestCase):
    """The `--agent` JSON envelope for a clean run. Not tabulated: its advisory-bearing counterpart
    lives in `DensityAdvisoryLintTests`, beside the fixture that produces an advisory."""

    def test_agent_output_is_agent_v1_jsonl_no_prose(self):
        """Kept separate: asserts the `aw.agent/v1` JSON envelope for a CLEAN run.

        Its subject is the machine-readable record `--agent` prints, not any lint outcome. Its
        advisory-bearing counterpart lives in `DensityAdvisoryLintTests` beside the fixture that
        produces an advisory.
        """
        import json

        p = CONFORMING_ORCHESTRATOR
        ns = argparse.Namespace(
            phase="author", all=False, legacy=False, agent=True, path=str(p)
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            L.run_lint(ns)
        out = buf.getvalue().strip()
        rec = json.loads(out)
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "ipd lint")
        self.assertEqual(rec["outcome"], "clean")
        self.assertEqual(rec["exit"], 0)


class NoDependencyTests(unittest.TestCase):
    """A STRUCTURAL scan of the linter's own imports. Nothing is linted, so there is nothing to tabulate."""

    def test_lint_module_is_stdlib_only(self):
        """Kept separate: a STRUCTURAL scan of the module's own source imports.

        Nothing is linted here. It reads `ipd_lint.py` and checks every import against an allowlist,
        which is what keeps the linter usable in an environment with no third-party packages.
        """
        src = (REPO_ROOT / "agent_workflows" / "ipd_lint.py").read_text(
            encoding="utf-8"
        )
        for line in src.splitlines():
            m = re.match(r"^(?:from|import)\s+([a-zA-Z0-9_.]+)", line.strip())
            if not m:
                continue
            top = m.group(1).split(".")[0]
            self.assertIn(
                top,
                {
                    "__future__",
                    "argparse",
                    "re",
                    "pathlib",
                    "typing",
                    "agent_workflows",
                },
                "unexpected import: " + line,
            )


class NameConformityTests(unittest.TestCase):
    """awcheck Order 03: `aw ipd lint` flags a nonconformant plan FILENAME (IPD-N001).

    ONE table replaces five tests. All five called `L._with_name_check` with a stand-in result, a
    path, and a `legacy` flag, then asserted whether IPD-N001 appeared and what disposition came back.
    Only those three inputs differed.

    `legacy` IS A COLUMN and the INCOMING DISPOSITION IS ANOTHER, which is why this is one table. The
    rule has two independent escape hatches (the `--legacy` flag, which recognizes the old
    hyphenated-date names, and the terminal-directory short-circuit, which never name-checks a plan
    whose result already came back `legacy`), plus one exemption (a path with no `plans/` segment).
    Those interact: the same bad name must be flagged in `pending/` and not in `executed/`, and a
    legacy-STYLE name must be flagged with the flag off and not with it on. Each of those is a
    relationship between two rows, and the two rows that state it are adjacent below. Two of them did
    not exist as tests at all before tabulating, because writing the table made the missing halves
    obvious: `legacy=True` over a name that is not even legacy-recognized, and a legacy-style name
    with the flag OFF.

    EACH ROW ALSO PINS THE RETURNED DISPOSITION, not just the code, because the old tests were
    inconsistent about it and the disposition is what callers act on: flagging a name has to ESCALATE
    a conforming result to error, and every non-flagging path has to leave the incoming disposition
    untouched.

    Why the table beats the five: one guard chain produces every row (terminal short-circuit, then the
    non-plan-path exemption, then the legacy allowance, then the grammar match), and a regression in
    any link changes several answers together. The dangerous direction is the quiet one: a widened
    escape hatch stops names being checked at all, which shows up as rows going clean rather than red.
    """

    #: (case, path to name-check, the `legacy` flag, the incoming disposition, whether IPD-N001 must
    #: fire, the expected returned disposition, why this row exists)
    NAMES = (
        (
            "a nonconformant name in pending/",
            ".aw/records/plans/pending/not-a-grammar.md",
            False,
            S.DISPOSITION_CONFORMING,
            True,
            S.DISPOSITION_ERROR,
            "THE RULE: the filename carries the Set, the Order, and the id6, so a name off-grammar is "
            "a plan the tooling cannot group, order, or resolve by id. Note it ESCALATES an otherwise "
            "conforming result to error rather than merely adding a diagnostic",
        ),
        (
            "a fully grammar-conformant name",
            ".aw/records/plans/pending/20260101-demo-01-aaa111-ok.ipd.md",
            False,
            S.DISPOSITION_CONFORMING,
            False,
            S.DISPOSITION_CONFORMING,
            "THE POSITIVE ROW: `YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md` passes untouched. Every "
            "refusing row is vacuous while this is broken, since a check that rejected every name "
            "satisfies them all and would fail the whole tracked tree",
        ),
        (
            "a recognized LEGACY name with --legacy",
            ".aw/records/plans/pending/2026-01-01-old-hyphenated.md",
            True,
            S.DISPOSITION_CONFORMING,
            False,
            S.DISPOSITION_CONFORMING,
            "pre-cutover names are GRANDFATHERED on request: the flag exists so the historical tree "
            "can be linted for its CONTENT without every file failing on its name",
        ),
        (
            "the SAME legacy name WITHOUT --legacy",
            ".aw/records/plans/pending/2026-01-01-old-hyphenated.md",
            False,
            S.DISPOSITION_CONFORMING,
            True,
            S.DISPOSITION_ERROR,
            "the other half of the row above, and the row that makes the flag mean something: by "
            "DEFAULT even a recognized legacy name is flagged, so the allowance is opt-in rather than "
            "automatic. Without this pairing the flag could be ignored entirely and both rows pass",
        ),
        (
            "--legacy over a name that is not even legacy-recognized",
            ".aw/records/plans/pending/not-a-grammar.md",
            True,
            S.DISPOSITION_CONFORMING,
            True,
            S.DISPOSITION_ERROR,
            "the flag suppresses RECOGNIZED legacy names, not all names. It is an allowance for a "
            "known historical shape, not a blanket off switch, which is the difference between "
            "linting the old tree and not linting names at all",
        ),
        (
            "a path with no `plans/` segment",
            "tests/fixtures/not-a-grammar.md",
            False,
            S.DISPOSITION_CONFORMING,
            False,
            S.DISPOSITION_CONFORMING,
            "the grammar governs PLANS. A fixture or arbitrary document is exempt, or this test file's "
            "own fixtures would fail the linter that reads them",
        ),
        (
            "a bad name in a TERMINAL directory whose result is already `legacy`",
            ".aw/records/plans/executed/bad-name.md",
            False,
            S.DISPOSITION_LEGACY,
            False,
            S.DISPOSITION_LEGACY,
            "THE SHORT-CIRCUIT: a result that came back `legacy` is not name-checked and its "
            "disposition is preserved. Renaming an executed plan would break every citation pointing "
            "at it, so the historical tree is left alone. Same bad name as the first row, opposite "
            "answer, which is what makes the DISPOSITION column the operative difference",
        ),
    )

    def test_every_path_and_flag_combination_gets_its_name_verdict(self):
        wrong = []
        positive_row_broken = False
        for case, path, legacy, incoming, fires, expected_disp, why in self.NAMES:
            diags, disp = L._with_name_check(
                L.LintResult(disposition=incoming, diagnostics=[]),
                Path(path),
                legacy=legacy,
            )
            found = [d for d in diags if d.code == L.C_NAME]
            problems = []
            if fires and not found:
                problems.append(
                    f"expected {L.C_NAME}; got diagnostics {[d.render(path) for d in diags]!r}"
                )
            if not fires and found:
                if (
                    expected_disp == S.DISPOSITION_CONFORMING
                    and incoming == expected_disp
                ):
                    positive_row_broken = True
                problems.append(
                    f"{L.C_NAME} must NOT fire here; it did: "
                    f"{[d.render(path) for d in found]!r}"
                )
            if disp != expected_disp:
                problems.append(
                    f"expected the returned disposition {expected_disp!r} (incoming was "
                    f"{incoming!r}), got {disp!r}"
                )
            if problems:
                wrong.append(
                    f"  {case} (legacy={legacy}, incoming={incoming!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if positive_row_broken:
            note = (
                " NOTE: a conformant name is among the flagged, so the grammar match itself is "
                "broken and every refusing row here is vacuous; in that state `aw ipd lint` fails "
                "every correctly-named plan in the tree."
            )
        self.assertEqual(
            wrong,
            [],
            f"the filename check was wrong for {len(wrong)} of {len(self.NAMES)} path/flag "
            f"combinations.{note} One guard chain produces every row (terminal short-circuit, then "
            "the non-plan-path exemption, then the legacy allowance, then the grammar match), so read "
            "the grouping: if the two rows sharing the legacy-STYLE name stopped disagreeing, the "
            "`--legacy` flag is being ignored in one direction or the other, and if the two rows "
            "sharing `not-a-grammar.md` stopped disagreeing, the terminal short-circuit did. FIX: "
            "rows going CLEAN is the quiet failure, because a widened escape hatch means names stop "
            f"being checked at all and nothing goes red to say so.\n"
            + "\n".join(wrong),
        )


class DensityAdvisoryLintTests(unittest.TestCase):
    """Order 07: Per-E-item density heuristic surfacing in linter (spec Section 8.1)."""

    def _dense_child(self) -> str:
        # A conforming child IPD with a multi-concern E-item
        doc = _conforming_child()
        # Replace E-01 action with a multi-concern action
        return doc.replace(
            "- [ ] E-01 do a thing.",
            "- [ ] E-01 add an append-only tamper-evident ledger AND crash recovery AND a 12-class evidence validator",
        )

    def _ready_to_execute(self, text: str) -> str:
        """Make a fixture pass the ready-to-execute gate, so only the DENSITY advisory remains."""
        text = text.replace("Status: to-review", "Status: approved")
        text = text.replace(
            "- 2026-08-03 to-review (tester): created.",
            "- 2026-08-03 approved (tester): approved.",
        )
        text = text.replace(
            "- Author: tester", "- Author: tester\n- Approval: tester 2026-08-03"
        )
        # Order oorry1: a ready-to-execute plan needs a Scope-Paths value; declare a real allowlist so
        # these rows isolate the DENSITY advisory (Z602) they are actually about.
        return text.replace(
            "- Scope: sample.",
            "- Scope: sample.\n- Scope-Paths: agent_workflows/foo.py",
        )

    #: (case, whether the E-item bundles multiple concerns, the lint PHASE, how many Z602 advisories
    #: are expected, why this row exists)
    DENSITY = (
        (
            "an E-item bundling three concerns with AND",
            True,
            "author",
            1,
            "THE HEURISTIC: `add a ledger AND crash recovery AND a validator` is three steps wearing "
            "one id, which defeats the E/V bijection because one V cannot verify three things "
            "independently. Surfaced as an ADVISORY because density is a judgement, not a defect",
        ),
        (
            "a single-concern E-item",
            False,
            "author",
            0,
            "THE POSITIVE ROW: an ordinary item must produce NO advisory. A heuristic that fired on "
            "everything would satisfy the row above while making the advisory channel pure noise, "
            "which is how advisories get ignored",
        ),
        (
            "the SAME dense item on a ready-to-execute plan at PRE-EXECUTION",
            True,
            "pre-execution",
            1,
            "AN ADVISORY MUST NOT GATE, and the PHASE is what shows it: the same finding that is "
            "informational at author must still be informational at the gate `aw ipd begin` consults, "
            "or a heuristic guess would block execution. Every row here therefore also asserts the "
            "disposition is CONFORMING with zero blocking diagnostics",
        ),
    )

    def test_the_density_heuristic_advises_without_ever_gating(self):
        """One table over the density advisory, replacing three tests.

        THE PHASE IS A COLUMN because the claim that matters is not that the heuristic fires but that
        firing NEVER changes the outcome. That is a statement about the same finding at two phases, so
        the author rows and the pre-execution row have to share a table; apart, the third test read as
        a separate fact rather than as the reason the first two are safe.

        Why the table beats the three: one detector plus one channel assignment produces every row.
        All rows losing their advisory means the detector stopped firing; any row gaining a blocking
        DIAGNOSTIC means the channel assignment broke and a heuristic guess now refuses plans. Each row
        asserts both channels for exactly that reason.
        """
        wrong = []
        positive_row_broken = False
        for case, dense, phase, count, why in self.DENSITY:
            text = self._dense_child() if dense else _conforming_child()
            if phase != "author":
                text = self._ready_to_execute(text)
            res = L.lint_text(text, checkpoint=phase, directory="pending")
            found = [a for a in res.advisories if a.code == L.C_SIZE_DENSITY]
            problems = []
            if len(found) != count:
                if count == 0:
                    positive_row_broken = True
                problems.append(
                    f"expected {count} IPD-Z602 advisory/advisories, got {len(found)}: "
                    f"{[a.render('t') for a in found]!r}"
                )
            if res.diagnostics:
                problems.append(
                    "an advisory must NEVER produce a blocking diagnostic, and this row has "
                    f"{[d.render('t') for d in res.diagnostics]!r}"
                )
            if res.disposition != S.DISPOSITION_CONFORMING or not res.passing:
                problems.append(
                    f"expected a CONFORMING, passing result; got {res.disposition!r}, "
                    f"passing={res.passing}"
                )
            for advisory in found:
                if "E-01" not in advisory.message:
                    problems.append(
                        f"the advisory must NAME the item it is about; it said "
                        f"{advisory.message!r}"
                    )
                if "multi-concern" not in advisory.message:
                    problems.append(
                        f"the advisory must say WHY (multi-concern); it said "
                        f"{advisory.message!r}"
                    )
                if advisory.line <= 0:
                    problems.append(
                        f"the advisory must carry a real line number so an editor can jump to it; "
                        f"got line {advisory.line}"
                    )
            if problems:
                wrong.append(
                    f"  {case} (phase={phase}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if positive_row_broken:
            note = (
                " NOTE: the single-concern row is among the failures, so the heuristic is firing on "
                "ordinary items and the advisory channel has become noise, which is how advisories "
                "come to be ignored entirely."
            )
        self.assertEqual(
            wrong,
            [],
            f"the density heuristic was wrong for {len(wrong)} of {len(self.DENSITY)} plans."
            f"{note} One detector plus one channel assignment produces every row, so read the "
            "grouping: ALL rows losing their advisory means the detector stopped firing, while ANY "
            "row gaining a blocking diagnostic means the channel assignment broke. FIX: the second is "
            "far worse than the first. Density is a JUDGEMENT about how work is split, and a judgement "
            "that blocks would refuse plans over a heuristic guess at the very gate `aw ipd begin` "
            f"consults.\n" + "\n".join(wrong),
        )

    def test_cli_agent_output_emits_advisory_record_with_clean_outcome(self):
        """Kept separate: asserts over the CLI's JSON RECORD, not over a LintResult.

        The subject is the `aw.agent/v1` envelope `run_lint` prints (its schema, cmd, outcome, exit,
        and finding count), which reaches an advisory only after the whole CLI layer has decided how to
        represent one. A table row over `lint_text` cannot see any of that.
        """
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            plan_file = Path(td) / "20260822-test-01-abc123-dense.ipd.md"
            plan_file.write_text(self._dense_child(), encoding="utf-8")

            ns = argparse.Namespace(
                phase="author", all=False, legacy=False, agent=True, path=str(plan_file)
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = L.run_lint(ns)

            self.assertEqual(rc, 0)
            rec = json.loads(buf.getvalue().strip())
            self.assertEqual(rec["schema"], "aw.agent/v1")
            self.assertEqual(rec["cmd"], "ipd lint")
            self.assertEqual(rec["outcome"], "clean")
            self.assertEqual(rec["exit"], 0)
            self.assertEqual(rec["findings"], 1)
            self.assertTrue(
                any(d["rule"] == "IPD-Z602" for d in rec.get("diagnostics", []))
            )

    def test_cli_human_output_emits_advisory_line(self):
        """Kept separate: asserts over HUMAN TERMINAL OUTPUT under two --detail settings.

        Same reason as the agent-output test, plus its own mode pair: by default the item row says
        `advisory` WITHOUT the rule id, and `--detail` adds the indented `IPD-Z602` line. That is a
        claim about rendering verbosity, not about whether the finding exists.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            plan_file = Path(td) / "20260822-test-01-abc123-dense.ipd.md"
            plan_file.write_text(self._dense_child(), encoding="utf-8")

            # Default: displays "advisory" on the item row without detailed sub-lines
            ns = argparse.Namespace(
                phase="author",
                all=False,
                legacy=False,
                agent=False,
                no_color=True,
                detail=False,
                path=str(plan_file),
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = L.run_lint(ns)

            self.assertEqual(rc, 0)
            out = buf.getvalue()
            self.assertIn("advisory", out)
            self.assertNotIn("IPD-Z602", out)

            # With --detail / --long: displays indented finding details
            ns_detail = argparse.Namespace(
                phase="author",
                all=False,
                legacy=False,
                agent=False,
                no_color=True,
                detail=True,
                path=str(plan_file),
            )
            buf_detail = io.StringIO()
            with redirect_stdout(buf_detail):
                rc_detail = L.run_lint(ns_detail)

            self.assertEqual(rc_detail, 0)
            out_detail = buf_detail.getvalue()
            self.assertIn("advisory", out_detail)
            self.assertIn("IPD-Z602", out_detail)


class CitationAnchorAdvisoryTests(unittest.TestCase):
    """citeanchor `mzc019`: the citation-anchor advisory (IPD-C801, spec Section 10.2).

    THE DETECTOR'S DISCRIMINATION IS THE SUBJECT, not merely that it fires. The naive form of this
    rule ("is there a backticked token on the same line?") was measured over the whole pending corpus
    and flagged 3 of 2304 structural citations, because a citation is normally written in backticks
    itself and a file path is itself a dotted token. That form could not flag the `216rgg` cell this
    rule was written from. So the rows below pin the EXCLUSIONS that make the difference (the citation
    itself, a bare path, a bare line range) alongside the positives, and a separate test reproduces
    `216rgg`'s real drifted citations as the anti-regression case.
    """

    #: The date used for a POST-cutover fixture. Derived from the constant so moving the cutover
    #: forward cannot silently turn every row below into a vacuous pass.
    POST_CUTOVER_DATE = "{0}-{1}-{2}".format(
        int(L.CITATION_ANCHOR_CUTOVER_DATE[:4]) + 1,
        L.CITATION_ANCHOR_CUTOVER_DATE[4:6],
        L.CITATION_ANCHOR_CUTOVER_DATE[6:8],
    )

    def _plan(self, body: str, *, date=None) -> str:
        """A conforming child plan whose Findings section carries ``body``."""
        text = _conforming_child().replace(
            "## Findings\n\n- x", "## Findings\n\n" + body
        )
        return text.replace(
            "- Date: 2026-08-03",
            "- Date: " + (date if date is not None else self.POST_CUTOVER_DATE),
        )

    def _advisories(self, body: str, *, date=None, phase="author"):
        text = self._plan(body, date=date)
        res = L.lint_text(text, checkpoint=phase, directory="pending")
        return res, [a for a in res.advisories if a.code == L.C_CITATION_ANCHOR]

    #: (case, the Findings body, how many IPD-C801 advisories are expected, why this row exists)
    ANCHORS = (
        (
            "a bare file:line with nothing beside it",
            "- the defect is at foo.py:123 and must be fixed",
            1,
            "THE BASE CASE: an offset alone is the reference type that expires. If this row stops "
            "firing the rule is dead and every other row passes vacuously",
        ),
        (
            "a QUALIFIED symbol and no offset at all",
            "- the defect is in `check_engine.check_collisions` and must be fixed",
            0,
            "THE COMPLIANT (a) FORM: a symbol survives insertion, deletion and a file move, so it "
            "needs no offset and must draw nothing",
        ),
        (
            "a qualified symbol PLUS a trailing offset",
            "- the defect is in `check_engine.check_collisions` (`check_engine.py:897-905`)",
            0,
            "THE RULE KEYS ON A MISSING ANCHOR, NOT ON THE DIGITS. Section 10.2 (c) blesses an "
            "offset appended to a symbol, so a rule that fired here would be telling authors to "
            "delete useful information",
        ),
        (
            "a quoted CONTENT STRING beside the offset",
            "- the branch whose message contains `different type` at `check_engine.py:897-905`",
            0,
            "THE COMPLIANT (b) FORM, for a construct with no symbol of its own: the emitted literal "
            "is greppable, which is exactly what an offset is not",
        ),
        (
            "an offset whose only companion is a BARE PATH in backticks",
            "- see `check_engine.py` at `check_engine.py:120` for detail",
            1,
            "ANTI-REGRESSION FOR THE MEASURED 99% FALSE-NEGATIVE: a backticked bare path is what the "
            "citation ALREADY names, so counting it as an anchor is what made the naive form flag 3 "
            "of 2304 citations. This row is the difference between a working rule and a decorative one",
        ),
        (
            "an offset whose only companion is a BARE LINE RANGE in backticks",
            "- the within-type branch (`:906-915`) at `check_engine.py:897`",
            1,
            "THE SAME FAILURE IN ITS OTHER COMMON SHAPE: the filename-less continuation form is a "
            "SECOND offset, not an anchor, and the corpus carries it in bulk. Dropping this row "
            "restores the false negative for every multi-location citation",
        ),
        (
            "a citation inside a FENCED block",
            "```text\nfoo.py:123\n```",
            0,
            "THE FENCE EXEMPTION, obtained by reusing `_structural_lines` rather than re-implementing "
            "fence detection. A quoted diagnostic's offset is the FACT being reported (Section 10.2's "
            "line-as-subject exception), so flagging it would make the rule fire on its own evidence",
        ),
        (
            "a citation inside a 4-space INDENTED block",
            '    File "foo.py:123", line 123, in main',
            0,
            "THE OTHER EXCLUDED REGION, pinned separately because a pasted traceback is indented "
            "rather than fenced and is the single most likely false positive in a real plan",
        ),
        (
            "a bare offset on a plan dated BEFORE the cutover",
            "- the defect is at foo.py:123 and must be fixed",
            0,
            "E-04's SUPPRESSION, as a column on the same body as the base row: the identical text "
            "flags post-cutover and is silent pre-cutover. Without this the first run reports roughly "
            "a thousand advisories on plans nobody can edit, and a rule that fires mostly on "
            "untouchable history is one every reader learns to skip",
        ),
    )

    def test_the_rule_flags_a_missing_anchor_and_never_the_digits(self):
        """One table over the detector, its exclusions, and its date gate.

        THE EXCLUSIONS SHARE THE TABLE WITH THE POSITIVES DELIBERATELY. The interesting property is
        not that a bare offset flags, it is that a bare PATH and a bare RANGE do not rescue it while a
        SYMBOL does. Those are four answers from one candidate-anchor set, so they belong in one table;
        apart, each read as a separate fact rather than as the discrimination the rule is made of.

        Every row also asserts the advisory NEVER reaches `diagnostics` and the disposition stays
        CONFORMING, because a citation-form heuristic over prose will have false positives and a gate
        that false-positives trains authors to bypass it.
        """
        wrong = []
        base_row_broken = False
        for case, body, count, why in self.ANCHORS:
            date = "2026-08-03" if "BEFORE the cutover" in case else None
            res, found = self._advisories(body, date=date)
            problems = []
            if len(found) != count:
                if count == 1 and "bare file:line with nothing" in case:
                    base_row_broken = True
                problems.append(
                    f"expected {count} {L.C_CITATION_ANCHOR} advisory/advisories, got "
                    f"{len(found)}: {[a.render('t') for a in found]!r}"
                )
            if res.diagnostics:
                problems.append(
                    "this rule must NEVER produce a blocking diagnostic, and this row has "
                    f"{[d.render('t') for d in res.diagnostics]!r}"
                )
            if res.disposition != S.DISPOSITION_CONFORMING or not res.passing:
                problems.append(
                    f"expected a CONFORMING, passing result; got {res.disposition!r}, "
                    f"passing={res.passing}"
                )
            for advisory in found:
                if advisory.line <= 0:
                    problems.append(
                        "the advisory must carry a real line number so an editor can jump to it; "
                        f"got line {advisory.line}"
                    )
                if "durable anchor" not in advisory.message:
                    problems.append(
                        f"the advisory must say WHAT is wrong; it said {advisory.message!r}"
                    )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if base_row_broken:
            note = (
                " NOTE: the base row is among the failures, so the detector is not firing at all and "
                "every zero-expecting row below it is passing vacuously."
            )
        self.assertEqual(
            wrong,
            [],
            f"the citation-anchor rule was wrong for {len(wrong)} of {len(self.ANCHORS)} rows."
            f"{note} One candidate-anchor set plus one date gate produces every row, so read the "
            "grouping: the BARE PATH and BARE RANGE rows failing together means the exclusion set was "
            "weakened back toward the naive 'is a backtick nearby' test that measured 3 of 2304 "
            "citations on this corpus, while the SYMBOL rows failing means the rule started keying on "
            "the digits instead of on the missing anchor and is now telling authors to delete useful "
            f"information.\n" + "\n".join(wrong),
        )

    def test_the_216rgg_drifted_citations_flag_while_its_compliant_bullet_does_not(
        self,
    ):
        """Kept separate: the subject is one REAL plan's actual text, not a synthetic fixture.

        This is the headline case the rule exists for. Plan `216rgg` was approved, twice reviewed, and
        every core anchor in it had drifted by the time it executed: its cross-type citation landed on
        a dictionary initialization and its `doctor.py` citation on a blank line. A detector that
        reports nothing here has reproduced the defect and must not ship, which is why this is an
        assertion and not a comment.

        THE THIRD CASE IS THE POINT AS MUCH AS THE FIRST TWO. That plan's own E-01 bullet names
        `check_engine.check_collisions` beside its offset, which is the compliant (a)+(c) form, so a
        rule that flagged it would be flagging correct authoring.
        """
        cases = (
            (
                "its Findings row, whose Location cell carries only the bare offset",
                "| F-1 | HIGH | `check_engine.py:897-905` | The cross-type branch emits 38 findings "
                "at severity `error`. | `check_collisions` run |",
                1,
                "A TABLE ROW IS JUDGED PER CELL. This row's Evidence cell carries "
                "`check_collisions`, so a line-scoped test lets one column vouch for another "
                "column's bare offset, which is the same 'symbol nearby' fallacy at row scale",
            ),
            (
                "its prose sentence carrying two bare offsets",
                "A THIRD DEFECT: `doctor.py:530` hardcodes `include_retired=True` while "
                "`check_engine.py:1760` passes a flag defaulting to `False`.",
                2,
                "BOTH offsets must be reported, not just the first: each is a separate expiring "
                "reference, and `include_retired` is a BARE identifier rather than a qualified one, "
                "so it must not be accepted as an anchor for either",
            ),
            (
                "its E-01 bullet, which names the symbol beside the offset",
                "- E-01 REMOVE THE CROSS-TYPE EMISSION from `check_engine.check_collisions` "
                "(`check_engine.py:897-905`).",
                0,
                "THE COMPLIANT FORM FROM THE SAME PLAN: the rule must distinguish the parts of a "
                "real plan that are right from the parts that are wrong, or it is not measuring "
                "anchor form at all",
            ),
        )
        wrong = []
        for case, body, count, why in cases:
            _res, found = self._advisories(body)
            if len(found) != count:
                wrong.append(
                    f"  {case}:\n"
                    f"    - expected {count} advisory/advisories, got {len(found)}: "
                    f"{[a.render('t') for a in found]!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            "the rule mishandled plan `216rgg`'s own citations, which is the case it was written "
            "from. FIX: if the two drifted rows stopped flagging, the candidate-anchor set now "
            "accepts something it must not (a bare identifier, a bare path, or the citation itself); "
            "if the E-01 row started flagging, it no longer accepts a qualified symbol.\n"
            + "\n".join(wrong),
        )

    def test_the_detector_discriminates_on_the_real_corpus_with_the_gate_disabled(self):
        """Kept separate: measures the detector over the tracked tree with the date gate bypassed.

        THE MEASUREMENT IS THE ASSERTION. A rule that reports near-zero on this corpus has reproduced
        the very defect the rule exists to address, because 90% of these plans demonstrably anchor by
        offset alone. The bound is a wide BAND rather than a fixed number on purpose: the corpus moves
        hourly as agents author and execute plans, so pinning an exact count would make this test a
        maintenance burden that gets deleted, while a band still fails loudly if the detector
        regresses to the naive form (measured: 3 of 2304, 0%) or degenerates into flagging everything.
        """
        # THE GLOB IS WIDENED PAST `pending/`, which is the remedy the floor's own note prescribes
        # rather than lowering the floor a second time. `pending/` is a WORK QUEUE: it shrinks every
        # time a plan executes, so a corpus-size assertion over it measures how much work is
        # outstanding, not whether the detector discriminates. Measured 2026-09-24: it fell to 150
        # citations and then to 73 across two batches of finalizations, failing twice for the same
        # non-reason. Every disposition directory carries the same prose and the same citation habits,
        # so reading them all keeps the denominator stable as plans move between directories, which is
        # exactly the property this assertion needs and `pending/` alone cannot provide.
        plans = sorted(SOURCE_PLANS.glob("*/*.ipd.md"))
        self.assertTrue(plans, "expected a nonempty pending corpus to measure against")
        citations = 0
        flagged = 0
        for path in plans:
            text = path.read_text(encoding="utf-8")
            for _lineno, line in L._structural_lines(text):
                for unit in L._citation_units(line):
                    citations += len(L._CITATION_RE.findall(unit))
                    if L._CITATION_RE.search(unit) and not L._has_durable_anchor(unit):
                        flagged += len(L._CITATION_RE.findall(unit))
        # THE FLOOR IS 100, NOT 500 (lowered 2026-09-24; backlog `24e5zv`). This assertion's own
        # docstring above says the bound is "a wide BAND rather than a fixed number on purpose"
        # because "the corpus moves hourly ... while pinning an exact count would make this test a
        # maintenance burden that gets deleted" - and then the floor was a fixed 500, which is the
        # very thing it warned against. It failed on 2026-09-24 reporting `150 not greater than 500`,
        # NOT because the detector regressed but because run `run-20260924T050407Z-3108751` executed
        # a batch of plans and the PENDING corpus shrank by design. A test that goes red when the
        # queue is worked down is measuring throughput, not the detector.
        #
        # WHY 100 IS STILL A REAL FLOOR: the purpose of this bound is only to guarantee the
        # denominator is large enough for the percentage below to mean something. At 100 citations a
        # single flagged unit moves the ratio by 1 point, so the 5-90% band is still a genuine
        # measurement rather than a rounding artifact. The BAND is the assertion; this is scaffolding
        # for it.
        self.assertGreater(
            citations,
            100,
            f"expected the pending corpus to carry a substantial body of file:line citations, found "
            f"{citations}; with too few, the ratio below is not a measurement of anything. If the "
            "pending queue has genuinely been worked down to almost nothing, this test has no corpus "
            "to measure and should be re-pointed at a wider glob rather than have its floor lowered "
            "again.",
        )
        pct = 100.0 * flagged / citations
        self.assertTrue(
            5.0 <= pct <= 90.0,
            f"the detector flagged {flagged} of {citations} citations ({pct:.0f}%) on the real "
            "corpus, which is outside the 5-90% band this rule must land in. FIX: a result near ZERO "
            "means the candidate-anchor set has been weakened back to 'is there a backticked token "
            "nearby', which measured 3 of 2304 (0%) and could not flag even the `216rgg` cell this "
            "rule was written from. A result near 100% means the exclusions broke and a compliant "
            "symbol anchor no longer counts, which would make the advisory pure noise.",
        )

    def test_the_new_advisory_is_visible_in_default_human_output(self):
        """Kept separate: asserts over HUMAN TERMINAL OUTPUT, and over a mode PAIR with IPD-Z602.

        E-05's whole reason. Without it the finding collapses into the single word `advisory` on the
        status line with no code and no message unless `--detail` is passed, so the nudge reaches an
        author who does not know to pass a flag they have no reason to suspect. The `IPD-Z602` half of
        the pair is not decoration: the fix had to be NARROW, and the only way to state "narrow" is to
        assert that the OTHER advisory's default quietness is unchanged.
        """
        import tempfile

        def render(text, *, detail):
            with tempfile.TemporaryDirectory() as td:
                d = Path(td) / ".aw" / "records" / "plans" / "pending"
                d.mkdir(parents=True)
                plan = d / "20260803-x-01-abc123-sample.ipd.md"
                plan.write_text(text, encoding="utf-8")
                ns = argparse.Namespace(
                    phase="author",
                    all=False,
                    legacy=False,
                    agent=False,
                    no_color=True,
                    detail=detail,
                    path=str(plan),
                )
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = L.run_lint(ns)
                return rc, buf.getvalue()

        anchored = self._plan("- the defect is at foo.py:123 and must be fixed")
        rc, out = render(anchored, detail=False)
        self.assertEqual(rc, 0, "the advisory must not move the exit status")
        self.assertIn(
            L.C_CITATION_ANCHOR,
            out,
            "the new advisory's CODE must appear in DEFAULT human output with no extra flag; "
            f"without it the nudge reaches nobody. Output was:\n{out}",
        )
        self.assertIn(
            "durable anchor",
            out,
            f"the advisory's MESSAGE must appear too, not just its code. Output was:\n{out}",
        )

        dense = _conforming_child().replace(
            "- [ ] E-01 do a thing.",
            "- [ ] E-01 add an append-only ledger AND crash recovery AND a 12-class validator",
        )
        rc_quiet, quiet = render(dense, detail=False)
        self.assertEqual(rc_quiet, 0)
        self.assertIn("advisory", quiet)
        self.assertNotIn(
            L.C_SIZE_DENSITY,
            quiet,
            "IPD-Z602's default quietness must be UNCHANGED. Making every advisory verbose by "
            "default would change unrelated output for every plan in the tree, which is a separate "
            f"decision with its own blast radius. Output was:\n{quiet}",
        )
        rc_detail, detailed = render(dense, detail=True)
        self.assertEqual(rc_detail, 0)
        self.assertIn(
            L.C_SIZE_DENSITY,
            detailed,
            "--detail must still reveal IPD-Z602, or the narrow fix broke the general path.",
        )


def _with_scope_paths(text: str, value) -> str:
    """Return ``text`` with a Scope-Paths metadata line set to ``value`` (or removed if None)."""
    out = []
    for ln in text.splitlines():
        if ln.startswith("- Scope-Paths:"):
            continue  # drop any existing one first
        out.append(ln)
        if value is not None and ln.startswith("- Scope:"):
            out.append("- Scope-Paths: " + value)
    return "\n".join(out) + "\n"


def _approved(text: str) -> str:
    """Make a fixture ready-to-execute: Status approved + the required Approval field.

    Only the METADATA-block Status (before the first H2) is changed, so an OQ's own
    `- Status: open` line later in the document is left intact.
    """
    out = []
    in_meta = True
    for ln in text.splitlines():
        if ln.startswith("## "):
            in_meta = False
        if in_meta and ln.startswith("- Status:"):
            out.append("- Status: approved")
            continue
        out.append(ln)
        if in_meta and ln.startswith("- Author:"):
            out.append("- Approval: 2026-08-24, human: approved")
    return "\n".join(out) + "\n"


class ScopePathsCheckpointTests(unittest.TestCase):
    """Order oorry1: conditional Scope-Paths enforcement (IPD-M106) in the CHECKPOINT layer.

    ONE table replaces six tests. All six built a plan with some `Scope-Paths` value (or none), linted
    it at some phase in some directory, and asserted whether IPD-M106 appeared as a BLOCKING
    diagnostic, as an ADVISORY, or not at all.

    THE OUTCOME IS THREE-VALUED, NOT A BOOL, and that is why every row states the blocking and the
    advisory channel separately rather than being weakened to one assertion. A fieldless
    ready-to-execute plan BLOCKS; the `grandfathered` marker is deliberately ADVISORY, meaning visible
    but non-blocking; and the author phase is SILENT. Collapsing advisory into either neighbour would
    erase the whole design: silent would let the historical tree pass unnoticed, blocking would stop
    it being executed at all.

    THE PHASE AND THE DIRECTORY ARE COLUMNS. The requirement fires at the ready-to-execute gate AND by
    STATUS, so an approved plan is blocked at `review-finalize` too, which is a separate trigger from
    the phase and needs its own row beside the `pre-execution` one. And a terminal-directory plan
    short-circuits to `legacy` before this rule is reached, which is the non-retroactivity guarantee.

    Why the table beats the six: one predicate over (phase, status, value) produces every row, and the
    realistic failures are a trigger being dropped (rows go silent, so unscoped plans execute) or the
    grandfathered marker losing its exemption (the historical tree becomes unexecutable). Either moves
    several rows at once, and reading which rows moved is the diagnosis.
    """

    #: (case, the Scope-Paths value or None to omit the field, whether to make the plan
    #: ready-to-execute, the phase, the directory, the expected outcome (`blocking` / `advisory` /
    #: `silent`), the expected disposition, why this row exists)
    SCOPES = (
        (
            "no field at all, at the AUTHOR phase",
            None,
            False,
            "author",
            "pending",
            "silent",
            S.DISPOSITION_CONFORMING,
            "SILENT WHILE AUTHORING: the allowlist is what a plan will be permitted to touch when it "
            "runs, and it cannot be known until the plan is written. Demanding it at author would make "
            "every fresh scaffold nonconforming",
        ),
        (
            "no field at all, on an APPROVED plan at PRE-EXECUTION",
            None,
            True,
            "pre-execution",
            "pending",
            "blocking",
            S.DISPOSITION_ERROR,
            "THE RULE: a plan about to execute must declare what it may touch, because that allowlist "
            "is what the runner's scope gate reconciles the actual diff against. No field means no "
            "gate, so it BLOCKS rather than warns",
        ),
        (
            "no field at all, on an APPROVED plan at REVIEW-FINALIZE",
            None,
            True,
            "review-finalize",
            "pending",
            "blocking",
            S.DISPOSITION_ERROR,
            "THE SECOND TRIGGER, independent of the phase: the requirement fires by STATUS too, so an "
            "approved plan cannot slip past by being linted at some OTHER checkpoint. Without this row "
            "the rule would be a single-phase check and any other phase would be a bypass",
        ),
        (
            "the `grandfathered` marker on an APPROVED plan at PRE-EXECUTION",
            "grandfathered",
            True,
            "pre-execution",
            "pending",
            "advisory",
            S.DISPOSITION_CONFORMING,
            "THE THREE-VALUED MIDDLE, and the row the outcome column exists for: the marker is "
            "VISIBLE but NON-BLOCKING, so pre-cutover plans remain executable while still being "
            "reported. Silent here would hide the whole historical backlog; blocking would freeze it",
        ),
        (
            "a real, grammar-valid allowlist on an APPROVED plan at PRE-EXECUTION",
            "agent_workflows/foo.py, tests/test_foo.py",
            True,
            "pre-execution",
            "pending",
            "silent",
            S.DISPOSITION_CONFORMING,
            "THE POSITIVE ROW: a comma-separated list of repo-relative paths satisfies the gate "
            "outright. Every blocking row is vacuous while this is broken, since a rule that refused "
            "every value satisfies them all and no plan could ever execute",
        ),
        (
            "the SCAFFOLD PLACEHOLDER left in place, on an APPROVED plan at PRE-EXECUTION",
            "TODO (comma-separated repo-relative paths or pathspecs)",
            True,
            "pre-execution",
            "pending",
            "blocking",
            S.DISPOSITION_ERROR,
            "planprio lkexaw E-12: the scaffold's placeholder is NOT a path. It used to parse as one "
            "relative entry, so a plan approved with the placeholder still in place linted clean and "
            "executed with no real fence for the scope gate to reconcile against",
        ),
        (
            "an ABSOLUTE path as the allowlist, on an APPROVED plan at PRE-EXECUTION",
            "/etc/passwd",
            True,
            "pre-execution",
            "pending",
            "blocking",
            S.DISPOSITION_ERROR,
            "the value is GRAMMAR-VALIDATED, not merely present: paths must be repo-relative. An "
            "absolute path is exactly the value whose acceptance would make the scope gate meaningless "
            "while looking declared",
        ),
        (
            "no field at all on a plan in the EXECUTED directory",
            None,
            False,
            "pre-execution",
            "executed",
            "silent",
            S.DISPOSITION_LEGACY,
            "NON-RETROACTIVITY: a terminal-directory record short-circuits to `legacy` before this "
            "rule is reached, so the entire pre-cutover executed tree is never blocked. Same missing "
            "field as the blocking rows, opposite answer, which is what makes the DIRECTORY column the "
            "operative difference",
        ),
    )

    def test_every_phase_and_value_reaches_its_three_valued_outcome(self):
        wrong = []
        positive_row_broken = False
        for (
            case,
            value,
            approved,
            phase,
            directory,
            outcome,
            disposition,
            why,
        ) in self.SCOPES:
            base = _executed_child() if directory == "executed" else _conforming_child()
            text = _with_scope_paths(base, value)
            if approved:
                text = _approved(text)
            res = L.lint_text(text, checkpoint=phase, directory=directory)
            blocking = [d for d in res.diagnostics if d.code == L.C_SCOPE_PATHS]
            advisory = [d for d in res.advisories if d.code == L.C_SCOPE_PATHS]
            got = "blocking" if blocking else ("advisory" if advisory else "silent")
            problems = []
            if got != outcome:
                if outcome == "silent" and value and value != "grandfathered":
                    positive_row_broken = True
                problems.append(
                    f"expected the outcome {outcome!r}, got {got!r} (blocking="
                    f"{[d.render('t') for d in blocking]!r}, advisory="
                    f"{[d.render('t') for d in advisory]!r})"
                )
            if res.disposition != disposition:
                problems.append(
                    f"expected disposition {disposition!r}, got {res.disposition!r}; all "
                    f"diagnostics: {[d.render('t') for d in res.diagnostics]!r}"
                )
            if problems:
                shown = "no field" if value is None else repr(value)
                wrong.append(
                    f"  {case}\n    (value={shown}, approved={approved}, phase={phase!r}, "
                    f"directory={directory!r}):\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if positive_row_broken:
            note = (
                " NOTE: a VALID allowlist is among the failures, so the grammar check itself is "
                "broken and every blocking row here is vacuous; in that state no plan can pass the "
                "gate at all."
            )
        self.assertEqual(
            wrong,
            [],
            f"IPD-M106 reached the wrong outcome for {len(wrong)} of {len(self.SCOPES)} "
            f"phase/value/directory combinations.{note} The outcome is THREE-VALUED (blocking / "
            "advisory / silent) and one predicate over (phase, status, value) produces every row, so "
            "read the grouping. If the BLOCKING rows went silent, a trigger was dropped and plans can "
            "now execute with no declared scope for the runner's gate to reconcile against. If the "
            "`grandfathered` row went blocking, the pre-cutover tree just became unexecutable. If it "
            "went silent, the historical backlog is now invisible. FIX: the advisory row is the one "
            f"most easily 'simplified' into either neighbour, and both directions are wrong.\n"
            + "\n".join(wrong),
        )

    def test_enforcement_lives_in_the_checkpoint_layer_not_in_metadata(self):
        """Kept separate: calls TWO internal checks directly to locate WHERE the rule lives.

        The table asserts what the composed `lint_text` reports; this asserts that `check_metadata`
        reports NOTHING about Scope-Paths while `check_scope_paths` does, which is a claim about the
        layering rather than about any document's outcome. It matters because a metadata-layer
        enforcement would fire at every phase, destroying the three-valued behavior the table pins.
        """
        fieldless = _with_scope_paths(_conforming_child(), None)
        doc = L.parse(fieldless)
        meta_diags = L.check_metadata(doc, "pending")
        self.assertEqual(
            [d for d in meta_diags if d.code == L.C_SCOPE_PATHS],
            [],
            "Scope-Paths must NOT be enforced in check_metadata",
        )
        approved_doc = L.parse(_approved(fieldless))
        block, _adv = L.check_scope_paths(approved_doc, "pre-execution", "pending")
        self.assertTrue(block, "check_scope_paths must enforce the field at the gate")


class ParenthesizedActorParsesInTheAttributionRegex(unittest.TestCase):
    """Plan fn2l1u E-03/V-03: the actor capture is LAZY, so an actor containing parentheses parses.

    The old bound `[^)]*` stopped at the FIRST `)`, so `- <date> executed (opencode (model)): msg`
    did not match at all; `_newest_executed_history` then fell through to its bare-line branch and
    IPD-S406 reported an EMPTY actor and EMPTY summary for a line where both are plainly present.
    Because IPD-S406 is POST-transition, that fired AFTER the lifecycle commit.
    """

    PAREN = "- 2026-08-30 executed (opencode (its_direct/some-model)): did the work"
    SLASH = "- 2026-08-30 executed (opencode/its_direct/some-model): did the work"
    # The hazard that decides lazy-versus-greedy: a MESSAGE containing `):`.
    HAZARD = "- 2026-09-08 executed (opencode/model): fixed foo(bar): baz"
    BOTH = "- 2026-09-08 executed (opencode (model)): fixed foo(bar): baz"

    #: (case, the history line, expected (status, actor, msg) captures, why this row exists)
    CAPTURES = (
        (
            "an actor containing parentheses",
            PAREN,
            ("executed", "opencode (its_direct/some-model)", "did the work"),
            "THE BUG: the old bound `[^)]*` stopped at the FIRST `)`, so this line did not match at "
            "all, `_newest_executed_history` fell through to its bare-line branch, and IPD-S406 "
            "reported an EMPTY actor and EMPTY summary for a line where both are plainly present. "
            "Because S406 is POST-transition, that fired AFTER the lifecycle commit",
        ),
        (
            "the slash-form actor",
            SLASH,
            ("executed", "opencode/its_direct/some-model", "did the work"),
            "the widening must be strictly ADDITIVE: a line that parsed before must parse IDENTICALLY "
            "now, or the fix is a regression wearing a fix's clothes",
        ),
        (
            "a MESSAGE containing `):`",
            HAZARD,
            ("executed", "opencode/model", "fixed foo(bar): baz"),
            "THE REASON THE CAPTURE IS LAZY AND NOT GREEDY. A greedy `(?P<actor>.*)` anchors on the "
            "LAST `):` and captures actor `opencode/model): fixed foo(bar`, corrupting a line that "
            "parses correctly today. This row fails under that alternative, which is what makes the "
            "choice evidenced rather than asserted",
        ),
        (
            "BOTH hazards at once",
            BOTH,
            ("executed", "opencode (model)", "fixed foo(bar): baz"),
            "the two hazards pull in OPPOSITE directions (a parenthesized actor needs the match to "
            "continue past a `)`, a `):` in the message needs it to stop at the first one), so a line "
            "carrying both is where a fix for either one alone falls over",
        ),
        (
            "the `aw set` generic actor",
            "- 2026-08-30 executed (aw set): summary here",
            ("executed", "aw set", "summary here"),
            "fn2l1u E-04: the generic-actor set is pinned NARROWLY, and the rule can only classify an "
            "actor it first PARSED. This row is the parse half of that; the membership half is "
            "asserted below",
        ),
        (
            "the `aw set, --by-human` generic actor",
            "- 2026-08-30 executed (aw set, --by-human): summary here",
            ("executed", "aw set, --by-human", "summary here"),
            "the second generic spelling, which contains a COMMA and a DOUBLE DASH: it parses whole "
            "rather than being split, which is what lets it be matched against the generic set",
        ),
    )

    def test_every_actor_and_message_shape_parses_into_its_three_captures(self):
        """One table over `_HISTORY_ATTRIB_RE`, replacing four tests and a fifth's parse half.

        THE HAZARD IS A COLUMN, which is the reason this is one table: the parenthesized-actor rows and
        the `):`-in-message rows pull the match in OPPOSITE directions, and the BOTH row exists only
        because they can co-occur. Asserted in four separate tests, each looked like an independent
        edge case; adjacent, they are visibly one tradeoff with a forced resolution.

        Why the table beats the four: one regex with lazy captures produces every row, and any
        re-bounding breaks a predictable SET of rows. A bound like `[^)]*` breaks both parenthesized
        rows; going greedy breaks both `):`-in-message rows. Seeing which set moved names the edit
        immediately, where four red lines would each be read as a separate puzzle.
        """
        wrong = []
        for case, line, expected, why in self.CAPTURES:
            match = L._HISTORY_ATTRIB_RE.match(line)
            if match is None:
                wrong.append(
                    f"  {case}: DID NOT MATCH AT ALL, so IPD-S406 would report an empty actor and "
                    f"empty summary for it\n    line: {line!r}\n    this row exists because: {why}"
                )
                continue
            got = (match.group("status"), match.group("actor"), match.group("msg"))
            if got != expected:
                labels = ("status", "actor", "msg")
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
            f"_HISTORY_ATTRIB_RE mis-split {len(wrong)} of {len(self.CAPTURES)} history lines. One "
            "regex with lazy captures produces every row and the rows trade off against each other, so "
            "read WHICH set moved. Both PARENTHESIZED rows failing means someone re-bounded the actor "
            "to `[^)]*`; both `):`-in-message rows failing means someone made a capture GREEDY. FIX: "
            "do not fix one row at a time, because each naive fix breaks the other set. A row that DID "
            "NOT MATCH AT ALL is the worst outcome: IPD-S406 then reports an empty actor for a line "
            f"that plainly has one, and it reports it AFTER the lifecycle commit.\n"
            + "\n".join(wrong),
        )

    def test_the_generic_actors_set_stays_narrow(self):
        """Kept separate: asserts SET MEMBERSHIP in `_GENERIC_ACTORS`, not a parse result.

        The table proves both generic spellings PARSE; this proves they are the ones the rule treats as
        generic. Pinned because the danger with this rule is ballooning it into judging whether a name
        looks specific enough, which would refuse the real actors agents and humans write.
        """
        for actor in ("aw set", "aw set, --by-human"):
            with self.subTest(actor=actor):
                self.assertIn(actor, L._GENERIC_ACTORS)

    def test_the_greedy_alternative_is_exhibited_as_WRONG(self):
        """Kept separate: asserts over a LOCALLY DEFINED greedy regex, not the shipped one.

        It pins the REJECTED alternative's failure so a later editor does not 'simplify' to greedy. The
        subject is a pattern compiled in this test body, which no row of a table over
        `_HISTORY_ATTRIB_RE` can be.
        """
        greedy = re.compile(
            r"^-\s+(?:\d{4}-\d{2}-\d{2})\s+(?P<status>\S+)\s+\((?P<actor>.*)\)\s*:\s*(?P<msg>.*)$"
        )
        g = greedy.match(self.HAZARD)
        self.assertIsNotNone(g)
        assert g is not None
        self.assertEqual(
            g.group("actor"),
            "opencode/model): fixed foo(bar",
            "if this ever stops corrupting the line, the lazy/greedy tradeoff changed",
        )

    def test_the_attribution_lint_no_longer_reports_an_empty_actor(self):
        """Kept separate: goes END TO END through `_newest_executed_history`, not the regex.

        The capture table asserts what the pattern matches; this asserts what the CONSUMER does with a
        whole parsed document, which is where the original bug actually surfaced: the fall-through to
        the bare-line branch reported an empty actor for a line that plainly had one.
        """
        plan = _approved(_conforming_child())
        plan = plan.replace("- Status: approved", "- Status: executed")
        plan += (
            "\n## Workflow history\n\n"
            "- 2026-08-30 executed (opencode (its_direct/some-model)): did the work "
            "and validated it.\n"
        )
        doc = L.parse(plan)
        parsed = L._newest_executed_history(doc)
        self.assertIsNotNone(parsed, "the newest executed entry must be found")
        assert parsed is not None
        actor, msg = parsed
        self.assertEqual(actor, "opencode (its_direct/some-model)")
        self.assertEqual(msg, "did the work and validated it.")
        self.assertNotIn(
            actor,
            L._GENERIC_ACTORS,
            "a real parenthesized actor must not be read as the generic default",
        )


# The gate-section clause bodies IPD-G801 keys on. Module scope so the class-level table below can
# name them directly.
PRODUCTION_CLAUSE_13 = (
    "13. On completion, run `aw ipd lint --phase pre-transition`, confirm it reports conforming and\n"
    "    every `V-*` carries observed evidence, then `git mv` this file to\n"
    "    `.aw/records/plans/executed/`, set `- Status: executed`, and append a\n"
    "    `## Workflow history` line."
)

CORRECTED_CLAUSE = (
    "11. On completion, run `aw ipd lint --phase pre-transition` and confirm it reports conforming.\n"
    "    The plan then reaches `executed` ONLY through the gated finalize transaction:\n"
    "        aw ipd finalize --actor '<agent/model>' --message '<summary>' --apply\n"
    "    In no case may you `git mv` this file or hand-edit `- Status:`; a hand-built transition\n"
    "    satisfies neither IPD-S406 nor IPD-M104."
)

RETIREMENT_CLAUSE = "13. On completion, `git mv` this file to `.aw/records/plans/superseded/` and set `- Status: superseded`."


class GateContractLintTests(unittest.TestCase):
    """dcri4s E-05 / E-06: deterministic lint refusing hand-rolled terminal lifecycle moves."""

    #: (case, the plan text, whether the rule must fire, message substrings required on the
    #: diagnostic, the expected disposition, why this row exists)
    GATES = (
        (
            "a gate carrying the PRODUCTION clause 13 text",
            _conforming_child().replace("Gate prose.", PRODUCTION_CLAUSE_13),
            True,
            ("aw ipd finalize", "git mv"),
            S.DISPOSITION_ERROR,
            "THE RULE, against the exact text the shipped template used to carry: a gate that "
            "PRESCRIBES `git mv` plus a hand-edited `- Status:` teaches every agent reading it to "
            "build the terminal transition by hand, which satisfies neither IPD-S406 nor IPD-M104. "
            "The needles are asserted because a refusal must name the replacement, not just the sin",
        ),
        (
            "a gate naming `aw ipd finalize`",
            _conforming_child().replace("Gate prose.", CORRECTED_CLAUSE),
            False,
            (),
            S.DISPOSITION_CONFORMING,
            "THE POSITIVE ROW: the corrected wording must lint clean, or the rule would flag the very "
            "text it demands and no plan could satisfy it. Every firing row is vacuous while this is "
            "broken",
        ),
        (
            "a RETIREMENT gate that `git mv`s to superseded/",
            _conforming_child().replace("Gate prose.", RETIREMENT_CLAUSE),
            False,
            (),
            S.DISPOSITION_CONFORMING,
            "SCOPE: the rule governs the path to `executed/`, which is the one that claims work was "
            "done. Retiring a plan to `superseded/` IS a hand move by design (there is no finalize "
            "transaction for it), so a rule keying on `git mv` alone would forbid the correct "
            "retirement procedure",
        ),
        (
            "the SAME defective clause quoted OUTSIDE the gate section",
            _conforming_child().replace(
                "Sample goal.",
                f"Sample goal.\n\nHere is a quote of defective text:\n{PRODUCTION_CLAUSE_13}\n",
            ),
            False,
            (),
            S.DISPOSITION_CONFORMING,
            "SECTION-BOUNDED, and the pair of the first row: the identical text is flagged in the gate "
            "and permitted in Goal. A plan must be able to DISCUSS the defective pattern (this repo's "
            "own plans do) without being accused of prescribing it, which is only checkable by having "
            "both rows",
        ),
    )

    def test_the_rule_fires_only_on_a_gate_prescribing_a_hand_rolled_terminal_move(
        self,
    ):
        """One table over IPD-G801, replacing four tests (dcri4s E-05/E-06).

        THE SECTION IS THE COLUMN, and it is the reason this is one table: the first and last rows
        carry the IDENTICAL defective text and must disagree, because the rule is about what a gate
        PRESCRIBES rather than what a document mentions. That is a relationship between two rows, and
        the old fourth test asserting it in isolation read as an unrelated edge case rather than as the
        other half of the first.

        Why the table beats the four: one section-scoped text match produces every row, and its two
        failure modes are opposite and equally bad. If it stops being section-scoped, the
        outside-the-gate row fails and plans can no longer discuss the pattern they are fixing. If its
        match widens past the finalize path, the retirement row fails and the correct retirement
        procedure becomes unlintable. Reading which row moved distinguishes them at a glance.
        """
        wrong = []
        positive_rows_broken = 0
        for case, text, fires, needles, disposition, why in self.GATES:
            res = L.lint_text(text, checkpoint="author")
            found = [d for d in res.diagnostics if d.code == L.C_GATE_HAND_ROLLED_MOVE]
            problems = []
            if fires and not found:
                problems.append(
                    "expected the hand-rolled-move diagnostic; the linter reported "
                    + repr([d.render("t") for d in res.diagnostics] or "nothing at all")
                )
            if not fires and found:
                positive_rows_broken += 1
                problems.append(
                    f"the rule must NOT fire here; it did: "
                    f"{[d.render('t') for d in found]!r}"
                )
            for needle in needles:
                if not any(needle in d.message for d in found):
                    problems.append(
                        f"the diagnostic never mentions {needle!r}; messages were "
                        f"{[d.message for d in found]!r}"
                    )
            if res.disposition != disposition:
                problems.append(
                    f"expected disposition {disposition!r}, got {res.disposition!r}"
                )
            if problems:
                wrong.append(
                    f"  {case}:\n"
                    + "".join(f"    - {p}\n" for p in problems)
                    + f"    this row exists because: {why}"
                )
        note = ""
        if positive_rows_broken:
            note = (
                f" {positive_rows_broken} row(s) that must NOT fire did fire, so the rule is "
                "over-matching and every firing row here is vacuous while that is true."
            )
        self.assertEqual(
            wrong,
            [],
            f"the hand-rolled-move gate rule was wrong for {len(wrong)} of {len(self.GATES)} gate "
            f"bodies.{note} One section-scoped text match produces every row, so read WHICH row moved: "
            "the OUTSIDE-THE-GATE row failing means the match stopped being section-scoped and plans "
            "can no longer quote the pattern they are fixing, while the RETIREMENT row failing means "
            "the match widened past the finalize path and the correct retirement procedure is now "
            "unlintable. FIX: the first and last rows carry IDENTICAL text and must disagree, so if "
            f"they ever agree the section scoping is the thing to look at, not the wording.\n"
            + "\n".join(wrong),
        )

    def test_template_execution_contract_prescribes_finalize_not_hand_rolled_move(self):
        """Kept separate: asserts over a SHIPPED TEMPLATE FILE, not over a linted plan.

        The table checks that the RULE fires correctly; this checks that the template the rule exists
        to protect does not itself carry the defective wording. Its subject is a file on disk and its
        checks are substring presence/absence over that file, so it is structurally different from any
        lint row.
        """
        template_path = (
            REPO_ROOT / ".aw" / "system" / "workflows" / "templates" / "plans-README.md"
        )
        text = template_path.read_text(encoding="utf-8")
        self.assertIn("gated", text)
        self.assertIn("finalize transaction", text)
        self.assertIn("IPD-S406", text)
        self.assertIn("IPD-M104", text)
        self.assertIn("AW_EXECUTION_ROLE=worker", text)
        self.assertIn("AW-LIFECYCLE-ROLE-001", text)
        self.assertIn("aw ipd finalize --actor", text)
        self.assertIn("superseded", text)
        self.assertIn("not-executed", text)
        self.assertNotIn("`git mv` to the terminal directory, set `Status:`", text)


class SharedLifecycleRenderingTests(unittest.TestCase):
    """Spec `uonrjg` R10.3, Sections 9.1 / 9.4, criteria A10/A11/A14/A17 (plan `9zvl2w` E-03/E-05).

    KEPT SEPARATE from every table in this file because the subject is the CLI's RENDERED BYTES, not
    a `LintResult`: each assertion is over raw escape sequences in the human line, which no row in a
    `LintResult` table can express.

    THE ONE DESIGN DECISION THIS PINS, and the reason it needs pinning: `ipd_lint` prints TWO
    status-shaped columns, and only ONE of them is lifecycle. The `- Status:` column holds plan
    statuses (spec Section 6.1) and converts. The DISPOSITION column holds
    `conforming`/`advisory`/`quarantined`/`legacy not evaluated`/`error`, of which only `quarantined`
    is a value the spec claims (Section 7.2, D15) - the other four are generic command outcomes R10.3
    keeps explicitly out of scope. So the column converts BY VALUE, and both halves of that split are
    asserted below, because either one alone would let the other regress silently.

    WHY THE GLYPH IS LOAD-BEARING FOR `quarantined` SPECIFICALLY: the spec maps it to `parked`, which
    is gray 244 - the SAME color `legacy/not evaluated` already falls back to. Adopting the spec color
    therefore costs the color distinction those two words used to have (`quarantined` was orange 214),
    and `◇` is what pays for it. A change that keeps the color but drops the glyph would make a
    quarantined plan indistinguishable from an unevaluated one, defeating Section 7.2's stated reason
    for listing the value at all ("the lint view must show it without calling it a pass").
    """

    _QUARANTINED = _conforming_child().replace(
        "- Author: tester",
        "- Quarantine: re-author later\n- Quarantine owner: maintainer\n"
        "- Quarantine follow-up: after the Set\n- Author: tester",
    )

    def _render(self, text, *, force_color=True, agent=False):
        import os
        import tempfile
        from pathlib import Path as _Path
        from unittest import mock

        with tempfile.TemporaryDirectory() as td:
            d = _Path(td) / ".aw" / "records" / "plans" / "pending"
            d.mkdir(parents=True)
            p = d / "20260803-x-01-abc123-sample.ipd.md"
            p.write_text(text, encoding="utf-8")
            ns = argparse.Namespace(
                phase="author", all=False, legacy=False, agent=agent, path=str(p)
            )
            env = {"FORCE_COLOR": "1"} if force_color else {}
            buf = io.StringIO()
            with mock.patch.dict(os.environ, env, clear=False):
                if not force_color:
                    os.environ.pop("FORCE_COLOR", None)
                with redirect_stdout(buf):
                    L.run_lint(ns)
            return buf.getvalue()

    def test_the_status_column_renders_the_shared_marker_and_color(self):
        out = self._render(_conforming_child())
        # `to-review` is spec Section 6.1 `review-queued`: `◔`, index 39, not bold. The glyph and the
        # word must carry the SAME escape (Section 9.1).
        self.assertIn("\033[38;5;39m\u25d4\033[0m", out, f"glyph missing: {out!r}")
        self.assertIn("\033[38;5;39mto-review\033[0m", out, f"status color: {out!r}")

    def test_the_artifact_type_word_carries_no_escape(self):
        out = self._render(_conforming_child())
        self.assertIn("plan", out)
        for escape in ("\033[1;38;5;33mplan", "\033[38;5;33mplan"):
            self.assertNotIn(
                escape,
                out,
                "criterion A10: the artifact TYPE word must not be lifecycle/tree-colored. "
                f"Section 11 item 5's exemption is for a path SEGMENT, not a bare word: {out!r}",
            )

    def test_quarantined_adopts_the_spec_parked_treatment_and_keeps_its_glyph(self):
        out = self._render(self._QUARANTINED)
        self.assertIn(
            "\033[38;5;244m\u25c7\033[0m",
            out,
            "the `◇` glyph is LOAD-BEARING for `quarantined`: the spec's `parked` gray (244) is the "
            "same color `legacy/not evaluated` already uses, so dropping the glyph makes the two "
            f"indistinguishable and defeats spec Section 7.2's reason for the row: {out!r}",
        )
        self.assertIn(
            "\033[38;5;244mquarantined\033[0m",
            out,
            f"`quarantined` must render spec Section 7.2's `parked` color: {out!r}",
        )
        self.assertNotIn(
            "\033[1;38;5;214mquarantined",
            out,
            "`quarantined` still carries the OLD generic 214, so the one spec-claimed value in the "
            "disposition column was not converted (criterion A17).",
        )

    def test_the_generic_dispositions_are_not_routed_through_the_lifecycle_resolver(
        self,
    ):
        """R10.3: the other four disposition words are generic outcomes and stay generic."""
        out = self._render(_conforming_child())
        self.assertIn(
            "\033[1;38;5;46mconforming\033[0m",
            out,
            "`conforming` lost its generic bright green. It is a command-level OK that spec "
            "`uonrjg` R10.3 keeps OUTSIDE this spec, so it must stay on `Term.status_256` and must "
            f"NOT be resolved (criterion A20 would render it `?`): {out!r}",
        )
        self.assertNotIn(
            "?",
            out,
            "a generic disposition was routed through the lifecycle resolver and rendered "
            "criterion A20's unknown glyph.",
        )

    def test_color_off_keeps_glyph_and_word_with_no_ansi(self):
        out = self._render(self._QUARANTINED, force_color=False)
        self.assertNotIn(
            "\033", out, f"criterion A11: ANSI leaked with color off: {out!r}"
        )
        self.assertIn("\u25c7", out, f"the glyph vanished with color off: {out!r}")
        self.assertIn("quarantined", out, f"the native word vanished: {out!r}")

    def test_agent_mode_emits_no_ansi(self):
        """Criterion A14, as a CHARACTERIZATION: this command already emitted zero and must stay at zero."""
        for label, text in (
            ("conforming", _conforming_child()),
            ("quarantined", self._QUARANTINED),
        ):
            with self.subTest(plan=label):
                out = self._render(text, agent=True)
                self.assertNotIn(
                    "\033", out, f"criterion A14 violation in --agent: {out!r}"
                )

    def test_quarantined_remains_distinguishable_from_legacy_not_evaluated(self):
        """The property the `parked` color costs and the glyph restores, asserted as a DIFFERENCE."""
        quarantined = self._render(self._QUARANTINED)
        legacy_ns_out = self._render(_executed_child())
        q_line = [ln for ln in quarantined.splitlines() if ln.startswith("- ")]
        l_line = [ln for ln in legacy_ns_out.splitlines() if ln.startswith("- ")]
        self.assertTrue(
            q_line and l_line, "expected one rendered row from each fixture"
        )
        self.assertNotEqual(
            q_line[0],
            l_line[0],
            "a quarantined plan and a legacy/not-evaluated one render identically, so the lint view "
            "can no longer tell an intentionally parked plan from an unevaluated one.",
        )


class SetidLengthLintTests(unittest.TestCase):
    """setidlen x75obw E-05 (catalog I-17): `IPD-M109` as a blocking error and as an advisory.

    FIXTURES, NOT THE LIVE CORPUS, AND THAT IS REQUIRED RATHER THAN CONVENIENT. Measured at execution
    2026-09-23: ZERO pending plans carry a setid over 14 (44 do repository-wide, 43 in `executed/` and
    1 in `not-executed/`), so the advisory fires on NOTHING currently editable. That is the intended
    prospective outcome, and it means a corpus-driven test would pass vacuously forever.

    THE TWO TIERS COME FROM DIFFERENT PLACES ON PURPOSE. The ERROR is `ipd_schema.validate_metadata`
    and is therefore visible to the PURE `lint_text`. The ADVISORY needs the per-repository cutover
    (I/O), so it is merged in `lint_file` exactly as the review-escalation and durable-carrier rules
    are; a test that got the advisory out of `lint_text` would prove the read had leaked into the pure
    path, so one row asserts that it does NOT.
    """

    def _plan_text(self, setid, date="2026-09-23"):
        return (
            _conforming_child()
            .replace("- Set: x", f"- Set: {setid} (topic)")
            .replace("- Date: 2026-08-03", f"- Date: {date}")
        )

    def _repo(self, d, cutover: "str | None" = "2026-09-23"):
        root = Path(d)
        cfg = root / ".aw" / "config"
        cfg.mkdir(parents=True)
        project: dict = {"schema_version": 2}
        if cutover is not None:
            project["cutovers"] = {"setid_length": cutover}
        (cfg / "project.json").write_text(json.dumps(project), encoding="utf-8")
        pend = root / ".aw" / "records" / "plans" / "pending"
        pend.mkdir(parents=True)
        return root, pend

    def _lint_file(
        self, setid, *, date="2026-09-23", cutover: "str | None" = "2026-09-23"
    ):
        with tempfile.TemporaryDirectory() as d:
            _root, pend = self._repo(d, cutover=cutover)
            p = pend / f"{date.replace('-', '')}-{setid}-01-abc123-x.ipd.md"
            p.write_text(self._plan_text(setid, date), encoding="utf-8")
            res = L.lint_file(p, checkpoint="author")
            return (
                res.disposition,
                [x.code for x in res.diagnostics if x.code == L.C_SETID_LENGTH],
                [a.code for a in res.advisories if a.code == L.C_SETID_LENGTH],
            )

    def test_setid_length_error_and_advisory_thresholds(self):
        self.assertEqual(L.C_SETID_LENGTH, "IPD-M109")
        self.assertNotEqual(L.C_SETID_LENGTH, L.C_META_FIELD)

        # 25+ chars: blocking error
        disp25, diag25, adv25 = self._lint_file("a" * 25)
        self.assertEqual(disp25, L.S.DISPOSITION_ERROR)
        self.assertEqual(diag25, [L.C_SETID_LENGTH])
        self.assertTrue(bool(diag25) ^ bool(adv25))

        # 15 to 24 chars: advisory, conforming disposition
        for n in (15, 16, 20, 24):
            disp, diag, adv = self._lint_file("a" * n)
            self.assertEqual(disp, L.S.DISPOSITION_CONFORMING, f"len={n}")
            self.assertEqual(diag, [], f"len={n}")
            self.assertEqual(adv, [L.C_SETID_LENGTH], f"len={n}")

        # 14 or fewer: clean
        disp14, diag14, adv14 = self._lint_file("a" * 14)
        self.assertEqual(disp14, L.S.DISPOSITION_CONFORMING)
        self.assertEqual((diag14, adv14), ([], []))

    def test_setid_length_cutover_repository_and_purity_rules(self):
        # Pre-cutover plan suppressed
        disp, diag, adv = self._lint_file("a" * 20, date="2026-08-01")
        self.assertEqual(disp, L.S.DISPOSITION_CONFORMING)
        self.assertEqual((diag, adv), ([], []))

        # Unstamped repository: no advisory, but error tier survives
        disp_un, diag_un, adv_un = self._lint_file("a" * 20, cutover=None)
        self.assertEqual(disp_un, L.S.DISPOSITION_CONFORMING)
        self.assertEqual((diag_un, adv_un), ([], []))
        disp_err, diag_err, _ = self._lint_file("a" * 25, cutover=None)
        self.assertEqual(disp_err, L.S.DISPOSITION_ERROR)
        self.assertEqual(diag_err, [L.C_SETID_LENGTH])

        # Purity contract: lint_text does no I/O, no advisory, but schema error fires
        res = L.lint_text(
            self._plan_text("a" * 20), checkpoint="author", directory="pending"
        )
        self.assertEqual(
            [a.code for a in res.advisories if a.code == L.C_SETID_LENGTH], []
        )
        err = L.lint_text(
            self._plan_text("a" * 25), checkpoint="author", directory="pending"
        )
        self.assertEqual(
            [x.code for x in err.diagnostics if x.code == L.C_SETID_LENGTH],
            [L.C_SETID_LENGTH],
        )

        # Terminal plan reaches legacy disposition first
        res_leg = L.lint_text(
            self._plan_text("a" * 25), checkpoint="author", directory="executed"
        )
        self.assertEqual(res_leg.disposition, L.S.DISPOSITION_LEGACY)
        self.assertEqual(
            [x.code for x in res_leg.diagnostics if x.code == L.C_SETID_LENGTH], []
        )


if __name__ == "__main__":
    unittest.main()
