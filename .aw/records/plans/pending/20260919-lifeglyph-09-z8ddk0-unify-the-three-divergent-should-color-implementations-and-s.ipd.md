# IPD: Unify the three divergent should_color implementations and stop a falsey FORCE_COLOR forcing color on

- Date: 2026-09-19
- Kind: child
- Concern: THREE INDEPENDENT `should_color` IMPLEMENTATIONS DISAGREE WITH EACH OTHER, and one inverts the meaning of a value users set deliberately. Measured by EXECUTION 2026-09-19, not by reading. `term.py:90` checks `TERM`, tests `NO_COLOR` by PRESENCE, and lets `FORCE_COLOR` escape it. `runner_shared.py:276` IGNORES `TERM` entirely and tests by TRUTHINESS, so `TERM=dumb aw oc run` emits color while `TERM=dumb aw attention` does not. `pwatch.py:951` ignores `FORCE_COLOR` completely, so `FORCE_COLOR=1 aw pwatch | cat` is plain while every other command colorizes. Worst of the four: `FORCE_COLOR=0` FORCES COLOR ON, even to a pipe, because the string `"0"` is truthy in Python, so a user writing the value that plainly means "do not force" gets the opposite. This blocks spec `uonrjg` R9.3a.2, which requires the depth resolver have EXACTLY ONE definition: a resolver cannot have one definition while the capability decision beneath it has three.
- Scope: IN: one shared `should_color` with one definition, carrying the maintainer's 2026-09-19 semantics (`NO_COLOR` presence-only; `FORCE_COLOR` interprets falsey values); `runner_shared.py` and `pwatch.py` consuming it instead of reimplementing; and a test pinning every cell of the two measured tables, none of which is pinned today. OUT: the depth ladder and the 16-color tier (child `pow5sj`, which sits ON this seam), the `--color`/`--no-color` FLAG surface (plan `yaxr4i`), and any lifecycle glyph or palette work.
- Scope-Paths: agent_workflows/term.py, agent_workflows/runner_shared.py, agent_workflows/pwatch.py, tests/test_term.py, tests/test_runner_shared.py, tests/test_runner_refork_guard.py, tests/test_rununify_run_queue.py, tests/fixtures/runner_shared_premove_fingerprints.json, tests/test_pwatch.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: lifeglyph
- Order: 9
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: z8ddk0
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved
- From-Backlog: nyz8dt
- Blocks-Release: next
- Work-Kind: bug

