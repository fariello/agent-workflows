# IPD: Driver self-finalizes: run aw ipd begin before and aw ipd finalize after each verified child turn, with scope reconciliation

- Date: 2026-08-27
- Kind: child
- Concern: The driver executes a child IPD and the agent commits its work, but NOTHING runs `aw ipd begin` or `aw ipd finalize`, so verified children stay `Status: approved` in pending/ and sets never finish (this session's "nothing moved to executed"; we finalized 3 by hand). The gated lifecycle (`aw ipd begin` writes an execution-authority receipt; `aw ipd finalize` validates it, runs pre/post-transition lint, reconciles changed-paths vs Scope-Paths, moves the plan to executed/, path-scoped-commits) already exists (ipd_lifecycle / cli `ipd begin`/`finalize`) - the driver just doesn't call it. This child wires it in. (ctt412 core.)
- Scope: In `oc_runipd.py` (and `agy_runipd.py`), make the driver drive the FULL lifecycle for an execute-action child: (1) run `aw ipd begin <id6> --actor <agent/model>` BEFORE the agent turn (fail-closed: no receipt = no execution authority), so scope + base HEAD are frozen; (2) after the agent turn completes AND the deterministic/verification checks pass, run `aw ipd finalize <id6> --actor ... [--scope-reason/--scope-ack ...]`, performing the two-way scope reconciliation programmatically (the driver knows the plan's Scope-Paths and the actual changed paths, so it can supply the acks/reasons that we did by hand); (3) on finalize success the child's runner status becomes `executed`; on finalize refusal (unresolved scope, failing lint, missing evidence) the child is recorded NOT-executed (substantially-complete/failed-safely) and the set stays unfinished - never fake executed. Do NOT isolate in a worktree yet (child 02) and do NOT change orchestrator handling (already done, 801dd28). Reuse the existing begin/finalize surface; do not fork a second finalize path.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/ipd_lifecycle.py, tests/
- Item-Dependencies: none
- Status: approved
- Set: driverfin
- Order: 1
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: p7peqf
- Approval: 2026-08-28, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-28 approved (aw set): status set to approved
- 2026-08-28 reviewed (/plan-review opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (receipt-path correction, finalize-gate precision, agy parity coverage, mid-execute_item path-move interaction, execution-contract completion). GO - PENDING HUMAN APPROVAL.
- 2026-08-28 to-review (aw set): status set to to-review
- 2026-08-28 reviewed (aw set): status set to reviewed
- 2026-08-28 to-review (aw set): status set to to-review

- 2026-08-28 reviewed (Antigravity): /plan-review passed with revisions; resolved Item-Dependencies to none, populated concrete V evidence, resolved OQ-01, and completed execution gate.
- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Wire the driver to run `aw ipd begin` before and `aw ipd finalize` after each verified execute-action child (with programmatic scope reconciliation), so a passing child lands in executed/ with no manual step and a failing/unreconcilable one is never faked executed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: begin before the turn

- [ ] E-01 In the driver's `execute_item` (both `oc_runipd.py` and `agy_runipd.py`), for a non-review (execute-action) child ONLY, run `aw ipd begin <id6> --actor <agent/model>` BEFORE the `run_opencode`/agent-turn launch and fail closed if it refuses (record the item blocked, do not launch, do not append a running attempt). Reuse the existing begin surface (subprocess to `python -m agent_workflows ipd begin`, mirroring `finalize_orchestrator`/`set_plan_approved`); store nothing new (begin already writes the gitignored `.aw/state/ipd-lifecycle/<id6>.receipt.json` receipt). Skip begin for review-action items.
  - Depends on: none
  - Expected outcome: a child's agent turn only starts after a valid begin receipt exists; a begin refusal blocks the child cleanly (no agent turn, item recorded blocked).
  - Execution state: pending

### Task group 2: finalize after a verified turn

- [ ] E-02 After the agent turn + verification pass, the driver runs `aw ipd finalize <id6> --actor ...`, computing the two-way scope reconciliation programmatically from the plan's Scope-Paths vs the actual changed paths (from the attempt's `ending_status`), supplying `--scope-ack` (declared-but-untouched paths) and `--scope-reason` (out-of-scope changes) as needed. GATE PRECISION: `reconcile_disposition` returns `executed` ONLY when the plan is already in `executed/`; before finalize a verified child is still in `pending/`, so it reports `substantially-complete`, not `executed`. Therefore trigger finalize when `disposition in {"executed", "substantially-complete"}` AND `verification_status == "verified"` (do NOT gate on `disposition == "executed"` alone - it would never fire). On finalize success (`FinalizeResult.exit_code == 0`) the plan is now in `executed/`, so re-resolve and set child status `executed`; on refusal (non-zero exit_code) record substantially-complete/failed-safely, never `executed`. Do NOT force the transition on refusal (mirror `finalize_orchestrator`'s never-force posture).
  - Depends on: E-01
  - Expected outcome: a verified child auto-transitions approved->executed/ with no manual step; an unreconcilable/failing child stays not-executed with a recorded reason.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `aw ipd begin`/`aw ipd finalize` (cli.py; ipd_lifecycle) are the gated lifecycle: begin freezes scope+base HEAD into a gitignored receipt = execution authority; finalize validates it, runs pre/post-transition lint, reconciles changed-vs-Scope-Paths (`--scope-ack` declared-but-untouched, `--scope-reason` out-of-scope), moves plan to executed/, path-scoped-commits.
- The driver already shells `aw ipd set`/`aw set` (set_plan_approved pattern, subprocess to `python -m agent_workflows`); mirror that for begin/finalize.
- The manual salvage this session proved the exact scope-ack shape finalize needs; encode that computation.

## Findings

- The transition machinery all exists; the only new logic is (a) calling begin/finalize at the right points in the driver loop and (b) computing the scope reconciliation the driver already has the data for. No forked finalize path.
- `finalize(...)` (ipd_lifecycle.py:1237) already accepts `scope_reasons`/`scope_acks` dicts and fails closed on a missing reason/ack, returning a `FinalizeResult` with the shared 0/1/2 exit convention; the CLI `ipd finalize` subcommand exposes `--scope-ack`/`--scope-reason` (cli.py). The driver need only marshal the two-way delta into those flags. No new finalize surface.
- INTERACTION to respect (do not break): `reconcile_disposition` (oc_runipd.py:1461-1466) treats plan LOCATION as source of truth - it returns `executed` when `plan_bucket == "executed"` and DOWNGRADES an agent's self-claimed `executed` to `substantially-complete` while the plan is still in `pending/`. Because finalize MOVES the plan to `executed/` mid-`execute_item`, any later `resolve_plan_path`/status handling in that call MUST tolerate the plan now living in `executed/` (the existing `plan_bucket`/`reconcile_interrupted` logic already does). This is why the finalize call happens AFTER `reconcile_disposition` + verification, and why the finalize gate is disposition-in-{executed,substantially-complete} rather than `disposition == "executed"`.
- Both drivers are in Scope-Paths and share a parallel `execute_item`/`set_plan_approved` structure (`agy_runipd.py:1604`, `:392`), so E-01/E-02 and their V-items apply to BOTH; tests cover `test_oc_runipd.py` and `test_agy_runipd_cli.py`.

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

- With a passing child, the driver runs begin then finalize; the plan is in executed/ with Status: executed (assert file location + status). Cover BOTH `test_oc_runipd.py` and `test_agy_runipd_cli.py`.
- A begin refusal blocks the child (no agent turn, recorded blocked).
- A finalize refusal (e.g. out-of-scope change -> non-zero `FinalizeResult.exit_code`) leaves the child NOT executed with a recorded reason; the driver does not stamp executed and does not force the transition.
- Programmatic scope reconciliation supplies the correct `--scope-ack` for declared-but-untouched Scope-Paths and `--scope-reason` for out-of-scope changed paths, derived from the attempt's `ending_status`.
- The finalize gate fires on a verified child that `reconcile_disposition` reports as `substantially-complete` (plan still in pending/ pre-finalize), not only on a literal `executed` disposition.

Validation command: `python -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -q` (paste the actual runner output; do not claim success unrun).

## Spec / documentation sync

- Update the runner docs to state the driver self-finalizes; cross-ref ctt412.

## Open questions

### OQ-01: When does the driver commit the agent's work vs. let finalize do the lifecycle commit?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved. The agent commits its product code changes path-scoped during its execution turn. `aw ipd finalize` separately performs the lifecycle commit covering only the plan movement, plan status metadata, and index manifest.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Tests in `tests/test_oc_runipd.py` AND `tests/test_agy_runipd_cli.py` (both drivers are in Scope-Paths) demonstrating `aw ipd begin` is invoked prior to agent execution (before the `run_opencode`/agent-turn launch in `execute_item`), generating a valid `.aw/state/ipd-lifecycle/<id6>.receipt.json` begin receipt (the gitignored path from `ipd_lifecycle.receipt_path_for`), and that a simulated begin refusal blocks the child cleanly without launching the agent turn (item recorded blocked).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Tests in `tests/test_oc_runipd.py` AND `tests/test_agy_runipd_cli.py` demonstrating that after a verified child turn (gate: disposition in {`executed`, `substantially-complete`} AND `verification_status == "verified"` - see Finding note below), `aw ipd finalize` is executed with programmatic `--scope-ack`/`--scope-reason` arguments computed from Scope-Paths vs the attempt's `ending_status` changed paths, the plan is moved to `.aw/records/plans/executed/` (so `plan_bucket` becomes `executed`), and the child's runner status is updated to `executed`. A companion test asserts a finalize REFUSAL (non-zero `FinalizeResult.exit_code`, e.g. an unreconciled out-of-scope change) leaves the child NOT executed with a recorded reason and does NOT stamp `executed`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

1. Open questions: all RESOLVED (OQ-01 resolved); execution requires explicit human approval.
2. Scope fence: touch ONLY `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/ipd_lifecycle.py` (read/reuse only; do NOT fork a second finalize path), and `tests/` (`test_oc_runipd.py`, `test_agy_runipd_cli.py`). Do NOT change orchestrator handling (done, 801dd28), do NOT add worktree isolation (child 02), do NOT touch `status_set.py`/`cli.py` finalize surfaces. If the work seems to need more, STOP and report.
3. Honesty rule (HARD MUST): when you report tests/validation passed, paste the ACTUAL runner output (`python -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -q`); never claim success you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move on completion: verify all V items with pasted test output, run `aw ipd lint --phase pre-transition`, then finalize via `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` (the gated transition that moves the plan to executed/, sets Status, appends workflow history, and path-scoped-commits). Do NOT mark executed or move the plan unless validation actually passed.
