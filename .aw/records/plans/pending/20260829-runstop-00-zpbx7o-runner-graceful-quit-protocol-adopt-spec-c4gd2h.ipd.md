# IPD: Runner graceful-quit protocol: adopt spec c4gd2h

- Date: 2026-08-29
- Kind: orchestrator
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Spec c4gd2h (approved 2026-08-29) defines a graceful-quit protocol for `aw oc run` / `aw agy run`, which today has NO graceful stop: SIGTERM makes the driver print `Terminated` and exit while its child `opencode` is reparented to init and keeps writing the tree, `driver.lock` is left holding a dead PID (`run_lock`, oc_runipd.py:738-756, never unlinks the lock file), and the working tree is left mid-edit. The driver installs NO signal handlers of its own (verified: the only signal references in oc_runipd.py are inside `terminate_process`, :1632-1670). This orchestrator sequences the 6-child adoption of spec c4gd2h and closes backlog kjzlgw.
- Scope: ORCHESTRATOR - authors NO product code. Its own execution work is (E-01) whole-Set verification only. The children carry all implementation. This plan owns the child table + dependency chain, the shared anti-greenwash execution contract every child inherits, the Set completion criteria, and the cross-IPD no-drift checks. It cites spec c4gd2h as binding and each child names the spec requirement ids (R1-R23) and acceptance criteria (A1-A10) it implements.
- Scope-Paths: .aw/records/plans/pending/20260829-runstop-00-zpbx7o-runner-graceful-quit-protocol-adopt-spec-c4gd2h.ipd.md
- Item-Dependencies: none
- Status: to-review
- Set: runstop
- Order: 0
- Highest E allocated: 01
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: zpbx7o

## Workflow history
- 2026-08-29 to-review (aw set): Authored review-ready from spec c4gd2h (graduation of backlog kjzlgw).

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.

## Goal

Adopt spec c4gd2h across a 6-child, dependency-ordered migration that gives `aw oc/agy run` four stop levels over ONE unconditional clean-shutdown invariant, so no stop ever leaves an orphaned agent process, a stale lock, an incoherent ledger, or a contaminated tree. Every child is authored greenwash-proof: acceptance is a pasted command result or an observation of real process/git/filesystem state, never an agent's prose claim.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: whole-Set verification (orchestrator authors no code)

- [ ] E-01 After ALL children (runstop-01..06) are in `executed/`, run the whole-Set verification: confirm every child's V-items were satisfied with pasted evidence, confirm spec c4gd2h acceptance criteria A1-A10 hold against the real repo, and confirm no cross-IPD drift (see Cross-IPD validation). Author no product code here.
  - Depends on: none
  - Expected outcome: a single verification record demonstrating each of A1-A10 holds with pasted command evidence; any failing criterion blocks the Set (this orchestrator stays not-executed).
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | What it does | Depends on | Spec ids |
|---|---|---|---|---|
| 00 | zpbx7o | Orchestrator (this) | - | R1-R23, A1-A10 |
| 01 | 2ouj70 | Phase 0: the ONE shared clean-shutdown routine (reap tree, release lock, coherent ledger, quarantine tree) + characterization tests pinning today's broken behavior | - | R1-R6, R23, A9 |
| 02 | gq6m2u | Phase 1: durable, idempotent, monotonic stop-request flag + the cooperative checkpoint poll | executed:2ouj70 | R7-R9, R11 |
| 03 | 1qxuke | Phase 2: levels 1-2 (stop-after-call, stop-after-set) at between-turn checkpoints | executed:gq6m2u | R20, A1, A4 |
| 04 | foi1b3 | Phase 3: level 3 (stop-now) at the next OBSERVED safe checkpoint, KNOWN disposition | executed:1qxuke | R10, R18, A3 |
| 05 | m0z0ti | Phase 4: level 4 (stop-now-force), `unknown_outcome`, resume refusal | executed:foi1b3 | R18-R19, R21-R22, A2, A6 |
| 06 | 71vjbn | Phase 5: trigger UX (escalating SIGINT, SIGTERM) + `aw oc/agy run stop <run-id>` | executed:m0z0ti | R12-R17, A5, A7, A10 |

Why this order: the invariant (Phase 0) must exist before any level can end in it; the flag+poll (Phase 1) must exist before any level can be requested; levels are added cheapest-first (between-turn, then turn-internal, then interrupt); the trigger UX lands last so it wires to all four levels at once instead of being rewritten per level.

Sequencing dependency OUTSIDE this Set: the out-of-repo stop-flag location (spec OQ-03) requires `wtiso` Phase 3+4 (`7p9n2v`, `58ha43`). Phase 1 therefore resolves the flag path through the shared accessor rather than hardcoding a root, and records that the out-of-repo guarantee is fully realized only once `wtiso` lands. This Set does not depend on `wtiso` for correctness on a shared checkout.

