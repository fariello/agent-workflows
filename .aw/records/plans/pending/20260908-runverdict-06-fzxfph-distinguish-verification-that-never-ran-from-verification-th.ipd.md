# IPD: Distinguish verification that never ran from verification that ran inconclusively and refuse a stale plan path loudly

- Date: 2026-09-08
- Kind: child
- Concern: `unverified` is written for THREE materially different facts and a reader cannot tell them apart. Measured at HEAD `44d4950d`, `verify_disp = "unverified"` is assigned at exactly three sites in `oc_runipd.py` (`:6432` unparseable outcome JSON with nonzero exit, `:6434` NO outcome file written at all, `:6436` the turn raised `KeyboardInterrupt` or `StallTimeout`), with the byte-identical triple in `agy_runipd.py` (`:3696`, `:3698`, `:3700`). "The verifier ran and could not conclude", "the verifier never wrote its verdict", and "the verifier turn was killed" are three different problems with three different remedies, and all three read as one benign-looking caveat.
  THIS IS THE SURVIVING HALF OF BACKLOG `t74o5q`. THAT ITEM'S CENTRAL MECHANISM IS ALREADY FIXED AND ITS 23 MEASURED FAILURES CANNOT RECUR. The item's root cause was that the verify prompt cited a `pending/` path the self-finalize step had already invalidated. That was fixed at commit `1549c018` ("fix(runner): re-resolve current plan path before verification turn", 2026-08-28 02:42 UTC), which re-resolves through `resolve_plan_path` immediately before building the prompt and passes the RE-RESOLVED value to both `build_verifier_prompt` and the child launch. Verified at HEAD: `oc_runipd.py:6373-6379` re-resolves and `:6396` passes `current_plan_path` to `run_opencode`; the agy twin is `:3637-3643` and `:3660`. THE FIX PREDATES THE ITEM: the item was filed 2026-08-30 02:02 UTC, and all 23 failing turns are in three runs created 2026-08-25T03:51Z (13), 2026-08-25T10:58Z (3) and 2026-08-28T00:29Z (7), every one BEFORE the fix. Re-measured 2026-09-08 across all 135 run directories: 57 verify session logs, 34 outcome files, 23 logs containing only `Error: File not found: .../pending/<plan>.ipd.md`, and ZERO such logs in any run created after the fix. So the item's fix (1) is DEAD, and its tests (a), (c) and (d) are already satisfied (the regression `tests/test_oc_runipd.py::VerifierPromptTests::test_resolve_plan_path_handles_transition_to_executed` shipped in the same commit and passes today: `1 passed`).
  WHAT SURVIVES IS THE ITEM'S FIX (3) AND (4), AND THEY ARE REAL. Fix (3): a verifier that exits without writing its outcome file must be a recorded HARD failure, not a quiet `unverified`. Fix (4): the `except DriverError: current_plan_path = plan_path` fallback (`oc_runipd.py:6376-6377`, agy `:3640-3641`) still SILENTLY substitutes a known-stale path when re-resolution fails, which is the same class of defect the fix removed from the happy path but left on the error path.
