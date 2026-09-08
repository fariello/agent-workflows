# IPD: Wire the run ownership trailers the runner already writes nothing into so a committed path can be attributed

- Date: 2026-09-08
- Kind: child
- Concern: THE ONLY IDENTIFIED WAY TO ATTRIBUTE A COMMIT TO AN EXECUTION IN THIS REPOSITORY IS BUILT, TESTED, AND WIRED TO NOTHING. `m73aet` (`runtrail-01`, executed) shipped immutable `AW-Run:`/`AW-Item:` git trailers per spec `25kzda` 4.6: `TRAILER_KEY_RUN`/`TRAILER_KEY_ITEM` (`git_commit_helper.py:48-49`), `compose_message_with_trailers` (`:162`), the canonical formatter `run_item_trailers` (`:226`, which returns `[]` when both values are absent so a message composes unchanged), and `offer_commit`'s `trailers: Sequence[str] = ()` parameter (`:353`), defaulting EMPTY so no existing caller changed behavior. MEASURED at HEAD: ZERO commits across the last 600 on all refs carry an `AW-Run` trailer, and `grep -rn 'AW-Run' agent_workflows/cli.py` returns ZERO, so there is no CLI flag either. The only caller that passes trailers is `work_cmd.py` via `_trailers_from_args` (`:362-384`), whose own docstring states the values must come from a live run and that "the runner wiring is deliberately deferred - a public flag whose only consumer does not exist yet is a contract taken on for nothing".
  THE GAP IS NARROWER THAN THE ITEM DESCRIBES, AND THAT CHANGES THE PLAN'S SHAPE. The item's step (2) says "give the antigravity runner the same commit path", on the measurement that `agy_runipd.py` does not call `offer_commit` at all (still true: ZERO hits). But the shipped commit path is NOT duplicated per host any more. `commit_backlog_close` (`oc_runipd.py:1331`) is the single function that calls `offer_commit` (`:1405`), and `agy_runipd.py` IMPORTS it (`:320`) along with `process_backlog_close` (`:324`) and CALLS the latter at `:3907`. So both hosts already reach one shared commit path, and passing trailers at that ONE call site serves both. The item's step (2) is therefore already satisfied by the rununify extraction, and treating it as outstanding would commission a second commit path where a shared one exists.
  THE ITEM'S THIRD STEP IS NOW SOMEONE ELSE'S, AND MUST NOT BE REBUILT HERE. Step (3) was "teach finalize to attribute a committed path by trailer instead of by changed-since-base_head". APPROVED plan `h9cn0y` (`scopeattr-01`, `- Status: approved`, `- From-Backlog: hyx1dg`) now owns finalize's committed-half attribution and is executing on it. Its review measured, in F-14, that git authorship cannot partition actors here and that the run record is unreachable from finalize, and concluded that trailers "are not merely a nicer future substrate, they are the ONLY identified way to attribute a commit to an execution here". It ships the weaker ownership-PREDICATE fix with a stated accepted cost, and explicitly defers trailers to a later plan, naming `a8eufb`. So this plan's job is to make the substrate EXIST so that cost can later be revisited; it must NOT re-implement the attribution logic `h9cn0y` is landing.
  THE ITEM'S SEQUENCING WARNING IS SUBSTANTIALLY WEAKER THAN WHEN IT WAS WRITTEN, which is what makes this graduable now. The item says wiring this means editing "the highest-contention files in the repo", cites "21 unexecuted plans" declaring them and the 7-plan `lanectn` Set as unexecuted, and recommends waiting for lane containment to remove the trigger. RE-MEASURED: 18 pending plans declare a runner file in `Scope-Paths`, and FOUR of `lanectn`'s children have EXECUTED (`cqx5v7`, `lhmrhx`, `y5od1h`, `604wra`), with three remaining approved. More decisively, the item's "cheaper path already queued" is now the DEFAULT: `--no-isolate-worktree` has `default=True` for `isolate_worktree` (`oc_runipd.py:7661-7665`), so every execute turn is isolated unless explicitly opted out, and an isolated lane is immune to the attribution noise by the item's own analysis. That does not make this work unnecessary, because the trailer is the substrate for a real fix rather than for noise suppression, but it does mean this plan is no longer starting the riskiest work in the repo to quiet paperwork.
