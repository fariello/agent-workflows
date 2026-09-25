# IPD: Make finalize rollback restore the recorded index entry instead of unstaging to HEAD

- Date: 2026-09-25
- Kind: child
- Concern: `ipd_lifecycle._rollback_precommit` step 3 ignores the journal's recorded `git_index_entries` (both arms of its `if p in prior_index:` issue the same `git restore --staged`), so a pre-commit rollback resets an owned path's index entry to HEAD instead of to the recorded prior state, discarding a staged edit to the plan file and emitting a spurious pathspec error for the never-indexed destination.
- Scope: IN: step 3 of `ipd_lifecycle._rollback_precommit` (restore each owned path's index entry to exactly what `_git_index_entries` recorded, no-op when already equal, and WRITE NOTHING when no entry was recorded) and one regression test. OUT: steps 1, 2 and 4 of the rollback; the journal schema; `_git_index_entries` itself; the post-commit paths.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, tests/test_ipd_lifecycle_cli.py
- Item-Dependencies: none
- Status: to-review
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: 67k1ol
- Blocks-Release: next
- Set: rollbackdead
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: zbh2yt

## Workflow history

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-801..PR-806 all FIXED, no open blocking question. All four probe findings reproduced exactly at review (F-1 identical arms, F-2 the staged blob reset to HEAD's with status flipping `M ` to ` M`, F-3 the rc-1 pathspec error, F-4 `update-index --index-info` restoring byte-for-byte). The REMEDY needed correcting: the proposed `--force-remove` arm stages a DELETION (`D  <path>`) on the strength of an ABSENT journal key, inverting the refuse-rather-than-overwrite discipline steps 1 and 2 establish, and OQ-01's empty-dict guard would not fire on a partially-recorded journal. That arm is removed; review measured that removing it costs no coverage. F-6's mechanism was also wrong: the fixture is not tracked at HEAD (it never commits), it is staged with no HEAD, which is what implies a per-path rather than empty-dict guard. Record: `.aw/records/reviews/20260925-rollbackdead-01-zbh2yt-make-finalize-rollback-restore-the-recorded-index-entry-inst.review.md`.
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 67k1ol; re-measured that the identical-arm branch is still present in `_rollback_precommit` step 3 and, in a scratch repo, that it resets a staged plan edit to HEAD (recorded blob `9c5043ab` became `dcc27807`), confirming the backlog's reading (2) rather than mere dead code.

## Goal

Make the rollback do what its own comment says ("Reset the index entry for this owned path to its recorded state"): consult the recorded entry, so a failed finalize leaves the shared index exactly as it found it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: regression test first

- [ ] E-01 Add a test to `tests/test_ipd_lifecycle_cli.py` class `RollbackFailureSemanticsTests`, named `test_rollback_restores_recorded_index_entry_not_head`. That class is the right home because its `setUp` calls `_commit_all(self.root, "init")`, so its plan file is genuinely tracked at HEAD and a staged-edit-versus-HEAD assertion is meaningful (the orchestrator-retirement fixture never commits, see F-6). It stages an edit to the plan file (`git add`), records `LC._git_index_entries(self.root, [plan_rel, dest_rel])`, calls `LC._rollback_precommit(self.root, journal)` with a journal carrying `original_path`, `original_bytes` (the current on-disk bytes, so step 2 is a no-op), `owned_paths`, and that `git_index_entries`, then asserts (a) `ok` is True, (b) the PLAN PATH's entry equals the recorded line explicitly, asserted on that single entry and not only through whole-dict equality so the failure message names BOTH blob ids, (c) `_git_index_entries` after equals the recorded dict, and (d) the destination path has no index entry. Also capture `git status --porcelain` before and after and assert it is unchanged, because the `M ` to ` M` flip is the operator-visible symptom. Run it against the UNCHANGED code and record that it fails.
  - Depends on: none
  - Expected outcome: the test exists and fails on assertion (b) against current code, with the failure naming the recorded blob and HEAD's blob, because `restore --staged` resets to HEAD.
  - Execution state: pending

### Task group 2: the fix

- [ ] E-02 Rewrite step 3 of `ipd_lifecycle._rollback_precommit` (the block under the comment "3. Restore the exact prior Git-index entries for lifecycle-owned paths") as a TWO-case rule. For each `p` in `owned`: read the CURRENT entry with `_git_index_entries(repo_root, [p])`; if it equals `prior_index.get(p)` (including both absent), DO NOTHING; else if `p in prior_index`, restore it by piping the recorded line to `git update-index --index-info` (the line is already in `ls-files --stage` format `<mode> <object> <stage>\t<path>`, which `--index-info` accepts, proven by F-4). The third case (no recorded entry) is E-03's and writes nothing; do NOT add a `--force-remove` arm (F-7). Delete the identical-arm `if/else`. Update the step-3 comment to state the cases and why the no-op case matters (the coordinator-worktree design means the shared index is normally untouched, so the common case must write nothing, F-5). `_git` cannot pass stdin (it delegates to `git_commit_helper._git`, which takes only args), so use a LOCAL `subprocess.run(["git", "update-index", "--index-info"], cwd=repo_root, input=line + "\n", text=True, capture_output=True)` rather than changing that shared signature. Both `cwd=repo_root` and `capture_output=True` are REQUIRED, not optional: the first so the call cannot run against whatever directory the process happens to be in, the second so E-04's failure message has stderr text to quote.
  - Depends on: E-01
  - Expected outcome: step 3 contains no duplicated call and no `--force-remove`; E-01 passes.
  - Execution state: pending

- [ ] E-03 Add the ABSENT-EVIDENCE GUARD as an explicit, commented case: when `p not in prior_index`, write NOTHING. State the reason in the comment, because the obvious-looking alternative is destructive. Measured at review: `git update-index --force-remove` on a path that IS in the index stages a DELETION (`git status` goes from clean to `D  <path>` with the file still on disk), and `_git_index_entries` returns `{}` both when a path genuinely had no entry AND when `ls-files` fails, so an absent recording is EVIDENCE ABSENCE rather than evidence of absence. Writing on it would invert the discipline steps 1 and 2 establish, both of which refuse rather than overwrite content the transaction did not write ("refusing a destructive restore"). The guard is PER PATH, not keyed on an empty dict: a journal carrying entries for some owned paths and not others is not empty, so an empty-dict-only guard would still write on the unrecorded path (OQ-01). This costs no coverage, measured: for a destination that a partial finalize staged, step 1 has already unlinked it, and `restore --staged`, `--force-remove` and do-nothing ALL end with no index entry and a clean or `?? `-only status.
  - Depends on: E-02
  - Expected outcome: no code path in step 3 writes the index for a path absent from `prior_index`; the two existing `"git_index_entries": {}` fixtures still pass.
  - Execution state: pending

- [ ] E-04 Make a failed index restore surface instead of being swallowed: if the `update-index` call returns nonzero, return `(False, "rollback could not restore the index entry for {p}: <stderr>")`, matching the existing step-1/step-2 failure strings ("rollback could not remove", "rollback could not restore"). Confirm by reading both callers in `_finalize_transaction` (the resume branch "Interrupted before the commit: finish rollback idempotently" and `_rollback_and_return`) that a `False` already routes to `PHASE_UNKNOWN_OUTCOME` with `rollback_error`, so no caller change is needed. Verified at review: the resume branch sets `existing["phase"] = PHASE_UNKNOWN_OUTCOME` plus `existing["rollback_error"] = msg` and returns `EXIT_CANNOT_RUN`; `_rollback_and_return` does the same on `cur`.
  - Depends on: E-03
  - Expected outcome: a nonzero `update-index` produces a `(False, ...)` result carrying the stderr text; callers unchanged.
  - Execution state: pending

### Task group 3: suite

- [ ] E-05 Run the bare suite `python3 -m pytest` and record the summary line.
  - Depends on: E-04
  - Expected outcome: no new failures relative to the pre-change baseline (compare by node id if the baseline is not clean).
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The rollback's peer-safety discipline: steps 1 and 2 of `_rollback_precommit` refuse rather than overwrite content the transaction did not write. Step 3's new no-op-when-equal rule keeps the same spirit: it never writes when nothing changed.
- `_git_index_entries` (`ipd_lifecycle.py:466`) records `git ls-files --stage` lines keyed by path; the journal key is `"git_index_entries"`, written in `_finalize_transaction` beside `"owned_paths"`.
- `ipd_lifecycle._git` delegates to `git_commit_helper._git` and takes no stdin.

## Findings

| ID | Finding | Evidence |
| --- | --- | --- |
| F-1 | Both arms of `if p in prior_index:` in `_rollback_precommit` step 3 are `_git(repo_root, ["restore", "--staged", "--", p])`; `prior_index` decides nothing. | read at HEAD `8e74dcac`, `ipd_lifecycle._rollback_precommit` |
| F-2 | This is a real (minor) behavior bug, not only dead code: `restore --staged` resets to HEAD. Scratch repo, plan staged with new content: recorded entry `100644 9c5043ab...`, after rollback `100644 dcc27807...` (HEAD blob), `git status` ` M` instead of `M `. | probe under `/tmp/opencode/g3/probe-rollbackdead/` |
| F-3 | For the never-indexed destination path the call exits 1 with "pathspec ... did not match any file(s) known to git", silently ignored. | same probe |
| F-4 | `git update-index --index-info` fed the recorded line restores the exact entry (probe: status returned to `M `). | same probe |
| F-5 | Since `u23gbn` the move and commit happen in a coordinator worktree, so the shared index is normally untouched and the ideal step 3 is usually a no-op; the recorded entries still matter for resume of a journal written before that change and for defense in depth. | `_finalize_transaction` comment "MUTATING + READY_TO_COMMIT + the commit, ALL IN A COORDINATOR-OWNED WORKTREE" |
| F-6 | CORRECTED AT REVIEW. Two direct-call fixtures pass `"git_index_entries": {}` (`tests/test_orchestrator_retirement.py`, `_worktree_shaped_journal` and a sibling), and they ARE the regression surface for E-03, but NOT for the reason first recorded here. The original claim was "the pending path is tracked at HEAD": it is not. `_init_git_repo` runs `git init` and NEVER COMMITS, so `git rev-parse HEAD` fails and nothing is tracked at HEAD. `make_set` STAGES the plan, so the path is in the INDEX with no HEAD behind it and the journal's `{}` MISDESCRIBES the index. That mechanism (a recording disagreeing with the index) is what implies a per-path guard rather than an empty-dict one. WHICH CASES REACH STEP 3: cases 2 and 3 of `test_rollback_preserves_peer_edits_restores_half_moves_and_is_idempotent` (both assert `ok` True and run to completion); case 1 and the second `{}` site both assert `assertFalse(ok)` with `unknown-outcome` and RETURN AT STEP 1, never reaching step 3. Verifying "the rollback tests pass" without knowing this could satisfy V-03 without ever exercising the guard. | Driven at review on the real fixture: `git rev-parse HEAD` fails after `setUp`; `_git_index_entries` returns `100644 30a4e612... 0\t.aw/records/plans/pending/20260906-rbhalf-00-orc000-synthetic.ipd.md` while the journal hard-codes `{}`; read of the four `{}` call sites' assertions. |
| F-7 | `--force-remove` IS DESTRUCTIVE ON AN INDEXED PATH, which is why E-03 writes nothing instead. Running it on a path present in the index took `git status` from clean to `D  <path>` with the file still on disk. Since `_git_index_entries` returns `{}` both for a genuinely unindexed path AND on any `ls-files` failure, an absent recording is EVIDENCE ABSENCE, so writing on it can stage a deletion of a peer's staged work in exactly the scenario this rollback exists to protect. Steps 1 and 2 both refuse rather than overwrite ("refusing a destructive restore"); step 3 must match. | Driven at review; `_git_index_entries` returns `out` unchanged when `rc != 0`. |
| F-8 | DROPPING THE UNRECORDED-PATH WRITE COSTS NO COVERAGE, which is what makes F-7's removal safe rather than merely cautious. For a destination path that a partial finalize staged, step 1 has already unlinked it, and all three candidate actions end identically: `restore --staged` exits 0 and clears the entry, `--force-remove` exits 0 and clears it, and doing nothing leaves no entry either. The ONLY case where the old and new rules differ is the plan file with a recorded entry, which is precisely the bug F-2 measures. | Driven at review across a staged-then-unlinked destination and a staged-then-deleted new path; all routes end with no index entry and a clean or `?? `-only status. |

## Proposed changes (ordered, validatable)

1. E-01 failing regression test.
2. E-02 two-case step 3 (no-op when equal, restore the recorded line otherwise).
3. E-03 absent-evidence guard (write nothing; no `--force-remove`).
4. E-04 surface restore failure.
5. E-05 bare suite.

## Deferred / out of scope (with reason)

- Removing `git_index_entries` from the journal entirely (backlog reading (1)).
  - Carrier-Declined: rejected, because the probe (F-2) shows the recorded entry is needed to restore a staged edit; reading (2) is correct.
- Correcting the journals in the two `"git_index_entries": {}` fixtures to record their real index entries (F-6).
  - Carrier-Declined: those journals are hand-built to exercise the peer-clobber and concurrent-destination arms, and `{}` is a legitimate shape for that purpose; after E-03 it is also SAFE, because an absent recording writes nothing. Correcting them would change tests this plan is not scoped to touch, for no behavior gain. The mechanism is recorded in F-6 so a later reader is not misled.

## Scope check

- Over-scope: none.
- Under-scope: none; the other rollback steps were audited by `4xt6u4`/`u23gbn`.
- Explicitly OUT: `git_commit_helper._git`'s signature (E-02 uses a local `subprocess.run` precisely to leave it alone); `_git_index_entries` itself; the journal schema; steps 1, 2 and 4; the two fixtures' journals; and any `--force-remove` of an index entry (F-7).

## Required tests / validation

New test in `RollbackFailureSemanticsTests`, plus the existing `tests/test_orchestrator_retirement.py` rollback tests (specifically cases 2 and 3 of `test_rollback_preserves_peer_edits_restores_half_moves_and_is_idempotent`, which are the ones that REACH step 3 per F-6) and the bare suite.

## Spec / documentation sync

N/A: no spec describes step 3's index mechanics; the docstring of `_rollback_precommit` already promises "exact prior Git-index entries", which this plan makes true.

## Open questions

### OQ-01: A journal whose `git_index_entries` has no entry for an owned path that IS in the index

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW, AND MORE BROADLY THAN THE ORIGINAL DEFAULT. The original default was "treat an EMPTY `git_index_entries` as not recorded and skip step 3 for every path", keeping a `--force-remove` arm otherwise. Two measurements changed the answer. FIRST, `--force-remove` on a path present in the index STAGES A DELETION (`git status` clean -> `D  <path>`, file still on disk), which on an ABSENT journal key inverts the refuse-rather-than-overwrite discipline steps 1 and 2 establish (F-7); and `_git_index_entries` returns `{}` on an `ls-files` failure too, so absence is evidence absence rather than evidence of absence. SECOND, the empty-dict condition is the WRONG key: a journal carrying entries for some owned paths and not others is not empty, so that guard would not fire and the unrecorded path would still be force-removed. ANSWER: the guard is PER PATH and the `--force-remove` arm is removed entirely (E-03). This costs no coverage, measured (F-8): for a staged destination, step 1 has already unlinked it and `restore --staged`, `--force-remove` and do-nothing all end with no index entry.
- Carrier-Declined: resolved in this plan by E-03 with its own V item; nothing is outstanding for a carrier to track. A maintainer preferring force-removal semantics would be deciding against F-7's measurement, which is a new decision rather than a deferred obligation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_ipd_lifecycle_cli.py -k test_rollback_restores_recorded_index_entry_not_head` run BEFORE E-02, showing `1 failed`, with the failure output naming BOTH blob ids (the recorded staged blob and HEAD's blob) and the `git status --porcelain` before/after values showing the `M ` to ` M` flip. A failure that reports only "dicts differ" does not satisfy this item: this test is the sole proof the bug exists, so its output must identify which blob replaced which.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the same command after E-02 showing `1 passed`, and `git diff agent_workflows/ipd_lifecycle.py` showing the duplicated `restore --staged` arms removed, the no-op-when-equal case present, and the `update-index --index-info` call carrying both `cwd=repo_root` and `capture_output=True`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: three pastes. (a) `git diff agent_workflows/ipd_lifecycle.py` showing NO `--force-remove` anywhere in step 3 and the absent-evidence case commented with its reason. (b) `python3 -m pytest -o addopts="" tests/test_orchestrator_retirement.py -k rollback` passing, AND a statement naming which cases exercised step 3 (cases 2 and 3 of `test_rollback_preserves_peer_edits_restores_half_moves_and_is_idempotent`; per F-6 the other two `{}` sites return at step 1, so a bare "the rollback tests pass" does NOT show the guard was exercised). (c) A driven probe on a scratch repo showing that with a journal whose `git_index_entries` OMITS an owned path that IS in the index, `_rollback_precommit` leaves that entry untouched and `git status` unchanged, which is the F-7 regression this guard exists to prevent.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a `mock.patch` probe (or an added assertion) where the `update-index` call returns nonzero and `_rollback_precommit` returns `(False, "rollback could not restore the index entry for ...")` WITH the stderr text present in the message (empty stderr means `capture_output=True` was dropped, E-02); quote the two caller sites showing `ok` False sets `PHASE_UNKNOWN_OUTCOME` and `rollback_error`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `python3 -m pytest` summary line (`N passed ...`); if any failures, list node ids and show each also fails on the pre-change baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Five items, one concern: making step 3 of the pre-commit rollback restore what the journal recorded. The count grew from four at review because E-02 was carrying the rewrite, the branch deletion, the comment, the stdin mechanism AND (after the OQ-01 resolution) the absent-evidence guard, and that guard is the one part where being wrong LOSES a peer's staged work rather than merely failing to restore it. It also has a different evidence surface: the restore is proven by E-01's new test, while the guard is proven by two PRE-EXISTING fixtures with hand-built journals plus a driven probe. No item introduces a second concern.

WHAT A HUMAN IS APPROVING. A change to the code path that runs when a finalize has ALREADY FAILED, which is the last thing standing between that failure and a co-worker's staged work in a shared checkout. Today it calls `git restore --staged` unconditionally, which resets an owned path's index entry to HEAD: measured, a recorded staged blob became HEAD's blob and `git status` flipped from `M ` to ` M`, silently discarding a peer's staged plan edit. After this change the recorded entry is restored byte-for-byte, and when nothing was recorded NOTHING is written. Two things to weigh. FIRST, review REMOVED a `--force-remove` arm this plan originally proposed, because it stages a deletion on the strength of an absent journal key (F-7); approving this is approving the narrower, write-nothing behavior, and review measured that the narrowing costs no coverage (F-8). SECOND, the common case is a NO-OP: since the mutations moved into a coordinator worktree (`u23gbn`) the shared index is normally untouched, so on a healthy tree this code should write nothing at all, and the fix matters for the resume path and for defense in depth (F-5).

SCOPE FENCE (a DECLARATION for reconciliation, not a stop directive). The intended surface: in `agent_workflows/ipd_lifecycle.py`, ONLY the step-3 block of `_rollback_precommit` (the loop under the comment "3. Restore the exact prior Git-index entries for lifecycle-owned paths") plus its comment, and a local `subprocess.run` for the `update-index --index-info` call; in `tests/test_ipd_lifecycle_cli.py`, one new test method in `RollbackFailureSemanticsTests`. EXPLICITLY NOT IN SCOPE: steps 1, 2 and 4 of the rollback; `_git_index_entries`; the journal schema; `git_commit_helper._git`'s signature (the local `subprocess.run` exists precisely to leave it alone); `tests/test_orchestrator_retirement.py` and its two `"git_index_entries": {}` journals, which are RUN but not edited; the post-commit paths and `_resume_post_commit`; and any `--force-remove` of an index entry. An out-of-scope edit is made and then JUSTIFIED (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path); it is not a reason to stop.

HONESTY RULE (hard MUST). Paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. This plan is most exposed to faking on V-01 and V-03(b)(c). V-01 must be run against UNPATCHED code and must name both blob ids, because a test written after the fix passes trivially and proves nothing about the bug. V-03(b) must name which fixture cases actually reached step 3: per F-6 two of the four `{}`-journal sites return at step 1 on `unknown-outcome`, so "the rollback tests pass" is output a tree with no guard at all produces identically. V-03(c) is the only direct evidence the absent-evidence guard holds.

STOP CONDITIONS (genuinely unsafe, distinct from the scope fence). Stop and report if: step 3's two arms are no longer byte-identical at HEAD (someone else has already fixed or changed this, so the plan needs re-deriving rather than applying); `_git_index_entries` no longer returns `ls-files --stage` lines verbatim, since `update-index --index-info` consuming them directly is what makes the restore a one-liner (F-4); or either caller in `_finalize_transaction` no longer routes a `(False, ...)` to `PHASE_UNKNOWN_OUTCOME` with `rollback_error`, which would make E-04 add a failure arm nothing handles.

This plan is `reviewed` and needs explicit human approval (`Status: approved`) before execution. The executor commits only the Scope-Paths via `aw commit zbh2yt -- <paths>`, never `git add -A`, and never pushes. It inherits `- Blocks-Release: next` from backlog `67k1ol` (`Work-Kind: bug`) and discharges it, so `67k1ol` may close once this is executed and validated. LIFECYCLE TRANSITION: reaching `executed/` via `aw ipd finalize` is UNCONDITIONALLY owed, but under `aw oc run` / `aw agy run` the RUNNER owns that transition, so do not invoke it yourself in a runner-driven execution; a hand execution invokes it. Never hand-roll a `git mv` to `executed/`. Transition only after `aw ipd lint --phase pre-transition` conforms and V-01..V-05 carry pasted evidence.
