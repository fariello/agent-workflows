# IPD: Correct the falsey FORCE_COLOR wording in the published color precedence contract and pin its worked-cases table to measured behavior

- Date: 2026-09-28
- Kind: child
- Concern: `docs/cli-output-contract.md` section 1.1 row 2 is the NORMATIVE published statement of the color environment layer, and it reads "`NO_COLOR` (any value, including empty) disables, UNLESS `FORCE_COLOR` is set; `FORCE_COLOR` (any non-empty value) enables". Taken at its word that makes `FORCE_COLOR=0` do two things: cancel `NO_COLOR` (it IS set) and enable color (`0` is non-empty). The shipped code does NEITHER, re-measured at HEAD `c763a2fa`. The affected reader is precisely an external script author choosing how to suppress color in CI, and the affected user is precisely one who set `NO_COLOR`, so the wrong expectation lands on the accessibility case. The same stale claim is repeated in `docs/cli-human-guide.md`, where it is additionally missing the `--color` flag layer that has shipped since it was written.
- Scope: IN: (a) reword section 1.1 row 2 of `docs/cli-output-contract.md` to state the falsey set explicitly and name the single predicate, and extend the worked-cases table beneath it with the six cells that discriminate a falsey `FORCE_COLOR` (five the current wording gets wrong, plus the one that proves a falsey value is not a second `NO_COLOR`); (b) correct the same claim in `docs/cli-human-guide.md`'s environment-precedence sentence, which is both stale on falsey values and silent on the flag layer; (c) make the worked-cases table EXECUTABLE by adding a test that parses it out of the file and drives `term.should_color` per row, so the document cannot silently go stale again; (d) close the measured coverage gap that let this survive, namely that `tests/test_term.py`'s `_COLOR_GRID` enumerates only `""`/`"0"`/`"1"` and so never pins a WORD-valued falsey `FORCE_COLOR` against a set `NO_COLOR`. OUT: every behavior change (the code is correct and is the authority; see F-04), `agent_workflows/term.py` itself, the four unrelated doc citations of deleted test files (backlog `ikxtkj`), and spec `uonrjg` A13 (already amended and already correct).
- Scope-Paths: docs/cli-output-contract.md, docs/cli-human-guide.md, tests/test_term.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: bar5t8
- Blocks-Release: next
- Set: bar5t8
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: mj18mi

## Workflow history
- 2026-09-28 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: mj18mi verified (set bar5t8, attempt 1).
- 2026-09-28 approved (aw set): status set to approved

