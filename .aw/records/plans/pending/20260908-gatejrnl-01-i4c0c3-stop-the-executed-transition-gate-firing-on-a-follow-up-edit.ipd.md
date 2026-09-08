# IPD: Stop the executed-transition gate firing on a follow-up edit to a plan already in executed

- Date: 2026-09-08
- Kind: child
- Concern: The `ipd-executed-transition-gate` pre-commit hook refuses an ORDINARY EDIT to a plan that is already, legitimately, in `executed/`. The cause is a specific bug in the transition detector, not the journal-lifetime problem the backlog item hypothesized: for a plain modification git reports status `M` with ONE path, the detector's `A/M/C` branch sets `old_path = None`, and the `moved_into_executed` test then reads `old_path is None` as "the file was not previously in executed/" and fires. So a file that has sat in `executed/` for weeks is classified as MOVING INTO `executed/` by every commit that touches it, and since no finalize journal exists for a transition that is not happening, the gate refuses. Recovering from this requires `--no-verify`, and the item is explicit about the real cost: a gate that false-positives on correct behavior trains agents to bypass it.
- Scope: Fix the false positive only. Make `moved_into_executed` ask the question it means to ask (was this path in `executed/` at HEAD?) instead of inferring it from a missing rename source, so a follow-up edit to an already-executed plan is not a transition. Preserve every genuine refusal, including the in-place hand-edited `- Status: executed` flip, which shares the same `M`/`old_path is None` shape and must keep refusing via the separate `gained_executed` test. Fixes NOTHING about the merge case, which approved plan `29wvmj` owns.
- Scope-Paths: agent_workflows/hooks/executed_transition_gate.py, tests/test_executed_transition_gate.py
- Item-Dependencies: none
- Status: to-review
- Set: gatejrnl
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: i4c0c3
- From-Backlog: gjadwm
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `gjadwm`, inheriting its `Blocks-Release: next` gate. THIS IS A NARROWING, AND IT ALSO CORRECTS THE ITEM'S DIAGNOSIS. The item reports TWO cases. CASE 1 (merging a lane-finalized plan) IS ALREADY OWNED by APPROVED plan `29wvmj` (Set `integpath`, Order 01, `From-Backlog: rnl3b7`), whose E-01 adds the merge-context detector via `git rev-parse --git-dir`, E-02 adds the in-tree finalize-evidence predicate accepting a `lifecycle(<id6>): finalize` commit reachable from the incoming side, E-03 preserves four refusal cases, E-04 makes the merge refusal actionable, E-05 tests through a real `git merge --no-ff --no-commit`, and E-06 installs the gate on `pre-merge-commit` too. That plan is approved and will land before this one runs, so case 1 is NOT graduated here and must NOT be re-implemented. CASE 2 (a follow-up commit to a plan already finalized in this tree) SURVIVES, and I reproduced it in a throwaway repo at HEAD `8b4e1570`: a plan committed in `executed/`, then a one-line body edit, `git add`, and `check()` returns rc 1 with "raw plan->executed transition (moved into executed/) with NO matching finalize evidence in .aw/state/". THE ITEM'S EXPLANATION FOR CASE 2 IS WRONG IN A WAY THAT MATTERS. It attributes case 2 to the journal being deleted on success, and therefore proposes retaining a durable completion record (its option 3) or accepting the begin receipt. Neither is needed. I traced the actual cause: `git diff --cached --name-status -M` reports `M<TAB><path>` for a plain edit, the detector's `A/M/C` branch assigns `old_path = None` (`executed_transition_gate.py:120-126`), and `moved_into_executed` is computed as `_EXECUTED_SEGMENT in ("/" + new_path) and (old_path is None or ...)` (`:132-134`), so `old_path is None` satisfies the second clause and the edit is classified as a move INTO `executed/`. Measured the discriminator that makes the fix safe: for that same edit the HEAD blob AT THE SAME PATH exists, and `gained_executed` is False (the HEAD content was already `executed`). So "was this path already in `executed/` at HEAD?" cleanly separates case 2 from every genuine transition, and the fix is one predicate rather than a new durable-state lifecycle. The item's own option 4 anticipated exactly this ("the staged-rename detection may be over-broad"); this plan implements that option and discards options 1 and 3 as unnecessary for case 2. The item's CONSTRAINT is honored: no refusal is weakened, and E-02 exists specifically because the in-place status flip shares case 2's `M`/`old_path is None` shape.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make an ordinary edit to an already-executed plan an ordinary commit. The gate should fire on a plan ENTERING `executed/`, not on every subsequent commit that touches a plan already there, so operators and agents stop being taught that `--no-verify` is routine.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: fix the over-broad transition detector

