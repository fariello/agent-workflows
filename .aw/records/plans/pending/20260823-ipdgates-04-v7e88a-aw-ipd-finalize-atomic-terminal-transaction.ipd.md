# IPD: aw ipd finalize atomic terminal transaction

- Date: 2026-08-23
- Kind: child
- Concern: A plan reaches `executed` today via `aw set executed`, which moves the file and writes a generic `executed (aw set)` actor with no scope comparison and no captured pre/post gate evidence - exactly the p7dqwz failure signature. There is no single command that atomically performs the terminal transition WHILE proving the changed paths stayed within the reviewed `Scope-Paths` and the gates ran.
- Scope: Add `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` as the only supported single-IPD terminal transaction (happy path + scope comparison + evidence). Touch: the single-IPD lifecycle module (from Order 03), agent_workflows/cli.py (register `ipd finalize`), agent_workflows/ipd_lint.py (invoke pre/post-transition phases), agent_workflows/status_set.py (reuse the status-write/move + owned-index-refresh helpers), and tests/test_ipd_lifecycle_cli.py. Does NOT implement the two-phase ROLLBACK/failure semantics (Order 05) or remove the raw bypass (Order 06); this child delivers the forward transaction and the scope-comparison refusal.
- Status: draft
- Set: ipdgates
- Order: 4
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: v7e88a

## Workflow history

- 2026-08-23 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created (decomposition of 39fz2x E-04, forward-transaction portion; rollback split to Order 05).

## Goal

Provide `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` as the single atomic terminal transaction for one IPD. On the happy path it: validates the matching `aw ipd begin` receipt (Order 03); runs pre-transition lint; computes the set of changed paths SINCE the receipt's frozen base HEAD (both committed commits and current working-tree changes attributable to this execution) and compares them against the frozen `Scope-Paths`, REFUSING on any unexplained path; appends the required attributed agent/model history entry; sets terminal status and moves the plan; refreshes ONLY the owned plan-index state; creates a path-scoped lifecycle commit; runs post-transition lint; and reports the commit plus the captured pre/post gate outputs. It MUST refuse the exact p7dqwz signatures: an extra `tests/test_empty_state_ux.py` path not in `Scope-Paths`, and absent pre-execution/pre-transition evidence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Scope comparison against the frozen receipt

- [ ] E-01 In the single-IPD lifecycle module, implement the finalize precheck: load and validate the matching begin receipt (fail if absent, or if the plan digest no longer matches the receipt); run pre-transition lint (fail closed on nonconform); compute the changed-path set SINCE the receipt's frozen base HEAD - the union of paths in commits made since the base AND current uncommitted changes attributable to this execution - and compare it against the frozen `Scope-Paths` (honoring the implicit lifecycle/generated exceptions from Order 02). Any path NOT in the allowlist is an unexplained-path REFUSAL with an actionable diagnostic naming the path; leave the plan unmoved on refusal.
  - Depends on: none
  - Expected outcome: finalize can decide, from the frozen receipt + real changed paths, whether execution stayed in scope, and refuses (plan unmoved) on any unexplained path.
  - Execution state: pending

### Task group 2: The atomic forward transition

- [ ] E-02 Implement the forward transition (only reached when E-01's precheck passes): append the attributed `<agent/model>` + `<summary>` history entry (never a generic actor), set terminal status, move the plan file, refresh ONLY the owned plan-index state (reuse `status_set` helpers), create the path-scoped lifecycle commit (only this plan's own files), run post-transition lint, and report the commit hash plus the captured pre-execution (from the receipt), pre-transition, and post-transition gate outputs. Register `aw ipd finalize <plan> --actor --message --apply` in `cli.py` with help and the 0/1/2 exit convention. (Failure/rollback handling is Order 05; this item implements the success path and its evidence report.)
  - Depends on: E-01
  - Expected outcome: on a clean, in-scope execution, one command performs the whole terminal transition and reports commit + three-phase gate evidence with attributed history.
  - Execution state: pending

### Task group 3: Prove the p7dqwz counterexample and positive fixture

- [ ] E-03 Add `tests/test_ipd_lifecycle_cli.py` finalize tests: (counterexample) a receipt allowing the planned files but a working tree that also changed `tests/test_empty_state_ux.py` (not in `Scope-Paths`) -> finalize REFUSES naming the unexpected path and leaves the approved plan, index, and history UNCHANGED; (positive) the same extra path INCLUDED in the reviewed `Scope-Paths` -> begin, pre-transition, path comparison, attributed history, terminal move, narrowly-refreshed index, path-scoped lifecycle commit, and post-transition all SUCCEED with agent/model attribution and captured evidence; (evidence-absent) finalize with no matching receipt REFUSES. Confirm `pytest -n auto` is green.
  - Depends on: E-01, E-02
  - Expected outcome: the exact observed failure is refused, the authorized case succeeds with full evidence, and a missing receipt is refused.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `status_set.py` already implements plan status-write, file move between disposition dirs, and owned-index refresh (with an exception-swallow at `status_set.py:580,617`); finalize REUSES these mechanisms behind the gated path rather than duplicating them.