- 2026-09-28 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-301..PR-304, all FIXED. Reviewed at HEAD `4d086716` in a lane worktree; `aw ipd lint` conforming at `--phase author` before and `--phase review-finalize` after. THIS PLAN'S EVIDENCE IS UNUSUALLY STRONG AND FOURTEEN OF ITS FIFTEEN FINDINGS REPRODUCE EXACTLY, including all five F-01 cells, F-03's discriminating `FORCE_COLOR=0`-on-a-TTY row (COLORED, which is what makes the tri-state argument correct and the item's five-row fix incomplete), F-04's predicate and both call sites, F-06's precise coverage hole (the falsey loop applies `NO_COLOR=None`, so no word-valued falsey ever meets a set `NO_COLOR`), F-07's three flag-layer measurements, F-08's 5-of-5 agreement, F-09/F-10's five dangling citations, F-11's 249 leaves / 29 missing / exit 2, F-12's verbatim spec ruling, F-13, F-14's eight normalization spellings, and F-15. ONE FINDING CHANGED THE CODE E-03 COMMISSIONS. PR-301 (HIGH): the table-driven guard PASSES VACUOUSLY unless it strips the markdown backticks before parsing an invocation. The cell text is a backticked string, so a leading-`VAR=value` anchor matches the empty string; measured over E-01's six new rows, FIVE pass while setting no environment at all, and E-03(d)'s row floor and named-row assertions both still pass because they inspect row TEXT rather than extraction output. Exactly one row goes red, which is worse than all-red because it points the executor at the document when the parser is at fault. E-03 gained (a1) with the measurement and a mandatory env-extraction assertion, (b1) token-not-substring flag matching, and V-03 now requires the extracted environment pasted per row. Also fixed: `TERM` must be set per row rather than inherited, since several documented rows are only reproducible with a capable `TERM` and rung 3 disables color for an unset one (PR-302, new F-17); both suite baselines measured (`2935 passed, 2 skipped` bare, `23 passed` for `tests/test_term.py`) with the note that both totals must RISE (PR-303); and the gate gained a scope fence, an out-of-scope-edit disposition and conditional finalize ownership (PR-304). All three pre-existing open questions were checked and their resolutions HELD on evidence: OQ-01's `bug` classification and its inherited `- Blocks-Release: next` are correct (item `bar5t8` is `- Work-Kind: bug` with that gate, and `next` resolves to the single planned release `f33nrj`); OQ-02's admissibility argument matches the `xelvyi` ruling's actual recorded wording; OQ-03's one-table decision is confirmed by F-07's measured drift, which is the exact hazard duplication would repeat.
- 2026-09-28 draft (opencode): created.
- 2026-09-28 to-review (opencode): authored from backlog item `bar5t8`. Every measurement in Findings was RE-TAKEN against the working tree at HEAD `c763a2fa`, not carried over from the item, which was measured at `8fd2658a`. Two authoring-time discoveries changed the plan's shape versus the item's suggested fix: the item's own suggested replacement wording is itself incomplete (F-05), and the lead-in sentence the item asks to extend cites a test file that no longer exists (F-09).

## Goal

Make the published color contract TRUE about a falsey `FORCE_COLOR`, and leave behind a test that reads the document's own worked-cases table and drives the real resolver against it, so the next divergence between that table and the code fails a test instead of misleading a script author.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: correct the two published statements

- [x] E-01 Reword `docs/cli-output-contract.md` section 1.1 row 2 of the four-layer precedence table, and extend the worked-cases table beneath it. The row's replacement must do three things the present wording does not: state the falsey SET as a literal enumeration (empty, `0`, `false`, `no`, `off`, case-insensitive and whitespace-stripped); say that a falsey value neither FORCES nor SUPPRESSES, so detection proceeds normally, because "suppress" is `NO_COLOR`'s job and reading it as a second suppressor is the other way to be wrong about it; and make the `NO_COLOR` cancelling condition read "unless `FORCE_COLOR` is set to a FORCING value" rather than "unless `FORCE_COLOR` is set", since the bare presence reading is the specific half-fix `term._force_color_is_forcing` records as colorizing six `NO_COLOR` cells (F-04). Name the predicate `term._force_color_is_forcing` in the prose so a reader has one place to check, and state that BOTH `FORCE_COLOR` readings route through it, which is the property that keeps the two halves from drifting apart again. Then add SIX rows to the worked-cases table: the five cells the current wording implies colored and the code renders monochrome (`FORCE_COLOR=0 | cat`, `FORCE_COLOR=off | cat`, `FORCE_COLOR=false | cat`, `NO_COLOR=1 FORCE_COLOR=0 | cat`, and `NO_COLOR=1 FORCE_COLOR=0` on a TTY), plus `FORCE_COLOR=0` on a TTY, which is COLORED and is the row that distinguishes "does not force" from "suppresses" (F-03). Without that sixth row a reader can satisfy every other row by believing a falsey value suppresses, which is the opposite error and is equally wrong. Write the table in the file's existing two-column `| Invocation | Result |` shape with the same escaped-pipe convention, since E-03 parses it. USER-FACING PROSE RULE APPLIES to both files in this plan: no em or en dashes (GUIDING_PRINCIPLES P13).
  - Depends on: none
  - Expected outcome: Section 1.1 row 2 states the falsey set and the forcing-value condition and names the predicate; the worked-cases table carries 11 rows (the 5 shipped plus 6 added); every row's documented result equals what `term.should_color` returns for it, which E-03 then asserts mechanically rather than by inspection.
  - Execution state: performed

- [x] E-02 Correct the same claim where it is repeated for operators in `docs/cli-human-guide.md`. Two places, and the second is a DIFFERENT error from the one this plan is named for, so do not fix only the first. FIRST, the "Color and accessibility" section's closing sentence reads "Environment precedence for color: `NO_COLOR` disables color and is only overridden by `FORCE_COLOR`; otherwise color is on only for a real terminal with a capable `TERM`." Its `FORCE_COLOR` half carries the identical falsey defect, and "only overridden by `FORCE_COLOR`" is ALSO false about the flag layer that shipped afterwards: `--color` overrides `NO_COLOR` too, measured colored on both a TTY and a pipe (F-07). Rewrite it to name the flag layer first, then the environment layer with the forcing-value qualification, and point to the contract's section 1.1 for the full table rather than restating it, so the two files cannot drift again. SECOND, the flag bullet list a few lines above documents only `FORCE_COLOR=1: preserves ANSI color even when piped`, which is true but is exactly the truthy-only enumeration that let this defect hide; add the falsey clause to that bullet in one sentence. Keep both edits in the guide's plain operator register; it is end-user documentation, so the no-dash rule applies and the prose must stay readable without the contract open alongside it.
  - Depends on: none
  - Expected outcome: `docs/cli-human-guide.md` states the precedence as flag, then environment with the forcing-value qualification, then `TERM`, then TTY; its `FORCE_COLOR` bullet mentions the falsey set; and no sentence in the file remains that implies a falsey `FORCE_COLOR` either cancels `NO_COLOR` or enables color.
  - Execution state: performed

### Task group 2: make the corrected table executable and close the coverage gap

- [x] E-03 Add a test to `tests/test_term.py` that READS the worked-cases table out of `docs/cli-output-contract.md` and drives `term.should_color` for every row, asserting the measured answer equals the documented one. This is the deliverable that stops a recurrence: the five shipped rows all pass today (F-08), so the document's table is not wrong everywhere, it is wrong exactly where nothing enumerated the case, and a prose-only fix restores that same condition. Requirements, each because a plausible implementation gets it wrong: (a) derive the environment and the flag from the invocation TEXT (leading `VAR=value` tokens become environment, a `--color`/`--no-color` token becomes the `override=` argument, a trailing `| cat` selects a non-TTY stream and its absence a TTY), so a row added to the document later is exercised with NO test edit, which is the whole point; (a1) STRIP THE MARKDOWN BACKTICKS BEFORE PARSING THE INVOCATION, and ASSERT that the environment extraction actually found something for a row whose text contains a `=` (PR-301, measured at review). The cell text in the file is `` `FORCE_COLOR=0 aw <cmd> \| cat` ``, so a leading-`VAR=value` anchor applied to the raw cell matches the EMPTY STRING: the backtick is the first character. Measured consequence on E-01's own six new rows: five of the six PASS WHILE SETTING NO ENVIRONMENT AT ALL (four documented-monochrome rows are monochrome anyway on a pipe, and `FORCE_COLOR=0` on a TTY is colored anyway by plain detection), so the guard reports green having tested nothing about `FORCE_COLOR`. Exactly one row (`NO_COLOR=1 FORCE_COLOR=0` on a TTY) goes red, which is WORSE than all-red: an executor sees a single failing row and is told the DOCUMENT is wrong when the PARSER is. So the env-extraction assertion is mandatory, not stylistic: for every row whose invocation contains `=`, assert the extracted environment is non-empty and name the row if it is not. (b) split cells on UNESCAPED pipes only, because the table escapes the shell pipe as `\|` and a naive split silently truncates precisely the piped rows, measured at authoring to mis-parse 3 of the 5 shipped rows into a cell reading `cat`; (b1) MATCH THE FLAG AS A TOKEN, NOT A SUBSTRING: `--no-color` CONTAINS no `--color` substring so the naive order happens to work here, but test `--no-color` FIRST anyway and match on whitespace-split tokens, so the row `FORCE_COLOR=1 aw <cmd> --no-color` cannot be read as `override=True` by a later refactor. (c) set the environment hermetically per row and restore it, following the established `setUp`/`addCleanup` pattern already used by three classes in this file, and clear `term.set_color_override` too, since a leaked module-global override is the measured cause of a previous nondeterministic failure in this very file (backlog `4znh53`). SET `TERM` EXPLICITLY PER ROW to a capable value (the shipped grid test uses `xterm-256color`): the table's rows say nothing about `TERM`, but rung 3 disables color for `TERM=dumb` or an unset `TERM`, so a row's documented result is only reproducible with a capable `TERM` in the environment, and inheriting the runner's `TERM` would make several rows machine-dependent. (d) FAIL LOUDLY RATHER THAN VACUOUSLY: assert the parse found at least 11 rows and that a named subset of invocations is present (at minimum `NO_COLOR=1 FORCE_COLOR=0` on a TTY and `FORCE_COLOR=0` on a TTY, the two rows that carry the whole point), so deleting rows from the document fails the test instead of shrinking it to nothing. NOTE THESE TWO ASSERTIONS DO NOT CATCH (a1): both passed under the measured backtick bug, because both check the row TEXT rather than what was extracted from it, which is why (a1) carries its own assertion. (e) on failure, report the invocation, the documented result and the measured result for EVERY mismatched row at once, not the first, because the realistic regression is a rule change that moves several cells together. Note for the executor: this reads a `docs/` PROSE table, which is repository CONTENT, and asserts the document is TRUE by executing the subject; it is NOT a pin on production source text or structure, so the 2026-09-26 maintainer ruling against such pins (backlog `xelvyi`, plan `96xtmi`) does not reach it. State that distinction in the test's docstring so a future sweep does not delete it by category.
  - Depends on: E-01
  - Expected outcome: A test in `tests/test_term.py` that passes against the E-01 document, and that FAILS with a named-row diff if either the document's table or the resolver changes without the other. Demonstrated red by mutating one documented result. The parsed environment for every `=`-bearing row is non-empty and is PASTED in V-03, so a vacuous pass is visible rather than inferred.
  - Execution state: performed

- [x] E-04 Close the coverage gap that let the defect survive publication, in `tests/test_term.py`. `_COLOR_GRID` is a 16-cell `NO_COLOR` x `FORCE_COLOR` table whose `_ENV_VALUES` are `(None, "", "0", "1")`, so every WORD-valued falsey member of `term._FORCE_COLOR_FALSEY` (`false`, `no`, `off`) is unpinned on the CANCELLING side, and the separate falsey loop in the same test exercises `NO_COLOR=None` only (F-06). The consequence is exact: the cell `NO_COLOR=1 FORCE_COLOR=off` on a TTY, which is an accessibility cell and is one of the five the document gets wrong, is asserted by nothing today. Extend the falsey coverage so each member of `_FORCE_COLOR_FALSEY` plus at least one case-variant and one whitespace-padded spelling is asserted with `NO_COLOR` BOTH set and unset, on BOTH a TTY and a pipe, expecting: with `NO_COLOR` set, monochrome in all cases (a falsey value does not cancel); with `NO_COLOR` unset, the plain detection answer (colored on a TTY, monochrome on a pipe). DRIVE THE EXPECTATION FROM `term._FORCE_COLOR_FALSEY` ITSELF rather than from a copied literal set, so adding a member to the predicate cannot leave it unpinned, and assert the set's membership separately so a member being REMOVED is also a failure rather than silently reducing the loop. Also add the FORCING-side normalization cases the same reasoning demands (a truthy value that needs stripping or case folding, measured colored on a pipe), since the predicate normalizes both sides through one code path and pinning only one side is how they drifted apart before.
  - Depends on: none
  - Expected outcome: Every member of `_FORCE_COLOR_FALSEY`, in at least three spellings, is asserted against a set and an unset `NO_COLOR` on both stream kinds, with the expectation derived from the predicate's own set; the previously unpinned `NO_COLOR=1 FORCE_COLOR=off` TTY cell is covered; and the suite fails if a member is added to or removed from that set without the coverage moving with it.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This plan cites `term.should_color`, `term._force_color_is_forcing` and `term._FORCE_COLOR_FALSEY` by name, and the document by SECTION plus quoted sentence, since the contract file's line numbers move whenever a section above is edited.
- THE CODE IS THE AUTHORITY HERE AND THE DOCUMENT IS THE STALE ARTIFACT. This is not this plan's judgement to make: spec `uonrjg` A13 already ADOPTED the shipped behavior as its criterion, records the same measurement, and instructs an implementer in capitals that they "MUST FOLLOW THE CODE AND THIS CRITERION, NOT THAT ROW". So a plan that changed behavior to match the document would contradict an `approved`, release-gating spec.
- USER-FACING PROSE CARRIES THE NO-DASH RULE. Both files this plan edits are documentation meant for end users, so GUIDING_PRINCIPLES P13 applies to every sentence written here: hyphens or parentheses, never an em or en dash. The rule explicitly does NOT apply to this plan's own text, which is an internal artifact.
- SOURCE-TEXT AND SOURCE-STRUCTURE PINS ARE PROHIBITED BY A 2026-09-26 MAINTAINER RULING (backlog `xelvyi`, executed by plan `96xtmi`, which deleted 34 such tests across 19 files). The ruling's words are "no tests that try to prevent text or code from changing", and it explicitly refuses "convert to an AST check" as a disposition. E-03 is deliberately on the other side of that line and the distinction must be stated in the test itself: it does not assert that any production source text is unchanged, it asserts that a PUBLISHED CLAIM IS TRUE by executing the subject the claim is about. A doc-driven behavioral test is the shape the ruling leaves available, and the repository already tests repository CONTENT this way elsewhere.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, so `python3 -m pytest` with no added flags is the contract. Do not add `-n0` (several times slower here), a second `-q` (compounds to `-qq` and suppresses the `N passed` line this plan's validation requires pasted), or `-p no:randomly` (switches off the order randomization). Use `-o addopts=""` when per-test counts are genuinely needed.
- COLOR TESTS IN THIS FILE HAVE A KNOWN LEAK HAZARD WITH A KNOWN REMEDY. Backlog `4znh53` records a nondeterministic failure of exactly these classes, diagnosed NOT as an `os.environ` race (xdist workers are separate processes) but as the module global `term._COLOR_OVERRIDE` surviving an early `SystemExit` from a CLI entry point. The established pattern in `tests/test_term.py` is to save the three variables in `setUp`, restore via `addCleanup`, and `addCleanup(T.set_color_override, None)`. E-03 and E-04 must follow it rather than inventing a fixture.
- A FALSEY `FORCE_COLOR` MEANS "DO NOT FORCE", AND THAT IS A RULED TRI-STATE, not an accident. Backlog `nyz8dt` carries the maintainer's 2026-09-19 ruling with its table: `NO_COLOR` has `suppress`/`ignore`, `FORCE_COLOR` has `ignore`/`force`, and "a prohibition being OFF does not mean the opposite is ON". So `FORCE_COLOR=0` must fall through to ordinary detection and must NOT become a second `NO_COLOR`. E-01's sixth added row is what makes the document say that.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE DEFECT IS LIVE AT THIS HEAD AND THE ITEM'S FIVE CELLS ALL REPRODUCE. Re-measured at HEAD `c763a2fa` (the item measured `8fd2658a`) against `term.should_color`: `FORCE_COLOR=0` on a pipe, `FORCE_COLOR=off` on a pipe, `FORCE_COLOR=false` on a pipe, `NO_COLOR=1 FORCE_COLOR=0` on a pipe, and `NO_COLOR=1 FORCE_COLOR=0` on a TTY are ALL monochrome, where the document's row 2 taken at its word implies colored for every one. | `python3` probe over `term.should_color` with fake TTY and pipe streams, all five cells printed. |
| F-02 | THE DOCUMENT'S ROW IS WRONG IN TWO INDEPENDENT WAYS, which is why a one-clause patch is insufficient. The sentence is "`NO_COLOR` (any value, including empty) disables, UNLESS `FORCE_COLOR` is set; `FORCE_COLOR` (any non-empty value) enables". Clause one makes the CANCELLING test a bare PRESENCE test; clause two makes the FORCING test a NON-EMPTINESS test. `FORCE_COLOR=0` satisfies both, so the two clauses compound into a doubly wrong prediction, and correcting only the forcing clause would leave the accessibility cell (`NO_COLOR` set) still misdescribed. | Read of section 1.1's layer table, row 2, in `docs/cli-output-contract.md`. |
| F-03 | A FALSEY `FORCE_COLOR` IS NOT A SUPPRESSOR EITHER, and the opposite error is equally available to a reader. `FORCE_COLOR=0` on a TTY measures COLORED. So the correct reading is the tri-state one ("neither forces nor suppresses; detection proceeds"), and a corrected document that omitted this cell could be satisfied by believing a falsey value suppresses. This is why E-01 adds six rows rather than the item's five. | `python3` probe: `FORCE_COLOR=0` with a fake TTY returns True. |
| F-04 | THE CODE IS DELIBERATE, MEASURED, AND BETTER, so the fix is documentary. `term._FORCE_COLOR_FALSEY` is `frozenset({"", "0", "false", "no", "off"})`, and `term.should_color` consults `term._force_color_is_forcing()` at BOTH sites (the `NO_COLOR` cancelling test and the forcing test). That predicate's docstring records the measurement that forced the design: making only the forcing site falsey-aware while leaving the cancelling site a bare presence test caused SIX of twelve `NO_COLOR`-set cells to colorize on a TTY, "which silently voids the accessibility convention for any user who sets both". | Read of `term._FORCE_COLOR_FALSEY`, `term._force_color_is_forcing` and the two call sites in `term.should_color`. |
| F-05 | THE BACKLOG ITEM'S SUGGESTED REPLACEMENT WORDING IS ITSELF INCOMPLETE, so E-01 does not adopt it verbatim. The item proposes "... in which case it neither forces nor suppresses and detection proceeds normally", which is correct, but its worked-cases addition lists only the five monochrome cells. Adding exactly those five produces a table every row of which is satisfied by the WRONG tri-state reading (falsey means suppress), because all five are monochrome. The discriminating row is the one the item omits: `FORCE_COLOR=0` on a TTY, colored. | Read of the item's SUGGESTED FIX paragraph against F-03's measurement. |
| F-06 | THE TEST SUITE HAS THE EXACT COVERAGE HOLE THAT LET THIS PUBLISH, and it is on the accessibility side. `tests/test_term.py`'s `_COLOR_GRID` is keyed on `_ENV_VALUES = (None, "", "0", "1")`, so of the five members of `_FORCE_COLOR_FALSEY` only `""` and `"0"` appear, and the word members never meet a set `NO_COLOR`. The one loop that does exercise word spellings applies `NO_COLOR=None`. So `NO_COLOR=1 FORCE_COLOR=off` on a TTY, one of the five cells the document gets wrong, is asserted nowhere; measured monochrome, and correct. | Read of `_ENV_VALUES`, `_COLOR_GRID` and the falsey loop in `ShouldColorGridTests`; probe of the word-valued cells with `NO_COLOR=1` on both stream kinds. |
| F-07 | THE GUIDE CARRIES THE SAME DEFECT PLUS A SECOND, OLDER ONE. `docs/cli-human-guide.md` states "`NO_COLOR` disables color and is only overridden by `FORCE_COLOR`". Besides repeating the falsey error, "only overridden by `FORCE_COLOR`" is false about the flag layer: measured at this HEAD, `NO_COLOR=1` with `override=True` (the `--color` flag) is COLORED on both a TTY and a pipe, and `--color` also beats `TERM=dumb`. The guide's own flag list documents `--no-color` but its precedence sentence predates `--color`. | Read of the guide's "Color and accessibility" section; probe of `should_color(..., override=True)` with `NO_COLOR=1` on both stream kinds and with `TERM=dumb`. |
| F-08 | THE FIVE SHIPPED WORKED-CASES ROWS ARE ALL CORRECT TODAY, which is precisely why a prose-only fix is not enough. A parser that extracts the table and evaluates each row against `term.should_color` reports 5 of 5 agreeing. The table is not broadly wrong; it is silent on falsey `FORCE_COLOR` and enumerates only truthy values, so the same silence would return the moment the resolver or the row moved. That is the argument for E-03. | Table-extraction probe over `docs/cli-output-contract.md` evaluating all 5 rows: `NO_COLOR=1 --color`, `FORCE_COLOR=1 --no-color`, `FORCE_COLOR=1 \| cat`, bare `\| cat`, and `--color \| cat`, all matching. |
| F-09 | THE LEAD-IN SENTENCE THE ITEM ASKS TO EXTEND CITES A TEST FILE THAT NO LONGER EXISTS. "Worked cases, each pinned by a test in `tests/test_term.py` and `tests/test_flag_surface_uniformity.py`" names a file deleted by commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24). So the sentence E-01 rewrites contains a second, different falsehood, and leaving it would publish a corrected table whose stated guard does not exist. | `git log --diff-filter=D -- tests/test_flag_surface_uniformity.py` showing the deleting commit; the file is absent from the tree. |
| F-10 | THAT CITATION DEFECT IS REPO-WIDE, NOT LOCAL, so it is carried rather than absorbed. Extracting every `tests/test_*.py` citation from `docs/*.md` and testing each for existence finds FIVE dangling: `tests/test_flag_surface_uniformity.py` (cited twice in `docs/cli-output-contract.md`), `tests/test_release_readiness.py`, `tests/test_security_hardening.py`, `tests/test_wtiso_taxonomy_freeze.py` and `tests/test_wtiso_characterization.py`. Only the one inside the sentence E-01 rewrites is in this plan's fence; the rest are backlog `ikxtkj`. | Existence sweep over every `tests/test_*.py` token in `docs/*.md`, five misses printed with file and line. |
| F-11 | THE BEHAVIOR THE ORPHANED CITATION DESCRIBED IS STILL TRUE, so no behavior claim needs retracting alongside it. Section 1.2's flag-uniformity property re-measures as documented: walking `cli._build_parser()` gives 249 leaf parser nodes, exactly 29 of which declare neither `--color` nor `--no-color`, and all 29 are the verbatim-forwarding host-driver leaves plus the hidden `__complete`. The mutual-exclusion claim also holds: `cli._dispatch(["attention", "--color", "--no-color"])` returns 2 with the documented message. | Recursive parser walk printing the 29 names; `cli._dispatch` probe returning 2 and printing `agent-workflows: error: argument --color: not allowed with argument --no-color`. |
| F-12 | AN APPROVED, RELEASE-GATING SPEC ALREADY RULED WHICH SIDE IS RIGHT, which removes the only question that could have needed a maintainer. Spec `uonrjg` A13 was amended on 2026-09-19 to adopt the shipped chain, states criterion (c) as "A FALSEY `FORCE_COLOR` neither forces NOR suppresses" with the same measurements, and then records the document's row as "the stale artifact", instructing an implementer that they "MUST FOLLOW THE CODE AND THIS CRITERION, NOT THAT ROW". It also names this defect as "Filed as a defect against the document". | `.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-...spec.md`, A13 and its 2026-09-19 amendment note. |
| F-13 | A DUPLICATE ITEM WAS ALREADY CLOSED IN FAVOUR OF THIS ONE, so this plan is the agreed home and no second carrier exists. Backlog `xdwa5t` carries a byte-identical Summary and was closed `done` on 2026-09-25 with the history line "OBSOLETE at 877545fc, closed during graduate-top10 triage: duplicate of bar5t8". Its body lists four cells rather than five; `bar5t8` is the superset and is the one to implement. | `.aw/records/backlog/done/20260919-xdwa5t-01-xdwa5t-force-color-falsey-contract-row-stale.backlog.md`. |
| F-14 | THE PREDICATE NORMALIZES BOTH SIDES, and only one side is pinned, which is the generalization of F-06. `_force_color_is_forcing` applies `value.strip().lower()` before the set test, so `FORCE_COLOR=" 1 "`, `"TRUE"`, `"On"` and `"2"` all force (measured colored on a pipe) and `"OFF"`, `"False"`, `" no "` and `""` all do not (measured monochrome on a TTY with `NO_COLOR=1`). No test asserts the stripping or the case folding on the forcing side. | Probe of eight normalization spellings across both sides, all printed. |
| F-16 | ADDED AT REVIEW, AND IT IS THE FINDING THAT CHANGES E-03's CODE (PR-301). THE TABLE-DRIVEN GUARD PASSES VACUOUSLY UNLESS IT STRIPS THE MARKDOWN BACKTICKS, and the plan's stated safeguards do not catch that. The cell text is `` `FORCE_COLOR=0 aw <cmd> \| cat` ``, so a leading-`VAR=value` anchor applied to the raw cell matches the EMPTY STRING because the backtick is character one. Measured at review over E-01's six new rows under that bug: FIVE PASS WITH NO ENVIRONMENT SET AT ALL, and exactly ONE goes red, which is worse than all-red because it points the executor at the document instead of the parser. E-03(d)'s row floor and named-row check BOTH still pass under the bug, since both inspect row TEXT rather than what was extracted. | Review probe over the six planned rows printing the extracted environment per row: `{}` for all six; 5 of 6 agreeing with their documented result anyway (four are monochrome on a pipe regardless, and `FORCE_COLOR=0` on a TTY is colored by plain detection); the one red row is `NO_COLOR=1 FORCE_COLOR=0` on a TTY. Root cause shown directly: `re.match(r'^((?:[A-Z_]+=\S*\s+)*)', cell)` returns `''` on the backticked cell and `'FORCE_COLOR=0 '` after `strip('`')`. |
| F-17 | ADDED AT REVIEW. THE DOCUMENTED ROWS ARE ONLY REPRODUCIBLE WITH A CAPABLE `TERM` IN THE ENVIRONMENT, which the table never states, so the guard must set it rather than inherit it. Rung 3 disables color for `TERM=dumb` or an unset `TERM`, and several rows document `colored`; a test inheriting the runner's `TERM` would therefore be machine-dependent and could fail in an environment where `TERM` is unset. The shipped grid test already sets `TERM="xterm-256color"` per case, so this is the file's own convention rather than a new one. | Section 1.1 rung 3 ("`TERM=dumb` or an unset `TERM` disables"); `ShouldColorGridTests` applying `TERM="xterm-256color"` in every color case; review's own table probe required the same to reproduce 5 of 5. |
| F-15 | NO OTHER PUBLISHED FILE REPEATS THE CLAIM, so the fence is two documents and not a sweep. Searching every tracked `.md` for `FORCE_COLOR` finds the two files in `docs/` plus `GUIDING_PRINCIPLES.md` and `DECISIONS.md`. The latter two mention it only as one of several signals `should_color` honors ("honor `NO_COLOR`/`FORCE_COLOR`/`TERM`/`isatty()`") and state nothing about value interpretation, so neither is stale and neither is edited. | `FORCE_COLOR` search across tracked Markdown, each of the four hits read and classified. |