- [ ] E-01 Make `moved_into_executed` in `_staged_plan_executed_transitions` (`agent_workflows/hooks/executed_transition_gate.py:97-149`) test whether the path was ALREADY under `executed/` at HEAD, instead of inferring it from `old_path is None`. Today the expression is `_EXECUTED_SEGMENT in ("/" + new_path) and (old_path is None or _EXECUTED_SEGMENT not in ("/" + old_path))` (`:132-134`), and for a plain `M` the `A/M/C` branch (`:120-126`) sets `old_path = None`, so the `or` short-circuits true and every edit to an executed plan reads as a move into `executed/`. Use the HEAD blob at `new_path` as the discriminator: the module already has `_blob_at` and already calls it (`head_text` at `:136`), so when a HEAD blob exists at the SAME path and that path is already under `executed/`, the file did not move there in this commit. Keep the genuine rename case (`R` with `old_path` outside `executed/`) firing exactly as today.
  - Depends on: none
  - Expected outcome: the case-2 reproduction (a body-only edit to a plan committed in `executed/`) returns rc 0 with no messages, while a `git mv` from `pending/` into `executed/` still returns rc 1 with "moved into executed/".
  - Execution state: pending

- [ ] E-02 PROVE THE IN-PLACE STATUS FLIP STILL REFUSES, because it shares case 2's exact git shape and is the single most likely way this fix could open a hole. A hand-edit that rewrites `- Status: approved` to `- Status: executed` WITHOUT moving the file is also reported as `M` with `old_path = None`, so E-01's change removes it from `moved_into_executed`. It must continue to refuse through the OTHER, independent test: `gained_executed`, which compares the staged content's executed status against the HEAD content's (`:135-139`). Verify by reading the code that the two conditions are OR'd (`if moved_into_executed or gained_executed`, `:141`) and then by running the existing test `test_hand_edited_status_executed_without_receipt_refused` (`tests/test_executed_transition_gate.py:96-107`), which pins precisely this and must pass UNMODIFIED. Note the ordering subtlety to confirm rather than assume: for an in-place flip the HEAD blob DOES exist at the same path, so E-01's new predicate will correctly say "did not move", and the refusal must come entirely from `gained_executed`.
  - Depends on: E-01
  - Expected outcome: `test_hand_edited_status_executed_without_receipt_refused` passes unmodified, and the refusal is demonstrated to originate from `gained_executed` rather than from the path test.
  - Execution state: pending

- [ ] E-03 Preserve every OTHER genuine refusal and the hook's no-op cases, checked case by case against the existing suite rather than by assertion. `tests/test_executed_transition_gate.py` already pins ten behaviors and ALL must still pass unmodified: the three no-op/negative cases (`test_ordinary_commit_no_plan_transition_is_noop` `:68`, `test_nonterminal_plan_change_not_gated` `:75`, `test_prompt_executed_transition_not_gated` `:84`), the two refusals (`:96`, `test_git_mv_into_executed_without_receipt_refused` `:109`), the three journal-binding cases (`test_finalize_journal_at_ready_to_commit_passes` `:122`, `test_stale_journal_wrong_dest_refused` `:144`, `test_journal_wrong_phase_refused` `:163`), the installed-hook end-to-end case (`test_real_finalize_own_commit_passes_via_installed_hook` `:183`), and `test_grandfathered_plan_without_finalize_is_refused` (`:201`). ALSO preserve the no-readable-`- Id:` refusal, which the hook handles separately and which `29wvmj` E-03(d) likewise requires to keep refusing. Do NOT change the refusal MESSAGE wording for any case that still refuses: operators and agents have learned it, and `29wvmj` E-03 makes the same demand from the merge side.
  - Depends on: E-01
  - Expected outcome: all ten existing tests pass with NO edits to the test file's existing cases, demonstrated by a pasted run.
  - Execution state: pending

### Task group 2: pin the fix and stay out of 29wvmj's way

