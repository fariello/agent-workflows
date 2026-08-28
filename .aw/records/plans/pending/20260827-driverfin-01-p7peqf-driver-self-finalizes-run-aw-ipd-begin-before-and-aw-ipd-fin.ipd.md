# IPD: Driver self-finalizes: run aw ipd begin before and aw ipd finalize after each verified child turn, with scope reconciliation

- Date: 2026-08-27
- Kind: child
- Concern: The driver executes a child IPD and the agent commits its work, but NOTHING runs `aw ipd begin` or `aw ipd finalize`, so verified children stay `Status: approved` in pending/ and sets never finish (this session's "nothing moved to executed"; we finalized 3 by hand). The gated lifecycle (`aw ipd begin` writes an execution-authority receipt; `aw ipd finalize` validates it, runs pre/post-transition lint, reconciles changed-paths vs Scope-Paths, moves the plan to executed/, path-scoped-commits) already exists (ipd_lifecycle / cli `ipd begin`/`finalize`) - the driver just doesn't call it. This child wires it in. (ctt412 core.)
- Scope: In `oc_runipd.py` (and `agy_runipd.py`), make the driver drive the FULL lifecycle for an execute-action child: (1) run `aw ipd begin <id6> --actor <agent/model>` BEFORE the agent turn (fail-closed: no receipt = no execution authority), so scope + base HEAD are frozen; (2) after the agent turn completes AND the deterministic/verification checks pass, run `aw ipd finalize <id6> --actor ... [--scope-reason/--scope-ack ...]`, performing the two-way scope reconciliation programmatically (the driver knows the plan's Scope-Paths and the actual changed paths, so it can supply the acks/reasons that we did by hand); (3) on finalize success the child's runner status becomes `executed`; on finalize refusal (unresolved scope, failing lint, missing evidence) the child is recorded NOT-executed (substantially-complete/failed-safely) and the set stays unfinished - never fake executed. Do NOT isolate in a worktree yet (child 02) and do NOT change orchestrator handling (already done, 801dd28). Reuse the existing begin/finalize surface; do not fork a second finalize path.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/ipd_lifecycle.py, tests/
- Item-Dependencies: unresolved
- Status: draft
- Set: driverfin
- Order: 1
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: p7peqf

## Workflow history

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Wire the driver to run `aw ipd begin` before and `aw ipd finalize` after each verified execute-action child (with programmatic scope reconciliation), so a passing child lands in executed/ with no manual step and a failing/unreconcilable one is never faked executed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: begin before the turn

- [ ] E-01 In the driver's per-child execute path (before launching the agent), run `aw ipd begin <id6> --actor <agent/model>` and fail closed if it refuses (record blocked, do not launch). Reuse the existing begin surface; store nothing new (begin already writes the gitignored receipt).
  - Depends on: none
  - Expected outcome: a child's agent turn only starts after a valid begin receipt exists; a begin refusal blocks the child cleanly.
  - Execution state: pending

### Task group 2: finalize after a verified turn

- [ ] E-02 After the agent turn + verification pass, the driver runs `aw ipd finalize <id6> --actor ...`, computing the two-way scope reconciliation programmatically from the plan's Scope-Paths vs the actual changed paths (supply `--scope-ack`/`--scope-reason` as needed). On success -> child status `executed`; on refusal -> record substantially-complete/failed-safely, never `executed`.
  - Depends on: E-01
  - Expected outcome: a verified child auto-transitions approved->executed/ with no manual step; an unreconcilable/failing child stays not-executed with a recorded reason.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `aw ipd begin`/`aw ipd finalize` (cli.py; ipd_lifecycle) are the gated lifecycle: begin freezes scope+base HEAD into a gitignored receipt = execution authority; finalize validates it, runs pre/post-transition lint, reconciles changed-vs-Scope-Paths (`--scope-ack` declared-but-untouched, `--scope-reason` out-of-scope), moves plan to executed/, path-scoped-commits.
- The driver already shells `aw ipd set`/`aw set` (set_plan_approved pattern, subprocess to `python -m agent_workflows`); mirror that for begin/finalize.
- The manual salvage this session proved the exact scope-ack shape finalize needs; encode that computation.

## Findings

The transition machinery all exists; the only new logic is (a) calling begin/finalize at the right points in the driver loop and (b) computing the scope reconciliation the driver already has the data for. No forked finalize path.

## Proposed changes (ordered, validatable)

1. `oc_runipd.py`/`agy_runipd.py`: `aw ipd begin` before the execute turn (fail-closed).
2. Same: `aw ipd finalize` after a verified turn, with programmatic scope-ack/reason.
3. `tests/`: begin-refusal blocks; verified turn finalizes to executed/; unreconcilable turn stays not-executed.

## Deferred / out of scope (with reason)

- Worktree isolation: child 02 (this child runs in the main tree; isolation wraps it next).
- Merge-back conflict handling / dirty-tree guard: child 03.
- Orchestrator handling: already done (801dd28).

## Scope check

- Over-scope: none.
- Under-scope: none (begin + finalize + scope reconciliation is the complete self-finalize deliverable).

## Required tests / validation

- With a passing child, the driver runs begin then finalize; the plan is in executed/ with Status: executed (assert file location + status).
- A begin refusal blocks the child (no agent turn, recorded blocked).
- A finalize refusal (e.g. out-of-scope change) leaves the child NOT executed with a recorded reason; the driver does not stamp executed.
- Programmatic scope reconciliation supplies the correct acks for declared-but-untouched paths.

## Spec / documentation sync

- Update the runner docs to state the driver self-finalizes; cross-ref ctt412.

## Open questions

### OQ-01: When does the driver commit the agent's work vs. let finalize do the lifecycle commit?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: The agent commits its own product changes path-scoped during the turn; `aw ipd finalize` makes the lifecycle commit (status/move/index). Confirm no double-commit and that finalize's path-scoped commit covers only the plan-lifecycle files. Reconcile with the selfcommit git_commit_helper if the driver later commits on the agent's behalf.

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