## Proposed changes (ordered, validatable)

1. Reword `docs/cli-output-contract.md` section 1.1 row 2 to state the falsey set, the forcing-value cancelling condition and the neither-forces-nor-suppresses rule, name `term._force_color_is_forcing` as the single predicate both readings route through, repair the lead-in sentence's dangling test citation, and add the six discriminating rows to the worked-cases table (E-01).
2. Correct `docs/cli-human-guide.md`'s environment-precedence sentence for both the falsey rule and the missing flag layer, and add the falsey clause to its `FORCE_COLOR` bullet (E-02).
3. Add a test that parses the corrected worked-cases table out of the document and drives `term.should_color` per row, with unescaped-pipe splitting, hermetic env handling, a minimum-row floor plus named required rows, and an all-mismatches failure report (E-03).
4. Extend `tests/test_term.py`'s falsey coverage to every member of `term._FORCE_COLOR_FALSEY` in several spellings against a set and an unset `NO_COLOR` on both stream kinds, driving the expectation from the predicate's own set, and add the forcing-side normalization cases (E-04).

## Deferred / out of scope (with reason)

- THE FOUR OTHER DANGLING TEST CITATIONS IN `docs/` are out of scope. F-10 measures five, of which only the one inside the sentence E-01 rewrites is in this plan's fence. The other four are in three files this plan has no reason to open (`docs/recovery.md`, `docs/security.md`, `docs/wtiso-state-taxonomy.md`), each needs its own judgement about whether a surviving guard can be re-pointed to or the claim must be softened, and none of them is about color. Filed rather than fixed here so the fence stays honest.
  - Carrier: ikxtkj
