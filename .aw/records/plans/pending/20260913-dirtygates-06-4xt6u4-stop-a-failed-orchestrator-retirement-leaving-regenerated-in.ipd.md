# IPD: Stop a failed orchestrator retirement leaving regenerated index files in the shared checkout

- Date: 2026-09-13
- Kind: child
- Concern: A FAILED orchestrator retirement does not restore the tree it started from, in a rollback whose documented job is to restore it. Measured 2026-09-13 with the repository's own fault injector: the plan was correctly restored to `pending/` with its original bytes, the `executed/` copy was removed, and HEAD was unmoved, but `git status --porcelain` afterwards reported `?? .aw/records/plans/INDEX.json` and `?? .aw/records/plans/INDEX.md`. The rollback regenerates the plans index from the current corpus, which WRITES those files rather than restoring their prior state. The existing fault tests assert plan restoration and HEAD but never tree cleanliness, which is why this went unnoticed.
- Scope: Make a failed retirement leave the shared checkout byte-identical to how it found it, and add the tree-cleanliness assertion the existing fault tests lack. Excludes relocating the retirement mutations into a worktree, which is Order 04 (`u23gbn`) and is gated on that plan's blocking OQ-03 about shared-versus-forked transaction code.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, tests/test_orchestrator_retirement.py
- Item-Dependencies: none
- Status: to-review
- Set: dirtygates
- Order: 6
- Highest E allocated: 02
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 4xt6u4
- Priority: medium
- Work-Kind: bug

## Workflow history

- 2026-09-13 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-09-13 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): CARVED OUT OF ORDER 04 (`u23gbn`) at the maintainer's direction after `/plan-review` raised PR-401. That review found Order 04 had a scoping error (its mechanisms live in shared code reaching every plan's terminal transition, not only the 4 rollup retirements it was scoped against) and correctly observed that Order 04's E-03 and E-04 are NOT gated by that question. Those two items are this plan; they fix a measured bug and need no architecture ruling.

## Goal

A retirement that fails must leave no trace. Today it leaves two untracked index files, so the tree after a failure differs from the tree before it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: leave no residue

- [ ] E-01 Stop a failed retirement leaving untracked index files in the shared checkout. `_rollback_precommit` (`ipd_lifecycle.py:1874`) step 4 "regenerates the plans index from the CURRENT corpus", which WRITES `.aw/records/plans/INDEX.json` and `INDEX.md` rather than restoring whatever state they were in before the attempt. Restore their PRIOR state instead: capture it in the journal alongside the plan's `original_bytes` and the `git_index_entries` the rollback already records, and put it back on the rollback path. NOTE WHAT MUST NOT CHANGE: the regeneration on the SUCCESS path is correct and stays, because a successful retirement really does change the corpus. Only the rollback path is wrong. Also preserve the existing `unknown-outcome` classification: if the index files were changed by a concurrent writer since the checkpoint, this must NOT perform a destructive restore, exactly as the destination-changed case already refuses (`:1897-1906`).
  - Depends on: none
  - Expected outcome: after a failed retirement, `git status --porcelain` in the shared checkout is byte-identical to before the attempt.
  - Execution state: pending

### Task group 2: pin it where it broke

- [ ] E-02 Add the assertion the existing fault tests lack, to the tests that already exercise the failure. `tests/test_orchestrator_retirement.py:1961-1972` asserts the plan is restored to `pending/`, that its bytes match, that the `executed/` destination is gone, and that HEAD is unmoved, but it never asserts THE TREE IS CLEAN, which is exactly why the residue went unnoticed. Add a `git status --porcelain` emptiness assertion to the existing `after_move` case and to the `before_commit` case at `:1984`, rather than writing a parallel test, so the property is pinned at the site where the failure actually occurs. DEMONSTRATE THE ASSERTION IS REAL: show it FAILING against the pre-fix behavior (the measured `?? INDEX.json` / `?? INDEX.md`) before the fix is applied, so the test is proven to detect the bug rather than merely passing afterwards.
  - Depends on: E-01
  - Expected outcome: the suite fails if a failed retirement leaves any residue, and the test is proven to detect the original defect.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The finalize transaction is journalled with explicit phases (`PHASE_PREPARED` -> `PHASE_MUTATING` -> `PHASE_READY_TO_COMMIT` -> `PHASE_COMMITTED_INCOMPLETE`/`PHASE_COMPLETE`, `:132-147`), and `_rollback_precommit` is driven entirely by that journal. Anything the rollback must restore has to be RECORDED in the journal first; that is the existing pattern for `original_bytes` and `git_index_entries`, and it is the pattern this fix follows.
