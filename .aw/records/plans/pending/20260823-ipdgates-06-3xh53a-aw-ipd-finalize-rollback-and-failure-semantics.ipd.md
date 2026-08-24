# IPD: aw ipd finalize rollback and failure semantics

- Date: 2026-08-23
- Kind: child
- Concern: The finalize transaction (Order 04) performs several steps (history append, status set, file move, index refresh, path-scoped commit, post-transition lint). If a step fails, a partial transition (e.g. plan moved + status set but no commit, or a post-commit lint failure) leaves the repo in an inconsistent, misleading state. Without explicit two-phase failure semantics, a failed finalize could look like a success or strand the plan half-transitioned.
- Scope: Add crash-safe two-phase failure semantics to `aw ipd finalize` and its adversarial tests. Touch: the single-IPD lifecycle module (from Orders 03/04/05), tests/test_ipd_lifecycle_cli.py, and the lifecycle spec/workflow/help through their managed owners. DEPENDS ON Order 05: rollback wraps the COMPLETE finalize transaction, which by this point includes the forward transition (Order 04) AND the two-way scope reconciliation (Order 05); rollback must therefore preserve or unwind reconciliation-side effects too. Reuse the repository's canonical `.aw/state/runtime/` transaction-journal + lock pattern rather than an in-memory-only snapshot. Does NOT change the forward happy path (Order 04) or the reconciliation policy (Order 05) beyond wrapping them in recovery, and does NOT remove the raw bypass (Order 07).
- Status: reviewed
- Set: ipdgates
- Order: 6
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 3xh53a

## Workflow history