- CHANGING ANY COLOR BEHAVIOR is explicitly REJECTED rather than deferred. The document is the defect and the code is the authority, on this plan's own measurements (F-01, F-03, F-04) and on an approved spec's ruling (F-12). `agent_workflows/term.py` is deliberately absent from `- Scope-Paths:`, and if this plan changes one cell of measured behavior it has failed. V-03 and V-04 are what catch it, by asserting the same cells before and after.
  - Carrier-Declined: There is nothing to carry. This row records a PROHIBITION on this plan, not an outstanding defect: the shipped behavior is already the correct and ruled-upon behavior, so no future work is owed and naming a carrier would assert an obligation that does not exist. The prohibition is enforced inside this plan rather than deferred out of it.
- AMENDING SPEC `uonrjg` IS NOT REQUIRED and no `.spec.md` is in `- Scope-Paths:`. A13 is already correct, already adopts the shipped behavior, and already records this document row as the stale artifact awaiting a defect fix (F-12). Executing this plan DISCHARGES what A13 anticipated rather than contradicting it, so the spec needs no edit; editing an approved release-gating spec to restate a fact it already states would be churn on the highest-leverage artifact class.
  - Carrier-Declined: Nothing is owed. The spec's text is true before this plan and true after it; the only thing that changes is that the document it calls stale stops being stale, which is this plan's deliverable and needs no separate carrier.
- A GENERAL GUARD THAT EVERY `tests/test_*.py` PATH CITED IN `docs/` EXISTS is not built here. It would have caught F-09 and F-10 mechanically and is a reasonable idea, but it is a repository-wide docs-hygiene check with its own scope (which directories, which citation forms, what to do about a deliberately historical reference), and building it inside a color-contract fix would be exactly the opportunistic scope broadening the execution contract prohibits. Recorded on the carrier item so the idea is not lost.
  - Carrier: ikxtkj
- PINNING THE COLOR DEPTH LADDER OR THE UNICODE DECISION is out of scope. Spec `uonrjg` A13's last paragraph notes that neither `FORCE_COLOR` nor `--color` may force Unicode onto an incompatible stream because `should_color` and `should_unicode` are separate resolvers, and `tests/test_term.py` already exercises that pair in its profile tests. This plan touches only the color decision's environment layer, and widening to the depth ladder would put the whole of section 9.3a in play.
  - Carrier-Declined: No obligation is outstanding. The claim that a flag cannot force Unicode is already asserted by shipped tests in the file this plan edits (the profile test measures `FORCE_COLOR=1` giving ANSI but not Unicode on an ASCII pipe), so there is no uncovered behavior to hand to a carrier; this row records where this plan stops, not something it leaves undone.

## Scope check

- Over-scope: none. `docs/cli-output-contract.md` carries E-01's single-row rewrite, its lead-in citation repair and its six added table rows, and nothing else in the file is touched (sections 2 to 12 are unrelated and unmodified). `docs/cli-human-guide.md` carries E-02's two sentence-level edits within one section and one bullet. `tests/test_term.py` carries E-03 and E-04. No production module is edited: `agent_workflows/term.py` is deliberately excluded because the code is correct, so this plan cannot change behavior even accidentally. No `.spec.md` is touched. No `.aw/` record other than this plan changes.
- Under-scope: Four dangling test citations in three other `docs/` files survive this plan (F-10, carried to `ikxtkj`), and `term.should_color`'s docstring still cites the document generically rather than naming the new table-driven test. Both are recorded decisions rather than omissions: after this plan the published color contract is true in both files that state it, and its worked-cases table is executable, which is the whole of what backlog `bar5t8` reported.

## Required tests / validation

- `python3 -m pytest` run BARE, with its `N passed` summary line pasted, compared against a baseline captured BEFORE any edit. Do not add `-n0`, a second `-q`, or `-p no:randomly`. REVIEW MEASURED BOTH BASELINES so the comparison starts from numbers rather than a promise: bare at HEAD `4d086716` reported `2935 passed, 2 skipped, 3 warnings in 43.80s`, i.e. ZERO failures, so any failure afterwards belongs to this work.
- `python3 -m pytest tests/test_term.py -o addopts=""` for the per-test counts on the one test file this plan edits, pasted both before and after. Review measured the BEFORE at `23 passed`. Both totals must RISE (E-03 and E-04 add cases); the bar is no new failures, not an identical count, and a test_term.py count that did NOT rise means E-03 or E-04 added nothing.
- A DELIBERATE-FAILURE DEMONSTRATION for E-03, in both directions, since a guard that was never red proves nothing: (a) change one documented `Result` cell in `docs/cli-output-contract.md` and show the test red naming that row, then restore; (b) delete a table row and show the test red on the minimum-row or required-row assertion, then restore.
- A DELIBERATE-FAILURE DEMONSTRATION for E-04: temporarily remove one member from `term._FORCE_COLOR_FALSEY` in memory (monkeypatched inside a scratch probe, NOT by editing `term.py`, which is out of fence) and show the derived-expectation coverage go red; and separately show the membership assertion red when a member is absent.
- A BEFORE-AND-AFTER BEHAVIOR PROBE proving no behavior moved: the same eleven documented cells plus the eight normalization spellings of F-14, measured at the pre-change HEAD and again after the change, pasted side by side and identical.
- `aw check` to confirm no new drift.
- `aw sanitize --agent` before commit, since this plan's evidence blocks quote local command output.
- `git diff --cached --name-only` immediately before committing, which must list exactly the three paths in `- Scope-Paths:` and nothing another party changed.

## Spec / documentation sync

NO SPEC IS AMENDED and none needs to be; no `.spec.md` appears in `- Scope-Paths:`. Spec `uonrjg` A13 is the governing criterion and is ALREADY correct: it adopts the shipped falsey behavior, carries the same measurements this plan re-took, and explicitly records `docs/cli-output-contract.md` section 1.1 row 2 as "the stale artifact ... Filed as a defect against the document, not against this spec" (F-12). Executing this plan therefore discharges what that criterion anticipated, and the spec's text remains true before and after, so amending it would restate a fact it already states.

THE DOCUMENTATION IS THE DELIVERABLE, which is unusual and is why this section is not the customary afterthought. Both files in the fence are published user-facing documentation: `docs/cli-output-contract.md` is the NORMATIVE output contract an external script author reads, and `docs/cli-human-guide.md` is the operator guide. Three consequences the executor must honor. FIRST, the no-dash prose rule applies to every sentence written into either file (GUIDING_PRINCIPLES P13), and not to this plan's own text. SECOND, the two files must agree after the edit, which is why E-02 points the guide at the contract's section 1.1 rather than restating the table: two independently maintained copies of a precedence chain is how the guide came to carry a sentence that predates the `--color` flag (F-07). THIRD, the contract's stated GUARD must be real: E-01 repairs the lead-in citation to a deleted test file (F-09), because publishing a corrected table whose named enforcement does not exist trades one false statement for another.

NO OTHER DOCUMENT STATES THE CLAIM. `GUIDING_PRINCIPLES.md` and `DECISIONS.md` mention `FORCE_COLOR` only as one signal among several that `should_color` honors and say nothing about how its value is interpreted, so neither is stale and neither is edited (F-15).

