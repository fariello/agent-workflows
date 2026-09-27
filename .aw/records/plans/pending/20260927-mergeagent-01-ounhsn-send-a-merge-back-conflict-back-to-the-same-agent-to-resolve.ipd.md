# IPD: Send a merge-back conflict back to the same agent to resolve in its lane instead of failing the item

- Date: 2026-09-27
- Kind: child
- Concern: A lane whose verified work CONFLICTS with main at merge-back is failed (`fail-merge`, terminal on the first attempt, not counted against the retry budget) and handed to a HUMAN, even when the agent that wrote the work is still in the run and the conflict is trivial. Measured 2026-09-27 in run-20260927T051110Z-3282017: `k4vi7z` (already finalized on its lane) failed on an additive-only `CHANGELOG.md` conflict, and `btth0a`'s lane conflicted with `sbo3hl` in `agent_workflows/upgrade_rehearsal.py` and `tests/test_aw_upgrade_test.py`; every hunk was keep-both and a human resolved them by hand. The runner already DETECTS the easy shape (`classify_conflict_shape_from_stages` over `classify_conflict_hunk_shape`, yielding `CONFLICT_SHAPE_ADJACENCY_ONLY`) and `conflict_resolver_remedy` already tells a HUMAN that keep-both is lossless, then stops anyway (`integrate_lane_branch`: "Nothing is RETRIED").
- Scope: IN: on a git merge conflict at merge-back of an EXECUTE lane, bring main into the lane (in the lane worktree, conflicts left for the agent), give the SAME agent a correction turn on its SAME session to resolve and commit, then re-run the normal merge-back (gate + suite + merge) under the integration lock; bounded by the run's existing `--retry-budget`; exhausted or refused = `fail-merge` exactly as today; both hosts; outcome tests; one CHANGELOG line. OUT: auto-resolving conflicts without an agent; review-lane conflicts; changing the gate, the suite or the integration lock; `aw <host> integrate` (the human path stays as is).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_merge_conflict_sendback.py, tests/test_runner_shared.py, CHANGELOG.md, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Blocks-Release: next
- From-Backlog: xyv75i
- Work-Kind: bug
- Priority: high
- Set: mergeagent
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: ounhsn
- Approval: 2026-09-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-27 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 all fixed. Three authored instructions were measured non-functional (the aw commit resolution cannot conclude a merge, classify_conflict_hunk_shape returns unknown on a default-style working-tree conflict, git rev-parse main exits 128 off a main branch); the consummation check was widened by the condition that detects the first of those; the required 25kzda spec amendment was added as E-07; the test item was split into E-05 (unit) and E-08 (driver), clearing IPD-Z602. Findings recorded in .aw/records/reviews/20260927-mergeagent-01-ounhsn-send-a-merge-back-conflict-back-to-the-same-agent-to-resolve.review.md
- 2026-09-27 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog xyv75i per maintainer ruling 2026-09-27: send a merge-back conflict back to the same agent under the existing retry budget.

- 2026-09-27 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A merge conflict between a lane's verified work and main is sent back to the agent that wrote the work, which resolves it in its own lane; the runner then re-runs the ordinary merge-back. The item fails only when the agent cannot resolve it within the run's existing retry budget.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prepare the lane

