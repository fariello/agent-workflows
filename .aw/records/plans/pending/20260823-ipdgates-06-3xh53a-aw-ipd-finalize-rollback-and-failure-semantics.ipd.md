# IPD: aw ipd finalize rollback and failure semantics

- Date: 2026-08-23
- Kind: child
- Concern: The finalize transaction (Order 04) performs several steps (history append, status set, file move, index refresh, path-scoped commit, post-transition lint). If a step fails, a partial transition (e.g. plan moved + status set but no commit, or a post-commit lint failure) leaves the repo in an inconsistent, misleading state. Without explicit two-phase failure semantics, a failed finalize could look like a success or strand the plan half-transitioned.
- Scope: Add the two-phase failure semantics to `aw ipd finalize` and its adversarial tests. Touch: the single-IPD lifecycle module (from Orders 03/04) and tests/test_ipd_lifecycle_cli.py. Does NOT change the forward happy path (Order 04) beyond wrapping it in rollback, and does NOT remove the raw bypass (Order 06).
- Status: to-review
- Set: ipdgates
- Order: 6
- Highest E allocated: 02
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 3xh53a

## Workflow history

- 2026-08-23 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created (split from 39fz2x E-04, the rollback/failure-semantics portion, per the reviewer's density finding).
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. Verified artifact_core.git_mv (artifact_core.py:136), Order 04 exists and its OQ-01 is resolved consistently (path-overlap policy, commit 8fd5454 by a concurrent agent). PR-001 (rollback mechanism was underspecified - "track each mutation" doesn't restore in-place status/history edits; added explicit SNAPSHOT-and-restore of the plan's original bytes/path + the INDEX bytes, plus the ordering invariant that all mutations are working-tree-only before the single last commit, so rollback = discard this plan's own working-tree changes without touching concurrent agents' files); PR-002 (index must be restored on rollback, not just the plan file - E-01/V-01/E-02 now assert INDEX byte-restore, including a failure injected AFTER the index rewrite); PR-003 (post-commit INCOMPLETE must be durably detectable, not just printed - finalize leaves the begin receipt UNCONSUMED so a later query distinguishes committed-but-incomplete from cleanly-executed). Step-0 records the inherited concurrency policy. No blocking OQ.
- 2026-08-23 renumber (opencode its_direct/pt3-claude-opus-4.8-1m-us): Order 05 -> 06 to make room for a new Order 05 (finalize two-way scope reconciliation, per DECISIONS.md D141). Filename + front-matter Order updated via `aw rename`; reset to `to-review` because the rollback now wraps a finalize that includes the new reconciliation step (a later child), and the numbering context changed.

## Goal

Make `aw ipd finalize` safe under failure with an explicit two-phase boundary at the lifecycle commit: BEFORE the commit, any failed step (receipt validation, pre-transition lint, scope comparison, history append, status set, file move, index refresh) MUST roll the partial transition back to the pre-finalize state (plan unmoved, status unchanged, index unchanged, no dangling commit); AFTER the commit, a post-transition failure (e.g. post-transition lint fails) MUST be reported as INCOMPLETE without rewriting history (no amend/reset of the lifecycle commit) and with an actionable next step. No failure mode may leave a half-transitioned plan that looks executed, and none may claim success.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Two-phase rollback boundary

- [ ] E-01 Wrap the Order 04 forward transition in a two-phase boundary with an EXPLICIT rollback mechanism (not just "track each mutation"). ORDERING INVARIANT (verified against Order 04 E-02: the step order is history -> status -> move -> index -> COMMIT -> post-lint): every content mutation happens IN THE WORKING TREE before the single lifecycle commit, and the commit is the LAST mutation. ROLLBACK MECHANISM: before mutating, SNAPSHOT the pre-finalize state that in-place edits would destroy - the plan file's original bytes (its `- Status:` / `## Workflow history` lines are rewritten), its original path (the `git mv` source), and the affected INDEX.json/INDEX.md bytes (the index refresh rewrites them). A failure at ANY step BEFORE the commit rolls back by RESTORING those snapshots (git-mv the file back to its source path, rewrite the original plan + index bytes, unstage), leaving no partial move, no in-file status/history residue, no stale index, and no dangling commit; return nonzero with an actionable diagnostic. (Because all pre-commit mutations are working-tree-only, rollback is equivalently: discard THIS plan's own working-tree changes + restore its original path - never `git reset`/`checkout` that could touch concurrent agents' files.) A failure AT OR AFTER the commit is reported INCOMPLETE (the commit stands; do NOT amend/reset) with a clear "post-commit step X failed; the plan is committed but the transition is incomplete - repair via <path>" message, AND that incompleteness MUST be DURABLY DETECTABLE - not merely printed once: leave the Order 03 begin receipt UNCONSUMED (finalize marks the receipt consumed/complete only on full success), so a later `aw ipd begin`/`finalize`/status query can tell a committed-but-incomplete transition from a cleanly-executed one. Ambiguous intervening state fails closed. Never claim a successful execution on any failure.
  - Depends on: none
  - Expected outcome: every finalize failure is either a clean snapshot-restore rollback (pre-commit, including the index) or a durably-detectable reported-incomplete (post-commit), never a silent partial, stale index, or false success.
  - Execution state: pending

### Task group 2: Adversarial proof

- [ ] E-02 Add adversarial `tests/test_ipd_lifecycle_cli.py` failure tests: (pre-commit) inject a failure at each pre-commit step (simulated lint fail, scope-comparison refusal mid-transaction, index-refresh error injected AFTER the index was rewritten) and assert the repo is byte-identical to the pre-finalize state (plan unmoved, original plan bytes, INDEX.json/INDEX.md restored byte-identical, nothing staged, no commit); (post-commit) simulate a post-transition lint failure AFTER the commit and assert the command reports INCOMPLETE without amend/reset, names a repair next step, and leaves the begin receipt UNCONSUMED (assert the incomplete state is detectable via the receipt); (concurrency) assert pre-existing dirty files and unrelated concurrent work on DISJOINT paths are NEVER committed by finalize and are untouched by rollback, and an intervening commit touching this plan's `Scope-Paths` fails closed with an actionable diagnostic. Confirm `pytest -n auto` is green.
  - Depends on: E-01
  - Expected outcome: rollback, incomplete-reporting, and concurrency-safety are each proven with an adversarial test.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Order 04 delivers the forward finalize transaction (history/status/move/index/commit/post-lint) whose steps this child wraps; the mutation helpers are the `status_set` primitives finalize reuses.
- `git` is the commit mechanism (`artifact_core.git_mv`, `artifact_core.py:136`, + a path-scoped commit); a pre-commit rollback must restore the plan's original bytes/path AND the affected INDEX.json/INDEX.md (the index refresh rewrote them), then unstage; a post-commit failure must NOT rewrite history.
- Concurrency policy is INHERITED from Order 04 OQ-01 (resolved, human): "this execution's changes" = the diff restricted to this plan's frozen `Scope-Paths` since the frozen base; unrelated concurrent commits/edits on DISJOINT paths are ignored, an intervening commit touching this plan's `Scope-Paths` fails closed. Rollback MUST never touch concurrent agents' files (working-tree-only restore of this plan's own paths).
- The path-scoped commit rule (only this plan's own files; leave concurrent edits untouched) is a standing repo contract; the concurrency tests enforce it for finalize.

## Findings

A multi-step terminal transaction without a defined failure boundary is the classic partial-commit hazard. Splitting rollback into its own IPD (per the reviewer's density finding on the original single E-04) gives it a dedicated adversarial test surface rather than burying it inside the forward-path item.

## Proposed changes (ordered, validatable)

1. Two-phase boundary: pre-commit rollback; post-commit reported-incomplete without history rewrite (E-01).
2. Adversarial tests for rollback, incomplete-reporting, and concurrency-safety (E-02).

## Deferred / out of scope (with reason)

- The forward happy path and scope comparison: Order 04 (dependency).
- Removing the raw bypass: Order 06.

## Scope check

- Over-scope: none.
- Under-scope: none; the failure boundary and its adversarial proof are the whole concern.

## Required tests / validation

- Adversarial failure tests in `tests/test_ipd_lifecycle_cli.py` per E-02.
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Document the two-phase failure semantics (pre-commit rollback / post-commit incomplete) in the IPD lifecycle spec + workflow doc via the managed verbs; update `aw ipd finalize --help` if the failure contract needs surfacing.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: corrective author
- Resolution or deferral rationale: no open decision - the two-phase boundary (pre-commit rollback, post-commit reported-incomplete without history rewrite) is the standard, unambiguous transaction contract; the concurrency policy is inherited from Order 04's OQ-01 resolution ("this execution's changes" definition), which this child's concurrency tests exercise.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a test proves a pre-commit failure restores the EXACT pre-finalize state - plan unmoved (original path), original plan bytes (no residual `- Status:`/history edit), INDEX.json/INDEX.md byte-identical to pre-finalize, nothing staged, no commit - with a nonzero exit; a post-commit failure reports INCOMPLETE without amend/reset, names a repair path, and leaves the begin receipt UNCONSUMED so the incomplete state is detectable afterward.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: adversarial tests pass for each injected pre-commit step failure (clean rollback), the post-commit incomplete case, and the concurrency cases (pre-existing dirty + unrelated concurrent work never committed; ambiguous intervening commit fails closed); `pytest -n auto` is green (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - the finalize transaction's failure semantics and their adversarial proof.

### Execution contract

1. Open questions RESOLVED: none open (OQ-01 records why); the concurrency definition is inherited from Order 04 OQ-01.
2. Scope fence: touch ONLY the single-IPD lifecycle module (wrap the Order 04 transition) and `tests/test_ipd_lifecycle_cli.py`, plus the failure-semantics doc via managed verbs. Do NOT change the forward happy path beyond wrapping it, and do NOT remove the raw bypass. If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped; never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, transition via `aw ipd finalize` (it exists by now, Order 04) - append the `## Workflow history` line, set `Status: executed`, move the plan, path-scoped lifecycle commit - and if the finalizer cannot finalize this plan, STOP and report (never fall back to a raw transition).