- [ ] E-04 Add the case-2 regression test, built the way the existing suite builds fixtures so it composes rather than inventing a second harness. Use the module's own helpers: `_write_plan(plan_id, ...)` (`tests/test_executed_transition_gate.py:49-61`), `_executed_dir()` (`:63-66`), `_commit_all` and `_stage` (`:29-32`). The test must commit a plan that is ALREADY in `executed/` with `- Status: executed`, then make a BODY-ONLY edit (touching neither the status line nor the path), stage it, and assert `check()` returns rc 0 with no messages. ALSO add the adjacent case that is easy to miss and would otherwise regress silently: a second commit that edits an already-executed plan's `## Workflow history` (which is what a correction to a finalized plan usually touches, and is exactly what case 2 was in the field). Assert the test FAILS against HEAD `8b4e1570` before the fix, so it is proven to bite.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: two new tests covering a body edit and a history edit to an already-executed plan; both fail at HEAD `8b4e1570` and pass after E-01.
  - Execution state: pending

- [ ] E-05 Keep this change DISJOINT from approved plan `29wvmj`, and verify the disjointness rather than trusting it, because both plans edit the SAME two files and `29wvmj` is approved and will likely land first. `29wvmj`'s `Scope-Paths` are `agent_workflows/hooks/executed_transition_gate.py`, `.pre-commit-config.yaml`, `CONTRIBUTING.md`, `tests/test_executed_transition_gate.py`; this plan touches only the first and last. The functional split is clean: `29wvmj` adds a merge-context detector and an in-tree evidence predicate (both consulted when a transition HAS been detected), while this plan corrects WHETHER a transition is detected at all. Before editing, re-read the file to see whether `29wvmj` has already landed; if it has, confirm its merge path still works after this change by running ITS tests too, and if the two edits have collided in a way that cannot be combined safely, STOP and report rather than reverting a sibling's work. Add a code comment at the fixed predicate naming both concerns, so a future reader does not "simplify" one back into the other.
  - Depends on: E-04
  - Expected outcome: a stated, verified account of whether `29wvmj` has landed; if it has, its own tests pass alongside the new ones; a comment records the two distinct concerns.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The hook is deliberately LOCAL best-effort prevention, not a security boundary: it is skippable with `--no-verify` and not cloned by default, and the portable authority is the `aw check`/`aw doctor` backstop. That framing is what makes a false positive expensive rather than merely annoying, since the mitigation an operator reaches for is the bypass.
