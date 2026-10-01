# IPD: Delete the two redundant length literals that restate a neighbouring set-equality, and pin the one claim the set-equality does not make

- Date: 2026-09-30
- Kind: child
- Concern: TWO TESTS ASSERT A LITERAL LENGTH ON THE LINE BESIDE AN ASSERTION THAT ALREADY PINS THE SAME COLLECTION, so the literal proves nothing its neighbour does not and its only future is to go stale when the collection legitimately grows. `GUIDING_PRINCIPLES.md` P16 prohibits "count or census pins" outright ("Never assert on the number of callers, call-site counts, definition counts, or closure sizes as a proxy for an invariant"). CASE 1, `tests/test_reaskscore_composed.py::TestSharedConstants::test_terminal_states_three_copies_are_mutually_equal`, asserts `len(runner_shared.TERMINAL_STATES) == 24` under a comment reading "23 + `retired`" (the comment is ALREADY WRONG: the value is 24 and 23 + 1 = 24, so the comment says 23 where it means the prior total; measured at HEAD `6df1fbbe`, `len(runner_shared.TERMINAL_STATES)` is 24). CASE 2, `tests/test_term.py::AuthoredSixteenColorPaletteTests::test_palette_coverage_named_colors_separations_and_collapses`, asserts `len(T.STAGE_COLOR_16) == 20` on the line AFTER `set(T.STAGE_COLOR_16) == set(LS.ALL_STAGES)`. The decisive evidence that Case 2's literal is the WRONG mechanism is in production code: `term.validate_16_color_palette`'s own docstring states "THE COVERAGE CHECK READS `lifecycle_style` RATHER THAN A LITERAL COUNT, deliberately. A hard-coded 'there must be 20 entries' is itself a second table that rots the moment the stage vocabulary changes". The test does the exact thing the code it tests documents as wrong.
- Scope: Delete BOTH redundant literals (and Case 1's incorrect comment), keeping every surrounding assertion, and add NOTHING in their place. BOTH CASES ARE PLAIN DELETIONS, because each collection's membership is already pinned absolutely in another file, so no coverage is lost either time. Case 1: `tests/test_terminal_status_vocabulary.py::test_terminal_states_union` asserts `TERMINAL_STATES` equals a hand-written 14-name canonical set unioned with a hand-written 10-entry alias map. Case 2: `tests/test_lifecycle_style.py::StageTableTests::test_stage_table_and_glyphs_progression` PARSES the spec's Section 5 table and asserts the module's 20 rows equal it field for field. THE ORIGINAL AUTHORING TREATED CASE 2 ASYMMETRICALLY (replacing the literal with a hand-transcribed 20-name frozenset) ON A PREMISE REVIEW MEASURED AND FALSIFIED: see the corrected F-4 and F-6, and F-12 on why adding such a list would re-create the very "tax on correct changes" this Set removes. EXCLUDES the third instance of this shape found by this plan's own scan (`tests/test_terminal_status_vocabulary.py`, `len(TERMINAL_STATES_CANONICAL) == 14`), which the backlog item does not name; it is recorded in Deferred with its reasoning rather than swept in.
- Scope-Paths: tests/test_reaskscore_composed.py, tests/test_term.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: aaoapo
- Set: structpin
- Order: 3
- Highest E allocated: 03
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 44c42h

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 44c42h verified (set structpin, attempt 1). [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261001-structpin-01-2je7m3-delete-redundant-len-swept-24-literal-from-test-ar.backlog.md: changed by the plan's approved execution (auto-reconciled by aw agy run)]
- 2026-10-01 approved (aw set): status set to approved

- 2026-09-30 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-401, PR-402, PR-403, PR-404 all FIXED, zero deferred, zero open findings. Structural lint `conforming` at `--phase author` and at `--phase review-finalize`. Reviewed at HEAD `b48bb220`; every measurement re-derived independently rather than read back. THE DIAGNOSIS IS CORRECT AND MOST FINDINGS REPRODUCE EXACTLY: F-1's AST scan returns the same 17 rows at the same line numbers with both targets present; F-2, F-3, F-5, F-8, F-10 (`55 passed in 7.47s`), F-9 and F-11 all verbatim; the `term.validate_16_color_palette` docstring and the P16 bullets are quoted accurately; the `b02ohu` deferral provenance and the `aaoapo` item text check out. BUT E-02's ENTIRE JUSTIFICATION WAS FALSIFIED, and with it the plan's central authored judgement that the two cases are asymmetric. PR-402 is the decisive finding: F-6 claimed no test pins the stage vocabulary, concluding that deleting Case 2's literal loses coverage and that a hand-transcribed 20-name frozenset must replace it. The pin EXISTS and the search missed it because its assertion never mentions `ALL_STAGES`: `tests/test_lifecycle_style.py::StageTableTests::test_stage_table_and_glyphs_progression` PARSES the spec's Section 5 table via `_parse_spec_section5()` and asserts `module_rows == spec_rows` over all 20 rows and 5 fields, with its helper docstring stating "Parsing rather than transcribing is the whole point". Measured: dropping any one of the 20 stages turns that test RED, including all three stages the edited test misses; it carries no marker and runs in the default suite (`1 passed in 0.14s`). PR-401: F-4's counterexample is also wrong. Its probe compared two SETS in isolation and never ran the test; re-measured by deleting the literal from the real test body and shrinking each stage in turn, 17 of 20 go RED with `KeyError` from `color_16_for_stage` inside the test's own separation and collapse assertions, `abandoned` (F-4's chosen victim) among them, leaving a residual gap of only 3 stages that F-6's pin then covers. New F-12 measures why a transcribed list would be actively harmful: in the only shape it would catch (a DELIBERATE, spec-amended vocabulary change) the parsed pin correctly agrees at 19 rows while the transcription goes red, so the list fires exactly when the change is right, which is the "tax on correct changes" this Set exists to remove and the "second table that rots" the production docstring rejects. E-02 IS THEREFORE NOW A PLAIN ONE-LINE DELETION like E-01, the diff is SMALLER than authored, OQ-01's answer is REVERSED from "pin it by name" to "delete it outright" with the reversal recorded rather than the question rewritten, and V-02 now demands a coverage-PRESERVATION demonstration (the surviving cross-file pin shown red) instead of a RED-then-GREEN on a new assertion. PR-403 corrected the Goal's overclaim that both tests would assert strictly MORE afterwards (they assert exactly as much, with one fewer thing to update) and recorded the one accepted residue in Under-scope. PR-404: the Deferred row for the third instance invited the reviewer to file an item; FILED as backlog `rdtme9`, and the row now carries it. Findings and four Decisions rows in `.aw/records/reviews/20260930-structpin-03-44c42h-delete-the-two-redundant-length-literals-that-restate-a-neig.review.md`. No production file and no test modified.
- 2026-09-30 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `aaoapo`, which plan `b02ohu` deferred to this carrier by name in two `## Deferred / out of scope` rows. Every claim below was MEASURED at HEAD `6df1fbbe` before being written, and one of the item's own premises was CORRECTED by that measurement rather than copied: the item's SUGGESTED FIX is "delete both literals and keep the set-equality assertions", and for Case 2 a plain deletion WOULD LOSE COVERAGE, because the surviving assertion is relative and a coordinated shrink of the palette and the stage vocabulary together passes it (demonstrated by construction in Findings F-4). E-02 therefore replaces rather than deletes. The item also asks to "Confirm first that no OTHER assertion in either test depends on the literal"; both tests were read in full and neither does (F-5).
- 2026-09-30 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Leave both tests with no literal that a legitimate addition to either collection can falsify, and lose no
coverage doing it.

The test of success is the same for both cases: the literal goes and nothing replaces it, because each
collection's membership is already pinned absolutely in another file that runs in the default suite
(Case 1 by a hand-written union of names, Case 2 by parsing the spec's normative Section 5 table). The
plan does NOT claim either test asserts strictly more afterwards; it claims each asserts exactly as much,
with one fewer thing to update when the collection legitimately grows. That is the whole benefit and it is
worth stating plainly rather than overselling.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the literal whose replacement already exists in another file

- [x] E-01 DELETE THE `len(runner_shared.TERMINAL_STATES) == 24` ASSERTION AND ITS INCORRECT COMMENT FROM `tests/test_reaskscore_composed.py::TestSharedConstants::test_terminal_states_three_copies_are_mutually_equal`, KEEPING ALL FOUR OTHER ASSERTIONS IN THAT TEST. Delete exactly two source lines: the comment reading "23 + `retired` (in-lane retirement, runner_shared.RETIRED_STATUS)." and the `self.assertEqual(len(runner_shared.TERMINAL_STATES), 24)` beneath it. DO NOT add a replacement in this file. The reason deletion is safe here (and, per the corrected F-6, is equally safe for Case 2) is that the exact membership of `TERMINAL_STATES` is pinned ABSOLUTELY in a different file: `tests/test_terminal_status_vocabulary.py::TestTerminalStatusVocabularyDefinitions::test_terminal_states_union` asserts `runner_shared.TERMINAL_STATES` equals `frozenset(EXPECTED_CANONICAL_STATES | set(EXPECTED_LEGACY_ALIASES.keys()))`, where both operands are hand-written module-level tables in that file (measured: 14 canonical names, 10 aliases, union 24). That assertion fixes every member by NAME, which is strictly stronger than fixing the count, so the literal is redundant against it and not merely against its own neighbours. The four retained assertions in the edited test are the real local invariants and are untouched: the two mutual-equality assertions across `oc_runipd`/`agy_runipd`/`runner_shared`, and the two `assertNotIn` assertions for the deliberately absent deferrable pair (`merge-retry`, `merge-unchecked`). VERIFY THE CROSS-FILE PIN IS LIVE BEFORE DELETING (V-01 makes this a stop condition): run `tests/test_terminal_status_vocabulary.py::TestTerminalStatusVocabularyDefinitions::test_terminal_states_union` and confirm it PASSES BY NAME and is not skipped. If it is absent or skipped, do not delete; report instead, because then the premise fails.
  - Depends on: none
  - Expected outcome: `tests/test_reaskscore_composed.py` contains no `len(runner_shared.TERMINAL_STATES)` assertion and no "23 + `retired`" comment (verified by search, pasted); the test retains and passes its two mutual-equality and two `assertNotIn` assertions; `test_terminal_states_union` confirmed passing by name before the deletion.
  - Execution state: performed

### Task group 2: the literal whose absolute pin lives in a spec-parsing test

- [x] E-02 DELETE THE `self.assertEqual(len(T.STAGE_COLOR_16), 20)` ASSERTION FROM `tests/test_term.py::AuthoredSixteenColorPaletteTests::test_palette_coverage_named_colors_separations_and_collapses`, KEEPING the preceding `set(T.STAGE_COLOR_16) == set(LS.ALL_STAGES)` and every later assertion in the test. Delete exactly one source line. DO NOT add a replacement in this file.

  THIS ITEM WAS A REPLACEMENT AND IS NOW A PLAIN DELETION, because review measurement falsified the premise that justified replacing (review PR-401/PR-402; see the corrected F-4 and F-6). The original E-02 argued that deletion would lose coverage because the surviving neighbour is relative and nothing else pins the stage vocabulary. BOTH halves are false. The vocabulary IS pinned, and by a strictly STRONGER mechanism than the transcription this item used to prescribe: `tests/test_lifecycle_style.py::StageTableTests::test_stage_table_and_glyphs_progression` PARSES the spec's Section 5 table with `_parse_spec_section5()` and asserts `module_rows == spec_rows` over all 20 rows and 5 fields, with its own docstring stating "Parsing rather than transcribing is the whole point: a transcription slip in any of 20 rows times 4 fields fails here instead of being read past". And the shrink this item was written to catch is caught anyway: measured, dropping any one of the 20 stages from `lifecycle_style` turns that spec-parsing test RED, and for 17 of the 20 the edited test itself also goes red via `KeyError` from `color_16_for_stage` in its own separation and collapse assertions.

  DO NOT REINSTATE A HAND-TRANSCRIBED STAGE LIST. It would duplicate the normative table a shipped test already parses, which is the second-table rot `term.validate_16_color_palette`'s docstring names and which `GUIDING_PRINCIPLES.md` P8 forbids; and in the only shape it would catch (a DELIBERATE, spec-amended vocabulary change) it goes red precisely when the change is correct, which is the "tax on correct changes" backlog `aaoapo` exists to remove.
  - Depends on: none
  - Expected outcome: `tests/test_term.py` contains no `len(T.STAGE_COLOR_16)` assertion (verified by search, pasted); the preceding palette-versus-`ALL_STAGES` equality and every later assertion survive verbatim; no stage-name list is added; the whole file passes; and the cross-file pin `tests/test_lifecycle_style.py::StageTableTests::test_stage_table_and_glyphs_progression` is confirmed passing BY NAME before the deletion.
  - Execution state: performed

### Task group 3: prove the shape is gone where this plan claims it is

- [x] E-03 RE-RUN THE REDUNDANT-LITERAL SCAN AND RECONCILE ITS SURVIVORS, because "the two I was sent for are gone" is a weaker claim than "no unaccounted instance of this shape remains in the files I touched". Re-run the AST scan recorded in F-1 over every `tests/**/*.py`: for each test function, collect `assertEqual(len(X), <int literal>)` and, separately, every operand of every other `assertEqual` in that same function (including the argument of a `set(...)` call), then report each subject appearing in both sets. That is the defect shape mechanically: a count literal standing beside an assertion that already constrains the same subject. Confirm the two rows this plan edits are ABSENT from the new output, and confirm the remaining rows are exactly the 15 the authoring run recorded (F-1 lists all 17). DO NOT edit any other row and DO NOT widen the scan's exclusions to make the output shorter; report any row that appeared since authoring, with its file and subject, so a human can file it. The scan's bound must be stated honestly in the report: it matches `assertEqual` only (not `assertEquals` aliasing through a helper, nor bare `assert len(x) == n`), so a pytest-style bare assert of the same shape would evade it; that bound is acceptable here because both target cases are `unittest`-style, and the scan's job is reconciliation of THIS plan's claim rather than a tree-wide guarantee.
  - Depends on: E-01, E-02
  - Expected outcome: pasted scan output showing neither `runner_shared.TERMINAL_STATES` nor `T.STAGE_COLOR_16` among the count-beside-equality rows, and the surviving row count reconciled against the authoring figure of 17 (expected 15); any new row named rather than silently absorbed.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `GUIDING_PRINCIPLES.md` P16 ("Test outcomes and behavior, never code structure or text") is the canonical home of this policy. Its "No count or census pins" bullet is the clause both literals violate. Its "Verify test sensitivity with mutation" bullet ("A test is only valid if breaking the underlying behavior makes the test fail") is why V-02 owes a demonstration that the SURVIVING cross-file pin still goes red, rather than only a green run of the edited file.
- THE PRODUCTION CODE UNDER TEST ALREADY ARGUES THIS PLAN'S CASE, which is the strongest single piece of evidence here. `term.validate_16_color_palette`'s docstring states: "THE COVERAGE CHECK READS `lifecycle_style` RATHER THAN A LITERAL COUNT, deliberately. A hard-coded 'there must be 20 entries' is itself a second table that rots the moment the stage vocabulary changes; asserting COVERAGE of the real vocabulary cannot rot." The test asserts the literal count the function it covers deliberately refuses to.
- The `structpin` Set's Order 01 (`b02ohu`) DEFERRED both of these cases to this carrier by name, in two `## Deferred / out of scope` rows each ending `- Carrier: aaoapo`, with the reason that they are counts over a RUNTIME DATA STRUCTURE rather than over code structure obtained by reading source. This plan is that carrier and its scope is exactly those two rows.
- Order 02 (`76ic0k`) installs a guard against NEW code-structure pins and deliberately does NOT detect this shape. Its scope is production-source reads (`inspect.getsource`, `ast.parse`); a count over a runtime collection is syntactically indistinguishable from a legitimate assertion about a collection of outputs, so no author-time guard covers what this plan fixes. This plan therefore needs no dependency on either sibling: it touches neither `Scope-Paths` entry of Order 02 and none of the five test files Order 01 edits.
- The suite is run BARE: `pyproject.toml` `addopts` supplies `-q -n auto --dist=worksteal` and a marker filter, so `python3 -m pytest` is already quiet, parallel and scoped. The execution contract forbids adding `-n0`, a second `-q`, or `-p no:randomly`. Use `-o addopts=""` only where a per-test count is genuinely needed.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measurements taken at HEAD `6df1fbbe`.

| Id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **THE DEFECT SHAPE OCCURS 17 TIMES, AND THE ITEM NAMES 2.** An AST scan over every `tests/**/*.py` for a subject appearing BOTH in an `assertEqual(len(X), <int>)` and in another `assertEqual` in the same function returns 17 rows. Both target cases are present. Most of the other 15 are legitimate (a count over a collection of OUTPUTS, for example `len(findings) == 1` in `tests/test_backlog_production.py::test_backlog_graduate_count`), which is exactly why no automated guard can catch this shape and why this plan edits only the two rows the item names. | Scan output includes `tests/test_reaskscore_composed.py:98 test_terminal_states_three_copies_are_mutually_equal len(runner_shared.TERMINAL_STATES)==24` and `tests/test_term.py:915 test_palette_coverage_named_colors_separations_and_collapses len(T.STAGE_COLOR_16)==20`; `TOTAL: 17` |
| F-2 | **BOTH LITERALS ARE CORRECT TODAY**, so this is a maintenance-cost change and not a bug fix, which is why `- Work-Kind: chore` is right. | `len(runner_shared.TERMINAL_STATES)` is 24; `len(T.STAGE_COLOR_16)` is 20; `len(LS.ALL_STAGES)` is 20; `set(T.STAGE_COLOR_16) == set(LS.ALL_STAGES)` is True |
| F-3 | **CASE 1'S MEMBERSHIP IS PINNED ABSOLUTELY IN ANOTHER FILE, so deleting its literal loses nothing.** `tests/test_terminal_status_vocabulary.py::test_terminal_states_union` asserts `TERMINAL_STATES` equals the union of two hand-written tables in that file, fixing all 24 members BY NAME. A name-level pin subsumes a count-level one. | `EXPECTED_CANONICAL_STATES` has 14 members, `EXPECTED_LEGACY_ALIASES` has 10 keys, union 24; the test body reads `self.assertEqual(runner_shared.TERMINAL_STATES, expected_union)` |
| F-4 | **FALSIFIED AT REVIEW (PR-401). THE PROBE TESTED ONE LINE, NOT THE TEST, AND ITS CHOSEN VICTIM IS CAUGHT BY A LATER ASSERTION.** The original row claimed a coordinated shrink removing `abandoned` escapes every surviving assertion, concluding that plain deletion loses coverage and that E-02 must replace rather than delete. The probe compared only the two SETS, in isolation, and never ran the test. RE-MEASURED by deleting the literal from the real test body and running it under a coordinated shrink of each of the 20 stages in turn: 17 of 20 go RED with `KeyError: '<stage>'`, raised by `color_16_for_stage` inside the test's OWN separation and collapse assertions, `abandoned` among them (it is a member of the gray collapse group). Only 3 stages escape: `authority-queued`, `reusable`, `review-queued`, the three the test never names. So the specific counterexample the plan was built on does not hold, and the residual gap is 3 stages rather than all 20. F-6 then removes even that gap. | Probe extracting the real test body, deleting the `len` line, and running it under `mock.patch.object` coordinated shrinks of each stage: `17 ERROR (KeyError)`, `3 PASS (UNDETECTED)` -> `['authority-queued', 'reusable', 'review-queued']`; plus the original set-only comparison reproduced (`abandoned` set-equality True at len 19) showing why the narrower probe misled. |
| F-5 | **NO OTHER ASSERTION IN EITHER TEST DEPENDS ON EITHER LITERAL**, which the backlog item explicitly asks to confirm before fixing. Both tests were read in full. Case 1's other four assertions are two cross-host mutual equalities and two `assertNotIn`. Case 2's later assertions all iterate or subscript the palette (named-color range check, three explicit separations, the `REQUIRED_16_COLOR_SEPARATIONS` loop, two collapse-group checks, the unnamed-merge check); none reads a length or an index that 20 fixes. | Both test bodies read end to end |
| F-6 | **FALSIFIED AT REVIEW (PR-402), AND THIS IS THE FINDING THAT DECIDES THE PLAN. THE STAGE VOCABULARY IS PINNED, BY PARSING THE SPEC, WHICH IS STRICTLY STRONGER THAN THE TRANSCRIPTION E-02 PROPOSED.** The original row concluded from an `ALL_STAGES` search that nothing pins the vocabulary, making E-02's replacement necessary. The search was too narrow: the pin does not mention `ALL_STAGES` in its assertion. `tests/test_lifecycle_style.py::StageTableTests::test_stage_table_and_glyphs_progression` calls `_parse_spec_section5()`, which reads the spec file and extracts Section 5's table, and asserts `module_rows == spec_rows` across all 20 rows and 5 fields (stage, unicode, ascii, color, bold). Its helper docstring states the intent verbatim: "Parsing rather than transcribing is the whole point: a transcription slip in any of 20 rows times 4 fields fails here instead of being read past." Measured: dropping any one of the 20 stages from `lifecycle_style` turns that test RED, INCLUDING all three stages F-4's corrected probe found the edited test misses. The test carries no `slow`/`livecorpus` marker and runs in the default suite (verified passing by name). So after a plain deletion the vocabulary remains pinned in both directions, against the NORMATIVE source rather than against a hand-copied list. | `rg -n "ALL_STAGES" tests/` returns four relative sites as the original row said, which is why the narrow search missed the pin; the pin itself is `tests/test_lifecycle_style.py` `_parse_spec_section5` + `self.assertEqual(module_rows, spec_rows)`. Probe dropping each stage from `_STAGE_ROWS`/`STAGES`/`STAGE_ORDER`/`ALL_STAGES` under `mock.patch.object`: the spec-parse test is RED for all of `authority-queued`, `reusable`, `review-queued`, `abandoned`. `python3 -m pytest tests/test_lifecycle_style.py::StageTableTests::test_stage_table_and_glyphs_progression -o addopts="" -q` -> `1 passed in 0.14s`. |
| F-12 | **THE ONLY CHANGE A HAND-TRANSCRIBED LIST WOULD CATCH IS A CORRECT ONE, SO ADDING IT WOULD RE-CREATE THE DEFECT THIS SET EXISTS TO REMOVE (review PR-402).** Simulating a fully coordinated, deliberate vocabulary removal (the spec's Section 5 row deleted TOO, then the module and the palette), the spec-parsing assertion legitimately AGREES (`module_rows == spec_rows` is True at 19 rows), because the spec is the normative source and it was amended. A hand-written 20-name frozenset would go RED there, i.e. exactly when the change is correct and approved. That is the "tax on correct changes" backlog `aaoapo` and `5zyuc8` describe, and paying it in a second table is what `term.validate_16_color_palette`'s docstring calls "a second table that rots" and what `GUIDING_PRINCIPLES.md` P8 forbids duplicating. | Probe patching `tests.test_lifecycle_style.SPEC_PATH` to a spec copy with the `reusable` row removed, alongside the module and palette shrink: `spec rows: 19  module rows: 19`, `module_rows == spec_rows: True`, while the edited `test_term` (literal deleted) is green. |
| F-7 | **THE NORMATIVE SOURCE FOR THE TWENTY NAMES IS THE SPEC, AND THE SUITE ALREADY READS IT DIRECTLY.** Still true as measured, but it no longer supports a transcription (see F-6): since the spec IS the source and a shipped test PARSES it, transcribing those names into a test would be a copy of a table the suite already compares against. `lifecycle_style` derives `ALL_STAGES` from a table it documents as spec-transcribed, and `STAGE_ORDER` is "Derived from the rows so it can never drift from the table"; the module additionally exposes each stage as a NAMED CONSTANT with the comment "as named constants so a consumer never spells one as a bare literal", which is a further reason not to write 20 bare string literals into a test. | Spec `cross-artifact-lifecycle-symbols-and-ansi-status-styling` Section 5's table has exactly 20 data rows (counted by parsing the heading-bounded segment); `lifecycle_style.py` comments read "The twenty semantic stages", "The NORMATIVE table, transcribed row for row from spec Section 5 IN SPEC ORDER", "as named constants so a consumer never spells one as a bare literal", and `ALL_STAGES: FrozenSet[str] = frozenset(STAGE_ORDER)` |
| F-8 | **CASE 1'S COMMENT IS ALREADY WRONG, which is the staleness the item predicts, arrived early.** It reads "23 + `retired`" beside an assertion of 24; the sum of the comment's own terms is 24, so the comment states a prior total as if it were the current one. E-01 deletes the comment with the assertion rather than correcting it, since the assertion it explains is going. | Source comment "# 23 + `retired` (in-lane retirement, runner_shared.RETIRED_STATUS)." sits immediately above `self.assertEqual(len(runner_shared.TERMINAL_STATES), 24)` |
| F-9 | **THE PRODUCTION VALIDATOR ENFORCES CASE 2'S COVERAGE AT IMPORT ALREADY, and it fails by NAME**, so the test's coverage half is a second line of defence and the literal a third that adds nothing. `validate_16_color_palette()` is called at module import. | `term.py` calls `validate_16_color_palette()` at module level; the function raises on `sorted(ALL_STAGES - set(STAGE_COLOR_16))` naming the missing stages, and on the reverse difference, and is followed by the separation and collapse checks |
| F-10 | **BOTH TARGET FILES AND THE CROSS-FILE PIN ARE GREEN AT AUTHORING**, so any red at execution is attributable to this plan's edits. | `python3 -m pytest tests/test_reaskscore_composed.py tests/test_term.py tests/test_terminal_status_vocabulary.py -o addopts="" -q` reports `55 passed in 3.91s` |
| F-11 | **THE SET'S SIBLINGS DO NOT COLLIDE WITH THIS PLAN.** Order 01 (`b02ohu`) declares five `Scope-Paths` and none is a file this plan edits; Order 02 (`76ic0k`) declares `tests/test_no_code_structure_pins.py, CONTRIBUTING.md`. So `- Item-Dependencies: none` is correct and no ordering constraint exists within the Set. | Both sibling plans' `- Scope-Paths:` lines read at authoring |

## Proposed changes (ordered, validatable)

1. E-01 deletes Case 1's literal and its stale comment. Smallest change, and it is a pure deletion because F-3 shows the absolute pin lives elsewhere.
2. E-02 deletes Case 2's literal, because the corrected F-6 shows the stage vocabulary is already pinned by a spec-parsing test that goes red for every stage, the corrected F-4 shows the edited test itself already catches 17 of 20, and F-12 shows a hand-transcribed replacement would fire only on correct, spec-approved changes.
3. E-03 re-runs the F-1 scan and reconciles its survivors, so the plan's completeness claim is measured rather than asserted.

E-01 and E-02 are INDEPENDENT (different files, different collections) and may be done in either order. E-03 depends on both.

## Deferred / out of scope (with reason)

- `tests/test_terminal_status_vocabulary.py::TestTerminalStatusVocabularyDefinitions::test_canonical_terminal_states_set` asserts `len(runner_shared.TERMINAL_STATES_CANONICAL) == 14` on the line after asserting `runner_shared.TERMINAL_STATES_CANONICAL == EXPECTED_CANONICAL_STATES`. This is the SAME defect shape as the two in scope, found by this plan's own scan (F-1), and its literal is strictly redundant against a full name-level equality on the preceding line. It is nonetheless OUT OF SCOPE: backlog `aaoapo` names exactly two cases and this is a third, in a third file that this plan otherwise only READS (E-01 depends on that file's `test_terminal_states_union` passing, so editing it in the same change would entangle the premise with the edit). Widening would be the opportunistic scope growth the execution contract forbids. FILED AT REVIEW as backlog `rdtme9`, so the observation is now carried by a live item rather than resting on this row alone.
  - Carrier: rdtme9
  - Carrier-Evidence: .aw/records/backlog/open/20260930-structpin-01-rdtme9-redundant-canonical-count-literal.backlog.md
- The other 14 rows from the F-1 scan are NOT this defect. A count over a collection of OUTPUTS (`len(findings) == 1`, `len(queue) == 22`, `len(runs) == 4`) is a legitimate assertion about what the code produced, which is precisely what P16 directs an author toward. They are recorded only so E-03's reconciliation has a denominator.
  - Carrier-Declined: NOTHING IS OWED, because this row records a NEGATIVE finding rather than deferred work. The scan in F-1 is deliberately over-inclusive (it matches the SHAPE `assertEqual(len(X), <int>)` beside another assertion on `X`), and these 14 rows were examined and judged CORRECT: a count over a collection the code just produced is precisely what P16's "Exercise the code ... assert observable outputs" bullet directs an author toward, so changing them would weaken real assertions. There is no gap for a later owner to close and filing an item would assert a defect that was measured not to exist.
- The stale comment in Case 1 (F-8) is deleted rather than corrected, because the assertion it annotates is being removed. No separate documentation fix is owed.
  - Carrier-Declined: Nothing is owed and nothing survives to carry: E-01 deletes the comment in the same edit as the assertion it annotates, so this row records WHY the comment is not separately corrected rather than deferring any work. Correcting a comment that is about to be deleted would be churn, and leaving it behind would strand a note explaining an assertion that no longer exists.

## Scope check

- Over-scope: none. Two `Scope-Paths` entries, both test files, one test edited in each; both edits are deletions (two lines and one line respectively) and nothing is added. No production module is touched: this plan changes how existing behavior is ASSERTED, never the behavior. After review the diff is SMALLER than authored, because E-02 no longer adds a 20-name frozenset.
- Under-scope: this plan does not prevent a new count-beside-equality literal being written tomorrow, and no guard can reasonably do so (F-1 shows the shape is indistinguishable from legitimate output-count assertions at the syntax level, which is also why Order 02's guard deliberately excludes it). It also leaves the third instance named in Deferred unfixed, though it is now FILED as backlog `rdtme9` rather than unfiled. AND IT ACCEPTS ONE NARROW RESIDUE, stated because E-02 changed shape at review: after the deletion, a change that removes a stage from `lifecycle_style` and its palette entry while ALSO amending the spec's Section 5 table is detected by NO test (F-12 measures it). That is deliberate: such a change is a deliberate, spec-approved vocabulary amendment, and a test that failed on it would be the tax this Set exists to remove, not a caught defect. The spec review, not a transcribed list in a test, is the control for that case.

## Required tests / validation

Every item's validation demands actual pasted output. The bare-suite baseline measured at authoring HEAD `6df1fbbe` is:

```
NOTE: 207 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
3387 passed, 2 skipped, 3 warnings in 93.36s (0:01:33)
```

Re-derive that baseline at execution rather than trusting it; the tree moves under concurrent lanes. THE TEST COUNT IS EXPECTED TO BE UNCHANGED by this plan: no test is added or removed, only assertions inside two existing tests change. A count that moves must be explained rather than accepted, and a count that FALLS by one or two is the specific failure mode to watch for (an assertion deleted along with its enclosing method by an over-broad edit).

E-02 requires a COVERAGE-PRESERVATION demonstration, per P16's mutation bullet: because this item now DELETES rather than replaces, the thing to prove is not that a new assertion is non-vacuous but that the coverage survives elsewhere. V-02 therefore demands that the cross-file spec-parsing pin be shown RED under a coordinated shrink, including for one of the three stages the edited test does not itself name. A plan that deletes an assertion owes evidence that nothing stopped being covered, and that is that evidence.

## Spec / documentation sync

N/A. `GUIDING_PRINCIPLES.md` P16 already states the policy this plan applies and restating it would be the duplication P8 forbids. No `.spec.md` file is amended and none appears in `Scope-Paths`: E-02 TRANSCRIBES the stage vocabulary from spec `cross-artifact-lifecycle-symbols-and-ansi-status-styling` Section 5 and cites it, which is a read of a normative source rather than a change to a contract. If an executor finds the spec's Section 5 table and `lifecycle_style.STAGE_ORDER` DISAGREE, that is a real defect in production data and a new carrier, not a licence to amend either here: stop and report it.

## Open questions

### OQ-01: Should E-02 pin the stage vocabulary by name, or delete the literal outright?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE as DELETE IT OUTRIGHT. THE ANSWER WAS REVERSED AT REVIEW (PR-402), and the reversal is recorded rather than the question rewritten, because the original answer ('pin it by name') rested on two premises that measurement falsified. FIRST, the claimed coverage loss does not exist. The original rationale cited F-4's coordinated shrink and F-6's 'no other test pins the vocabulary'. Re-measured: the shrink is caught for 17 of the 20 stages by the edited test's OWN later assertions (`KeyError` from `color_16_for_stage`), and for ALL 20 by `tests/test_lifecycle_style.py::StageTableTests::test_stage_table_and_glyphs_progression`, which PARSES the spec's Section 5 table and asserts the module's rows equal it field for field. F-6's search missed that pin because the pin's assertion never mentions `ALL_STAGES`. So there is no regression class left undetected and the 'DO NOT WEAKEN AN ASSERTION' rule is not engaged: deleting a literal whose invariant a stronger test already carries weakens nothing. SECOND, the proposed replacement is the WRONG mechanism here even though a named vocabulary assertion is a legitimate form in general. The repository precedent the original rationale cited (`tests/test_terminal_status_vocabulary.py` writing out 14 names) applies where NO parsed normative source exists; here one does, and `lifecycle_style` additionally exposes every stage as a named constant precisely 'so a consumer never spells one as a bare literal'. Transcribing 20 bare literals into a test would duplicate a table the suite already parses, which is the 'second table that rots' `term.validate_16_color_palette`'s docstring rejects and the duplication P8 forbids. F-12 measures the decisive consequence: in the only shape a transcribed list would catch (a DELIBERATE, spec-amended vocabulary change) the parsed pin correctly agrees while the transcription goes red, so the list would fire exactly when the change is right. That is the 'tax on correct changes' backlog `aaoapo` exists to remove, and adding it here would have made this plan reintroduce its own Set's defect.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: FIRST, the stop condition, taken BEFORE the deletion: a pasted run of `tests/test_terminal_status_vocabulary.py::TestTerminalStatusVocabularyDefinitions::test_terminal_states_union` showing it PASSED BY NAME (not skipped, not deselected), plus the pasted member counts of `EXPECTED_CANONICAL_STATES` and `EXPECTED_LEGACY_ALIASES` and their union (authoring baseline to reproduce or refute: 14, 10, 24). If that test is absent, skipped, or no longer asserts full membership, DO NOT DELETE; report and stop, because E-01's premise has failed. SECOND: a search over `tests/test_reaskscore_composed.py` for `len(runner_shared.TERMINAL_STATES)` and for `23 +` each returning zero matches, pasted. THIRD: a pasted run of `tests/test_reaskscore_composed.py` showing green, with a quoted excerpt of the edited test proving all four retained assertions survived (both mutual equalities and both `assertNotIn`).
  - Observed evidence: PASS. Stop condition verified live (1 passed in 0.29s; counts 14, 10, union 24), zero matches for len literal and stale comment in tests/test_reaskscore_composed.py, and all 11 tests pass with all 4 retained assertions intact.
    1. Stop condition run BEFORE deletion:
    ```
    $ python3 -m pytest tests/test_terminal_status_vocabulary.py::TestTerminalStatusVocabularyDefinitions::test_terminal_states_union -o addopts="" -v
    tests/test_terminal_status_vocabulary.py::TestTerminalStatusVocabularyDefinitions::test_terminal_states_union PASSED [100%]
    ============================== 1 passed in 0.29s ===============================
    ```
    Member counts check:
    ```
    EXPECTED_CANONICAL_STATES: 14
    EXPECTED_LEGACY_ALIASES: 10
    union: 24
    ```
    2. Searches over `tests/test_reaskscore_composed.py`:
    ```
    $ grep -n "len(runner_shared.TERMINAL_STATES)" tests/test_reaskscore_composed.py || echo "NO MATCHES FOR len(runner_shared.TERMINAL_STATES)"
    NO MATCHES FOR len(runner_shared.TERMINAL_STATES)

    $ grep -n "23 +" tests/test_reaskscore_composed.py || echo "NO MATCHES FOR 23 +"
    NO MATCHES FOR 23 +
    ```
    3. Run of `tests/test_reaskscore_composed.py`:
    ```
    $ python3 -m pytest tests/test_reaskscore_composed.py -o addopts="" -v
    tests/test_reaskscore_composed.py::TestSharedConstantsByteIdenticalAndUnwidened::test_execute_reporting_success_states_is_derived_by_subtraction PASSED [  9%]
    tests/test_reaskscore_composed.py::TestSharedConstantsByteIdenticalAndUnwidened::test_terminal_states_three_copies_are_mutually_equal PASSED [ 18%]
    tests/test_reaskscore_composed.py::TestSharedConstantsByteIdenticalAndUnwidened::test_reexports_are_identical_objects PASSED [ 27%]
    tests/test_reaskscore_composed.py::TestSharedConstantsByteIdenticalAndUnwidened::test_five_constants_eight_definition_sites_values_and_types PASSED [ 36%]
    tests/test_reaskscore_composed.py::TestReconstructShapeAComposed::test_shape_a_rescued_turn_rescores_and_siblings_do_not_cascade[agy_runipd] PASSED [ 45%]
    tests/test_reaskscore_composed.py::TestReconstructShapeAComposed::test_shape_a_rescued_turn_rescores_and_siblings_do_not_cascade[oc_runipd] PASSED [ 54%]
    tests/test_reaskscore_composed.py::TestReconstructShapeBAndCollisionExclusivity::test_shape_b_zero_work_turn_retried_once_within_budget[oc_runipd] PASSED [ 63%]
    tests/test_reaskscore_composed.py::TestReconstructShapeBAndCollisionExclusivity::test_exclusivity_argument_holds_in_general_from_two_load_bearing_conditions PASSED [ 72%]
    tests/test_reaskscore_composed.py::TestReconstructShapeBAndCollisionExclusivity::test_collision_case_truncated_and_rescued_is_rescored_and_not_retried[agy_runipd] PASSED [ 81%]
    tests/test_reaskscore_composed.py::TestReconstructShapeBAndCollisionExclusivity::test_shape_b_zero_work_turn_retried_once_within_budget[agy_runipd] PASSED [ 90%]
    tests/test_reaskscore_composed.py::TestReconstructShapeBAndCollisionExclusivity::test_collision_case_truncated_and_rescued_is_rescored_and_not_retried[oc_runipd] PASSED [100%]
    ============================== 11 passed in 1.85s ==============================
    ```
    Quoted excerpt of edited test proving four retained assertions:
    ```python
    85:     def test_terminal_states_three_copies_are_mutually_equal(self) -> None:
    86:         """Assert that all three copies of TERMINAL_STATES are mutually equal and contain no deferrable states."""
    87:         self.assertEqual(
    88:             set(oc_runipd.TERMINAL_STATES),
    89:             set(agy_runipd.TERMINAL_STATES),
    90:             "oc_runipd and agy_runipd TERMINAL_STATES must be equal",
    91:         )
    92:         self.assertEqual(
    93:             set(oc_runipd.TERMINAL_STATES),
    94:             set(runner_shared.TERMINAL_STATES),
    95:             "host TERMINAL_STATES and runner_shared.TERMINAL_STATES must be equal",
    96:         )
    97:         # Deferrable pair is deliberately absent
    98:         self.assertNotIn("merge-retry", runner_shared.TERMINAL_STATES)
    99:         self.assertNotIn("merge-unchecked", runner_shared.TERMINAL_STATES)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: FIRST, the stop condition, taken BEFORE the deletion: a pasted run of `tests/test_lifecycle_style.py::StageTableTests::test_stage_table_and_glyphs_progression` showing it PASSED BY NAME (not skipped, not deselected), which is the cross-file pin that makes this deletion safe. If it is absent, skipped, or no longer parses the spec and compares it to the module table, DO NOT DELETE; report and stop, because E-02's premise has failed exactly as the original premise did. SECOND: a search over `tests/test_term.py` for `len(T.STAGE_COLOR_16)` returning zero matches, pasted, plus a search confirming NO stage-name list was added (the diff must be a one-line deletion; paste `git diff -- tests/test_term.py`). THIRD: the COVERAGE-PRESERVATION demonstration, which replaces the original RED-then-GREEN and is the load-bearing evidence for this item. Apply a coordinated shrink (drop one stage from `lifecycle_style`'s rows, `STAGES`, `STAGE_ORDER` and `ALL_STAGES` AND its `STAGE_COLOR_16` entry, via `mock.patch.object` as the neighbouring `test_validator_rejects_corrupted_palettes` does) and paste, for at least one of `authority-queued`, `reusable` or `review-queued` (the three the edited test does not itself name, per the corrected F-4) plus one stage it does name: that `test_stage_table_and_glyphs_progression` goes RED in both cases. That is the proof the vocabulary is still pinned after the deletion. Then revert and paste the pass. FOURTH: a pasted `python3 -m pytest tests/test_term.py` showing green.
  - Observed evidence: PASS. Stop condition verified live (1 passed in 0.10s), zero matches for len(T.STAGE_COLOR_16) in tests/test_term.py with one-line deletion diff, coverage preservation verified red under coordinated shrink for reusable, authority-queued, and abandoned, unperturbed test passes, and full test_term.py passes (28 passed in 5.99s).
    1. Stop condition run BEFORE deletion:
    ```
    $ python3 -m pytest tests/test_lifecycle_style.py::StageTableTests::test_stage_table_and_glyphs_progression -o addopts="" -v
    tests/test_lifecycle_style.py::StageTableTests::test_stage_table_and_glyphs_progression PASSED [100%]
    ============================== 1 passed in 0.10s ===============================
    ```
    2. Search over `tests/test_term.py` for `len(T.STAGE_COLOR_16)` and git diff:
    ```
    $ grep -n "len(T.STAGE_COLOR_16)" tests/test_term.py || echo "NO MATCHES FOR len(T.STAGE_COLOR_16)"
    NO MATCHES FOR len(T.STAGE_COLOR_16)

    $ git diff -- tests/test_term.py
    diff --git a/tests/test_term.py b/tests/test_term.py
    index 9601697a4..c59cdd8e0 100644
    --- a/tests/test_term.py
    +++ b/tests/test_term.py
    @@ -912,7 +912,6 @@ class ColorDepthPrecedenceTests(_DepthTestBase):
     class AuthoredSixteenColorPaletteTests(unittest.TestCase):
         def test_palette_coverage_named_colors_separations_and_collapses(self):
             self.assertEqual(set(T.STAGE_COLOR_16), set(LS.ALL_STAGES))
    -        self.assertEqual(len(T.STAGE_COLOR_16), 20)

             named = set(range(30, 38)) | set(range(90, 98))
             wrong = {s: c for s, c in T.STAGE_COLOR_16.items() if c not in named}
    ```
    3. Coverage-preservation demonstration (unnamed `reusable` and `authority-queued`, named `abandoned`, followed by unperturbed revert):
    ```
    --- Unnamed stage 1: reusable ---
    === Running probe for victim: reusable ===
    test_stage_table_and_glyphs_progression (tests.test_lifecycle_style.StageTableTests.test_stage_table_and_glyphs_progression) ... FAIL
    AssertionError: Lists differ: [('fo[500 chars]), ('parked', '◇', 'P', 244, False), ('superse[127 chars]lse)] != [('fo[500 chars]), ('reusable', '↻', '~', 81, False), ('parked[162 chars]lse)]
    First differing element 14:
    ('parked', '◇', 'P', 244, False)
    ('reusable', '↻', '~', 81, False)
    FAILED (failures=1)
    wasSuccessful: False

    --- Unnamed stage 2: authority-queued ---
    === Running probe for victim: authority-queued ===
    test_stage_table_and_glyphs_progression (tests.test_lifecycle_style.StageTableTests.test_stage_table_and_glyphs_progression) ... FAIL
    AssertionError: Lists differ: [('fo[70 chars]), ('ready', '◕', '>', 45, True), ('reviewing'[548 chars]lse)] != [('fo[70 chars]), ('authority-queued', '◑', 'A', 135, False),[592 chars]lse)]
    First differing element 2:
    ('ready', '◕', '>', 45, True)
    ('authority-queued', '◑', 'A', 135, False)
    FAILED (failures=1)
    wasSuccessful: False

    --- Named stage: abandoned ---
    === Running probe for victim: abandoned ===
    test_stage_table_and_glyphs_progression (tests.test_lifecycle_style.StageTableTests.test_stage_table_and_glyphs_progression) ... FAIL
    AssertionError: Lists differ: [('fo[607 chars]), ('unknown', '?', '?', 244, False), ('none',[18 chars]lse)] != [('fo[607 chars]), ('abandoned', '∅', 'N', 244, False), ('unkn[55 chars]lse)]
    First differing element 17:
    ('unknown', '?', '?', 244, False)
    ('abandoned', '∅', 'N', 244, False)
    FAILED (failures=1)
    wasSuccessful: False

    --- Unperturbed run (revert) ---
    test_stage_table_and_glyphs_progression (tests.test_lifecycle_style.StageTableTests.test_stage_table_and_glyphs_progression) ... ok
    OK
    Unperturbed wasSuccessful: True
    ```
    4. Run of `tests/test_term.py`:
    ```
    $ python3 -m pytest tests/test_term.py -o addopts="" -v
    ============================== 28 passed in 5.99s ==============================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the re-run F-1 scan output, pasted in full, showing neither `runner_shared.TERMINAL_STATES` nor `T.STAGE_COLOR_16` among the count-beside-equality rows, and a stated reconciliation of the surviving row count against the authoring figure of 17 (expected 15, since this plan removes exactly two rows). Any row present now that was absent at authoring must be NAMED with its file and subject rather than absorbed into the total. Plus a pasted bare `python3 -m pytest`, green, with its `N passed` line and the count reconciled against a re-derived execution baseline: the expected delta is ZERO, and any change must be explained (a FALL of one or two is the specific failure mode to investigate, since it would indicate an edit removed a test method rather than an assertion).
  - Observed evidence: PASS. Re-run AST scan confirms neither target literal present, 15 authoring rows survived, 1 new row in test_artifact_audit.test_terminal_states_tolerance_and_counterexample_trichotomy reconciled and filed as backlog chore 2je7m3 (total 16), and bare suite passes with delta zero (4112 passed vs 4112 baseline).
    1. Re-run F-1 AST scan output:
    ```
    tests/test_artifact_audit.py:515 test_terminal_states_tolerance_and_counterexample_trichotomy len(swept)==24
    tests/test_backlog_production.py:220 test_backlog_graduate_count len(findings)==1
    tests/test_cli.py:1168 test_no_write_paths_asserted_by_bytes len(prompts)==1
    tests/test_history_provenance.py:50 test_a_legacy_item_keeps_every_prior_record_through_a_transition len(before)==3
    tests/test_layout.py:40 test_logical_roots_are_the_four len(self.model.logical_roots)==4
    tests/test_layout.py:49 test_root_classes_are_the_six_and_are_not_collapsed len(self.model.root_classes)==6
    tests/test_layout.py:214 test_primary_types_equal_the_live_known_primary_types len(self.model.primary_types())==9
    tests/test_layout.py:245 test_traversal_exclusions_equal_the_live_set_as_sets len(self.model.traversal_exclusions)==7
    tests/test_model_vocab.py:139 test_01_seed_equivalence len(models)==13
    tests/test_model_vocab.py:140 test_01_seed_equivalence len(norms)==22
    tests/test_oc_runipd.py:122 test_selector_deduplication_supports_interleaved_set_resume len(queue)==22
    tests/test_oc_runipd.py:5571 test_alias_refusal_and_acceptance len(runs)==1
    tests/test_root_run_scratch_migration.py:321 test_nothing_is_lost_the_path_sets_are_equal_modulo_the_prefix len(before)==6
    tests/test_run_viewer.py:1594 test_detailed_resolver_and_error_handling len(runs)==1
    tests/test_spec_production.py:213 test_spec_plan_count len(findings)==1
    tests/test_terminal_status_vocabulary.py:74 test_canonical_terminal_states_set len(runner_shared.TERMINAL_STATES_CANONICAL)==14
    TOTAL: 16
    ```
    Neither `runner_shared.TERMINAL_STATES` nor `T.STAGE_COLOR_16` appears.
    Reconciliation against authoring figure of 17:
    - Authoring had 17 rows.
    - Two rows deleted by this plan: `tests/test_reaskscore_composed.py:98` and `tests/test_term.py:915`.
    - Exactly 15 authoring rows survived.
    - 1 new row appeared since authoring (added in commit 7ffd3f8a5): `tests/test_artifact_audit.py:515 test_terminal_states_tolerance_and_counterexample_trichotomy len(swept)==24`. This new finding was filed as backlog chore item `2je7m3` in Set `structpin`.
    - Total: 15 surviving + 1 new = 16 rows.

    2. Bare `python3 -m pytest` suite count reconciliation:
    - Execution baseline at turn start:
    ```
    NOTE: 231 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    4112 passed, 2 skipped, 3 warnings in 90.94s (0:01:30)
    ```
    - Post-edit validation:
    ```
    NOTE: 231 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    4112 passed, 2 skipped, 3 warnings in 161.87s (0:02:41)
    ```
    - Delta: ZERO (4112 passed vs 4112 passed).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required by the count thresholds (3 E-leaves in 3 groups, well under the 18-leaf / 5-group bars).

EXECUTE ONLY WHAT THIS PLAN DECLARES. The two `Scope-Paths` entries are the whole authorized surface. This plan changes how existing behavior is ASSERTED and must not change the behavior itself, so if execution appears to require editing a module under `agent_workflows/`, STOP and report: a replacement that needs a production edit to pass has found a real defect, which is a new carrier rather than a widening of this one. The one sanctioned TEMPORARY exception is V-02's coverage-preservation demonstration, which deliberately perturbs `lifecycle_style` and/or `term` IN MEMORY (via `mock.patch.object`, not by editing a file) to prove the surviving cross-file pin still fires; nothing is written to a production module, and the pasted evidence must show the unperturbed pass afterwards.

DO NOT WEAKEN AN ASSERTION TO MAKE IT PASS. This plan DELETES two assertions, so the honesty obligation is specifically to prove nothing stopped being covered: each `V-*` demands that the cross-file pin which carries the coverage be shown live BEFORE the deletion (V-01 for `TERMINAL_STATES`, V-02 for the stage vocabulary), and each makes an absent or skipped pin a STOP condition rather than something to work around. If either pin is missing, leave that literal in place, mark the item incomplete, and report it: a redundant literal honestly labelled is better than a silent coverage loss.

BOTH CASES ARE NOW PLAIN DELETIONS, AND THAT SYMMETRY IS THE REVIEWED CONCLUSION, NOT A SIMPLIFICATION. The original plan made E-02 a REPLACEMENT (a hand-transcribed 20-name frozenset) and warned an executor not to "simplify" it into a deletion. Review measured that premise and falsified it: the stage vocabulary IS pinned, by `tests/test_lifecycle_style.py::StageTableTests::test_stage_table_and_glyphs_progression` PARSING the spec's Section 5 table, which is stronger than any transcription and goes red for every one of the 20 stages (corrected F-6); the edited test itself already catches 17 of 20 via `KeyError` (corrected F-4); and a transcribed list would fire only on a correct, spec-approved vocabulary change, which is the tax this Set removes (F-12). SO DO NOT ADD A STAGE-NAME LIST TO `tests/test_term.py`. If you believe one is needed, you are re-deriving a premise that was measured false; re-read F-4, F-6 and F-12 and report rather than adding a second table.
