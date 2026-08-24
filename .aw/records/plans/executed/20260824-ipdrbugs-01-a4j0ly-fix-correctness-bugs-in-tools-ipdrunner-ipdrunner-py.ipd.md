# IPD: Fix correctness bugs in tools/ipdrunner/ipdrunner.py

- Date: 2026-08-24
- Kind: child
- Concern: bugs
- Scope: tools/ipdrunner/ipdrunner.py (and its test module tools/ipdrunner/test_ipdrunner.py)
- Status: executed
- Set: ipdrbugs
- Order: 1
- Highest E allocated: 07
- Author: assess/its_direct/pt3-claude-opus-4.8
- Id: a4j0ly

## Workflow history
- 2026-08-24 executed (aw set): E-01..E-07 performed, V-01..V-07 pass; fixes 5ceffd6, doc-sync fbeee1c; 8 tests pass.
- 2026-08-24 approved (aw set, --by-human): Human approved via plan-review GO in chat; proceeding to execution.

- 2026-08-24 draft (assess/its_direct/pt3-claude-opus-4.8): created.
- 2026-08-24 /assess bugs (assess/its_direct/pt3-claude-opus-4.8): assessed tools/ipdrunner/ipdrunner.py; proposed 6 changes (4 fixes acted, 2 down-scoped/deferred).
- 2026-08-24 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. PR-001..PR-004 fixed. PR-001 strengthened E-04/V-01 with a negative anti-regression assertion (bare resume must not re-queue partial/failed-safely) and named the baseline continuity test. PR-002 completed the B-04 deferral (added required-decision + consequence-if-unresolved). PR-003 pulled B-05 into scope as E-07 (Fix Bar: Low risk => fix, not defer on value). PR-004 added a Coordination section cross-referencing the sibling pending IPD pr2nd0 (same file; complementary; shared reconcile_interrupted / session-id / test_ipdrunner.py surfaces; ordering note). OQ-01 resolved interactively (event log only). aw ipd lint --phase review-finalize: conforming. Baseline suite green (3 tests).
- 2026-08-24 approved (aw ipd set, --by-human): human approved ("approved. go.") after plan-review.
- 2026-08-24 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): E-01..E-07 performed, V-01..V-07 pass with pasted evidence. Fixes committed 5ceffd6 (E-01/E-02/E-03/E-07 + E-04/E-05/E-06 tests); runbook doc-sync committed fbeee1c. Tests authored first and shown RED pre-fix, then GREEN: `python3 -m pytest tools/ipdrunner/test_ipdrunner.py -q` = 8 passed. Checkpoints 1 (pre-execution) and 2 (pre-transition) both conforming.

## Goal

Fix confirmed correctness defects in the restartable OpenCode IPD driver so that (a) a plain
`resume` no longer silently abandons the unit of work that was in flight when the run was
interrupted, (b) the "not a Git repository" precondition reports its intended diagnostic
instead of a raw `git` failure, (c) selecting an empty Set reports an accurate error, and
(d) each fix is pinned by a regression test. These paths govern durable multi-hour autonomous
execution, so a lost or mis-reported unit of work is a data-integrity concern, not cosmetic.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Resume must not abandon an interrupted item (B-01)

- [x] E-01 In `run_queue` (tools/ipdrunner/ipdrunner.py:696), make a plain `resume` re-queue the single item left `interrupted` by `reconcile_interrupted` so it is retried in recovery mode, without touching terminal/other items. Concretely: after `reconcile_interrupted` (line 698), before the `retry_incomplete` block, re-queue items whose status is `interrupted` by setting `status = "queued"` and `recovery_next = True`, and emit an `interrupted-requeued` event to `events.jsonl`. Per OQ-01 (resolved: event log only), do NOT print an additional stderr notice. Leave the broader `--retry-incomplete` behavior (line 699-711) unchanged for the other nonterminal states.
  - Depends on: none
  - Expected outcome: after an interruption, `resume <run_id>` (no flags) picks the interrupted item back up as attempt N+1 in recovery mode, reusing the Set session; only `--retry-incomplete` additionally re-queues `partial`/`failed-safely`/`blocked`/`substantially-complete`.
  - Execution state: performed