- Detection compares the STAGED index (`:0:`) against HEAD via `git diff --cached --name-status -M` and fires on either of two independent conditions OR'd together (`:141`): `moved_into_executed` (a rename into `executed/`) or `gained_executed` (a status flip). Knowing they are independent is what makes this fix safe: removing a false `moved_into_executed` does not disarm the flip case.
- `git diff --name-status` yields ONE path for `A`/`M`/`C` and TWO for `R`, which is why the parser has two branches (`:117-126`). The `A/M/C` branch's `old_path = None` is correct as a statement about rename SOURCE and wrong as a proxy for "was not previously here"; that conflation is the whole defect.
- `_finalize_evidence_ok` (`:152-174`) binds the journal to THIS transition by matching `journal["dest_path"]` against the staged path, and requires the phase to be a finalize-transaction phase. It is only ever consulted for a DETECTED transition, so this plan does not touch it.
- The journal genuinely is a transaction artifact deleted on success, and the module's docstring explains why the begin RECEIPT is deliberately not accepted as proof (the receipt carries the pending-time digest and is consumed only after the commit). Both facts are TRUE and are simply not the cause of case 2; do not "fix" them here.
- `tests/test_executed_transition_gate.py` builds real git repositories in a `TemporaryDirectory` and drives `GATE.check(self.root)` directly, with one test going end-to-end through the installed hook (`:183`). Extend that harness; do not add a mock-based test, since the defect lives in what git actually reports.
- Plan text for fixtures comes from a shared helper (`LT._completed_plan_text`), so a new test should reuse it rather than hand-writing plan bodies that could drift from the schema.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | CASE 1 IS ALREADY OWNED, so it is not graduated: approved plan `29wvmj` adds the merge-context detector and the in-tree finalize-evidence predicate, and installs the gate on `pre-merge-commit`. | `.aw/records/plans/pending/20260906-integpath-01-29wvmj-...ipd.md`, `- Status: approved`, E-01 through E-06 |
| F-2 | Case 2 REPRODUCES at HEAD: a plan committed in `executed/`, then a body-only edit and `git add`, gives `check()` rc 1 with "raw plan->executed transition (moved into executed/) with NO matching finalize evidence in .aw/state/". | measured in a throwaway repo at `8b4e1570` |
| F-3 | THE ITEM'S DIAGNOSIS OF CASE 2 IS WRONG, and the correction shrinks the fix from a durable-state redesign to one predicate. The cause is not journal deletion; it is that a plain `M` sets `old_path = None` and `moved_into_executed` reads that as "was not in executed/". | `executed_transition_gate.py:120-126` (the `A/M/C` branch), `:132-134` (the `or old_path is None` clause) |
| F-4 | git reports exactly `M<TAB><path>` for the case-2 edit, confirming the single-path shape that drives `old_path = None`. | measured `git diff --cached --name-status -M -- .aw/records/plans/` in the reproduction |
| F-5 | The discriminator the fix needs is available and already used elsewhere in the same function: for the case-2 edit the HEAD blob at the SAME path EXISTS, and `gained_executed` evaluates False. | measured via `_blob_at(root,'HEAD',path)` and `_has_executed_status` at `8b4e1570`; `head_text` already computed at `:136` |
| F-6 | The two firing conditions are independent and OR'd, so fixing the path test cannot disarm the status-flip refusal. | `executed_transition_gate.py:141` |
| F-7 | The in-place hand-edit shares case 2's git shape (`M`, one path), which is why E-02 exists as an explicit proof obligation rather than an assumption. | `tests/test_executed_transition_gate.py:96-107` |
| F-8 | Ten behaviors are already pinned by tests and give this change a dense regression fence. | `tests/test_executed_transition_gate.py:68`, `:75`, `:84`, `:96`, `:109`, `:122`, `:144`, `:163`, `:183`, `:201` |
| F-9 | The cost of the false positive is recorded and repeated, not hypothetical: both of the item's cases were resolved with `--no-verify` under maintainer authorization, and `29wvmj` records four more bypasses on the merge path. | backlog `gjadwm` (workaround section); `29wvmj` Concern (bypasses on `eyh1fu`, `txc9l1`, `uyeko5`, `eulhzt`) |
| F-10 | The item's option 4 anticipated this exact cause ("the staged-rename detection may be over-broad"), so this plan implements the item's own cheapest option and drops its options 1 and 3 as unnecessary for case 2. | backlog `gjadwm`, "WHAT TO SOLVE FOR" items 3 and 4 |

## Proposed changes (ordered, validatable)

1. Test whether the path was already under `executed/` at HEAD instead of inferring it from a missing rename source (E-01).
2. Prove the in-place status flip still refuses through `gained_executed` (E-02).
3. Preserve all ten pinned behaviors and the no-`- Id:` refusal, case by case (E-03).
4. Add regression tests for a body edit and a history edit to an already-executed plan (E-04).
5. Verify disjointness from approved plan `29wvmj` and comment the two concerns (E-05).

## Deferred / out of scope (with reason)