- Run packets / verifier-role code already carry `allowed_paths`/`forbidden_paths` matching; reuse that path-matching rather than a second engine.
- `aw ipd lint` owns the pre-transition and post-transition phases; finalize INVOKES them.
- The begin receipt (Order 03) provides the frozen base HEAD + `Scope-Paths` this transaction binds to.

## Findings

The terminal transition must be one transaction so scope comparison, attributed history, the three gates, and the lifecycle commit cannot be partially skipped. Comparing against the frozen base HEAD (not just the end-state tree) is what lets finalize attribute changes to THIS execution and ignore pre-existing/concurrent edits.

## Proposed changes (ordered, validatable)

1. Receipt-validated pre-transition + changed-path-vs-Scope-Paths comparison with unexplained-path refusal (E-01).
2. The atomic forward transition (history, status/move, owned-index, path-scoped commit, post-transition lint, evidence) + CLI verb (E-02).
3. Counterexample + positive + evidence-absent tests (E-03).

## Deferred / out of scope (with reason)

- Two-phase ROLLBACK and post-commit incomplete-reporting: Order 05 (its own adversarial test surface).
- Removing raw `aw set executed`: Order 06.
- Concurrency/ambiguous-baseline edge exhaustiveness: the core refusal is here; the adversarial concurrency matrix is Order 05.

## Scope check

- Over-scope: none.
- Under-scope: none for the forward transaction; rollback is deliberately Order 05.

## Required tests / validation

- `tests/test_ipd_lifecycle_cli.py` finalize tests per E-03 (counterexample, positive, evidence-absent).
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Amend the IPD lifecycle spec (managed verb) and `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md` with the finalize transaction contract; update CLI `--help`. Update `.aw/records/plans/README.md` and `CONTRIBUTING.md` to point terminal transition at `aw ipd finalize` (the raw-path removal itself is Order 06).

## Open questions

### OQ-01: How is "changed since base HEAD attributable to THIS execution" computed when unrelated concurrent commits/edits exist?

- Blocking: yes
- Status: open
- Owner: human
- Resolution or deferral rationale: TODO (human). The worktree may contain concurrent unrelated edits (as it does now with `unifyfileio`/`execset` changes) and there may be intervening commits by other work. Options: (A) compare ONLY the paths this execution's own commits touched (diff base..HEAD limited to commits authored under this receipt) plus staged/working changes the executor is about to commit - ignore unrelated dirty files entirely; (B) require a clean baseline and treat ANY change since base as in-scope-or-refuse (simplest, but hostile to the current multi-plan worktree reality); (C) an ambiguous intervening state (e.g. commits by another actor since base) fails closed with an actionable diagnostic. The executor MUST get a human decision, since it defines what finalize considers "this execution's changes".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a test shows finalize loads+validates the receipt, runs pre-transition lint, computes changed paths since the frozen base per OQ-01's resolution, and REFUSES an unexplained path (plan unmoved), while accepting an in-`Scope-Paths` change; a stale/mismatched receipt is rejected.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: on a clean in-scope run, finalize appends an attributed (non-generic) history entry, sets terminal status, moves the plan, refreshes only the owned index, creates a path-scoped lifecycle commit of only this plan's files, runs post-transition lint, and reports the commit + three-phase gate evidence; `--help` documents it with 0/1/2 exit codes.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the p7dqwz counterexample refuses `tests/test_empty_state_ux.py` and leaves plan/index/history unchanged; the positive fixture (extra path in `Scope-Paths`) fully succeeds with attribution + evidence; a missing receipt refuses; `pytest -n auto` is green (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - the forward atomic terminal transaction with scope comparison and evidence (rollback is Order 05).

### Execution contract

1. Open questions RESOLVED: OQ-01 (what "this execution's changes" means vs concurrent edits) MUST be resolved by a human before E-01.
2. Scope fence: touch ONLY the single-IPD lifecycle module, `cli.py` (finalize verb), `ipd_lint.py` (invoke pre/post-transition), `status_set.py` (reuse move/index helpers behind the gated path), `tests/test_ipd_lifecycle_cli.py`, and the lifecycle doc/spec/README/CONTRIBUTING via managed verbs. Do NOT implement rollback (Order 05) or remove the raw bypass (Order 06). If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests/gates passed, paste the ACTUAL runner output and the receipt path/digest; never claim a pass from narration or an unchecked box.
4. Commit ONLY this plan's own changed files, path-scoped; never `git add -A`/bare/`-a`; never push. Before each commit, compare the intended path list with `git diff --name-only` and leave concurrent user/agent edits untouched.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit. This is the FIRST plan that MAY dogfood its own `aw ipd finalize` once E-02 lands; if it does and the finalizer cannot finalize it, STOP and report (do not fall back to a raw transition).
