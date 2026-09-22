"""orchtyped Order 01 (`dpdyed`): the typed child-tracking row grammar and its ONE shared function.

WHAT THIS PINS, and why each half exists rather than merely that it does.

E-01/V-01, THE GRAMMAR IS ANCHORED AT BOTH ENDS. Spec `r07vma` R1a's whole claim is that a deliverable
cannot be PHRASED into a conforming row, and that claim rests entirely on the anchors: a pattern that
merely SEARCHES for `CONFIRM <id6> REACHED <status>` accepts `E-02 ESTABLISH THE BASELINE, then CONFIRM
dpdyed REACHED executed`, which is exactly the welded row the rule exists to refuse. So the
mid-line/leading-prose/trailing-prose rows below are the load-bearing cases, not decoration, and a
ticked box is asserted to CONFORM because a mid-execution or hand-run parent legitimately has one.

E-02/V-02, THE CHILD ID6 COMES FROM THE SHARED ROW-WALK, AND AN UNUSABLE TABLE IS A REFUSAL. R3
requires ONE definition of "who are this Set's children", so the id6 cells are read through
`runner_shared.child_table_rows` (already shared by the probe cache and `parse_declared_child_orders`)
and the order graph plus refusal reason through `ipd_set_plan.parse_child_table`. The
no-`Id`-column case is asserted against a REAL orchestrator because half the live corpus has no such
column, and a resolver assuming one either crashes or vacuously passes on half the population.

E-03/V-03, THE STATUS VOCABULARY IS NOT COPIED. `ipd_schema.RECOGNIZED_STATUS` is the one list; a
second one in the linter would be a defect, so the test drives all nine values through the rule and
asserts the reference rather than the membership only.

E-04/V-04, THE RULE MUST ACTUALLY FIRE. A stable `C_*` code is INERT on its own: `lint_text` builds
`diags` from an explicit list of `check_*` calls and the disposition is `conforming` iff `diags` is
empty. So the wiring tests assert a NONZERO `aw ipd lint` exit on a violating orchestrator and silence
on a `Kind: child` plan, and one asserts the fence-aware reading, because this plan's own body quotes
the grammar template and a raw-line scan would eventually flag a plan for describing the rule.

E-05/V-05, THE REFUSAL'S CONTENTS, NOT ITS WORDING. R7 is a CONTENT requirement: the invariant, an
explicit anti-deletion clause, and BOTH remedies with neither prescribed. The test asserts the three
CONTENTS are present and deliberately does NOT assert an exact string, which would make every wording
improvement a test failure.

FIXTURES ARE BUILT IN THIS MODULE WHEREVER THE ASSERTION IS ABOUT THE RULE. Pinning a rule test to a
live plan's mutable text is what broke
`tests/test_orchestrator_retirement.py::RealRepositorySets`. The exceptions are deliberate and
narrow: the three corpus measurements (the pre-migration conforming count, the no-`Id`-column
population, and the parent `d1u4sy` as a live conforming fixture) are claims ABOUT THE CORPUS, and a
frozen copy of a corpus is not evidence about the corpus. Each of those carries its own skip so it
reports "not measurable here" rather than passing vacuously.
"""

from __future__ import annotations

import argparse
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agent_workflows import ipd_lint as L
from agent_workflows import ipd_schema as S
from agent_workflows import ipd_set_plan as ISP
from agent_workflows import runner_shared as RS
from tests.support import REPO_ROOT, SOURCE_PLANS

# ==================================================================================================
# A frozen conforming orchestrator, built here so a rule test never depends on a mutable plan
# ==================================================================================================

#: A minimal orchestrator whose two rows are written IN the R1a grammar. Everything the rule reads is
#: present: the metadata `- Kind:` bullet, a child table with an `Id` column and a dependency column,
#: and two typed rows with their `Depends on:` edges.
CONFORMING = """# IPD: frozen conforming orchestrator fixture

- Date: 2026-09-22
- Kind: orchestrator
- Concern: fixture.
- Scope: fixture.
- Scope-Paths: grandfathered
- Status: approved
- Set: fixture
- Order: 0
- Highest E allocated: 02
- Author: fixture
- Id: fix000
- Approval: 2026-09-22, fixture

## Workflow history

- 2026-09-22 approved (fixture): created.

## Goal

Fixture.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action.

### Task group 1: track the children

- [ ] E-01 CONFIRM aaa111 REACHED executed
  - Depends on: none
  - Expected outcome: aaa111 reads `- Status: executed` on disk.
  - Execution state: pending
  - Context, not an obligation: continuation lines are not parsed (R1a).

- [ ] E-02 CONFIRM bbb222 REACHED executed
  - Depends on: E-01
  - Expected outcome: bbb222 reads `- Status: executed` on disk.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | What it does | Depends on |
| --- | --- | --- | --- |
| 01 | `aaa111` | first child | none |
| 02 | `bbb222` | second child | 01 |

## Completion criteria (the whole Set is done only when)

- Fixture.

## Cross-IPD validation

- Fixture.

## Deferred / out of scope (with reason)

none

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

Fixture.

## Open questions

### OQ-01: fixture?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: fixture.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass.

- [ ] V-01 validates E-01
  - Required evidence: aaa111 reads `- Status: executed`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: bbb222 reads `- Status: executed`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: fixture.

Transition via `aw ipd finalize`.
"""

#: The same document as a `Kind: child`. Used to prove the rule is kind-gated.
AS_CHILD = CONFORMING.replace("- Kind: orchestrator", "- Kind: child").replace(
    "- Order: 0", "- Order: 1"
)

#: The child table with its `Id` column removed, which is HALF the live corpus's shape.
NO_ID_COLUMN = CONFORMING.replace(
    "| Order | Id | What it does | Depends on |\n"
    "| --- | --- | --- | --- |\n"
    "| 01 | `aaa111` | first child | none |\n"
    "| 02 | `bbb222` | second child | 01 |",
    "| Order | What it does | Depends on |\n"
    "| --- | --- | --- |\n"
    "| 01 | first child | none |\n"
    "| 02 | second child | 01 |",
)


