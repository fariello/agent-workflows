# IPD: delete the already-extracted re-forks and make the anti-re-fork guards symmetric

- Date: 2026-09-03
- Kind: child
- Concern: Five symbols are DEFINED inside the runner modules even though a non-runner module already owns an AST-identical definition, so a fix to the owner silently does not reach the runner. This is not hypothetical: it is exactly how `Heartbeat` drifted (`stallfp-01`/`kaga7s`), and the reason it went unnoticed is that the anti-re-fork guard was written for ONE runner only. `tests/test_render_stream.py:539` (`test_oc_runipd_source_has_no_inline_definitions`) asserts ten render-layer names are absent from `oc_runipd`, and NOTHING makes the same assertion about `agy_runipd`; its only agy-side guard (`:554`) covers `Heartbeat` alone. So agy still carries `Palette` (`agy_runipd.py:262`), `_strip_ansi` (`:284`) and `_one_line` (`:288`), all three AST-identical to `render_stream`'s, and BOTH runners carry `_read_id`/`_read_status` (`oc_runipd.py:2193`/`:2198`, `agy_runipd.py:1362`/`:1367`) AST-identical to `selectors.py`'s. Measured at HEAD `c8bb11ae` by research `tvnq50` (E-01 of orchestrator `5e4sb6`).
- Scope: Delete those five re-forked definitions and import them from their owning modules instead, then make the guard SYMMETRIC so a re-fork in either runner fails a test. This is the Set's cheapest and most clearly-correct slice: every deletion is provably behavior-neutral because the replacement definition is AST-identical, verified per symbol rather than assumed. Excludes extracting the class (a) common symbols (that is child 02), excludes reconciling any diverged symbol (deferred behind `lanectn` and the E-02 characterization baseline), excludes changing `render_stream` or `selectors` themselves, and excludes `Heartbeat`, which is ALREADY FIXED (`agy_runipd.py:43` imports it) so this plan must not "re-fix" it.
- Scope-Paths: agent_workflows/agy_runipd.py, agent_workflows/oc_runipd.py, tests/test_render_stream.py, tests/test_runner_refork_guard.py
- Item-Dependencies: none
- Status: to-review
- Set: rununify
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 2r306y
- Blocks-Release: next
- From-Spec: none

## Workflow history

- 2026-09-03 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored FROM E-01's inventory (research `tvnq50`), as orchestrator `5e4sb6`'s SECOND GATE requires ("the children do not exist and must be authored FROM E-01's inventory, not before it. A reviewer should refuse any child plan whose scope was written without the measurement behind it"). RE-SCOPED against the orchestrator's own child table, which is now stale in two ways: it names FOUR re-forks (`Palette`/`_one_line`/`_strip_ansi`/`Heartbeat`), but `Heartbeat` was fixed while the orchestrator sat, and the repo-wide sweep found TWO the table never named (`_read_id`, `_read_status`, owned by `selectors.py`, re-forked in BOTH runners rather than only agy). So the real list is five, and one of the two new ones makes this plan touch `oc_runipd` as well, which the table assumed it would not. Authored review-ready, not draft.
- 2026-09-03 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make each of these five symbols have exactly ONE definition in the package, and make the guard that enforces it cover BOTH runners, so the `Heartbeat` failure mode cannot recur silently in either direction.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the guard is missing before relying on it

- [ ] E-01 Write the SYMMETRIC anti-re-fork guard FIRST, in a new `tests/test_runner_refork_guard.py`, and prove it FAILS at current HEAD. It must assert, for BOTH `oc_runipd` and `agy_runipd` and for every symbol in a declared table, that (a) the runner's source does NOT contain a top-level definition of that symbol, and (b) the runner's attribute IS the owning module's object (`assertIs`), which is the check that catches a copy that is textually different but semantically stale. Drive it from a DATA table of `(symbol, owning module)` pairs, not from repeated hand-written assertions, because the existing one-sided guard's ten hand-written `assertNotIn` lines are precisely why adding a symbol did not extend the guarantee. Use AST parsing to find top-level definitions, NOT substring matching: `assertNotIn("class Palette:", src)` also matches a comment or a docstring and misses `class Palette (object):`.
  - Depends on: none
  - Expected outcome: a new test that FAILS at HEAD naming all five re-forks (3 agy-side, 2 in both runners), and that would also fail if `Heartbeat` regressed. Paste the failure.
  - Execution state: pending

### Task group 2: delete the re-forks