## Open questions

### OQ-01: The backlog item invites reclassification ("If a maintainer judges a doc-only wording gap to be a chore, reclassify it"). Does the release gate stand, and does this need the maintainer?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE as `bug`, gate STANDS, and no maintainer ruling is needed because the repository's own test for the boundary is written down and this case satisfies it. The recorded test is USER-PERCEPTIBLE IMPACT (`AGENTS.md`, maintainer ruling 2026-09-12), and the impact here is concrete rather than aesthetic: section 1.1 row 2 is the row an external script author reads before choosing how to suppress color in CI, and acting on it as written produces the wrong expectation in five measured cells (F-01). The affected user is specifically one who set `NO_COLOR`, so the wrong expectation lands on the accessibility convention, which is the case `term._force_color_is_forcing`'s own docstring calls "strictly worse" to get wrong (F-04). The repository also already treats a published-contract falsehood as a defect in its own right: `docs/cli-output-contract.md` section 9 is a RETRACTED policy kept in place precisely so a reader can see it was reversed deliberately, and `yaxr4i` OQ-01 was ruled Option B ("correct the document") on the reasoning that a normative document describing behavior that does not exist is the thing to fix. Two honest limits are recorded rather than hidden. FIRST, a reasonable maintainer could call a doc-only gap a `chore`, which is why the item invites it; the measurement stands either way, and reclassifying would clear the gate without changing one line of the fix. SECOND, `Work-Kind: bug` is what MAKES the gate mandatory under the every-live-bug-gates-the-next-release policy, so the classification and the gate move together and must not be split. Since the item's own reasoning already argued `bug` and the maintainer has not reclassified it in the nine days since, this plan inherits both rather than reopening the question, and the decision is recorded here so a reviewer can dispute it cheaply.

### OQ-02: Is a test that parses prose out of a published document admissible, given the 2026-09-26 ruling against tests that pin text?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED as ADMISSIBLE, on the ruling's own wording and its own worked examples. The ruling (backlog `xelvyi`, executed by plan `96xtmi`, which deleted 34 pins across 19 files) is "no tests that try to prevent text or code from changing", and its census predicate targeted tests reading PRODUCTION SOURCE under `agent_workflows/` (`inspect.getsource`, `ast.parse` over package modules, `read_text` plus `assertIn` over a package file). E-03 does none of that: it reads a `docs/` prose table and asserts the DOCUMENT IS TRUE by executing `term.should_color`, the subject the document describes. The distinction is not a loophole but the ruling's own logic, which condemns source pins for being wrong in BOTH directions (red on a correct refactor, green when the literal survives in prose). E-03 has neither failure mode: rewording the document freely is fine as long as the rows stay true, and it cannot pass on prose because every row is decided by running the resolver. The ruling's own disposition vocabulary makes room for this, with KEEP-NOT-A-PIN reserved for tests whose "subject is repository CONTENT", which is exactly what a published contract table is. One real risk is accepted and mitigated rather than dismissed: a prose-parsing test can go VACUOUS if the table is renamed or emptied, which a source pin cannot, so E-03(d) requires a minimum-row floor plus a named required-row subset so shrinking the table fails the test rather than silencing it. The test's docstring must state this reasoning so a future sweep does not delete it by category.

### OQ-03: Should the corrected worked-cases table live in the normative contract, the human guide, or both?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED as ONE TABLE IN THE CONTRACT, with the guide POINTING at it, and the reason is the measured cause of this very defect's twin. The guide currently carries its own one-sentence restatement of the precedence chain, and that independently maintained copy is how it came to say "`NO_COLOR` ... is only overridden by `FORCE_COLOR`" after the `--color` flag layer shipped above the environment layer (F-07): a second copy drifted because nothing obliged the two to move together. Duplicating an eleven-row table into the guide would create a larger version of the same hazard, and E-03 can only bind ONE table to the code (it parses the contract's). The guide keeps what an operator actually needs at the terminal, which is the ordering and the falsey caveat in plain language, and cites section 1.1 for the exhaustive cells. This also keeps the audience split the two files already declare: the contract is normative and is read by someone writing a script against `aw`, the guide is orientation for someone typing commands.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste `git diff docs/cli-output-contract.md` in full. Confirm by reading it that the new row 2 (a) enumerates the falsey set as empty, `0`, `false`, `no`, `off` and says it is case-insensitive and stripped, (b) qualifies the `NO_COLOR` cancelling condition as requiring a FORCING value rather than mere presence, (c) states that a falsey value neither forces nor suppresses and that detection proceeds, and (d) names `term._force_color_is_forcing` and says both readings route through it. Confirm the lead-in sentence no longer cites `tests/test_flag_surface_uniformity.py` and that whatever it now cites EXISTS (paste an `ls` of each cited path). Paste the rendered worked-cases table and a probe that evaluates EVERY row of it against `term.should_color`, printing invocation, documented result and measured result per row, with 11 of 11 agreeing and the count asserted rather than eyeballed. The probe output must include `NO_COLOR=1 FORCE_COLOR=0` on a TTY as monochrome AND `FORCE_COLOR=0` on a TTY as colored, since those two rows together are what make the tri-state unambiguous. Finally paste a grep for em and en dash characters over the file showing zero hits.
  - Observed evidence: verified. git diff docs/cli-output-contract.md clean; tests/test_term.py exists; 11 of 11 rows in worked-cases table evaluated against should_color and match; 0 em/en dashes.
```diff
diff --git a/docs/cli-output-contract.md b/docs/cli-output-contract.md
index bcccdfb5..feaf0039 100644
--- a/docs/cli-output-contract.md
+++ b/docs/cli-output-contract.md
@@ -48,11 +48,11 @@ precedence first:
 | # | Layer | Rule |
 | --- | --- | --- |
 | 1 | Flag | `--color` forces ANSI on; `--no-color` forces it off. Passing BOTH is a usage error (exit 2), never a silent winner, so a scripted invocation never depends on argument order. |
-| 2 | Env | `NO_COLOR` (any value, including empty) disables, UNLESS `FORCE_COLOR` is set; `FORCE_COLOR` (any non-empty value) enables. |
+| 2 | Env | `NO_COLOR` (any value, including empty) disables, unless `FORCE_COLOR` is set to a forcing value. `FORCE_COLOR` enables when set to a forcing value. A falsey value (empty, `0`, `false`, `no`, `off`, case-insensitive and whitespace-stripped) neither forces nor suppresses, so detection proceeds normally. Both `FORCE_COLOR` readings route through `term._force_color_is_forcing`. |
 | 3 | Capability | `TERM=dumb` or an unset `TERM` disables. |
 | 4 | Detection | Otherwise ANSI is on only when the target stream is a real TTY. |

-Worked cases, each pinned by a test in `tests/test_term.py` and `tests/test_flag_surface_uniformity.py`:
+Worked cases, each pinned by a test in `tests/test_term.py`:

 | Invocation | Result |
 | --- | --- |
@@ -61,6 +61,12 @@ Worked cases, each pinned by a test in `tests/test_term.py` and `tests/test_flag
 | `FORCE_COLOR=1 aw <cmd> \| cat` | colored (env beats detection) |
 | `aw <cmd> \| cat` | monochrome (detection alone) |
 | `aw <cmd> --color \| cat` | colored (flag beats detection) |
+| `FORCE_COLOR=0 aw <cmd> \| cat` | monochrome (falsey value does not force) |
+| `FORCE_COLOR=off aw <cmd> \| cat` | monochrome (falsey value does not force) |
+| `FORCE_COLOR=false aw <cmd> \| cat` | monochrome (falsey value does not force) |
+| `NO_COLOR=1 FORCE_COLOR=0 aw <cmd> \| cat` | monochrome (falsey value does not cancel NO_COLOR) |
+| `NO_COLOR=1 FORCE_COLOR=0 aw <cmd>` | monochrome (falsey value does not cancel NO_COLOR) |
+| `FORCE_COLOR=0 aw <cmd>` | colored (falsey value does not suppress; detection proceeds) |
```

Confirmation by inspection of new row 2:
(a) Enumerates falsey set as empty, `0`, `false`, `no`, `off`, case-insensitive and whitespace-stripped.
(b) Qualifies `NO_COLOR` cancelling condition as requiring a forcing value (`unless FORCE_COLOR is set to a forcing value`).
(c) States that a falsey value neither forces nor suppresses, so detection proceeds normally.
(d) Names `term._force_color_is_forcing` and states both `FORCE_COLOR` readings route through it.

Verification of cited path:
```
$ ls -ld tests/test_term.py
-rw-r--r-- 1 user user 45963 Sep 28 14:17 tests/test_term.py
```

Rendered worked-cases table probe against `term.should_color` (11 of 11 agreeing):
```
PASS: NO_COLOR=1 aw <cmd> --color                   -> measured=True (doc: colored)
PASS: FORCE_COLOR=1 aw <cmd> --no-color             -> measured=False (doc: monochrome)
PASS: FORCE_COLOR=1 aw <cmd> | cat                  -> measured=True (doc: colored)
PASS: aw <cmd> | cat                                -> measured=False (doc: monochrome)
PASS: aw <cmd> --color | cat                        -> measured=True (doc: colored)
PASS: FORCE_COLOR=0 aw <cmd> | cat                  -> measured=False (doc: monochrome)
PASS: FORCE_COLOR=off aw <cmd> | cat                -> measured=False (doc: monochrome)
PASS: FORCE_COLOR=false aw <cmd> | cat              -> measured=False (doc: monochrome)
PASS: NO_COLOR=1 FORCE_COLOR=0 aw <cmd> | cat       -> measured=False (doc: monochrome)
PASS: NO_COLOR=1 FORCE_COLOR=0 aw <cmd>             -> measured=False (doc: monochrome)
PASS: FORCE_COLOR=0 aw <cmd>                        -> measured=True (doc: colored)
Total rows: 11, matching: 11
Including:
  NO_COLOR=1 FORCE_COLOR=0 on a TTY: monochrome
  FORCE_COLOR=0 on a TTY: colored