- [ ] E-01 Add `runner_shared.prepare_lane_for_conflict_resolution(repo, handle, *, run_checked) -> ConflictPrep` (NamedTuple: `ok`, `conflicted_paths`, `merge_head`, `detail`). In the LANE worktree (`handle.path`), run `git merge --no-ff --no-commit <main tip>`. READ THE TIP AS `git rev-parse HEAD` IN `repo`, NOT `git rev-parse main`: a repository whose integration branch is not literally named `main` makes `git rev-parse main` exit 128 (`fatal: ambiguous argument 'main'`, measured in a scratch repo on `master`), and every shipped site that needs this value already reads `HEAD` in `repo` (`_resolved_main_tip`, `git_head`). Because the caller in E-03 runs INSIDE `integrate_under_repository_lock`, that tip is the same one the lock recorded in `item["integration_serialization"]["main_tip_in_lock"]`, so PREFER that recorded value when present and fall back to reading `HEAD`. If the merge is clean (main moved but nothing now conflicts), commit it with subject `merge main into lane <id6> for merge-back` and return `ok=True, conflicted_paths=(), merge_head=""`. If it conflicts, leave the markers in place and return `ok=True` with the conflicted paths from `git diff --name-only --diff-filter=U` and `merge_head=<the tip>` (the value the E-03 consummation check compares against). REFUSE, DO NOT RE-MERGE, WHEN A MERGE IS ALREADY IN PROGRESS: `merge_in_progress(handle.path)` true on entry returns `ok=False` with a detail naming it, because a second `git merge` then exits 128 (`fatal: You have not concluded your merge (MERGE_HEAD exists)`, measured) and would otherwise be misread as a git failure. If git fails for any other reason, `git merge --abort` in the lane and return `ok=False`. Never touches main or the primary checkout. Main is NOT merged into by this function.
  - Depends on: none
  - Expected outcome: a pure lane-local helper; main's HEAD and the primary checkout are byte-identical before and after; it works on a repository whose branch is not named `main`.
  - Execution state: pending

### Task group 2: ask the agent, then re-integrate

- [ ] E-02 Add `runner_shared.merge_conflict_question(detail, *, main_tip) -> str`, the prompt for the correction turn, where `detail` is the mapping `build_conflict_resolver_detail` returns. In plain words: main moved while you worked and these files now conflict; main has been merged into your lane and the merge is IN PROGRESS with conflict markers in the working tree; for each file resolve the conflict (for a file classified `adjacency-only`, keeping both sides in a sensible order is correct; otherwise read both sides and resolve on their merits, never keep both blindly); remove every conflict marker; run the tests your plan names; then CONCLUDE THE MERGE with `git add -- <the conflicted paths>` followed by a bare `git commit --no-edit` (see the two mechanical facts below); do NOT run `aw ipd begin`/`finalize`; then write the outcome file.

  THE COMMIT INSTRUCTION IS THE ONE PLACE THIS ITEM MUST NOT FOLLOW THE REPOSITORY'S USUAL `aw commit` CONTRACT, and both reasons are measured, so state them IN THE PROMPT so the agent does not "correct" itself back to the contract:
  (a) A PATH-SCOPED COMMIT IS IMPOSSIBLE MID-MERGE. `git commit -- <paths>` exits 128 with `fatal: cannot do a partial commit during a merge`, so the pathspec form the contract mandates cannot conclude a merge at all.
  (b) `aw commit` DOES NOT CONCLUDE THE MERGE EITHER, AND ITS FAILURE IS SILENT. It routes through `git_commit_helper.offer_commit` -> `commit_lock.commit_isolated`, which commits in a DETACHED throwaway worktree and advances the branch by `update-ref` under a CAS. Measured in a scratch repo: it reports `committed` and creates a SINGLE-PARENT commit, leaves `MERGE_HEAD` present, and leaves main NOT an ancestor of the lane, so the merge is recorded as an ordinary edit and the incoming side is never joined. The subsequent merge-back then re-conflicts on the same hunk (reproduced). Additionally `_staged_paths` reads git's merge-populated index, which holds every path the merge touched, so a plan whose `Scope-Paths` does not name them all makes `aw commit` refuse out-of-scope before it gets that far (measured: a merge staging `o.txt` under a plan declaring only `f.txt` yields `out_of_scope: ['o.txt']`).
  The bare `git commit --no-edit` is therefore the CORRECT tool here, not a contract violation to apologize for: git itself owns concluding a merge it started, the commit is made from the merge state so it carries BOTH parents, and the paths in it are exactly the ones git staged. The prompt MUST say this explicitly, and MUST NOT tell the agent that the out-of-scope paths are "recorded automatically" (the finalize scope reconciliation already ran on the lane before merge-back, so nothing records these).

  Reuse `classify_conflict_shape_from_stages` (via `build_conflict_resolver_detail`) for the shape and `format_conflict_resolver_facts` for the per-file facts rather than re-deriving them. DO NOT call `classify_conflict_hunk_shape` on the working-tree file: it requires a `|||||||` base section and git's DEFAULT conflict style emits none, so it returns `unknown` for a conflict the stage-based classifier correctly calls `adjacency-only` (measured on the same scratch conflict: working-tree text -> `unknown` "carry NO `|||||||` base section"; `classify_conflict_shape_from_stages` -> `adjacency-only`). The shape must be computed while the merge is in progress, which is where E-03 calls it.
  - Depends on: E-01
  - Expected outcome: one prompt builder; the only new wording in the run's prompts; the rendered adjacency-only prompt names the correct shape rather than `unknown`.
  - Execution state: pending