- Scope: Make the runner PASS the trailers it already has the machinery to write, at the ONE shared commit call site both hosts reach, so a commit carries machine-readable run and item ownership. Attribution CONSUMPTION is explicitly excluded: `h9cn0y` owns finalize's committed-half logic and this plan must not touch it. This plan makes a writer real; it does not add a reader.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/git_commit_helper.py, tests/test_runner_backlog_close.py, tests/test_run_trailer_wiring.py
- Item-Dependencies: none
- Status: to-review
- Set: runtrailwire
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: wao266
- From-Backlog: a8eufb
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `a8eufb`, NARROWED to step (1) of the item's own three-step plan, with steps (2) and (3) verified DEAD or OWNED. Step (2) ("give the antigravity runner the same commit path") is already satisfied: `agy_runipd.py` imports `commit_backlog_close` from `oc_runipd` (`:320`) and calls the shared `process_backlog_close` (`:3907`), so ONE call site (`oc_runipd.py:1405`) serves both hosts and building a second would be a regression against the rununify extraction. Step (3) (teach finalize to attribute by trailer) is owned by APPROVED plan `h9cn0y`, whose review F-14 independently reached this item's conclusion (trailers are the only available attribution channel), which ships the weaker predicate fix with a stated accepted cost and defers trailers to a later plan naming `a8eufb`. Re-graduating step (3) would re-implement work an approved plan already declares. ALSO re-measured: the item's contention warning is weaker than written (18 pending plans declare a runner file, not 21; four of seven `lanectn` children have EXECUTED), and its "cheaper path already queued" mitigation is now the DEFAULT (`isolate_worktree` defaults True), so the item's reason for staying open no longer holds. The item's own SECOND paragraph is also stale and was NOT carried forward: its claim that "no durable per-commit ownership record exists" was already corrected in the item itself on 2026-09-03, and this plan starts from the corrected state.

## Goal

Turn a built-but-unreachable ownership mechanism into commits that actually carry it, so the next plan that needs to attribute a commit has real data to read instead of a parameter nobody passes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the live state, since three of the item's premises have moved

- [ ] E-01 RE-MEASURE THE FOUR CLAIMS THIS PLAN RESTS ON, by symbol, and write each down. Do not inherit them from this plan's prose; two of them are exactly the kind that drifted under the item.
  THE FOUR: (a) the trailer machinery exists and `offer_commit` accepts `trailers` defaulting empty; (b) NO commit in recent history carries an `AW-Run` trailer and no CLI flag mentions it; (c) `commit_backlog_close` is the ONLY `offer_commit` call site in either runner, and `agy_runipd.py` reaches it by IMPORT rather than by its own copy; (d) `h9cn0y` is still `approved` and still owns finalize's committed-half attribution.
  IF (c) HAS CHANGED, STOP AND RE-SCOPE. This plan's entire economy is that ONE call site serves both hosts. If a second `offer_commit` call has appeared in either runner, or if agy has grown its own commit path, then the item's step (2) is live again and this plan is the wrong shape: report that rather than wiring one site and claiming both hosts.
  IF (d) HAS CHANGED, SAY SO EXPLICITLY. If `h9cn0y` has EXECUTED, its accepted cost is now live in the tree and this plan's Deferred section should name the follow-up that revisits it. If it has been retired, the consumption half is unowned and that is a finding for a human, not a licence for this plan to absorb it.
  - Depends on: none
  - Expected outcome: a written, symbol-cited statement of all four claims as they stand at your HEAD, with an explicit re-scope or STOP if (c) or (d) has moved.
  - Execution state: pending

### Task group 2: pass the trailers at the one shared site

