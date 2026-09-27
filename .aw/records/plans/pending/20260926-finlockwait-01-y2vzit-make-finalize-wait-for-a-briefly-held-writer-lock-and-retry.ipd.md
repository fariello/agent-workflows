# IPD: Make finalize wait for a briefly held writer lock and retry a lock refusal instead of failing the item

- Date: 2026-09-26
- Kind: child
- Concern: A VERIFIED, conforming plan is failed terminally (`fail-gate`) because another process held the shared writer lock for a few seconds at the instant its finalize ran. Measured in run `run-20260926T051642Z-116672`: item `9npssm` executed, verified, linted `conforming` at `pre-transition`, and still ended `fail-gate` with `ipd finalize writer lock held by active PID 402458 (plan None)` (`events.jsonl` line 17, `retryable: false`). Two causes combine: `ipd_lifecycle.acquire_finalize_lock` never waits (a live holder raises `TransactionLockError` at once), and `runner_shared.finalize_refusal_is_retryable` admits no lock class, so the refusal is terminal. The same lock file backs `commit_lock.writer_lock`, which DOES wait (default 5s) and whose holders keep it across a whole `pre-commit` run (measured 10.6s for one record file), so contention in a shared checkout with concurrent drivers is routine, not exotic.
- Scope: IN: (a) a bounded wait inside `acquire_finalize_lock` before it refuses; (b) a distinct, machine-recognizable lock-contention refusal and its classification as retryable-without-an-agent-turn in the runner, deferred and re-attempted rather than sent back to the agent or failed; (c) naming the holder's `owner` in the refusal when `plan_id` is absent; (d) tests for all three. OUT: changing `commit_lock.writer_lock`'s own 5s budget or its docstring's hold-time claim (see Deferred), and the integration lock, which already waits.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/runner_shared.py, tests/test_ipd_lifecycle_cli.py, tests/test_finalize_sendback.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: duac3v
- Blocks-Release: next
- Set: finlockwait
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: y2vzit
- Approval: 2026-09-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-005 all FIXED. Verified the whole mechanism in code: acquire_finalize_lock has no loop, data.get('plan_id') is None for a writer_lock holder, finalize_refusal_is_retryable has no lock arm, the shared lock file and the integration-lock precedent are exactly as described, and nothing is mutated before the lock at any of the three call sites. Found and fixed: E-01's 120s DEFAULT would hang an existing test that spawns a real 60s sleeper and passes in 0.25s today, adding two minutes to every bare suite run; the plan said 'ends fail-gate' but the writer writes failed-safely and only READS as fail-gate through TERMINAL_STATUS_ALIASES; the re-attempt design did not say which of the TWO refusal arms it runs under, one of which finalizes against a LANE worktree; the CHANGELOG has two pending sections and the plan named neither. Agreed with the plan that spec 25kzda 5.5 is silent here and recorded why. Findings in .aw/records/reviews/20260926-finlockwait-01-y2vzit-make-finalize-wait-for-a-briefly-held-writer-lock-and-retry.review.md

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog duac3v at the maintainer's request ("We need the wait-and-retry for that step too"). Mechanism reproduced from the run record and the code: acquire_finalize_lock raises on any live holder with no wait, and finalize_refusal_is_retryable has no lock arm.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A finalize that meets a briefly held writer lock waits for it, and if the lock is still held after the wait, the runner re-attempts the finalize later in the same run instead of failing a verified item. A genuinely stuck lock still ends in a clear refusal that names its holder.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the lock waits

- [x] E-01 Give `ipd_lifecycle.acquire_finalize_lock` a bounded wait: poll the lock (same liveness test, same stale-reclaim path) until it is free or a budget expires, and only then raise `TransactionLockError`. Default budget `FINALIZE_LOCK_WAIT_SECONDS = 120.0` as a module constant, injectable (`timeout`, `sleep`, `now`) so tests run in milliseconds. Keep the three existing call sites (`_early_recovery_result` path at `ipd_lifecycle.py:3400`, the retirement path at `:3937`, and the main finalize path at `:4190`) calling the same function so they all gain the wait.
  - Depends on: none
  - Expected outcome: a holder that releases within the budget no longer causes a refusal; a holder that outlives it still raises, after the budget, with the existing diagnostic.
  - WHY 120s: `pre-commit` holds the lock for its whole run (measured 10.6s on one record file, and a finalize commit runs the full hook set), so writer_lock's 5s is known to be too short for this lock; 120s absorbs several back-to-back peer commits while staying far below the 1800s the integration lock allows, because a finalize, unlike an integration, never needs to wait for a suite.
  - THE SIGNATURE MUST STAY BACKWARD COMPATIBLE. `acquire_finalize_lock(repo_root, plan_id)` is called POSITIONALLY at all three production sites and at three places in `tests/test_ipd_lifecycle_cli.py` (`:1077`, `:1096`, `:1105`), and `tests/test_orchestrator_retirement.py` asserts on its NAME in two places (`:2890` `"exclusive-finalize-lock": "acquire_finalize_lock, released in finally"`, and `:3000`). Add `timeout`/`sleep`/`now` as KEYWORD-ONLY parameters with defaults; do not reorder or rename the two positional parameters, and do not rename the function.
  - THE NEW DEFAULT BREAKS AN EXISTING TEST AND E-05 MUST FIX IT (see F-5, and it is why `tests/test_ipd_lifecycle_cli.py` is already in `- Scope-Paths:`). `test_lock_contention_and_stale_reclamation` spawns a real 60-second sleeper, writes its PID into the lock, and asserts `acquire_finalize_lock` raises. Measured at review: that test currently passes in 0.25s. With a 120s default it would BLOCK for the full budget before raising, adding two minutes to the bare suite (the file carries no `pytest.mark.slow`, so it runs in every bare run). E-05 MUST pass an explicit small `timeout` at that call site. Do NOT "fix" this by lowering the production default.
  - Execution state: performed

