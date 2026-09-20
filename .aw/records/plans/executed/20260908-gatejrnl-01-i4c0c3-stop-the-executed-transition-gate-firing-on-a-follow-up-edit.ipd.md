# IPD: Stop the executed-transition gate firing on a follow-up edit to a plan already in executed

- Date: 2026-09-08
- Kind: child
- Concern: The `ipd-executed-transition-gate` pre-commit hook refuses an ORDINARY EDIT to a plan that is already, legitimately, in `executed/`. The cause is a specific bug in the transition detector, not the journal-lifetime problem the backlog item hypothesized, and it is TWO conflations of the same root mistake rather than one. For a plain modification git reports status `M` with ONE path, and the detector's `A/M/C` branch sets `old_path = None` (`executed_transition_gate.py:133-138`). That single `None` then poisons BOTH firing conditions: `moved_into_executed` reads `old_path is None` as "the file was not previously in executed/" (`:146-148`), AND `head_text` is computed as `_blob_at(repo_root, "HEAD", old_path) if old_path else None` (`:150`), so `gained_executed` compares the staged content against NOTHING and is likewise True for any executed-status plan (`:151-153`). A file that has sat in `executed/` for weeks is therefore classified as a transition by every commit that touches it, on either condition independently, and since no finalize journal exists for a transition that is not happening, the gate refuses. Recovering from this requires `--no-verify`, and the item is explicit about the real cost: a gate that false-positives on correct behavior trains agents to bypass it.
- Scope: Fix the false positive only, in BOTH predicates, because fixing either one alone leaves the refusal firing through the other (MEASURED: see F-11). The single root fix is to read the HEAD blob at the path the file actually occupied (`old_path or new_path`) instead of only at a rename source, then derive both `was_in_executed_at_head` and `gained_executed` from it. Preserve every genuine refusal, including the in-place hand-edited `- Status: executed` flip, and BIND the exemption to the plan's `- Id:` so an already-executed path cannot be used as a shelter for substituted content. The merge case is NOT touched: it was owned by plan `29wvmj`, which is ALREADY EXECUTED and whose code is present in this file at HEAD.
- Scope-Paths: agent_workflows/hooks/executed_transition_gate.py, tests/test_executed_transition_gate.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: gatejrnl
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: i4c0c3
- From-Backlog: gjadwm
- Blocks-Release: next

## Workflow history
- 2026-09-20 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: i4c0c3 verified (set gatejrnl, attempt 1).
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-08 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review APPROVE WITH REVISIONS APPLIED; PR-801..PR-809. Readiness `go-pending-approval`. Reviewed at HEAD `f7962663`; `aw ipd lint --phase author` conformed clean before semantic review and `--phase review-finalize` after. THE REVIEW FOUND THE PLAN'S OWN FIX INSUFFICIENT AND UNSAFE, both by executing it rather than reading it. PR-801 (BLOCKER): E-01 as drafted does NOT fix the bug; patching only `moved_into_executed` leaves the case-2 edit refused at rc 1 with the reason merely changing to `gained '- Status: executed'`, because `head_text` is ALSO guarded on `old_path` and so `gained_executed` compares against nothing. E-01 now repairs both from one `head_path = old_path or new_path`. PR-802 (BLOCKER): the drafted fix OPENS A HOLE the current code lacks, letting a wholesale content substitution at an already-executed path commit at rc 0; new E-02 binds the exemption to `_plan_id_of(head_text) == plan_id`, measured rc 1 with it and rc 0 without. PR-803: the plan's F-5 asserted `gained_executed` evaluates False for case 2; it evaluates True, and that wrong measurement is exactly what hid PR-801. PR-804: `29wvmj` is EXECUTED, not approved-and-pending, and its code commit `bcd9755f` is an ancestor of the plan's own cited baseline `8b4e1570` by 16 commits, so every coordination and disjointness instruction was moot at authoring time; E-05 became E-06, which verifies against landed code and treats the 15 merge tests as a live regression surface. PR-805: the test fence is 27 tests in three classes, not ten, and every cited line number was stale. PR-806: the stated suite baseline (1 failed, 5648 passed, `test_orchestrator_retirement`) is wrong in count and in the named test; measured `1 failed, 5866 passed, 3 skipped, 2 xfailed` with the failure in `test_reporting_contract.py`. PR-807/808/809: added the uncovered in-`executed/` status-flip case, the `A`-into-`executed/` preservation proof, and the fixture rule that a test must COMMIT the executed state first or its setup is itself the transition. The full fix was applied to a scratch copy and measured: all 27 tests pass, case 2 returns rc 0, and the four preserved refusals return rc 1; the source tree was restored to HEAD. OQ-01 resolved: its in-scope half became E-02, its policy half stays deferred, and it is no longer left open.
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `gjadwm`, inheriting its `Blocks-Release: next` gate. THIS IS A NARROWING, AND IT ALSO CORRECTS THE ITEM'S DIAGNOSIS. The item reports TWO cases. CASE 1 (merging a lane-finalized plan) IS ALREADY OWNED by APPROVED plan `29wvmj` (Set `integpath`, Order 01, `From-Backlog: rnl3b7`), whose E-01 adds the merge-context detector via `git rev-parse --git-dir`, E-02 adds the in-tree finalize-evidence predicate accepting a `lifecycle(<id6>): finalize` commit reachable from the incoming side, E-03 preserves four refusal cases, E-04 makes the merge refusal actionable, E-05 tests through a real `git merge --no-ff --no-commit`, and E-06 installs the gate on `pre-merge-commit` too. That plan is approved and will land before this one runs, so case 1 is NOT graduated here and must NOT be re-implemented. CASE 2 (a follow-up commit to a plan already finalized in this tree) SURVIVES, and I reproduced it in a throwaway repo at HEAD `8b4e1570`: a plan committed in `executed/`, then a one-line body edit, `git add`, and `check()` returns rc 1 with "raw plan->executed transition (moved into executed/) with NO matching finalize evidence in .aw/state/". THE ITEM'S EXPLANATION FOR CASE 2 IS WRONG IN A WAY THAT MATTERS. It attributes case 2 to the journal being deleted on success, and therefore proposes retaining a durable completion record (its option 3) or accepting the begin receipt. Neither is needed. I traced the actual cause: `git diff --cached --name-status -M` reports `M<TAB><path>` for a plain edit, the detector's `A/M/C` branch assigns `old_path = None` (`executed_transition_gate.py:120-126`), and `moved_into_executed` is computed as `_EXECUTED_SEGMENT in ("/" + new_path) and (old_path is None or ...)` (`:132-134`), so `old_path is None` satisfies the second clause and the edit is classified as a move INTO `executed/`. Measured the discriminator that makes the fix safe: for that same edit the HEAD blob AT THE SAME PATH exists, and `gained_executed` is False (the HEAD content was already `executed`). So "was this path already in `executed/` at HEAD?" cleanly separates case 2 from every genuine transition, and the fix is one predicate rather than a new durable-state lifecycle. The item's own option 4 anticipated exactly this ("the staged-rename detection may be over-broad"); this plan implements that option and discards options 1 and 3 as unnecessary for case 2. The item's CONSTRAINT is honored: no refusal is weakened, and E-02 exists specifically because the in-place status flip shares case 2's `M`/`old_path is None` shape.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make an ordinary edit to an already-executed plan an ordinary commit. The gate should fire on a plan ENTERING `executed/`, not on every subsequent commit that touches a plan already there, so operators and agents stop being taught that `--no-verify` is routine.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: fix the over-broad transition detector