- [ ] E-02 PASS `run_item_trailers(run_id, item_id6)` AT THE SHARED `offer_commit` CALL SITE, and derive both values from the live run's own state rather than reconstructing them. `commit_backlog_close` currently calls `offer_commit(repo, paths, message=..., assume_yes=True, interactive=False)` with no `trailers=`.
  USE THE CANONICAL FORMATTER, NEVER A HAND-BUILT STRING. `run_item_trailers` exists precisely "so callers do not hand-format the keys (and drift)" and skips an absent value, returning `[]` when both are missing, which composes to an unchanged message. That empty-safe behavior is what makes this change safe for any path lacking a run id.
  THE VALUES MUST COME FROM THE RUN, NOT FROM A GUESS. `commit_backlog_close`'s current signature is `(repo, item_id6, message)` and it has no run id, so the run id must be threaded from the state the caller already holds (`process_backlog_close` receives `state`, which carries `run_id`, and `oc_runipd.py:1487` is the call). Thread it explicitly; do NOT read a global, and do NOT reach into `.aw/records/runs/`, which is gitignored and absent from a lane worktree.
  DO NOT BREAK THE SHARED IMPORT. `agy_runipd.py` imports `commit_backlog_close` by name (`:320`); a signature change must keep that import valid, and `tests/test_runner_backlog_close.py:1166` asserts on that name. Prefer an optional keyword so both hosts and every existing test keep working.
  MIND WHAT THAT FUNCTION ALREADY GUARDS, and preserve all of it: it filters paths to basenames containing the item's id6 so a co-worker's concurrent edit cannot be swept in, it requires `-uall` porcelain, it parses the status field rather than slicing a fixed width, and it FAILS CLOSED when fewer than two paths are seen because a legitimate close always yields both sides of a move. Each of those is a fix for a measured live failure. Adding a trailer must change nothing about them.
  - Depends on: E-01
  - Expected outcome: the shared call site passes canonically formatted trailers derived from the live run and item; `agy_runipd.py`'s import still resolves; every existing guard in that function is unchanged.
  - Execution state: pending

- [ ] E-03 DECIDE AND RECORD WHAT HAPPENS WHEN THERE IS NO RUN ID, rather than letting it fall out of the code. A hand-run `aw` invocation, a resumed path, or a test double may have no run id at all.
  THE ANSWER SHOULD BE: OMIT THE TRAILER, NEVER FABRICATE ONE. `run_item_trailers` already skips an absent value, so the safe behavior is the default. State it in a comment at the site, because the tempting "improvement" is to synthesize an id from a timestamp or a plan id, and a trailer that ASSERTS run ownership it cannot substantiate is worse than no trailer: the whole value of an immutable trailer is that a later reader can trust it. This is the same discipline `h9cn0y` E-03 applies when it refuses to name a responsible sha it cannot substantiate.
  DO NOT ADD A CLI FLAG. `work_cmd._trailers_from_args`'s docstring already records the reasoning: "a public flag whose only consumer does not exist yet is a contract taken on for nothing". That reasoning still holds for a flag on the RUNNER, whose values come from the run itself and never from a human.
  - Depends on: E-02
  - Expected outcome: a missing run id omits the trailer with the reason stated in a comment at the site; nothing is synthesized; no new CLI flag exists.
  - Execution state: pending

### Task group 3: prove the trailer is real and prove nothing else moved

- [ ] E-04 PROVE A REAL COMMIT CARRIES THE TRAILER, READ BACK THROUGH GIT'S OWN PARSER. An assertion on the composed message string is not enough: the point of a trailer is that `git` recognizes it as one.
  READ IT BACK WITH `git log --format='%(trailers:key=AW-Run,valueonly)'`, which is the same interface any future consumer would use, in a throwaway repository. A test that only checks the message text would pass even if the trailer block were malformed and git ignored it, which is exactly the failure mode that would make a future reader's attribution silently empty.
  ASSERT BOTH KEYS AND THE EMPTY CASE: a commit made with a run id and item id6 carries both `AW-Run` and `AW-Item`; a commit made without them carries NEITHER and its message is byte-identical to what it is today. The second assertion is what proves this change is additive.
  ASSERT BOTH HOSTS ARE COVERED BY THE ONE CHANGE, since that is this plan's central claim. Prove it structurally rather than by running two runners: assert that `agy_runipd.commit_backlog_close is oc_runipd.commit_backlog_close`, which is the same shape `tests/test_runner_refork_guard.py` already uses for shared symbols.
  - Depends on: E-03
  - Expected outcome: a real commit's trailers read back through git's own parser for both keys; the no-run-id commit is byte-identical to today; the shared-object identity between hosts is asserted.
  - Execution state: pending