- [ ] E-03 In `execute_item_core`, at the execute-lane publish site (the `integrate_under_repository_lock(..., integrate=_publish, ...)` call and the `record_integration_refusal` branch that follows it), when `integ_kind == INTEGRATION_REFUSAL_CONFLICT` and the reason carries the `git-merge-conflict` cause token (read it with `read_integration_cause`, the ONE reader, never by matching the raw prefix), and the item has correction budget left (`frozen_retry_budget(state)` against a new durable counter `MERGE_CONFLICT_RETRY_COUNT_KEY` on the ITEM, counted before the turn so a crash cannot yield a free retry): call E-01; if it returns conflicts, build `build_conflict_resolver_detail(handle.path, paths=conflicted, base_commit=handle.base_commit)` WHILE THE MERGE IS STILL IN PROGRESS (the stage-based classifier reads the three index stages, so it must precede anything that clears them, exactly as `integrate_lane_branch` orders it today), then ask E-02's question through the SAME in-lane follow-up mechanism the gate-answer turn uses (`resume_via_launcher(raw_launcher, ...)` with `work_dir=<lane>`, the attempt's own session, `log_suffix/label_suffix="merge-conflict"`, host-specific argument shapes exactly as `perform_gate_answer`'s caller passes them, and the same `except (KeyboardInterrupt, StallTimeout)` containment so an interrupted follow-up leaves the refusal STANDING rather than raising out of the publish site); then recollect lane submissions; then run the CONSUMMATION CHECK below; then re-run the SAME `integrate_under_repository_lock(..., integrate=_publish)` call (gate, suite and merge, inside the lock, main re-read). Loop while conflicts recur and budget remains. If E-01 returned a clean merge, skip the ask and re-run `_publish` directly (counts against the budget too).

  THE CONSUMMATION CHECK IS THREE CONDITIONS, NOT TWO, AND THE THIRD IS THE LOAD-BEARING ONE. Require ALL of: (i) `git diff --name-only --diff-filter=U` in the lane is EMPTY; (ii) `git grep -nE '^(<<<<<<<|>>>>>>>)' -- <conflicted paths>` is EMPTY; and (iii) THE MERGE WAS ACTUALLY CONSUMMATED, proved by BOTH `merge_in_progress(handle.path)` being FALSE and `git merge-base --is-ancestor <prep.merge_head> <lane HEAD>` succeeding. Conditions (i) and (ii) alone are INSUFFICIENT and would let a broken resolution through: measured in a scratch repo, after the `aw commit` path (`commit_lock.commit_isolated`) both (i) and (ii) PASS while `MERGE_HEAD` is still present and main is NOT an ancestor of the lane, and the ensuing merge-back re-conflicts on the identical hunk. Treat a failure of (iii) as an UNRESOLVED attempt (not as a git fault): consume the attempt, and on the next loop E-01's `merge_in_progress` guard will report `ok=False` naming the unconcluded merge, which is the honest terminal detail. Prefer condition (ii) over a whole-tree marker scan for the reason `diff_has_conflict_markers` documents: a line-anchored, path-scoped grep cannot reject a lane for pasting pytest output.

  On exhaustion, an unresolved attempt, `ok=False`, or a non-conflict refusal, fall through to the existing `record_integration_refusal` path unchanged, so the item ends `fail-merge` with today's reason and remedy plus a `merge_conflict_sendback` record listing each attempt. THE LANE MUST BE LEFT INTEGRABLE BY THE EXISTING HUMAN PATH on every terminal arm: `aw <host> integrate <id6>` re-reads the lane branch and `lane_holds_finalized_plan` reads its TREE, so a lane left with an in-progress merge would refuse there too. Therefore on the terminal arm, if `merge_in_progress(handle.path)` is true, `git merge --abort` in the LANE (never in `repo`) before falling through, and record that the abort ran. Record each attempt on the attempt as `attempt["merge_conflict_sendback"] = [{"conflicted": [...], "shape": ..., "resolved": bool, "consummated": bool}]` and emit `merge-conflict-sent-back` / `merge-conflict-resolved` / `merge-conflict-unresolved` events.
  - Depends on: E-01, E-02
  - Expected outcome: a conflicted execute lane gets up to `retry_budget` agent resolutions before it can end `fail-merge`; a budget of 0 behaves exactly as today; a resolution that removed the markers WITHOUT concluding the merge is caught rather than published; every terminal arm leaves the lane with no merge in progress.
  - Execution state: pending