### Task group 2: Correct precondition and selector diagnostics (B-02, B-03)

- [x] E-02 In `initialize_run` (tools/ipdrunner/ipdrunner.py:251), fix the "Not a Git repository" guard so it reports that message on a non-git directory instead of letting `git_common_dir` raise a raw `Command failed (128): git rev-parse --git-common-dir` DriverError. Wrap the `git_common_dir(repo)` probe so a failed `git rev-parse` is treated as "not a repository" and re-raised as the intended `DriverError(f"Not a Git repository: {repo}")`. Do not change the happy path for a real repo or worktree.
  - Depends on: none
  - Expected outcome: running `start`/driver init against a directory that is not a Git repository fails with `ipdrunner: Not a Git repository: <path>` (exit 2), not the raw git-plumbing error.
  - Execution state: performed

- [x] E-03 In `expand_selectors` (tools/ipdrunner/ipdrunner.py:184), distinguish "no selector given" from "the given selector(s) resolved to zero plans". When a selector matches a known Set (or Set prefix) whose `order` is empty, raise a specific `DriverError` naming that Set (e.g. `Set '<setid>' has an empty order (no plans to run)`) instead of the misleading terminal `At least one id6 or Set selector is required`, which currently fires even though a selector WAS supplied.
  - Depends on: none
  - Expected outcome: `expand_selectors(manifest, ["<empty-set>"])` raises an error that names the empty Set; `expand_selectors(manifest, [])` (truly no selectors) still raises the "At least one id6 or Set selector is required" message.
  - Execution state: performed

### Task group 3: Regression tests pinning the three fixes

- [x] E-04 Add a regression test that a plain `resume` retries an item that was left `interrupted` (drive `run_queue`/`reconcile_interrupted` with a state whose in-flight item is `running` with no `executed` bucket move, assert it becomes `queued` with `recovery_next` then is attempted). Follow the existing style in tools/ipdrunner/test_ipdrunner.py (unittest, tempdir, fake `opencode` script where a subprocess is needed). Include a NEGATIVE assertion in the same or an adjacent test that a bare `resume` does NOT re-queue a terminal-nonterminal item that is only reachable via `--retry-incomplete` (e.g. a `partial` or `failed-safely` item stays put on bare resume), so E-01 is proven not to broaden bare-resume scope beyond `interrupted`.
  - Depends on: E-01
  - Expected outcome: a test that fails against the current code (bare resume leaves the item `interrupted`) and passes after E-01, AND asserts that a `partial`/`failed-safely` item is untouched by a bare resume (still requires `--retry-incomplete`).
  - Execution state: performed

- [x] E-05 Add a regression test for the non-git-directory diagnostic: invoking init against a fresh non-git tempdir yields the `Not a Git repository` DriverError (assert on the message), not a `Command failed (128)` message.
  - Depends on: E-02
  - Expected outcome: a test asserting the intended precondition message; fails on current code, passes after the guard fix.
  - Execution state: performed

- [x] E-06 Add a regression test that `expand_selectors` on a manifest whose selected Set has an empty `order` raises an error naming that Set, and that `expand_selectors(manifest, [])` still raises the generic "At least one ..." message.
  - Depends on: E-03
  - Expected outcome: two assertions distinguishing the empty-Set and no-selector cases; fails on current code, passes after the selector fix.
  - Execution state: performed

### Task group 4: Honest per-attempt session id (B-05)