def _row(text: str, ident: str) -> L.OrchestratorRow:
    """The verdict for one row of ``text``, by E id."""
    result = L.orchestrator_row_conformance(text)
    for row in result.rows:
        if row.ident == ident:
            return row
    raise AssertionError(f"no row {ident} in {[r.ident for r in result.rows]!r}")


def _replace_row(text: str, new_first_line: str) -> str:
    """Swap E-02's first line, leaving its continuation lines untouched."""
    return text.replace("- [ ] E-02 CONFIRM bbb222 REACHED executed", new_first_line)


# ==================================================================================================
# E-01 / V-01: the grammar, and its anchors
# ==================================================================================================


class TheGrammarIsAnchored(unittest.TestCase):
    """ONE table, because every row states the same relationship: a first line, and whether the typed
    grammar accepts it.

    THE ANCHORS ARE THE SUBJECT, which is why this is a table rather than two tests. A search-based
    pattern passes the `mid-line` and `trailing prose` rows while failing nothing else, so those rows
    are the only ones that can tell an anchored implementation from an unanchored one. The conforming
    rows are here to keep the table falsifiable in the other direction: a pattern that rejects
    everything would satisfy the refusals alone.
    """

    #: (case, the row's first line, whether it must CONFORM, why this row exists)
    ROWS = (
        (
            "the canonical form",
            "- [ ] E-02 CONFIRM bbb222 REACHED executed",
            True,
            "the shape spec R1a specifies; if this fails the grammar is not the spec's",
        ),
        (
            "a TICKED box",
            "- [x] E-02 CONFIRM bbb222 REACHED executed",
            True,
            "a mid-execution or hand-run orchestrator carries ticked rows, and shape conformance is "
            "not a statement about progress",
        ),
        (
            "trailing prose after the status",
            "- [ ] E-02 CONFIRM bbb222 REACHED executed and then re-run the suite",
            False,
            "THE WELDED ROW. This is how a deliverable would ride along on a tracking row, and it is "
            "the single case that makes R1a's by-construction claim true rather than aspirational",
        ),
        (
            "leading prose before CONFIRM",
            "- [ ] E-02 First CONFIRM bbb222 REACHED executed",
            False,
            "a row that merely CONTAINS the phrase is not conforming; a search-based pattern passes "
            "this and would accept an arbitrarily long preamble",
        ),
        (
            "an over-indented row",
            "  - [ ] E-02 CONFIRM bbb222 REACHED executed",
            False,
            "the `^` anchor; an indented leaf is a continuation-line shape, not a checklist row, and "
            "`parse` does not treat it as a leaf at all",
        ),
        (
            "a lowercase keyword",
            "- [ ] E-02 confirm bbb222 REACHED executed",
            False,
            "the keywords are literal; accepting case variants starts the slide back to a vocabulary "
            "rule, which spec Section 3 measured and abandoned",
        ),
        (
            "a five-character id where six are required",
            "- [ ] E-02 CONFIRM bbb22 REACHED executed",
            False,
            "the id6 is a fixed-width token; a looser field would let an arbitrary word occupy it",
        ),
        (
            "no `REACHED` keyword",
            "- [ ] E-02 CONFIRM bbb222 executed",
            False,
            "the keyword is what separates the two typed fields; without it the row is prose",
        ),
    )

    def test_each_row_is_accepted_or_refused_as_the_anchors_require(self):
        wrong = []
        for case, first_line, must_conform, why in self.ROWS:
            text = _replace_row(CONFORMING, first_line)
            result = L.orchestrator_row_conformance(text)
            # An over-indented row is not a leaf at all, so E-02 disappears from the row set; that
            # is itself a refusal of the document (the row no longer tracks a child), and is asserted
            # through the document-level verdict rather than through a per-row lookup.
            got = result.conforming and len(result.rows) == 2
            if got != must_conform:
                wrong.append(
                    f"  {case}: expected conforming={must_conform}, got {got}\n"
                    f"    rows: {[(r.ident, r.conforming, r.reason) for r in result.rows]!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            "the typed row grammar mishandled a case its anchors decide. FIX: if a REFUSAL row "
            "started conforming, the pattern has been widened (most likely `^`/`$` was dropped or a "
            "`.*` crept in), which re-opens the place a deliverable can be welded onto a tracking "
            "row. If a CONFORMING row started refusing, the pattern no longer matches the shape "
            "spec `r07vma` R1a specifies.\n" + "\n".join(wrong),
        )

    def test_the_three_typed_fields_come_back_parsed(self):
        """Kept separate: the subject is the RETURNED FIELDS, not the accept/refuse verdict.

        The table above asserts a boolean. R1a's criterion 2 demands a conforming row yield
        `(child_id6, status, depends_on)`, and a rule that accepted the right rows while returning
        the wrong fields would satisfy the table and be useless to both consumers.
        """
        row = _row(CONFORMING, "E-02")
        self.assertEqual(
            (row.child_id6, row.status, row.depends_on),
            ("bbb222", "executed", "E-01"),
        )

    def test_a_conforming_row_inside_a_FENCE_is_not_seen(self):
        """Kept separate: the subject is the fence-aware structural view, not the grammar.

        THE HAZARD IS SELF-INFLICTED. This Set's own plans quote the grammar template, so a rule
        scanning raw lines would eventually flag a plan for DESCRIBING the rule. Reading rows through
        `parse` (which is built on `_structural_lines`) is what prevents it, and this is the only test
        that would notice a future implementation re-deriving the row set from `text.splitlines()`.
        """
        fenced = CONFORMING.replace(
            "### Task group 1: track the children",
            "### Task group 1: track the children\n\n```\n"
            "- [ ] E-98 CONFIRM aaa111 REACHED executed\n"
            "- [ ] E-99 PRODUCE THE INVENTORY before any child runs\n"
            "```\n",
        )
        result = L.orchestrator_row_conformance(fenced)
        self.assertEqual(
            [r.ident for r in result.rows],
            ["E-01", "E-02"],
            "a row quoted inside a fenced code block was read as a checklist row; the rule must "
            "consume `ipd_lint.parse` (built on `_structural_lines`) rather than raw lines",
        )
        self.assertTrue(result.conforming)


