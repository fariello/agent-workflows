# IPD: Unify the three divergent should_color implementations and stop a falsey FORCE_COLOR forcing color on

- Date: 2026-09-19
- Kind: child
- Concern: THREE INDEPENDENT `should_color` IMPLEMENTATIONS DISAGREE WITH EACH OTHER, and one inverts the meaning of a value users set deliberately. Measured by EXECUTION 2026-09-19, not by reading. `term.py:90` checks `TERM`, tests `NO_COLOR` by PRESENCE, and lets `FORCE_COLOR` escape it. `runner_shared.py:276` IGNORES `TERM` entirely and tests by TRUTHINESS, so `TERM=dumb aw oc run` emits color while `TERM=dumb aw attention` does not. `pwatch.py:951` ignores `FORCE_COLOR` completely, so `FORCE_COLOR=1 aw pwatch | cat` is plain while every other command colorizes. Worst of the four: `FORCE_COLOR=0` FORCES COLOR ON, even to a pipe, because the string `"0"` is truthy in Python, so a user writing the value that plainly means "do not force" gets the opposite. This blocks spec `uonrjg` R9.3a.2, which requires the depth resolver have EXACTLY ONE definition: a resolver cannot have one definition while the capability decision beneath it has three.
- Scope: IN: one shared `should_color` with one definition, carrying the maintainer's 2026-09-19 semantics (`NO_COLOR` presence-only; `FORCE_COLOR` interprets falsey values); `runner_shared.py` and `pwatch.py` consuming it instead of reimplementing; and a test pinning every cell of the two measured tables, none of which is pinned today. OUT: the depth ladder and the 16-color tier (child `pow5sj`, which sits ON this seam), the `--color`/`--no-color` FLAG surface (plan `yaxr4i`), and any lifecycle glyph or palette work.
- Scope-Paths: agent_workflows/term.py, agent_workflows/runner_shared.py, agent_workflows/pwatch.py, tests/test_term.py, tests/test_runner_shared.py, tests/test_runner_refork_guard.py, tests/test_rununify_run_queue.py, tests/fixtures/runner_shared_premove_fingerprints.json, tests/test_pwatch.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Set: lifeglyph
- Order: 9
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: z8ddk0
- From-Backlog: nyz8dt
- Blocks-Release: next
- Work-Kind: bug