- [x] E-01 Fix the SHARED root cause in `_staged_plan_executed_transitions` (`agent_workflows/hooks/executed_transition_gate.py:110-162`): read the HEAD blob at the path the file ACTUALLY occupied at HEAD, and derive BOTH firing conditions from it. Today `head_text = _blob_at(repo_root, "HEAD", old_path) if old_path else None` (`:150`), so for a plain `M` (where `:133-138` sets `old_path = None`) the HEAD side is never read at all. Replace that with `head_path = old_path or new_path` and `head_text = _blob_at(repo_root, "HEAD", head_path)`, which is correct for BOTH branches: for an `R` git gives the rename source, and for an `A`/`M`/`C` the path is unchanged, so `new_path` IS where it was. Then express the path test as its actual question: `was_in_executed_at_head = head_text is not None and _EXECUTED_SEGMENT in ("/" + head_path)` and `moved_into_executed = _EXECUTED_SEGMENT in ("/" + new_path) and not was_in_executed_at_head`. THIS IS ONE FIX, NOT TWO, and it must be done as one: fixing only the path test leaves `gained_executed` firing on the identical input, so the refusal merely changes its message (MEASURED, F-11). Note what the `head_text is not None` clause preserves: a brand-new file ADDED directly at an `executed/` path (git code `A`, no HEAD blob) still has `was_in_executed_at_head` False and so still REFUSES (MEASURED, F-13).
  - Depends on: none
  - Expected outcome: the case-2 reproduction (a body-only edit to a plan committed in `executed/`) returns rc 0 with no messages; a `git mv` from `pending/` into `executed/` still returns rc 1 with "moved into executed/"; a plan ADDED straight into `executed/` still returns rc 1.
  - Execution state: performed

- [x] E-02 BIND THE NEW EXEMPTION TO THE PLAN'S `- Id:`, so being at an already-executed path does not become a shelter for arbitrary content. E-01 makes "this path held an executed plan at HEAD" sufficient to skip the gate, which introduces a hole the current code does not have: REPLACE the whole file at that path with a DIFFERENT plan (a different `- Id:`, `- Status: executed`) and it commits unchallenged, which is a raw plan->executed transition wearing an existing filename. MEASURED at HEAD: the substitution passes with rc 0 under the E-01-only fix, and refuses with rc 1 once the id is bound (F-12). Add the third clause: `and _plan_id_of(head_text) == plan_id`, where `plan_id` is the already-computed staged id (`:144`). A plan whose HEAD content had no readable id also fails this clause and is therefore gated, which is the correct fail-closed direction and consistent with the hook's existing no-`- Id:` refusal (`:302-306`).
  - Depends on: E-01
  - Expected outcome: a wholesale content substitution at an already-executed path returns rc 1, while the case-2 body edit still returns rc 0; both measured in the same session.
  - Execution state: performed

- [x] E-03 PROVE THE IN-PLACE STATUS FLIP STILL REFUSES, and note that the mechanism is NOT the one the pre-review draft of this plan assumed. A hand-edit rewriting `- Status: approved` to `- Status: executed` WITHOUT moving the file is reported as `M` with `old_path = None`, so it is removed from `moved_into_executed` by E-01 and must refuse through `gained_executed` instead. That works only BECAUSE E-01 also repairs `head_text`: with the old `if old_path else None` expression, `gained_executed` compared against nothing and was vacuously True for every executed plan (which is precisely the case-2 bug), whereas after E-01 it compares the staged content against the real HEAD content at the same path and is True exactly when the status genuinely changed. Verify the two conditions remain OR'd (`if moved_into_executed or gained_executed`, `:155`), then run `test_hand_edited_status_executed_without_receipt_refused` (`tests/test_executed_transition_gate.py:103-114`) and `test_hand_edit_outside_a_merge_still_refused` (`:424`), both of which pin this and must pass UNMODIFIED. ALSO cover the case neither existing test reaches: a plan sitting IN `executed/` at HEAD carrying a NON-executed status, flipped in place to executed. That must still refuse (MEASURED rc 1, F-14), and it is the case that proves the exemption is about the transition and not about the directory.
  - Depends on: E-01, E-02
  - Expected outcome: both existing hand-edit tests pass unmodified; the in-`executed/`-but-not-yet-executed status flip is demonstrated to return rc 1; the refusal is shown to originate from `gained_executed`.
  - Execution state: performed

- [x] E-04 Preserve every OTHER genuine refusal and the hook's no-op cases, checked case by case against the existing suite rather than by assertion. `tests/test_executed_transition_gate.py` holds TWENTY-SEVEN tests in three classes, not ten (the pre-review draft of this plan counted only `PreCommitExecutedGateTests` and predated `29wvmj` landing; MEASURED: `27 passed`, F-15), and ALL must still pass unmodified. In `PreCommitExecutedGateTests` (10): the three no-op/negative cases (`test_ordinary_commit_no_plan_transition_is_noop` `:75`, `test_nonterminal_plan_change_not_gated` `:82`, `test_prompt_executed_transition_not_gated` `:91`), the two refusals (`:103`, `test_git_mv_into_executed_without_receipt_refused` `:116`), the three journal-binding cases (`:129`, `:151`, `:170`), the installed-hook end-to-end case (`:190`), and `test_grandfathered_plan_without_finalize_is_refused` (`:208`). In `MergeAwareInTreeEvidenceTests` (15) THE WHOLE MERGE SURFACE IS NOW A LIVE REGRESSION SURFACE FOR THIS CHANGE, not a sibling's future work: those tests drive real `git merge` calls in which a plan arrives from a lane, and this plan alters the very predicate that decides whether that arrival is a transition, so they are the strongest evidence that the fix did not disarm the merge path. And in `PreCommitConfigStageRegistrationTests` (2) the config assertions. ALSO preserve the no-readable-`- Id:` refusal (`:461`). Do NOT change the refusal MESSAGE wording for any case that still refuses: operators and agents have learned it, and the merge-case tests assert on its exact substrings (`:444`, `:500`).
  - Depends on: E-01, E-02
  - Expected outcome: all 27 existing tests pass with NO edits to the test file's existing cases, demonstrated by a pasted run that shows the count.
  - Execution state: performed

### Task group 2: pin the fix and keep the merge path intact

- [x] E-05 Add the regression tests, built the way the existing suite builds fixtures so they compose rather than inventing a second harness. Use `PreCommitExecutedGateTests`' own helpers: `_write_plan(plan_id, ...)` (`tests/test_executed_transition_gate.py:56-67`), `_executed_dir()` (`:69-72`), `_commit_all` and `_stage` (`:36-42`). Note the fixture detail that decides whether these tests are honest: `LT._completed_plan_text` yields `- Status: approved`, so a test must write the plan INTO `executed/` with the status already replaced by `executed` and COMMIT that state first, otherwise the very first commit is itself the transition. Add FOUR tests: (a) a BODY-ONLY edit to an already-executed plan, asserting rc 0 and no messages; (b) an edit to that plan's `## Workflow history`, which is what a correction to a finalized plan actually touches and was case 2 in the field; (c) the E-02 hole, a wholesale content substitution with a DIFFERENT `- Id:` at an already-executed path, asserting rc 1; (d) the E-03 case, a plan already in `executed/` at HEAD whose non-executed status is flipped in place, asserting rc 1. Prove (a) and (b) FAIL against the pre-change code, and that they fail for the RIGHT reason (the message must contain "moved into executed/"), so a test that merely errors in setup is not mistaken for a reproduction.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: four new tests; (a) and (b) fail before the change with the "moved into executed/" refusal and pass after; (c) and (d) pass after and are demonstrated to be genuine refusals rather than vacuous passes.
  - Execution state: performed