class ThePreMigrationCorpusCount(unittest.TestCase):
    """Kept separate and pinned to the LIVE tree, because the claim is ABOUT the live tree.

    A frozen copy of a corpus is not evidence about the corpus, so this is the one place a rule test
    legitimately reads mutable plans. Spec `r07vma` Section 5 cost 3 states the expected answer and
    WHY it must be re-derived: the grammar is new, so nothing authored before it can conform by
    accident, and a NON-ZERO count (beyond the parent deliberately written in the grammar) would mean
    the grammar had been quietly widened.

    THE ASSERTION IS A PROPERTY, NOT A COUNT. The corpus moves hourly as agents author and migrate
    plans, and child `68uhp0` will migrate all of it, so pinning `5 of 38` would make this test a
    maintenance burden that gets deleted. What is asserted is: every conforming row belongs to a plan
    whose rows ALL conform, which is what "the grammar was not widened to fit an existing plan" means
    operationally and which survives the migration.
    """

    def _orchestrators(self):
        pending = SOURCE_PLANS / "pending"
        if not pending.is_dir():
            self.skipTest("no pending plan tree in this checkout")
        out = []
        for path in sorted(pending.glob("*.ipd.md")):
            text = path.read_text(encoding="utf-8")
            doc = L.parse(text)
            if doc.meta_fields.get("Kind") != S.KIND_ORCHESTRATOR:
                continue
            out.append((path, text, doc))
        if not out:
            self.skipTest("no pending orchestrator to measure")
        return out

    def test_no_orchestrator_is_PARTIALLY_conforming(self):
        partial = {}
        for path, text, doc in self._orchestrators():
            result = L.orchestrator_row_conformance(text, doc=doc)
            conforming = sum(1 for r in result.rows if r.conforming)
            if 0 < conforming < len(result.rows):
                partial[path.name] = f"{conforming}/{len(result.rows)}"
        self.assertEqual(
            partial,
            {},
            "an orchestrator has SOME conforming rows and some not, which is the signature of a "
            "grammar that was widened to make one stubborn row pass: a pre-migration plan should "
            "conform on every row (it was authored in the grammar) or none (it predates it). FIX: "
            "re-read the widened pattern rather than the plan.\n"
            f"partially conforming: {partial}",
        )

    def test_the_parent_that_is_written_in_the_grammar_conforms(self):
        """`d1u4sy` is authored IN this grammar on purpose, so it is a LIVE conforming fixture.

        If the implementation rejects it, either the grammar or that plan is wrong, and the Set's own
        cross-IPD validation says that disagreement must be REPORTED rather than patched on one side.
        """
        for path, text, doc in self._orchestrators():
            if doc.meta_fields.get("Id") != "d1u4sy":
                continue
            result = L.orchestrator_row_conformance(text, doc=doc)
            self.assertTrue(
                result.conforming,
                "the Set's own parent `d1u4sy` is written in the R1a grammar and must conform; "
                f"refusals: {[(r.ident, r.reason) for r in result.findings]!r}",
            )
            self.assertEqual(len(result.rows), 5)
            return
        self.skipTest("d1u4sy is no longer a pending orchestrator")


# ==================================================================================================
# E-02 / V-02: resolving the child id6 against the orchestrator's OWN child table
# ==================================================================================================