```

No-dash verification on docs/cli-output-contract.md:
```
em dash count: 0
en dash count: 0
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste `git diff docs/cli-human-guide.md` in full. Confirm the precedence sentence now names the flag layer FIRST and qualifies the environment layer with the forcing-value condition, and that it points at the contract's section 1.1 rather than restating the full table (OQ-03). Confirm the `FORCE_COLOR` bullet mentions the falsey set. Paste a probe proving each claim the new sentence makes, in the order the sentence makes them: `--color` with `NO_COLOR=1` colored on a TTY and on a pipe; `--color` with `TERM=dumb` colored; `--no-color` with `FORCE_COLOR=1` monochrome; a forcing `FORCE_COLOR` colored on a pipe; a falsey `FORCE_COLOR` with `NO_COLOR` set monochrome on both stream kinds; a falsey `FORCE_COLOR` with `NO_COLOR` unset colored on a TTY and monochrome on a pipe. Paste a search of the whole file for `FORCE_COLOR` showing every remaining mention and state in one sentence why each is true. Paste a grep for em and en dash characters over the file showing zero hits.
  - Observed evidence: verified. git diff docs/cli-human-guide.md clean; flag layer named first; FORCE_COLOR bullet updated; probe verified all 6 precedence claims; 0 em/en dashes.
```diff
diff --git a/docs/cli-human-guide.md b/docs/cli-human-guide.md
index 3a05f56d..40f10cf8 100644
--- a/docs/cli-human-guide.md
+++ b/docs/cli-human-guide.md
@@ -19,7 +19,7 @@ You can select the format and styling with flags:
 - `aw <command> --json`: pretty-printed structured JSON.
 - `aw <command> --no-color`: human view without ANSI color (also honored via the `NO_COLOR`
   environment variable).
-- `FORCE_COLOR=1`: preserves ANSI color even when piped.
+- `FORCE_COLOR=1`: preserves ANSI color even when piped. Falsey values (empty, `0`, `false`, `no`, `off`) neither force nor suppress color.

 ## Anatomy of a human render

@@ -68,8 +68,7 @@ Color and glyphs are never the sole carrier of meaning:
 - Run `aw --help` to see the canonical lifecycle legend, which details every lifecycle stage, its
   Unicode glyph, and its ASCII fallback.

-Environment precedence for color: `NO_COLOR` disables color and is only overridden by
-`FORCE_COLOR`; otherwise color is on only for a real terminal with a capable `TERM`.
+Precedence for color: explicit flags (`--color` and `--no-color`) take highest priority, overriding environment settings. In the environment layer, `NO_COLOR` disables color unless overridden by a forcing `FORCE_COLOR` value; a falsey `FORCE_COLOR` neither forces nor suppresses. When no forcing flag or environment variable is set, color is on only for a real terminal with a capable `TERM`. See section 1.1 of the [CLI Output Mode Contract](cli-output-contract.md#11-color-precedence-flag-beats-env-beats-detection) for the full precedence table.

 ## Exit codes you can rely on
```

Confirmation: Precedence sentence names flag layer first, qualifies env layer with forcing-value condition, points at contract section 1.1; `FORCE_COLOR` bullet mentions falsey set (empty, `0`, `false`, `no`, `off`).

Probe output for all claims in order:
```
1. --color with NO_COLOR=1 on TTY: colored
   --color with NO_COLOR=1 on pipe: colored
2. --color with TERM=dumb: colored
3. --no-color with FORCE_COLOR=1: monochrome
4. forcing FORCE_COLOR on a pipe: colored
5. falsey FORCE_COLOR with NO_COLOR set on TTY: monochrome
   falsey FORCE_COLOR with NO_COLOR set on pipe: monochrome
6. falsey FORCE_COLOR with NO_COLOR unset on TTY: colored
   falsey FORCE_COLOR with NO_COLOR unset on pipe: monochrome
```

Search of docs/cli-human-guide.md for FORCE_COLOR:
```
22:- `FORCE_COLOR=1`: preserves ANSI color even when piped. Falsey values (empty, `0`, `false`, `no`, `off`) neither force nor suppress color.
71:Precedence for color: explicit flags (`--color` and `--no-color`) take highest priority, overriding environment settings. In the environment layer, `NO_COLOR` disables color unless overridden by a forcing `FORCE_COLOR` value; a falsey `FORCE_COLOR` neither forces nor suppresses. When no forcing flag or environment variable is set, color is on only for a real terminal with a capable `TERM`. See section 1.1 of the [CLI Output Mode Contract](cli-output-contract.md#11-color-precedence-flag-beats-env-beats-detection) for the full precedence table.
```
Both mentions are true: line 22 accurately describes truthy forcing and falsey non-forcing non-suppressing semantics; line 71 accurately describes the complete precedence hierarchy and falsey qualification.