- [x] E-06 Verify against the ALREADY-LANDED `29wvmj` rather than planning around it as future work, and comment the fixed predicate. `29wvmj` is NOT approved-and-pending: it is EXECUTED, its plan sits at `.aw/records/plans/executed/20260906-integpath-01-29wvmj-...ipd.md` with `- Status: executed`, and its code commit `bcd9755f` ("fix(hooks): accept a finalized lane merge in the executed-transition gate (29wvmj)") is an ancestor of HEAD (F-16). Two consequences the executor must act on. FIRST, there is no coordination question and no possibility of a collision with a sibling in flight; the merge-context detector (`_merge_incoming_commits` `:206`), the in-tree predicate (`_intree_finalize_evidence_ok` `:261`), and the merge-case refusal (`:314-326`) are all present in the file you are editing, and its 15 merge tests are part of the run E-04 requires. SECOND, the interaction to check is real and specific rather than a formality: `check()` computes merge state and evidence only for transitions the detector RETURNED (`:292-298`), so narrowing the detector narrows what the merge path ever sees. Confirm by running the merge tests that a lane legitimately carrying a plan into `executed/` is still DETECTED as a transition (it must be, since at HEAD the plan was in `pending/`, so `was_in_executed_at_head` is False), and that the accepted case is accepted via evidence rather than via the new exemption. Add a code comment at the predicate stating the two distinct concerns it now separates (did this file ENTER executed/ in this commit, versus was it merely EDITED there) so a future reader does not collapse one back into the other.
  - Depends on: E-05
  - Expected outcome: a stated account, with pasted `git log`/`git merge-base` evidence, that `29wvmj` has already landed; the 15 merge tests pass; a demonstration that a lane-carried plan is still detected as a transition and accepted only on evidence; the comment is in place.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The hook is deliberately LOCAL best-effort prevention, not a security boundary: it is skippable with `--no-verify` and not cloned by default, and the portable authority is the `aw check`/`aw doctor` backstop. That framing is what makes a false positive expensive rather than merely annoying, since the mitigation an operator reaches for is the bypass.
- Detection compares the STAGED index (`:0:`) against HEAD via `git diff --cached --name-status -M` and fires on either of two independent conditions OR'd together (`:155`): `moved_into_executed` (a rename into `executed/`) or `gained_executed` (a status flip). Their independence cuts BOTH ways, and the draft of this plan got the direction wrong: it correctly noted that fixing the path test cannot disarm the flip case, but missed that this also means fixing the path test cannot SILENCE the flip case when the flip test is itself broken on the same input (F-11).
- `git diff --name-status` yields ONE path for `A`/`M`/`C` and TWO for `R`, which is why the parser has two branches (`:131-138`). The `A/M/C` branch's `old_path = None` is correct as a statement about rename SOURCE and wrong as a proxy for "was not previously here". Because `head_text` is ALSO guarded on `old_path` (`:150`), that one conflation propagates into both predicates; it is one defect with two symptoms, not two defects.
- `_finalize_evidence_ok` (`:165-186`) binds the journal to THIS transition by matching `journal["dest_path"]` against the staged path, and requires the phase to be a finalize-transaction phase. It is only ever consulted for a DETECTED transition, so this plan does not touch it. The same is true of the merge-aware second accepting path (`_merge_incoming_commits` `:206`, `_intree_finalize_evidence_ok` `:261`), which is why narrowing the detector is the only change needed and also why the merge tests are a live regression surface for it.
- The journal genuinely is a transaction artifact deleted on success, and the module's docstring explains why the begin RECEIPT is deliberately not accepted as proof (the receipt carries the pending-time digest and is consumed only after the commit). Both facts are TRUE and are simply not the cause of case 2; do not "fix" them here.
- `tests/test_executed_transition_gate.py` builds real git repositories in a `TemporaryDirectory` and drives `GATE.check(self.root)` directly, with tests going end-to-end through the installed hook (`:190`, `:531`, `:548`) and through real `git merge` invocations. Extend that harness; do not add a mock-based test, since the defect lives in what git actually reports. The merge class states this rule explicitly at `:221-227` ("a mocked fixture would pass against the very bug it is meant to detect").
- Plan text for fixtures comes from a shared helper (`LT._completed_plan_text`), so a new test should reuse it rather than hand-writing plan bodies that could drift from the schema. It emits `- Status: approved`, so a fixture that needs an ALREADY-EXECUTED starting state must replace the status AND commit that state before making the edit under test; otherwise the setup commit is itself the transition and the test proves nothing.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | CASE 1 IS ALREADY DONE, not merely owned: plan `29wvmj` is EXECUTED and its code is in the file this plan edits. Superseded in part by F-16, which corrects this row's original claim that it was `approved` and pending. | `.aw/records/plans/executed/20260906-integpath-01-29wvmj-...ipd.md:12` `- Status: executed`; commit `bcd9755f` |
| F-2 | Case 2 REPRODUCES at HEAD: a plan committed in `executed/`, then a body-only edit and `git add`, gives `check()` rc 1 with "raw plan->executed transition (moved into executed/) with NO matching finalize evidence in .aw/state/". | re-measured at review time on HEAD `f7962663` in a throwaway repo; `_staged_plan_executed_transitions` returned one tuple with reason `moved into executed/` |
| F-3 | THE ITEM'S DIAGNOSIS OF CASE 2 IS WRONG, and the correction shrinks the fix from a durable-state redesign to one predicate pair. The cause is not journal deletion; it is that a plain `M` sets `old_path = None`, which then corrupts BOTH firing conditions. | `executed_transition_gate.py:133-138` (the `A/M/C` branch), `:146-148` (the `or old_path is None` clause), `:150` (`head_text` guarded on `old_path`) |
| F-4 | git reports exactly `M<TAB><path>` for the case-2 edit, confirming the single-path shape that drives `old_path = None`. | re-measured `git diff --cached --name-status -M` in the reproduction |
| F-5 | CORRECTED BY F-11. The pre-review draft claimed `gained_executed` "evaluates False" for the case-2 edit. It evaluates TRUE, because `head_text` is `None` for an `M` and `not _has_executed_status(None)` is True. The HEAD blob at the same path does exist and does carry the executed status, but the CODE never reads it. | measured: `_has_executed_status(staged)` True, `_has_executed_status(HEAD-at-same-path)` True, code-computed `gained_executed` True |
| F-6 | The two firing conditions are independent and OR'd, which is why BOTH must be fixed: independence means fixing one cannot disarm the other, and equally means fixing one cannot silence the other. | `executed_transition_gate.py:155` |
| F-7 | The in-place hand-edit shares case 2's git shape (`M`, one path), which is why E-03 exists as an explicit proof obligation rather than an assumption. | `tests/test_executed_transition_gate.py:103-114` |
| F-8 | TWENTY-SEVEN behaviors are pinned by tests, in three classes, giving this change a much denser regression fence than the ten the draft counted. | `python3 -m pytest tests/test_executed_transition_gate.py` -> `27 passed`; classes at `:45`, `:221`, `:580` |
| F-9 | The cost of the false positive is recorded and repeated, not hypothetical: both of the item's cases were resolved with `--no-verify` under maintainer authorization, and `29wvmj` records four more bypasses on the merge path. | backlog `gjadwm` (workaround section); `29wvmj` Concern (bypasses on `eyh1fu`, `txc9l1`, `uyeko5`, `eulhzt`) |
| F-10 | The item's option 4 anticipated this exact cause ("the staged-rename detection may be over-broad"), so this plan implements the item's own cheapest option and drops its options 1 and 3 as unnecessary for case 2. | backlog `gjadwm`, "WHAT TO SOLVE FOR" items 3 and 4 |
| F-11 | THE PLAN'S ORIGINAL E-01 DOES NOT FIX THE BUG. Patching only `moved_into_executed` (using the same-path HEAD blob as the discriminator, exactly as the draft specified) leaves the case-2 edit REFUSED at rc 1; the reason string merely changes from `moved into executed/` to `gained '- Status: executed'`. This is why E-01 now repairs `head_text` as well. | executed the draft's own patch against the reproduction: `transitions` returned one tuple, reason `gained '- Status: executed'`, `check()` rc 1 |
| F-12 | THE FIX AS DRAFTED OPENS A HOLE THE CURRENT CODE DOES NOT HAVE. With the path-based exemption alone, replacing an already-executed plan's file wholesale with a DIFFERENT plan (different `- Id:`, `- Status: executed`) commits at rc 0. Binding the exemption to `_plan_id_of(head_text) == plan_id` refuses it at rc 1 while the case-2 body edit still passes at rc 0. | measured both variants against a two-plan fixture; hence E-02 |
| F-13 | The `head_text is not None` clause is load-bearing, not defensive dressing: a plan ADDED straight into `executed/` (git code `A`, no HEAD blob) still refuses at rc 1 under the full fix, so the fix does not exempt new arrivals. | measured in a separate fixture with the full fix applied |
| F-14 | The full fix (E-01 plus E-02) passes ALL 27 existing tests with no test-file edits, including the 15 merge tests, and an in-`executed/`-but-not-yet-executed status flip still refuses at rc 1. | `27 passed in 3.13s` with the patched module in place; source restored to HEAD afterwards |
| F-15 | The draft's test-count and line numbers were stale (ten tests, `:68`..`:201`) because they predate `29wvmj` landing, which added `MergeAwareInTreeEvidenceTests` and `PreCommitConfigStageRegistrationTests` and shifted every line. E-04 is re-baselined to the current file. | `tests/test_executed_transition_gate.py` at HEAD: 616 lines, 3 classes, 27 tests |
| F-16 | `29wvmj` LANDED BEFORE THIS PLAN WAS AUTHORED, so every statement about it being approved and about coordinating with a sibling in flight was already false at authoring time. Its code commit is an ancestor of HEAD, and the plan's own cited baseline commit `8b4e1570` is 16 commits AFTER it. | `git merge-base --is-ancestor bcd9755f HEAD` -> 0; `git rev-list --count bcd9755f..8b4e1570` -> 16 |
| F-17 | The plan's stated suite baseline is wrong in both the count and the named failing test. Measured bare `python3 -m pytest` on HEAD `f7962663`: `1 failed, 5866 passed, 3 skipped, 2 xfailed`, and the failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` (untracked `opencode-recovery/` files), NOT `test_orchestrator_retirement`. | pasted summary line from the review run |