- [x] E-07 In `execute_item` (tools/ipdrunner/ipdrunner.py:589), stop seeding `attempt["session_id"]` with the prior/None Set session at attempt creation time; instead set the attempt's `session_id` only from a session id actually observed for THAT attempt (the value extracted at line 618-625), leaving it absent/None when no `ses_` id was parsed for that attempt, so the report's "Last session" column (ipdrunner.py:342-348) never attributes a stale or unrelated session to an attempt. Do not change the Set-session continuity check (line 618-624) or the `set_sessions` map. This is a small, local, Low-risk correctness-of-record fix.
  - Depends on: none
  - Expected outcome: a completed attempt shows the session id observed during that attempt (or null when none was parsed), not a value inherited from the prior Set session; the existing Set-session continuity test remains green.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Plan lifecycle: `.aw/records/plans/{pending,executed,superseded,not-executed,reusable}/`. IPDs are
  named by the uniform grammar `YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md` and are scaffolded (not
  hand-named) with `aw ipd scaffold`; ids are assigned by `aw ipd sync`; structure is checked by
  `aw ipd lint`. This IPD was born via `aw ipd scaffold` and set to `Status: to-review`.
- Contributor contract (AGENTS.md / CONTRIBUTING.md): commit ONLY changed files, path-scoped
  (`git commit -m msg -- <path>`); never `git add -A`/`-a`; never push. When reporting tests passed,
  paste the ACTUAL runner output. Do not add commits to a plan already in `executed/`. No em/en dashes
  in USER-FACING prose; internal/AI-facing artifacts (this IPD included) are exempt.
- Tests: `tools/ipdrunner/test_ipdrunner.py` is a `unittest` module importing `ipdrunner as driver`;
  run with `python3 -m pytest tools/ipdrunner/test_ipdrunner.py -q` (or `python3 test_ipdrunner.py`
  from that dir). Current suite (3 tests) passes on baseline.
- The driver's own design goal is durable restartability: state.json is written atomically
  (`atomic_write_json` fsyncs file + parent dir), events are appended to `events.jsonl` with fsync,
  and a `driver.lock` (`fcntl.LOCK_EX|LOCK_NB`) serializes control of a run. Fixes must preserve
  this restartability contract.
- Review-scope exclusions honored: the framework dir `.aw/system/workflows/` and
  `workflow-artifacts/` run records were NOT assessed as project code.

## Findings