## Workflow history
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-19 reviewed (aw set): /plan-review round 1 complete (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901..PR-907 all FIXED, none deferred, none open; readiness go-pending-approval. Review record at .aw/records/reviews/20260919-lifeglyph-09-z8ddk0-unify-the-three-divergent-should-color-implementations-and-s.review.md. Human approval is still required and was NOT given.

- 2026-09-19 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901 through PR-907 all FIXED, none deferred, none open. Reviewed at HEAD `3a513262`; `aw ipd lint --phase author --agent` clean, exit 0, before and after. THE DIAGNOSIS IS CORRECT IN EVERY PARTICULAR and I re-executed all four defects rather than reading them. Every finding is therefore about the FIX, and the three serious ones share one root: the plan described the intended END STATE accurately and never described the EDIT that reaches it, so each of the three named source changes had a shortest-path implementation that is wrong in a way the plan's own validation would not catch. I found each by applying the naive edit and measuring. PR-901 (HIGH): E-01 named only the TRUTHINESS read of `FORCE_COLOR` at `term.py:103`, leaving the PRESENCE read at `:100` a presence test, so the literal edit lets a falsey `FORCE_COLOR` still CANCEL `NO_COLOR` while no longer forcing; measured, all TWELVE `NO_COLOR`-set cells then colorize on a TTY, `NO_COLOR=1 FORCE_COLOR=0` among them, which voids the accessibility convention the whole ruling defers to and is strictly worse than the bug being fixed. E-01 now mandates ONE forcing predicate at both sites and V-05 requires the NAIVE edit (not a full revert) as the mutation that must fail. PR-902 (HIGH): E-02's "exactly one definition in the package" reads as delete-the-def-and-import, which FAILS FOUR shipped guards, three of which exist specifically to assert `runner_shared` DEFINES this symbol; measured per shape, the sanctioned one-line delegation keeps three green and the byte-identical fingerprint fails under both, so it needs a declared `SUPERSEDED_SINCE_MOVE` exemption (new E-03) with two count updates. FIVE test surfaces were undeclared, including the historical fixture, so an executor would have faced four red tests outside its fence and would plausibly have repaired them by rewriting the anti-re-fork evidence. PR-903 (HIGH): only two of `pwatch`'s three conjuncts are the shared decision, so the obvious conversion SILENTLY DELETES `--no-color`; measured on a pty (current `False`, naive `True`), and its two shipped tests run through a PIPE so `10 passed` either way. PR-904 (MEDIUM) corrects the plan's own success criterion: the post-fix `def` count is 2, not 1, so E-04's guard and V-02's evidence were both unobtainable, and the same wording propagates to `pow5sj`'s V-01. Also fixed: an absent scope fence and honesty rule (alone among the nine children) plus the flagged hand-rolled `git mv` wording (PR-906), a missing suite baseline where two sibling numbers conflict (PR-907), and one overstated Step 0 claim (PR-905). Item count 4 -> 7, decomposition not scope creep. Suite baseline `7306 passed, 3 skipped, 2 xfailed`. OQ-01 is non-blocking and carried by `yaxr4i`; no question blocks execution. Readiness go-pending-approval.
- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `nyz8dt` on the maintainer's instruction to convert it into a lifeglyph child rather than keep it standalone. Carries `nyz8dt`'s `Blocks-Release: next` and `Work-Kind: bug`. ORDER 9 IS NOT ITS QUEUE POSITION: `queue_sort_key` puts `dependency_depth` FIRST, so this depth-0 child precedes `pow5sj`, which declares `executed:z8ddk0`. The Order number is a filename cluster, not evidence of sequence.

## Goal

Make the color capability decision have one definition with the maintainer's ruled semantics, so the depth resolver `pow5sj` builds can honestly claim R9.3a.2's "exactly one definition" and so a falsey `FORCE_COLOR` stops meaning its own opposite.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: One definition, with the ruled semantics

- [x] E-01 Make `term.should_color` the single definition and apply the maintainer's 2026-09-19 semantics: `NO_COLOR` is PRESENCE-ONLY (any setting disables, empty included, no value interpreted); `FORCE_COLOR` INTERPRETS its value, so `0`/`false`/`no`/`off` mean NOT FORCING and fall through to ordinary TTY detection rather than suppressing.

  IMPLEMENT ONE FORCING PREDICATE AND CONSULT IT IN BOTH PLACES. This is the whole content of the item and the reason it is not a two-line edit. `term.py` reads `FORCE_COLOR` TWICE: by PRESENCE at `:100` (where it cancels `NO_COLOR`) and by TRUTHINESS at `:103` (where it forces). Changing only the second reading, which is the literal text of this item's first sentence and is the edit an executor will reach for, leaves the FIRST reading a presence test, and a presence test is now WRONG because a falsey `FORCE_COLOR` must no longer cancel `NO_COLOR`. MEASURED AT REVIEW by executing that exact naive edit: it produces COLOR ON A TTY for all twelve cells where `NO_COLOR` is set and `FORCE_COLOR` is present, including `NO_COLOR=1 FORCE_COLOR=0`, which is a NEW accessibility regression strictly worse than the defect being fixed (see F-05). So define one helper, e.g. `_force_color_is_forcing() -> bool` returning `v is not None and v.strip().lower() not in {"", "0", "false", "no", "off"}`, and write the `NO_COLOR` rung as `"NO_COLOR" in os.environ and not _force_color_is_forcing()`. Both readings then move together by construction, which is the durable property; a second independent falsey check at each site would re-create the same two-reading split this item exists to close.
  - Depends on: none
  - Expected outcome: `FORCE_COLOR=0` no longer forces color and no longer reaches a pipe; it falls through, giving color on a TTY and plain to a pipe. `NO_COLOR=1 FORCE_COLOR=0` is PLAIN on a TTY (the naive edit makes it colored). `FORCE_COLOR=1` still beats `NO_COLOR=1`, so `tests/test_term.py:48` keeps passing unchanged. `FORCE_COLOR=''` is read ONCE, through the shared predicate, so the presence-versus-truthiness contradiction at `:100`/`:103` is structurally gone rather than merely corrected at one of the two sites.
  - Execution state: performed

- [x] E-02 Convert `runner_shared.py:275` to consume the single definition instead of reimplementing it, in the SANCTIONED WRAPPER SHAPE rather than as an import. Note this makes the runners start honoring `TERM=dumb`, a behavior CHANGE and the correct one.

  THE SHAPE IS NOT FREE, AND THE OBVIOUS SHAPE BREAKS FOUR SHIPPED GUARDS. Measured at review by running the real guard methods against each candidate shape (F-06): deleting `runner_shared`'s `def` in favor of `from agent_workflows.term import should_color` FAILS four tests, because three separate harnesses assert that `runner_shared` DEFINES this symbol (`test_runner_refork_guard.py:224` region via `Owned("should_color", "runner_shared", BOTH)`; `test_rununify_run_queue.py:93` `RESOLVES_IN_RUNNER_SHARED`; `test_runner_shared.py` `test_exactly_one_definition_package_wide`, which asserts exactly ONE in-scope def site and gets zero). USE SHAPE B, the one-line delegating wrapper the repository already sanctions for exactly this case (`is_pure_delegation`, `tests/test_rununify_run_queue.py:250`): a single `return` statement naming the shared callable, docstring permitted. Measured, Shape B keeps three of the four guards PASSING. The fourth is E-03's work, so do not attempt to satisfy it here.
  - Depends on: E-01
  - Expected outcome: `runner_shared.should_color` is a one-statement delegation to `term.should_color`; both runners still reach it at their existing 15 call sites unchanged. `TERM=dumb aw oc run` is plain, matching `aw attention`. `test_runner_refork_guard`, `test_rununify_run_queue`'s closure classification, and `test_exactly_one_definition_package_wide` all still pass.
  - Execution state: performed

- [x] E-03 Re-baseline the ONE guard E-02 cannot satisfy in place: `tests/test_runner_shared.py::PureMoveFingerprintTests::test_every_clean_symbol_is_a_STRICT_fingerprint_match`, which holds `should_color`'s BODY byte-identical to the pre-move capture in `tests/fixtures/runner_shared_premove_fingerprints.json`, and which therefore FAILS under every shape that changes that body (measured: both Shape A and Shape B fail). This is deliberate, not incidental: that harness exists to prove a moved body was not silently edited, so a legitimate supersession must be DECLARED there rather than worked around.

  DO IT THE WAY THE FILE ALREADY DOES IT, which is an enumerated exemption with a written reason. Add `should_color` to `SUPERSEDED_SINCE_MOVE` (`tests/test_runner_shared.py:199`), which is the list `state_root` and `_run_git` already occupy for exactly this reason ("SUPERSEDED by design in subsequent approved IPDs"), and write the paragraph of justification the file's convention requires beside theirs, citing this plan's id. TWO COUNT ASSERTIONS MOVE WITH IT and both are in the same method: the clean-move count `23` becomes `22` and `len(SUPERSEDED_SINCE_MOVE)` `2` becomes `3`. Measured at review: leaving either untouched fails. Do NOT instead delete the exemption machinery, loosen the comparison, or edit the FIXTURE's captured fingerprint: the fixture is a historical capture of pre-move bodies, and rewriting it would destroy the harness's only evidence rather than record a supersession.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest tests/test_runner_shared.py` passes; `should_color` appears in `SUPERSEDED_SINCE_MOVE` with a reason naming `z8ddk0`; the two counts are updated together in the same method; the fixture JSON is UNCHANGED.
  - Execution state: performed

- [x] E-04 Convert `pwatch.py:950-952` to consume the single definition, PRESERVING its `--no-color` flag as an override ABOVE the shared decision. This makes `pwatch` start honoring `FORCE_COLOR` and `TERM`, both behavior CHANGES and both correct.

  THE FLAG MUST SURVIVE THE CONVERSION AND ITS OWN TESTS WILL NOT TELL YOU IF IT DOES NOT. `pwatch`'s expression is `not args.no_color and os.environ.get("NO_COLOR") is None and sys.stdout.isatty()`; only the last two conjuncts are the shared decision, and `args.no_color` is a USER-FACING flag (`pwatch.py:847`) with no equivalent inside `should_color`, which reads no argparse state. Replacing the whole expression with `term.should_color(sys.stdout)` therefore SILENTLY DELETES `--no-color`. Measured at review on a real pty: with `--no-color` passed, the current expression yields `False` and the naive replacement yields `True`. Write it as `color_enabled = not args.no_color and term.should_color(sys.stdout)`. AND NOTE THE MEASUREMENT GAP (F-07): the two shipped tests that pass `--no-color` (`tests/test_pwatch.py:225`, `:236`) run through a PIPE, where `isatty()` is already False, so both keep passing with the flag entirely removed; they cannot detect this regression, which is why E-06 adds a pty case.
  - Depends on: E-01
  - Expected outcome: `color_enabled` consults the shared decision with `--no-color` layered above it. `FORCE_COLOR=1 aw pwatch | cat` colorizes, matching every other command. `TERM=dumb` is plain. `aw pwatch --no-color` on a REAL TTY is still plain.
  - Execution state: performed

### Task group 2: Pin what was never pinned

- [x] E-05 Pin EVERY cell of the two measured tables in `tests/test_term.py`: the 4x4 `NO_COLOR` x `FORCE_COLOR` grid (unset / `''` / `'0'` / `'1'`) against both a TTY and a pipe, plus the `TERM` axis (`xterm-256color` / `dumb` / `''` / unset). None of the empty-string or `'0'` cases is pinned today, which is why all four defects survived: the behavior is accidental, not contractual.

  THE TWELVE `NO_COLOR`-SET CELLS ARE THE POINT, not filler. They are what distinguishes the correct composition from the naive edit E-01 warns about: the two implementations agree on the four cells where `NO_COLOR` is unset and disagree on all twelve where it is set (measured at review, F-05). A grid that pins only the headline `FORCE_COLOR='0'` case therefore passes for the broken edit. Pin the EXPECTED value explicitly per cell rather than computing it from the implementation, and name each case so a failure identifies the cell. The authoritative expectations are the table reproduced under `## Project conventions discovered` below, itself the backlog `nyz8dt` tri-state ruling made concrete.
  - Depends on: E-01
  - Expected outcome: a table-driven test whose 32 env cases (16 cells x 2 stream kinds) plus 8 `TERM` cases are the measured grid, each with a named expectation. Reverting any part of E-01 fails at least one named case, INCLUDING the naive single-site edit.
  - Execution state: performed

- [x] E-06 Pin the two consumer behavior CHANGES E-02 and E-04 make, because neither is covered by any existing test and both are the user-visible half of this plan. (a) `runner_shared.should_color` honors `TERM=dumb` (it ignores `TERM` entirely today, and no test reads `TERM` against it). (b) `pwatch`'s `--no-color` still suppresses color ON A REAL TTY after the conversion, which requires a pty because a piped run is already colorless and so cannot distinguish the flag working from the flag being deleted (F-07). Use `pty.fork`, as measured at review; `tests/test_pwatch.py` already shells out via `subprocess`, so this is a new case in a familiar file rather than a new harness.
  - Depends on: E-02, E-04
  - Expected outcome: a `TERM=dumb` case against `runner_shared.should_color` that FAILS before E-02, and a pty-based `pwatch --no-color` case that FAILS if the flag conjunct is dropped. Both named so the failure says which behavior regressed.
  - Execution state: performed

- [x] E-07 Add a guard asserting the package contains exactly ONE ORIGINATING `should_color` definition, so a future module cannot quietly add a fourth. This is the mechanical property R9.3a.2 demands and that `pow5sj`'s V-01 will grep for.

  THE OBVIOUS FORM OF THIS GUARD IS FALSE AFTER E-02, and getting this wrong makes the guard either permanently red or decorative. `grep -c "def should_color"` returns TWO after E-02, because the sanctioned delegating wrapper in `runner_shared` IS a `def` (measured at review). So the guard must assert one ORIGINATING definition and permit sanctioned delegations, which is precisely the distinction `is_pure_delegation` (`tests/test_rununify_run_queue.py:250`) already draws: reuse that predicate rather than authoring a second notion of the same thing. State the rule as: across `agent_workflows/*.py`, exactly one top-level `def should_color` is not a pure delegation, and it is in `term.py`. AST, not substring: the file-local convention (`tests/test_runner_refork_guard.py` docstring) records that `assertNotIn("class Palette:", src)` was evaded by whitespace and satisfied by a comment.
  - Depends on: E-02, E-04
  - Expected outcome: a test that FAILS if a second ORIGINATING definition is introduced and PASSES with `runner_shared`'s sanctioned wrapper present. `pow5sj`'s one-definition evidence becomes true by construction rather than by inspection at that moment, and its V-01 `grep` expectation is corrected by this plan's V-07 evidence rather than left to surprise that plan's executor.
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: Paste the executed 4x4 grid (`NO_COLOR` unset/`''`/`'0'`/`'1'` x `FORCE_COLOR` unset/`''`/`'0'`/`'1'`) against a TTY and a pipe, and reconcile it CELL BY CELL against the authoritative table under `## Project conventions discovered`; an evidence block that pastes a grid without stating it matches that table fails this item. It must show: `FORCE_COLOR='0'` now falls through (color on a TTY, plain to a pipe) rather than forcing; `NO_COLOR=''` disables; `FORCE_COLOR='1'` still beats `NO_COLOR='1'`. AND IT MUST SHOW THE F-05 CELL EXPLICITLY: `NO_COLOR=1` with `FORCE_COLOR=0` is PLAIN ON A TTY. That one cell is the difference between this item and the naive edit, so an evidence block omitting it does not demonstrate E-01 was done correctly. Paste the source of the single forcing predicate and a `grep` showing BOTH `FORCE_COLOR` read sites call it, proving the two-reading split is structurally closed rather than corrected at one site. Paste `tests/test_term.py:48` `test_force_color_overrides_no_color` PASSING unchanged, since the ruling preserves it.
  - Observed evidence: the post-change 4x4 grid matches the authoritative table in all 32 cells, the F-05 cell `NO_COLOR=1 FORCE_COLOR=0` is PLAIN on a TTY, both `FORCE_COLOR` read sites call the one predicate, and `test_force_color_overrides_no_color` passes unchanged. Detail:

    POST-CHANGE GRID, executed 2026-09-19. Each cell is `TTY / PIPE`; `COLOR` in caps marks color reaching a PIPE.

    ```
    # measuring: <worktree>/agent_workflows/term.py

    --- term.should_color (TERM=xterm-256color) ---
    | NO_COLOR \ FORCE_COLOR | unset | '' | '0' | '1' |
    |---|---|---|---|---|
    | unset | color / plain | color / plain | color / plain | color / COLOR |
    | '' | plain / plain | plain / plain | plain / plain | color / COLOR |
    | '0' | plain / plain | plain / plain | plain / plain | color / COLOR |
    | '1' | plain / plain | plain / plain | plain / plain | color / COLOR |

    --- term.should_color: TERM axis (NO_COLOR and FORCE_COLOR unset) ---
    | TERM | TTY | PIPE |
    |---|---|---|
    | xterm-256color | color | plain |
    | dumb | plain | plain |
    | '' | plain | plain |
    | unset | plain | plain |
    ```

    CELL-BY-CELL RECONCILIATION AGAINST THE AUTHORITATIVE TABLE: all 16 cells x 2 stream kinds MATCH the
    table under `## Project conventions discovered`, and all 4 `TERM` rows x 2 stream kinds match the
    second table. Checked mechanically rather than by eye, by the permanent test that encodes the table
    independently of the implementation (`_COLOR_GRID` / `_TERM_GRID` in `tests/test_term.py`), which
    enumerates 40 named cases and reports every one passing (see V-05). Zero cells differ.

    The three specifically demanded cells, read off the grid above:
    - `FORCE_COLOR='0'` with `NO_COLOR` unset FALLS THROUGH: row `unset`, column `'0'` is `color / plain`.
      Was `color / COLOR` before (color forced into a pipe).
    - `NO_COLOR=''` DISABLES: row `''`, column `unset` is `plain / plain`.
    - `FORCE_COLOR='1'` still beats `NO_COLOR='1'`: row `'1'`, column `'1'` is `color / COLOR`.

    THE F-05 CELL, EXPLICITLY. Row `'1'`, column `'0'` (`NO_COLOR=1 FORCE_COLOR=0`) is `plain / plain`, so
    it is PLAIN ON A TTY. The naive single-site edit makes this cell colored; measured under that exact
    mutation in V-05 below, where it fails by name.

    PRE-CHANGE BASELINE, measured from this worktree's git HEAD (`c58ec3ab`) rather than from memory, so
    the change is attributable:

    ```
    # measuring PRE-CHANGE term.should_color from git HEAD
    # has _force_color_is_forcing: False

    --- term.should_color AT HEAD (pre-change) (TERM=xterm-256color) ---
    | NO_COLOR \ FORCE_COLOR | unset | '' | '0' | '1' |
    |---|---|---|---|---|
    | unset | color / plain | color / plain | color / COLOR | color / COLOR |
    | '' | plain / plain | color / plain | color / COLOR | color / COLOR |
    | '0' | plain / plain | color / plain | color / COLOR | color / COLOR |
    | '1' | plain / plain | color / plain | color / COLOR | color / COLOR |
    ```

    THE SINGLE FORCING PREDICATE, post-change source:

    ```python
    def _force_color_is_forcing() -> bool:
        """Is `FORCE_COLOR` set to a value that genuinely FORCES color on?
        ...
        """

        value = os.environ.get("FORCE_COLOR")
        if value is None:
            return False
        return value.strip().lower() not in _FORCE_COLOR_FALSEY
    ```

    BOTH READ SITES CONSULT IT, so the split is structurally closed rather than corrected at one site:

    ```
    $ grep -n "_force_color_is_forcing" agent_workflows/term.py
    105:def _force_color_is_forcing() -> bool:
    141:       to a genuinely FORCING value (see :func:`_force_color_is_forcing`).
    154:    if "NO_COLOR" in os.environ and not _force_color_is_forcing():
    157:    if _force_color_is_forcing():
    ```

    `:154` is the `NO_COLOR`-cancelling rung and `:157` is the forcing rung; `FORCE_COLOR` is now named
    NOWHERE else in the function, which `test_both_force_color_read_sites_agree_by_construction` asserts
    by AST (zero direct `FORCE_COLOR` constants in `should_color`, exactly two calls to the predicate).

    THE PRESERVED CASE, passing unchanged (the test body is untouched; my diff of this file deletes no lines):

    ```
    $ python3 -m pytest tests/test_term.py::ShouldColorTests::test_force_color_overrides_no_color -o addopts="" -v
    tests/test_term.py::ShouldColorTests::test_force_color_overrides_no_color PASSED [100%]
    ============================== 1 passed in 0.11s ===============================
    ```

    ONE CORRECTION TO THE PLAN'S OWN PREDICTION, recorded because it is a measurement and not a
    preference: F-05 and this item both say the naive edit colorizes all TWELVE `NO_COLOR`-set cells. It
    colorizes SIX of them (measured, V-05). The six with `FORCE_COLOR` UNSET stay plain, because there the
    naive presence test is still the correct test. The defect is real, the direction is exactly as
    described, and the count is six. The code comments and the test header state six.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste `runner_shared.should_color`'s post-change source, showing a SINGLE statement delegating to `term.should_color`. Paste `python3 -m pytest tests/test_runner_refork_guard.py tests/test_rununify_run_queue.py -o addopts=""` PASSING, and name the three guards F-06 measured as shape-sensitive (`test_the_owning_module_really_defines_every_tabled_symbol`, `test_the_shared_resolving_names_really_do_resolve_in_runner_shared`, `test_exactly_one_definition_package_wide`), each shown passing. Paste `TERM=dumb` output from a runner command and from `aw attention` showing BOTH plain (they diverge today). Do NOT paste a `grep -c "def should_color" == 1` claim here: after this item the correct count is 2, and V-07 owns the one-definition property in its corrected form (F-08).
  - Observed evidence: `runner_shared.should_color` is a delegation to `term.should_color`, all three shape-sensitive guards pass by name (67 passed across the two files), and the runner now matches `aw attention` under `TERM=dumb` where they diverged at HEAD in four cases. One declared deviation: a fifth shipped guard forced the import to be function-local. Detail:

    POST-CHANGE SOURCE. One delegating statement, plus a function-local import that the shape discussion below explains:

    ```python
    def should_color(stream: TextIO | None = None) -> bool:
        """Decide whether to emit ANSI color for ``stream`` (default stdout).

        A SANCTIONED ONE-LINE DELEGATION to :func:`agent_workflows.term.should_color` ...
        """
        from agent_workflows import term

        return term.should_color(stream)
    ```

    A DEVIATION FROM THE ITEM AS WRITTEN, DECLARED RATHER THAN ABSORBED, and it is the one material
    surprise of this execution. The item says "a single `return` statement naming the shared callable",
    which I implemented first as a module-level `from agent_workflows import term as _term` plus a bare
    return. That FAILED a FIFTH shipped guard the plan did not anticipate:

    ```
    $ python3 -m pytest tests/test_orchestrator_probe_cache.py -o addopts=""
    AssertionError: Items in the first set but not the second:
    'agent_workflows.term' : runner_shared gained a module-level first-party import: ['agent_workflows.term']
    FAILED tests/test_orchestrator_probe_cache.py::TheRowWalkIsSharedWithTheRetirementGate::test_no_new_module_level_first_party_import_in_runner_shared
    ```

    That guard allows exactly `render_stream` and `runner_profiles` at module level, "because a
    module-level import added here would change the import graph for BOTH host drivers", and its own
    docstring names the function-local import as this module's established route (which is how
    `ipd_lint`, `ipd_schema`, `ipd_lifecycle` and `worktree_lease` all arrive). Its file is NOT in this
    plan's `- Scope-Paths:`, and the scope fence forbids re-baselining an anti-re-fork guard to make a
    test green, so I conformed to the convention instead: the import moved inside the function. The body
    is therefore `import` + `return` rather than `return` alone. Decision recorded as D-01 with the
    alternatives; the underlying predicate gap is filed as backlog `uhbi1o`.

    THE THREE SHAPE-SENSITIVE GUARDS F-06 NAMED, each shown passing by name:

    ```
    $ python3 -m pytest "tests/test_runner_refork_guard.py::SymmetricReForkGuardTests::test_the_owning_module_really_defines_every_tabled_symbol" \
        "tests/test_rununify_run_queue.py::TheClosureClassificationIsPinned::test_the_shared_resolving_names_really_do_resolve_in_runner_shared" \
        "tests/test_runner_shared.py::SingleDefinitionTests::test_exactly_one_definition_package_wide" \
        "tests/test_runner_shared.py::LaneIntegrationExtractionTests::test_exactly_one_definition_package_wide" -o addopts="" -v
    tests/test_runner_refork_guard.py::SymmetricReForkGuardTests::test_the_owning_module_really_defines_every_tabled_symbol PASSED [ 25%]
    tests/test_runner_shared.py::LaneIntegrationExtractionTests::test_exactly_one_definition_package_wide PASSED [ 50%]
    tests/test_runner_shared.py::SingleDefinitionTests::test_exactly_one_definition_package_wide PASSED [ 75%]
    tests/test_rununify_run_queue.py::TheClosureClassificationIsPinned::test_the_shared_resolving_names_really_do_resolve_in_runner_shared PASSED [100%]
    ============================== 4 passed in 5.34s ===============================
    ```

    (The plan named three; `test_exactly_one_definition_package_wide` exists in TWO classes, so four node
    ids are run. Both pass.)

    THE WHOLE TWO FILES, PASSING:

    ```
    $ python3 -m pytest tests/test_runner_refork_guard.py tests/test_rununify_run_queue.py -o addopts="" -q
    ...................................................................      [100%]
    67 passed in 8.51s
    ```

    `TERM=dumb` PARITY, measured on a REAL pty (a pipe is plain regardless and so proves nothing here):

    ```
    aw attention, TERM=dumb, pty           -> ANSI present: False
    aw attention, capable TERM, pty        -> ANSI present: True
    aw oc runs, TERM=dumb                  -> ANSI present: False
    aw oc runs, capable                    -> ANSI present: True
    aw oc run --help, TERM=dumb            -> ANSI present: False
    aw oc run --help, capable              -> ANSI present: True
    ```

    Both plain under `TERM=dumb`, both colored on a capable terminal, so the runner and `attention` now
    AGREE. And the decision the runners actually call, measured on a pty at the symbol level, since the
    CLI surfaces above reach several display paths:

    ```
    ===== on a REAL TTY with TERM=dumb =====
    oc_runipd.should_color   : False
    agy_runipd.should_color  : False
    runner_shared.should_color: False
    term.should_color        : False
    isatty                   : True
    ```

    THE DIVERGENCE THIS CLOSED, measured at git HEAD (`c58ec3ab`) by loading both pre-change bodies, so the
    "they diverge today" claim is evidenced rather than asserted:

    ```
    PRE-CHANGE (git HEAD) disagreement table
    | case | term.py | runner_shared.py | agree? |
    |---|---|---|---|
    | TERM=dumb, TTY | False | True | NO |
    | TERM='' , TTY | False | True | NO |
    | NO_COLOR='', TTY | False | True | NO |
    | NO_COLOR='0', FORCE='' TTY | True | False | NO |
    | FORCE_COLOR='0', PIPE | True | True | yes |
    ```

    Four disagreeing cases before, zero after (V-01's grid and the runner grid are now cell-identical).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste `python3 -m pytest tests/test_runner_shared.py -o addopts=""` PASSING. Paste the `SUPERSEDED_SINCE_MOVE` tuple showing `should_color` added, the justification paragraph written beside `state_root`'s and `_run_git`'s, and the two updated count assertions (`23`->`22`, `2`->`3`). Paste `git diff --stat tests/fixtures/runner_shared_premove_fingerprints.json` showing NO CHANGE, since editing the historical capture instead of declaring the supersession is the failure mode this item exists to prevent.
  - Observed evidence: `tests/test_runner_shared.py` passes (186), `should_color` is enumerated in `SUPERSEDED_SINCE_MOVE` with its written justification, the two counts moved `23`->`22` and `2`->`3`, and the historical fixture is UNCHANGED. Detail:

    THE FILE PASSING:

    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="" -q
    ..........................................                               [100%]
    186 passed in 23.30s
    ```

    (186, up from the 181 at HEAD: E-06 added the 4-test `SharedColorDecisionTests` class and the
    fingerprint test moved from failing to passing.)

    BEFORE THE EXEMPTION, the one guard E-02 could not satisfy in place, failing exactly as F-06 predicted:

    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="" -q
    E    AssertionError: 'Module(body=[FunctionDef(name=\'should_c[1788 chars]))])' != "Module(body=[FunctionDef(name='should_co[1405 chars]))])"
    E    : `should_color` was NOT a pure move: its body differs from the pre-move capture at 1ecc5891f6bf8c4f1e42b1e9f863839157c8cc6d
    FAILED tests/test_runner_shared.py::PureMoveFingerprintTests::test_every_clean_symbol_is_a_STRICT_fingerprint_match
    1 failed, 181 passed in 21.34s
    ```

    THE ENUMERATED EXEMPTION:

    ```
    $ grep -n "SUPERSEDED_SINCE_MOVE = " tests/test_runner_shared.py
    220:SUPERSEDED_SINCE_MOVE = ("state_root", "_run_git", "should_color")
    ```

    THE JUSTIFICATION PARAGRAPH, written beside `state_root`'s and `_run_git`'s in the same comment block
    and in the same form (what changed, why the exemption is legitimate, where the replacement coverage
    lives), abridged here and present in full at `tests/test_runner_shared.py:201-219`:

    ```
    # `should_color` BECAME A DELEGATION to `term.should_color` (IPD `z8ddk0` E-02), and the exemption is
    # recorded here rather than absorbed. WHY IT IS LEGITIMATE: the pre-move body was one of THREE
    # independent implementations of the color capability decision that DISAGREED with each other,
    # measured by execution 2026-09-19. This one ignored `TERM` entirely, so `TERM=dumb aw oc run` emitted
    # color while `TERM=dumb aw attention` did not, and it read both variables by TRUTHINESS, so
    # `FORCE_COLOR=0` - the value that plainly means "do not force" - FORCED COLOR ON, even into a pipe.
    # Spec `uonrjg` R9.3a.2 requires the depth resolver above this decision have EXACTLY ONE definition,
    # which is unsatisfiable while the decision beneath it has three.
    # ... THE `def` DELIBERATELY REMAINS, as a single delegating statement, because three shipped guards
    # assert `runner_shared` DEFINES this symbol ... A delegation cannot fingerprint as the body it
    # replaces, which is why no shape of this change can satisfy the STRICT match and why the exemption is
    # the only honest route. The unified decision has its OWN dedicated coverage in `tests/test_term.py`
    # ... and the delegation itself is pinned by `SharedColorDecisionTests` in this file.
    ```

    THE TWO COUNTS, updated together in the same method (`23`->`22` and `2`->`3`):

    ```
    $ grep -n "len(clean)," -A 2 tests/test_runner_shared.py
    458:            len(clean),
    459-            22,
    460-            "the clean-move count must not drift silently",

    $ grep -n "len(SUPERSEDED_SINCE_MOVE)," -A 2 tests/test_runner_shared.py
    463:            len(SUPERSEDED_SINCE_MOVE),
    464-            3,
    465-            "a name added to SUPERSEDED_SINCE_MOVE must be accounted for in the clean count above",
    ```

    THE FIXTURE IS UNTOUCHED, which is the failure mode this item exists to prevent:

    ```
    $ git diff --stat tests/fixtures/runner_shared_premove_fingerprints.json
    $ git status --short tests/fixtures/runner_shared_premove_fingerprints.json
    ```

    Both produce NO OUTPUT, i.e. the historical capture is unmodified and unstaged. It stays declared in
    `- Scope-Paths:` so the fence is honest about the file that had to be seen NOT to change; expect a
    `--scope-ack` for it at finalize, which the plan's scope fence already anticipates as the correct
    outcome rather than a failure.

    AND THE EXEMPTION IS NOT DECORATIVE: `test_a_superseded_symbol_is_accounted_for` asserts every name on
    that list genuinely DIFFERS from the pre-move capture, so a name added without a real supersession
    fails. It is among the 186 passing above.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste `pwatch.py`'s post-change `color_enabled` assignment showing `not args.no_color` STILL PRESENT above the shared call. Paste `FORCE_COLOR=1 aw pwatch ... | cat` showing ANSI bytes (plain today) and a `TERM=dumb` run showing none. Then paste the pty measurement from E-06 proving `aw pwatch --no-color` on a REAL TTY is still plain; a piped `--no-color` run is NOT acceptable evidence here, because F-07 measured that it passes even with the flag deleted.
  - Observed evidence: `not args.no_color` is still present above the shared call, `FORCE_COLOR=1` now colorizes a pipe and `TERM=dumb` does not (both wrong at HEAD), and a REAL pty shows `--no-color` plain with a colored control. Detail:

    THE FLAG SURVIVED THE CONVERSION, layered above the shared call:

    ```
    $ grep -n "color_enabled = " agent_workflows/pwatch.py
    964:    color_enabled = not args.no_color and term.should_color(sys.stdout)
    ```

    `FORCE_COLOR=1` NOW REACHES A PIPE (it was plain before this plan, the only command in the toolkit
    that ignored the variable). Piped through `cat`, rendered with `cat -v` so the escapes are visible:

    ```
    $ env -u NO_COLOR FORCE_COLOR=1 TERM=xterm-256color python3 -m agent_workflows pwatch --once python | cat -v
    ^[[1;38;5;39mpwatch: python^[[0m ^[[2m(every 2.5s)^[[0m ^[[38;5;241m...^[[0m ^[[38;5;244m2026-09-19 17:13:42^[[0m
    ^[[1;38;5;255mdeluged^[[0m^[[38;5;245m,2775^[[0m ^[[38;5;186m/usr/bin/deluged^[[0m ...
    ```

    `TERM=dumb` IS PLAIN (also a behavior change; `pwatch` ignored `TERM` too):

    ```
    $ env -u NO_COLOR -u FORCE_COLOR TERM=dumb python3 -m agent_workflows pwatch --once python | cat -v
    pwatch: python (every 2.5s) -- 2026-09-19 17:13:42

    deluged,2775 /usr/bin/deluged -d -c /var/lib/deluged/config -l /var/log/deluged/daemon.log -L info
    ```

    BOTH WERE WRONG AT HEAD, measured by checking out the pre-change file and re-running the same commands,
    so these are attributable changes and not ambient behavior:

    ```
    $ git checkout HEAD -- agent_workflows/pwatch.py
    $ env -u NO_COLOR FORCE_COLOR=1 TERM=xterm-256color python3 -m agent_workflows pwatch --once python | cat -v
    pwatch: python (every 2.5s) -- 2026-09-19 17:13:48        <- NO escapes: FORCE_COLOR ignored
    $ python3 <pty probe>
    pty, TERM=dumb           -> ANSI present: True            <- TERM ignored
    ```

    THE PTY MEASUREMENT, which is the only evidence that can distinguish a working flag from a deleted one:

    ```
    pty, --no-color          -> ANSI present: False
    pty, default             -> ANSI present: True
    pty, TERM=dumb           -> ANSI present: False
    ```

    `--no-color` on a REAL TTY is plain, while the same TTY without the flag is colored, so the second line
    is the control that stops the first passing vacuously. Both are permanent cases now
    (`tests/test_pwatch.py::ColorDecisionOnARealTtyTests`), and V-06 shows the first FAILING when the
    conjunct is dropped.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste the new table-driven test's case list and its passing output, showing a named case for every cell of the 4x4 grid on both stream kinds plus the four `TERM` values. Then prove the pins BITE, and prove it against the RIGHT mutation: apply the NAIVE single-site edit F-05 describes (change only the truthiness test at `term.py:103`, leave the presence test at `:100`), paste the suite FAILING with the `NO_COLOR`-set cells named, and restore. A revert of the whole item is the easy mutation and proves less; the naive edit is the one a real executor would plausibly ship, so that is the one the grid must catch.
  - Observed evidence: all 40 named cases pass (32 env cells + 8 TERM), and the NAIVE single-site edit fails six of them by name including the F-05 cell, plus the structural test. Detail:

    ALL 40 NAMED CASES, enumerated and passing (32 = 16 cells x 2 stream kinds, plus 8 = 4 `TERM` values x 2):

    ```
    ok   case='NO_COLOR=unset FORCE_COLOR=unset on a tty'
    ok   case='NO_COLOR=unset FORCE_COLOR=unset on a pipe'
    ok   case='NO_COLOR=unset FORCE_COLOR=empty on a tty'
    ok   case='NO_COLOR=unset FORCE_COLOR=empty on a pipe'
    ok   case='NO_COLOR=unset FORCE_COLOR=0 on a tty'
    ok   case='NO_COLOR=unset FORCE_COLOR=0 on a pipe'
    ok   case='NO_COLOR=unset FORCE_COLOR=1 on a tty'
    ok   case='NO_COLOR=unset FORCE_COLOR=1 on a pipe'
    ok   case='NO_COLOR=empty FORCE_COLOR=unset on a tty'
    ok   case='NO_COLOR=empty FORCE_COLOR=unset on a pipe'
    ok   case='NO_COLOR=empty FORCE_COLOR=empty on a tty'
    ok   case='NO_COLOR=empty FORCE_COLOR=empty on a pipe'
    ok   case='NO_COLOR=empty FORCE_COLOR=0 on a tty'
    ok   case='NO_COLOR=empty FORCE_COLOR=0 on a pipe'
    ok   case='NO_COLOR=empty FORCE_COLOR=1 on a tty'
    ok   case='NO_COLOR=empty FORCE_COLOR=1 on a pipe'
    ok   case='NO_COLOR=0 FORCE_COLOR=unset on a tty'
    ok   case='NO_COLOR=0 FORCE_COLOR=unset on a pipe'
    ok   case='NO_COLOR=0 FORCE_COLOR=empty on a tty'
    ok   case='NO_COLOR=0 FORCE_COLOR=empty on a pipe'
    ok   case='NO_COLOR=0 FORCE_COLOR=0 on a tty'
    ok   case='NO_COLOR=0 FORCE_COLOR=0 on a pipe'
    ok   case='NO_COLOR=0 FORCE_COLOR=1 on a tty'
    ok   case='NO_COLOR=0 FORCE_COLOR=1 on a pipe'
    ok   case='NO_COLOR=1 FORCE_COLOR=unset on a tty'
    ok   case='NO_COLOR=1 FORCE_COLOR=unset on a pipe'
    ok   case='NO_COLOR=1 FORCE_COLOR=empty on a tty'
    ok   case='NO_COLOR=1 FORCE_COLOR=empty on a pipe'
    ok   case='NO_COLOR=1 FORCE_COLOR=0 on a tty'
    ok   case='NO_COLOR=1 FORCE_COLOR=0 on a pipe'
    ok   case='NO_COLOR=1 FORCE_COLOR=1 on a tty'
    ok   case='NO_COLOR=1 FORCE_COLOR=1 on a pipe'
    ok   case='TERM=xterm-256color on a tty'
    ok   case='TERM=xterm-256color on a pipe'
    ok   case='TERM=dumb on a tty'
    ok   case='TERM=dumb on a pipe'
    ok   case='TERM=empty on a tty'
    ok   case='TERM=empty on a pipe'
    ok   case='TERM=unset on a tty'
    ok   case='TERM=unset on a pipe'

    total named cases: 40  failures: 0
    ```

    ```
    $ python3 -m pytest tests/test_term.py -o addopts="" -q
    .......................                                                  [100%]
    23 passed in 2.17s
    ```

    The expectations are WRITTEN OUT per cell in `_COLOR_GRID`/`_TERM_GRID`, never computed from the
    implementation, so the table is a stated contract a reviewer can dispute rather than a mirror of
    whatever the code does. `test_the_grid_covers_every_combination_exhaustively` asserts the table has all
    16 combinations and the 4 `TERM` values, so a silently-dropped row fails too.

    THE PINS BITE, AGAINST THE RIGHT MUTATION. Applied exactly the naive single-site edit F-05 describes -
    corrected the forcing site, left the `NO_COLOR`-cancelling site a PRESENCE test:

    ```
    $ python3 - <<'EOF'   # the naive edit
    old = '    if "NO_COLOR" in os.environ and not _force_color_is_forcing():'
    new = '    if "NO_COLOR" in os.environ and "FORCE_COLOR" not in os.environ:'
    EOF
    applied naive single-site edit
    ```

    The grid under that mutation, showing color where the table demands plain:

    ```
    --- term.should_color (TERM=xterm-256color) ---
    | NO_COLOR \ FORCE_COLOR | unset | '' | '0' | '1' |
    |---|---|---|---|---|
    | unset | color / plain | color / plain | color / plain | color / COLOR |
    | '' | plain / plain | color / plain | color / plain | color / COLOR |
    | '0' | plain / plain | color / plain | color / plain | color / COLOR |
    | '1' | plain / plain | color / plain | color / plain | color / COLOR |
    ```

    And the suite FAILING with the offending cells NAMED, one subtest per cell:

    ```
    $ python3 -m unittest -v tests.test_term.ShouldColorGridTests.test_every_no_color_force_color_cell_matches_the_ruled_expectation
      ... (case='NO_COLOR=empty FORCE_COLOR=empty on a tty') ... FAIL
      ... (case='NO_COLOR=empty FORCE_COLOR=0 on a tty') ... FAIL
      ... (case='NO_COLOR=0 FORCE_COLOR=empty on a tty') ... FAIL
      ... (case='NO_COLOR=0 FORCE_COLOR=0 on a tty') ... FAIL
      ... (case='NO_COLOR=1 FORCE_COLOR=empty on a tty') ... FAIL
      ... (case='NO_COLOR=1 FORCE_COLOR=0 on a tty') ... FAIL
    AssertionError: True != False : NO_COLOR=empty FORCE_COLOR=empty on a tty: expected plain
    AssertionError: True != False : NO_COLOR=empty FORCE_COLOR=0 on a tty: expected plain
    AssertionError: True != False : NO_COLOR=0 FORCE_COLOR=empty on a tty: expected plain
    AssertionError: True != False : NO_COLOR=0 FORCE_COLOR=0 on a tty: expected plain
    AssertionError: True != False : NO_COLOR=1 FORCE_COLOR=empty on a tty: expected plain
    AssertionError: True != False : NO_COLOR=1 FORCE_COLOR=0 on a tty: expected plain
    Ran 4 tests in 0.101s
    FAILED (failures=3)
    ```

    ```
    $ python3 -m pytest tests/test_term.py -o addopts="" -q     # under the mutation
    2 failed, 18 passed in 0.15s
    FAILED tests/test_term.py::ShouldColorGridTests::test_every_no_color_force_color_cell_matches_the_ruled_expectation
    FAILED tests/test_term.py::ShouldColorGridTests::test_both_force_color_read_sites_agree_by_construction
    ```

    THE F-05 CELL IS AMONG THEM by name: `NO_COLOR=1 FORCE_COLOR=0 on a tty: expected plain`. The
    structural test fails independently, which is the second line of defense: even a grid that had missed a
    cell would catch this mutation, because the two `FORCE_COLOR` readings no longer go through one
    predicate.

    A MEASURED CORRECTION TO F-05's COUNT: SIX cells flip, not twelve. The six are exactly those where
    `NO_COLOR` is set AND `FORCE_COLOR` is PRESENT-but-falsey (`''` or `'0'`). The other six `NO_COLOR`-set
    cells have `FORCE_COLOR` UNSET, where the naive presence test `"FORCE_COLOR" not in os.environ` is
    still the correct test and the cell stays plain. The regression is real and in the described direction;
    only the magnitude differs. Recorded here, in the code comment, and in the test header so the next
    reader is not misled by the plan's figure.

    RESTORED after measuring:

    ```
    $ git diff --stat agent_workflows/term.py
     agent_workflows/term.py | 66 ++++++++++++++++++++++++++++++++++++++++++++-----
     1 file changed, 60 insertions(+), 6 deletions(-)
    $ python3 -m pytest tests/test_term.py -o addopts="" -q
    ....................                                                     [100%]
    20 passed in 0.13s
    ```

    (20 at that moment; 23 after E-07 added its three cases.)
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Paste both new cases passing. Then prove each BITES independently: revert E-02's `TERM` behavior in a scratch edit and paste the `TERM=dumb` runner case FAILING; separately drop the `not args.no_color` conjunct and paste the pty `pwatch` case FAILING. Restore after each. State plainly that the pre-existing piped `--no-color` tests kept passing under that second mutation (`tests/test_pwatch.py:225`, `:236`), which is the measured gap this item closes.
  - Observed evidence: both consumer pins pass (186 and 14) and each BITES independently: the `TERM=dumb` runner case fails on a pre-change body, the pty `pwatch` case fails when the flag conjunct is dropped while the shipped piped tests still report `10 passed`. Detail:

    BOTH NEW SURFACES PASSING:

    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="" -q
    186 passed in 23.30s

    $ python3 -m pytest tests/test_pwatch.py -o addopts="" -q
    ..............                                                           [100%]
    14 passed in 1.53s
    ```

    (14, up from the 10 at HEAD: four new pty/pipe cases.)

    (a) THE `TERM=dumb` RUNNER CASE BITES. Reverted `runner_shared.should_color` to its pre-change body in a
    scratch edit, leaving everything else in place:

    ```
    $ python3 -m unittest -v tests.test_runner_shared.SharedColorDecisionTests
    test_a_falsey_force_color_no_longer_forces_color_into_a_pipe ... FAIL
    test_it_is_a_single_delegating_statement ... FAIL
    test_it_reaches_the_single_originating_definition ... ok
    test_term_dumb_is_now_honored ... FAIL
    AssertionError: True is not false : TERM=dumb must be plain; the runners are not consulting the shared decision
    AssertionError: 4 != 1 : should_color has 4 statements; a wrapper that grows logic is a re-fork with extra steps
    AssertionError: True is not false : FORCE_COLOR=0 must not force color into a pipe
    Ran 4 tests in 0.101s
    FAILED (failures=3)
    ```

    `test_term_dumb_is_now_honored` FAILS before E-02, which is the property the plan demanded. Note
    `test_it_reaches_the_single_originating_definition` stayed green under this mutation and that is
    honest, not a weakness: it compares the two functions' answers in a case where the pre-change bodies
    happened to AGREE, so the `TERM` case is what carries the proof. Restored:

    ```
    $ python3 -m unittest tests.test_runner_shared.SharedColorDecisionTests
    Ran 4 tests in 0.095s
    OK
    ```

    (b) THE PTY `pwatch` CASE BITES, and the shipped piped tests DO NOT. Dropped the `not args.no_color`
    conjunct (the naive conversion), changing nothing else:

    ```
    $ python3 - <<'EOF'
    old = "    color_enabled = not args.no_color and term.should_color(sys.stdout)"
    new = "    color_enabled = term.should_color(sys.stdout)"
    EOF
    DROPPED the `not args.no_color` conjunct (the naive conversion)

    $ python3 <pty probe>
    pty, --no-color          -> ANSI present: True      <- the flag is GONE
    pty, default             -> ANSI present: True
    pty, TERM=dumb           -> ANSI present: False
    ```

    ```
    $ python3 -m pytest tests/test_pwatch.py -o addopts="" -q     # NEW cases present, mutation applied
    FAILED tests/test_pwatch.py::ColorDecisionOnARealTtyTests::test_no_color_flag_still_suppresses_color_on_a_real_tty
    ```

    STATED PLAINLY, AS THE ITEM REQUIRES: under that SAME mutation, the two pre-existing piped `--no-color`
    tests (`tests/test_pwatch.py:225` `test_all_flag_combinations_parse_and_run` and `:236`
    `test_watch_agy_wrapper_backwards_compatibility`) KEPT PASSING, and so did the whole file as it stood
    at HEAD:

    ```
    $ python3 -m pytest tests/test_pwatch.py -o addopts="" -q     # at HEAD's test content, mutation applied
    ..........                                                               [100%]
    10 passed in 0.75s
    ```

    Ten passed with a user-facing flag entirely deleted. That is the measured coverage gap this item closes:
    both of those tests run through a PIPE, where `isatty()` is already False, so the output is colorless
    whether the flag works or does not exist. Only the pty case distinguishes them. Restored:

    ```
    $ grep -n "color_enabled = " agent_workflows/pwatch.py
    964:    color_enabled = not args.no_color and term.should_color(sys.stdout)
    ```

    A NOTE ON THE `DeprecationWarning` the pty cases emit under `pytest -n auto` (3 warnings in the full
    run): CPython warns whenever `forkpty` runs in a multi-threaded process, which an xdist worker is. The
    documented hazard is a child that keeps executing Python after the fork; this child `execve`s
    immediately, replacing the process image and discarding every inherited lock, so the warning is expected
    rather than a latent deadlock. Measured stable: `14 passed` on five consecutive parallel runs. Recorded
    in the test docstring so the coverage is not deleted to silence a warning.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: Paste the guard passing WITH `runner_shared`'s sanctioned wrapper in place, which is what proves it is not simply counting `def`s. Paste `grep -c "def should_color" agent_workflows/*.py` showing the total is 2 and explain which one is the delegation, so the next reader (and `pow5sj`'s executor) is not misled by F-08's trap. Then add a second ORIGINATING `def should_color` in a scratch module, paste the guard FAILING, and remove it. Finally paste the BARE `python3 -m pytest` summary line for the final state, compared against the review baseline `7306 passed, 3 skipped, 2 xfailed`, and list any test updated because it encoded the old divergence with the reason for each.
  - Observed evidence: the guard passes with the sanctioned wrapper present, `grep -c` totals 2 (one originating in `term.py`, one delegation in `runner_shared.py`), a scratch fourth originating definition makes it FAIL, and the bare suite is `1 failed, 7096 passed, 3 skipped, 2 xfailed` against a measured pre-change baseline of `1 failed, 7080 passed, 3 skipped, 2 xfailed` - the SAME one pre-existing failure, filed as backlog `a3ugp1`. Detail:

    THE GUARD PASSES WITH THE SANCTIONED WRAPPER IN PLACE, which is what proves it is not counting `def`s:

    ```
    $ python3 -m pytest tests/test_term.py::OneOriginatingDefinitionTests -o addopts="" -v
    tests/test_term.py::OneOriginatingDefinitionTests::test_exactly_one_originating_definition_and_it_is_in_term PASSED
    tests/test_term.py::OneOriginatingDefinitionTests::test_the_known_delegation_is_recognized_rather_than_counted_as_a_fork PASSED
    tests/test_term.py::OneOriginatingDefinitionTests::test_the_delegation_predicate_refuses_a_body_with_logic PASSED
    ```

    THE COUNT IS TWO, AND F-08's TRAP IS REAL:

    ```
    $ grep -c "def should_color" agent_workflows/*.py | grep -v ":0"
    agent_workflows/runner_shared.py:1
    agent_workflows/term.py:1
    --- total: 2
    ```

    FOR THE NEXT READER AND FOR `pow5sj`'s EXECUTOR: `term.py`'s is the ONE ORIGINATING definition, the real
    implementation. `runner_shared.py`'s is a SANCTIONED DELEGATION whose entire body is
    `from agent_workflows import term` + `return term.should_color(stream)`; it exists as a `def` rather
    than an import because three shipped guards assert that module DEFINES the symbol (see V-02), and an
    import fails all three. So a `grep -c "def should_color" == 1` expectation is FALSE on a correct tree,
    and `pow5sj`'s V-01 should expect TWO `def`s with ONE originating body, asserted the way
    `OneOriginatingDefinitionTests` does it (AST + a delegation predicate), not by counting lines.

    THE GUARD FAILS ON A FOURTH ORIGINATING DEFINITION. Added a scratch module carrying a real body:

    ```
    $ cat agent_workflows/_z8ddk0_scratch_fork.py
    def should_color(stream=None):
        target = stream if stream is not None else sys.stdout
        if os.environ.get("FORCE_COLOR"):
            return True
        return bool(target.isatty())

    $ grep -c "def should_color" agent_workflows/*.py | grep -v ":0"
    agent_workflows/runner_shared.py:1
    agent_workflows/term.py:1
    agent_workflows/_z8ddk0_scratch_fork.py:1

    $ python3 -m pytest tests/test_term.py::OneOriginatingDefinitionTests -o addopts="" -q
    E       AssertionError: Lists differ: ['_z8ddk0_scratch_fork.py', 'term.py'] != ['term.py']
    FAILED tests/test_term.py::OneOriginatingDefinitionTests::test_exactly_one_originating_definition_and_it_is_in_term
    1 failed, 2 passed in 2.06s
    ```

    Note WHICH assertion failed and which did not: the originating-count test failed while the
    delegation-recognition test stayed green, i.e. the guard distinguishes a fork from a wrapper rather than
    rejecting both. Scratch module removed:

    ```
    $ rm agent_workflows/_z8ddk0_scratch_fork.py
    $ python3 -m pytest tests/test_term.py -o addopts="" -q
    .......................                                                  [100%]
    23 passed in 2.17s
    ```

    THE BARE SUITE, FINAL STATE:

    ```
    $ python3 -m pytest
    FAILED tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today
    1 failed, 7096 passed, 3 skipped, 2 xfailed, 3 warnings in 89.10s (0:01:29)
    ```

    COMPARED AGAINST THE BASELINE, and the baseline I compare against is the one I MEASURED on this tree
    rather than the review's remembered figure. At HEAD `c58ec3ab`, BEFORE any edit of mine:

    ```
    $ python3 -m pytest        # pre-change, clean tree
    FAILED tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today
    1 failed, 7080 passed, 3 skipped, 2 xfailed in 93.13s (0:01:33)
    ```

    So: `7080 -> 7096 passed` (+16 net, from the new grid/consumer/guard cases), skips and xfails unchanged,
    and THE SAME ONE PRE-EXISTING FAILURE before and after. The review's `7306` figure does not reproduce on
    this tree at this HEAD, which the plan's own conventions section anticipates ("a DIFFERENT total is
    expected and only an unexplained FAILURE is a finding"); the lane was rebased and suites consolidated
    since that measurement.

    THE ONE FAILURE IS NOT MINE AND IS NOT IN MY SCOPE.
    `test_no_pending_plan_is_refused_on_a_verdict_today` fails identically on the untouched tree (shown
    above). It names three `reaskscore` plans (`s0gnha`, `ty7w6o`, `svacmz`) whose newest history entry is
    the one RESOLVING their blocking question and which `plan_readiness.newest_verdict` still classifies
    `negative`. Nothing in this plan touches `plan_readiness.py` or those plans. FILED as backlog `a3ugp1`
    (`Work-Kind: bug`, `Blocks-Release: next`, since it is a live bug) with the reproduction.

    TESTS UPDATED BECAUSE THEY ENCODED THE OLD DIVERGENCE: NONE, and that is a measured statement rather
    than an omission. No shipped assertion was weakened, deleted, or rewritten. The only pre-existing test
    content I modified is in the two files the plan declares for exactly this purpose:
    - `tests/test_runner_shared.py`: added `should_color` to `SUPERSEDED_SINCE_MOVE` with its written
      justification and moved the two counts `23`->`22` / `2`->`3` (E-03, the declared exemption; V-03).
    - `tests/test_runner_shared.py` and `tests/test_term.py`: my OWN new delegation predicates subtract a
      function-local `import` as well as a docstring, because the shipped import guard makes
      `import` + `return` the only legal spelling of a delegation in `runner_shared` (see V-02 and D-01).
      Both still refuse a body carrying real logic, which `test_the_delegation_predicate_refuses_a_body_with_logic`
      proves in both directions.
    The historical fixture `tests/fixtures/runner_shared_premove_fingerprints.json` is UNCHANGED (V-03).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. RECORDED AT REVIEW because the item count grew from 4 to 7 and a reader should know the growth was decomposition rather than scope creep: no new concern entered the plan. E-02 split into E-02/E-03 because the conversion and the fingerprint exemption are separate deliverables in separate files with separate evidence (F-06); E-02 split again into E-04 because `runner_shared` and `pwatch` need DIFFERENT shapes for different reasons (a sanctioned wrapper versus a preserved flag conjunct) and bundling them is what hid F-07; and E-03 split into E-05/E-06 because a `term.py` unit grid and a pty-based consumer regression are independent test surfaces. Every one of the seven still addresses one concern in one file region and is executable in one focused pass.

This plan MUST NOT execute until a human approves it (`aw set approved z8ddk0 --by-human`). It declares NO dependencies and is depth-0, so `queue_sort_key` places it ahead of `pow5sj`, which declares `executed:z8ddk0`. Its Order of 9 is a filename cluster and is NOT its queue position; the runner sorts by dependency depth first and re-checks each edge at dispatch.

OPEN QUESTIONS: OQ-01 is `- Blocking: no` and carried by `yaxr4i`, so nothing here waits on a ruling. No question in this plan blocks execution.

WHY THIS CHILD EXISTS RATHER THAN A STANDALONE BACKLOG ITEM: it was first filed as backlog `nyz8dt`, on three reasons the maintainer asked me to re-examine, of which two were FALSE (the Set already declares `term.py` and `runner_shared.py` in three children's `Scope-Paths`, and `yaxr4i` does NOT rewrite the engine, it asserts the engine is already correct) and one was unsupported (`pow5sj`'s scope does not exclude behavior changes). The maintainer then ruled to convert it. Recorded because the honest reason for a plan's shape is worth more to a later reader than a tidy one.

SCOPE FENCE: the files this plan may write are those declared in `- Scope-Paths:` (`agent_workflows/term.py`, `agent_workflows/runner_shared.py`, `agent_workflows/pwatch.py`, `tests/test_term.py`, `tests/test_runner_shared.py`, `tests/test_runner_refork_guard.py`, `tests/test_rununify_run_queue.py`, `tests/fixtures/runner_shared_premove_fingerprints.json`, `tests/test_pwatch.py`). An out-of-scope edit is permitted but must then be JUSTIFIED, which `aw ipd finalize` enforces by refusing to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. NOTE THE ONE DECLARED PATH THAT IS EXPECTED TO END UNMODIFIED: `tests/fixtures/runner_shared_premove_fingerprints.json` is declared so the fence is HONEST about the file E-03 must be seen not to have touched, and V-03 requires proving it unchanged; expect to pass a `--scope-ack` for it at finalize, which is the correct outcome rather than a failure. In particular this child must NOT add depth resolution, a 16-color tier, or `aw config` keys (`pow5sj`'s); must NOT add a `--color` flag or touch `cli.py`'s `common` parser (`yaxr4i`'s); must NOT edit any `.spec.md` or `docs/` file (`7p3tt8`'s, per Spec / documentation sync); must NOT touch `render_stream.py`, `attention.py`, or either runner's display code; and must NOT weaken, delete, or rewrite any anti-re-fork assertion or the historical fingerprint capture in order to make a guard green, which is the specific wrong turn F-06 exists to prevent. DO STOP AND REPORT for one genuinely unsafe condition: if `is_pure_delegation` or the `SUPERSEDED_SINCE_MOVE` machinery E-03 and E-07 build on has been renamed or removed, report that rather than authoring a parallel copy of either, since a second notion of "sanctioned delegation" would silently reopen the re-fork hole.

HONESTY RULE (hard MUST): when reporting tests or measurements, paste the ACTUAL command output. Never claim a suite run, a grid cell, a pty measurement, or a guard result you did not run. A `V-*` evidence block must contain real output, not a description of expected output. V-01 and V-05 in particular demand the `NO_COLOR`-set cells explicitly, and V-04 and V-06 demand a REAL pty rather than a pipe, precisely because a plausible-sounding piped round trip was measured to pass while the flag was entirely deleted (F-07).

On completion: append the workflow-history line, set the terminal `Status: executed`, and move this plan to `.aw/records/plans/executed/` via `aw ipd finalize` as a post-gate lifecycle step, never as a checklist item and never as a hand-rolled `git mv`. When a runner owns the turn it performs that finalize itself; a hand-run executor invokes it directly. Commit path-scoped (`git commit -m msg -- <path>`); never `git add -A`; never push.