## The shared anti-greenwash execution contract (every child inherits this verbatim)

Acceptance for every `V-*` item in this Set is a PASTED command result or an observation of real process/git/filesystem state, never an agent's prose claim:

- A process-reaping claim MUST be proven by a process-table observation (no descendant of the driver alive, nothing reparented to init), not by asserting the code called a kill.
- A lock-release claim MUST be proven by the lock being absent or re-acquirable, not by reading code.
- A ledger-coherence claim MUST be proven by parsing the ledger after the stop.
- A tree-cleanliness claim MUST be proven by `git status --porcelain` output.
- No test may use a wall-clock sleep to define a checkpoint (spec R10).
- No test may spawn a real network-using agent; the child is a controllable local fake.

## Completion criteria (the whole Set is done only when)

- All six children are in `.aw/records/plans/executed/` with every `V-*` carrying real observed evidence.
- Spec c4gd2h acceptance criteria A1-A10 all demonstrably hold, with pasted output.
- CID-1..CID-3 (below) pass.
- `python -m pytest -q` is green.
- Spec `c4gd2h` is moved to `implemented` with cited evidence (not before).
- Backlog `kjzlgw` is `done` via HANDOFF (this plan carries `From-Backlog: kjzlgw` + `Blocks-Release: next`, so closing the item drops no release gate).

## Cross-IPD validation

- CID-1 Exactly ONE cleanup routine exists and all four levels plus crash recovery call it (spec R5, A9). Prove with an AST or import-graph check scoped to `agent_workflows/`, NOT a text grep (the guard test itself contains the symbol).
- CID-2 No child introduced a second stop-flag path or a raw `<repo>/.aw/state` construction (spec OQ-03; the `wtiso` Phase 3 AST guard forbids it).
- CID-3 Both drivers (`oc_runipd.py`, `agy_runipd.py`) expose the same four levels and the same `stop` verb; no level exists in one driver only.

## Deferred / out of scope (with reason)

- Unifying `oc_runipd.py` and `agy_runipd.py` (backlog `dhuape`): children land symmetrically in both, but de-duplication is a separate concern.
- Crash-recovery redesign: consumed from research `ud28vy`, not re-specified (spec non-goal; GUIDING_PRINCIPLES P8 single source of truth).
- Worktree isolation (Set `wtiso`): a sequencing dependency for the flag location, not work this Set performs.
- Pause/resume-mid-turn: explicit spec non-goal. A stopped turn is stopped, not suspended.
- `stop --all` across concurrent runs (spec OQ-02, non-blocking): ship per-run-id first.

## Scope check

- Over-scope: none. The orchestrator writes no product code.
- Under-scope: none. Every spec requirement R1-R23 is claimed by exactly one child and every acceptance criterion A1-A10 by at least one child (see the child table's Spec ids column).

## Required tests / validation

Whole-Set verification (E-01), performed only after all six children are `executed/`:

- Re-run each child's validation commands; confirm the pasted evidence in each child's V-items matches a fresh run.
- Demonstrate spec c4gd2h A1-A10 against the real repo with pasted output.
- Run CID-1..CID-3.
- `python -m pytest -q` green overall.

## Open questions

### OQ-01: Should the `stop` verb also be exposed as a top-level `aw run stop`?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: `runstop-06` implements `aw oc run stop` and `aw agy run stop` per spec R14. A unified `aw run stop` presupposes the runner unification in backlog `dhuape`; deferred to that work rather than pre-building a facade here.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a pasted whole-Set verification record showing, for each spec acceptance criterion A1-A10, the command run and its actual output; a per-child table confirming each child's V-items carry real observed evidence (prose-only evidence fails this item); and pasted output for CID-1, CID-2, CID-3.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (inherited verbatim by every child):

- Open questions: OQ-01 here is resolved; spec OQ-01 and OQ-03 are RESOLVED in c4gd2h. No unresolved question blocks execution.
- Scope fence: touch ONLY the declared `Scope-Paths` of the child being executed. Widening requires a new plan, not an in-place edit.
- Honesty rule (hard MUST): paste the ACTUAL runner output into each `V-*` Observed evidence. Never claim a test passed that was not run.
- Commits: path-scoped only (`git commit -m msg -- <path>`); never `git add -A`/`-a`; never push; never tag or release.
- Lifecycle: run `aw ipd begin <child> --actor <agent/model>` BEFORE executing (fail-closed: no receipt, no execution authority), then `aw ipd finalize` after validation passes. Never hand-move a plan to `executed/`.
- If any validation fails, STOP and report rather than marking the plan executed.