- 2026-08-23 /plan-review (codex/gpt-5.6-sol): APPROVE WITH REVISIONS APPLIED. PR-001 (HIGH: the snapshot existed only conceptually/in memory and could not recover a crash or interruption; added an atomic runtime journal, finalize lock, idempotent recovery, and crash fault injection, reusing the layout-migration transaction pattern); PR-002 (HIGH: blindly restoring INDEX bytes and merely unstaging could clobber concurrent index/staging work; added exact owned-path Git-index preservation, deterministic index regeneration after plan restore, collision checks, and staged/disjoint concurrency tests); PR-003 (HIGH: post-commit INCOMPLETE had no executable resume contract and the receipt alone did not define commit-outcome ambiguity; added journal phases, commit-outcome classification, same-command post-commit resume, and fail-closed unknown-outcome handling); PR-004 (MEDIUM: E-01 bundled journal ownership, rollback, post-commit recovery, and observability into one pass; decomposed them into focused E/V items). No blocking OQ.
- 2026-08-23 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created (split from 39fz2x E-04, the rollback/failure-semantics portion, per the reviewer's density finding).
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. Verified artifact_core.git_mv (artifact_core.py:136), Order 04 exists and its OQ-01 is resolved consistently (path-overlap policy, commit 8fd5454 by a concurrent agent). PR-001 (rollback mechanism was underspecified - "track each mutation" doesn't restore in-place status/history edits; added explicit SNAPSHOT-and-restore of the plan's original bytes/path + the INDEX bytes, plus the ordering invariant that all mutations are working-tree-only before the single last commit, so rollback = discard this plan's own working-tree changes without touching concurrent agents' files); PR-002 (index must be restored on rollback, not just the plan file - E-01/V-01/E-02 now assert INDEX byte-restore, including a failure injected AFTER the index rewrite); PR-003 (post-commit INCOMPLETE must be durably detectable, not just printed - finalize leaves the begin receipt UNCONSUMED so a later query distinguishes committed-but-incomplete from cleanly-executed). Step-0 records the inherited concurrency policy. No blocking OQ.
- 2026-08-23 renumber (opencode its_direct/pt3-claude-opus-4.8-1m-us): Order 05 -> 06 to make room for a new Order 05 (finalize two-way scope reconciliation, per DECISIONS.md D141). Filename + front-matter Order updated via `aw rename`; reset to `to-review` because the rollback now wraps a finalize that includes the new reconciliation step (a later child), and the numbering context changed.
- 2026-08-23 consistency-fix (opencode its_direct/pt3-claude-opus-4.8-1m-us): post-renumber Set audit - declared the explicit dependency on Order 05 in Scope (body previously named only Order 04, contradicting orchestrator 00's table which says 06 depends on 05); corrected the Deferred line "Removing the raw bypass: Order 06" -> "Order 07".

## Goal

Make `aw ipd finalize` safe under ordinary failure AND process interruption with a durable two-phase boundary at the lifecycle commit. BEFORE the commit, any failed or interrupted step (receipt validation, pre-transition lint, scope reconciliation, history append, status set, file move, index refresh) MUST be recoverable to the pre-finalize state without touching unrelated concurrent work. AFTER a commit, a failed or interrupted post-transition check MUST remain a durably classified INCOMPLETE transaction that the same finalize command can resume without amending/resetting history or creating a second lifecycle commit. A commit-command error must be classified from repository evidence rather than guessed. No failure path may return or later report clean finalize success until post-transition validation passes and the receipt/journal is completed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Durable transaction ownership and checkpoints

- [ ] E-01 Before any finalize mutation, acquire one exclusive finalize lock covering the shared plan manifest and atomically create/update a transaction journal under the canonical gitignored `.aw/state/runtime/` transaction area (reuse the crash-safe layout-migration pattern; do not invent conversational/in-memory state as authority). Persist: plan Id/digest and original path+bytes; pre-finalize HEAD; the intended lifecycle-owned path set; existence/digests/bytes for INDEX.json and INDEX.md; the exact pre-existing Git-index entries for lifecycle-owned paths; the begin receipt and Order-05 reconciliation-state identifiers/digests; and a phase/checkpoint enum sufficient to distinguish prepared, mutating, ready-to-commit, committed-incomplete, unknown-outcome, and complete. Write each checkpoint atomically before proceeding to the next irreversible action. A second finalizer for the same/shared manifest fails with an actionable lock-owner/retry diagnostic; stale-lock recovery must consult the journal rather than deleting state blindly.
  - Depends on: none
  - Expected outcome: finalize has one durable, resumable source of transaction truth and serializes the short shared-manifest mutation window without serializing unrelated plan execution.
  - Execution state: pending

### Task group 2: Pre-commit rollback and interrupted-run recovery

- [ ] E-02 Wrap every Order-04/05 mutation before the lifecycle commit in idempotent journal-driven rollback. Restore the plan to its original bytes/path with atomic writes; leave the begin receipt and optional `scope add`/reconciliation answers unconsumed until full success; restore the exact prior Git-index entries for lifecycle-owned paths without altering any disjoint staged or dirty work. Do NOT blindly rewrite snapshotted INDEX bytes over concurrent state: after restoring the plan, regenerate the plan index deterministically from the CURRENT corpus, verify it, and require its result to equal the original bytes only when no concurrent plan-state change occurred. If an owned path changed incompatibly since the recorded checkpoint, classify `unknown-outcome` and stop without destructive restore. On process restart, re-running `aw ipd finalize <same-plan>` must detect any prepared/mutating/ready-to-commit journal and idempotently finish rollback before offering a fresh attempt. Rollback failure retains the journal/lock recovery evidence and exits nonzero; it never reports the repository restored.
  - Depends on: E-01
  - Expected outcome: exceptions and crashes before commit converge to a truthful pre-finalize plan/index/Git-index state while preserving unrelated concurrent work; a collision is surfaced rather than overwritten.
  - Execution state: pending

### Task group 3: Commit boundary and post-commit completion

- [ ] E-03 Treat the commit boundary by OBSERVED repository state, not by whether the commit subprocess was merely invoked. Persist the pre-commit HEAD and intended path/tree evidence; after the commit call (including a nonzero/interrupt result), classify: HEAD unchanged/no lifecycle commit -> pre-commit rollback; the intended lifecycle commit exists -> `committed-incomplete`; incompatible or ambiguous HEAD/path evidence -> `unknown-outcome`, fail closed, and preserve the journal. For `committed-incomplete`, never amend/reset or create a second lifecycle commit: report INCOMPLETE with the exact same-command recovery action `aw ipd finalize <plan>`; leave the begin receipt and reconciliation run-state unconsumed; and on that re-invocation resolve the executed selector, verify the recorded commit/path/digests, rerun only post-transition validation, then atomically mark receipt + journal complete on success. If validation still fails, require the corrective-follow-up IPD prescribed by the lifecycle workflow and retain INCOMPLETE. Only `complete` may return/report finalize success; a missing/corrupt journal at an apparently partial terminal state is `unknown-outcome`, never inferred success.
  - Depends on: E-01, E-02
  - Expected outcome: commit-command ambiguity and post-commit failures have deterministic, non-history-rewriting outcomes and an executable recovery path.
  - Execution state: pending

### Task group 4: Adversarial proof

- [ ] E-04 Add adversarial `tests/test_ipd_lifecycle_cli.py` tests covering: failure at each pre-commit checkpoint, failure after index rewrite, crash/restart after move and after index refresh, rollback failure, stale-lock recovery, two simultaneous finalizers, commit hook/no-commit failure, commit-succeeded-but-result-interrupted ambiguity, post-transition failure plus same-command resume, persistent post-transition failure requiring a corrective, and corrupt/missing journal unknown-outcome. Assert plan bytes/path, receipt/reconciliation consumption state, journal phase, HEAD, INDEX correctness, and the exact Git-index entries. Prove pre-existing dirty AND staged disjoint work is never committed or altered; prove a concurrent plan/index change is preserved by regeneration or fails closed rather than being overwritten; and retain the inherited in-`Scope-Paths` intervening-commit refusal. Confirm focused tests and `pytest -n auto` are green with actual output pasted.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: exception, crash, concurrency, ambiguous-commit, post-commit-resume, and recovery-failure semantics are empirically proven rather than narrated.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Order 04 delivers the forward finalize transaction (history/status/move/index/commit/post-lint) whose steps this child wraps; the mutation helpers are the `status_set` primitives finalize reuses.
- `git` is the commit mechanism (`artifact_core.git_mv`, `artifact_core.py:136`, + a path-scoped commit). `git_mv` stages the rename and its fallback is a plain filesystem move, so the journal must record filesystem AND Git-index state rather than assuming one mechanism succeeded atomically.
- The repository's canonical crash-safe precedent is `layout_migration.MigrationManager`: a lock + transaction file under `.aw/state/runtime/`, atomic checkpoint persistence, a per-mutation journal, and idempotent resume/rollback. This plan reuses that pattern at smaller scope (GUIDING_PRINCIPLES P5/P10/P11) rather than relying on an exception handler with volatile snapshots.
- INDEX.json/INDEX.md are shared generated views, not exclusively owned document bytes. Restoring stale snapshots can erase a concurrent plan transition; rollback restores the plan first and regenerates/validates the index from the current corpus, with byte-equality required only in the no-concurrency case.
- Concurrency policy is INHERITED from Order 04 OQ-01 (resolved, human): "this execution's changes" = the diff restricted to this plan's frozen `Scope-Paths` since the frozen base; unrelated concurrent commits/edits on DISJOINT paths are ignored, an intervening commit touching this plan's `Scope-Paths` fails closed. Rollback MUST never touch concurrent agents' files (working-tree-only restore of this plan's own paths).
- The path-scoped commit rule (only this plan's own files; leave concurrent edits untouched) is a standing repo contract; the concurrency tests enforce it for finalize.

## Findings

A multi-step terminal transaction without a defined failure boundary is the classic partial-commit hazard. Splitting rollback into its own IPD (per the reviewer's density finding on the original single E-04) gives it a dedicated adversarial test surface rather than burying it inside the forward-path item.

## Proposed changes (ordered, validatable)

1. Durable transaction journal, lock, and exact ownership snapshot (E-01).
2. Idempotent pre-commit rollback and crash recovery without concurrent-work loss (E-02).
3. Evidence-based commit-boundary classification and same-command post-commit completion (E-03).
4. Adversarial proof across exceptions, crashes, concurrency, and ambiguous outcomes (E-04).

## Deferred / out of scope (with reason)

- The forward happy path and scope comparison: Order 04; the two-way scope reconciliation: Order 05 (both dependencies, wrapped by this rollback).
- Removing the raw bypass: Order 07.

## Scope check

- Over-scope: none.
- Under-scope repaired by this review: durable crash recovery, shared-index/Git-index preservation, and an executable post-commit resume contract were previously missing.

## Required tests / validation

- Adversarial failure tests in `tests/test_ipd_lifecycle_cli.py` per E-04.
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Document the journal phases, lock behavior, pre-commit rollback, unknown-outcome refusal, same-command post-commit resume, and corrective-follow-up condition in the IPD lifecycle spec + workflow doc via the managed verbs; update `aw ipd finalize --help` so interruption and recovery are learn-as-you-go.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: corrective author
- Resolution or deferral rationale: no open human decision remains. D141 fixes the truth-preserving recovery policy; the lifecycle workflow fixes the no-history-rewrite/corrective rule; `layout_migration.MigrationManager` supplies the repository's canonical lock + runtime-journal + idempotent-resume pattern; and Order 04 OQ-01 fixes concurrent path attribution. This plan applies those authorities rather than inventing a new policy.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: tests inspect the atomically-written journal and prove it records every required ownership/digest/checkpoint field; the finalize lock serializes two finalizers with an actionable retry diagnostic; stale-lock handling consults the journal; and no tracked file is mutated before the prepared checkpoint exists.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: exception and crash/restart tests prove a pre-commit failure restores the original plan bytes/path, preserves receipt/reconciliation state, restores exact lifecycle-owned Git-index entries, and leaves disjoint dirty/staged work untouched. INDEX files are byte-identical in the no-concurrency case; a concurrent plan/index change is retained by deterministic regeneration or produces a non-destructive unknown-outcome. Failed rollback remains journaled and never reports restored.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: tests prove a failed commit with unchanged HEAD rolls back; a commit that exists despite an interrupted/nonzero result is classified committed-incomplete; ambiguous HEAD/path evidence is unknown-outcome; post-transition failure leaves receipt/reconciliation unconsumed and reports the exact `aw ipd finalize <plan>` recovery action; re-invocation performs no second lifecycle mutation/commit, reruns post-transition validation, and completes the receipt/journal only on pass; persistent failure requires a corrective IPD.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: the complete focused fault matrix passes (per E-04), including interruption, rollback-failure, lock, staging, shared-index, commit ambiguity, post-commit resume, and corrupt-journal cases; `pytest -n auto` is green and its ACTUAL runner output is pasted.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - the finalize transaction's failure semantics - decomposed into four focused passes (journal ownership, pre-commit rollback, post-commit completion, adversarial proof).

### Execution contract

1. Open questions RESOLVED: none open (OQ-01 records the controlling D141/lifecycle/journal evidence); the concurrency definition is inherited from Order 04 OQ-01. PREREQUISITE: Order 05 is executed and its reconciliation run-state schema is inspectable; if it mutates state not covered by this journal/consumption contract, STOP and amend this plan before implementation.
2. Scope fence: touch ONLY the single-IPD lifecycle module (wrap the Order 04/05 transition), `tests/test_ipd_lifecycle_cli.py`, and the lifecycle spec/workflow/help through managed owners. Do NOT change the forward happy path or reconciliation policy beyond wrapping them in journal/recovery behavior, and do NOT remove the raw bypass. If an executable recovery path requires a new CLI flag/verb or another module rather than same-command resume, STOP and report; do not silently expand scope.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped; never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, transition via `aw ipd finalize` (it exists by now, Order 04) - append the `## Workflow history` line, set `Status: executed`, move the plan, path-scoped lifecycle commit - and if the finalizer cannot finalize this plan, STOP and report (never fall back to a raw transition).
