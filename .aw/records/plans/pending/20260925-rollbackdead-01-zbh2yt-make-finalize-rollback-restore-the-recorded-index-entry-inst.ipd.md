# IPD: Make finalize rollback restore the recorded index entry instead of unstaging to HEAD

- Date: 2026-09-25
- Kind: child
- Concern: `ipd_lifecycle._rollback_precommit` step 3 ignores the journal's recorded `git_index_entries` (both arms of its `if p in prior_index:` issue the same `git restore --staged`), so a pre-commit rollback resets an owned path's index entry to HEAD instead of to the recorded prior state, discarding a staged edit to the plan file and emitting a spurious pathspec error for the never-indexed destination.
- Scope: IN: step 3 of `ipd_lifecycle._rollback_precommit` (restore each owned path's index entry to exactly what `_git_index_entries` recorded, no-op when already equal, remove an entry only when none was recorded) and one regression test. OUT: steps 1, 2 and 4 of the rollback; the journal schema; `_git_index_entries` itself; the post-commit paths.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, tests/test_ipd_lifecycle_cli.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: 67k1ol
- Blocks-Release: next
- Set: rollbackdead
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: zbh2yt

## Workflow history

- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 67k1ol; re-measured that the identical-arm branch is still present in `_rollback_precommit` step 3 and, in a scratch repo, that it resets a staged plan edit to HEAD (recorded blob `9c5043ab` became `dcc27807`), confirming the backlog's reading (2) rather than mere dead code.

## Goal

Make the rollback do what its own comment says ("Reset the index entry for this owned path to its recorded state"): consult the recorded entry, so a failed finalize leaves the shared index exactly as it found it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: regression test first

- [ ] E-01 Add a test to `tests/test_ipd_lifecycle_cli.py` class `RollbackFailureSemanticsTests`, named `test_rollback_restores_recorded_index_entry_not_head`. It stages an edit to the plan file (`git add`), records `LC._git_index_entries(self.root, [plan_rel, dest_rel])`, calls `LC._rollback_precommit(self.root, journal)` with a journal carrying `original_path`, `original_bytes` (the current on-disk bytes, so step 2 is a no-op), `owned_paths`, and that `git_index_entries`, then asserts (a) `ok` is True, (b) `_git_index_entries` after equals the recorded dict byte-for-byte, and (c) the destination path has no index entry. Run it against the UNCHANGED code and record that it fails.
  - Depends on: none
  - Expected outcome: the test exists and fails on assertion (b) against current code, because the staged blob is reset to HEAD's blob.
  - Execution state: pending

### Task group 2: the fix

- [ ] E-02 Rewrite step 3 of `ipd_lifecycle._rollback_precommit` (the block under the comment "3. Restore the exact prior Git-index entries for lifecycle-owned paths"). For each `p` in `owned`: read the CURRENT entry with `_git_index_entries(repo_root, [p])`; if it equals `prior_index.get(p)` (including both absent), do nothing; else if `p in prior_index`, restore it by piping the recorded line to `git update-index --index-info` (the line is already in `ls-files --stage` format `<mode> <object> <stage>\t<path>`, which `--index-info` accepts); else run `git update-index --force-remove -- p`. Delete the identical-arm `if/else`. Update the step-3 comment to state the three cases and why the no-op case matters (the coordinator-worktree design means the shared index is normally untouched, so the common case must write nothing). `_git` cannot pass stdin, so use `subprocess.run([... "update-index", "--index-info"], cwd=repo_root, input=line + "\n", text=True, capture_output=True)` or add a minimal stdin parameter locally; prefer the local `subprocess.run` so `git_commit_helper._git`'s signature is untouched.
  - Depends on: E-01
  - Expected outcome: step 3 contains no duplicated call; E-01 passes.
  - Execution state: pending

- [ ] E-03 Make a failed index restore surface instead of being swallowed: if the `update-index` call returns nonzero, return `(False, "rollback could not restore the index entry for {p}: <stderr>")`, matching the existing step-1/step-2 failure strings ("rollback could not remove", "rollback could not restore"). Confirm by reading both callers in `_finalize_transaction` (the resume branch "Interrupted before the commit: finish rollback idempotently" and `_rollback_and_return`) that a `False` already routes to `PHASE_UNKNOWN_OUTCOME` with `rollback_error`, so no caller change is needed.
  - Depends on: E-02
  - Expected outcome: a nonzero `update-index` produces a `(False, ...)` result; callers unchanged.
  - Execution state: pending

### Task group 3: suite

- [ ] E-04 Run the bare suite `python3 -m pytest` and record the summary line.
  - Depends on: E-03
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
| F-6 | Existing direct-call tests pass `"git_index_entries": {}` (`tests/test_orchestrator_retirement.py`, `_worktree_shaped_journal` and a sibling), so with the new rule their owned paths are removed only if an entry now exists; the pending path is tracked at HEAD, so `--force-remove` would unstage-delete it. Those tests must be checked (see OQ-01). | `AFailedRetirementCannotDestroyAPeersInFlightEdit._worktree_shaped_journal` |

## Proposed changes (ordered, validatable)

1. E-01 failing regression test.
2. E-02 three-case step 3.
3. E-03 surface restore failure.
4. E-04 bare suite.

## Deferred / out of scope (with reason)

- Removing `git_index_entries` from the journal entirely (backlog reading (1)).
  - Carrier-Declined: rejected, because the probe (F-2) shows the recorded entry is needed to restore a staged edit; reading (2) is correct.

## Scope check

- Over-scope: none.
- Under-scope: none; the other rollback steps were audited by `4xt6u4`/`u23gbn`.

## Required tests / validation

New test in `RollbackFailureSemanticsTests`, plus the existing `tests/test_orchestrator_retirement.py` rollback tests and the bare suite.

## Spec / documentation sync

N/A: no spec describes step 3's index mechanics; the docstring of `_rollback_precommit` already promises "exact prior Git-index entries", which this plan makes true.

## Open questions

### OQ-01: A journal whose `git_index_entries` is empty but whose owned path IS tracked

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: `_git_index_entries` records every tracked owned path, so a real journal for a tracked plan always carries its entry; an empty dict with a tracked path only arises in hand-built test journals (F-6) or a failed `ls-files` (the function returns `{}` on rc != 0). DEFAULT: treat an EMPTY `git_index_entries` as "not recorded" and skip step 3 for every path (write nothing), rather than force-removing tracked paths. Implement that guard in E-02 and note it in the step-3 comment. If a reviewer prefers force-removal semantics, only the guard changes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_ipd_lifecycle_cli.py -k test_rollback_restores_recorded_index_entry_not_head` run BEFORE E-02, showing `1 failed` with the assertion diff naming the HEAD blob vs the recorded blob.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the same command after E-02 showing `1 passed`; paste `git diff agent_workflows/ipd_lifecycle.py` showing the duplicated `restore --staged` arms removed and the three cases present; paste `python3 -m pytest -o addopts="" tests/test_orchestrator_retirement.py -k rollback` passing (covers OQ-01's empty-dict guard).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a `mock.patch` probe (or an added assertion) where `update-index` returns nonzero and `_rollback_precommit` returns `(False, "rollback could not restore the index entry for ...")`; quote the two caller sites showing `ok` False sets `PHASE_UNKNOWN_OUTCOME`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `python3 -m pytest` summary line (`N passed ...`); if any failures, list node ids and show each also fails on the pre-change baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires `/plan-review` then explicit human approval before execution. Commit via `aw commit <plan> -- <paths>`, never push; transition with `aw ipd finalize` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