- [ ] E-02 Delete the three render-layer re-forks from `agy_runipd.py` (`Palette` at `:262`, `_strip_ansi` at `:284`, `_one_line` at `:288`) and import them from `render_stream` instead. The import already exists at `agy_runipd.py:45` (`from agent_workflows.render_stream import (...)`), so ADD the three names to it rather than adding a second import statement. Follow the shape `oc_runipd` already uses (`oc_runipd.py:64-102`), including its re-export comment convention, since `Palette` is referenced 11 times in agy and 14 in oc and 6 test files reference it, so the name must stay reachable as `agy_runipd.Palette`.
  - Depends on: E-01
  - Expected outcome: `agy_runipd` defines none of the three; `agy_runipd.Palette is render_stream.Palette` is True; the 11 agy call sites are unchanged; E-01's guard now passes for those three.
  - Execution state: pending

- [ ] E-03 Delete `_read_id` and `_read_status` from BOTH runners (`oc_runipd.py:2193`/`:2198`, `agy_runipd.py:1362`/`:1367`) and import them from `selectors`. NOTE THE HAZARD, found at authoring: both names are PRIVATE by convention (leading underscore) and `selectors.py` declares no `__all__` at all, so importing them is legal but reaches into another module's private surface. Decide ONE of two ways and record which: (a) import the private names directly, accepting the coupling, which is what the runners already do implicitly by copying them; or (b) have `selectors` expose a public alias and import that. Prefer (b) if it costs one line, because a private-name import across modules is the kind of coupling a later reader deletes without knowing who depended on it. Do NOT change `selectors`' behavior either way.
  - Depends on: E-01
  - Expected outcome: neither runner defines either symbol; both resolve to `selectors`' definition by `assertIs`; the 2 oc and 2-3 agy call sites per symbol are unchanged; the chosen option (a) or (b) is stated in the plan's history.
  - Execution state: pending

### Task group 3: retire the one-sided guard in favour of the symmetric one

- [ ] E-04 Fold the existing one-sided guard into the symmetric one and DELETE the superseded assertions rather than leaving both. `tests/test_render_stream.py:539` (`test_oc_runipd_source_has_no_inline_definitions`) and `:554` (`test_agy_runipd_has_no_inline_heartbeat_copy`) are the one-sided pair; their ten oc-side names and the agy-side `Heartbeat` name must all appear in E-01's data table first, so the guarantee STRICTLY GROWS and nothing is silently dropped. Keep `test_heartbeat_is_the_same_object_in_both_drivers` (`:561`) and `test_exactly_one_heartbeat_definition_in_the_package` (`:565`): the first is already symmetric and the second is a repo-wide check this plan does not replace.
  - Depends on: E-02, E-03
  - Expected outcome: the two one-sided tests are gone, every name they asserted is in the symmetric table, and the coverage difference is stated explicitly (which names are newly guarded, which merely moved).
  - Execution state: pending

- [ ] E-05 Prove the symmetric guard is load-bearing rather than decorative, by SABOTAGE in BOTH directions. Re-insert a copy of one symbol into `oc_runipd`, confirm the guard fails, revert; then do the same in `agy_runipd`, confirm it fails, revert. A guard that has only been observed passing is not evidence, and the one-sided direction is exactly what let `Heartbeat` drift, so the agy direction specifically must be demonstrated.
  - Depends on: E-04
  - Expected outcome: two pasted failures, one per runner, each naming the re-inserted symbol, plus a clean run after both reverts and `git status` showing no residue.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The shared-render precedent is `oc_runipd.py:64-102`: import the names from `render_stream` and re-export them, with a comment recording why (`# Re-exported from render_stream for backward-compatible access via ``oc_runipd``.`). Follow it; do not invent a second pattern.