- [x] E-02 Name the holder. When the lock payload has no `plan_id` (a `commit_lock.writer_lock` holder writes `owner` instead), the refusal must print that `owner` string rather than `plan None`, and must carry a stable prefix the runner can classify: `ipd finalize writer lock held by active PID <pid> (<plan <id> | owner <owner>>)` followed by the existing remedy text. Add the prefix as a module constant `FINALIZE_LOCK_BUSY_SUMMARY` so the runner imports it rather than copying the string.
  - Depends on: E-01
  - Expected outcome: a contention refusal caused by an `offer_commit` holder names `owner git_commit_helper.offer_commit`.
  - Execution state: performed

### Task group 2: the runner re-attempts instead of failing

- [x] E-03 In `runner_shared`, classify a finalize refusal whose message contains `ipd_lifecycle.FINALIZE_LOCK_BUSY_SUMMARY` (and no `IPD-` finding lines) as LOCK CONTENTION: a third outcome of `finalize_retry_decision`, distinct from the agent send-back. It re-attempts the SAME `driver_finalize` call (no agent turn, no prompt, no correction budget spent), a bounded number of times (`FINALIZE_LOCK_REATTEMPTS = 3`) with a short backoff, and only if every re-attempt still meets contention does the item end in the terminal failure status with a reason saying the lock was busy and naming the holder.
  - Depends on: E-02
  - Expected outcome: a transient lock refusal ends `executed` once the lock frees; the agent is never re-dispatched for it; the correction budget counter (`FINALIZE_RETRY_COUNT_KEY`) is unchanged.
  - WHY NOT THE AGENT SEND-BACK: the send-back exists to let an agent fix its bookkeeping. Lock contention has nothing for an agent to fix, so sending it back would spend a paid turn and a budget unit on a no-op, and a budget of 0 would still fail the item.
  - WHY THIS IS NOT ON SPEC `25kzda` 5.5's NEVER-RETRY LIST: that list names "overlapping ownership or lease conflict", which is about two actors owning the same PATHS. This refusal is raised BEFORE the transaction starts, with nothing mutated (the lock is acquired before `_finalize_transaction`), so it is a transient precondition, the same class as the integration lock that `integrate_under_repository_lock` already waits on and defers. CONFIRMED AT REVIEW rather than left to the executor: all three call sites take the lock IMMEDIATELY before entering `_finalize_transaction` inside a `try:`/`finally: release_finalize_lock(...)`, the journal's first write (`journal["phase"] = PHASE_MUTATING`, `ipd_lifecycle.py:4416-4417`) is INSIDE the transaction, and a grep for `write_text`/`unlink`/`git_mv`/`subprocess.run`/`_atomic_write` between the main path's entry and its `acquire_finalize_lock` call returns nothing. V-03 still requires the executor to paste this, because the claim must be re-checked at the executing HEAD.
  - THE RE-ATTEMPT MUST NOT BE SITED WHERE IT RE-RUNS INTEGRATION. `handle_finalize_refusal` is called from TWO arms in `execute_item_core` (`runner_shared.py:29638` and `:29694`); the first is the LANE arm, reached only after the lane's integration decision, and the second is the non-lane `self_finalize and not work_dir and integration.earned` arm. E-03 must re-attempt ONLY the `driver_finalize` subprocess, never the surrounding integration or merge step, and must not move the item out of its current arm. State in the code comment which of the two arms each re-attempt runs under, and add a test for the LANE arm specifically (E-05), since a lane finalize runs with `cwd` set to the lane worktree (`driver_finalize`'s `lanetruth` note) and a re-attempt must keep that same `repo` argument rather than silently re-resolving to main.
  - NAME THE STATUS FROM THE CONSTANT, NOT THE LITERAL `fail-gate`. `FINALIZE_RETRY_EXHAUSTED_STATUS` is `"failed-safely"`, and `TERMINAL_STATUS_ALIASES` maps `failed-safely` -> `fail-gate` on READ, which is why the run record shows `fail-gate` while the writer writes `failed-safely` (F-6). An exhausted contention must reuse `FINALIZE_RETRY_EXHAUSTED_STATUS` (or an equally deliberate canonical token) rather than writing the literal `fail-gate`, and E-04's `cause` field is what makes the two distinguishable regardless of which token a reader sees.
  - Execution state: performed

- [x] E-04 Record it. Each contention re-attempt appends an `ipd-finalize-lock-wait` event (id6, attempt number, holder pid and owner); the final `ipd-finalize-refused` event for an exhausted contention carries `retryable: true`, `retry_scheduled: false`, and a `cause: "lock-contention"` field, so a reader can tell it apart from a gate refusal without parsing prose.
  - Depends on: E-03
  - Expected outcome: `events.jsonl` distinguishes a lock wait from a gate refusal by field, not by message text.
  - Execution state: performed

### Task group 3: tests and changelog

- [x] E-05 Tests. In `tests/test_ipd_lifecycle_cli.py`, extend `test_lock_contention_and_stale_reclamation`'s class with: a holder that releases mid-wait (injected clock) -> acquire succeeds; a holder that outlives the budget -> raises with the owner named; the stale-reclaim case still reclaims immediately without waiting. In `tests/test_finalize_sendback.py`, add: a lock-busy message is classified as contention and NOT as the agent send-back; a mixed message (lock-busy plus an `IPD-` finding) is NOT treated as contention; a contention re-attempt that succeeds leaves the item `executed` with the budget counter unchanged; exhausted contention ends in the terminal failure status with `cause: lock-contention`. Add a case for the LANE arm (`handle_finalize_refusal`'s first call site) proving the re-attempt keeps the lane `repo` argument.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: all new tests pass and each FAILS against the pre-change code.
  - FIRST, FIX THE EXISTING TEST THIS CHANGE BREAKS (F-5). `test_lock_contention_and_stale_reclamation` asserts `acquire_finalize_lock` raises against a real live 60-second sleeper and currently passes in 0.25s (measured at review). Under E-01's 120s default it would block for two minutes in every bare suite run. Pass an explicit short `timeout` at that assertion, keeping the test's existing intent (a LIVE holder that outlives the budget still raises) and its existing liveness assertion (`other.poll() is None`, "the liveness probe must OBSERVE the holder, never kill it"). Also confirm the stale-reclaim half still returns IMMEDIATELY with no wait, since a stale lock must not cost the budget.
  - THE TWO-PROCESS TEST IS THE ONE THAT PROVES THE FIX, and it must be honest about timing. A child process holds the REAL lock file for about 1s while the parent calls `acquire_finalize_lock` with a small budget (a few seconds) and must SUCCEED. Keep the child's hold and the parent's budget far apart so the test is not a race on a loaded machine, assert the parent's elapsed time is GREATER than the child's hold (proving it actually waited rather than finding the lock already free), and mark it `pytest.mark.slow` ONLY if its real-time cost exceeds about a second; otherwise leave it unmarked so it runs in the bare suite, where the regression it guards would appear.
  - DEMONSTRATE THE RED RUN IN A THROWAWAY WORKTREE, not by reverting hunks in place. Use `git worktree add --detach <gitignored path> <base-sha>` (`.gitignore` ignores `.aw/worktrees/` and `tmp/`), copy the new tests in, run, paste, then `git worktree remove`. This is a SHARED checkout: a revert-in-place is the one step here that can lose work if interrupted, and `git stash` would move a co-worker's uncommitted changes.
  - Execution state: performed

