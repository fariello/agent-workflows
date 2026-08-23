# IPD: aw ipd begin fail-closed execution-start receipt

- Date: 2026-08-23
- Kind: child
- Concern: There is no durable, inspectable proof that an IPD passed the pre-execution gate at a known base HEAD before work began. p7dqwz's terminal record retained no pre-execution evidence, so scope/lifecycle claims could not be independently checked after the fact. A scope check performed only against the final working tree is insufficient (product changes may already be committed; unrelated concurrent edits may exist), so the allowlist and base MUST be frozen BEFORE execution.
- Scope: Add `aw ipd begin <plan> --actor <agent/model>` as the authoritative single-IPD execution entry and its receipt. Touch: a new narrowly-named single-IPD lifecycle module (e.g. `agent_workflows/ipd_lifecycle.py`), agent_workflows/cli.py (register the `ipd begin` verb + flags + help), reuse agent_workflows/run_freeze.py (`freeze_requirements`), agent_workflows/ipd_lint.py (invoke the pre-execution phase), and a new tests/test_ipd_lifecycle_cli.py. Does NOT implement finalize (Order 04) or remove bypasses (Order 06); it produces only the receipt that finalize will later require.
- Status: draft
- Set: ipdgates
- Order: 3
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: xjbvu2

## Workflow history

- 2026-08-23 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created (decomposition of 39fz2x E-03).

## Goal

Provide `aw ipd begin <plan> --actor <agent/model>` as the fail-closed start of single-IPD execution: it runs `aw ipd lint --phase pre-execution`, freezes the plan's requirements and `Scope-Paths` with the existing `run_freeze` primitives, binds a receipt to (plan Id, plan content digest, base HEAD, actor/model, timestamp), and atomically writes a resumable LOCAL lifecycle receipt. Any failure mode - lint exit 1/2, a dirty or ambiguous baseline, a missing actor/model, or an interrupted write - MUST leave NO valid receipt and therefore NO execution authority, so that finalize (Order 04) cannot later succeed without independently-inspectable proof that the approved plan and its scope passed the pre-execution gate at a specific base HEAD.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The receipt and its binding

- [ ] E-01 In a new single-IPD lifecycle module, implement the begin receipt: run the pre-execution lint phase; if it does not conform, write nothing and exit nonzero. On conformance, freeze the plan requirements and `Scope-Paths` via `run_freeze.freeze_requirements`, capture the base HEAD (refusing a dirty or ambiguous worktree/baseline with an actionable diagnostic), require a non-empty `--actor <agent/model>`, and build a receipt record binding {plan Id, plan content digest, frozen requirement/scope digest, base HEAD, actor/model, timestamp}. Write it ATOMICALLY to a local (uncommitted, gitignored) lifecycle-receipt location so an interrupted write leaves no partial/valid receipt; make it resumable (a re-read returns the same receipt deterministically).
  - Depends on: none
  - Expected outcome: a conforming pre-execution run yields exactly one atomic, resumable receipt bound to the plan+scope+base; any failure yields none.
  - Execution state: pending

### Task group 2: The CLI verb

- [ ] E-02 Register `aw ipd begin <plan> --actor <agent/model>` in `cli.py` calling the E-01 module, with help/usage text describing the receipt and the fail-closed contract, and the shared exit-code convention (0 ok / 1 findings / 2 cannot-run). Resolve the `<plan>` selector via the standard resolver. Do not mutate the plan or any tracked file (the receipt is local-only).
  - Depends on: E-01
  - Expected outcome: `aw ipd begin` is a usable CLI entry that produces the receipt and self-documents via `--help`.
  - Execution state: pending

### Task group 3: Prove fail-closed

- [ ] E-03 Add `tests/test_ipd_lifecycle_cli.py` begin-command tests: a conforming plan yields a receipt capturing plan Id, requirement/scope digest, exact `Scope-Paths`, base HEAD, actor/model, timestamp, and the pre-execution lint output; a changed plan digest INVALIDATES a prior receipt; lint exit 1/2, a missing `--actor`, a dirty/ambiguous baseline, and a simulated interrupted write each leave NO valid receipt; and a resume reads the same receipt deterministically. Confirm `pytest -n auto` is green.
  - Depends on: E-01, E-02
  - Expected outcome: every fail-closed path is proven to produce no execution authority, and the happy path is fully bound and resumable.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `run_freeze.freeze_requirements()` (`agent_workflows/run_freeze.py:131`) supplies stable requirement digests; reuse it rather than inventing a second digest engine.