- [ ] E-04 Keep the finalized plan finalized: the lane already moved the plan to `executed/` and committed its finalize before merge-back (`lane_holds_finalized_plan`), so the correction turn must not re-finalize. Assert in E-03's code path that it never calls `driver_finalize`/`finalize_with_contention_retry` and never re-issues `begin`; the finalize record on the lane is what merge-back publishes. Update `TURN_RETRY_CLASSIFICATION`'s `fail-merge` reason text to say a git merge conflict is first sent back to the agent under `--retry-budget` and is terminal only after that (the row stays `False`: this send-back happens inside the item's own integration, not as a re-dispatched turn). Update `integrate_lane_branch`'s "Nothing is RETRIED" comment to point at the send-back so the two do not contradict each other.
  - Depends on: E-03
  - Expected outcome: no double finalize; the documented behavior matches the code.
  - Execution state: pending

- [ ] E-07 AMEND SPEC `25kzda` in the SAME change, because this plan contradicts its shipped text and a code-only change would leave the contract stating the opposite of the behavior. Section 2.1a's rule reads "EVERY OTHER CONFLICT CLASS REMAINS TERMINAL ON ITS FIRST ATTEMPT ... as does any genuine merge conflict that does not positively classify", and Section 2.1 says the ladder "never applies to a genuine merge conflict ... none of which repetition fixes". Add a sibling section (2.1b) recording the maintainer's 2026-09-27 ruling and stating the distinction precisely: the send-back is neither a LADDER RE-ATTEMPT nor a RE-DERIVATION, but an AGENT CORRECTION TURN that CHANGES THE INPUTS before the merge is retried (main is merged into the lane and a human-equivalent resolution is committed there), so Section 2.1's stated reason ("repetition does not fix those classes") does not reach it, exactly as 2.1a's recomputed-versus-retried distinction does not. State the four properties that bound it: it applies ONLY to the `git-merge-conflict` cause on an EXECUTE lane; it is bounded by `--retry-budget` and NOT by `--integration-retry-limit`, so the two-quantity distinction Section 2.1 draws is untouched; the ladder itself is unchanged (`classify_integration_refusal` still returns False for `fail-merge`, `decide_integration_deferral` still terminal on attempt 1); and an exhausted or unresolved send-back reaches `fail-merge` with today's reason and remedy. Do it with `aw specs`; add `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` to `- Scope-Paths:` so both runners announce the declared spec edit before the run and the finalize scope gate can reconcile it.
  - Depends on: E-04
  - Expected outcome: the spec and the code agree; `aw check` clean; the amendment is announced as a declared spec edit.
  - Execution state: pending

### Task group 3: tests and record

- [ ] E-05 Add `tests/test_merge_conflict_sendback.py` covering E-01 and E-02 as UNIT surfaces (no driver, no spawn), on BOTH hosts (`BOTH` / `_MODULES` as `tests/test_runner_shared.py` uses them), OUTCOME tests only (no source-text pins). Build the conflict the way `test_a_real_conflict_still_aborts_leaving_main_clean` does (lane and main both write `clash.txt`), and additionally one repository whose branch is NOT named `main`. Cases: (1) `prepare_lane_for_conflict_resolution` on a conflicting lane/main pair returns `ok=True, conflicted_paths=('clash.txt',)`, leaves markers in the lane file, and leaves `repo`'s HEAD and `git status --short` byte-identical; (2) the same on a lane whose main moved on an UNRELATED file returns `ok=True, conflicted_paths=()` and a lane whose HEAD now has main as an ancestor; (3) called with a merge already in progress it returns `ok=False` naming the unconcluded merge and does NOT run a second `git merge`; (4) the non-`main` branch name still works (this is the `git rev-parse main` regression); (5) `merge_conflict_question` for an ADJACENCY-ONLY set names that shape and the keep-both instruction, for a SEMANTIC set names the resolve-on-merits instruction instead, and in both cases carries the bare `git commit --no-edit` instruction and NOT a pathspec commit.
  - Depends on: E-01, E-02
  - Expected outcome: five unit cases pass on both hosts; case (1) is the one that proves main is untouched and case (4) is the one that fails against a `git rev-parse main` implementation.
  - Execution state: pending

- [ ] E-08 Add the DRIVER-LEVEL outcome cases to `tests/test_merge_conflict_sendback.py`, which need a different harness from E-05 (a real `execute_item_core`/queue path with the host spawn replaced by a fake that edits the lane; no real model, the suite forbids real spawns). Cases: (a) the fake resolves properly (writes both lines, removes markers, `git add` + bare `git commit --no-edit`) -> the item integrates, main contains BOTH lines, `merge-conflict-resolved` emitted, exactly one agent ask recorded; (b) the fake does nothing -> after `retry_budget` asks the item is `fail-merge`, main unchanged, lane preserved with NO merge in progress, `merge-conflict-unresolved` recorded; (c) `--retry-budget 0` -> no ask at all, `fail-merge` exactly as before (the fake's call count is 0); (d) main moved on an UNRELATED file so E-01's merge is clean -> the item integrates with no agent ask; (e) THE CONSUMMATION REGRESSION: the fake removes the markers and commits via the `aw commit` path (`commit_lock.commit_isolated`) WITHOUT concluding the merge -> the attempt is counted UNRESOLVED and the item does NOT integrate, which is the case conditions (i) and (ii) alone would wrongly pass. Update `test_merge_conflict_terminal_and_budget_independence` only if its assertions about `decide_integration_deferral` change; they should NOT, because the ladder is untouched, and if they do the ladder was altered out of scope.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: five driver outcome cases pass on both hosts; (e) fails against an implementation that checks only markers and unmerged paths.
  - Execution state: pending

- [ ] E-06 Add one `- Changed:` line to `## 2.0.0 (pending)` in `CHANGELOG.md`, plain words, no em or en dashes: when a finished item's work conflicts with main, the run now hands the conflict back to the same agent to resolve in its lane and then merges it, instead of failing the item; it fails only if the agent cannot resolve it within the run's retry budget. Then run the bare suite and the leak sanitizer.
  - Depends on: E-07, E-08
  - Expected outcome: one line; suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Follow-up agent turns inside an item's own integration already exist and are the template: the gate-answer turn (`perform_gate_answer`, asked via `resume_via_launcher` on the attempt's session in the lane, bounded by `--retry-budget`, maintainer ruling 2026-09-20 "share it, add no second knob").
- The retry budget is `run_recovery.DEFAULT_RETRY_LIMIT = 2`, frozen per run (`frozen_retry_budget`); `0` means no retries and must keep today's behavior.
- The integration lock (`integrate_under_repository_lock`) re-reads main's tip inside the lock and records it as `item["integration_serialization"]["main_tip_in_lock"]`; every publish goes through it. It reads the tip as `git rev-parse HEAD` in `repo` (`_resolved_main_tip`), never by the branch name `main`.
- Conflict shape and resolver facts already exist (`build_conflict_resolver_detail` -> `classify_conflict_shape_from_stages` -> `classify_conflict_hunk_shape`, plus `format_conflict_resolver_facts` and `conflict_resolver_remedy`); reuse them. THE ENTRY POINT MATTERS: the stage-based wrapper is the usable one, because the bare hunk classifier needs a `|||||||` base section that git's default conflict style does not emit.
- The cause token on a refusal reason is read with `read_integration_cause` (the ONE reader) and written with `tag_integration_cause` (the ONE writer); never match the prefix by hand.
- A merge conflict must be concluded by git's own `git commit` from the merge state. `aw commit` routes through `commit_lock.commit_isolated`, which commits in a detached throwaway worktree, so it CANNOT conclude a merge (measured: single-parent commit, `MERGE_HEAD` retained, incoming side not joined). This is the one place a bare `git commit` is correct rather than a contract violation.
- Tests: outcome only (maintainer standing rule); both hosts; no real model spawns.
- Cite code by symbol; line numbers drift.

## Findings

| # | Location | Finding |
| --- | --- | --- |
| F-1 | `runner_shared.integrate_lane_branch` conflict branch | On `merge_in_progress`, after the records-only re-derivation fails, it aborts and returns `fail-merge` tagged `git-merge-conflict`; its comment says "Nothing is RETRIED ... Every other conflict class remains terminal on its first attempt." |
| F-2 | `decide_integration_deferral` / `classify_integration_refusal` | Only `merge-retry` and `merge-unchecked` defer; `fail-merge` is terminal on attempt 1 regardless of budget (pinned by `test_merge_conflict_terminal_and_budget_independence`). |
| F-3 | `TURN_RETRY_CLASSIFICATION` | `fail-merge` is `False`: "integration refused; owned by the integration deferral ladder or human". |
| F-4 | measured 2026-09-27 | `k4vi7z` (CHANGELOG, additive-only) and `btth0a` (two files, additive-only unions with `sbo3hl`) were resolved by hand as keep-both; `tests/test_aw_upgrade_test.py` 46 passed after the union. |
| F-5 | `conflict_resolver_remedy` | Already tells a human to keep both sides for an adjacency-only set; that advice becomes the agent's instruction instead. |
| F-6 | measured at review 2026-09-27, scratch repo | `git commit -- <paths>` mid-merge exits 128: `fatal: cannot do a partial commit during a merge`. The path-scoped commit form the execution contract mandates cannot conclude a merge, so the correction turn needs a different instruction. |
| F-7 | measured at review 2026-09-27, `commit_lock.commit_isolated` on a conflicted lane | It reports `committed` and creates a SINGLE-PARENT commit, leaves `MERGE_HEAD` present, and leaves the incoming tip NOT an ancestor of the lane. The two checks E-03 originally proposed (no unmerged paths, no markers) BOTH pass in that state, and the re-run merge-back then re-conflicts on the identical hunk. So `aw commit` silently defeats the whole mechanism and the marker/unmerged checks cannot detect it. |
| F-8 | measured at review 2026-09-27 | `classify_conflict_hunk_shape` on the working-tree file returns `unknown` ("carry NO `\|\|\|\|\|\|\|` base section"), while `classify_conflict_shape_from_stages` on the same conflict returns `adjacency-only`. E-02's original reuse would have told every agent the shape was unknown, discarding precisely the signal the Concern cites. |
| F-9 | measured at review 2026-09-27, scratch repo on `master` | `git rev-parse main` exits 128 (`fatal: ambiguous argument 'main'`). E-01's original tip read would fail outright on such a repository; `_resolved_main_tip` reads `HEAD` for this reason. |
| F-10 | measured at review 2026-09-27 | A second `git merge` with `MERGE_HEAD` present exits 128 (`fatal: You have not concluded your merge`), so an E-01 called twice (the loop's second pass after an unconcluded resolution) reports a git failure whose real cause is the prior attempt. |
| F-11 | spec `25kzda` Sections 2.1 and 2.1a | 2.1a states "EVERY OTHER CONFLICT CLASS REMAINS TERMINAL ON ITS FIRST ATTEMPT ... as does any genuine merge conflict that does not positively classify", and 2.1 says the ladder "never applies to a genuine merge conflict". This plan changes that behavior, so the spec must be amended in the same change or the contract will state the opposite of the code. |
| F-12 | measured at review 2026-09-27 | `work_cmd._staged_paths` during a merge returns EVERY path the merge staged (a merge touching `o.txt` under a plan declaring only `f.txt` yields `out_of_scope: ['o.txt']`), so `aw commit <plan>` would refuse the resolution on scope before reaching the commit. Another reason the `aw commit` instruction could not work. |

## Proposed changes (ordered, validatable)

1. E-01 lane-local merge of main with conflicts left for the agent.
2. E-02 the correction question, carrying the merge-concluding commit instruction.
3. E-03 the bounded send-back loop at the execute publish site, gated on the three-condition consummation check; E-04 no re-finalize and aligned docs.
4. E-07 the spec `25kzda` amendment that makes the contract match the behavior.
5. E-05 unit cases for the helper and the prompt; E-08 the driver-level outcome cases including the consummation regression.
6. E-06 CHANGELOG and suite.

## Deferred / out of scope (with reason)

- Automatic keep-both resolution without an agent for adjacency-only conflicts.
  - Carrier-Declined: the maintainer chose agent resolution; an agent turn is cheap relative to a stranded item and also covers non-additive conflicts.
- Review-lane conflicts (`integrate_review_lane_branch`).
  - Carrier-Declined: review lanes write plan and review records only, and none were measured conflicting; nothing is outstanding.
- Changing `aw <host> integrate` (human re-integration).
  - Carrier-Declined: it remains the manual path after a `fail-merge`; the send-back happens before that point.

## Scope check

- Over-scope: none.
- Under-scope: the spec amendment (now E-07) was missing and is added; the driver-level test surface was bundled with the unit surface and is split out as E-08.

## Required tests / validation

Outcome tests only (maintainer standing rule). `tests/test_merge_conflict_sendback.py` carries two harnesses: E-05's UNIT cases over `prepare_lane_for_conflict_resolution` and `merge_conflict_question` (no driver, no spawn), and E-08's DRIVER cases over the real publish site with a faked spawn, asserting what ends up on main, the item's status, whether the agent was asked, and that a resolution which did not CONCLUDE the merge is rejected. Both hosts. Run the suite BARE: `python3 -m pytest`.

## Spec / documentation sync

SPEC `25kzda` IS AMENDED, by E-07, and that is required rather than optional: Section 2.1a's rule says "EVERY OTHER CONFLICT CLASS REMAINS TERMINAL ON ITS FIRST ATTEMPT ... as does any genuine merge conflict that does not positively classify", and Section 2.1 says the ladder "never applies to a genuine merge conflict ... none of which repetition fixes". This plan makes a genuine merge conflict non-terminal on its first attempt, so a code-only change would leave an approved contract asserting the opposite of the shipped behavior (F-11). The amendment adds a sibling Section 2.1b recording the maintainer's 2026-09-27 ruling and the agent-correction-versus-repetition distinction, and leaves every ladder sentence, the two-quantity budget distinction, and 2.1a itself untouched. The spec file is declared in `- Scope-Paths:` so both runners announce the edit before the run starts. CHANGELOG gains one line.

## Open questions

### OQ-01: Should a merge conflict go back to the agent?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED 2026-09-27 BY THE MAINTAINER when asked directly: yes, send it back to the same agent, bounded by the existing retry budget.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a scratch run (or test output) of `prepare_lane_for_conflict_resolution` on a lane/main pair that conflicts, showing `conflicted_paths == ('clash.txt',)`, `merge_head` equal to the tip that was merged, markers present in the lane file, and `git -C <repo> rev-parse HEAD` plus `git -C <repo> status --short` byte-identical before and after. ALSO paste the two refusal/guard cases: the same call in a repository whose branch is named `master` (must NOT exit 128 on a `rev-parse`), and the call made while a merge is already in progress (must return `ok=False` naming the unconcluded merge, and must not have run a second `git merge`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the rendered question for one adjacency-only and one semantic conflict, showing the file list and the two DIFFERENT resolution instructions, AND showing that the adjacency-only render names `adjacency-only` rather than `unknown` (the F-8 regression). ALSO paste the commit instruction verbatim from the rendered prompt, showing it names a bare `git commit --no-edit` and contains NO `aw commit` and NO `git commit -- <paths>` pathspec form.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste E-08 cases (a), (b) and (e) passing (node ids, both hosts), the `merge_conflict_sendback` record from case (a) showing `consummated: true`, and the record from case (e) showing the attempt counted as unresolved with `consummated: false`. ALSO paste, for case (b)'s terminal arm, evidence that the lane has NO merge in progress afterwards (no `MERGE_HEAD`) so the human `aw <host> integrate` path is still usable.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste E-08 case (a)'s evidence that finalize was not called a second time (the fake finalize double's call count, or no second `lifecycle(<id6>): finalize` commit in `git log`), plus the updated `TURN_RETRY_CLASSIFICATION` row text and the updated `integrate_lane_branch` comment.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_merge_conflict_sendback.py -o addopts="" -v` showing the five unit cases passed on both hosts, with case (4) (the non-`main` branch name) named in the output.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `git diff` of the `25kzda` spec file showing the new Section 2.1b and showing that Sections 2.1 and 2.1a are otherwise UNCHANGED (no ladder sentence edited), the `aw specs` command used with its output, `aw check --agent` exit 0, and `python3 -m pytest -o addopts="" tests/test_run_flag_surface.py` passing (that suite binds this spec's grammar bidirectionally, so a spec edit that disturbed the flag stanza would fail there).
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `python3 -m pytest tests/test_merge_conflict_sendback.py -o addopts="" -v` showing all five driver cases passed on both hosts, and paste the measured proof that case (e) is not vacuous: run it against an implementation whose consummation check omits condition (iii) and show it PASSES there (so the case would not have caught F-7), then show it FAILS with the full three-condition check absent a proper resolution.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `git diff CHANGELOG.md`, `git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'` printing nothing, the final summary line of a BARE `python3 -m pytest` with 0 failed, and `aw sanitize --agent` exit 0.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern, what happens when verified work conflicts with main at merge-back; the helper, the question, the loop and the contract amendment are one mechanism. The two test items are split because they need different harnesses (direct helper calls versus a real driver with a faked spawn), which is a density split rather than a second concern.

This plan is `reviewed` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING, three things rather than one:
1. A run spends up to `--retry-budget` (default 2) extra agent turns on an item whose verified work conflicts with main, and those turns may edit files outside the plan's Scope-Paths to resolve the merge; `fail-merge` is now reached only after that.
2. THE CORRECTION TURN IS INSTRUCTED TO USE A BARE `git commit --no-edit`, NOT `aw commit`. This is a deliberate, bounded exception to the repository's commit contract and it is not optional: measured at review, a path-scoped commit is impossible mid-merge (`fatal: cannot do a partial commit during a merge`) and the `aw commit` path cannot conclude a merge at all (it commits in a detached worktree, yielding a single-parent commit with `MERGE_HEAD` still present and the incoming side never joined). The commit is still hook-gated by git, is still never pushed, and contains exactly the paths git staged for the merge.
3. AN APPROVED SPEC IS AMENDED. E-07 adds a Section 2.1b to `25kzda`, because that spec currently states a genuine merge conflict is terminal on its first attempt and this plan makes it not. The amendment records the maintainer's 2026-09-27 ruling and leaves the ladder, the budget distinction and Section 2.1a untouched.

WHAT REVIEW CHANGED: the mechanism and the maintainer's ruling stand as authored. What moved is the mechanics. Three of the plan's original instructions were measured NOT to work (the `aw commit` resolution, the `classify_conflict_hunk_shape` reuse, and the `git rev-parse main` tip read), the consummation check was one condition short of detecting the failure the `aw commit` instruction would have produced, the required spec amendment was absent, and the test surface bundled two harnesses. See F-6 through F-12.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the files in `- Scope-Paths:`, which now include the `25kzda` spec file. If the work requires another file, make the edit and JUSTIFY it at finalize (`--scope-reason`).

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a test passed that was not run. Run the suite BARE (`python3 -m pytest`), no `-n0`, no extra `-q`, no `-p no:randomly`.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit ounhsn -- <paths>`; never `git add -A`, never push. The runner owns finalize in a lane. After execution set backlog `xyv75i` `done` with `--evidence` citing the executed plan (it carries `Blocks-Release: next`).