## Proposed changes (ordered, validatable)

1. Read the HEAD blob at the path the file actually occupied and derive BOTH firing conditions from it (E-01).
2. Bind the new exemption to the plan's `- Id:` so an executed path is not a shelter for substituted content (E-02).
3. Prove the in-place status flip still refuses, through the now-correct `gained_executed` (E-03).
4. Preserve all 27 pinned behaviors, including the 15 merge tests, and the no-`- Id:` refusal (E-04).
5. Add four regression tests: body edit, history edit, content substitution, in-place flip inside `executed/` (E-05).
6. Verify against the already-landed `29wvmj` and comment the two concerns at the predicate (E-06).

## Deferred / out of scope (with reason)

- CASE 1, THE MERGE CASE. ALREADY IMPLEMENTED AND EXECUTED by plan `29wvmj`, whose code commit `bcd9755f` is an ancestor of HEAD (F-16). Nothing about it is deferred and nothing about it is a sibling's pending work; it is existing behavior this plan must not break, which is why its 15 tests are inside E-04's required run rather than in a coordination note.
- RETAINING A DURABLE FINALIZE COMPLETION RECORD (the item's option 3). Unnecessary once F-3 is accepted: case 2 needs no evidence at all, because no transition is occurring. It would also turn a transient transaction artifact into durable state needing its own lifecycle, in a `.aw/state/` tree that is separately the subject of relocation work.
- ACCEPTING THE BEGIN RECEIPT AS PROOF (the item's first candidate). The module's docstring gives a sound reason for refusing it (pending-time digest, consumed only after the commit), and this plan needs no new evidence path.
- MAKING THE HOOK ADVISORY, or moving enforcement wholly to `aw check`/`aw doctor` (the item's question 5). A real policy change about where enforcement lives, well beyond a false-positive fix, and it would weaken a gate the item explicitly says not to weaken.
- THE SIBLING RECEIPT/JOURNAL DEFECTS the item groups with this one: `xmqv5l` (begin freezes a whole-file digest) and `v880xk` (a stale frozen base makes scope-drift emit ~1000 findings). Both are separate open items outside this plan's ownership. The item's suggestion that the whole finalize-evidence model deserves one coherent review is reasonable and is NOT attempted here; F-3 shows case 2 does not need it.

## Scope check

- Over-scope: none. Both files in `Scope-Paths` are required: the module by E-01/E-02/E-06, the test file by E-05.
- Under-scope: closed by review. E-02 was ADDED because the fix as drafted opened a substitution hole (F-12), and E-03 gained the in-`executed/` status-flip case that no existing test covers (F-14). The three sibling defects and the enforcement-point question remain deliberately out (see Deferred). No refusal message wording changes.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. MEASURED baseline at review time on HEAD `f7962663`: `1 failed, 5866 passed, 3 skipped, 2 xfailed`, the one failure being `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, caused by untracked `opencode-recovery/` files in the working tree and unrelated to this change (F-17). Judge on the DELTA against that, re-baseline if your own tree differs, and expect additional environmental failures inside a lane worktree from tests that read live repo state.
- `python3 -m pytest tests/test_executed_transition_gate.py` for the focused surface: all 27 existing tests plus the four new ones, so 31. Paste the count, since a run that silently collected fewer tests is the failure mode this check exists to catch.
- The case-2 reproduction re-run by hand in a throwaway repo, before and after, with `check()`'s rc and messages pasted, plus the substitution case from E-02 and the `A`-into-`executed/` case from F-13 in the same session.
- The 15 merge tests specifically (`MergeAwareInTreeEvidenceTests`), named and pasted, since they are the strongest evidence the narrowed detector did not disarm the accepting path `29wvmj` added (E-06).

## Spec / documentation sync

No `.spec.md` file governs this hook's detection logic, so none is edited and none is declared in `Scope-Paths`. `CONTRIBUTING.md` documents the hook and is deliberately NOT touched here, though the reason in the draft was wrong: `29wvmj` is executed, so its `Scope-Paths` no longer reserve anything. The real reason stands on its own: this change alters no DOCUMENTED behavior, because a follow-up edit to an already-executed plan was never documented as gated (it was a defect, not a rule). The hook's own module docstring at `:1-38` DOES describe the detection rule and MUST be updated by E-01/E-02 to state that a plan already in `executed/` at HEAD under the SAME `- Id:` is not a transition, so the code does not keep describing the over-broad rule it no longer implements.

## Open questions

### OQ-01: Should a follow-up edit to an already-executed plan be gated in some OTHER way?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED at review as NO for the general policy, with the narrow part of the concern brought INTO scope as E-02. The concern is legitimate: editing a plan already in `executed/` can rewrite history a gate previously validated, and the execution contract says to close a post-execution gap with a NEW corrective IPD rather than an in-place edit. Review split it in two. The part that is genuinely THIS gate's business is content SUBSTITUTION, because swapping a different plan into an executed filename IS a raw plan->executed transition and the draft's fix would have permitted it (F-12); that is now E-02 and is enforced by the `- Id:` binding. The part that remains out is the general "do not edit executed plans" rule, which would be a new policy with a much larger blast radius (every legitimate typo fix, every records reconciliation) and deserves its own item and rule name rather than arriving as a side effect of a false-positive fix. Non-blocking: the in-scope half is implemented, and the deferred half changes nothing about whether this plan is safe to run.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the `git diff` of the changed lines, which MUST show BOTH the `head_path = old_path or new_path` / `head_text` repair and the rewritten `moved_into_executed`; a diff touching only the path predicate means E-01 was done as originally drafted and is INCOMPLETE (F-11). Paste a hand-run reproduction in a throwaway repo showing BEFORE (rc 1 with the "moved into executed/" message) and AFTER (rc 0, no messages) for a body-only edit to a plan committed in `executed/`. In the SAME session paste (a) a `git mv` from `pending/` into `executed/` still returning rc 1, and (b) a plan ADDED straight into `executed/` still returning rc 1, so the fix is shown to be narrow rather than a blanket exemption.
  - Observed evidence: BOTH halves of the repair are in the diff (`git diff -- agent_workflows/hooks/executed_transition_gate.py`), so this is not the drafted path-only patch:

    ```diff
    -        moved_into_executed = _EXECUTED_SEGMENT in ("/" + new_path) and (
    -            old_path is None or _EXECUTED_SEGMENT not in ("/" + old_path)
    +        head_path = old_path or new_path
    +        head_text = _blob_at(repo_root, "HEAD", head_path)
    +        was_in_executed_at_head = head_text is not None and _EXECUTED_SEGMENT in (
    +            "/" + head_path
    +        )
    +        same_plan_at_head = plan_id is not None and _plan_id_of(head_text) == plan_id
    +        moved_into_executed = _EXECUTED_SEGMENT in ("/" + new_path) and not (
    +            was_in_executed_at_head and same_plan_at_head
         )
    -        # A status flip: staged content is executed but the HEAD content at the OLD path was not.
    -        head_text = _blob_at(repo_root, "HEAD", old_path) if old_path else None
    ```

    Hand reproduction, one harness run against two pinned module copies (the harness prints WHICH module it imported, because a bare `python3 script.py` silently picks up an installed copy from another checkout; see DECISION 03-i4c0c3-D1). BEFORE = the HEAD copy extracted with `git archive HEAD agent_workflows`, AFTER = this lane's working tree:

    ```text
    ############ BEFORE  gate module under test: .../attempt-1/head-pkg/agent_workflows/hooks/executed_transition_gate.py
    --- CASE a body-only edit to an already-executed plan
        git diff --cached --name-status -M:  M  .aw/records/plans/executed/20260908-demo-01-abc123-demo.ipd.md
        _staged_plan_executed_transitions -> [('....ipd.md', 'abc123', 'moved into executed/')]
        check() rc=1 messages=['... (abc123): raw plan->executed transition (moved into executed/) with NO matching finalize evidence in .aw/state/. ...']
    --- CASE mv git mv pending/ -> executed/ (must still REFUSE)
        git diff --cached --name-status -M:  R092  .aw/records/plans/pending/...  .aw/records/plans/executed/...
        check() rc=1 messages=['... (moved into executed/) ...']
    --- CASE add plan ADDED straight into executed/ (must still REFUSE)
        git diff --cached --name-status -M:  A  .aw/records/plans/executed/20260908-demo-01-abc123-demo.ipd.md
        check() rc=1 messages=['... (moved into executed/) ...']

    ############ AFTER   gate module under test: .../.aw/worktrees/i4c0c3/agent_workflows/hooks/executed_transition_gate.py
    --- CASE a body-only edit to an already-executed plan
        _staged_plan_executed_transitions -> []
        check() rc=0 messages=[]
    --- CASE b workflow-history edit to an already-executed plan
        _staged_plan_executed_transitions -> []
        check() rc=0 messages=[]
    --- CASE mv git mv pending/ -> executed/ (must still REFUSE)
        _staged_plan_executed_transitions -> [('....ipd.md', 'abc123', 'moved into executed/')]
        check() rc=1 messages=['... (moved into executed/) ...']
    --- CASE add plan ADDED straight into executed/ (must still REFUSE)
        git diff --cached --name-status -M:  A  .aw/records/plans/executed/20260908-demo-01-abc123-demo.ipd.md
        _staged_plan_executed_transitions -> [('....ipd.md', 'abc123', 'moved into executed/')]
        check() rc=1 messages=['... (moved into executed/) ...']
    ```

    F-11 INDEPENDENTLY RE-MEASURED, because it is the finding that decides whether E-01 is complete. A third module copy was patched with the DRAFT's path-only fix (the path predicate repaired, `head_text` left guarded on `old_path`) and the case-2 edit is STILL REFUSED, the reason merely changing:

    ```text
    gate module under test: .../attempt-1/draftE01-pkg/agent_workflows/hooks/executed_transition_gate.py
    --- CASE a body-only edit to an already-executed plan
        _staged_plan_executed_transitions -> [('....ipd.md', 'abc123', "gained '- Status: executed'")]
        check() rc=1 messages=["... raw plan->executed transition (gained '- Status: executed') with NO matching finalize evidence ..."]
    ```

    F-13 holds: the `A`-into-`executed/` case above refuses under the FULL fix, so the exemption is not a blanket one. Harness and captured transcripts: `.aw/state/lane-submissions/run-20260920T041049Z-2017708/03-i4c0c3/attempt-1/repro_i4c0c3.py` (untracked lane submission).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the id-binding clause as it appears in the code, and paste a measured demonstration of the hole and its closure: the same content-substitution fixture (an already-executed path overwritten with a different `- Id:` and `- Status: executed`) returning rc 0 WITHOUT the clause and rc 1 WITH it, alongside the case-2 body edit returning rc 0 in both. Both numbers from one session. Asserting the clause is present without the rc-0 half does not validate this item, because the rc-0 half is the proof the hole was real.
  - Observed evidence: the clause as shipped, in `_staged_plan_executed_transitions`:

    ```python
    same_plan_at_head = plan_id is not None and _plan_id_of(head_text) == plan_id
    moved_into_executed = _EXECUTED_SEGMENT in ("/" + new_path) and not (
        was_in_executed_at_head and same_plan_at_head
    )
    ```

    Note the `plan_id is not None` guard: without it, a staged plan with no readable id and a HEAD blob with none either would make `None == None` an identity MATCH and exempt the very case the hook refuses at `:314-319`. The hole and its closure, measured in ONE session by running the same harness against two module copies differing ONLY in that clause (the variant is the shipped file with the clause deleted):

    ```text
    === E-01 ONLY (no id binding): substitution + case-a
    gate module under test: .../attempt-1/e01only-pkg/agent_workflows/hooks/executed_transition_gate.py
    --- CASE sub content substitution (different - Id:) at an executed path (must REFUSE)
        check() rc=0 messages=[]          <-- THE HOLE: a raw plan->executed transition commits unchallenged
    --- CASE a body-only edit to an already-executed plan
        check() rc=0 messages=[]

    === WITH THE ID BINDING (shipped)
    gate module under test: .../.aw/worktrees/i4c0c3/agent_workflows/hooks/executed_transition_gate.py
    --- CASE sub content substitution (different - Id:) at an executed path (must REFUSE)
        _staged_plan_executed_transitions -> [('....ipd.md', 'zzz999', 'moved into executed/')]
        check() rc=1 messages=['... (zzz999): raw plan->executed transition (moved into executed/) with NO matching finalize evidence in .aw/state/. ...']
    --- CASE a body-only edit to an already-executed plan
        check() rc=0 messages=[]          <-- the false positive stays fixed
    ```

    The refusal names `zzz999`, the SUBSTITUTED plan's id, which is the actionable identification: it tells the operator which plan is arriving without a finalize. F-12 is therefore confirmed as measured rather than accepted on the review's word.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the passing results of `test_hand_edited_status_executed_without_receipt_refused` and `test_hand_edit_outside_a_merge_still_refused`, AND `git diff -- tests/test_executed_transition_gate.py` proving neither was modified. Paste the evaluated values of `moved_into_executed` and `gained_executed` for the hand-edit fixture, showing the refusal originates from `gained_executed`. Paste the in-`executed/`-but-not-yet-executed flip returning rc 1 with its message.
  - Observed evidence: THE TWO NAMED TESTS NO LONGER EXIST AS FUNCTIONS, and the substance they pinned does. Commit `75b90271` ("test: tabulate eleven more suites (385 -> 160 tests)") landed AFTER this plan's review and converted both into ROWS of the two decision tables; see DECISION 03-i4c0c3-D2. Their successors are the row `"a hand-edited `- Status: executed` in place, no journal"` (`PreCommitExecutedGateTests.SITUATIONS`, asserting `REASON_STATUS_FLIP` and forbidding the merge wording) and the row `"a hand-edited status flip OUTSIDE any merge"` (`MergeAwareInTreeEvidenceTests.MERGE_DECISIONS`). Both pass, named individually:

    ```text
    === MergeAwareInTreeEvidenceTests.MERGE_DECISIONS (`check` given merge state)
      [PASS] a hand-edited status flip OUTSIDE any merge
               want_rc=1 got_rc=1 missing=[] leaked=[]
      [PASS] a `git mv` into executed/ OUTSIDE any merge
               want_rc=1 got_rc=1 missing=[] leaked=[]
    ```

    `PreCommitExecutedGateTests`' whole table (which contains the in-place hand-edit row) passes: `1 passed, 5 deselected` for `-k test_each_staged_situation`, and the full file is `6 passed` (V-04). NEITHER PRE-EXISTING CASE WAS MODIFIED: `git diff -- tests/test_executed_transition_gate.py | grep -cE '^-[^-]'` returns `0`, i.e. the diff REMOVES no line at all and is additions-only.

    The two predicates evaluated by hand from the same git evidence the gate reads, for both flip fixtures:

    ```text
    gate module: .../.aw/worktrees/i4c0c3/agent_workflows/hooks/executed_transition_gate.py
      hand-edit flip in PENDING (the `_flip_status_in_place` fixture)
        git code=M old=None new='.aw/records/plans/pending/20260824-demo-01-abc123-demo.ipd.md'
        was_in_executed_at_head=False same_plan_at_head=True
        moved_into_executed=False  gained_executed=True
        check() rc=1
        message: ... (abc123): raw plan->executed transition (gained '- Status: executed') with NO matching finalize evidence in .aw/state/. ...

      flip of a plan ALREADY IN executed/ but not yet executed (new row d)
        git code=M old=None new='.aw/records/plans/executed/20260824-demo-01-abc123-demo.ipd.md'
        was_in_executed_at_head=True same_plan_at_head=True
        moved_into_executed=False  gained_executed=True
        check() rc=1
        message: ... (abc123): raw plan->executed transition (gained '- Status: executed') with NO matching finalize evidence in .aw/state/. ...
    ```

    So the refusal originates from `gained_executed` in BOTH, with `moved_into_executed` now False, exactly as E-03 predicts; the second row is the case that proves the exemption is about the TRANSITION and not the directory (`was_in_executed_at_head=True` yet still refused). The two conditions remain OR'd (`if moved_into_executed or gained_executed:`, unchanged by this plan). NO WORDING CHANGED for either: the pending flip reported `gained '- Status: executed'` at HEAD too, verified by loading the HEAD module copy under a distinct name and running the same fixture (`HEAD gate, pending hand-edit flip -> [(..., 'abc123', "gained '- Status: executed'")]`, and `HEAD gate, git mv into executed/ -> [(..., 'abc123', 'moved into executed/')]`).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `python3 -m pytest tests/test_executed_transition_gate.py -v` output listing every pre-existing test name as passing and showing a total of 31 (27 existing plus 4 new); a count below 31 means tests were lost or not collected. Paste a diff of the test file showing only ADDITIONS, with no edits to existing cases. Separately demonstrate the no-readable-`- Id:` refusal still refuses.
  - Observed evidence: THE EXPECTED COUNT OF 31 IS UNREACHABLE AND ITS PURPOSE IS SERVED A DIFFERENT WAY; see DECISION 03-i4c0c3-D2. Commit `75b90271` re-tabulated this file after review, so the 27 tests are now 29 TABLE ROWS plus one non-row test inside 6 pytest test functions, and a row is not separately collectable. The check the item wants (nothing lost, nothing uncollected) is therefore made on ROWS, counted from the data rather than asserted: 11 + 4 + 7 + 4 + 3 = 29 rows at HEAD, 33 after this plan adds 4, with 30 -> 34 behaviours counting the non-row test.

    ```text
    $ python3 -m pytest tests/test_executed_transition_gate.py -o addopts="" -v
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: <repo>/.aw/worktrees/i4c0c3
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collected 6 items

    tests/test_executed_transition_gate.py::PreCommitConfigStageRegistrationTests::test_both_git_stages_are_registered_with_only_the_gate_at_merge_time PASSED [ 16%]
    tests/test_executed_transition_gate.py::PreCommitExecutedGateTests::test_each_staged_situation_gets_its_own_verdict_and_reason PASSED [ 33%]
    tests/test_executed_transition_gate.py::PreCommitExecutedGateTests::test_real_finalize_own_commit_passes_via_installed_hook PASSED [ 50%]
    tests/test_executed_transition_gate.py::MergeAwareInTreeEvidenceTests::test_the_merge_detector_reports_the_incoming_side_in_every_state PASSED [ 66%]
    tests/test_executed_transition_gate.py::MergeAwareInTreeEvidenceTests::test_merge_state_never_becomes_a_blanket_exemption PASSED [ 83%]
    tests/test_executed_transition_gate.py::MergeAwareInTreeEvidenceTests::test_git_itself_enforces_the_gate_at_both_merge_stages PASSED [100%]

    ============================== 6 passed in 5.17s ===============================
    ```

    ROW COUNT, read off the tables themselves so it cannot drift from the file:

    ```text
    PreCommitExecutedGateTests.SITUATIONS:                 15   (11 at HEAD + 4 added here)
    MergeAwareInTreeEvidenceTests.DETECTOR_STATES:          4
    MergeAwareInTreeEvidenceTests.MERGE_DECISIONS:          7
    MergeAwareInTreeEvidenceTests.INSTALLED_HOOK_RUNS:      4
    PreCommitConfigStageRegistrationTests.REGISTRATIONS:    3
    total rows: 33  (+1 non-row test) = 34 behaviours pinned; HEAD was 29 rows / 30 behaviours
    ```

    Every pre-existing row passes individually and by name; all 15 merge rows are enumerated under V-06, and the 11 pre-existing `SITUATIONS` rows pass inside the table run above (a failing row would be NAMED in the assertion message, as demonstrated in V-05 where exactly the intended rows failed and no other). ADDITIONS ONLY: `git diff -- tests/test_executed_transition_gate.py | grep -cE '^-[^-]'` -> `0`, so no existing case was edited or deleted.

    The no-readable-`- Id:` refusal still refuses, in BOTH directions:

    ```text
    row 'a plan with no readable `- Id:`, during a merge' -> rc=1
      message: ....ipd.md: this plan is being moved to executed (moved into executed/) but has no readable '- Id:' handle to verify a finalize receipt against; run `aw ipd finalize` instead.

    edit to an already-executed plan that has NO `- Id:` on EITHER side (not a merge) -> rc=1
      message: ....ipd.md: this plan is being moved to executed (moved into executed/) but has no readable '- Id:' handle ...
    ```

    That second case is the one the `plan_id is not None` guard exists for: without it `_plan_id_of(None-ish) == None` would read as an identity match and EXEMPT an id-less plan, which is the fail-open direction. No refusal message wording changed for any case that still refuses (verified against the HEAD module copy under V-03).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste all four new tests' source and names, their passing result, AND for (a) and (b) their FAILING output when run against pre-change code (stash the source fix and re-run), including the assertion text showing the failure was the "moved into executed/" refusal rather than a setup error. For (c) and (d) show the assertion is on rc 1 with a real refusal message. A test that passes both before and after validates nothing.
  - Observed evidence: the four cases are ROWS of `PreCommitExecutedGateTests.SITUATIONS` (D-2), added with their `why` prose and their fixtures. Names and assertions as written:

    ```python
    ("a BODY-ONLY edit to a plan already committed in executed/",
     lambda self: self._edit_already_executed_plan("body"), None, 0, (), (), ...),
    ("an edit to an already-executed plan's `## Workflow history`",
     lambda self: self._edit_already_executed_plan("history"), None, 0, (), (), ...),
    ("a WHOLESALE content substitution (different `- Id:`) at an already-executed path",
     lambda self: self._substitute_plan_at_executed_path(), None, 1,
     ("zzz999", "aw ipd finalize", REASON_MOVED), (MERGE_WORDING,), ...),
    ("a plan ALREADY IN executed/ at HEAD but NOT yet executed, flipped in place",
     lambda self: self._flip_status_inside_executed(), None, 1,
     ("abc123", "aw ipd finalize", REASON_STATUS_FLIP), (MERGE_WORDING,), ...),
    ```

    So (c) and (d) assert rc 1 AND a real refusal message: (c) must name the substituted id `zzz999`, the remedy, and the `moved into executed/` reason; (d) must name `abc123`, the remedy, and the `gained '- Status: executed'` reason; both forbid the merge wording, since neither is a merge. The fixtures COMMIT the executed state first (`_commit_plan_already_executed`), whose docstring records why: `LT._completed_plan_text` yields `- Status: approved`, so a fixture that staged without committing would make its own setup the transition and prove nothing about a follow-up edit. `_flip_status_inside_executed` additionally asserts its precondition (`- Status: approved` present at HEAD) so a fixture drift cannot turn it into a vacuous pass.

    ALL FOUR PASS after the change (the table run in V-04: `6 passed`). AGAINST PRE-CHANGE CODE, with the module restored to HEAD and the test file kept, rows (a), (b) and (d) FAIL, each for the right reason and none in setup:

    ```text
    $ python3 -m pytest tests/test_executed_transition_gate.py -o addopts="" -q -k test_each_staged_situation
    E   AssertionError: ... the gate misjudged 3 of 15 staged situations.
    E     a BODY-ONLY edit to a plan already committed in executed/:
    E       - expected exit code 0, got 1 with messages ['.aw/records/plans/executed/20260824-demo-01-abc123-demo.ipd.md (abc123): raw plan->executed transition (moved into executed/) with NO matching finalize evidence in .aw/state/. ...']
    E       - an accepted situation must report NOTHING, got [... (moved into executed/) ...]
    E     an edit to an already-executed plan's `## Workflow history`:
    E       - expected exit code 0, got 1 with messages [... raw plan->executed transition (moved into executed/) ...]
    E     a plan ALREADY IN executed/ at HEAD but NOT yet executed, flipped in place:
    E       - the refusal must state ["gained '- Status: executed'"]; it said '... raw plan->executed transition (moved into executed/) ...'
    1 failed, 5 deselected in 1.11s
    ```

    (a) and (b) fail with exactly the `moved into executed/` refusal the item requires, which is the field defect, not a setup error. (d) fails on the REASON: pre-change it refused through the wrong predicate, which is the F-5/F-11 conflation.

    ROW (c) IS PROVEN AGAINST THE RIGHT BASELINE, and it is a different one, which matters: pre-change code refuses the substitution too (no false negative to expose there), so its guard is the E-01-ONLY variant, i.e. the shipped fix with the id binding deleted. Run with that variant in place:

    ```text
    id binding present? False
    E   AssertionError: ... the gate misjudged 1 of 15 staged situations.
    E     a WHOLESALE content substitution (different `- Id:`) at an already-executed path:
    E       - expected exit code 1, got 0 with messages []
    E       - the refusal must state ['zzz999', 'aw ipd finalize', 'moved into executed/']; it said ''
    1 failed, 5 deselected in 1.26s
    ```

    Exactly ONE row fails in that run, so the row is specific to the clause it guards. The source module was restored from the saved copy afterwards and re-verified (`id binding present? True`, `6 passed`).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `git merge-base --is-ancestor bcd9755f HEAD` (with its exit status), `git log --oneline -- agent_workflows/hooks/executed_transition_gate.py`, and the `- Status:` line of `29wvmj`'s plan file, establishing it is EXECUTED and in-tree. Paste the 15 `MergeAwareInTreeEvidenceTests` passing by name. Paste evidence that a lane-carried plan is still DETECTED (the `_staged_plan_executed_transitions` tuple during a real merge) and accepted via `_intree_finalize_evidence_ok` rather than via the new exemption. Paste the added comment. Paste the bare `python3 -m pytest` summary line and compare it to the F-17 baseline.
  - Observed evidence: `29wvmj` is EXECUTED and its code is in the file this plan edits (F-16 confirmed):

    ```text
    $ git merge-base --is-ancestor bcd9755f HEAD; echo "is-ancestor rc=$?"
    is-ancestor rc=0
    $ git log --oneline -1 bcd9755f
    bcd9755f fix(hooks): accept a finalized lane merge in the executed-transition gate (29wvmj)
    $ git log --oneline -- agent_workflows/hooks/executed_transition_gate.py
    70792b53 feat(run_viewer): classify an artifact difference by direction on read git evidence (zexed1)
    bcd9755f fix(hooks): accept a finalized lane merge in the executed-transition gate (29wvmj)
    f7a3702e feat(ipdgates-08): local pre-commit gate on raw plan->executed commits (dulzpy)
    $ grep -n '^- Status:' .aw/records/plans/executed/*29wvmj*.ipd.md
    12:- Status: executed
    ```

    ALL 15 MERGE ROWS PASS, BY NAME. `unittest -v` prints only the 3 enclosing functions (a passing `subTest` is silent), so each row was driven individually:

    ```text
    gate module under test: .../.aw/worktrees/i4c0c3/agent_workflows/hooks/executed_transition_gate.py
    === MergeAwareInTreeEvidenceTests.DETECTOR_STATES (`_merge_incoming_commits`)
      [PASS] no merge in progress at all                                   expected=[] actual=[]
      [PASS] a lane exists but no merge has been started                   expected=[] actual=[]
      [PASS] a hand merge (`git merge --no-commit`) in progress            expected=['153aaa54...'] actual=['153aaa54...']
      [PASS] a merge inside a WORKTREE, where `.git` is a FILE             expected=['153aaa54...'] actual=['153aaa54...']
    === MergeAwareInTreeEvidenceTests.MERGE_DECISIONS (`check` given merge state)
      [PASS] a merge whose incoming side carries the matching finalize commit   want_rc=0 got_rc=0 missing=[] leaked=[]
      [PASS] a merge whose incoming side has NO finalize commit                 want_rc=1 got_rc=1 missing=[] leaked=[]
      [PASS] a merge carrying a finalize commit for a DIFFERENT id6             want_rc=1 got_rc=1 missing=[] leaked=[]
      [PASS] a finalize commit already reachable from HEAD                      want_rc=1 got_rc=1 missing=[] leaked=[]
      [PASS] a plan with no readable `- Id:`, during a merge                    want_rc=1 got_rc=1 missing=[] leaked=[]
      [PASS] a hand-edited status flip OUTSIDE any merge                        want_rc=1 got_rc=1 missing=[] leaked=[]
      [PASS] a `git mv` into executed/ OUTSIDE any merge                        want_rc=1 got_rc=1 missing=[] leaked=[]
    === MergeAwareInTreeEvidenceTests.INSTALLED_HOOK_RUNS (real git, real hook)
      [PASS] hand merge of an evidenced lane, gated at `pre-commit`             want_rc=0 got_rc=0 missing=[]
      [PASS] automated merge of an UNEVIDENCED lane, at `pre-merge-commit`      want_rc=1 got_rc=1 missing=[]
      [PASS] automated merge of an EVIDENCED lane, at `pre-merge-commit`        want_rc=0 got_rc=0 missing=[]
      [PASS] an OCTOPUS merge of two evidenced lanes                            want_rc=0 got_rc=0 missing=[]
    === 15 merge rows exercised; failures: 0
    ```

    THE SUBSTANTIVE INTERACTION, measured rather than argued. During a real `git merge --no-ff --no-commit` of an evidenced lane, the arrival is STILL DETECTED as a transition, and acceptance comes from in-tree evidence and NOT from the new exemption:

    ```text
    transitions DETECTED           : [('.aw/records/plans/executed/20260824-demo-01-abc123-demo.ipd.md', 'abc123', 'moved into executed/')]
    incoming merge side(s)         : ['3cd4b7535e89']
    journal evidence (must be False, `.aw/state/` cannot travel): [False]
    IN-TREE evidence (must be True, this is the accepting path): [True]
    check() rc=0 messages=[]
    [PASS] DETECTED as a transition (at HEAD the plan was in pending/, so `was_in_executed_at_head` is
           False) and accepted ONLY via in-tree evidence
    ```

    That is the narrowing risk closed: `check()` consults merge state only for transitions the detector RETURNED, and the detector still returns this one, so the `29wvmj` path is reached exactly as before.

    THE COMMENT E-06 REQUIRES is at the predicate, naming the two concerns:

    ```python
    # TWO DISTINCT CONCERNS, kept apart deliberately; do not collapse one back into the other:
    #   (1) did this file ENTER `executed/` IN THIS COMMIT  -> `moved_into_executed`
    #   (2) was it merely EDITED while ALREADY there        -> exempt, nothing is transitioning
    ```

    The module docstring gained a matching `WHAT IS *NOT* A TRANSITION (gatejrnl i4c0c3)` paragraph, so the code no longer describes the over-broad rule it stopped implementing (the obligation in this plan's spec-sync section).

    BARE SUITE (`python3 -m pytest`, per the repository contract):

    ```text
    1 failed, 7206 passed, 3 skipped, 2 xfailed, 3 warnings in 207.94s (0:03:27)
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    ```

    COMPARED TO THE F-17 BASELINE: the shape matches (one failure, unrelated to this change) but BOTH the count and the failing test differ, because the tree has moved on (5866 -> 7206 passed) and the lane environment differs. The failure is ENVIRONMENTAL, not a delta from this plan, proven two ways rather than asserted: (1) it disappears when the ambient variable is removed, `env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py -o addopts="" -q` -> `43 passed`; and (2) it REPRODUCES with this plan's change fully reverted under the same environment -> `1 failed, 42 passed`. The test asserts `OPENCODE_CONFIG_CONTENT` is absent for a non-isolated turn, and this runner turn exports it into the lane, which is precisely the "additional environmental failures inside a lane worktree from tests that read live repo state" the plan's own validation section anticipated. Filed as backlog `to77re`. F-17's own named failure (`test_reporting_contract.py`) does NOT occur here.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan has been REVIEWED (`- Status: reviewed`, `- Readiness: go-pending-approval`). It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`. Note that it graduates only PART of backlog item `gjadwm` and CORRECTS that item's stated cause for the part it does graduate (F-1, F-3), and that review in turn corrected the plan's OWN diagnosis: the draft's E-01 would not have fixed the bug (F-11) and would have opened a substitution hole (F-12).

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE THE REFLEXIVE HAZARD: this plan edits the very pre-commit gate that will run on its own commits, so verify with `git diff --cached --name-only` before each commit, re-verify after any failed hook, and never reach for `--no-verify` to land a change to the hook that exists to stop that habit. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