- `aw ipd lint` already owns the phase checkpoints (`--phase pre-execution`); this command INVOKES it, it does not reimplement lint.
- Run records / receipts that carry machine-specific paths or session detail are LOCAL-ONLY by convention (see `.gitignore` for `workflow-artifacts/`); the receipt MUST be local-only and gitignored, never committed.
- `Scope-Paths` is defined by Order 02 (dependency); begin freezes whatever the approved plan declares.

## Findings

Freezing the scope+base BEFORE work is what makes a later scope comparison meaningful; checking only the end-state working tree cannot distinguish this IPD's changes from pre-existing commits or concurrent edits. The receipt is the anchor finalize (Order 04) binds its evidence to.

## Proposed changes (ordered, validatable)

1. Implement the atomic, resumable, fail-closed begin receipt bound to plan+scope+base+actor (E-01).
2. Register the `aw ipd begin` CLI verb with help + exit codes (E-02).
3. Test every fail-closed path + happy-path binding + resume (E-03).

## Deferred / out of scope (with reason)

- Terminal finalization and path comparison: Order 04.
- Removing raw `aw set executed`: Order 06.
- `Scope-Paths` schema/grammar: Order 02 (dependency).

## Scope check

- Over-scope: none.
- Under-scope: none; the receipt, its binding, the CLI verb, and fail-closed tests are included.

## Required tests / validation

- `tests/test_ipd_lifecycle_cli.py` begin tests per E-03.
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Amend the IPD lifecycle spec (via its managed verb) and `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md` to document `aw ipd begin` and the receipt; update CLI `--help`. (Docs may be batched into Order 04's transaction doc if cleaner, but the begin contract must be documented before the Set completes.)

## Open questions

### OQ-01: Where does the local receipt live, and what is its lifetime?

- Blocking: yes
- Status: open
- Owner: human
- Resolution or deferral rationale: TODO (human). The receipt must be local-only (never committed, may carry base HEAD + actor). Options: (A) under `.aw/` in a gitignored subdir (e.g. `.aw/state/ipd-lifecycle/<id6>.receipt.json`) - discoverable, co-located; (B) under the existing `workflow-artifacts/` local tree; (C) an OS-level per-repo cache dir. Also: does a receipt expire (e.g. invalid if base HEAD moved) or persist until finalize consumes it? The executor MUST get a human decision on location + lifetime before E-01 fixes the path.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a test shows a conforming run writes exactly one atomic receipt binding plan Id/digest/scope/base HEAD/actor/timestamp; lint-nonconform, dirty/ambiguous baseline, missing actor, and interrupted write each leave no valid receipt; a re-read is deterministic (resume).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: `aw ipd begin --help` documents the fail-closed contract; the verb resolves the plan selector, produces the receipt, mutates no tracked file, and returns the correct exit codes (0/1/2).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: `tests/test_ipd_lifecycle_cli.py` begin tests pass (happy binding + every fail-closed path + resume + digest-invalidation); `pytest -n auto` is green (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - the fail-closed pre-execution receipt and its CLI entry.

### Execution contract

1. Open questions RESOLVED: OQ-01 (receipt location + lifetime) MUST be resolved by a human before E-01.
2. Scope fence: touch ONLY the new single-IPD lifecycle module, `cli.py` (begin verb), `ipd_lint.py` (invoke pre-execution phase), reuse `run_freeze.py`, and `tests/test_ipd_lifecycle_cli.py`, plus the lifecycle doc/spec via managed verbs. Do NOT implement finalize or remove bypasses. If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output and the receipt path/digest; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push. The receipt is local-only and MUST NOT be committed (confirm it is gitignored).
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via the existing lifecycle workflow, since `aw ipd finalize` does not exist until Order 04).