class TheChildId6ResolvesAgainstThisSetsOwnTable(unittest.TestCase):
    """ONE table: each row is a child-table shape, and the verdict it must produce for a row whose
    grammar is already correct.

    WHY ONE TABLE. Every row below holds the CHECKLIST constant and varies only the TABLE, so a
    failure is attributable to the table shape. The dangerous direction is the quiet one: a resolver
    that vacuously PASSES when it cannot read the table reports conformance it never established,
    which is why the unusable-table rows assert a refusal REASON and not merely non-conformance.
    """

    #: (case, the document, the expected reason for E-02 ("" = must conform), why this row exists)
    TABLES = (
        (
            "a row naming a genuine child of the Set",
            CONFORMING,
            "",
            "the baseline; without it every refusal row could be satisfied by refusing everything",
        ),
        (
            "a row naming a plan that is NOT a child of this Set",
            _replace_row(CONFORMING, "- [ ] E-02 CONFIRM zzz999 REACHED executed"),
            L.ORCH_ROW_CHILD_UNKNOWN,
            "R1a requires the id6 resolve to a row of THIS orchestrator's own child table; a rule "
            "that only checked id6 SHAPE would pass a valid-looking id belonging to another Set",
        ),
        (
            "a child table with NO `Id` column",
            NO_ID_COLUMN,
            L.ORCH_ROW_TABLE_UNUSABLE,
            "HALF the live corpus has this shape, so a resolver assuming the column exists either "
            "crashes or vacuously passes on half the population; it must REFUSE and name the cause",
        ),
        (
            "a child table that does not parse at all",
            CONFORMING.replace(
                "| Order | Id | What it does | Depends on |", "| Q | R |"
            ),
            L.ORCH_ROW_TABLE_UNUSABLE,
            "an unparseable table means conformance is UNKNOWN, not satisfied; `parse_child_table`'s "
            "own `reason` must reach the message so the caller's fallback is never silent",
        ),
        (
            "no child-table section at all",
            CONFORMING.replace(
                "## Child IPDs, sequence, and dependencies", "## Child IPDs elsewhere"
            ),
            L.ORCH_ROW_TABLE_UNUSABLE,
            "the degenerate case, which must refuse rather than raise",
        ),
    )

    def test_each_table_shape_produces_its_verdict(self):
        wrong = []
        for case, text, expected, why in self.TABLES:
            try:
                row = _row(text, "E-02")
                got = row.reason
            except (
                AssertionError
            ) as exc:  # a row that vanished is itself a failure to report
                got = f"<no E-02 row: {exc}>"
            if got != expected:
                wrong.append(
                    f"  {case}: expected reason {expected!r}, got {got!r}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            "child-id6 resolution mishandled a table shape. FIX: if an unusable table started "
            "PASSING, the resolver is treating 'cannot read the table' as 'the row is fine', which "
            "reports conformance it never established. If the genuine child started refusing, the "
            "id6 cells are no longer being read from `runner_shared.child_table_rows`.\n"
            + "\n".join(wrong),
        )

    def test_the_unusable_table_message_quotes_the_underlying_reason(self):
        """Kept separate: asserts the MESSAGE carries the cause, not just that a refusal happened.

        The table above asserts a reason CODE. A refusal whose text says only "unusable" sends an
        author looking in the wrong place; the whole point of `ChildTableResult.reason` existing is
        that the caller's fallback is never silent.
        """
        row = _row(NO_ID_COLUMN, "E-02")
        self.assertIn("no `Id` column", row.message)
        broken = CONFORMING.replace(
            "| Order | Id | What it does | Depends on |", "| Q | R |"
        )
        reason = ISP.parse_child_table(broken).reason or ""
        self.assertTrue(reason, "expected parse_child_table to explain this refusal")
        self.assertIn(
            reason,
            _row(broken, "E-02").message,
            "the refusal must quote `parse_child_table`'s own reason rather than a generic message",
        )

    def test_the_id6_cells_come_from_the_ONE_shared_row_walk(self):
        """Kept separate: the subject is R3 (one definition), asserted by CONSTRUCTION not by grep.

        `ipd_set_plan.parse_child_table` deliberately returns NO id6 (its fields are exactly
        `('rows','reason')` and `order_to_id` is an INPUT), so a validation citing it as the SOURCE of
        the id6 would be false. The id6s must therefore agree with `runner_shared.child_table_rows`,
        which is ALREADY the shared row-walk behind the probe cache and `parse_declared_child_orders`.
        """
        self.assertEqual(
            ISP.ChildTableResult._fields,
            ("rows", "reason"),
            "parse_child_table's result gained a field; if it now carries id6s, this rule should "
            "consume that rather than reading cells itself",
        )
        rows = RS.child_table_rows(CONFORMING)
        self.assertEqual(rows[0][1].strip().strip("`"), "Id")
        from_walk = {
            cells[1].strip().strip("`") for cells in rows[1:] if len(cells) > 1
        }
        resolved, reason = L._child_id6_index(CONFORMING)
        self.assertEqual(reason, "")
        self.assertEqual(
            set(resolved),
            from_walk,
            "the rule's id6 set must be exactly what the shared row-walk reports; a difference means "
            "a second table scanner was written, which is the R3 violation this Set exists to stop",
        )

    def test_a_backticked_cell_and_a_prose_cell_resolve_as_the_corpus_writes_them(self):
        """Kept separate: the subject is CELL TEXT, measured against two real corpus shapes.

        The live corpus writes an Id cell as `` `dpdyed` `` (backticked), as
        `` `1bdxcp` (currently authored as Order 02) `` (backticked plus prose) and as
        `UNAUTHORED, must be written before this Set runs` (no id6 at all). The first two must
        resolve; the third must not, because inventing an id6 for an unauthored child would forge a
        reference.
        """
        mixed = CONFORMING.replace(
            "| 02 | `bbb222` | second child | 01 |",
            "| 02 | `bbb222` (currently authored as Order 03) | second child | 01 |",
        )
        resolved, reason = L._child_id6_index(mixed)
        self.assertEqual(reason, "")
        self.assertEqual(set(resolved), {"aaa111", "bbb222"})

        unauthored = CONFORMING.replace(
            "| 02 | `bbb222` | second child | 01 |",
            "| 02 | UNAUTHORED, must be written before this Set runs | second child | 01 |",
        )
        resolved, reason = L._child_id6_index(unauthored)
        self.assertEqual(reason, "")
        self.assertEqual(
            set(resolved),
            {"aaa111"},
            "an unauthored-child cell must resolve to NO id6, so a row naming one is refused rather "
            "than silently accepted",
        )


class TheNoIdColumnPopulationIsReal(unittest.TestCase):
    """Kept separate and pinned to the LIVE tree: the claim is that this shape EXISTS in the corpus.

    The table-shape table above uses a constructed no-`Id` document, which proves the rule handles the
    shape but not that the shape matters. This measures the real population, because that is what makes
    the refusal a migration instruction (child `68uhp0` adds the column) rather than a hypothetical.
    """

    def test_at_least_one_live_orchestrator_declares_no_Id_column(self):
        pending = SOURCE_PLANS / "pending"
        if not pending.is_dir():
            self.skipTest("no pending plan tree in this checkout")
        without = []
        total = 0
        for path in sorted(pending.glob("*.ipd.md")):
            text = path.read_text(encoding="utf-8")
            doc = L.parse(text)
            if doc.meta_fields.get("Kind") != S.KIND_ORCHESTRATOR:
                continue
            total += 1
            _ids, reason = L._child_id6_index(text)
            if "no `Id` column" in reason:
                without.append(path.name)
        if not total:
            self.skipTest("no pending orchestrator to measure")
        self.assertTrue(
            without,
            "no live orchestrator lacks an `Id` column. If child `68uhp0`'s migration has run, that "
            "is the intended end state and this test should be re-expressed; until then it means the "
            f"detector stopped recognizing the shape. measured over {total} orchestrator(s)",
        )


# ==================================================================================================
# E-03 / V-03: the status vocabulary is `ipd_schema.RECOGNIZED_STATUS`, not a local list
# ==================================================================================================


