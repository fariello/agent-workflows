# IPD: Fail-closed dirty-tree/integration guard and merge-back conflict handling so a run never contaminates or half-finishes

- Date: 2026-08-27
- Kind: child
- Concern: Even with self-finalize (01) and worktree isolation (02), a run can still HALF-FINISH or CONTAMINATE at the boundaries: the main tree may be dirty with un-owned changes when integration starts, or a verified branch may CONFLICT on merge-back (e.g. ipddeps+xprio both edited ipd_schema.py). Without a guard, integration would either fail silently, leave a partial merge, or clobber. This child adds the fail-closed guard + merge-back conflict handling so a run NEVER contaminates the main tree or claims a set finished when it didn't.
- Scope: (1) DIRTY-TREE GUARD: before integrating a verified branch to main (child 02), assert the main tree has no un-owned dirty paths overlapping the incoming change; if it does, REFUSE to integrate (record integration-blocked, leave the verified branch intact + the worktree preserved, continue independent items) rather than merging into a dirty base. (2) MERGE-BACK CONFLICT HANDLING: attempt the integration; on a genuine conflict, ABORT the merge (`git merge --abort`), leave main untouched, record `merge-conflict` with the conflicting paths + the preserved branch, and mark the IPD not-integrated (NOT executed on main) - never leave conflict markers or a partial merge. (3) SET COMPLETION HONESTY: a set is only "finished" when all children integrated cleanly; a child blocked on dirty/conflict leaves its orchestrator unfinalized (consistent with 801dd28's all-children-executed rule). (4) Optional: use the cross-set Scope-Paths overlap to WARN (or serialize) known-conflicting sets before they run. This is the safety layer over 01+02; it does NOT auto-resolve conflicts (a human/serial ordering does).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/worktree_lease.py, tests/
- Item-Dependencies: unresolved
- Status: draft
- Set: driverfin
- Order: 3
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 7kbtkw

## Workflow history

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add the fail-closed guard + merge-back conflict handling over self-finalize (01) and isolation (02): refuse to integrate into a dirty main base, abort-and-record on a merge conflict (never leave a partial merge or contamination), and keep set-completion honest.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: dirty-tree integration guard

- [ ] E-01 Before integrating a verified branch to main, assert main has no un-owned dirty paths overlapping the incoming change; if it does, REFUSE (record integration-blocked, preserve the verified branch + worktree, continue independent items). Never merge into a contaminated base.
  - Depends on: none
  - Expected outcome: with a dirty overlapping main tree, integration is refused cleanly and the verified branch is preserved; main is untouched.
  - Execution state: pending

### Task group 2: merge-back conflict handling + completion honesty

- [ ] E-02 On integration, attempt the merge; on genuine conflict, `git merge --abort`, leave main untouched, record `merge-conflict` with conflicting paths + preserved branch, mark the IPD not-integrated (not executed on main); never leave conflict markers/partial merge. A set is finished only when all children integrated cleanly (a conflicted/blocked child leaves its orchestrator unfinalized, per 801dd28).
  - Depends on: E-01
  - Expected outcome: a conflicting branch aborts cleanly (main pristine, no markers), is recorded with paths + preserved branch, and its set is NOT reported finished.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The runner already records terminal per-item states (blocked/failed-safely/dependency-blocked) + events.jsonl; add integration-blocked/merge-conflict in the same shape.
- 801dd28: orchestrator finalizes iff ALL children executed - a not-integrated child keeps the set open automatically; this child just must not falsely mark a conflicted child executed.
- The committed cross-set Scope-Paths analysis (orchestrator notes) identifies known-overlapping sets (ipddeps+xprio: ipd_schema.py/status_set.py) usable for the optional pre-run warn/serialize.

## Findings

Isolation converts silent clobbering into an explicit merge conflict; this child ensures that conflict fails CLOSED (abort, record, preserve) instead of leaving a mess, and keeps "set finished" honest. It does not auto-resolve conflicts.

## Proposed changes (ordered, validatable)

1. `oc_runipd.py`/`agy_runipd.py`: dirty-base guard before integrate.
2. Merge attempt + abort-on-conflict + record `merge-conflict`/`integration-blocked`; preserve branch/worktree.
3. Optional: pre-run warn/serialize for known-overlapping sets (from Scope-Paths overlap).
4. `tests/`: dirty base refused; conflicting branch aborts clean (main pristine); set with a conflicted child not reported finished.

## Deferred / out of scope (with reason)

- Automatic conflict RESOLUTION: out (human/serial ordering resolves genuine conflicts; the driver only detects + fails closed).
- Self-finalize (01) and isolation (02): dependencies.

## Scope check

- Over-scope: none.
- Under-scope: none (guard + conflict handling + completion honesty is this child's deliverable).

## Required tests / validation

- Integration into a dirty overlapping main is refused; verified branch preserved; main untouched.
- A conflicting merge-back aborts (`git merge --abort`), main has NO conflict markers/partial merge, and the event records the conflicting paths + preserved branch.
- A set with a conflicted/blocked child is NOT reported finished; its orchestrator stays unfinalized.

## Spec / documentation sync

- Document the fail-closed integration behavior + how to resolve a recorded merge-conflict (the preserved branch); cross-ref the cross-set overlap analysis.

## Open questions

### OQ-01: Should the driver auto-serialize known-overlapping sets, or only warn?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Detect-and-warn (or fail-closed at merge) is the safe default; auto-serializing overlapping sets using the Scope-Paths analysis is a nice-to-have that could prevent conflicts before they happen. Default warn/fail-closed; auto-serialize is optional/future.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