- [ ] E-05 PROVE THE COMMIT PATH'S EXISTING BEHAVIOR IS UNCHANGED, because this function is the runner's only shipped commit and its guards each fix a measured live failure. Assert every one still holds with trailers present: the id6 basename filter still excludes a co-worker's concurrently-modified DIFFERENT backlog item; the fewer-than-two-paths case still returns None rather than committing half a move; the porcelain parse still handles a `" D <path>"` entry without eating the path's first character; and the untracked-file case still stages the individual FILE rather than the directory.
  RUN THE EXISTING SUITE FOR THAT FUNCTION AND PASTE ITS OWN SUMMARY LINE. `tests/test_runner_backlog_close.py` covers it, including a source-level assertion at `:576` that reads `inspect.getsource(oc_runipd.commit_backlog_close)`; a source-substring test can break on a legitimate edit, so if it does, report what it asserts and why the edit is still correct rather than loosening it silently.
  RUN THE SUITE BARE (`python3 -m pytest`) and judge on the DELTA. Baseline on main 2026-09-08: `1 failed, 5648 passed`, the failure being the pre-existing `test_orchestrator_retirement` case. Roughly 32 further failures inside a lane are environmental. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
  ALSO ASSERT NO CONSUMER WAS ADDED. Show that nothing in `ipd_lifecycle.py` reads a trailer, so this plan cannot be mistaken for having done `h9cn0y`'s job or for having changed finalize's behavior.
  - Depends on: E-04
  - Expected outcome: every existing guard holds with trailers present; the function's own suite passes with its summary line pasted; the bare-suite delta is empty; no trailer consumer exists anywhere.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE WHOLE MECHANISM EXISTS AND IS EMPTY-SAFE BY DESIGN. `run_item_trailers` returns `[]` when both values are absent and `offer_commit`'s `trailers` defaults to `()`, so adding a caller cannot change any other caller's message.