class TheStatusVocabularyIsTheSharedOne(unittest.TestCase):
    """ONE table over the WHOLE vocabulary plus its near-misses, because the rule is membership.

    Enumerating all nine values is not padding: the plan's OQ-01 records the open question of whether
    to narrow to the terminal subset, so a test that checked only `executed` would pass unchanged if
    someone narrowed the rule by accident, and the decision would be made silently.
    """

    def test_every_recognized_status_parses_and_an_unknown_one_is_refused(self):
        wrong = []
        for status in sorted(S.RECOGNIZED_STATUS):
            text = _replace_row(
                CONFORMING, f"- [ ] E-02 CONFIRM bbb222 REACHED {status}"
            )
            row = _row(text, "E-02")
            if not row.conforming or row.status != status:
                wrong.append(
                    f"  recognized status {status!r} was refused ({row.reason!r}); the vocabulary is "
                    "`ipd_schema.RECOGNIZED_STATUS` and this rule accepts all of it (plan OQ-01: "
                    "narrowing to the terminal subset is a later, evidence-led change)"
                )
        for bogus in ("finished", "done", "Executed", "executed."):
            text = _replace_row(
                CONFORMING, f"- [ ] E-02 CONFIRM bbb222 REACHED {bogus}"
            )
            row = _row(text, "E-02")
            if row.conforming:
                wrong.append(
                    f"  unrecognized token {bogus!r} was ACCEPTED; a row may only name a real plan "
                    "status, or a parent can declare a wait nothing can ever satisfy"
                )
        self.assertEqual(wrong, [], "\n".join(wrong))

    def test_the_refusal_names_the_vocabulary(self):
        """Kept separate: an author told only "invalid" has to go looking for the list."""
        row = _row(
            _replace_row(CONFORMING, "- [ ] E-02 CONFIRM bbb222 REACHED finished"),
            "E-02",
        )
        self.assertEqual(row.reason, L.ORCH_ROW_STATUS_UNKNOWN)
        for value in sorted(S.RECOGNIZED_STATUS):
            self.assertIn(value, row.message)

    def test_no_second_status_list_was_introduced(self):
        """Kept separate: a STRUCTURAL scan of the linter's own source, not a lint result.

        R3's reasoning applies to the vocabulary as much as to the grammar: a second copy of the nine
        values would be two lists that drift. The check is that the module names the SHARED constant
        and does not contain a literal re-listing of the vocabulary.
        """
        src = (REPO_ROOT / "agent_workflows" / "ipd_lint.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("S.RECOGNIZED_STATUS", src)
        # A COPY OF THE VOCABULARY IS DETECTED BY ITS DISTINCTIVE MEMBERS, and deliberately NOT by
        # looking for `"not-executed", "reusable"`: that pair ALSO occurs in `_dir_of`'s
        # DIRECTORY-anchor tuple, which is a different vocabulary that legitimately shares four words
        # with this one. The first version of this test matched that line and failed on correct code,
        # which is the false-positive shape a wording-based rule always has (spec `r07vma` Section 3).
        # `auto-approved` and `to-review` are statuses and are NOT disposition directories, so a
        # container holding both is a status list.
        for line in src.splitlines():
            if '"auto-approved"' in line and '"to-review"' in line:
                self.fail(
                    "ipd_lint appears to carry its own copy of the plan status vocabulary "
                    f"({line.strip()!r}); consume `ipd_schema.RECOGNIZED_STATUS` instead"
                )


# ==================================================================================================
# E-04 / V-04: ONE function, a stable code, and the wiring WITHOUT WHICH THE CODE NEVER FIRES
# ==================================================================================================


class TheRuleIsOneFunctionWithPerRowDetail(unittest.TestCase):
    def test_the_result_exposes_per_row_fields_rather_than_a_bare_bool(self):
        """R3/R8: children `r3xk1f` and `0xmk4e` render their own output from this result.

        A bare bool would force each consumer to re-derive the rule to say WHICH row failed and WHY,
        which is exactly the drift R3 exists to prevent.
        """
        result = L.orchestrator_row_conformance(
            _replace_row(CONFORMING, "- [ ] E-02 PRODUCE THE INVENTORY")
        )
        self.assertFalse(result.conforming)
        self.assertEqual(len(result.rows), 2)
        self.assertEqual(
            [r.conforming for r in result.rows],
            [True, False],
            "the result must distinguish the conforming row from the violating one",
        )
        finding = result.findings[0]
        self.assertEqual(finding.ident, "E-02")
        self.assertTrue(finding.line > 0)
        self.assertTrue(finding.message)
        self.assertEqual(result.declared_orders, ("1", "2"))

    def test_EVERY_violation_is_reported_not_just_the_first(self):
        """R8 in miniature: a consumer that stops at the first finding gives the operator the
        fix-one-then-rediscover-the-next cycle the spec calls the worst possible experience."""
        both = _replace_row(CONFORMING, "- [ ] E-02 PRODUCE THE INVENTORY").replace(
            "- [ ] E-01 CONFIRM aaa111 REACHED executed",
            "- [ ] E-01 ESTABLISH THE BASELINE before any child runs",
        )
        result = L.orchestrator_row_conformance(both)
        self.assertEqual([r.ident for r in result.findings], ["E-01", "E-02"])

    def test_a_child_plan_is_untouched_by_the_rule(self):
        """The rule is about an Order-0 parent's checklist and nothing else.

        `Kind` is read from `doc.meta_fields`, which `parse` bounds to the metadata region, so a plan
        QUOTING `- Kind: orchestrator` in its prose is not misclassified.
        """
        result = L.orchestrator_row_conformance(AS_CHILD)
        self.assertFalse(result.applies)
        self.assertTrue(result.conforming)
        self.assertEqual(result.rows, ())

        quoting = AS_CHILD.replace(
            "## Goal",
            "## Goal\n\nA plan carrying `- Kind: orchestrator` is a parent.\n",
        )
        self.assertFalse(L.orchestrator_row_conformance(quoting).applies)


class TheStableCodeIsFreeAndInTheShapeFamily(unittest.TestCase):
    def test_the_new_code_did_not_recycle_an_existing_one(self):
        """Confirmed by comparing IMPORTED VALUES, never by grep.

        THREE existing constants are MULTI-LINE assignments (`IPD-S406`, `IPD-M107`, `IPD-M108`), so a
        single-line grep over the source finds 27 of the 30 pre-existing values and can report a code
        FREE when it is taken. Codes are stable and are never recycled.
        """
        values = {
            name: value
            for name, value in vars(L).items()
            if name.startswith("C_") and isinstance(value, str)
        }
        others = {v for k, v in values.items() if k != "C_ORCH_ROW"}
        self.assertEqual(
            len(values),
            len(set(values.values())),
            f"two `C_*` constants share a value: {sorted(values.items())}",
        )
        self.assertNotIn(L.C_ORCH_ROW, others)
        self.assertTrue(
            L.C_ORCH_ROW.startswith("IPD-S4"),
            "a checklist-SHAPE rule belongs in the `IPD-S4xx` state/shape family",
        )


class TheRuleActuallyFires(unittest.TestCase):
    """The tests that separate a WIRED rule from an inert constant.

    A `C_*` constant contributes nothing on its own: `lint_text` builds `diags` from an explicit list
    of `check_*` calls and the disposition is `conforming` iff `diags` is empty. So a validation that
    shows only the constant's existence proves nothing, and these assert a real lint DISPOSITION and a
    real process EXIT.
    """

    #: (case, the document, the phase, whether IPD-S407 must fire, why this row exists)
    VIOLATING = _replace_row(CONFORMING, "- [ ] E-02 PRODUCE THE INVENTORY")
    PHASES = (
        (
            "a violating orchestrator at review-finalize",
            VIOLATING,
            "review-finalize",
            True,
            "THE PRIMARY GATE: R5's bounded repair loop lives at review, so the rule must be visible "
            "there or the loop has nothing to repair and no consumer has a control that does anything",
        ),
        (
            "the same document at pre-transition",
            VIOLATING,
            "pre-transition",
            True,
            "the gate `aw ipd finalize` runs, so a HAND-RUN orchestrator cannot reach `executed` "
            "carrying an untyped row",
        ),
        (
            "the same document at author",
            VIOLATING,
            "author",
            False,
            "MEASURED, not preferred: 11 of 12 live orchestrators do not conform pre-migration, and "
            "`aw check plans` sweeps at `author`, so firing here would mass-fail eleven other "
            "agents' approved plans - the false-refusal cascade spec `25kzda` 2.5b warns leads to "
            "agents DELETING the child checklist",
        ),
        (
            "the same document at pre-execution",
            VIOLATING,
            "pre-execution",
            False,
            "MEASURED, and this exclusion was learned by breaking a test: `aw ipd begin` gates on "
            "this phase, and the SHIPPED `aw ipd scaffold` skeleton is itself non-conforming (it "
            "emits `- [ ] E-01 TODO one observable action.` and a prose placeholder where the child "
            "table goes), so firing here refuses every freshly scaffolded orchestrator at `begin` - "
            "the wrong end of the lifecycle, since authoring and repair happen before `begin` and "
            "`review-finalize` already covers them",
        ),
        (
            "the same document at post-transition",
            VIOLATING,
            "post-transition",
            False,
            "it runs on the ALREADY-COMMITTED plan, so a finding cannot refuse anything and would "
            "only leave a completed transition `committed-incomplete`",
        ),
        (
            "a CONFORMING orchestrator at review-finalize",
            CONFORMING,
            "review-finalize",
            False,
            "keeps the rows above falsifiable: a check that always fired would satisfy them",
        ),
        (
            "a CHILD plan at review-finalize",
            AS_CHILD,
            "review-finalize",
            False,
            "the kind gate; `77tr3o` OQ-1 rejected teaching the honesty checker an orchestrator "
            "special case, and the mirror of that is not policing a child with an orchestrator rule",
        ),
    )

    def test_the_lint_disposition_moves_exactly_where_it_should(self):
        wrong = []
        for case, text, phase, must_fire, why in self.PHASES:
            res = L.lint_text(text, checkpoint=phase, directory="pending")
            fired = L.C_ORCH_ROW in {d.code for d in res.diagnostics}
            if fired != must_fire:
                wrong.append(
                    f"  {case} @ {phase}: expected IPD-S407 fired={must_fire}, got {fired}\n"
                    f"    disposition={res.disposition} codes="
                    f"{sorted({d.code for d in res.diagnostics})}\n"
                    f"    this row exists because: {why}"
                )
            if must_fire and res.disposition != S.DISPOSITION_ERROR:
                wrong.append(
                    f"  {case} @ {phase}: the code fired but the disposition is "
                    f"{res.disposition!r}; a diagnostic that does not move the disposition cannot "
                    "refuse anything"
                )
        self.assertEqual(
            wrong,
            [],
            "the row rule is not wired to the lint disposition as intended. FIX: `check_orchestrator"
            "_rows` must be CALLED from `lint_text` (a `C_*` constant alone is inert), gated on "
            "`Kind: orchestrator` and on `_ORCH_ROW_BLOCKING_CHECKPOINTS`.\n"
            + "\n".join(wrong),
        )

    def _lint_cli(self, text: str, phase: str):
        """Run the real `aw ipd lint` over a temp repo and return (exit code, stdout)."""
        with tempfile.TemporaryDirectory() as td:
            pending = Path(td) / ".aw" / "records" / "plans" / "pending"
            pending.mkdir(parents=True)
            plan = pending / "20260922-fixture-00-fix000-frozen-orchestrator.ipd.md"
            plan.write_text(text, encoding="utf-8")
            ns = argparse.Namespace(
                phase=phase,
                all=False,
                legacy=False,
                agent=False,
                detail=True,
                path=str(plan),
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = L.run_lint(ns)
            return rc, buf.getvalue()

    def test_the_verb_exits_NONZERO_on_a_violating_orchestrator(self):
        """Kept separate: asserts the PROCESS EXIT, which is what a gate consumes.

        `lint_text` returning an error disposition and `aw ipd lint` exiting nonzero are different
        facts, and only the second is what `aw ipd begin`/`finalize` and a human at a terminal see.
        """
        rc, out = self._lint_cli(
            _replace_row(CONFORMING, "- [ ] E-02 PRODUCE THE INVENTORY"),
            "review-finalize",
        )
        self.assertEqual(rc, 1, out)
        self.assertIn(L.C_ORCH_ROW, out)

    def test_the_verb_exits_zero_on_the_conforming_orchestrator(self):
        rc, out = self._lint_cli(CONFORMING, "review-finalize")
        self.assertEqual(rc, 0, out)
        self.assertNotIn(L.C_ORCH_ROW, out)

    def test_the_verb_does_not_report_the_code_for_a_CHILD_plan(self):
        """Asserts the CODE's absence, NOT a zero exit, and the distinction is deliberate.

        `AS_CHILD` is the orchestrator fixture with its `- Kind:` flipped, so it legitimately draws
        `IPD-H202` for the five headings a CHILD plan requires and an orchestrator does not. Demanding
        exit 0 here would make this test about the kind-specific heading contract, which it is not
        about, and the tempting "fix" would be to weaken the assertion to the code anyway. So it is
        written that way from the start: the claim is that the ROW rule does not fire on a child.
        """
        rc, out = self._lint_cli(AS_CHILD, "review-finalize")
        self.assertNotIn(L.C_ORCH_ROW, out)
        self.assertEqual(
            rc, 1, "expected only the unrelated kind-specific heading findings"
        )
        self.assertIn("IPD-H202", out)

    def test_the_SHIPPED_SCAFFOLD_is_not_conforming_which_is_why_begin_is_not_gated(
        self,
    ):
        """Kept separate: this is the EVIDENCE for excluding `pre-execution`, not a wish.

        `aw ipd begin` gates on the `pre-execution` lint. The row rule was wired there first and broke
        `tests/test_orchestrator_retirement.py::TheHumanFacingGateIsUNCHANGED::
        test_the_ordinary_finalize_still_refuses_an_orchestrator`, whose fixture is built from the REAL
        scaffold. THE TEST WAS RIGHT: the shipped skeleton emits a TODO row and a prose placeholder
        where the child table goes, so gating `begin` on the row rule would refuse every freshly
        scaffolded orchestrator before its author could fill it in.

        THIS TEST IS WRITTEN TO FAIL LOUDLY WHEN THAT IS FIXED, which is the point: a later plan making
        the scaffold conforming (spec `r07vma` OQ-01's proposed direction) should re-open the question
        of adding `pre-execution` back, and this is where that reader is told so. Teaching the scaffold
        is NOT in this plan's `- Scope-Paths:`; it is reported as a finding instead.
        """
        from agent_workflows import ipd_authoring as A

        skeleton = A.build_skeleton(
            kind="orchestrator",
            title="probe",
            author="tester",
            when="2026-09-22",
            set_name="probe",
            order=0,
            plan_id="prb000",
        )
        result = L.orchestrator_row_conformance(skeleton)
        self.assertTrue(result.applies)
        self.assertFalse(
            result.conforming,
            "the shipped `aw ipd scaffold` orchestrator skeleton now CONFORMS to the typed row. That "
            "is the intended end state and it removes the reason `pre-execution` is excluded from "
            "`_ORCH_ROW_BLOCKING_CHECKPOINTS`: re-read that constant's comment and consider adding "
            "the phase back, using `tests/test_orchestrator_retirement.py::"
            "TheHumanFacingGateIsUNCHANGED` as the proof.",
        )
        self.assertNotIn(
            L.C_ORCH_ROW,
            {
                d.code
                for d in L.lint_text(
                    skeleton, checkpoint="pre-execution", directory="pending"
                ).diagnostics
            },
            "a freshly scaffolded orchestrator must still pass `aw ipd begin`",
        )

    def test_MUTATION_breaking_one_field_makes_a_pin_fail(self):
        """A mutation check: the pins above must be sensitive to the validation they claim to test.

        Each mutation disables ONE typed field's validation and asserts a case that previously refused
        now passes, which is what proves the corresponding pin is load-bearing rather than incidental.
        """
        import unittest.mock as mock

        bad_status = _replace_row(
            CONFORMING, "- [ ] E-02 CONFIRM bbb222 REACHED finished"
        )
        self.assertFalse(L.orchestrator_row_conformance(bad_status).conforming)
        with mock.patch.object(
            S, "RECOGNIZED_STATUS", frozenset(S.RECOGNIZED_STATUS | {"finished"})
        ):
            self.assertTrue(
                L.orchestrator_row_conformance(bad_status).conforming,
                "widening the vocabulary did not change the verdict, so the status pin is not "
                "reading `ipd_schema.RECOGNIZED_STATUS` at all",
            )
        self.assertFalse(
            L.orchestrator_row_conformance(bad_status).conforming,
            "the mutation leaked: the rule must read the shared vocabulary at call time",
        )

        not_a_child = _replace_row(
            CONFORMING, "- [ ] E-02 CONFIRM zzz999 REACHED executed"
        )
        self.assertFalse(L.orchestrator_row_conformance(not_a_child).conforming)
        with mock.patch.object(
            L, "_child_id6_index", return_value=(frozenset({"aaa111", "zzz999"}), "")
        ):
            self.assertTrue(
                L.orchestrator_row_conformance(not_a_child).conforming,
                "the child-resolution pin is not consulting `_child_id6_index`",
            )
        self.assertFalse(L.orchestrator_row_conformance(not_a_child).conforming)


class TheFunctionIsSitedInIpdLintAndRunnerSharedIsUnchanged(unittest.TestCase):
    """OQ-01's resolution, asserted rather than asserted-in-prose.

    A separate shared module is NOT a neutral alternative: child `0xmk4e` would import it from
    `runner_shared`, whose module-level first-party imports are pinned by SET EQUALITY, so that import
    breaks a shipped test. Siting the function in `ipd_lint` costs nothing because `runner_shared`
    already reaches `ipd_lint` through function-local imports.
    """

    def test_the_function_lives_in_ipd_lint(self):
        self.assertEqual(
            L.orchestrator_row_conformance.__module__, "agent_workflows.ipd_lint"
        )
        self.assertIs(L, sys.modules["agent_workflows.ipd_lint"])

    def test_it_is_reachable_the_way_a_runner_will_reach_it(self):
        """A FUNCTION-LOCAL import, which is how `runner_shared` already reaches `ipd_lint`."""
        code = (
            "from agent_workflows import runner_shared as rs\n"
            "def reach():\n"
            "    from agent_workflows import ipd_lint as l\n"
            "    return l.orchestrator_row_conformance\n"
            "assert callable(reach())\n"
            "print('ok')\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ok", proc.stdout)

    def test_no_module_level_first_party_import_was_added_to_this_module(self):
        """`ipd_lint` must stay importable with no first-party module at import time beyond its own.

        `ipd_set_plan` imports `ipd_lint` AT MODULE LEVEL, so a module-level import of it here would
        close an import cycle. `runner_shared` is likewise reached only in function bodies.
        """
        import ast

        tree = ast.parse(
            (REPO_ROOT / "agent_workflows" / "ipd_lint.py").read_text(encoding="utf-8")
        )
        module_level = set()
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom):
                continue
            mod = node.module or ""
            if not mod.startswith("agent_workflows"):
                continue
            if mod == "agent_workflows":
                module_level.update(a.name for a in node.names)
            else:
                module_level.add(mod.split(".")[-1])
        self.assertEqual(
            module_level,
            {"ipd_schema", "lifecycle_style", "term"},
            f"ipd_lint's module-level first-party imports changed: {sorted(module_level)}. A "
            "module-level `ipd_set_plan` or `runner_shared` import here closes an import cycle.",
        )


# ==================================================================================================
# E-05 / V-05: the refusal's CONTENTS (R7), never its exact wording
# ==================================================================================================


class TheRefusalSatisfiesR7(unittest.TestCase):
    """ONE table over every refusal mode, because R7's three contents are required in ALL of them.

    ASSERTING CONTENTS AND NOT A STRING IS THE POINT. An exact-string assertion would make every
    wording improvement a test failure, and the requirement is about what an author is TOLD: the
    invariant and why it exists, an explicit statement that deleting the item is not a fix, and BOTH
    remedies with neither prescribed.
    """

    MODES = (
        (
            "an untyped row",
            _replace_row(CONFORMING, "- [ ] E-02 PRODUCE THE INVENTORY"),
        ),
        (
            "a row naming a non-child",
            _replace_row(CONFORMING, "- [ ] E-02 CONFIRM zzz999 REACHED executed"),
        ),
        (
            "a row with an unknown status",
            _replace_row(CONFORMING, "- [ ] E-02 CONFIRM bbb222 REACHED finished"),
        ),
        ("a table with no `Id` column", NO_ID_COLUMN),
    )

    def test_every_refusal_carries_the_invariant_the_prohibition_and_both_remedies(
        self,
    ):
        wrong = []
        for case, text in self.MODES:
            row = _row(text, "E-02")
            if row.conforming:
                wrong.append(f"  {case}: expected a refusal, got conformance")
                continue
            msg = row.message
            checks = (
                (
                    "the invariant (retired programmatically, items performed by nobody)",
                    "retired PROGRAMMATICALLY" in msg and "performed by NOBODY" in msg,
                ),
                (
                    "the anti-deletion clause",
                    "DELETING the item is NOT an acceptable fix" in msg,
                ),
                (
                    "remedy 1 (move the step into a child)",
                    "MOVE the step into a child" in msg,
                ),
                (
                    "remedy 2 (remove it because a child already covers it)",
                    "REMOVE it because a child already covers it" in msg,
                ),
                ("neither remedy prescribed", "does not prescribe either" in msg),
                ("the canonical form", L.ORCH_ROW_CANONICAL in msg),
            )
            for what, ok in checks:
                if not ok:
                    wrong.append(
                        f"  {case}: the message is missing {what}\n    message: {msg}"
                    )
        self.assertEqual(
            wrong,
            [],
            "a refusal message does not satisfy spec `r07vma` R7, which is a CONTENT requirement. "
            "The reason BOTH remedies must appear is measured: `rh5tt6` E-02 welds a redundant half "
            "(re-run the suite, which every child already does) to a genuinely uncovered half (an "
            "end-to-end install proof the plan itself calls 'the part no child owns'), so the correct "
            "repair is DELETE for one and A CHILD for the other, and a message prescribing one "
            "produces a pointless child plan for work already done.\n"
            + "\n".join(wrong),
        )

    def test_the_test_does_not_pin_an_exact_string(self):
        """A meta-assertion, kept because R7 is about contents and a future reader may not know why.

        The three content constants are module-level data. Rewording any of them must keep this suite
        green, because the requirement is what the author is told and not how it is phrased.
        """
        for const in (
            L.ORCH_ROW_INVARIANT,
            L.ORCH_ROW_NO_DELETION,
            L.ORCH_ROW_REMEDIES,
        ):
            self.assertTrue(const.strip())
        rendered = L.render_orchestrator_row_refusal(
            row="- [ ] E-02 X", ident="E-02", reason="r", detail="d"
        )
        for const in (
            L.ORCH_ROW_INVARIANT,
            L.ORCH_ROW_NO_DELETION,
            L.ORCH_ROW_REMEDIES,
        ):
            self.assertIn(const, rendered)


if __name__ == "__main__":
    unittest.main()