- Scope: Split `unverified` into distinguishable recorded facts so "verification never ran" is not reported as "verification was inconclusive", and make the stale-path fallback refuse loudly instead of proceeding with a path it knows may be wrong. EXCLUDES the verdict MAPPING for a verdict that WAS written (sibling `1bfppy`, this Set's Order 05, which owns the fail-closed table); excludes re-fixing the prompt path (already fixed at `1549c018`); excludes the model/rate-card record (`vlf75p`) and the unconsumed-evidence defect (`rbftpl`); excludes changing whether the verifier turn runs at all.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_runner_refork_guard.py
- Item-Dependencies: none
- Status: to-review
- Set: runverdict
- Order: 6
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: fzxfph
- Blocks-Release: next
- From-Backlog: t74o5q

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `t74o5q` as a NARROWED plan; the item carries `- Blocks-Release: next` and this plan inherits that gate. THE OBSOLESCENCE FINDING IS THE MOST IMPORTANT THING IN THIS HISTORY, because it removes most of the item's stated work and all of its urgency. The item's headline ("40% of verifier turns never ran") describes 23 turns in three runs, all created before commit `1549c018` (2026-08-28 02:42 UTC) fixed the exact mechanism it names, and the item was written 2026-08-30, two days AFTER the fix. Measured rather than inferred: every one of the 23 short `File not found` logs is in a run created 2026-08-25 or 2026-08-28T00:29Z; zero runs created after the fix contain one; the fix's own regression test ships in `tests/test_oc_runipd.py` and passes today; and the re-resolved path now reaches BOTH the prompt and the child launch, which the item said it did not. So the item's fix (1) and its tests (a), (c) and (d) are DEAD and are NOT graduated. The item's own "NOT A RESOLUTION-LOGIC DEFECT" paragraph was already half-right and half-stale: it correctly said `resolve_plan_path` was fine, and incorrectly said "the resolved value is not what reaches the CHILD PROCESS", which was true before `1549c018` and is false at HEAD.
  WHAT THIS PLAN GRADUATES IS THE ITEM'S FIX (3) AND (4) AND ITS TEST (b), each re-verified as live at HEAD `44d4950d`. Fix (3) survives because `verify_disp = "unverified"` is genuinely written for three distinct facts at three sites per host, which I located and read rather than trusting. Fix (4) survives verbatim: the silent fallback to a known-stale `plan_path` is still there on the error path, at `oc_runipd.py:6376-6377` and `agy_runipd.py:3640-3641`. Its fix (2) ("order the turn so verification happens BEFORE the plan is moved") is NOT graduated and is recorded as deferred with the reason: `1549c018` solved the same problem by re-resolution rather than reordering, so reordering the self-finalize sequence now would be a second solution to a solved problem, with real blast radius on the `driver_begin`/`driver_finalize` transaction.
  ORDERING RELATIVE TO SIBLING `1bfppy` (Order 05, the verdict mapping): INDEPENDENT, declared as no dependency. That plan owns the case where a verdict WAS written and is mis-mapped; this plan owns the case where no verdict was written at all. They touch adjacent lines in the same block, which is a coordination note and not a dependency, and the runner isolates each item in its own worktree.

## Goal

Make the run record say WHICH of three things happened when verification did not produce a verdict, and stop the verifier launching against a path the runner knows may be stale.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: distinguish the three facts

- [ ] E-01 ENUMERATE AND NAME THE THREE FACTS currently collapsed into `unverified`, as a closed set in `runner_shared.py`, and record at each write site which fact it records. Located at HEAD `44d4950d` (find them by SYMBOL, inside `execute_item`'s `v_outcome_file` block, never by these line numbers): `oc_runipd.py:6432` unparseable outcome JSON with a nonzero exit; `:6434` no outcome file written at all; `:6436` the turn raised `KeyboardInterrupt` or `StallTimeout`. The agy triple is `:3696`, `:3698`, `:3700` and is byte-identical.
  SITE THE NAMES IN `runner_shared.py`, NOT IN `oc_runipd.py`. `agy_runipd` already imports 47 names from `oc_runipd` (AST-measured 2026-09-08) and zero flow back, so adding these to oc for agy to import would make it 48 and deepen the layering defect backlog `cnwy8g` owns.
  CHECK WHETHER `run_state.py` ALREADY HAS THE VOCABULARY BEFORE INVENTING TOKENS. It defines `STATE_FAILED`, `STATE_VERIFYING`, `STATE_VERIFIED` and `STATE_CORRECTION_REQUIRED` (`:30-34`) and imports no first-party module (AST-verified), so consuming it cannot create a cycle. If it has no token for "never ran", say so explicitly rather than silently minting a fourth vocabulary; the repository already has three overlapping ones (`TERMINAL_STATES`, `run_state.ALL_STATES`, and the `verify_disp` strings), and a fourth is a real cost.
  COORDINATE WITH SIBLING `1bfppy`, which is adding a shared verdict mapping to the SAME module for the adjacent case. Read its status on disk. If it has landed, its mapping is where the "a verdict was written" cases live and this plan's names cover only the "no verdict was written" cases; the two sets must not overlap or a value will be classified twice.
  - Depends on: none
  - Expected outcome: a closed named set in `runner_shared.py` distinguishing the three facts, each write site annotated with which it records; `run_state`'s existing vocabulary consumed where it fits and the gap stated where it does not; no overlap with sibling `1bfppy`'s mapping.
  - Execution state: pending

- [ ] E-02 WRITE THE DISTINGUISHED FACT AT ALL SIX SITES (three per host) so the run record carries which one occurred, and make "verification never ran" a RECORDED HARD failure rather than a quiet caveat. This is the item's fix (3).
  DO NOT CHANGE WHETHER THE RUN CONTINUES, and this is the boundary that keeps this plan small. `integration_is_earned` (`oc_runipd.py:3684`) ALREADY refuses integration when validation is ON and `verify_disp != "verified"`, with an explicit reason ("a green suite deliberately does NOT override an explicit verifier verdict"), and `self_finalize` is gated on the earned verdict, so an `unverified` turn already does not auto-merge and its lane is already preserved. So "hard failure" here means RECORDED AND REPORTED AS SUCH, not a new refusal. Confirm that gate still holds after your change and paste it; do NOT add a second refusal on top of it.
  BE PRECISE ABOUT THE INTERRUPT CASE. The `KeyboardInterrupt`/`StallTimeout` site is a DELIBERATE-STOP-adjacent fact, and this repository has an explicit contract that a deliberate stop must not be relabelled as a failure (spec `c4gd2h` R22 forbids fabricating a disposition, and `runner_stop.is_indeterminate` marks a force-cut item INDETERMINATE precisely so nothing claims to know its outcome). Check whether that site is already covered by the indeterminate machinery before classifying it as a failure, and if it is, leave it alone and say so.
  - Depends on: E-01
  - Expected outcome: all six sites record the distinguished fact; the never-ran case is reported as a hard failure rather than a caveat; the run's continue/refuse behavior and lane preservation are UNCHANGED and proven so; the interrupt site's interaction with the indeterminate machinery checked rather than assumed.
  - Execution state: pending

### Task group 2: refuse the stale path instead of using it

- [ ] E-03 MAKE THE STALE-PATH FALLBACK REFUSE LOUDLY. `except DriverError: current_plan_path = plan_path` (`oc_runipd.py:6376-6377`, agy `:3640-3641`) silently substitutes a path captured earlier in the turn when re-resolution fails. That is the item's fix (4), and it is the last surviving piece of the original path defect: commit `1549c018` fixed the HAPPY path by re-resolving, and left this ERROR path substituting a value it knows may be wrong.
  A REFUSAL, NOT A CRASH, AND NOT A SILENT SKIP. An unresolvable plan means verification CANNOT be performed, which E-01 already gives a name to; record that fact and report it rather than launching a child against a path that may not exist. Reuse E-01's vocabulary; do not invent a fourth outcome here.
  STATE WHEN THIS CAN ACTUALLY FIRE, because a refusal on an unreachable branch is dead code. `resolve_plan_path` (`runner_shared.py:1119`) raises `DriverError` only when the id6 resolves to zero files or to more than one; it tries the id6 selector, then the configured path, then an `rglob` over three roots. Determine and record which real conditions produce that (a plan deleted mid-turn, an id6 collision, a lane worktree missing the plan) and cite the one you can actually construct in a test.
  DO NOT REORDER THE SELF-FINALIZE SEQUENCE. The item's fix (2) proposed moving verification before the plan move; that is NOT this plan's scope, because `1549c018` solved the same problem by re-resolution and reordering the `driver_begin`/`driver_finalize` transaction now would be a second solution to a solved problem.
  - Depends on: E-01
  - Expected outcome: an unresolvable plan produces a named recorded refusal instead of a launch against a stale path; the conditions under which it can fire are stated and at least one is constructible in a test; the self-finalize ordering is untouched.
  - Execution state: pending

### Task group 3: prove and fence

- [ ] E-04 TEST ALL THREE FACTS AND THE REFUSAL, per host, from FIXTURES rather than the live run tree. `.aw/records/runs/` is gitignored and roughly 32 tests fail inside a lane worktree precisely because several read live run state, so a test built on the real corpus passes here and fails in isolation.
  ASSERT THE HISTORICAL CASE IS ALREADY FIXED RATHER THAN RE-FIXING IT. The item's test (d) asked for a regression proving the 23 historical cases would now run; that regression ALREADY EXISTS and passes (`tests/test_oc_runipd.py::VerifierPromptTests::test_resolve_plan_path_handles_transition_to_executed`, shipped in `1549c018`, measured `1 passed` on 2026-09-08). Do NOT write a second one. Instead paste that test's passing output as the evidence that the dead half of the item is genuinely dead, and note whether an AGY twin of it exists; if it does not, adding one is in scope and is the honest gap, since `resolve_plan_path` is shared but the agy call site is its own.
  ADD THE PRE-FIX CONTRAST FOR WHAT THIS PLAN DOES CHANGE. For each of the three facts, show that before the change all three produced the same recorded value and after it they do not. Without that contrast a test asserting three distinct values proves nothing about the defect.
  - Depends on: E-02, E-03
  - Expected outcome: per-host tests for the three facts and the refusal, fixture-driven; the existing `1549c018` regression pasted as passing; an agy twin added if absent; the pre-fix contrast pasted.
  - Execution state: pending

- [ ] E-05 PIN THE SHARING SYMMETRICALLY AND MUTATION-CHECK IT. Register every symbol this plan adds in `tests/test_runner_refork_guard.py`'s `REFORK_TABLE` with BOTH runners listed, which its `test_the_table_covers_both_runners` already enforces, and assert object identity across `oc_runipd`, `agy_runipd` and `runner_shared`.
  GREP IS NOT EVIDENCE OF SHARING. It cannot distinguish a shared object from a textually identical copy, which is exactly how `render_stream` was extracted and then re-forked in the other driver with nothing noticing; the one-sided versions of this guard were RETIRED for that reason. Mutation-check: define a local copy in `agy_runipd`, show the guard FAILS, revert, show it passes.
  - Depends on: E-04
  - Expected outcome: a `REFORK_TABLE` row covering both runners; object-identity assertions across all three modules; the guard demonstrated to fail under a re-fork mutation; the AST-measured oc-to-agy import count unchanged at 47 or lower.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE PATH DEFECT IS FIXED AND THE FIX'S SHAPE IS THE PRECEDENT. `1549c018` re-resolves through `resolve_plan_path` immediately before use and passes the re-resolved value to both the prompt and the child. That is the pattern; this plan extends it to the error path rather than replacing it.
- `resolve_plan_path` IS SHARED AND DISPOSITION-AGNOSTIC (`runner_shared.py:1119`): it resolves by id6 through `selectors.resolve_selectors` first, then the configured path, then an `rglob` over three roots, raising `DriverError` only on zero or multiple matches.
- AN `unverified` TURN ALREADY DOES NOT AUTO-MERGE. `integration_is_earned` (`oc_runipd.py:3684`) refuses when validation is ON and the verdict is not `verified`, and its docstring records the measured cost of the opposite mistake (~$528 across five overnight runs, 21 plans stranded). So this plan improves the RECORD, not the gate.
- A DELIBERATE STOP MUST NOT BE RELABELLED A FAILURE. Spec `c4gd2h` R22 forbids fabricating a disposition, `runner_stop.is_indeterminate` exists to mark a force-cut item as unknown-outcome, and `reconcile_interrupted` (`oc_runipd.py:6782`) refuses to promote such an item even when the plan sits in `executed/`. The interrupt-case classification must respect that.
- THE IMPORT DIRECTION IS ONE-WAY: `agy_runipd` imports 47 names from `oc_runipd`; `oc_runipd` imports zero from agy. Shared symbols go in `runner_shared`.
- `run_state.py` IMPORTS NO FIRST-PARTY MODULE (AST-verified) and already defines a verification state vocabulary, but NEITHER driver imports it (AST walk, zero matches). Sibling `1bfppy` is wiring it in for the adjacent case.
- `.aw/records/runs/` IS GITIGNORED. Use fixtures; roughly 32 tests fail inside a lane worktree because several read live run state.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses).

## Findings

| Id | Severity | Location (measured at HEAD `44d4950d`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | OBSOLETE | `oc_runipd.py:6373-6379`, `:6396`; agy `:3637-3643`, `:3660` | THE ITEM'S CENTRAL DEFECT IS FIXED. The verify prompt and the child launch both receive the RE-RESOLVED path, fixed at `1549c018` (2026-08-28 02:42 UTC), two days BEFORE the item was filed (2026-08-30 02:02 UTC). | `git log -S` on the fix; source read at both hosts; commit timestamps |
| F-2 | OBSOLETE | 135 run directories | All 23 `File not found` verifier logs are in three runs created 2026-08-25T03:51Z (13), 2026-08-25T10:58Z (3), 2026-08-28T00:29Z (7), every one BEFORE the fix. ZERO runs created after it contain one. | scanned every `sessions/*verify*` across all runs: 57 logs, 34 outcome files, 23 short `File not found` logs, all pre-fix |
| F-3 | OBSOLETE | `tests/test_oc_runipd.py` | The item's requested test (d) ALREADY EXISTS and passes: `VerifierPromptTests::test_resolve_plan_path_handles_transition_to_executed`, shipped in the same commit as the fix. | `python3 -m pytest -k transition_to_executed` -> `1 passed` |
| F-4 | HIGH | `oc_runipd.py:6432`, `:6434`, `:6436`; agy `:3696`, `:3698`, `:3700` | `verify_disp = "unverified"` is written for THREE materially different facts (unparseable JSON, no outcome file at all, turn killed) with three different remedies, indistinguishable in the record. | source read, both hosts |
| F-5 | HIGH | `oc_runipd.py:6376-6377`, agy `:3640-3641` | `except DriverError: current_plan_path = plan_path` still SILENTLY substitutes a known-stale path when re-resolution fails. The happy path was fixed; the error path was not. | source read, both hosts |
| F-6 | MED | `oc_runipd.py:3684` | An `unverified` turn already does not auto-merge and its lane is preserved, so this plan changes the RECORD rather than the gate, which is why it is small. | source read of `integration_is_earned` |
| F-7 | MED | `run_state.py:30-34`; both drivers | A verification state vocabulary exists and neither driver imports it, so a fourth ad-hoc vocabulary is a real risk this plan must avoid. | AST walk, zero matches in both drivers |
| F-8 | LOW | backlog `t74o5q` | The item's ordering advice ("fix this first, it fired 23 times") is obsolete, and its claim that "the resolved value is not what reaches the CHILD PROCESS" was true before `1549c018` and is false at HEAD. | F-1, F-2 |

## Proposed changes (ordered, validatable)

1. E-01 names the three collapsed facts in `runner_shared.py`, consuming `run_state`'s vocabulary where it fits and stating the gap where it does not.
2. E-02 writes the distinguished fact at all six sites and reports the never-ran case as a hard failure, changing no gate and respecting the indeterminate machinery.
3. E-03 makes the stale-path fallback refuse with a named recorded reason, and states the conditions under which it can fire.
4. E-04 tests all three facts and the refusal per host from fixtures, pastes the existing `1549c018` regression as evidence the dead half is dead, and adds an agy twin if absent.
5. E-05 pins the sharing symmetrically and mutation-checks the guard.

## Deferred / out of scope (with reason)

- NOT GRADUATED AS OBSOLETE, and recorded in the backlog item itself rather than only here: the item's fix (1) (pass the plan by stable id / re-resolve before launch) and its tests (a), (c) and (d). All were delivered by `1549c018` on 2026-08-28, before the item was written, and the regression test ships with it and passes. Re-implementing them would be work an existing commit already declares.
- THE ITEM'S FIX (2) (order the turn so verification happens BEFORE the plan is moved, or have the mover publish the new path back). NOT graduated, deliberately. `1549c018` solved the same problem by re-resolution, so reordering now is a second solution to a solved problem, and it would reach into the `driver_begin`/`driver_finalize` transaction (`oc_runipd.py:894`, `:976`), which has its own receipt and scope-reconciliation gates. If a future defect shows re-resolution is insufficient, reordering is the right response then.
- THE VERDICT MAPPING for a verdict that WAS written: sibling `1bfppy` (this Set, Order 05). That plan owns the fail-closed table; this one owns the absence of a verdict. Adjacent lines, separate concerns.
- THE MODEL AND RATE-CARD RECORD: sibling `vlf75p`. VERIFIER EVIDENCE NEVER CONSUMED: sibling `rbftpl`.
- CHANGING WHETHER THE VERIFIER TURN RUNS. The `validate` default and its per-host resolution belong to pending plans `tm2cz8`/`ybkmzp` (`hostdefault`) and `kgpptv` (`runprofile` Order 06).
- ADDING A NEW REFUSAL BEYOND THE STALE-PATH ONE. The integration gate already refuses correctly; a second refusal on top would be redundant and could strand work the existing gate handles.

## Scope check

- Over-scope: `runner_shared.py` is in scope ONLY to hold the named facts. Do NOT edit `run_state.py`, `verify_roles.py`, `runner_stop.py` or the `driver_begin`/`driver_finalize` transaction. Do NOT change `integration_is_earned`. Do NOT re-fix the prompt path.
- Under-scope: stated rather than left as `none`. The distinguished facts are recorded and reported to a human but are NOT made machine-readable in `--json`/`--agent` (that surface belongs to pending plan `r2i1b1`, whose E-03 must first extract five duplicated predicate copies). A rejected or never-run turn is also NOT requeued; that is sibling `1bfppy`'s OQ-01.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals. Cases belong in `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py`; the sharing guard in `tests/test_runner_refork_guard.py`. Fixtures, never the gitignored live run tree. `tests/test_oc_runipd.py::VerifierPromptTests::test_resolve_plan_path_handles_transition_to_executed` must keep passing untouched: it is the existing regression for the already-fixed half and this plan must not disturb it.

## Spec / documentation sync

Spec `25kzda` (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, `- Status: approved`) governs verification, and this plan moves the code TOWARD it rather than amending it, so no spec file is declared in `- Scope-Paths:`. The relevant approved text, quoted rather than paraphrased: §4.2's `RUN-FRESH-VERIFIER` row requires a "valid evidence-linked envelope", its failure message is `[RUN-FRESH-VERIFIER] <item> has no valid independent verification attempt`, and its action is `RETRY, then FAIL ITEM`. That row describes EXACTLY the never-ran case this plan names, and it already calls it a failure, so recording it as one needs no amendment.
TWO THINGS TO CHECK RATHER THAN ASSUME. FIRST, that row's action is `RETRY, then FAIL ITEM`, and this plan deliberately does NOT retry (see the under-scope note). Read the row and report whether the spec is satisfied by recording the failure without retrying, or whether the retry is required; if required, that is a maintainer decision about scope rather than something to resolve silently. SECOND, the spec quotes operator-facing recovery strings verbatim; if this plan's new reason text collides with one, reflect it. Do NOT edit §4.2's finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Does the interrupt site belong in the three-fact split at all, or is it already owned by the indeterminate machinery?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-02 already instructs that the site be CHECKED against the indeterminate machinery and left alone if covered, so the plan is executable either way. The question matters because spec `c4gd2h` R22 forbids fabricating a disposition and `runner_stop.is_indeterminate` exists precisely so a force-cut turn is recorded as unknown-outcome rather than as a failure. If that machinery already reaches this site, classifying it as a verification failure would be a fabrication in the direction the spec forbids. Measured starting point: `reconcile_interrupted` (`oc_runipd.py:6782`) refuses to promote an indeterminate item even when the plan is in `executed/`, so the concept is live in this file. Read `runner_stop.is_indeterminate`'s callers before answering.

### OQ-02: Does an agy twin of the `1549c018` path regression exist, and if not is adding one in scope?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-04 already instructs that the twin be added if absent, which is the conservative answer. Recorded because the honest position matters: `resolve_plan_path` is SHARED (`runner_shared.py:1119`) so the resolution logic is covered once, but each host has its OWN call site and its own `except DriverError` fallback, and a shared function does not prove a call site passes its result onward. `1549c018` added the test to `tests/test_oc_runipd.py` only. Grep `tests/test_agy_runipd_cli.py` before answering; if the twin is absent, adding it is small and belongs here since this plan edits that exact fallback.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the named fact set as written and its location in `runner_shared.py`. Paste the annotation at each of the six write sites. State whether `run_state.py`'s existing vocabulary was consumed and for which facts, and where it had no token, name the gap explicitly. Paste sibling `1bfppy`'s `- Status:` line and directory read at validation time, and paste proof the two name sets do NOT overlap (a set-intersection, printed empty).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste, for each of the three facts, the recorded value in a real `state.json` queue entry, showing three DISTINCT values where there was one. Paste the PRE-FIX contrast showing all three were previously identical. Paste `integration_is_earned`'s refusal for a never-ran turn and proof the lane is preserved, demonstrating the gate is unchanged. State OQ-01's answer and paste the reading of `runner_stop.is_indeterminate`'s callers that decided it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the refusal as written and the ACTUAL output when a plan cannot be re-resolved, showing it names the reason and does NOT launch a child. Paste the constructed test case that makes `resolve_plan_path` raise, and state which real-world condition it represents. Paste proof no child process was launched (assert on the argv or the absence of a session log, not on prose).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new tests and their actual runner output, per host. Paste `tests/test_oc_runipd.py::VerifierPromptTests::test_resolve_plan_path_handles_transition_to_executed` PASSING, as the evidence that the item's dead half is genuinely dead. State OQ-02's answer and, if a twin was added, paste it passing. Paste the pre-fix contrast for each of the three facts. Paste proof no test reads `.aw/records/runs/`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new `REFORK_TABLE` row showing BOTH runners, and `tests/test_runner_refork_guard.py` passing. Paste object-identity output for every added symbol across all three modules. Paste the MUTATION CHECK in full: define a local copy in `agy_runipd`, paste the FAILING guard output, revert, paste the passing output. Paste the AST-measured oc-to-agy import count before and after, showing it did not increase from 47.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the six paths in `- Scope-Paths:`. Do NOT re-fix the verifier prompt path (already fixed at `1549c018`; re-doing it is the single most likely wasted action on this plan). Do NOT reorder the self-finalize sequence. Do NOT edit `run_state.py`, `verify_roles.py`, `runner_stop.py`, `integration_is_earned`, or the `driver_begin`/`driver_finalize` transaction. Do NOT change the verdict MAPPING for a verdict that was written (sibling `1bfppy`). Do NOT add a symbol to `oc_runipd` for `agy_runipd` to import. Do NOT add a new refusal beyond the stale-path one. Do NOT edit spec `25kzda`, and never its §4.2 finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. `oc_runipd.py` and `agy_runipd.py` are the highest-contention files in this repository and are being edited by live runs; measured, their line numbers moved roughly 70 and 95 lines in a single day, and sibling `1bfppy` edits the SAME block. Find `execute_item`'s `v_outcome_file` block, `resolve_plan_path`, `build_verifier_prompt`, `integration_is_earned`, `reconcile_interrupted`, and `runner_stop.is_indeterminate` by name.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved fzxfph --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, close backlog `t74o5q`, which this plan carries as `- From-Backlog:` and whose `- Blocks-Release: next` gate it inherits. The item's obsolete halves are recorded in the item itself, so closing it does not silently drop work: the surviving fixes (3) and (4) ship here and fixes (1) and (2) are recorded as already-delivered and deliberately-not-done respectively.