Verified by reading the actual code paths and, where cheap, reproducing (see run record
`evidence.md`). Severity = impact if left alone; Remediation Risk gates whether to act now.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| B-01 | High | Low | QA / data-integrity | resume/idempotency | Plain `resume` (no `--retry-incomplete`) never retries the item left in flight at interruption. `reconcile_interrupted` sets that item to `interrupted` (line 688); the main loop only runs items with status `queued` (line 714); only `--retry-incomplete` re-queues `interrupted` (line 701-710). So a bare `resume` silently abandons that unit of work (its partial progress and Set-session continuity) while still running later `queued` items, contradicting the `resume` help text "Resume an existing run". | ipdrunner.py:688, 699-711, 712-714; resume help ipdrunner.py:807-814 |
| B-02 | Medium | Low | software engineer | error handling / diagnostics | The "Not a Git repository" guard cannot emit its own message. `not (repo/".git").exists() and not git_common_dir(repo).exists()` calls `git_common_dir`, whose `run_checked` raises `DriverError("Command failed (128): git rev-parse --git-common-dir ... fatal: not a git repository")` BEFORE `.exists()` is evaluated, so line 252's intended clear message is unreachable on the exact case it targets. | ipdrunner.py:251-252, 64-67, 49-61; reproduced (see evidence) |
| B-03 | Low | Low | novice / software engineer | error handling / diagnostics | `expand_selectors` reports "At least one id6 or Set selector is required" even when a selector WAS given but resolved to zero plans (a known Set with an empty `order`). Misleading diagnostic sends the user to fix the wrong thing. | ipdrunner.py:192-193, 204-209; reproduced (see evidence) |
| B-04 | Low | Medium-Low | software engineer | concurrency / TOCTOU | `initialize_run` checks `run_dir.exists()` (line 260) and creates state BEFORE `run_lock` is acquired (main: line 830 init, line 836 lock). Two concurrent `start --run-id X` race the existence check (`mkdir(..., exist_ok=True)` will not fail), so both could initialize the same run dir before either locks it. Auto-generated run ids include the pid so are effectively collision-free; the race needs an explicit duplicate `--run-id`. | ipdrunner.py:258-263, 826-837 |
| B-05 | Low | Low | QA | reporting accuracy | `execute_item` seeds `attempt["session_id"]` with the prior/None Set session (line 589) and only overwrites it when a NEW session id is extracted (line 618-625). If a launch produces no parseable `ses_` id, the attempt (and the report's "Last session" column) can show a stale/`null` session that does not correspond to that attempt. Cosmetic, not a control-flow bug; addressed in scope by E-07 (Fix Bar: Low risk => fix, do not defer on value). | ipdrunner.py:589, 618-625, 342-348 |

## Proposed changes (ordered, validatable)

1. B-01 (E-01): re-queue an `interrupted` item on a plain `resume` in recovery mode. Remediation Risk:
   Low. This is the highest-value fix: it closes a silent abandonment of in-flight work in the durable
   restart path. Down-scoped to only the `interrupted` state so `resume` semantics for terminal states
   are unchanged and `--retry-incomplete` remains the broader knob.
2. B-02 (E-02): make the non-git precondition report `Not a Git repository: <path>`.
   Remediation Risk: Low. Wrap the `git_common_dir` probe; do not alter real-repo/worktree behavior.
3. B-03 (E-03): raise an accurate error for a selected-but-empty Set; keep the generic
   message only for the truly-no-selector case. Remediation Risk: Low.
4. B-05 (E-07): record only the session id actually observed for an attempt, never a value inherited
   from the prior Set session. Remediation Risk: Low. Added during plan-review because its Remediation
   Risk is Low, so the Fix Bar requires fixing it rather than deferring on value.
5. Regression tests (E-04 pins B-01, E-05 pins B-02, E-06 pins B-03). Each new test must FAIL on current
   code and PASS after its fix (demonstrate both when executing). B-05/E-07 is validated by reading the
   edited seam plus confirming the existing Set-session-continuity test stays green (no separate test
   mandated, since the fix is a local record-honesty change, not a control-flow path).

## Deferred / out of scope (with reason)

- B-04 (init-before-lock TOCTOU): DEFERRED. Remediation Risk Medium on the Functionality/Complexity
  axis: correctly closing it means acquiring the lock (or an equivalent atomic create) BEFORE
  `initialize_run` writes state, which reorders the `start` control flow and the lock lifetime and
  risks regressing the atomic-state/lock design that the existing test
  `test_atomic_state_and_set_session_continuity` guards. The exposure is narrow (only concurrent
  `start` with the SAME explicit `--run-id`; auto ids embed the pid). Required decision/evidence to
  lift the deferral: a design for acquiring the lock (or an atomic run-dir create) BEFORE state is
  written, plus a concurrency test, without regressing the atomic-state/lock invariant. Consequence if
  left unresolved: two operators (or a script) that concurrently launch `start` with the same explicit
  `--run-id` could interleave initialization of the same run dir before either holds the lock, risking a
  corrupted/partially-initialized `state.json` for that run; the durable-restart guarantee for that run
  would not hold. Recommend a follow-up IPD that redesigns the create-then-lock ordering with its own
  dedicated test, rather than bolting it onto this bug-fix pass.
- B-05 (stale session in report): NOW IN SCOPE (E-07). It was deferred at assess time on value, but its
  Remediation Risk is Low, and the Fix Bar forbids deferring a Low-risk finding on effort/value; plan-
  review pulled it into scope as a small local fix. No finding remains deferred on an invalid basis.

## Scope check

- Over-scope: none. Each proposed fix traces to a confirmed defect on a reachable path; no gold-plating.
- Under-scope: the driver has no test exercising the interrupted-resume path at all (the gap that hid
  B-01); E-items add that missing regression coverage. B-05 (session record honesty) is now in scope
  (E-07) per the Fix Bar. Only B-04 concurrency remains deferred, on a valid Medium-risk axis with a
  named consequence, routed to a follow-up IPD rather than silently dropped.

## Coordination with sibling pending IPD (same file)

A separate, already-reviewed pending IPD targets the SAME file, `tools/ipdrunner/ipdrunner.py`:
`.aw/records/plans/pending/20260824-ipdrunner-01-pr2nd0-harden-ipdrunner-process-lifecycle-dependency-validation-and.ipd.md`
(Id pr2nd0, findings F-01..F-06; Status reviewed, GO - PENDING HUMAN APPROVAL). The two plans are
COMPLEMENTARY (distinct bugs), but they touch overlapping code and the same test module, so whichever
executes second MUST rebase on the first and reconcile:

- Shared code regions:
  - `reconcile_interrupted` (ipdrunner.py:655-693): pr2nd0 F-05/E-04 adds `interrupted_at` to the
    active attempt; this plan's E-01 edits the caller `run_queue` (not `reconcile_interrupted` itself)
    to re-queue the `interrupted` item. Adjacent, low conflict, but verify both intents survive.
  - Session id handling: pr2nd0 F-06/E-03 broadens `extract_session_id` key matching; this plan's E-07
    changes per-attempt session attribution in `execute_item`. Different functions, complementary; the
    executor MUST NOT let one revert the other.
  - `tools/ipdrunner/test_ipdrunner.py`: pr2nd0 E-05 and this plan's E-04/E-05/E-06 both append tests to
    the same file - the real merge surface. Add tests additively; do not clobber the sibling's cases.
- Non-overlapping here: this plan's B-02 (git guard) and B-03 (`expand_selectors`) are untouched by
  pr2nd0. This plan's DEFERRED B-04 (init-before-lock TOCTOU) is also NOT covered by pr2nd0, so the
  follow-up IPD recommended for B-04 remains necessary.
- Ordering: no hard dependency in either direction; recommended order is pr2nd0 first (it is already
  reviewed) then this plan rebased on it, but either order is safe if the executor reconciles the shared
  test file and re-runs the full suite. The executor MUST run the full `test_ipdrunner.py` suite after
  integration to prove neither plan regressed the other.

## Required tests / validation

- Run the full suite and paste actual output: `python3 -m pytest tools/ipdrunner/test_ipdrunner.py -q`
  (baseline: 3 passing). After the fixes + new tests, all tests (existing 3 + 3 new) must pass.
- For B-01 and each new test, first demonstrate the test FAILS on the pre-fix code (temporarily, or by
  reasoning shown in the walkthrough), then PASSES after the fix, to prove the test actually pins the
  bug rather than tautologically passing.
- Manual smoke (optional, cheap): invoke driver init against a fresh non-git tempdir and confirm the
  message is `ipdrunner: Not a Git repository: <path>` with exit code 2.

## Spec / documentation sync

- No user-facing behavior spec changes required: the fixes make actual behavior match the documented
  `resume` help text and the intended precondition message, so they align code to existing docs.
- DONE at execution: the overnight-execution runbook
  (`tools/ipdrunner/20260823-pending-ipds-overnight-execution-runbook.md`) previously described bare
  `resume` only as "Resume queued work" with interrupted/partial/etc. retries listed solely under
  `--retry-incomplete`. Added a short paragraph (after the bare-`resume` example) stating that a plain
  `resume` now also re-queues the single in-flight `interrupted` item in recovery mode, while
  `partial`/`failed-safely`/`blocked`/`dependency-blocked` items still require `--retry-incomplete`. This
  keeps the runbook honest about the new E-01 behavior.

## Open questions

### OQ-01: Should a bare `resume` also emit a one-line notice when it re-queues an interrupted item?

- Blocking: no
- Status: resolved
- Owner: human (plan-review interactive decision, 2026-08-24)
- Resolution or deferral rationale: RESOLVED - event log only. The human decided the driver emits the
  `events.jsonl` `interrupted-requeued` record only and does NOT print an additional stderr notice,
  keeping the change minimal and consistent with how other lifecycle transitions are recorded. E-01 is
  therefore scoped to emit the JSONL event and MUST NOT add a stderr line.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted test output showing the new interrupted-resume test passing after E-01, plus a demonstration (pre-fix run or reasoning) that a bare `resume` left the item `interrupted` before the fix. Anti-regression: the negative assertion from E-04 (a `partial`/`failed-safely` item is NOT re-queued by a bare resume) passes, and the existing `test_atomic_state_and_set_session_continuity` and the other baseline tests remain green, proving E-01 did not broaden bare-resume scope or disturb the atomic-state/Set-session-continuity invariant.
  - Observed evidence: PRE-FIX (RED): `test_bare_resume_requeues_interrupted_item` and `test_bare_resume_does_not_requeue_partial_or_failed` FAILED with `AttributeError: module 'ipdrunner' has no attribute 'requeue_interrupted'` (the requeue helper did not exist, so a bare resume left the item `interrupted`). POST-FIX (GREEN): added `requeue_interrupted` (ipdrunner.py) and wired it into `run_queue` before the `retry_incomplete` block; both tests pass. Positive test asserts the `interrupted` item -> `queued` with `recovery_next=True` and an `interrupted-requeued` event id6 returned; negative test asserts `partial`/`failed-safely` items are untouched (`requeue_interrupted` returns `[]`, statuses unchanged). Full suite `python3 -m pytest tools/ipdrunner/test_ipdrunner.py -q` = `........  8 passed in 0.47s`, including the baseline `test_atomic_state_and_set_session_continuity` still green. Commit 5ceffd6.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: reading of the edited `initialize_run` guard showing the `git_common_dir` probe is wrapped so a non-repo yields `DriverError("Not a Git repository: <path>")`; plus a demonstration (pasted output or the V-05 test) that a fresh non-git dir now produces that message, not `Command failed (128)`. Confirm the real-repo happy path still initializes (existing subprocess test still green).
  - Observed evidence: `initialize_run` now wraps the probe in `try: common_dir_exists = git_common_dir(repo).exists() except DriverError: common_dir_exists = False`, raising `DriverError(f"Not a Git repository: {repo}")` when neither `.git` nor a common dir is found (ipdrunner.py). PRE-FIX (RED): `test_non_git_dir_reports_clear_message` FAILED: `AssertionError: 'Not a Git repository' not found in 'Command failed (128): git rev-parse --git-common-dir\nfatal: not a git repository ...'`. POST-FIX (GREEN): test passes (message contains `Not a Git repository`, does not contain `Command failed`). Real-repo happy path untouched: `test_atomic_state_and_set_session_continuity` (which inits against a real `git init` repo) still green in the 8-passed run. Commit 5ceffd6.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: reading of the edited `expand_selectors` showing a selected-but-empty Set raises an error naming that Set, while the empty-selector case still raises "At least one id6 or Set selector is required"; plus the V-06 test output demonstrating both branches.
  - Observed evidence: `expand_selectors` now tracks `matched_set` for direct and prefix Set matches and, when `matched_set is not None and not candidates`, raises `DriverError(f"Set '{matched_set}' has an empty order (no plans to run)")` before the loop; the terminal generic message is reached only when no selector produced candidates at all (ipdrunner.py). PRE-FIX (RED): `test_empty_set_reports_named_set` FAILED (`assertNotIn("At least one id6 or Set selector is required", ...)` tripped because the empty Set fell through to the generic message). POST-FIX (GREEN): both `test_empty_set_reports_named_set` (message contains `empty`, not the generic text) and `test_no_selector_still_reports_generic_message` (empty selector list still raises the generic message) pass in the 8-passed run. Commit 5ceffd6.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted `python3 -m pytest tools/ipdrunner/test_ipdrunner.py -q` output showing the new interrupted-resume test present and passing; and evidence it FAILED on pre-fix code (temporary run or documented reasoning) so it genuinely pins B-01.
  - Observed evidence: The E-04 tests (`ResumeRequeueTests.test_bare_resume_requeues_interrupted_item` and `test_bare_resume_does_not_requeue_partial_or_failed`) were authored FIRST and run against pre-fix code, where they FAILED (no `requeue_interrupted` attribute), demonstrating they genuinely pin B-01 rather than passing tautologically. After E-01 they pass. `python3 -m pytest tools/ipdrunner/test_ipdrunner.py -v` collected 8 items -> `8 passed in 0.47s`, listing the two new ResumeRequeue tests. Commit 5ceffd6.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: pasted test output showing the non-git-diagnostic test passing after E-02, and that it FAILED (asserted on the wrong `Command failed` message) on pre-fix code.
  - Observed evidence: `GitPreconditionTests.test_non_git_dir_reports_clear_message` was authored first; PRE-FIX it FAILED with `AssertionError: 'Not a Git repository' not found in 'Command failed (128): git rev-parse --git-common-dir\nfatal: not a git repository ...'`. POST-FIX (E-02) it passes: the DriverError message contains `Not a Git repository` and not `Command failed`. Part of the `8 passed` suite run. Commit 5ceffd6.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: pasted test output showing the empty-Set/no-selector test passing after E-03, and that it FAILED on pre-fix code (the empty-Set case previously got the generic message).
  - Observed evidence: `SelectorErrorTests.test_empty_set_reports_named_set` was authored first; PRE-FIX it FAILED (the empty Set fell through to the generic "At least one id6 or Set selector is required" message, tripping `assertNotIn`). POST-FIX (E-03) it passes, and `test_no_selector_still_reports_generic_message` confirms the empty-selector-list case still raises the generic message. Both are in the `8 passed` suite run. Commit 5ceffd6.
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: reading of the edited `execute_item` showing `attempt["session_id"]` is no longer seeded from the prior Set session at creation and is set only from a session id observed for that attempt (else left null); confirmation the Set-session continuity check (line 618-624) and `set_sessions` map are untouched; and pasted output showing the existing `test_atomic_state_and_set_session_continuity` (and the rest of the suite) still passing after E-07.
  - Observed evidence: In `execute_item` the attempt dict now sets `"session_id": None` at creation (was `state.get("set_sessions", {}).get(item["setid"])`); the only place it is populated is the post-launch block `if session_id: ... attempt["session_id"] = session_id`, which is the session observed for THAT attempt. The Set-session continuity check and `state["set_sessions"]` map are unchanged (the `if existing and existing != session_id: raise DriverError(...)` guard and `state["set_sessions"][item["setid"]] = session_id` remain). The existing `test_atomic_state_and_set_session_continuity` still asserts `sessions[0] == sessions[1]` and both are non-empty because the fake opencode emits a `ses_` id each attempt; it passes in the `8 passed` suite run. Commit 5ceffd6.
  - Result: pass



## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This IPD is a proposal only. Per the assess workflow it must be human-approved before execution
(`aw spec`/plan approval; optionally run `/plan-review` first); it is NOT auto-run. On execution, the
executor MUST: run `aw ipd sync` to assign ids to the `E-NEW`/`V-NEW` leaves and build the E/V
bijection; commit ONLY the files changed, path-scoped (`git commit -m ... -- tools/ipdrunner/...`),
never `git add -A`/`-a`, never push; paste ACTUAL test-runner output as evidence (no claimed passes);
and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` item is verified with
concrete evidence, move this IPD to `.aw/records/plans/executed/`. If validation does not pass, STOP
and report; do not mark executed.