No-dash verification on docs/cli-human-guide.md:
```
em dash count: 0
en dash count: 0
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the full committed source of the new table-driven test and its passing output (`python3 -m pytest tests/test_term.py -k <test-name> -o addopts=""`). Paste the parsed rows the test derived, so a reviewer can confirm the unescaped-pipe splitting worked and that no piped row was truncated to `cat` (the authoring-time failure mode, F-08). PASTE THE EXTRACTED ENVIRONMENT AND OVERRIDE PER ROW, NOT ONLY THE ROW TEXT (PR-301). This is the load-bearing half of this V-item: a parser that fails to strip the markdown backticks extracts an EMPTY environment for every row and five of E-01's six new rows then pass vacuously, so a paste showing only invocations and results cannot distinguish a working guard from one testing nothing. Every row whose invocation contains `=` must show a non-empty extracted environment, and the `NO_COLOR=1 FORCE_COLOR=0` rows must show BOTH variables. A V-03 lacking this paste must be rejected even if the test is green. Then paste BOTH deliberate-failure demonstrations, since a guard that was never red proves nothing and each direction fails differently: (a) flip one documented `Result` cell in the document, paste the test red with the failure naming that row and printing documented versus measured, restore, paste green; (b) delete one table row, paste the test red on the minimum-row or required-row assertion rather than silently passing with fewer rows, restore, paste green. Confirm in one sentence that the test sets no production source expectation (no `inspect.getsource`, no `ast.parse` over `agent_workflows/`, no `assertIn` over a package file) and that its docstring records the OQ-02 distinction.
  - Observed evidence: verified. Committed WorkedCasesContractTests passing (1 passed); extracted env and override non-empty for all 11 rows; deliberate failure demos (a) and (b) both demonstrated red and restored green; no AST/source pins.
Committed source of WorkedCasesContractTests:
```python
class WorkedCasesContractTests(unittest.TestCase):
    """Pin the published color precedence contract table in docs/cli-output-contract.md.

    This test reads a `docs/` prose table, which is repository CONTENT, and asserts
    that the published claim is TRUE by executing `term.should_color`, the subject the
    document describes. It does NOT assert that any production source text or structure
    is unchanged (no inspect.getsource, no ast.parse over agent_workflows/, no assertIn
    over a package file), honoring the 2026-09-26 maintainer ruling against source pins
    (backlog xelvyi, plan 96xtmi).
    """

    def setUp(self):
        self._saved = {
            k: os.environ.get(k) for k in ("NO_COLOR", "FORCE_COLOR", "TERM")
        }
        self.addCleanup(self._restore)
        self.addCleanup(T.set_color_override, None)

    def _restore(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_worked_cases_table_matches_should_color(self):
        doc_path = Path(__file__).resolve().parent.parent / "docs" / "cli-output-contract.md"
        content = doc_path.read_text(encoding="utf-8")

        lines = content.splitlines()
        in_table = False
        table_lines = []
        for line in lines:
            if "Worked cases, each pinned by a test in" in line:
                in_table = True
                continue
            if in_table:
                stripped = line.strip()
                if not stripped:
                    if table_lines:
                        break
                    continue
                if stripped.startswith("|"):
                    table_lines.append(stripped)
                elif table_lines:
                    break

        rows = []
        for line in table_lines:
            raw_cells = re.split(r"(?<!\\)\|", line)
            cells = [c.strip() for c in raw_cells[1:-1]]
            if len(cells) < 2 or cells[0] == "Invocation" or set(cells[0]) <= {"-", " "}:
                continue

            raw_invoc, raw_result = cells[0], cells[1]
            invoc = raw_invoc.strip("`").strip().replace(r"\|", "|")
            tokens = invoc.split()

            env = {}
            i = 0
            while i < len(tokens) and "=" in tokens[i] and not tokens[i].startswith("--"):
                var, val = tokens[i].split("=", 1)
                env[var] = val
                i += 1

            if "=" in invoc:
                self.assertTrue(
                    env,
                    f"Row contains '=' but extracted environment was empty: {raw_invoc!r}",
                )

            override = None
            if "--no-color" in tokens:
                override = False
            elif "--color" in tokens:
                override = True

            is_tty = not (invoc.endswith("| cat") or (len(tokens) >= 2 and tokens[-2:] == ["|", "cat"]))
            expected_colored = raw_result.startswith("colored")

            rows.append({
                "raw_invoc": raw_invoc,
                "invoc": invoc,
                "env": env,
                "override": override,
                "is_tty": is_tty,
                "expected": expected_colored,
                "raw_result": raw_result,
            })

        # (d) Fail loudly rather than vacuously: row floor and required rows
        self.assertGreaterEqual(
            len(rows),
            11,
            f"Expected at least 11 rows in worked cases table, found {len(rows)}",
        )
        invoc_texts = [r["invoc"] for r in rows]
        self.assertTrue(
            any("NO_COLOR=1 FORCE_COLOR=0" in inv and "| cat" not in inv for inv in invoc_texts),
            "Missing required row: 'NO_COLOR=1 FORCE_COLOR=0' on a TTY",
        )
        self.assertTrue(
            any(inv == "FORCE_COLOR=0 aw <cmd>" or (inv.startswith("FORCE_COLOR=0") and "| cat" not in inv) for inv in invoc_texts),
            "Missing required row: 'FORCE_COLOR=0' on a TTY",
        )

        # (e) Report every mismatch at once
        mismatches = []
        for r in rows:
            for k in ("NO_COLOR", "FORCE_COLOR"):
                os.environ.pop(k, None)
            os.environ["TERM"] = "xterm-256color"
            for k, v in r["env"].items():
                os.environ[k] = v
            T.set_color_override(r["override"])
            stream = _FakeTTY() if r["is_tty"] else _FakePipe()
            measured = T.should_color(stream, override=r["override"])
            if measured != r["expected"]:
                mismatches.append(
                    f"Invocation: {r['invoc']!r} | "
                    f"Documented: {'colored' if r['expected'] else 'monochrome'} | "
                    f"Measured: {'colored' if measured else 'monochrome'}"
                )

        if mismatches:
            self.fail(
                "Documented color contract table mismatches:\n"
                + "\n".join(mismatches)
            )
```

Passing output:
```
$ python3 -m pytest tests/test_term.py -k test_worked_cases_table_matches_should_color -o addopts=""
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
collected 26 items / 25 deselected / 1 selected

tests/test_term.py .                                                     [100%]

======================= 1 passed, 25 deselected in 0.14s =======================
```

Extracted environment and override per row:
```
#   Invocation                                    Extracted Env                       Override   TTY?   Doc Result
------------------------------------------------------------------------------------------------------------------
1   NO_COLOR=1 aw <cmd> --color                   {'NO_COLOR': '1'}                   True       True   colored
2   FORCE_COLOR=1 aw <cmd> --no-color             {'FORCE_COLOR': '1'}                False      True   monochrome
3   FORCE_COLOR=1 aw <cmd> | cat                  {'FORCE_COLOR': '1'}                None       False  colored
4   aw <cmd> | cat                                {}                                  None       False  monochrome
5   aw <cmd> --color | cat                        {}                                  True       False  colored
6   FORCE_COLOR=0 aw <cmd> | cat                  {'FORCE_COLOR': '0'}                None       False  monochrome
7   FORCE_COLOR=off aw <cmd> | cat                {'FORCE_COLOR': 'off'}              None       False  monochrome
8   FORCE_COLOR=false aw <cmd> | cat              {'FORCE_COLOR': 'false'}            None       False  monochrome
9   NO_COLOR=1 FORCE_COLOR=0 aw <cmd> | cat       {'NO_COLOR': '1', 'FORCE_COLOR': '0'} None       False  monochrome
10  NO_COLOR=1 FORCE_COLOR=0 aw <cmd>             {'NO_COLOR': '1', 'FORCE_COLOR': '0'} None       True   monochrome
11  FORCE_COLOR=0 aw <cmd>                        {'FORCE_COLOR': '0'}                None       True   colored
```

Deliberate failure demo (a) - flipped Result cell:
```
FAIL: WorkedCasesContractTests.test_worked_cases_table_matches_should_color
AssertionError: Documented color contract table mismatches:
Invocation: 'FORCE_COLOR=0 aw <cmd>' | Documented: monochrome | Measured: colored
```
Restored row 11 and test passed green (1 passed).

Deliberate failure demo (b) - deleted row:
```
FAIL: WorkedCasesContractTests.test_worked_cases_table_matches_should_color
AssertionError: 10 not greater than or equal to 11 : Expected at least 11 rows in worked cases table, found 10
```
Restored row 11 and test passed green (1 passed).

The test asserts repository content rather than production source structure (no inspect.getsource, no ast.parse over agent_workflows, no assertIn over package files), and its docstring explicitly records the OQ-02 maintainer ruling distinction.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the full committed source of the extended falsey and forcing coverage and its passing output. Paste the generated case list showing every member of `term._FORCE_COLOR_FALSEY` in at least three spellings (exact, case-variant, whitespace-padded) crossed with `NO_COLOR` set and unset and with both stream kinds, and confirm by reading that the expectation is DERIVED from the predicate's own set rather than from a copied literal. Confirm the specific previously-unpinned cell `NO_COLOR=1 FORCE_COLOR=off` on a TTY is present and expects monochrome (F-06). Paste both deliberate-failure demonstrations: monkeypatch one member out of `_FORCE_COLOR_FALSEY` inside a scratch probe (NOT by editing `term.py`, which is outside the fence) and show the derived coverage red; and show the membership assertion red when a member is absent. ALSO carry the whole-plan no-regression evidence here, since this is the last item before commit: paste the BARE `python3 -m pytest` output with its `N passed` line and state it against the pre-change baseline; paste `python3 -m pytest tests/test_term.py -o addopts=""` before and after with both counts; paste the before-and-after behavior probe over the eleven documented cells and the eight normalization spellings showing IDENTICAL results either side of the change, which is the proof that a documentation fix changed no behavior; paste `aw check`; paste `aw sanitize --agent`; and paste `git diff --cached --name-only` immediately before committing, which must list exactly `docs/cli-output-contract.md`, `docs/cli-human-guide.md` and `tests/test_term.py`.
  - Observed evidence: verified. Committed test_force_color_falsey_membership and test_force_color_extended_falsey_and_forcing passing (2 passed); 60 falsey cases generated and verified; unpinned cell NO_COLOR=1 FORCE_COLOR=off on TTY verified; deliberate failure demos 1 and 2 demonstrated red; bare pytest 3018 passed (+3); test_term.py 26 passed (+3); behavior probe 100% identical; aw check and aw sanitize clean.
Committed source of test_force_color_falsey_membership and test_force_color_extended_falsey_and_forcing:
```python
    def test_force_color_falsey_membership(self):
        """Assert exact canonical membership of T._FORCE_COLOR_FALSEY."""
        expected = frozenset({"", "0", "false", "no", "off"})
        self.assertEqual(
            T._FORCE_COLOR_FALSEY,
            expected,
            f"Unexpected _FORCE_COLOR_FALSEY: {T._FORCE_COLOR_FALSEY ^ expected}",
        )

    def test_force_color_extended_falsey_and_forcing(self):
        """Extended falsey coverage and forcing-side normalization (E-04)."""
        def spellings_for(base: str) -> list[str]:
            if base == "":
                return ["", "  ", "\t"]
            elif base == "0":
                return ["0", " 0 ", "  0 \t"]
            else:
                return [base, base.upper(), f" {base.capitalize()} "]

        required_members = {"", "0", "false", "no", "off"}
        all_bases = sorted(set(T._FORCE_COLOR_FALSEY) | required_members)

        # 1. Falsey coverage across all members, variants, NO_COLOR states, stream kinds
        for base in all_bases:
            for spelling in spellings_for(base):
                for no_color in ("1", None):
                    for stream_kind, stream_cls in (("tty", _FakeTTY), ("pipe", _FakePipe)):
                        expected = False if no_color is not None else (stream_kind == "tty")
                        case = (
                            f"spelling={spelling!r} NO_COLOR={no_color} "
                            f"on {stream_kind} (base={base!r})"
                        )
                        with self.subTest(case=case):
                            self._apply(
                                NO_COLOR=no_color,
                                FORCE_COLOR=spelling,
                                TERM="xterm-256color",
                            )
                            self.assertEqual(
                                T.should_color(stream_cls()),
                                expected,
                                f"{case}: expected {'color' if expected else 'plain'}",
                            )

        # 2. Forcing-side normalization: truthy values needing stripping or case-folding
        forcing_cases = [
            (" 1 ", "pipe", _FakePipe, None, True),
            (" 1 ", "pipe", _FakePipe, "1", True),
            (" 1 ", "tty", _FakeTTY, "1", True),
            ("TRUE", "pipe", _FakePipe, None, True),
            ("TRUE", "pipe", _FakePipe, "1", True),
            ("On", "pipe", _FakePipe, None, True),
            ("On", "pipe", _FakePipe, "1", True),
            ("2", "pipe", _FakePipe, None, True),
            ("2", "pipe", _FakePipe, "1", True),
            (" true ", "pipe", _FakePipe, None, True),
            (" true ", "pipe", _FakePipe, "1", True),
            (" YES ", "pipe", _FakePipe, None, True),
            (" YES ", "pipe", _FakePipe, "1", True),
        ]
        for force_val, stream_kind, stream_cls, no_color, expected in forcing_cases:
            case = f"FORCE_COLOR={force_val!r} NO_COLOR={no_color} on {stream_kind}"
            with self.subTest(case=case):
                self._apply(
                    NO_COLOR=no_color,
                    FORCE_COLOR=force_val,
                    TERM="xterm-256color",
                )
                self.assertEqual(
                    T.should_color(stream_cls()),
                    expected,
                    f"{case}: expected {'color' if expected else 'plain'}",
                )
```

Passing output:
```
$ python3 -m pytest tests/test_term.py -k "test_force_color" -o addopts=""
============================= test session starts ==============================
collected 26 items / 24 deselected / 2 selected

tests/test_term.py ..                                                    [100%]

======================= 2 passed, 24 deselected in 0.12s =======================
```

Generated case list (60 falsey cases across all spellings and conditions):
```
#   Base       Spelling        NO_COLOR   Stream   Expected Result
------------------------------------------------------------------
1   ''         ''              1          tty      monochrome
2   ''         ''              1          pipe     monochrome
3   ''         ''              None       tty      colored
4   ''         ''              None       pipe     monochrome
5   ''         '  '            1          tty      monochrome
6   ''         '  '            1          pipe     monochrome
7   ''         '  '            None       tty      colored
8   ''         '  '            None       pipe     monochrome
9   ''         '\t'            1          tty      monochrome
10  ''         '\t'            1          pipe     monochrome
11  ''         '\t'            None       tty      colored
12  ''         '\t'            None       pipe     monochrome
13  '0'        '0'             1          tty      monochrome
14  '0'        '0'             1          pipe     monochrome
15  '0'        '0'             None       tty      colored
16  '0'        '0'             None       pipe     monochrome
17  '0'        ' 0 '           1          tty      monochrome
18  '0'        ' 0 '           1          pipe     monochrome
19  '0'        ' 0 '           None       tty      colored
20  '0'        ' 0 '           None       pipe     monochrome
21  '0'        '  0 \t'        1          tty      monochrome
22  '0'        '  0 \t'        1          pipe     monochrome
23  '0'        '  0 \t'        None       tty      colored
24  '0'        '  0 \t'        None       pipe     monochrome
25  'false'    'false'         1          tty      monochrome
26  'false'    'false'         1          pipe     monochrome
27  'false'    'false'         None       tty      colored
28  'false'    'false'         None       pipe     monochrome
29  'false'    'FALSE'         1          tty      monochrome
30  'false'    'FALSE'         1          pipe     monochrome
31  'false'    'FALSE'         None       tty      colored
32  'false'    'FALSE'         None       pipe     monochrome
33  'false'    ' False '       1          tty      monochrome
34  'false'    ' False '       1          pipe     monochrome
35  'false'    ' False '       None       tty      colored
36  'false'    ' False '       None       pipe     monochrome
37  'no'       'no'            1          tty      monochrome
38  'no'       'no'            1          pipe     monochrome
39  'no'       'no'            None       tty      colored
40  'no'       'no'            None       pipe     monochrome
41  'no'       'NO'            1          tty      monochrome
42  'no'       'NO'            1          pipe     monochrome
43  'no'       'NO'            None       tty      colored
44  'no'       'NO'            None       pipe     monochrome
45  'no'       ' No '          1          tty      monochrome
46  'no'       ' No '          1          pipe     monochrome
47  'no'       ' No '          None       tty      colored
48  'no'       ' No '          None       pipe     monochrome
49  'off'      'off'           1          tty      monochrome
50  'off'      'off'           1          pipe     monochrome
51  'off'      'off'           None       tty      colored
52  'off'      'off'           None       pipe     monochrome
53  'off'      'OFF'           1          tty      monochrome
54  'off'      'OFF'           1          pipe     monochrome
55  'off'      'OFF'           None       tty      colored
56  'off'      'OFF'           None       pipe     monochrome
57  'off'      ' Off '         1          tty      monochrome
58  'off'      ' Off '         1          pipe     monochrome
59  'off'      ' Off '         None       tty      colored
60  'off'      ' Off '         None       pipe     monochrome

Confirmed previously-unpinned cell NO_COLOR=1 FORCE_COLOR=off on TTY:
[('off', 'off', '1', 'tty', 'monochrome')] (case #49)
```

Deliberate failure demo 1 - monkeypatching "off" out of _FORCE_COLOR_FALSEY against derived coverage:
```
Ran 1 test in 0.006s
FAILED (failures=9)
AssertionError: True != False : spelling='off' NO_COLOR=1 on tty (base='off'): expected plain
AssertionError: True != False : spelling='off' NO_COLOR=1 on pipe (base='off'): expected plain
AssertionError: True != False : spelling='off' NO_COLOR=None on pipe (base='off'): expected plain
AssertionError: True != False : spelling='OFF' NO_COLOR=1 on tty (base='off'): expected plain
AssertionError: True != False : spelling='OFF' NO_COLOR=1 on pipe (base='off'): expected plain
AssertionError: True != False : spelling='OFF' NO_COLOR=None on pipe (base='off'): expected plain
AssertionError: True != False : spelling=' Off ' NO_COLOR=1 on tty (base='off'): expected plain
AssertionError: True != False : spelling=' Off ' NO_COLOR=1 on pipe (base='off'): expected plain
AssertionError: True != False : spelling=' Off ' NO_COLOR=None on pipe (base='off'): expected plain
```

Deliberate failure demo 2 - monkeypatching "off" out of _FORCE_COLOR_FALSEY against membership assertion:
```
FAIL: test_force_color_falsey_membership (tests.test_term.ShouldColorGridTests.test_force_color_falsey_membership)
AssertionError: Items in the second set but not the first:
'off' : Unexpected _FORCE_COLOR_FALSEY: frozenset({'off'})
```

Whole-plan no-regression evidence:
1. Bare pytest suite:
Pre-change baseline: `1 failed, 3015 passed, 2 skipped, 3 warnings in 83.91s (0:01:23)`
Post-change: `1 failed, 3018 passed, 2 skipped, 3 warnings in 115.44s (0:01:55)` (+3 passed, 0 new failures; single pre-existing failure in tests/test_dependency_block_reporting.py).
2. Per-test counts on tests/test_term.py:
Before: `23 passed in 10.39s`
After: `26 passed in 2.44s`
3. Before-and-after behavior probe (11 documented cells + 8 normalization spellings):
```
=== 11 DOCUMENTED CELLS ===
NO_COLOR=1 aw <cmd> --color                   -> colored
FORCE_COLOR=1 aw <cmd> --no-color             -> monochrome
FORCE_COLOR=1 aw <cmd> | cat                  -> colored
aw <cmd> | cat                                -> monochrome
aw <cmd> --color | cat                        -> colored
FORCE_COLOR=0 aw <cmd> | cat                  -> monochrome
FORCE_COLOR=off aw <cmd> | cat                -> monochrome
FORCE_COLOR=false aw <cmd> | cat              -> monochrome
NO_COLOR=1 FORCE_COLOR=0 aw <cmd> | cat       -> monochrome
NO_COLOR=1 FORCE_COLOR=0 aw <cmd>             -> monochrome
FORCE_COLOR=0 aw <cmd>                        -> colored

=== 8 NORMALIZATION SPELLINGS ===
FORCE_COLOR=" 1 " | cat                       -> colored
FORCE_COLOR="TRUE" | cat                      -> colored
FORCE_COLOR="On" | cat                        -> colored
FORCE_COLOR="2" | cat                         -> colored
NO_COLOR=1 FORCE_COLOR="OFF"                  -> monochrome
NO_COLOR=1 FORCE_COLOR="False"                -> monochrome
NO_COLOR=1 FORCE_COLOR=" no "                 -> monochrome
NO_COLOR=1 FORCE_COLOR=""                     -> monochrome
```
Results before and after are 100% byte-identical.
4. `aw check`:
Clean across all edited files (0 findings for mj18mi or touched files).
5. `aw sanitize --agent`:
Clean (`{"outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0}`).
6. `git diff --cached --name-only` immediately before commit:
docs/cli-human-guide.md
docs/cli-output-contract.md
tests/test_term.py
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan was authored `to-review` with NO `- Readiness:` field, which was correct: that field is an OUTPUT of review and writing one at authoring time would forge the attestation that gates auto-approval. Review has since recorded a readiness value in front matter; explicit human approval (`Status: approved`) is still required before execution.

WHAT REVIEW CHANGED, because one finding alters the code E-03 commissions rather than the prose an executor reads. PR-301: the table-driven guard must STRIP THE MARKDOWN BACKTICKS before parsing an invocation, and must ASSERT that it extracted a non-empty environment for every `=`-bearing row. Measured at review, a parser that omits the strip extracts an empty environment for every row, and five of E-01's six new rows then PASS while setting no environment at all; the row floor and named-row checks in E-03(d) do not catch it because both inspect row text rather than extraction output. Exactly one row goes red, which is worse than all-red, because it tells the executor the document is wrong when the parser is. V-03 now requires the extracted environment pasted per row.

SCOPE FENCE. Touch only the three paths in `- Scope-Paths:`. Do NOT edit `agent_workflows/term.py` (the code is the authority here, F-04/F-12), any `.spec.md`, or the four other dangling doc citations outside the one sentence E-01 rewrites (carried by `ikxtkj`). If an out-of-scope edit turns out to be genuinely necessary, MAKE IT AND JUSTIFY IT: `aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path, so an unexpected edit is a thing to explain rather than a reason to stop. The one condition that DOES warrant stopping is the inverted-premise case named below (a measured color cell moving), because continuing would mean correcting the wrong artifact.

On execution, the executor MUST: commit only the three paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; verify the staged set with `git diff --cached --name-only` before committing, since this is a shared checkout and another party's work must never be swept in; run the BARE `python3 -m pytest` suite and paste its ACTUAL output rather than claiming success; and complete every `V-*` item with the concrete pasted evidence it demands, including the four deliberate-failure demonstrations in V-03 and V-04 that prove the new coverage consists of real guards rather than tests that were never red.

THE ONE WAY THIS PLAN CAN FAIL SILENTLY, stated for the executor: this is a DOCUMENTATION fix whose whole premise is that the code is correct (F-04, F-12). If any measured color cell moves, the plan has inverted its own premise and corrected the wrong artifact. V-04's before-and-after behavior probe is the check that catches it, and it must be performed by comparing the two pasted probe outputs, not by observing that the suite is green. Equally, do NOT edit `agent_workflows/term.py` to make a document sentence easier to write: the sentence is what changes here.

This plan inherits `- Blocks-Release: next` from backlog item `bar5t8` because its `- Work-Kind:` is `bug`, and the repository policy is that every live bug gates the next release. That gate travels with this plan and must not be cleared as part of executing it. OQ-01 records why the classification stands and what would change if a maintainer reclassified it.

The plan MUST reach `.aw/records/plans/executed/` only once `aw ipd lint --phase pre-transition` reports conforming and every validation item above is verified with pasted evidence. WHO PERFORMS THE TRANSITION IS CONDITIONAL: under `aw oc run` / `aw agy run` the RUNNER owns begin/finalize and the executor must NOT call finalize itself; only when working by hand outside a runner does the executor run `aw ipd finalize`. Never hand-roll a `git mv` into `executed/`. If any validation item cannot be satisfied, leave the plan in `pending/` and report the blocker.