- `agy_runipd.py:43` already imports `Heartbeat` from `render_stream` with an explanatory comment at `:34` recording that the module "silently did not reach `aw agy run`". That comment is the historical record of this exact defect class and should not be deleted.
- Guards in this repo are expected to be sabotage-verified. `tests/test_render_stream.py:565` already checks "exactly one definition in the package" by walking the package rather than by grep, which is the standard this plan's E-01 follows.
- The orchestrator's hard constraint: a child must land in BOTH runners or neither, and every guard it adds must assert over BOTH runners.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | The guard is ONE-SIDED, and that is the root cause rather than the re-forks themselves. Ten render-layer names are asserted absent from `oc_runipd`; the agy side checks only `Heartbeat`. | `tests/test_render_stream.py:539-552` (oc, ten `assertNotIn`), `:554-560` (agy, `Heartbeat` only) |
| F-2 | THREE render re-forks remain in agy, all AST-identical to the owner, so deleting them cannot change behavior. | `agy_runipd.py:262` `Palette`, `:284` `_strip_ansi`, `:288` `_one_line`; AST-identical to `render_stream`'s, verified per symbol |
| F-3 | TWO re-forks the orchestrator's child table never named, and they sit in BOTH runners, not just agy. This is why this plan's Scope-Paths include `oc_runipd.py`, which the table assumed it would not touch. | `oc_runipd.py:2193`/`:2198` and `agy_runipd.py:1362`/`:1367`, both AST-identical to `selectors.py`'s `_read_id`/`_read_status` |
| F-4 | `Heartbeat` is ALREADY FIXED, so the orchestrator's child table is stale and a literal execution of it would be a no-op plus confusion. | `agy_runipd.py:43`: `from agent_workflows.render_stream import Heartbeat as Heartbeat` |
| F-5 | The names must stay REACHABLE as runner attributes after the move; this is not a pure deletion. `Palette` alone is referenced 11 times in agy, 14 in oc, and by 6 test files. | `rg -c` per symbol: `Palette` 11/14, `_strip_ansi` 1/2, `_one_line` 3/2, `_read_id` 2/2, `_read_status` 3/3 |
| F-6 | HAZARD for E-03: `_read_id`/`_read_status` are private-by-convention and `selectors.py` declares no `__all__`, so a cross-module private import is legal but couples to another module's internals. | `rg -c "^__all__" agent_workflows/selectors.py` -> 0 |
| F-7 | Substring guards are weak. The existing one-sided guard uses `assertNotIn("class Palette:", src)`, which a comment satisfies and which `class Palette (object):` evades. E-01 therefore uses AST parsing. | `tests/test_render_stream.py:542` |
| F-8 | CONTENTION, live at authoring: another session committed `render_stream.py` and `tests/test_render_stream.py` in `a396cb1b` (progress-bar percentage formatting). Unrelated to this work, but both files are in this plan's blast radius. | `git log --oneline -1 a396cb1b` |

## Proposed changes (ordered, validatable)

1. Add the symmetric, AST-based, table-driven re-fork guard and prove it fails at HEAD (E-01).
2. Delete the three agy render re-forks; extend the existing `render_stream` import (E-02).
3. Delete `_read_id`/`_read_status` from both runners; import from `selectors`, deciding the private-name question explicitly (E-03).
4. Fold the one-sided guards into the symmetric table and delete them, growing coverage strictly (E-04).
5. Sabotage-verify the guard in both directions (E-05).

## Deferred / out of scope (with reason)

- The class (a) COMMON extraction (34 symbols): that is child 02, and it needs a new shared module, which this plan deliberately does not create.
- Every class (c) DIVERGED symbol: gated behind `lanectn` landing AND E-02's characterization baseline, per the orchestrator's re-pointed sequencing gate.
- `Heartbeat`: already fixed (F-4). Not re-fixed here; only folded into the symmetric guard so it cannot regress.
- Changing `render_stream` or `selectors` themselves, beyond at most a one-line public alias if E-03 chooses option (b).
- The 40 names `agy_runipd` imports FROM `oc_runipd`. This is a genuine structural finding of E-01 (the runners are not peers; agy already depends on oc), but re-homing them is a shared-module design question for child 02 and beyond, not a re-fork deletion. Recorded so it is not mistaken for part of this slice.

## Scope check

- Over-scope: none. Every edit deletes a duplicate definition or strengthens the guard that prevents it.
- Under-scope: this plan does not reduce the runners' line counts materially (the five symbols are ~40 lines total). Its value is the GUARD, not the deletion: without a symmetric guard the next extraction re-forks again, which is F-1's whole point.

## Required tests / validation