- ONE SHARED COMMIT PATH SERVES BOTH HOSTS. `commit_backlog_close` (`oc_runipd.py:1331`) holds the only `offer_commit` call in either runner (`:1405`); `agy_runipd.py` imports it (`:320`) and calls the shared `process_backlog_close` (`:3907`). `agy_runipd.py` has ZERO `offer_commit` hits of its own, and that is correct, not a gap.
- THAT FUNCTION'S GUARDS ARE ALL SCAR TISSUE FROM MEASURED FAILURES: the id6 basename filter, `-uall`, the width-independent porcelain parse, and the fail-closed fewer-than-two-paths rule. Its comments record each. Preserve them.
- `offer_commit` IS THE SHARED-CHECKOUT-SAFE PATH: it snapshots the index before staging, commits only the intersection of its own staged set with the requested paths, and resets only its own paths on failure. Do not replace it with raw git.
- THE DEFERRAL WAS DELIBERATE AND DOCUMENTED. `work_cmd._trailers_from_args` records that no CLI flag was added because "a public flag whose only consumer does not exist yet is a contract taken on for nothing". That reasoning applies to a runner flag too.
- `h9cn0y` OWNS FINALIZE'S COMMITTED-HALF ATTRIBUTION and independently concluded that trailers are the only available attribution channel here (its F-14). This plan supplies the substrate; it must not touch the consumer.
- ISOLATION IS THE DEFAULT (`isolate_worktree` default True, `oc_runipd.py:7661-7665`), which is why the item's contention-based reason for staying open no longer holds.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name; both runner files move by tens of lines per day.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the mechanism is built and reaches nothing | Trailer keys, composer, canonical formatter, and `offer_commit`'s empty-default `trailers` parameter all exist. ZERO commits in the last 600 across all refs carry `AW-Run`; ZERO `AW-Run` hits in `cli.py`. | `git_commit_helper.py:48-49`, `:162`, `:226`, `:353`; `git log --format='%(trailers:key=AW-Run,valueonly)'` over 600 commits; grep of `cli.py` |
| F-2 | HIGH | the item's step (2) is ALREADY DONE | `commit_backlog_close` is the ONLY `offer_commit` call in either runner and `agy_runipd.py` reaches it by IMPORT, calling the shared `process_backlog_close`. So ONE call site serves both hosts; building a second commit path would regress the rununify extraction. | `oc_runipd.py:1331`, `:1405`, `:1487`; `agy_runipd.py:320`, `:324`, `:3907`; `grep -c offer_commit agy_runipd.py` -> 0 |
| F-3 | HIGH | the item's step (3) is OWNED by an approved plan | `h9cn0y` (`- Status: approved`, `From-Backlog: hyx1dg`) owns finalize's committed-half attribution, ships the ownership-predicate fix with a stated accepted cost, and DEFERS trailers to a later plan naming `a8eufb`. Re-graduating step (3) would re-implement declared work. | `h9cn0y` metadata; its Deferred section's `COMMIT TRAILERS (a8eufb)` entry; its F-14 |
| F-4 | HIGH | an approved plan independently confirms this is the ONLY channel | `h9cn0y`'s review F-14 measured identical `%an`/`%ae` across five incident commits (other actors' and the plan's own alike), and F-13 that the run record is unreachable from finalize. It concludes trailers "are ... the ONLY identified way to attribute a commit to an execution here". | `h9cn0y` F-13, F-14 |
| F-5 | MEDIUM | the item's contention warning has weakened | It cites "21 unexecuted plans" declaring the runner files and the `lanectn` Set as unexecuted. Re-measured: 18 pending plans declare a runner file in `Scope-Paths`, and FOUR of seven `lanectn` children have EXECUTED (`cqx5v7`, `lhmrhx`, `y5od1h`, `604wra`). | `grep -l` over pending `Scope-Paths`; `ls .aw/records/plans/executed/ \| grep lanectn` |
| F-6 | MEDIUM | the item's "cheaper path" is now the DEFAULT | It recommends waiting for lane containment to remove the trigger. `isolate_worktree` already defaults True, so every execute turn is isolated unless opted out, and an isolated lane is immune by the item's own analysis. | `oc_runipd.py:7661-7665`; `:3063`; `:5985` |
| F-7 | MEDIUM | empty-safety is what makes this additive | `run_item_trailers` returns `[]` for absent values and `offer_commit`'s parameter defaults `()`, so the no-run-id path composes an unchanged message. | `git_commit_helper.py:226-239`, `:353` |
| F-8 | MEDIUM | the target function is dense with measured fixes | Its own comments record four: the id6 basename filter against co-worker sweep-in, `-uall` (without which the untracked file was never staged), the width-independent porcelain parse (a fixed slice ate the path's first character), and fail-closed on fewer than two paths. All must survive. | `commit_backlog_close`'s comment blocks |
| F-9 | MEDIUM | a source-substring test guards it | `tests/test_runner_backlog_close.py:576` asserts over `inspect.getsource(oc_runipd.commit_backlog_close)`, so a legitimate edit can trip it. Report rather than loosen. | that test |
| F-10 | LOW | the item's own second paragraph is stale | Its original text concluded "no durable per-commit ownership record exists"; the item itself corrected that on 2026-09-03. This plan starts from the corrected state, not the original. | the item's `STALENESS CORRECTION 2026-09-03` section |
| F-11 | LOW | two finding codes wait on a READER, not a writer | `RUN-COMMIT-CONTENTS`/`RUN-COMMIT-GATEWAY` stay UNBOUND because "nothing reads a trailer back". This plan does not bind them, and must not claim to. | `run_evidence.py`'s binding tally comment |

## Proposed changes (ordered, validatable)

1. Re-measure the four load-bearing claims by symbol, with an explicit STOP if the shared-call-site or ownership claims have moved (E-01).
2. Pass canonically formatted trailers at the one shared `offer_commit` call site, threading the run id from state (E-02).
3. Omit the trailer when there is no run id, stating at the site why nothing is synthesized, and add no CLI flag (E-03).
4. Prove a real commit's trailers read back through git's own parser, and that the no-trailer message is byte-identical (E-04).
5. Prove every existing guard in that function still holds and that no trailer consumer was added (E-05).

## Deferred / out of scope (with reason)

- TEACHING FINALIZE TO ATTRIBUTE BY TRAILER (the item's step 3). Owned by APPROVED plan `h9cn0y`, which explicitly defers trailers to a later plan naming this item. This plan supplies the substrate ONLY. Once trailers actually exist in history, a follow-up should revisit `h9cn0y` E-02's accepted cost (that excluding the unowned committed class also stops demanding a reason for the executor's OWN out-of-scope commit) and E-03's message, both of which that plan states are weaker than they would be with trailers available. Filing that follow-up is the honest successor to this plan, not part of it.
- GIVING THE AGY RUNNER ITS OWN COMMIT PATH (the item's step 2). Already satisfied: both hosts reach one shared function by import. Building a second would regress the rununify de-duplication that `5e4sb6` exists to complete.
- INVERTING `test_committed_half_of_a_coworker_is_STILL_refused_documented_limitation`. That characterization test pins finalize's REFUSAL and belongs to whoever changes finalize's attribution, which is `h9cn0y`. The item requires it be inverted rather than deleted; this plan touches neither it nor `tests/test_finalize_scope_ownership.py`.
- BINDING `RUN-COMMIT-CONTENTS` / `RUN-COMMIT-GATEWAY`. Both are unbound because nothing READS a trailer, and writing one is not proving a commit's tree diff equals the item-owned delta. Binding them on the strength of a writer would be exactly the fail-open error `wlxkoz` documents.
- A CLI FLAG FOR TRAILERS. Deliberately not added, reusing the recorded reasoning: the values come from a live run, never from a human, so a public flag would be a contract taken on for nothing.
- BACKFILLING TRAILERS ONTO EXISTING COMMITS. Impossible without rewriting history, and the trailers' value is that they are immutable. Existing commits stay unattributed; any future consumer must tolerate their absence.
- WIDENING WHICH COMMITS CARRY TRAILERS. This plan wires the ONE shipped commit path. If other commit paths should also carry them, that is a broader convention change needing its own decision, and `offer_commit`'s empty default means nothing else changes meanwhile.

## Scope check

- Over-scope: none. One call site, one threaded parameter, two test modules.
- Scope-Paths justification: `agent_workflows/oc_runipd.py` holds `commit_backlog_close` and its `offer_commit` call, plus `process_backlog_close` which already receives the `state` carrying `run_id`, i.e. E-02 and E-03 in full; `agent_workflows/git_commit_helper.py` holds `run_item_trailers` and `offer_commit` and is in scope ONLY in case the canonical formatter needs a docstring correction now that a real consumer exists (a change of substance there would be a scope-widening finding, since the mechanism is already tested and correct); `tests/test_runner_backlog_close.py` is the existing suite for the target function and must show its guards unchanged (E-05), including its source-substring assertion; `tests/test_run_trailer_wiring.py` is new and carries the git-parser read-back, the empty case, and the shared-object identity assertion (E-04). `agy_runipd.py` is deliberately NOT in scope: F-2 establishes it reaches the shared function by import, so it needs no edit, and editing it would contradict this plan's central claim.
- Under-scope, stated rather than left as `none`: this plan adds no trailer READER, does not touch finalize or `ipd_lifecycle.py`, does not touch `tests/test_finalize_scope_ownership.py` or invert its characterization test, does not bind either waiting finding code, adds no CLI flag, backfills nothing, and does not widen which commit paths carry trailers. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- A GIT-PARSER READ-BACK TEST in a throwaway repository: `git log --format='%(trailers:key=AW-Run,valueonly)'` and the same for `AW-Item`, both non-empty and correct. An assertion on the composed message string alone is NOT sufficient and does not satisfy this requirement.
- AN EMPTY-CASE TEST: with no run id, the commit carries NEITHER key and its message is byte-identical to today's.
- A SHARED-OBJECT IDENTITY ASSERTION that `agy_runipd.commit_backlog_close is oc_runipd.commit_backlog_close`, proving one change covers both hosts.
- `tests/test_runner_backlog_close.py` re-run with ITS OWN summary line pasted, since it guards every measured fix in the target function including a source-substring assertion.
- GUARD-PRESERVATION ASSERTIONS with trailers present: the id6 basename filter still excludes another item's concurrently-modified file; fewer than two paths still returns None; the `" D <path>"` porcelain entry still parses without truncation; an untracked file is still staged individually.
- NEGATIVE PROOF that no trailer CONSUMER was added: show that nothing in `ipd_lifecycle.py` reads a trailer.
- A POST-CHANGE HISTORY CHECK is NOT required and must not be faked: this plan's own commits may carry trailers only if made through the runner, so if you cannot produce one, say so plainly rather than asserting history now contains trailers.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

`run_item_trailers`'s DOCSTRING says the mechanism exists "so callers do not hand-format the keys (and drift)". With a real runner consumer it should also record WHERE the values come from (the live run's state, never a human or a synthesized id), because the tempting future change is to accept them from an argument for convenience and that would let an unattested trailer into history.

`work_cmd._trailers_from_args`'s DOCSTRING states that "the runner wiring is deliberately deferred". That sentence becomes FALSE once E-02 lands and it is the sentence a future reader would trust. Correct it to say the runner now wires them at the shared commit path, and preserve the reasoning about not adding a public flag, which still holds. NOTE this file is NOT in `Scope-Paths`: a docstring correction there is a legitimate scope-widening finding to declare and reconcile at finalize rather than to make silently, and if the executor prefers, it may instead record the staleness for a follow-up. Do not leave a knowingly false docstring without doing one or the other.

Spec `25kzda` 4.6 already specifies the trailers, and 4.2's `RUN-COMMIT-CONTENTS`/`RUN-COMMIT-GATEWAY` rows correctly say those codes are unbound because nothing READS a trailer. That stays true after this plan: do NOT edit those rows. The 4.2 table is transcribed into `run_evidence.RUN_FINDING_CODES` under a byte-equality test, so an incidental cell edit IS a code change and would fail the suite.

## Open questions

### OQ-01: Should this land before or after `h9cn0y` executes?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: EITHER ORDER IS SAFE, because the two plans touch DISJOINT code and this one adds no reader. `h9cn0y`'s Scope-Paths are `ipd_lifecycle.py` plus two finalize test modules; this plan's are `oc_runipd.py`, `git_commit_helper.py` and two other test modules, with no overlap. `h9cn0y` explicitly does not consume trailers (its E-02 forbids a run-record dependency and its F-14 records that nothing can be consumed today), so landing this first does not change its behavior, and landing it second does not invalidate anything here. No `Item-Dependencies` edge is declared for that reason. What DOES depend on order is the FOLLOW-UP that revisits `h9cn0y`'s accepted cost, which needs both this plan's writer and that plan's predicate in place; that follow-up is named in Deferred and is not this plan.

### OQ-02: Should every commit path carry trailers, or only the runner's shipped commit?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ONLY THE RUNNER'S SHIPPED COMMIT, for now, and the reason is that a trailer must be TRUE. `AW-Run`/`AW-Item` assert that a specific run's specific item produced this commit; only the runner knows that. `aw set`, `aw rename` and `aw archive` also call `offer_commit`, but a human running them has no run id, and a synthesized one would be a false ownership claim in immutable history, which is worse than absence (the same reasoning `h9cn0y` E-03 uses to refuse naming a sha it cannot substantiate). `offer_commit`'s empty default means those callers are unaffected without any special-casing. Widening later is a convention decision that should be made when a reader exists to care.

### OQ-03: What should a future reader do about the commits that will never carry a trailer?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: TOLERATE THEIR ABSENCE AND NEVER INFER FROM IT, which is a constraint on the future reader rather than work for this plan, recorded here so the next plan does not assume a clean corpus. Backfilling is impossible without rewriting history and would destroy the immutability that makes a trailer worth trusting. So an untrailered commit means UNKNOWN ownership, never "not the run's": treating absence as evidence would be the fail-open inference this repository has already rejected twice, once for the host capabilities and once for authorship-based attribution. The consuming plan must fail closed on an untrailered commit.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the ACTUAL output for all four claims at your HEAD: the trailer symbols and `offer_commit`'s signature; the trailer-count search over recent history and the `cli.py` grep; the `offer_commit` call-site count in BOTH runners plus `agy_runipd.py`'s import line; and `h9cn0y`'s current `- Status:`. State explicitly whether claim (c) or (d) has moved, and if either has, paste the re-scope or the STOP rather than proceeding.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the changed call site showing `run_item_trailers` used (not a hand-built string) and the run id threaded from state. Paste NEGATIVE proof that no `.aw/records/runs/` read and no global lookup was introduced. Paste the signature change and confirm `agy_runipd.py`'s import still resolves by importing it in a live interpreter. THEN paste a diff or side-by-side of the function's four guards showing each is textually unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the comment at the site stating that a missing run id omits the trailer and that nothing is synthesized. Paste proof that no new CLI flag exists (search for the trailer keys and any new argument in both runners and `cli.py`). Quote the code path showing the omission is achieved by the formatter's own empty-safe behavior rather than by a special case.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the ACTUAL passing output of the read-back test AND quote the `git log --format='%(trailers:key=AW-Run,valueonly)'` assertion, so it is visible that git's own parser recognized the trailer rather than the test matching a substring. Paste the `AW-Item` assertion too. Paste the empty-case assertion showing the message is byte-identical without a run id. Paste the `agy_runipd.commit_backlog_close is oc_runipd.commit_backlog_close` assertion and its result.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `tests/test_runner_backlog_close.py`'s OWN summary line; if its source-substring assertion at `:576` failed, quote what it asserts and justify the edit rather than loosening it. Paste the four guard-preservation assertions and their results. Paste NEGATIVE proof that nothing in `ipd_lifecycle.py` reads a trailer. THEN paste the BARE `python3 -m pytest` summary lines before and after and state the failure-set delta explicitly. If you could not produce a real trailered commit in this repository's history, say so plainly rather than claiming history now contains one.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is narrow by construction: it wires ONE parameter at ONE call site that both hosts already share. It carries no blocking open question, because the design decisions it faced (what to do without a run id, which commit paths qualify, what a future reader owes an untrailered commit) are all resolved above from existing recorded reasoning rather than needing a new maintainer ruling.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Re-locate every symbol by NAME, never by the line numbers cited here: `oc_runipd.py` and `agy_runipd.py` are under concurrent edit by live runs and their line numbers moved roughly seventy and ninety-five lines in a single day. Do NOT edit `agy_runipd.py`, `ipd_lifecycle.py`, or `tests/test_finalize_scope_ownership.py`: each would either contradict this plan's central claim or take work an approved plan already owns. Paste ACTUAL test output and never claim a trailer exists in history without showing git parsing it. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the git-parser read-back and the negative proof that no consumer was added. On finalize, file the follow-up named in Deferred (revisit `h9cn0y`'s accepted cost now that trailers exist) rather than leaving that dependency implicit.