- CASE 1, THE MERGE CASE. Owned by APPROVED plan `29wvmj` (E-01/E-02/E-05/E-06). It is approved and will land before this plan runs, so implementing it here would be duplicated work against a sibling's declared scope.
- RETAINING A DURABLE FINALIZE COMPLETION RECORD (the item's option 3). Unnecessary once F-3 is accepted: case 2 needs no evidence at all, because no transition is occurring. It would also turn a transient transaction artifact into durable state needing its own lifecycle, in a `.aw/state/` tree that is separately the subject of relocation work.
- ACCEPTING THE BEGIN RECEIPT AS PROOF (the item's first candidate). The module's docstring gives a sound reason for refusing it (pending-time digest, consumed only after the commit), and this plan needs no new evidence path.
- MAKING THE HOOK ADVISORY, or moving enforcement wholly to `aw check`/`aw doctor` (the item's question 5). A real policy change about where enforcement lives, well beyond a false-positive fix, and it would weaken a gate the item explicitly says not to weaken.
- THE SIBLING RECEIPT/JOURNAL DEFECTS the item groups with this one: `xmqv5l` (begin freezes a whole-file digest) and `v880xk` (a stale frozen base makes scope-drift emit ~1000 findings). Both are separate open items outside this plan's ownership. The item's suggestion that the whole finalize-evidence model deserves one coherent review is reasonable and is NOT attempted here; F-3 shows case 2 does not need it.

## Scope check

- Over-scope: none. Both files in `Scope-Paths` are required by E-01 and E-04.
- Under-scope: the merge case, the three sibling defects, and the enforcement-point question are all left alone (see Deferred). No refusal message wording changes.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. Baseline on `main` is 1 failed, 5648 passed (the known `test_orchestrator_retirement` failure); judge on the DELTA, and expect additional environmental failures inside a lane worktree from tests that read live repo state.
- `python3 -m pytest tests/test_executed_transition_gate.py` for the focused surface: all ten existing tests plus the two new ones.
- The case-2 reproduction re-run by hand in a throwaway repo, before and after, with `check()`'s rc and messages pasted.
- If `29wvmj` has landed by execution time, run its tests too and paste the result (E-05).

## Spec / documentation sync

No `.spec.md` file governs this hook's detection logic, so none is edited and none is declared in `Scope-Paths`. `CONTRIBUTING.md` documents the hook and is deliberately NOT touched here: it is in `29wvmj`'s `Scope-Paths`, that plan is approved, and this change alters no documented behavior (a follow-up edit to an already-executed plan was never documented as gated). The hook's own module docstring describes what it detects and MUST be updated by E-01 to say that a plan already in `executed/` at HEAD is not a transition, so the code does not keep describing the over-broad rule it no longer implements.

## Open questions

### OQ-01: Should a follow-up edit to an already-executed plan be gated in some OTHER way?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: DEFERRED with a recommendation of NO, recorded because a reviewer could reasonably ask. There is a separate, legitimate concern that editing a plan already in `executed/` can rewrite history a gate previously validated, and the repository does care about that: the execution contract says to close a post-execution gap with a NEW corrective IPD rather than an in-place edit. But THIS hook is specifically the plan-to-executed TRANSITION gate, and widening it into a general "do not edit executed plans" rule would be a new policy with a much larger blast radius (every legitimate typo fix, every `aw ipd finalize` follow-up, every records reconciliation). If that policy is wanted it deserves its own item and its own rule name, not a side effect of a false-positive fix.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff` of the changed predicate, AND paste a hand-run reproduction in a throwaway repo showing BEFORE (rc 1 plus the "moved into executed/" message) and AFTER (rc 0, no messages) for a body-only edit to a plan committed in `executed/`. In the same session paste a `git mv` from `pending/` into `executed/` still returning rc 1, so the fix is shown to be narrow rather than a blanket exemption.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the passing result of `test_hand_edited_status_executed_without_receipt_refused` AND `git diff -- tests/test_executed_transition_gate.py` proving that test was not modified. Additionally paste a demonstration that the refusal comes from `gained_executed` and not the path test (for example an instrumented print, or the evaluated values of `moved_into_executed` and `gained_executed` for that fixture).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the full `python3 -m pytest tests/test_executed_transition_gate.py -v` output listing all ten pre-existing test names as passing, and paste a diff of the test file showing only ADDITIONS (no edits to existing cases). Separately demonstrate the no-readable-`- Id:` refusal still refuses.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the two new tests' source and names, their passing result, AND their FAILING output when run against pre-change code (stash the source fix and re-run). A test that passes both before and after validates nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: state and show whether `29wvmj` has landed (paste `git log --oneline -- agent_workflows/hooks/executed_transition_gate.py` and the file's current state around the merge detector). If landed, paste its tests passing alongside the new ones. Paste the added comment naming the two distinct concerns. Paste the bare `python3 -m pytest` summary line and compare it to the stated baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened. A reviewer should note that this plan graduates only PART of backlog item `gjadwm` and CORRECTS that item's stated cause for the part it does graduate; the evidence is in F-1 and F-3.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE THE REFLEXIVE HAZARD: this plan edits the very pre-commit gate that will run on its own commits, so verify with `git diff --cached --name-only` before each commit, re-verify after any failed hook, and never reach for `--no-verify` to land a change to the hook that exists to stop that habit. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
