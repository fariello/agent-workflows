# IPD: Shared close-legitimacy predicate: aw backlog set done fails closed on a blocking item without handoff/resolvable-evidence/de-gate, plus aw check consistency rules

- Date: 2026-08-25
- Kind: child
- Concern: `aw backlog set done` on an item carrying `- Blocks-Release: <R>` currently drops it from the release-blocker view with NO check (backlog.py:426 gates only `-> blocked`), so a release gate can silently vanish when nothing has shipped and no plan inherited it. The agreed policy (design discussion 2026-08-25) is: a backlog item translated into a plan should be closed `done`, but a blocking item may only leave the active-blocker set if the gate is provably preserved or released. This must be a deterministic boundary, not prose, and it must be ONE shared predicate that the setter, `aw check`, and the child-03 hook all call so they cannot diverge (the status_untooled_gate.py:33-45 pattern: hook delegates to a single check_engine rule).
- Scope: Implement the shared close-legitimacy predicate and wire it at the setter + check surfaces (child 03 adds the hook). (1) Predicate: a single function (in check_engine.py) `evaluate_blocking_close(repo_root, item_path, target_status, evidence=None)` that, for an item carrying `Blocks-Release: <R>`, returns per-transition severity: `-> done` is LEGITIMATE iff one of {HANDOFF: a plan carrying `From-Backlog: <this id6>` AND `Blocks-Release: <R>` (same release) exists; SATISFIED: a resolvable `evidence` citation - generalize the specs `_evidence_resolvable` (specs.py:673) to accept an existing artifact path (executed IPD, a records file, a committed doc) not only executed IPDs; DE-GATED: the item no longer carries Blocks-Release, i.e. it was cleared in/before this transition}, else ILLEGITIMATE (fail-closed). (2) Setter gate: in `agent_workflows/backlog.py` `run_set`, before writing, if new_status == "done" and the item carries Blocks-Release and none of the three paths hold, REFUSE with a teaching error naming all three fixes (`--from-backlog` plan, `--evidence <path>`, or `--blocks-release -`); add `--evidence` to `aw backlog set` (cli.py). (3) WARN transitions (allowed, never block): blocking `-> parked` and priority-demote-of-a-blocker emit `aw check`/`attention` warnings (severity warn, not error). (4) `aw check` consistency rules reusing the predicate: `check.blocking-item-closed-without-gate` (an already-`done` blocking item with no preserved/satisfied gate - the backstop for a hand-edit bypass), `check.from-backlog-gate-mismatch` (a `From-Backlog` plan whose `Blocks-Release` != the item's), and `check.orphaned-live-blocker` (a blocking item already graduated to a blocking plan but still `open` - warn). Everything else (priority promote, open<->parked non-blocking, block/unblock, reopen) is unchecked.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/check_engine.py, agent_workflows/cli.py, agent_workflows/releases.py, agent_workflows/attention.py, agent_workflows/specs.py, tests/
- Status: draft
- Set: bklggrad
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: orb9zb

## Workflow history

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Implement one shared close-legitimacy predicate and enforce it at the `aw backlog set` setter and `aw check`: a release-blocking backlog item cannot reach `done` unless the gate is handed off (a `From-Backlog` blocking plan), satisfied (resolvable `--evidence`), or explicitly de-gated; blocking `-> parked` and priority-demote-of-a-blocker warn but never block. One predicate so setter/check/hook cannot diverge.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the shared predicate

- [ ] E-02 Add `evaluate_blocking_close(repo_root, item_path, target_status, evidence=None)` to `agent_workflows/check_engine.py` returning a structured verdict (legitimate/illegitimate + reason + severity). Implements the three legitimacy paths (HANDOFF via a `From-Backlog`+matching-`Blocks-Release` plan; SATISFIED via resolvable evidence; DE-GATED when Blocks-Release absent) and the two WARN cases (blocking->parked, priority-demote-of-blocker).
  - Depends on: none
  - Expected outcome: pure function returns fail-closed for a bare blocking `-> done`, legitimate for each of the three paths, and warn (not error) for park/demote. (Cross-IPD: consumes bklggrad-01's From-Backlog field/resolver; ordering tracked in the orchestrator dependency table.)
  - Execution state: pending
- [ ] E-03 Generalize evidence resolvability: factor the specs `_evidence_resolvable` (specs.py:673) into a shared resolver that accepts an existing executed IPD OR another resolvable artifact path (a records file / committed doc), so non-IPD backlog items (README/research/prompt/check work) can be closed with cited evidence. Keep specs' `implemented` behavior unchanged (it may pass its own stricter predicate).
  - Depends on: none
  - Expected outcome: the shared resolver accepts a real artifact path and rejects a nonexistent/unsafe one; specs `implementing -> implemented` behavior is unchanged.
  - Execution state: pending

### Task group 2: setter gate + --evidence

- [ ] E-04 In `agent_workflows/backlog.py` `run_set`, before rendering/writing, call the predicate when `new_status == "done"`; on an illegitimate blocking close, REFUSE (return nonzero) with a teaching error listing all three fixes. Add `--evidence <path>` to `aw backlog set` in `agent_workflows/cli.py` (dest `evidence`).
  - Depends on: E-02, E-03
  - Expected outcome: `aw backlog set done <blocking-item>` fails with the teaching error; adding a `From-Backlog` plan, or `--evidence <resolvable>`, or `--blocks-release -` each makes it succeed.
  - Execution state: pending

### Task group 3: check consistency rules + warns

- [ ] E-05 Add `aw check` rules reusing the predicate: `check.blocking-item-closed-without-gate` (error: an already-`done` blocking item with no preserved/satisfied gate), `check.from-backlog-gate-mismatch` (error: `From-Backlog` plan's `Blocks-Release` differs from the item's), and `check.orphaned-live-blocker` (warn: a still-`open` blocking item already graduated to a blocking plan). Fold into the cross-tree sweep next to `check_blocks_release`.
  - Depends on: E-02
  - Expected outcome: `aw check` fires each rule on a crafted fixture and is clean otherwise.
  - Execution state: pending
- [ ] E-06 Surface the WARN transitions in `agent_workflows/attention.py`/`aw check`: blocking `-> parked` and priority-demote-of-a-blocker emit a warning with a de-gate hint; never change exit-code-blocking behavior for these.
  - Depends on: E-02
  - Expected outcome: parking or demoting a blocker produces a warning surfaced by `aw check`/`aw attention`, exit code unaffected.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The setter gates only `-> blocked` today (backlog.py:426-436); the `done` branch has no check. That `if new_status == ...` block is the insertion point for the `done` gate.
- The hook/check no-divergence pattern is established: `status_untooled_gate.check` (hooks/status_untooled_gate.py:33) delegates to `check_engine.check_status_untooled`. Child 03's hook must delegate to THIS child's predicate the same way.
- Evidence resolvability precedent: specs `implementing -> implemented` requires a resolvable `--evidence` citation (specs.py:464-468, `_evidence_resolvable`:673), currently executed-IPD-only. Generalize, do not fork.

## Findings

The gate must be one predicate with three severities (fail-closed on `done`, warn on park/demote) consumed by three surfaces. The only new primitive needed beyond child-01's `From-Backlog` is a generalized evidence resolver so non-IPD items are closable.

## Proposed changes (ordered, validatable)

1. `check_engine.py`: `evaluate_blocking_close` predicate + the three `aw check` rules + the two warn signals.
2. Shared evidence resolver generalized from `specs._evidence_resolvable`.
3. `backlog.py` `run_set`: `done`-gate calling the predicate; `cli.py`: `--evidence`.
4. `attention.py`: surface the warn transitions.
5. `tests/`: fail-closed + each legitimacy path + each check rule + warn (non-blocking) behavior.

## Deferred / out of scope (with reason)

- The `From-Backlog` field/setter/dangling check: child 01 (dependency).
- The pre-commit hook + install wiring: child 03.
- Closing `3gr7fk` through the guard (dogfood): the orchestrator's post-set step, after this child + 01 land.

## Scope check

- Over-scope: none.
- Under-scope: none (predicate + setter gate + check rules + warns are the complete deliverable).

## Required tests / validation

- Fail-closed: `aw backlog set done` on a blocking item with no handoff/evidence/de-gate returns nonzero with the three-fix teaching error.
- Each legitimacy path succeeds: a matching `From-Backlog` blocking plan; a resolvable `--evidence`; a prior `--blocks-release -`.
- `aw check` fires `blocking-item-closed-without-gate`, `from-backlog-gate-mismatch`, `orphaned-live-blocker` on crafted fixtures; clean otherwise.
- Warn-only: blocking `-> parked` and priority-demote-of-blocker succeed (exit 0) but produce an `aw check`/`attention` warning.
- Non-regression: specs `implementing -> implemented` evidence behavior unchanged.

## Spec / documentation sync

- Update AGENTS.md "Release gates" to document the close-legitimacy rule and the three fixes; document `aw backlog set --evidence`.

## Open questions

### OQ-01: Should SATISFIED accept a git commit hash as evidence, or only an in-tree artifact path?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Start with a resolvable in-tree artifact path (deterministic, matches the specs precedent). A commit-hash form is a possible later extension; not required for the release blocker close.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-02 validates E-02
  - Required evidence: unit tests of `evaluate_blocking_close`: fail-closed on bare blocking `-> done`; legitimate for HANDOFF, SATISFIED, DE-GATED; warn for park/demote; paste output.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: test that the shared evidence resolver accepts a real artifact path and rejects nonexistent/unsafe; a spec `implementing -> implemented` regression test still passes; paste output.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: CLI test that `aw backlog set done <blocking-item>` fails with the three-fix teaching error, and succeeds via each of the three paths; paste output.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: tests that `aw check` fires `blocking-item-closed-without-gate`, `from-backlog-gate-mismatch`, and `orphaned-live-blocker` on fixtures and is clean otherwise; paste output.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: test that blocking `-> parked` and priority-demote-of-blocker each produce a warning via `aw check`/`aw attention` with exit code unchanged; paste output.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