## Workflow history
- 2026-09-19 reviewed (aw set): /plan-review round 1 complete (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901..PR-907 all FIXED, none deferred, none open; readiness go-pending-approval. Review record at .aw/records/reviews/20260919-lifeglyph-09-z8ddk0-unify-the-three-divergent-should-color-implementations-and-s.review.md. Human approval is still required and was NOT given.

- 2026-09-19 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901 through PR-907 all FIXED, none deferred, none open. Reviewed at HEAD `3a513262`; `aw ipd lint --phase author --agent` clean, exit 0, before and after. THE DIAGNOSIS IS CORRECT IN EVERY PARTICULAR and I re-executed all four defects rather than reading them. Every finding is therefore about the FIX, and the three serious ones share one root: the plan described the intended END STATE accurately and never described the EDIT that reaches it, so each of the three named source changes had a shortest-path implementation that is wrong in a way the plan's own validation would not catch. I found each by applying the naive edit and measuring. PR-901 (HIGH): E-01 named only the TRUTHINESS read of `FORCE_COLOR` at `term.py:103`, leaving the PRESENCE read at `:100` a presence test, so the literal edit lets a falsey `FORCE_COLOR` still CANCEL `NO_COLOR` while no longer forcing; measured, all TWELVE `NO_COLOR`-set cells then colorize on a TTY, `NO_COLOR=1 FORCE_COLOR=0` among them, which voids the accessibility convention the whole ruling defers to and is strictly worse than the bug being fixed. E-01 now mandates ONE forcing predicate at both sites and V-05 requires the NAIVE edit (not a full revert) as the mutation that must fail. PR-902 (HIGH): E-02's "exactly one definition in the package" reads as delete-the-def-and-import, which FAILS FOUR shipped guards, three of which exist specifically to assert `runner_shared` DEFINES this symbol; measured per shape, the sanctioned one-line delegation keeps three green and the byte-identical fingerprint fails under both, so it needs a declared `SUPERSEDED_SINCE_MOVE` exemption (new E-03) with two count updates. FIVE test surfaces were undeclared, including the historical fixture, so an executor would have faced four red tests outside its fence and would plausibly have repaired them by rewriting the anti-re-fork evidence. PR-903 (HIGH): only two of `pwatch`'s three conjuncts are the shared decision, so the obvious conversion SILENTLY DELETES `--no-color`; measured on a pty (current `False`, naive `True`), and its two shipped tests run through a PIPE so `10 passed` either way. PR-904 (MEDIUM) corrects the plan's own success criterion: the post-fix `def` count is 2, not 1, so E-04's guard and V-02's evidence were both unobtainable, and the same wording propagates to `pow5sj`'s V-01. Also fixed: an absent scope fence and honesty rule (alone among the nine children) plus the flagged hand-rolled `git mv` wording (PR-906), a missing suite baseline where two sibling numbers conflict (PR-907), and one overstated Step 0 claim (PR-905). Item count 4 -> 7, decomposition not scope creep. Suite baseline `7306 passed, 3 skipped, 2 xfailed`. OQ-01 is non-blocking and carried by `yaxr4i`; no question blocks execution. Readiness go-pending-approval.
- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `nyz8dt` on the maintainer's instruction to convert it into a lifeglyph child rather than keep it standalone. Carries `nyz8dt`'s `Blocks-Release: next` and `Work-Kind: bug`. ORDER 9 IS NOT ITS QUEUE POSITION: `queue_sort_key` puts `dependency_depth` FIRST, so this depth-0 child precedes `pow5sj`, which declares `executed:z8ddk0`. The Order number is a filename cluster, not evidence of sequence.

## Goal

Make the color capability decision have one definition with the maintainer's ruled semantics, so the depth resolver `pow5sj` builds can honestly claim R9.3a.2's "exactly one definition" and so a falsey `FORCE_COLOR` stops meaning its own opposite.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: One definition, with the ruled semantics

- [ ] E-01 Make `term.should_color` the single definition and apply the maintainer's 2026-09-19 semantics: `NO_COLOR` is PRESENCE-ONLY (any setting disables, empty included, no value interpreted); `FORCE_COLOR` INTERPRETS its value, so `0`/`false`/`no`/`off` mean NOT FORCING and fall through to ordinary TTY detection rather than suppressing.

  IMPLEMENT ONE FORCING PREDICATE AND CONSULT IT IN BOTH PLACES. This is the whole content of the item and the reason it is not a two-line edit. `term.py` reads `FORCE_COLOR` TWICE: by PRESENCE at `:100` (where it cancels `NO_COLOR`) and by TRUTHINESS at `:103` (where it forces). Changing only the second reading, which is the literal text of this item's first sentence and is the edit an executor will reach for, leaves the FIRST reading a presence test, and a presence test is now WRONG because a falsey `FORCE_COLOR` must no longer cancel `NO_COLOR`. MEASURED AT REVIEW by executing that exact naive edit: it produces COLOR ON A TTY for all twelve cells where `NO_COLOR` is set and `FORCE_COLOR` is present, including `NO_COLOR=1 FORCE_COLOR=0`, which is a NEW accessibility regression strictly worse than the defect being fixed (see F-05). So define one helper, e.g. `_force_color_is_forcing() -> bool` returning `v is not None and v.strip().lower() not in {"", "0", "false", "no", "off"}`, and write the `NO_COLOR` rung as `"NO_COLOR" in os.environ and not _force_color_is_forcing()`. Both readings then move together by construction, which is the durable property; a second independent falsey check at each site would re-create the same two-reading split this item exists to close.
  - Depends on: none
  - Expected outcome: `FORCE_COLOR=0` no longer forces color and no longer reaches a pipe; it falls through, giving color on a TTY and plain to a pipe. `NO_COLOR=1 FORCE_COLOR=0` is PLAIN on a TTY (the naive edit makes it colored). `FORCE_COLOR=1` still beats `NO_COLOR=1`, so `tests/test_term.py:48` keeps passing unchanged. `FORCE_COLOR=''` is read ONCE, through the shared predicate, so the presence-versus-truthiness contradiction at `:100`/`:103` is structurally gone rather than merely corrected at one of the two sites.
  - Execution state: pending

- [ ] E-02 Convert `runner_shared.py:275` to consume the single definition instead of reimplementing it, in the SANCTIONED WRAPPER SHAPE rather than as an import. Note this makes the runners start honoring `TERM=dumb`, a behavior CHANGE and the correct one.

  THE SHAPE IS NOT FREE, AND THE OBVIOUS SHAPE BREAKS FOUR SHIPPED GUARDS. Measured at review by running the real guard methods against each candidate shape (F-06): deleting `runner_shared`'s `def` in favor of `from agent_workflows.term import should_color` FAILS four tests, because three separate harnesses assert that `runner_shared` DEFINES this symbol (`test_runner_refork_guard.py:224` region via `Owned("should_color", "runner_shared", BOTH)`; `test_rununify_run_queue.py:93` `RESOLVES_IN_RUNNER_SHARED`; `test_runner_shared.py` `test_exactly_one_definition_package_wide`, which asserts exactly ONE in-scope def site and gets zero). USE SHAPE B, the one-line delegating wrapper the repository already sanctions for exactly this case (`is_pure_delegation`, `tests/test_rununify_run_queue.py:250`): a single `return` statement naming the shared callable, docstring permitted. Measured, Shape B keeps three of the four guards PASSING. The fourth is E-03's work, so do not attempt to satisfy it here.
  - Depends on: E-01
  - Expected outcome: `runner_shared.should_color` is a one-statement delegation to `term.should_color`; both runners still reach it at their existing 15 call sites unchanged. `TERM=dumb aw oc run` is plain, matching `aw attention`. `test_runner_refork_guard`, `test_rununify_run_queue`'s closure classification, and `test_exactly_one_definition_package_wide` all still pass.
  - Execution state: pending

- [ ] E-03 Re-baseline the ONE guard E-02 cannot satisfy in place: `tests/test_runner_shared.py::PureMoveFingerprintTests::test_every_clean_symbol_is_a_STRICT_fingerprint_match`, which holds `should_color`'s BODY byte-identical to the pre-move capture in `tests/fixtures/runner_shared_premove_fingerprints.json`, and which therefore FAILS under every shape that changes that body (measured: both Shape A and Shape B fail). This is deliberate, not incidental: that harness exists to prove a moved body was not silently edited, so a legitimate supersession must be DECLARED there rather than worked around.

  DO IT THE WAY THE FILE ALREADY DOES IT, which is an enumerated exemption with a written reason. Add `should_color` to `SUPERSEDED_SINCE_MOVE` (`tests/test_runner_shared.py:199`), which is the list `state_root` and `_run_git` already occupy for exactly this reason ("SUPERSEDED by design in subsequent approved IPDs"), and write the paragraph of justification the file's convention requires beside theirs, citing this plan's id. TWO COUNT ASSERTIONS MOVE WITH IT and both are in the same method: the clean-move count `23` becomes `22` and `len(SUPERSEDED_SINCE_MOVE)` `2` becomes `3`. Measured at review: leaving either untouched fails. Do NOT instead delete the exemption machinery, loosen the comparison, or edit the FIXTURE's captured fingerprint: the fixture is a historical capture of pre-move bodies, and rewriting it would destroy the harness's only evidence rather than record a supersession.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest tests/test_runner_shared.py` passes; `should_color` appears in `SUPERSEDED_SINCE_MOVE` with a reason naming `z8ddk0`; the two counts are updated together in the same method; the fixture JSON is UNCHANGED.
  - Execution state: pending

- [ ] E-04 Convert `pwatch.py:950-952` to consume the single definition, PRESERVING its `--no-color` flag as an override ABOVE the shared decision. This makes `pwatch` start honoring `FORCE_COLOR` and `TERM`, both behavior CHANGES and both correct.

  THE FLAG MUST SURVIVE THE CONVERSION AND ITS OWN TESTS WILL NOT TELL YOU IF IT DOES NOT. `pwatch`'s expression is `not args.no_color and os.environ.get("NO_COLOR") is None and sys.stdout.isatty()`; only the last two conjuncts are the shared decision, and `args.no_color` is a USER-FACING flag (`pwatch.py:847`) with no equivalent inside `should_color`, which reads no argparse state. Replacing the whole expression with `term.should_color(sys.stdout)` therefore SILENTLY DELETES `--no-color`. Measured at review on a real pty: with `--no-color` passed, the current expression yields `False` and the naive replacement yields `True`. Write it as `color_enabled = not args.no_color and term.should_color(sys.stdout)`. AND NOTE THE MEASUREMENT GAP (F-07): the two shipped tests that pass `--no-color` (`tests/test_pwatch.py:225`, `:236`) run through a PIPE, where `isatty()` is already False, so both keep passing with the flag entirely removed; they cannot detect this regression, which is why E-06 adds a pty case.
  - Depends on: E-01
  - Expected outcome: `color_enabled` consults the shared decision with `--no-color` layered above it. `FORCE_COLOR=1 aw pwatch | cat` colorizes, matching every other command. `TERM=dumb` is plain. `aw pwatch --no-color` on a REAL TTY is still plain.
  - Execution state: pending

### Task group 2: Pin what was never pinned

- [ ] E-05 Pin EVERY cell of the two measured tables in `tests/test_term.py`: the 4x4 `NO_COLOR` x `FORCE_COLOR` grid (unset / `''` / `'0'` / `'1'`) against both a TTY and a pipe, plus the `TERM` axis (`xterm-256color` / `dumb` / `''` / unset). None of the empty-string or `'0'` cases is pinned today, which is why all four defects survived: the behavior is accidental, not contractual.

  THE TWELVE `NO_COLOR`-SET CELLS ARE THE POINT, not filler. They are what distinguishes the correct composition from the naive edit E-01 warns about: the two implementations agree on the four cells where `NO_COLOR` is unset and disagree on all twelve where it is set (measured at review, F-05). A grid that pins only the headline `FORCE_COLOR='0'` case therefore passes for the broken edit. Pin the EXPECTED value explicitly per cell rather than computing it from the implementation, and name each case so a failure identifies the cell. The authoritative expectations are the table reproduced under `## Project conventions discovered` below, itself the backlog `nyz8dt` tri-state ruling made concrete.
  - Depends on: E-01
  - Expected outcome: a table-driven test whose 32 env cases (16 cells x 2 stream kinds) plus 8 `TERM` cases are the measured grid, each with a named expectation. Reverting any part of E-01 fails at least one named case, INCLUDING the naive single-site edit.
  - Execution state: pending

- [ ] E-06 Pin the two consumer behavior CHANGES E-02 and E-04 make, because neither is covered by any existing test and both are the user-visible half of this plan. (a) `runner_shared.should_color` honors `TERM=dumb` (it ignores `TERM` entirely today, and no test reads `TERM` against it). (b) `pwatch`'s `--no-color` still suppresses color ON A REAL TTY after the conversion, which requires a pty because a piped run is already colorless and so cannot distinguish the flag working from the flag being deleted (F-07). Use `pty.fork`, as measured at review; `tests/test_pwatch.py` already shells out via `subprocess`, so this is a new case in a familiar file rather than a new harness.
  - Depends on: E-02, E-04
  - Expected outcome: a `TERM=dumb` case against `runner_shared.should_color` that FAILS before E-02, and a pty-based `pwatch --no-color` case that FAILS if the flag conjunct is dropped. Both named so the failure says which behavior regressed.
  - Execution state: pending

- [ ] E-07 Add a guard asserting the package contains exactly ONE ORIGINATING `should_color` definition, so a future module cannot quietly add a fourth. This is the mechanical property R9.3a.2 demands and that `pow5sj`'s V-01 will grep for.

  THE OBVIOUS FORM OF THIS GUARD IS FALSE AFTER E-02, and getting this wrong makes the guard either permanently red or decorative. `grep -c "def should_color"` returns TWO after E-02, because the sanctioned delegating wrapper in `runner_shared` IS a `def` (measured at review). So the guard must assert one ORIGINATING definition and permit sanctioned delegations, which is precisely the distinction `is_pure_delegation` (`tests/test_rununify_run_queue.py:250`) already draws: reuse that predicate rather than authoring a second notion of the same thing. State the rule as: across `agent_workflows/*.py`, exactly one top-level `def should_color` is not a pure delegation, and it is in `term.py`. AST, not substring: the file-local convention (`tests/test_runner_refork_guard.py` docstring) records that `assertNotIn("class Palette:", src)` was evaded by whitespace and satisfied by a comment.
  - Depends on: E-02, E-04
  - Expected outcome: a test that FAILS if a second ORIGINATING definition is introduced and PASSES with `runner_shared`'s sanctioned wrapper present. `pow5sj`'s one-definition evidence becomes true by construction rather than by inspection at that moment, and its V-01 `grep` expectation is corrected by this plan's V-07 evidence rather than left to surprise that plan's executor.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Verified 2026-09-19 BY EXECUTION: with `NO_COLOR=1 FORCE_COLOR=1` on a TTY, `term.should_color` returns True, so `FORCE_COLOR` currently beats `NO_COLOR` and the maintainer's Reading A preserves that.
- Verified 2026-09-19: `FORCE_COLOR=0` yields color to a PIPE in both `term.py` and `runner_shared.py`; `TERM=dumb` yields color in `runner_shared.py` but not `term.py`; `FORCE_COLOR=1` yields plain in `pwatch.py` alone.
- Verified 2026-09-19, CORRECTED AT REVIEW (F-09): nothing in `agent_workflows/` or CI sets `NO_COLOR` or `FORCE_COLOR`, so for the package both are always the user's own environment. The ONE assignment anywhere in the repo is `tools/aw_upgrade_test.py:543` (`env["NO_COLOR"] = "1"` for a sandboxed subprocess), which is a deliberate harness choice unaffected by this plan. The earlier absolute wording ("NOTHING in the package, the runners, or CI", "zero assignments") would have misled the next reader auditing this.
- `--no-color` exists on the shared `common` parser (`cli.py:832`) but does NOT set `NO_COLOR` or route through `should_color`: it constructs `Term(color=False)` directly. `--color` does not exist at all. Both facts belong to `yaxr4i`, not here. NOTE the separate case of `pwatch --no-color` (`pwatch.py:847`), which is INSIDE this plan's scope because E-04 rewrites the expression that reads it; see F-07.
- The suite runs BARE as `python3 -m pytest` per AGENTS.md. BASELINE MEASURED AT REVIEW, 2026-09-19, at HEAD `3a513262`: `7306 passed, 3 skipped, 2 xfailed in 161.81s`. A post-execution run must be read against this number, not against a remembered one; sibling `lifeglyph` reviews recorded `8369` and `7468` at earlier commits because the lane was rebased and suites were consolidated, so a DIFFERENT total is expected and only an unexplained FAILURE is a finding.
- `- Readiness:` is deliberately absent at authoring (it is `/plan-review`'s output; IPD-M107 refuses an unattested value). This review writes it.

### The authoritative expectation table (added at review; E-05 pins exactly this)

Both grids below were EXECUTED at review, 2026-09-19, against a composition implementing the backlog `nyz8dt` ruling (`NO_COLOR` presence-only, suppressing unless `FORCE_COLOR` is genuinely FORCING; `FORCE_COLOR` forcing iff non-empty and not in `{0,false,no,off}`). They are the target behavior, not the current behavior. Written here so E-05 pins a stated contract rather than whatever the implementation happens to do, and so a reviewer can dispute a cell.

`TERM=xterm-256color`, `NO_COLOR` down, `FORCE_COLOR` across, each cell `TTY / PIPE`:

| `NO_COLOR` \ `FORCE_COLOR` | unset | `''` | `'0'` | `'1'` |
|---|---|---|---|---|
| unset | color / plain | color / plain | color / plain | color / COLOR |
| `''` | plain / plain | plain / plain | plain / plain | color / COLOR |
| `'0'` | plain / plain | plain / plain | plain / plain | color / COLOR |
| `'1'` | plain / plain | plain / plain | plain / plain | color / COLOR |

`TERM` axis, `NO_COLOR` and `FORCE_COLOR` both unset:

| `TERM` | TTY | PIPE |
|---|---|---|
| `xterm-256color` | color | plain |
| `dumb` | plain | plain |
| `''` | plain | plain |
| unset | plain | plain |

THE TWO ROWS THAT CARRY THE WHOLE FINDING SET. Row `unset` / column `'0'` is the headline defect: color to a PIPE today, plain after the fix. The twelve cells in the lower three rows are what F-05 is about: the correct composition makes every one of them plain except where `FORCE_COLOR` genuinely forces, while the naive single-site edit makes all twelve COLORED on a TTY.

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | High | `FORCE_COLOR=0` forces color ON, even to a pipe, because `"0"` is truthy. A user writing it means the opposite. This is the likeliest of the four to be hit, since `FORCE_COLOR=0` is common in CI configuration. | Measured 2026-09-19: `NO_COLOR` unset, `FORCE_COLOR='0'` gives COLOR to both a TTY and a pipe in `term.py` and `runner_shared.py`. |
| F-02 | High | Three implementations, three behaviors. They agree on the four ordinary cases and diverge on empty strings and on `TERM`, so the spec's Section 9.3 instruction to "preserve current behavior" is UNDERSPECIFIED: there are three current behaviors. | `term.py:90`, `runner_shared.py:276`, `pwatch.py:951`, each read and executed 2026-09-19. |
| F-03 | Medium | `yaxr4i` line 97 asserts "The color ENGINE is already correct and complete... it does not need new color logic". That premise is FALSIFIED by F-01 and F-02, and `yaxr4i` is `approved`, so an executor would otherwise trust it and leave the engine alone. This plan does not amend `yaxr4i` (it is approved and owns a different axis) but records the falsification so the next reader of that line is not misled. | `yaxr4i` line 97; contradicted by the measurements above. |
| F-04 | Medium | No test pins any empty-string or `'0'` case, so none of this behavior is contractual and all four defects were free to survive. | `grep` for `NO_COLOR.*= ""` in `tests/` returns nothing, 2026-09-19. |
| F-05 | High | ADDED AT REVIEW. THE LITERAL READING OF E-01 INTRODUCES AN ACCESSIBILITY REGRESSION WORSE THAN THE DEFECT IT FIXES. `term.py` reads `FORCE_COLOR` twice, by PRESENCE at `:100` (cancelling `NO_COLOR`) and by TRUTHINESS at `:103` (forcing). E-01 as originally written named only the forcing test, and applying exactly that edit makes a falsey `FORCE_COLOR` still CANCEL `NO_COLOR` while no longer forcing, so the fall-through reaches TTY detection and colorizes. Measured by executing the naive edit: all TWELVE cells with `NO_COLOR` set and `FORCE_COLOR` present return color on a TTY, `NO_COLOR=1 FORCE_COLOR=0` among them. `NO_COLOR` is the accessibility convention the whole ruling defers to, so silently voiding it for any user who also sets a falsey `FORCE_COLOR` is the worst available outcome. E-01 now mandates ONE forcing predicate consulted at both sites, and E-05 pins all twelve cells, which is what makes the naive edit fail. | `term.py:99-104`; naive-edit grid executed 2026-09-19 (12 of 12 `NO_COLOR`-set cells colored on a TTY); correct-composition grid executed for contrast (0 of 12 colored except where `FORCE_COLOR` genuinely forces). |
| F-06 | High | ADDED AT REVIEW. E-02's DELIVERABLE AS WORDED BREAKS FOUR SHIPPED GUARDS, and three of them exist specifically to assert that `runner_shared` DEFINES this symbol, which "consume it instead of reimplementing it" reads as an instruction to stop doing. Measured by running the real guard methods against a patched source: the import shape fails `test_runner_refork_guard::test_the_owning_module_really_defines_every_tabled_symbol`, `test_rununify_run_queue::test_the_shared_resolving_names_really_do_resolve_in_runner_shared`, `test_runner_shared::test_exactly_one_definition_package_wide` (0 sites where 1 is asserted), and the fingerprint harness. The one-line delegating wrapper the repo already sanctions keeps the first three PASSING. The fourth (the byte-identical fingerprint) fails under BOTH shapes and needs a declared exemption, which is now E-03. Left unsplit, an executor would hit four red tests with no guidance and would plausibly "fix" them by editing the guards or the fixture, destroying the anti-re-fork evidence. | `Owned("should_color", "runner_shared", BOTH)` at `tests/test_runner_refork_guard.py:137`; `RESOLVES_IN_RUNNER_SHARED` at `tests/test_rununify_run_queue.py:93`; `tests/test_runner_shared.py:634` `test_exactly_one_definition_package_wide`, `:420` `test_every_clean_symbol_is_a_STRICT_fingerprint_match`, `:199` `SUPERSEDED_SINCE_MOVE`; `is_pure_delegation` at `tests/test_rununify_run_queue.py:250`; all four run against both candidate shapes 2026-09-19. |
| F-07 | High | ADDED AT REVIEW. CONVERTING `pwatch` THE OBVIOUS WAY SILENTLY DELETES A USER-FACING FLAG, AND ITS OWN TESTS CANNOT SEE IT. `pwatch.py:951` is `not args.no_color and os.environ.get("NO_COLOR") is None and sys.stdout.isatty()`; only the last two conjuncts are the shared decision. `should_color` reads no argparse state, so replacing the whole expression drops `--no-color` (`pwatch.py:847`). Measured on a real pty: with `--no-color`, current yields `False`, naive replacement yields `True`. The two shipped tests passing `--no-color` (`tests/test_pwatch.py:225`, `:236`) run through a PIPE where `isatty()` is already False, so both pass with the flag entirely removed: `10 passed` either way. E-04 now mandates the flag stay layered above, and E-06 adds the pty case that can actually detect the loss. | `pwatch.py:847,950-952`; `tests/test_pwatch.py:225,236`; pty measurement 2026-09-19 (`--no-color`: current `False`, naive `True`); `python3 -m pytest tests/test_pwatch.py` -> `10 passed`. |
| F-08 | Medium | ADDED AT REVIEW. E-04's one-definition guard AS WORDED would be false the moment E-02 lands, because the sanctioned delegating wrapper is itself a `def`, so a `grep -c "def should_color"` guard returns 2 and a naive assertion of 1 is permanently red. This also propagates: `pow5sj`'s V-01 demands a `grep` proving exactly one definition, and V-02 here originally demanded `grep -rn "def should_color"` return exactly ONE LINE, which the correct implementation contradicts. Both are corrected to the ORIGINATING-definition property, reusing the existing `is_pure_delegation` predicate rather than inventing a second notion. | `pow5sj` V-01 ("Paste `grep -c` proving exactly ONE depth-resolver definition"); this plan's original V-02; `is_pure_delegation` at `tests/test_rununify_run_queue.py:250`; measured post-E-02 def count = 2. |
| F-09 | Low | ADDED AT REVIEW. The plan's Step 0 claim that "NOTHING in the package, the runners, or CI ever SETS `NO_COLOR` or `FORCE_COLOR`" is very nearly right but not exact: `tools/aw_upgrade_test.py:543` sets `env["NO_COLOR"] = "1"` for its sandboxed subprocess. That is a deliberate harness choice and is unaffected by this plan (presence-only `NO_COLOR` is the semantics it already relies on), but the absolute wording would mislead a later reader auditing the same question. Corrected in place. | `tools/aw_upgrade_test.py:543`; `grep` over `agent_workflows/`, `tools/`, CI config 2026-09-19. |

## Proposed changes (ordered, validatable)

1. One definition in `term.py` carrying the ruled semantics, via ONE forcing predicate consulted at both `FORCE_COLOR` read sites (E-01).
2. `runner_shared` consumes it as a sanctioned one-line delegation (E-02).
3. The fingerprint harness records the supersession as an enumerated exemption (E-03).
4. `pwatch` consumes it with `--no-color` preserved above it (E-04).
5. Table-driven pins for the full measured grid plus the `TERM` axis (E-05).
6. Pins for the two consumer behavior changes, including a pty case for `pwatch --no-color` (E-06).
7. A guard forbidding a fourth ORIGINATING definition, permitting sanctioned delegations (E-07).

## Deferred / out of scope (with reason)

- The `--color` / `--no-color` FLAG surface and their mutual exclusivity: owned by plan `yaxr4i` E-02, which the maintainer ruled on 2026-09-19 (two flags, mutually exclusive). This plan fixes the ENGINE those flags will sit on.
  - Carrier: yaxr4i
- The depth ladder, the authored 16-color tier, and `aw config` depth pinning: child `pow5sj`, which declares `executed:z8ddk0` so it builds on the unified seam.
  - Carrier: pow5sj
- Amending spec `uonrjg` Section 9.3a.2, whose "unchanged, and unconditional" wording is false as written (`FORCE_COLOR` does currently defeat `NO_COLOR`), and Section 9.3, which says "preserve current behavior" where three behaviors exist.
  - Carrier: 7p3tt8
- Correcting `docs/cli-human-guide.md:74`, whose precedence sentence ("`NO_COLOR` ... is only overridden by `FORCE_COLOR`") becomes imprecise once only a FORCING `FORCE_COLOR` overrides. Added at review; see Spec / documentation sync for why the carrier is right and what it does not yet name.
  - Carrier: 7p3tt8
- Amending `yaxr4i` to correct its falsified "engine is already correct and complete" premise (F-03).
  - Carrier-Declined: NOT THIS PLAN'S TO EDIT, and the risk it guards against is already removed by this plan EXISTING. `yaxr4i` is `approved` and owns the flag surface, a different axis; amending an approved plan to fix a premise about work this plan now performs would be churn. The hazard was that an executor trusts line 97 and leaves the engine alone, and that cannot happen once the engine is owned by a child with its own E-items. F-03 records the falsification so the next reader of that line is not misled, which is the durable part.

## Scope check

- Over-scope: none. Each E-item maps to a measured divergence, to R9.3a.2's one-definition requirement, or to a shipped guard that the measured change provably disturbs.
- Under-scope: CLOSED AT REVIEW, and the gaps were not cosmetic. The original four items named three source files and one test file, while the measured change touches FIVE test surfaces the plan did not declare: three anti-re-fork guards, one historical fixture, and `tests/test_pwatch.py`. E-03 and E-06 now own that work and `- Scope-Paths:` declares it. An executor working from the original declaration would have finished with red tests outside its own fence and no authority to touch them, which is the specific failure mode the finalize scope gate then refuses.
- Under-scope, remaining and deliberate: this plan does NOT widen to the `cli.py` flag surface even though it is adjacent, because `yaxr4i` already owns it and two plans editing one argparse parent is how a Set acquires merge conflicts for no benefit. Note the distinction from `pwatch --no-color`, which IS in scope: that flag is read by an expression E-04 rewrites, so preserving it is part of this plan's own edit rather than an incursion into `yaxr4i`'s axis.

## Required tests / validation

Run the suite BARE: `python3 -m pytest`, and paste the actual summary line. The review baseline at HEAD `3a513262` is `7306 passed, 3 skipped, 2 xfailed`; compare against that number rather than a remembered one.

E-02 and E-04 change runner and pwatch behavior, so the run must be read for collateral damage rather than only for green: any test that encoded the OLD divergence (runner colorizing under `TERM=dumb`, pwatch ignoring `FORCE_COLOR`) should be UPDATED with its reason recorded, never deleted silently.

FOUR SPECIFIC HARNESSES WILL REACT, three of them by design and one requiring a declared exemption. Measured at review by running the real guard methods against patched source, so this is not a precaution but a prediction: `tests/test_runner_refork_guard.py` and `tests/test_rununify_run_queue.py` PASS under E-02's sanctioned wrapper shape and FAIL under the import shape; `tests/test_runner_shared.py::test_exactly_one_definition_package_wide` likewise; and `tests/test_runner_shared.py::test_every_clean_symbol_is_a_STRICT_fingerprint_match` FAILS under BOTH shapes and is E-03's work. IF ANY OF THESE FOUR IS RED AT THE END, the fix is in this plan's items, NOT in the guard: do not edit an assertion, loosen a comparison, or rewrite `tests/fixtures/runner_shared_premove_fingerprints.json`, all of which destroy anti-re-fork evidence that took a prior Set to establish.

## Spec / documentation sync

No `.spec.md` edit here, so none is declared in `- Scope-Paths:`. The two false statements in `uonrjg` (Section 9.3a.2's "unchanged, and unconditional" and Section 9.3's "preserve current behavior") are carried by child `7p3tt8`, which already declares a specs path and owns the amendment work.

THE USER-FACING DOCUMENTATION THIS PLAN FALSIFIES IS ALSO `7p3tt8`'s, checked at review rather than assumed, and the check found the carrier is ALREADY CORRECT for one of the two lines and only NEARLY correct for the other. `docs/cli-human-guide.md:27` tells users "`FORCE_COLOR=1` keeps color even when piped", which stays TRUE after this plan (only falsey values change) and needs no edit. `docs/cli-human-guide.md:74` states the precedence as "`NO_COLOR` disables color and is only overridden by `FORCE_COLOR`", which becomes IMPRECISE after this plan: it is overridden only by a FORCING `FORCE_COLOR`, not by any setting of it. `7p3tt8` E-02 already declares `docs/cli-human-guide.md` in its `- Scope-Paths:` and already rewrites this file's color section (its F-02 targets `:67-68`), so the carrier exists and the file is declared; what `7p3tt8` does not yet name is line `:74` specifically. That is recorded here rather than fixed here because this plan does not declare that file and because a two-plan edit to one paragraph is the churn the Set's boundaries exist to avoid. `docs/cli-output-contract.md:33` lists the three controls without stating precedence, so it survives unchanged.

## Open questions

### OQ-01: Should `--no-color` route through the unified `should_color` rather than bypassing it?

- Blocking: no
- Status: open
- Owner: none
- Carrier: yaxr4i
- Resolution or deferral rationale: NOT BLOCKING because this plan's own deliverable is complete without it: unifying three implementations and fixing the falsey-value inversion neither needs nor prevents the flag routing change. Recorded because the measurement that found the three divergent engines also found that `--no-color` does not reach any of them (`cli.py:832` sets `Term(color=False)` directly), which means the top rung of the precedence chain is split across two layers, and `pow5sj` F-06 already notes the same thing. The flag layer is `yaxr4i`'s, which is why the carrier points there rather than at this plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the executed 4x4 grid (`NO_COLOR` unset/`''`/`'0'`/`'1'` x `FORCE_COLOR` unset/`''`/`'0'`/`'1'`) against a TTY and a pipe, and reconcile it CELL BY CELL against the authoritative table under `## Project conventions discovered`; an evidence block that pastes a grid without stating it matches that table fails this item. It must show: `FORCE_COLOR='0'` now falls through (color on a TTY, plain to a pipe) rather than forcing; `NO_COLOR=''` disables; `FORCE_COLOR='1'` still beats `NO_COLOR='1'`. AND IT MUST SHOW THE F-05 CELL EXPLICITLY: `NO_COLOR=1` with `FORCE_COLOR=0` is PLAIN ON A TTY. That one cell is the difference between this item and the naive edit, so an evidence block omitting it does not demonstrate E-01 was done correctly. Paste the source of the single forcing predicate and a `grep` showing BOTH `FORCE_COLOR` read sites call it, proving the two-reading split is structurally closed rather than corrected at one site. Paste `tests/test_term.py:48` `test_force_color_overrides_no_color` PASSING unchanged, since the ruling preserves it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste `runner_shared.should_color`'s post-change source, showing a SINGLE statement delegating to `term.should_color`. Paste `python3 -m pytest tests/test_runner_refork_guard.py tests/test_rununify_run_queue.py -o addopts=""` PASSING, and name the three guards F-06 measured as shape-sensitive (`test_the_owning_module_really_defines_every_tabled_symbol`, `test_the_shared_resolving_names_really_do_resolve_in_runner_shared`, `test_exactly_one_definition_package_wide`), each shown passing. Paste `TERM=dumb` output from a runner command and from `aw attention` showing BOTH plain (they diverge today). Do NOT paste a `grep -c "def should_color" == 1` claim here: after this item the correct count is 2, and V-07 owns the one-definition property in its corrected form (F-08).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste `python3 -m pytest tests/test_runner_shared.py -o addopts=""` PASSING. Paste the `SUPERSEDED_SINCE_MOVE` tuple showing `should_color` added, the justification paragraph written beside `state_root`'s and `_run_git`'s, and the two updated count assertions (`23`->`22`, `2`->`3`). Paste `git diff --stat tests/fixtures/runner_shared_premove_fingerprints.json` showing NO CHANGE, since editing the historical capture instead of declaring the supersession is the failure mode this item exists to prevent.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste `pwatch.py`'s post-change `color_enabled` assignment showing `not args.no_color` STILL PRESENT above the shared call. Paste `FORCE_COLOR=1 aw pwatch ... | cat` showing ANSI bytes (plain today) and a `TERM=dumb` run showing none. Then paste the pty measurement from E-06 proving `aw pwatch --no-color` on a REAL TTY is still plain; a piped `--no-color` run is NOT acceptable evidence here, because F-07 measured that it passes even with the flag deleted.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the new table-driven test's case list and its passing output, showing a named case for every cell of the 4x4 grid on both stream kinds plus the four `TERM` values. Then prove the pins BITE, and prove it against the RIGHT mutation: apply the NAIVE single-site edit F-05 describes (change only the truthiness test at `term.py:103`, leave the presence test at `:100`), paste the suite FAILING with the `NO_COLOR`-set cells named, and restore. A revert of the whole item is the easy mutation and proves less; the naive edit is the one a real executor would plausibly ship, so that is the one the grid must catch.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste both new cases passing. Then prove each BITES independently: revert E-02's `TERM` behavior in a scratch edit and paste the `TERM=dumb` runner case FAILING; separately drop the `not args.no_color` conjunct and paste the pty `pwatch` case FAILING. Restore after each. State plainly that the pre-existing piped `--no-color` tests kept passing under that second mutation (`tests/test_pwatch.py:225`, `:236`), which is the measured gap this item closes.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Paste the guard passing WITH `runner_shared`'s sanctioned wrapper in place, which is what proves it is not simply counting `def`s. Paste `grep -c "def should_color" agent_workflows/*.py` showing the total is 2 and explain which one is the delegation, so the next reader (and `pow5sj`'s executor) is not misled by F-08's trap. Then add a second ORIGINATING `def should_color` in a scratch module, paste the guard FAILING, and remove it. Finally paste the BARE `python3 -m pytest` summary line for the final state, compared against the review baseline `7306 passed, 3 skipped, 2 xfailed`, and list any test updated because it encoded the old divergence with the reason for each.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. RECORDED AT REVIEW because the item count grew from 4 to 7 and a reader should know the growth was decomposition rather than scope creep: no new concern entered the plan. E-02 split into E-02/E-03 because the conversion and the fingerprint exemption are separate deliverables in separate files with separate evidence (F-06); E-02 split again into E-04 because `runner_shared` and `pwatch` need DIFFERENT shapes for different reasons (a sanctioned wrapper versus a preserved flag conjunct) and bundling them is what hid F-07; and E-03 split into E-05/E-06 because a `term.py` unit grid and a pty-based consumer regression are independent test surfaces. Every one of the seven still addresses one concern in one file region and is executable in one focused pass.

This plan MUST NOT execute until a human approves it (`aw set approved z8ddk0 --by-human`). It declares NO dependencies and is depth-0, so `queue_sort_key` places it ahead of `pow5sj`, which declares `executed:z8ddk0`. Its Order of 9 is a filename cluster and is NOT its queue position; the runner sorts by dependency depth first and re-checks each edge at dispatch.

OPEN QUESTIONS: OQ-01 is `- Blocking: no` and carried by `yaxr4i`, so nothing here waits on a ruling. No question in this plan blocks execution.

WHY THIS CHILD EXISTS RATHER THAN A STANDALONE BACKLOG ITEM: it was first filed as backlog `nyz8dt`, on three reasons the maintainer asked me to re-examine, of which two were FALSE (the Set already declares `term.py` and `runner_shared.py` in three children's `Scope-Paths`, and `yaxr4i` does NOT rewrite the engine, it asserts the engine is already correct) and one was unsupported (`pow5sj`'s scope does not exclude behavior changes). The maintainer then ruled to convert it. Recorded because the honest reason for a plan's shape is worth more to a later reader than a tidy one.

SCOPE FENCE: the files this plan may write are those declared in `- Scope-Paths:` (`agent_workflows/term.py`, `agent_workflows/runner_shared.py`, `agent_workflows/pwatch.py`, `tests/test_term.py`, `tests/test_runner_shared.py`, `tests/test_runner_refork_guard.py`, `tests/test_rununify_run_queue.py`, `tests/fixtures/runner_shared_premove_fingerprints.json`, `tests/test_pwatch.py`). An out-of-scope edit is permitted but must then be JUSTIFIED, which `aw ipd finalize` enforces by refusing to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. NOTE THE ONE DECLARED PATH THAT IS EXPECTED TO END UNMODIFIED: `tests/fixtures/runner_shared_premove_fingerprints.json` is declared so the fence is HONEST about the file E-03 must be seen not to have touched, and V-03 requires proving it unchanged; expect to pass a `--scope-ack` for it at finalize, which is the correct outcome rather than a failure. In particular this child must NOT add depth resolution, a 16-color tier, or `aw config` keys (`pow5sj`'s); must NOT add a `--color` flag or touch `cli.py`'s `common` parser (`yaxr4i`'s); must NOT edit any `.spec.md` or `docs/` file (`7p3tt8`'s, per Spec / documentation sync); must NOT touch `render_stream.py`, `attention.py`, or either runner's display code; and must NOT weaken, delete, or rewrite any anti-re-fork assertion or the historical fingerprint capture in order to make a guard green, which is the specific wrong turn F-06 exists to prevent. DO STOP AND REPORT for one genuinely unsafe condition: if `is_pure_delegation` or the `SUPERSEDED_SINCE_MOVE` machinery E-03 and E-07 build on has been renamed or removed, report that rather than authoring a parallel copy of either, since a second notion of "sanctioned delegation" would silently reopen the re-fork hole.

HONESTY RULE (hard MUST): when reporting tests or measurements, paste the ACTUAL command output. Never claim a suite run, a grid cell, a pty measurement, or a guard result you did not run. A `V-*` evidence block must contain real output, not a description of expected output. V-01 and V-05 in particular demand the `NO_COLOR`-set cells explicitly, and V-04 and V-06 demand a REAL pty rather than a pipe, precisely because a plausible-sounding piped round trip was measured to pass while the flag was entirely deleted (F-07).

On completion: append the workflow-history line, set the terminal `Status: executed`, and move this plan to `.aw/records/plans/executed/` via `aw ipd finalize` as a post-gate lifecycle step, never as a checklist item and never as a hand-rolled `git mv`. When a runner owns the turn it performs that finalize itself; a hand-run executor invokes it directly. Commit path-scoped (`git commit -m msg -- <path>`); never `git add -A`; never push.