- The rollback deliberately refuses a destructive restore when a concurrent writer changed a path since the checkpoint, classifying it `unknown-outcome` instead. That fail-closed posture is load-bearing in a shared checkout and must extend to the index files.
- The index manifests are GITIGNORED in this repository (`.aw/.gitignore:45-46`, verified with `git check-ignore`), not merely untracked. That is a stronger statement than "untracked" and it lowers the severity further: the clean-base check excludes untracked paths, and a gitignored path is additionally invisible to a normal `git status`. The measured residue was observed with an explicit porcelain call in a test fixture, not in a run. The defect is real (a rollback that claims to restore does not) but it is a correctness defect, not an outage risk in this repository.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | A failed retirement leaves the shared checkout altered. Measured with `fault_injection="after_move"`: tree before was EMPTY; after the failure it held `?? .aw/records/plans/INDEX.json` and `?? .aw/records/plans/INDEX.md`, while the plan itself was correctly restored and HEAD unmoved. | reproduced through the repository's own test harness during the session that authored Order 04 |
| F-2 | The existing fault tests cannot catch it. They assert plan restoration, destination removal and HEAD, and never tree cleanliness. | `tests/test_orchestrator_retirement.py:1961-1972` |
| F-3 | The cause is in the rollback, not the mutation: step 4 regenerates the index from the current corpus rather than restoring its prior state. | `_rollback_precommit` docstring and body (`ipd_lifecycle.py:1874-1925`) |
| F-4 | Severity is low but real, and LOWER than first stated. The manifests are GITIGNORED, not merely untracked: `.aw/.gitignore:45-46` lists both, confirmed with `git check-ignore -v` (rc=0). So they are invisible to a normal `git status`, the clean-base check would not see them even if it included untracked paths, and no run has been observed to fail because of this residue. It is a correctness defect in a rollback that claims to restore, not an outage risk. | `.aw/.gitignore:45-46`; `git check-ignore -v` on both paths returns rc=0 |
| F-5 | This fix is INDEPENDENT of the worktree relocation. `/plan-review` established that Order 04's E-03 and E-04 are not gated by its blocking OQ-03, which is why they are carved here. | Order 04 (`u23gbn`) OQ-03: "E-03 and E-04 are NOT gated and may be executed on their own" |

## Proposed changes (ordered, validatable)

1. Record the index manifests' prior state in the journal and restore it on the rollback path, preserving the `unknown-outcome` refusal for a concurrent change (E-01).
2. Add tree-cleanliness assertions to the two existing fault-injection tests, proven to fail against the pre-fix behavior (E-02).

## Deferred / out of scope (with reason)

- Relocating the retirement mutations into a coordinator-owned worktree. That is Order 04 (`u23gbn`) and is gated on its blocking OQ-03, which asks whether the change belongs in the SHARED `_finalize_transaction` (two callers, reaching every plan's terminal transition) or in a forked rollup-specific body. This plan needs no answer to that question.
- Making the index manifests tracked, or changing how they are generated. Out of scope; only the rollback path's behavior is wrong.
- The success path's regeneration. Correct as it stands: a successful retirement really does change the corpus.

## Scope check

- Over-scope: none. Two files, one rollback path, two existing tests extended.
- Under-scope: this plan fixes the index manifests specifically, and does not audit `_rollback_precommit` for other paths it may write rather than restore. If review wants that audit it should be its own plan; state so rather than widening this one.

## Required tests / validation

- The two existing fault-injection cases (`after_move`, `before_commit`) extended with a tree-cleanliness assertion, passing.
- The new assertion demonstrated FAILING against the pre-fix behavior, so it is proven to detect the defect.
- A concurrent-change case: if the index manifests changed since the checkpoint, the rollback refuses a destructive restore and classifies `unknown-outcome` rather than clobbering them.
- A successful retirement still regenerates the index correctly (the success path is unchanged).
- Full suite run bare, with the failure set diffed against a baseline from the same commit; paste both counts and the diff.

## Spec / documentation sync

- No spec amendment expected: spec `77tr3o` R-4/R-5/R-6 govern what the transition MEANS, and this plan changes only whether a failed rollback restores two generated files. VERIFY BEFORE EXECUTING by reading those requirements; if one speaks to rollback completeness, amend it in this plan and add the spec file to `Scope-Paths` first.
- Update `_rollback_precommit`'s docstring, which currently says it "regenerates the plans index from the CURRENT corpus" as a description of correct behavior.

## Open questions

### OQ-01: Restore the index manifests from the journal, or regenerate them from the restored corpus?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED at authoring from the requirement itself, so no human decision is needed. The acceptance property is observable and stated in E-01: after a failure the tree must be byte-identical to before the attempt. RESTORING FROM THE JOURNAL satisfies that directly. Regenerating from the restored corpus would usually produce the same bytes, but only if the corpus is byte-identical AND the generator is deterministic, and it would still CREATE the files in a tree where they may not have existed at all before the attempt, which is exactly the observed defect. So restore, and record the prior state (including "absent") in the journal. Non-blocking and resolved because the plan's own acceptance criterion decides it; recorded so the implementer does not re-open it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `git status --porcelain` immediately BEFORE and immediately AFTER a `fault_injection="after_move"` retirement, both EMPTY. The pre-fix measurement showed `?? .aw/records/plans/INDEX.json` and `?? .aw/records/plans/INDEX.md`; the after must show neither. Also paste the concurrent-change case showing `unknown-outcome` and no destructive restore, and a successful retirement showing the index still regenerated.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the extended fault-injection test output for both the `after_move` and `before_commit` cases, and paste the assertion FAILING against the pre-fix behavior (or state precisely why that demonstration is impossible). A test that only passes after the fix is not evidence that it detects the bug. Paste the bare full-suite counts before and after with the FAILED-set diff.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one measured defect in one rollback path, plus the assertion that pins it. Carved from Order 04 precisely so it carries no architecture decision.

Execution contract: commit only files this plan changed, path-scoped, never `git add -A`, never push. Paste actual runner output for every test claim. Do not weaken the rollback's `unknown-outcome` refusal in the course of this change.

Post-gate lifecycle move: this plan reaches `executed/` only when every V-item above carries pasted evidence and `aw ipd lint --phase pre-transition` reports conforming.
