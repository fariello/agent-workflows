# IPD: aw oc/agy run: self-finalize each verified IPD and isolate each run in its own worktree (finished sets, safe parallel)

- Date: 2026-08-27
- Kind: orchestrator
- Concern: `aw oc/agy run` leaves work UNFINISHED and CONTAMINATES the tree, so a batch of IPDs reliably ends with committed-but-approved children, blocked orchestrators, and a dirty main checkout (observed repeatedly 2026-08-27). Two root defects: (1) the driver never runs `aw ipd begin`/`aw ipd finalize` - the agent executes + commits, but nothing performs the terminal `approved -> executed` transition, so children stay `approved` and sets never finish (backlog ctt412, blocks 2.0.0); (2) every run edits the ONE main working tree with NO isolation, so concurrent runs (and even a serial run inheriting a prior run's uncommitted leftovers) clobber each other's files and `aw ipd finalize` refuses on foreign dirty paths. The `worktree_lease` infra (allocate_worktree/teardown_worktree/LeaseTable/allocate_session/assert_worker_scope) already exists but the driver does not use it. Graduated from backlog ctt412; inherits its `Blocks-Release: next`.
- Scope: Make `aw oc/agy run` produce FINISHED sets and be safe to run in parallel, by (a) SELF-FINALIZING each verified child (driver runs `aw ipd begin` before the agent turn and `aw ipd finalize` after, with the two-way scope reconciliation) and (b) ISOLATING each IPD's execution in its own git worktree/branch (via `worktree_lease`), integrating the verified branch back to main, with a fail-closed guard so a run never contaminates the main tree or half-finishes. Three children: 01 self-finalize (the ctt412 core); 02 per-run worktree isolation + merge-back; 03 the fail-closed dirty-tree/integration guard + merge-back conflict handling. Orchestrator-execution is ALREADY fixed (commit 801dd28: the runner no longer agent-executes Kind: orchestrator IPDs and auto-finalizes them iff all children executed) - this set builds on that. EXPLICITLY OUT: the graceful-quit stop protocol (backlog kjzlgw) and the uninformative-blocked-output cosmetic fix are separate.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/worktree_lease.py, agent_workflows/ipd_lifecycle.py, tests/
- Item-Dependencies: unresolved
- Status: draft
- From-Backlog: ctt412
- Blocks-Release: next
- Set: driverfin
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: yt93ir

## Workflow history
- 2026-08-28 draft (aw set): status set to draft

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Make `aw oc/agy run` reliably produce FINISHED sets and be safe to run in parallel: self-finalize each verified child (begin+finalize) and isolate each IPD's execution in its own git worktree, integrating verified branches back to main behind a fail-closed guard. Graduated from ctt412.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO code; the children carry the work. Its only step is the whole-Set integration check. (Per commit 801dd28, the runner will administratively finalize THIS orchestrator once all children are executed - no agent turn.)

### Task group 1: whole-Set verification

- [ ] E-01 After children 01-03 execute, confirm a driven `aw oc run` of a multi-IPD set: (a) runs each child in its own worktree, (b) finalizes each verified child to executed/ automatically, (c) leaves the main tree clean throughout, (d) integrates verified branches to main (or reports a merge conflict without contaminating), and (e) a whole set ends with every child + orchestrator executed and NO uncommitted leftovers. Full suite green.
  - Depends on: none
  - Expected outcome: an end-to-end driven set finishes with zero manual begin/finalize and a clean tree.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (id6) | What it does | Depends on |
|---|---|---|---|
| 01 | p7peqf | Driver self-finalizes: `aw ipd begin` before + `aw ipd finalize` after each verified child, with scope reconciliation | none |
| 02 | emus4n | Per-run worktree isolation: execute each IPD in its own worktree via `worktree_lease`; integrate verified branch to main | 01 |
| 03 | 7kbtkw | Fail-closed dirty-tree/integration guard + merge-back conflict handling (never contaminate or half-finish) | 02 |

Order 01 -> 02 -> 03 (finalize must work before isolation wraps it; the guard hardens both). Orchestrator verifies last (auto-finalized by the runner per 801dd28).

## Completion criteria (the whole Set is done only when)

- The driver runs `aw ipd begin` before and `aw ipd finalize` after each verified child, so a child that passes lands in executed/ with no manual step (01).
- Each IPD executes in its own git worktree/branch (via worktree_lease), and its verified commits integrate back to main; the main tree is untouched during the agent turn (02).
- The driver fails closed rather than contaminating: it refuses to integrate/advance on an un-owned dirty state or an unresolved merge conflict, records it, and moves to independent work (03).
- A driven multi-IPD set ends with every child + orchestrator executed and a clean tree; full suite green.

## Cross-IPD validation

- Self-finalize (01) is the transition; isolation (02) wraps it; the guard (03) protects both - one coherent pipeline, no duplicated finalize path.
- Reuses the EXISTING `worktree_lease` (allocate/teardown/lease/session) and `aw ipd begin`/`finalize` - no forked worktree or finalize logic.
- Builds on 801dd28 (orchestrators already not agent-executed); this set does not re-touch that.

## Deferred / out of scope (with reason)

- Graceful-quit stop protocol (backlog kjzlgw): separate; about interrupting a run cleanly, not finishing sets.
- Uninformative blocked-output (cosmetic): separate.
- Merge-back POLICY for shared-file sets that legitimately conflict (e.g. ipddeps+xprio both editing ipd_schema.py): child 03 handles conflict DETECTION + fail-closed; automatic conflict RESOLUTION is out (a human/serial ordering resolves genuine conflicts).

## Scope check

- Over-scope: none (graceful-quit + output deferred).
- Under-scope: none (finalize + isolation + guard is the complete 'finished sets, safe parallel' deliverable).

## Required tests / validation

Aggregate of children: self-finalize drives approved->executed with scope reconciliation (01); an IPD runs in an isolated worktree and integrates back, main tree untouched mid-turn (02); the guard fails closed on dirty/conflict without contaminating, and an end-to-end driven set finishes clean (03). Plus the orchestrator's whole-set end-to-end check.

## Open questions

### OQ-01: For shared-file sets that genuinely conflict at merge-back (ipddeps+xprio both edit ipd_schema.py), does the driver serialize them or surface a conflict?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Child 03 detects the conflict and fails closed (records it, continues independent work) rather than auto-resolving. Whether the driver ALSO auto-serializes known-overlapping sets (using the cross-set Scope-Paths analysis) is a nice-to-have; default is detect-and-defer, human/serial ordering resolves. Decide in child 03.

### OQ-02: Worktree state (.aw/records/runs/, begin receipts) - does it live in the worktree or the main repo?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Run ledger + begin receipts are per-run durable state; likely anchored to the main repo's `.aw/` (gitignored) keyed by run-id, not duplicated per worktree. Confirm in child 02 so finalize can find the receipt regardless of which worktree executed.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