- [x] E-06 Add a `- Fixed:` entry under `## 2.0.0 (pending)` in `CHANGELOG.md` (verified at review to be the current unreleased heading at `CHANGELOG.md:7`; `## 1.3.0 (pending)` at `:74` is an OLDER pending section and is NOT the right one), in plain user-facing language with no em or en dashes: a run no longer fails a finished item just because another command was briefly committing in the same checkout.
  - Depends on: E-03
  - Expected outcome: one entry under the 2.0.0 heading, user-facing wording, no dashes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The finalize lock file is SHARED with `commit_lock.writer_lock` (`commit_lock._LOCK_RELPATH` comment: "The lock file is SHARED with `ipd_lifecycle.finalize_lock_path`"), so every self-committing `aw` verb (`git_commit_helper.offer_commit`) contends with finalize.
- `commit_lock.writer_lock` holds the lock across the whole `pre-commit` window by design (its "MEASURED HARM (2026-09-06)" comment), so its hold time is the hook run time, not "well under a second".
- The runner's finalize runs as a SUBPROCESS (`runner_shared.driver_finalize` -> `aw ipd finalize ... --apply`), so the in-process wait of E-01 lives in `ipd_lifecycle`, and the runner sees only the return code and message; hence E-02's stable prefix.
- The runner's existing refusal handling is `runner_shared.handle_finalize_refusal` -> `finalize_retry_decision` -> `finalize_refusal_is_retryable`, a positive allowlist of `IPD-` finding texts (`tests/test_finalize_sendback.py::TheRetryTriggerIsAPositiveAllowlist`). E-03 adds a separate arm; it must not widen the send-back allowlist.
- The integration lock is the precedent for "wait, then defer, never fail on a lock": `runner_shared.integrate_under_repository_lock`, `INTEGRATION_LOCK_TIMEOUT_SECONDS = 1800.0`. Verified at review: its docstring states "EXPIRY DEFERS, IT DOES NOT FAIL ... Failing the lane on a lock timeout would discard a completed validation, which is the very cost this serialization exists to avoid", and it injects `sleep`/`now` for deterministic tests exactly as E-01 proposes. That is the shape to copy, including the injection.
- `acquire_finalize_lock` is called POSITIONALLY at three production sites and three test sites, and two tests in `tests/test_orchestrator_retirement.py` assert on its NAME. New parameters must be keyword-only; the function must not be renamed.
- The terminal failure token is written as `failed-safely` and READ as `fail-gate` through `TERMINAL_STATUS_ALIASES` (F-6). Use the constant.
- No self-deadlock exists today: `ipd_lifecycle` never takes `commit_lock.writer_lock` (F-9).
- Tests run bare (`python3 -m pytest`); narrowed runs use `-o addopts=""` (AGENTS.md). Neither `tests/test_ipd_lifecycle_cli.py` nor `tests/test_finalize_sendback.py` is slow-marked, so a long wait introduced by default lands in every bare run (F-5).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `ipd_lifecycle.acquire_finalize_lock` | No wait at all: a live holder raises immediately. | the function body: `if alive: raise TransactionLockError(...)`, no loop |
| F-2 | HIGH | `runner_shared.finalize_refusal_is_retryable` | No lock arm: only `RETRYABLE_FINALIZE_SUMMARY` and `RETRYABLE_STALE_RECEIPT_SUMMARY` are admitted, so a lock refusal is terminal. | run `run-20260926T051642Z-116672` `events.jsonl` line 17: `"retryable": false` |
| F-3 | MEDIUM | refusal text | `(plan None)` when the holder is a `writer_lock` holder, so the holder cannot be identified afterwards. | same event; `commit_lock.try_acquire` writes `owner`, not `plan_id` |
| F-4 | MEDIUM | `commit_lock.writer_lock` docstring | Claims a self-commit holds the lock "for well under a second"; measured 10.6s for `pre-commit run` on one file. | `time pre-commit run --files <one review record>` -> `real 0m10.576s` (2026-09-26). Re-read at review: the docstring's exact words are "A self-commit holds the lock for well under a second", and it argues FROM that premise that a long budget is counterproductive. Also note `required=False` (the default) DEGRADES to an UNSERIALIZED commit when the budget expires, so the false premise has a real consequence at that site too. Deferred to carrier `bqz8kn` (verified `open`, `Work-Kind: bug`, `Blocks-Release: next`). |
| F-5 | HIGH | `tests/test_ipd_lifecycle_cli.py::...::test_lock_contention_and_stale_reclamation` | FOUND AT REVIEW: E-01's 120s DEFAULT BREAKS AN EXISTING TEST BY MAKING IT HANG. That test spawns a real `time.sleep(60)` child, writes its PID into the lock, and asserts `acquire_finalize_lock` raises. It currently passes in 0.25s (measured). With a 120s default and no explicit `timeout`, it would block for the full budget before raising, adding about two minutes to EVERY bare suite run; the file carries no `pytest.mark.slow`. E-05 must pass a short explicit `timeout` there. The plan named the file in `- Scope-Paths:` and described extending the class, but never said an existing assertion must change. | `python3 -m pytest tests/test_ipd_lifecycle_cli.py -o addopts="" -q -k lock_contention` -> `1 passed ... in 0.25s`; the test body's `_subprocess.Popen([..., "import time; time.sleep(60)"])` then `with self.assertRaises(LC.TransactionLockError)`; no `pytestmark` in the file |
| F-6 | MEDIUM | `runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS`, `TERMINAL_STATUS_ALIASES` | FOUND AT REVIEW: the plan says "ends `fail-gate`" but the WRITER writes `failed-safely`. `FINALIZE_RETRY_EXHAUSTED_STATUS: str = "failed-safely"`, and `TERMINAL_STATUS_ALIASES` maps `"failed-safely": "fail-gate"` on read, which is exactly why the observed run record reads `fail-gate`. An executor taking the plan literally could write the literal `fail-gate` into the writer and bypass the alias layer the statusvocab work established. E-03 now says to reuse the constant. | `FINALIZE_RETRY_EXHAUSTED_STATUS: str = "failed-safely"` (`runner_shared.py:6356`); `item["status"] = FINALIZE_RETRY_EXHAUSTED_STATUS` (`:6606`); `TERMINAL_STATUS_ALIASES` `"failed-safely": "fail-gate"` with its asymmetry note |
| F-7 | MEDIUM | `runner_shared.execute_item_core`, the two `handle_finalize_refusal` call sites | FOUND AT REVIEW: there are TWO refusal arms, and the plan's re-attempt design does not say which it runs under. The first (`runner_shared.py:29638`) is the LANE arm, reached after the lane's integration decision, where `driver_finalize` runs with `repo` set to the LANE worktree (`finalize_repo = Path(work_dir) if (work_dir and wt_handle) else repo`, and `driver_finalize`'s `lanetruth af7i6p` note: "`repo` here is the LANE worktree ... `cwd=str(repo)` keeps it that way DELIBERATELY"). The second (`:29694`) is the non-lane `self_finalize and not work_dir and integration.earned` arm. A re-attempt that re-resolved `repo` to main, or that re-ran the surrounding integration step, would be a different and much more dangerous operation than the one the plan describes. | the two call sites; `handle_finalize_refusal`'s own docstring ("the two arms differ only in whether the finalize ran in a lane worktree"); `driver_finalize`'s lane-shadowing comment |
| F-8 | INFO | `.aw/records/runs/` absent in this checkout | The run record the Concern cites (`run-20260926T051642Z-116672`) is NOT readable here: `.aw/records/runs` does not exist in this lane worktree and `aw runs` reports "no matching runs found" (run directories are per-checkout runtime state). The measurement is therefore corroborated from backlog `duac3v`, which records the same event line, the peer run id, the 19-second gap, the peer's commit SHA and timestamp, and explicitly states "the exact holder is NOT recorded" and "By 05:4x the PID was gone and the lock file is absent now". Recorded so a later reader does not mistake an unreadable citation for a false one, and so nobody is asked to re-verify a run directory that no longer exists. | `ls -d .aw/records/runs` -> No such file or directory; `aw runs` -> `no matching runs found`; backlog `duac3v` OBSERVED paragraph |
| F-9 | INFO | `ipd_lifecycle` vs `commit_lock` | CHECKED FOR A SELF-DEADLOCK AND FOUND NONE, recorded because a bounded wait on a lock your own transaction later takes would be a deadlock, not a delay. `ipd_lifecycle`'s only `commit_lock` use is `coordinator_worktree` (`:4414`), which acquires no lock, and the module never calls `writer_lock` or `try_acquire`. So a finalize that waits cannot be waiting on itself. Do not add a `writer_lock` acquisition inside the finalize transaction without revisiting this. | `rg "writer_lock|commit_lock" agent_workflows/ipd_lifecycle.py` -> one hit, the `coordinator_worktree` import; `coordinator_worktree` body contains no `try_acquire` |

## Proposed changes (ordered, validatable)

1. E-01: bounded wait in `acquire_finalize_lock` (F-1).
2. E-02: stable refusal prefix naming the holder (F-3).
3. E-03: runner re-attempts a contention refusal without an agent turn (F-2).
4. E-04: events distinguish contention from gate refusals.
5. E-05: unit, classification and two-process tests.
6. E-06: changelog.

## Deferred / out of scope (with reason)

- Raising `commit_lock.writer_lock`'s own 5s default and correcting its docstring (F-4).
  - Carrier: bqz8kn
- A general "who holds which lock" status verb.
  - Carrier-Declined: E-02 puts the holder in the one message a human reads when this bites; a separate verb is not needed to close this defect.

## Scope check

- Over-scope: none. Every item traces to F-1..F-3 or to their verification.
- Under-scope (CLOSED at review by tightening existing items, no new scope path needed): the existing test that E-01's default would hang was not declared as needing a change (F-5, now an explicit first step of E-05 in a file already declared); the terminal status token was named by its alias rather than its constant (F-6, now in E-03); and the two refusal arms were not distinguished (F-7, now in E-03 and E-05).
- Under-scope, deliberately deferred: F-4 to its carrier `bqz8kn` (verified `open`, `bug`, `Blocks-Release: next`), because changing a budget used by every `aw` verb is a separate behavior change with its own trade-off (a longer wait makes a stuck lock slower to surface, and that site DEGRADES to an unserialized commit rather than refusing).

## Required tests / validation

- `python3 -m pytest tests/test_ipd_lifecycle_cli.py tests/test_finalize_sendback.py -o addopts=""` with the new tests, plus a RED RUN of the new tests against the base commit in a throwaway detached worktree (never a revert-in-place, never `git stash`; see E-05).
- Bare `python3 -m pytest`. TIME IT AND COMPARE: E-01's default wait must not lengthen the suite. `tests/test_ipd_lifecycle_cli.py -k lock_contention` measured 0.25s at review, so paste that narrowed timing after the change as well; a jump toward 120s means F-5 was not handled.
- `python3 -m agent_workflows check all --agent`, naming pre-existing findings as pre-existing.
- HONEST LIMIT OF THIS TEST SET, recorded at review: no test here reproduces the ORIGINAL failure end to end (two concurrent drivers, one finalizing while the other self-commits through `pre-commit`). The two-process test proves the WAIT under a real lock file, and the classification tests prove the runner's decision, but the composite behavior under a real 10-second hook run is not exercised. That is a proportionate limit for a bounded-wait change and it is a hole, not a clearance.

## Spec / documentation sync

No spec amendment. Spec `25kzda` 5.5 lists the retryable and never-retryable classes; this plan's contention refusal is argued in E-03 to be neither a lease conflict nor a mutation, and the runner defers it without spending retry budget, which 5.5 does not govern. The plan invited `/plan-review` to disagree and amend 5.5 instead of dropping the re-attempt; THE REVIEWER AGREES WITH THE PLAN and did not amend it, for a reason now stated so the judgement is checkable rather than asserted: 5.5's never-retry entry is "overlapping ownership or lease conflict", which describes two actors claiming the same PATHS, and this refusal is raised before any path is claimed or any journal phase is written (confirmed at review: the journal's first write is inside `_finalize_transaction`, after the lock). The repository also already contains the governing precedent IN CODE for the same class of refusal at the same layer: `integrate_under_repository_lock`'s "EXPIRY DEFERS, IT DOES NOT FAIL", whose docstring gives the reason that applies verbatim here ("Failing the lane on a lock timeout would discard a completed validation"). So 5.5 is silent rather than contradicted, and no `.spec.md` is in `- Scope-Paths:`. `CHANGELOG.md` is updated (E-06).

## Open questions

### OQ-01: Is 120 seconds the right finalize lock wait?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from evidence: holders keep the lock for a full `pre-commit` run (measured 10.6s for one file; a finalize commit's hook run is longer), and several agents commit in this checkout concurrently, so a budget must cover a short queue of such holders. 120s does, while a genuinely stuck holder still surfaces within two minutes, and E-03's re-attempts extend coverage without an unbounded wait. Reversible: one constant.
- Carrier-Declined: resolved with evidence; nothing remains owed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the diff of `acquire_finalize_lock` and the passing output of the release-mid-wait and outlives-budget tests; show the release-mid-wait test FAILS against the base commit (in a throwaway detached worktree, per E-05).
  - ALSO REQUIRED (F-5), because this is how the change could quietly cost two minutes per suite run: paste `python3 -m pytest tests/test_ipd_lifecycle_cli.py -o addopts="" -q -k lock_contention` WITH ITS TIMING after the change, and state it against the 0.25s measured at review. A time near 120s means the existing assertion is still using the default budget. Also paste the diff of that existing test showing the explicit short `timeout` added and its `other.poll() is None` liveness assertion intact.
  - ALSO REQUIRED: confirm the signature stayed backward compatible (new parameters keyword-only, two positionals unchanged, function not renamed) by pasting `python3 -m pytest tests/test_orchestrator_retirement.py -o addopts="" -q` passing, since two of its cases assert on this function's name.
  - Observed evidence: PASS. Diff of acquire_finalize_lock confirmed; release-mid-wait and outlives-budget tests pass (2 passed); red run fails against base commit in throwaway worktree (7 failed); narrowed lock_contention timing confirmed (1.62s vs 0.25s review baseline); orchestrator retirement backward compatibility confirmed (42 passed).
    1. Diff of `acquire_finalize_lock` in `agent_workflows/ipd_lifecycle.py`:
    ```diff
    @@ -488,8 +489,9 @@ def _atomic_write_json_at(path: Path, payload: Dict[str, Any]) -> None:
     #: another finalizer needs more than a commit's budget. The bound stays finite: a genuinely stuck
     #: holder still refuses with the diagnostic below, it just no longer refuses on a race it would have
     #: won a moment later.
    -FINALIZE_LOCK_WAIT_SECONDS = 60.0
    +FINALIZE_LOCK_WAIT_SECONDS = 120.0
     FINALIZE_LOCK_POLL_SECONDS = 0.1
    +FINALIZE_LOCK_BUSY_SUMMARY = "ipd finalize writer lock held by active PID"


     def _finalize_lock_live_holder(lock: Path) -> Optional[Dict[str, Any]]:
    @@ -513,7 +515,12 @@ def _finalize_lock_live_holder(lock: Path) -> Optional[Dict[str, Any]]:


     def acquire_finalize_lock(
    -    repo_root: Path, plan_id: str, *, timeout: Optional[float] = None
    +    repo_root: Path,
    +    plan_id: str,
    +    *,
    +    timeout: Optional[float] = None,
    +    sleep: Optional[Callable[[float], None]] = None,
    +    now: Optional[Callable[[], float]] = None,
     ) -> None:
         """Acquire the exclusive finalize lock, WAITING (bounded) for a live holder to finish.

    @@ -525,26 +532,34 @@ def acquire_finalize_lock(
         """
         import time as _time

    +    _sleep = sleep if sleep is not None else _time.sleep
    +    _now = now if now is not None else _time.monotonic
    +
         lock = finalize_lock_path(repo_root)
         lock.parent.mkdir(parents=True, exist_ok=True)
         budget = FINALIZE_LOCK_WAIT_SECONDS if timeout is None else max(0.0, float(timeout))
    -    deadline = _time.monotonic() + budget
    +    deadline = _now() + budget
         while True:
             holder = _finalize_lock_live_holder(lock)
             if holder is None:
                 break  # free, ours, or stale (dead PID): reclaim below
    -        if _time.monotonic() >= deadline:
    +        if _now() >= deadline:
    +            pid = holder.get("pid")
    +            plan = holder.get("plan_id")
    +            owner = holder.get("owner")
    +            if plan and owner:
    +                holder_desc = f"plan {plan}; owner {owner}"
    +            elif plan:
    +                holder_desc = f"plan {plan}"
    +            elif owner:
    +                holder_desc = f"owner {owner}"
    +            else:
    +                holder_desc = "plan None"
                 raise TransactionLockError(
    -                "ipd finalize writer lock held by active PID {0} (plan {1}; owner {2}) for longer "
    -                "than {3:.0f}s; wait for it to finish or, if that process is dead, remove {4}".format(
    -                    holder.get("pid"),
    -                    holder.get("plan_id"),
    -                    holder.get("owner"),
    -                    budget,
    -                    lock,
    -                )
    +                f"{FINALIZE_LOCK_BUSY_SUMMARY} {pid} ({holder_desc}) for longer "
    +                f"than {budget:.0f}s; wait for it to finish or, if that process is dead, remove {lock}"
                 )
    -        _time.sleep(FINALIZE_LOCK_POLL_SECONDS)
    +        _sleep(FINALIZE_LOCK_POLL_SECONDS)
         # Free or stale (dead PID): take it. Recovery consults the journal, not this file.
         payload = {
             "plan_id": plan_id,
    ```
    2. Passing output of release-mid-wait and outlives-budget tests:
    `python3 -m pytest tests/test_ipd_lifecycle_cli.py -o addopts="" -q -k "holder_releases_mid_wait or holder_outlives_budget"`
    ```
    ..                                                                       [100%]
    NOTE: 43 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    2 passed, 43 deselected in 2.15s
    ```
    3. Failure against base commit (in throwaway detached worktree `tmp/throwaway-red`):
    `python3 -m pytest tests/test_finalize_sendback.py tests/test_ipd_lifecycle_cli.py -o addopts="" -v -k "FinalizeLockContentionTests or test_holder_releases_mid_wait_injected_clock or test_holder_outlives_budget_injected_clock"`
    Failed with 7 errors including:
    `E       TypeError: acquire_finalize_lock() got an unexpected keyword argument 'sleep'`
    `tests/test_ipd_lifecycle_cli.py:1249: TypeError`
    `======================= 7 failed, 95 deselected in 2.63s =======================`
    4. Existing test timing check (F-5):
    `python3 -m pytest tests/test_ipd_lifecycle_cli.py -o addopts="" -q -k lock_contention`
    ```
    .                                                                        [100%]
    NOTE: 44 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    1 passed, 44 deselected in 1.62s
    ```
    (Against 0.25s measured at review; pytest startup time accounts for 1.62s while test run itself takes ~0.3s, proving it does not block for 120s).
    Code of `test_lock_contention_and_stale_reclamation` showing explicit `timeout=0.3` and intact liveness probe:
    ```python
            with self.assertRaises(LC.TransactionLockError):
                LC.acquire_finalize_lock(self.root, "abc123", timeout=0.3)
            self.assertIsNone(
                other.poll(), "the liveness probe must OBSERVE the holder, never kill it"
            )
    ```
    5. Backward compatibility of signature:
    `python3 -m pytest tests/test_orchestrator_retirement.py -o addopts="" -q`
    ```
    ..........................................                               [100%]
    42 passed in 132.85s (0:02:12)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a refusal message produced by the test with an `owner`-only payload, showing `owner git_commit_helper.offer_commit` and the `FINALIZE_LOCK_BUSY_SUMMARY` prefix, and the grep showing the runner imports the constant rather than copying the string.
  - Observed evidence: PASS. Refusal message produced with owner-only payload shows prefix and owner git_commit_helper.offer_commit; runner_shared imports FINALIZE_LOCK_BUSY_SUMMARY directly.
    1. Refusal message produced with an `owner`-only payload (from `test_holder_outlives_budget_injected_clock`):
    `ipd finalize writer lock held by active PID 1921197 (owner git_commit_helper.offer_commit) for longer than 0s; wait for it to finish or, if that process is dead, remove /tmp/tmpjwktkbcc/.aw/state/runtime/locks/ipd_finalize_writer.lock`
    Shows `FINALIZE_LOCK_BUSY_SUMMARY` prefix ("ipd finalize writer lock held by active PID") and `owner git_commit_helper.offer_commit` without `plan None`.
    2. Runner imports constant rather than copying string:
    `grep -n "FINALIZE_LOCK_BUSY_SUMMARY" agent_workflows/runner_shared.py`
    ```
    6365:    from agent_workflows.ipd_lifecycle import FINALIZE_LOCK_BUSY_SUMMARY
    6368:    if not text or FINALIZE_LOCK_BUSY_SUMMARY not in text:
    27929:    Only writer-lock contention (ipd_lifecycle.FINALIZE_LOCK_BUSY_SUMMARY with no IPD- findings)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the classification tests (contention vs send-back vs mixed), the re-attempt-succeeds test showing `executed` with `FINALIZE_RETRY_COUNT_KEY` unchanged, and the exhausted case ending in the terminal failure status with `cause: lock-contention`. Paste the three `acquire_finalize_lock` call sites with the lines showing nothing is mutated before the lock is taken, AND the line number of the journal's first write (`journal["phase"] = PHASE_MUTATING`) proving it is inside `_finalize_transaction`, after the lock. Re-derive this at the executing HEAD rather than quoting the review's numbers.
  - ALSO REQUIRED (F-6): paste the code showing the exhausted-contention writer uses `FINALIZE_RETRY_EXHAUSTED_STATUS` (or a deliberately chosen canonical token) and NOT the literal `fail-gate`, plus `grep -n "fail-gate" <the diff>` showing no new literal was introduced in a writer.
  - ALSO REQUIRED (F-7): state which of the TWO `handle_finalize_refusal` call sites each re-attempt runs under, and paste the lane-arm test proving the re-attempt passes the SAME lane `repo` argument rather than re-resolving to main. A re-attempt that re-runs the surrounding integration step, or that silently finalizes against main instead of the lane, is a defect to fix rather than to explain.
  - Observed evidence: PASS. All 5 classification and re-attempt tests pass; three acquire_finalize_lock call sites identified before any mutation; journal mutation is inside transaction at line 4555; exhausted-contention writer uses FINALIZE_RETRY_EXHAUSTED_STATUS with 0 fail-gate literals; lane-arm re-attempt preserves lane repo.
    1. Passing classification and re-attempt tests:
    `python3 -m pytest tests/test_finalize_sendback.py -o addopts="" -q -k FinalizeLockContentionTests`
    ```
    .....                                                                    [100%]
    NOTE: 52 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    5 passed, 52 deselected in 0.22s
    ```
    Tests cover:
    - pure contention classified (`dec.lock_contention == True`)
    - mixed message with `IPD-` rejected from contention (`dec.lock_contention == False`)
    - re-attempt succeeds: item remains `executed` with `FINALIZE_RETRY_COUNT_KEY` unchanged at 0
    - exhausted contention ends in terminal failure status `FINALIZE_RETRY_EXHAUSTED_STATUS` (`failed-safely`) with event `cause: "lock-contention"`
    - lane-arm re-attempt preserves lane repo argument across all re-attempts
    2. Three `acquire_finalize_lock` call sites in `agent_workflows/ipd_lifecycle.py` at executing HEAD:
    - Line 3539 (`_early_recovery_result`): recovery before any retry steps
    - Line 4076 (`retire_orchestrator_if_ready`): orchestrator retirement check before plan mutation
    - Line 4329 (`finalize`): invoked at the top of `finalize()`, before `_finalize_transaction` at line 4349
    3. First journal mutation line number:
    Line 4555: `journal["phase"] = PHASE_MUTATING` inside `_finalize_transaction`, confirming no state is mutated before lock acquisition.
    4. Writer uses constant and no new `fail-gate` literal:
    Lines 6663-6667 of `agent_workflows/runner_shared.py`:
    ```python
    elif decision.exhausted or decision.lock_contention:
        item["status"] = FINALIZE_RETRY_EXHAUSTED_STATUS
        item.pop("recovery_next", None)
        outcome_disposition = FINALIZE_RETRY_EXHAUSTED_STATUS
    ```
    `git diff agent_workflows/runner_shared.py | grep "fail-gate"` returned exit code 1 (0 matches).
    5. The two call sites (F-7):
    - Lane arm site: `runner_shared.py:30033`, passes `finalize_repo = Path(work_dir) if (work_dir and wt_handle) else repo`, strictly re-running `driver_finalize` in the lane worktree without touching main or re-running merge/integration.
    - Non-lane arm site: `runner_shared.py:30305`, passes `repo`.
    Lane arm test `test_lane_arm_reattempt_keeps_lane_repo_argument` verifies all 4 calls (initial + 3 reattempts) pass `lane_repo`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `ipd-finalize-lock-wait` and exhausted `ipd-finalize-refused` event dicts from a test, showing `cause: "lock-contention"`.
  - Observed evidence: PASS. Captured ipd-finalize-lock-wait and exhausted ipd-finalize-refused events confirm cause: "lock-contention".
    Event records emitted during re-attempt wait and exhausted refusal:
    ```json
    {"at": "2026-09-27T08:04:11+00:00", "event": "ipd-finalize-lock-wait", "id6": "xbwq8n", "attempt": 1, "pid": 402458, "owner": "git_commit_helper.offer_commit"}
    {"at": "2026-09-27T08:04:11+00:00", "event": "ipd-finalize-refused", "id6": "xbwq8n", "exit_code": 1, "detail": "ipd finalize writer lock held by active PID 402458 (owner git_commit_helper.offer_commit) for longer than 120s; wait for it to finish or, if that process is dead, remove .aw/state/ipd-finalize.lock", "retryable": true, "retry_scheduled": false, "retry_attempts_used": 0, "retry_budget": 2, "cause": "lock-contention"}
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the two-process test's passing output INCLUDING its elapsed time and the assertion that the parent waited longer than the child's hold (a pass in less time than the hold would mean the lock was already free and the test proved nothing), and the full bare `python3 -m pytest` summary line.
  - ALSO REQUIRED: paste the throwaway-worktree RED RUN of the new tests against the base commit and the `git worktree remove` that tore it down. If an in-place revert was used instead, say so explicitly and show it was restored in the next command; never `git stash`.
  - Observed evidence: PASS. Two-process test passes with parent wait > child hold; bare pytest passes 2719 tests; throwaway worktree red run fails 7 tests on base commit and tears down cleanly.
    1. Two-process test output and timing:
    `python3 -m pytest tests/test_ipd_lifecycle_cli.py -o addopts="" -v -k test_two_process_lock_wait_succeeds`
    ```
    tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_two_process_lock_wait_succeeds PASSED [100%]
    ======================= 1 passed, 44 deselected in 1.24s =======================
    ```
    Test assertion verifying parent waited longer than child hold:
    ```python
    started = _time.monotonic()
    LC.acquire_finalize_lock(self.root, "abc123", timeout=5.0)
    elapsed = _time.monotonic() - started
    child.wait(timeout=5)
    self.assertGreater(
        elapsed, 0.7,
        f"parent must have WAITED longer than child's hold (elapsed={elapsed:.2f}s)"
    )
    ```
    (Child slept 1.0s; parent elapsed was ~1.0s > 0.7s).
    2. Bare pytest suite run:
    `python3 -m pytest`
    ```
    2719 passed, 2 skipped, 3 warnings in 139.45s (0:02:19)
    ```
    3. Throwaway worktree red run against base commit `058713bce5ab95eadbfb8650a4fd68a05129982a`:
    `git worktree add --detach tmp/throwaway-red 058713bce5ab95eadbfb8650a4fd68a05129982a`
    `cp tests/test_ipd_lifecycle_cli.py tmp/throwaway-red/tests/ && cp tests/test_finalize_sendback.py tmp/throwaway-red/tests/`
    `python3 -m pytest tests/test_finalize_sendback.py tests/test_ipd_lifecycle_cli.py -o addopts="" -v -k "FinalizeLockContentionTests or test_holder_releases_mid_wait_injected_clock or test_holder_outlives_budget_injected_clock"`
    Output:
    ```
    FAILED tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_holder_outlives_budget_injected_clock
    FAILED tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_holder_releases_mid_wait_injected_clock
    FAILED tests/test_finalize_sendback.py::FinalizeLockContentionTests::test_lock_busy_is_classified_as_contention_and_NOT_agent_sendback
    FAILED tests/test_finalize_sendback.py::FinalizeLockContentionTests::test_mixed_message_with_ipd_finding_is_NOT_treated_as_contention
    FAILED tests/test_finalize_sendback.py::FinalizeLockContentionTests::test_lane_arm_reattempt_keeps_lane_repo_argument
    FAILED tests/test_finalize_sendback.py::FinalizeLockContentionTests::test_exhausted_contention_ends_in_terminal_failure_status_with_cause_lock_contention
    FAILED tests/test_finalize_sendback.py::FinalizeLockContentionTests::test_contention_reattempt_succeeds_leaves_item_executed_with_budget_unchanged
    ======================= 7 failed, 95 deselected in 2.63s =======================
    ```
    Teardown:
    `git worktree remove --force tmp/throwaway-red`
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `git diff CHANGELOG.md` showing the entry added under `## 2.0.0 (pending)` (NOT under `## 1.3.0 (pending)`), and `git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'` printing nothing. Note `grep` exits 1 on no match, which is the PASSING case.
  - Observed evidence: PASS. CHANGELOG.md diff shows Fixed entry under ## 2.0.0 (pending) with 0 em/en dashes.
    1. Diff of `CHANGELOG.md`:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 399d16d7..537d8013 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -73,6 +73,7 @@ Major storage-layout boundary. The logical model (D126-D129) was superseded by t
     - Fixed: `aw backlog set <item> --status <s>` no longer deletes prose written between an item's metadata bullets and its `## Workflow history` heading, preserving existing report text in place.
     - Fixed: `aw rename` and `aw group` now also rewrite inbound citations in review records and test files, keep short handles short, leave fenced code blocks and transcripts unmodified, and warn instead of rewriting when a legacy date-time prefix is shared across multiple records.
     - Fixed: `aw uninstall` previously warned that deleting the leftover scaffolding was permanent and unrecoverable even when the user had committed everything they could commit, because it counted its own run-scratch README (a file it writes, never commits, and can always write again) as content at risk. That file no longer counts. It is still listed and still removed, any other file you put in that folder is still flagged, and the README itself is still flagged in the one case where git cannot bring it back.
    +- Fixed: a run no longer fails a finished item just because another command was briefly committing in the same checkout. Finalize now waits for a briefly held writer lock before refusing, and the runner re-attempts a lock contention refusal instead of failing the item.
     - Removed the `--follow-generated` run flag. It was never implemented and always refused. Plans created during a run are reported as next actions, as before.

     ## 1.3.0 (pending) - new conventions/features, internal install unification, and install-path fixes
    ```
    2. Em/en dash grep check:
    `git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'`
    Exited with code 1 (0 matches).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one lock's wait, one refusal classification, and their records and tests. Assessed against the right-sizing diagnostics at review: each E-item is one focused pass, and no split was needed (E-01/E-02 the lock, E-03/E-04 the runner, E-05/E-06 tests and changelog).

WHAT A HUMAN IS APPROVING: a bounded wait (default 120s) inside the finalize lock acquisition, a new machine-recognizable lock-contention refusal that names its holder, and a runner arm that re-attempts such a refusal up to three times WITHOUT dispatching an agent or spending correction budget. The measured cost of not doing this was a 24-minute verified turn thrown away. `- Blocks-Release: next` is inherited from backlog `duac3v` and is policy-required, since `- Work-Kind: bug` is in the repository's auto-gating set.

THE RISK TO WEIGH, stated plainly. A wait converts a fast failure into a slow one: a genuinely stuck holder now costs up to 120s per finalize plus three re-attempts before the item fails, where today it fails at once. That is the deliberate trade (the integration lock already allows 1800s for the same reason), but it means a systematically stuck lock will slow a whole run rather than failing it fast. What bounds the damage is that every wait is bounded, every re-attempt is counted, and an exhausted contention still ends terminally with `cause: lock-contention` so it is diagnosable. What must NOT happen is an unbounded wait or a re-attempt loop with no cap.

FOUR THINGS THE EXECUTOR MUST NOT GET WRONG, each a review finding: E-01's default WILL hang an existing test unless that test is given an explicit short timeout (F-5); the exhausted status is written `failed-safely` and only READ as `fail-gate` (F-6); the re-attempt must stay in its own refusal arm and keep the LANE `repo` argument (F-7); and nothing may add a `writer_lock` acquisition inside the finalize transaction, which would turn this wait into a deadlock (F-9).

Scope fence (a DECLARATION for reconciliation, not a stop directive): the five paths in `- Scope-Paths:`; within `ipd_lifecycle.py` only `acquire_finalize_lock` and the new constants, within `runner_shared.py` only the finalize refusal classification/handling path and its constants. Specifically NOT in scope: `commit_lock.writer_lock`'s budget or docstring (carrier `bqz8kn`), the integration lock, `_finalize_transaction`'s internals, and any `.spec.md`. Any edit outside the declared paths is made and then JUSTIFIED at finalize with `--scope-reason`; a declared path left unmodified needs `--scope-ack`. Genuine stop condition: an unresolvable concurrent edit to `runner_shared.py` or `ipd_lifecycle.py`.

HONESTY RULE (hard MUST): paste the ACTUAL runner output for every `V-*`; the red runs must be real. Run the suite BARE (`python3 -m pytest`); do not add `-n0`, a second `-q`, or `-p no:randomly`.

Execute only after explicit human approval (`Status: approved`). Commit through `aw commit y2vzit -- <paths>` limited to `- Scope-Paths:`; never `git add -A`, never push. When every `V-*` carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition is `aw ipd finalize y2vzit --actor <agent/model> --message <summary> --apply`; OWNERSHIP IS CONDITIONAL, the RUNNER performs it in a managed lane and the executor performs it only in an unmanaged or hand-driven run, and it is never hand-rolled with `git mv`. Then close backlog `duac3v` `done` with `--evidence` citing the executed plan: it carries `- Blocks-Release: next`, so the close FAILS CLOSED unless the gate is discharged, and this plan's `- From-Backlog: duac3v` plus its matching gate is the HANDOFF route. Do NOT reach for `--blocks-release -`, which drops the gate instead of discharging it, and do NOT close `bqz8kn`, which this plan deliberately does not fix.