- The new symmetric guard, demonstrated FAILING at HEAD and passing after, plus sabotage in both runner directions (E-05).
- `python3 -m pytest tests/test_render_stream.py tests/test_runner_refork_guard.py` green, with counts.
- Both driver suites green: `tests/test_oc_runipd.py` (93 tests at authoring) and `tests/test_agy_runipd_cli.py` (20).
- Full suite bare (`python3 -m pytest`), compared against YOUR OWN pre-change measurement, not a number written here. Baseline at authoring HEAD `c8bb11ae`: `4092 passed, 3 skipped, 4 xfailed`. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`.
- An `assertIs` check per symbol, since object identity is what proves the runner sees the owner's definition rather than an equal-looking copy.

## Spec / documentation sync

- N/A. No spec governs the render layer's ownership, and this plan changes no public contract: every affected name remains reachable at its existing runner attribute path (F-5).

## Open questions

### OQ-01: For `_read_id`/`_read_status`, import the private names or add a public alias to `selectors`?

- Blocking: no
- Status: open
- Owner: executor (E-03), with a stated default
- Resolution or deferral rationale: NOT BLOCKING because either option is behavior-neutral and one line, and E-03 states the default (option (b), a public alias) with its reason: a cross-module private import is coupling a later reader will delete without knowing who depended on it, whereas an alias documents the dependency. Recorded as a question rather than silently chosen because it touches `selectors.py`, which is outside this plan's Scope-Paths, so choosing (b) requires either adding that path with a `--scope-reason` or choosing (a). The executor must state which it did.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new guard FAILING at pre-change HEAD, with the failure naming all five re-forked symbols and identifying which runner each is in. Paste the data table itself, showing it is a table rather than repeated assertions, and show the definition check is AST-based (paste the parsing code, not a grep). A guard never observed failing is not accepted as evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "^class Palette|^def _strip_ansi|^def _one_line" agent_workflows/agy_runipd.py` returning NOTHING. Paste `agy_runipd.Palette is render_stream.Palette` (and the same for the other two) evaluating True. Paste the amended import statement showing the three names were ADDED to the existing `render_stream` import at `agy_runipd.py:45` rather than a second import being introduced. Confirm the 11 agy `Palette` call sites are untouched by pasting the count before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n "^def _read_id|^def _read_status" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` returning NOTHING, i.e. BOTH runners, since a one-sided deletion recreates the divergence. Paste `assertIs` results tying both names in both runners to `selectors`' definitions. STATE EXPLICITLY which OQ-01 option was taken; if (b), paste the one-line `selectors` addition and the `--scope-reason` justifying that out-of-fence path.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `rg -n "test_oc_runipd_source_has_no_inline_definitions|test_agy_runipd_has_no_inline_heartbeat_copy" tests/` returning NOTHING. Paste the symmetric table showing all ten previously-oc-only names plus `Heartbeat` are present, so coverage strictly grew. State which names are NEWLY guarded on the agy side versus merely relocated, so the growth is auditable rather than asserted. Paste `tests/test_render_stream.py` still green, and confirm `test_heartbeat_is_the_same_object_in_both_drivers` and `test_exactly_one_heartbeat_definition_in_the_package` were retained.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: TWO pasted failures from deliberate sabotage, one per runner, each naming the re-inserted symbol; then the guard green after both reverts; then `git status --porcelain` showing no sabotage residue. Also paste both driver suites and the full bare suite with counts, compared against your own pre-change measurement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 5 E-leaves across 3 task groups, under the thresholds. One concern throughout: give each already-extracted symbol a single definition and make the guard that enforces it symmetric.

Open questions: OQ-01 is non-blocking with a stated default and is a one-line choice the executor records. No blocking question remains, so this plan is executable once approved.

This plan is `to-review` and requires explicit human approval before execution.

Scope fence: touch ONLY `agent_workflows/agy_runipd.py`, `agent_workflows/oc_runipd.py`, `tests/test_render_stream.py`, and the new `tests/test_runner_refork_guard.py`. Do NOT change `render_stream.py` behavior. Do NOT create the shared runner module (that is child 02). Do NOT touch any class (c) diverged symbol. `selectors.py` is OUT of fence: reaching it requires OQ-01 option (b) plus a `--scope-reason`. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt). Do NOT edit a sibling plan or the orchestrator, and do NOT reimplement a rule another plan owns.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Do NOT claim a de-duplication on the strength of a grep: the identity assertions are the proof. Do NOT describe this plan as reducing duplication materially; it removes ~40 lines and installs the guard that stops the next re-fork, which is the real deliverable.

Execution contract: RE-READ both runner modules immediately before editing and locate every symbol BY NAME, not by the line numbers in this plan: another session committed `render_stream.py` and `tests/test_render_stream.py` in `a396cb1b` while this plan was being authored, and the runners are the highest-contention files in the repo. Commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and re-verify after any hook interruption.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
