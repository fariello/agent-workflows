# IPD: Fail-closed dirty-tree/integration guard and merge-back conflict handling so a run never contaminates or half-finishes

- Date: 2026-08-27
- Kind: child
- Concern: Even with self-finalize (01) and worktree isolation (02), a run can still HALF-FINISH or CONTAMINATE at the boundaries: the main tree may be dirty with un-owned changes when integration starts, or a verified branch may CONFLICT on merge-back (e.g. ipddeps+xprio both edited ipd_schema.py). Without a guard, integration would either fail silently, leave a partial merge, or clobber. This child adds the fail-closed guard + merge-back conflict handling so a run NEVER contaminates the main tree or claims a set finished when it didn't.
- Scope: (1) DIRTY-TREE GUARD: before running child-02's integration gate for a verified branch, assert the main tree has no un-owned dirty paths overlapping the incoming change; if it does, REFUSE (record `integration-blocked`, leave the verified branch + worktree preserved, continue independent items) rather than integrating over a dirty base. (2) CONFLICT HANDLING ON THE GATE RESULT: layer on child-02's `execute_merge_and_revalidate_gate` result - a non-passing `IntegrationGateResult` (conflict/stale-base/combined-red/scope) leaves main untouched (diff-based gate = no partial merge; abort any real merge left in the apply step), records `merge-conflict` with the failing paths + preserved branch, and marks the IPD not-integrated (NOT executed on main); never conflict markers or a partial merge. Do NOT fork a separate live-merge path. (3) SET COMPLETION HONESTY: a set is "finished" only when all children integrated cleanly; a child blocked on dirty/conflict leaves its orchestrator unfinalized (consistent with 801dd28's all-children-executed rule; no new code, just do not falsely stamp executed). This is the safety layer over 01+02; it does NOT auto-resolve conflicts (a human/serial ordering does). The optional cross-set warn/serialize is DEFERRED (no committed overlap data source; see Deferred).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/worktree_lease.py, agent_workflows/render_stream.py, tests/
- Item-Dependencies: executed:emus4n
- Status: reviewed
- Set: driverfin
- Order: 3
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 7kbtkw

## Workflow history
- 2026-08-28 reviewed (/plan-review opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed (re-expressed E-02 to consume child-02's `execute_merge_and_revalidate_gate` result instead of forking a live `git merge --abort` path, corrected the overstated committed cross-set-overlap-analysis claim, added `render_stream.py` to Scope-Paths for the two new `TERMINAL_STATES` colors, deferred the optional warn/serialize with a stated no-data-source reason, added agy parity coverage, completed execution contract). GO - PENDING HUMAN APPROVAL (gated on child-02 emus4n executed).
- 2026-08-28 to-review (aw set): status set to to-review
- 2026-08-28 reviewed (aw set): status set to reviewed
- 2026-08-28 to-review (aw set): status set to to-review

- 2026-08-28 reviewed (Antigravity): /plan-review passed with revisions; resolved Item-Dependencies to executed:emus4n, populated concrete V evidence, resolved OQ-01, and completed execution gate.
- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add the fail-closed guard + merge-back conflict handling over self-finalize (01) and isolation (02): refuse to integrate into a dirty main base, abort-and-record on a merge conflict (never leave a partial merge or contamination), and keep set-completion honest.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: dirty-tree integration guard

- [ ] E-01 In `execute_item` (both `oc_runipd.py` and `agy_runipd.py`), BEFORE invoking child-02's integration gate for a verified branch, inspect the MAIN tree via `git status --short` and assert it has no un-owned dirty paths overlapping the incoming change's `changed_files`; if it does, REFUSE (set item status `integration-blocked` added to `TERMINAL_STATES`, emit an `integration-blocked` event, preserve the verified branch + worktree, continue independent items). Never run the integration gate against a contaminated base.
  - Depends on: none
  - Expected outcome: with a dirty overlapping main tree, integration is refused cleanly (status `integration-blocked`) and the verified branch/worktree are preserved; main is untouched.
  - Execution state: pending

### Task group 2: merge-back conflict handling + completion honesty

- [ ] E-02 Handle a NON-passing integration-gate result from child-02: when `execute_merge_and_revalidate_gate` returns an `IntegrationGateResult` with `passed == False` (`INTEGRATION_FAILED_CONFLICT`/`INTEGRATION_FAILED_STALE_BASE`/`INTEGRATION_FAILED_COMBINED_RED`/scope violation), leave main UNTOUCHED (the gate is diff-based, so there is no partial merge to abort - if a real `git merge` was performed in the apply step and left markers/index state, `git merge --abort` it), set item status `merge-conflict` (added to `TERMINAL_STATES`) recording the failing `IntegrationFinding` messages/paths + the preserved `aw/lane/<id6>` branch, and mark the IPD not-integrated (NOT executed on main); never leave conflict markers/partial merge. A set is finished only when all children integrated cleanly (a conflicted/blocked child leaves its orchestrator unfinalized, per 801dd28 - no new code needed, just do not falsely stamp executed).
  - Depends on: E-01
  - Expected outcome: a non-passing gate result leaves main pristine (no markers), the child is recorded `merge-conflict` with the gate's paths + preserved branch, and its set is NOT reported finished.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The runner already records terminal per-item states in `TERMINAL_STATES` (`oc_runipd.py:67-77`: blocked/failed-safely/dependency-blocked/partial/...) + events.jsonl; add `integration-blocked`/`merge-conflict` to `TERMINAL_STATES` in the same shape. Their DISPLAY colors live in `_STATUS_COLOR` (`render_stream.py:47`, mirrored in `agy_runipd.py:84`), which `oc_runipd.py` imports (`:43`) and falls back to yellow for unknown states (`oc_runipd.py:1697`). Adding an explicit color requires editing `render_stream.py` (added to Scope-Paths); a state with no explicit color still renders (default yellow), so an explicit entry is a nicety, not a correctness requirement.
- 801dd28 (verified: "fix(oc-run): do not agent-execute orchestrators; finalize iff all children executed"): orchestrator finalizes iff ALL children executed - a not-integrated child keeps the set open automatically (`orchestrator_children_all_executed` helper, `oc_runipd.py:262`); this child just must not falsely mark a conflicted child executed.
- INTEGRATION MECHANISM (reconciled with child-02): child-02 integrates by REUSING `orchestrate_isolation.execute_merge_and_revalidate_gate`, which is DIFF/combined-diff based - it detects conflict via disjoint-ownership overlap + conflict markers and returns an `IntegrationGateResult` (`INTEGRATION_FAILED_CONFLICT`/`INTEGRATION_FAILED_STALE_BASE`/`INTEGRATION_FAILED_COMBINED_RED`) WITHOUT leaving a partial merge. This child therefore layers its fail-closed handling on the GATE RESULT, it does NOT introduce a separate live `git merge`/`git merge --abort` path (that would fork the integration mechanism the set committed to in child-02). The dirty-tree pre-check (E-01) inspects main's working tree via `git status` before the gate runs and is genuinely net-new.
- Cross-set overlap data source: the ipddeps+xprio overlap on `ipd_schema.py`/`status_set.py` is documented in the INDIVIDUAL plans' Step-0 notes (`xprio-00:67`, `ipddeps-00:68`), NOT in a single consolidated committed analysis artifact. The optional warn/serialize (see Deferred) has no dedicated real data source today, which is why it is deferred, not built here.

## Findings

- Isolation converts silent clobbering into an explicit, gate-detected integration failure; this child ensures that failure fails CLOSED (leave main pristine, record with paths, preserve branch/worktree) instead of leaving a mess, and keeps "set finished" honest. It does not auto-resolve conflicts and does not fork the integration mechanism - it consumes child-02's `IntegrationGateResult`.
- The genuinely net-new code here is the DIRTY-TREE pre-check (E-01) and the two new `TERMINAL_STATES`; the conflict path (E-02) is mostly branching on the existing gate's `passed`/`status`/`findings`, and completion honesty already falls out of 801dd28.

## Proposed changes (ordered, validatable)

1. `oc_runipd.py`/`agy_runipd.py`: dirty-base guard before invoking the integration gate; add `integration-blocked`/`merge-conflict` to `TERMINAL_STATES`.
2. Branch on child-02's `IntegrationGateResult`: non-passing -> record `merge-conflict` with the gate's failing paths, leave main untouched, preserve branch/worktree; passing -> integrate (child-02's job).
3. `render_stream.py`: optional `_STATUS_COLOR` entries for the two new states (default-yellow fallback otherwise).
4. `tests/` (`test_oc_runipd.py` AND `test_agy_runipd_cli.py`): dirty base refused (`integration-blocked`); non-passing gate result leaves main pristine (no markers) and records `merge-conflict` with paths + preserved branch; set with a conflicted child not reported finished.

## Deferred / out of scope (with reason)

- Automatic conflict RESOLUTION: out (human/serial ordering resolves genuine conflicts; the driver only detects + fails closed).
- OPTIONAL pre-run warn/serialize of known-overlapping sets: DEFERRED (no E/V item here). There is no single consolidated committed cross-set overlap analysis to drive it (only per-plan Step-0 notes); building a real cross-set Scope-Paths overlap detector is its own concern. This child delivers only the dirty-tree guard + gate-result conflict handling + completion honesty.
- Self-finalize (01) and isolation (02): dependencies.

## Scope check

- Over-scope: none.
- Under-scope: none (guard + conflict handling + completion honesty is this child's deliverable).

## Required tests / validation

- Integration into a dirty overlapping main is refused (`integration-blocked`); verified branch/worktree preserved; main untouched. Cover BOTH `test_oc_runipd.py` and `test_agy_runipd_cli.py`.
- A non-passing integration-gate result leaves main with NO conflict markers/partial merge; the item records `merge-conflict` with the gate's paths + preserved branch.
- A set with a conflicted/blocked child is NOT reported finished; its orchestrator stays unfinalized.

Validation command: `python -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -q` (paste the actual runner output; do not claim success unrun).

## Spec / documentation sync

- Document the fail-closed integration behavior + how to resolve a recorded merge-conflict (the preserved branch); cross-ref the cross-set overlap analysis.

## Open questions

### OQ-01: Should the driver auto-serialize known-overlapping sets, or only warn?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved. The driver warns on known Scope-Paths overlaps and strictly fails closed (aborts merge, preserves worktree branch, records merge-conflict) upon detecting a live integration conflict.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Tests in `tests/test_oc_runipd.py` AND `tests/test_agy_runipd_cli.py` proving that if the main repository has unstaged or untracked changes overlapping an incoming branch's `changed_files`, the integration gate is NOT invoked, the item status is `integration-blocked`, an `integration-blocked` event is emitted, and the main working tree remains unmodified with the verified branch/worktree preserved.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Tests in `tests/test_oc_runipd.py` AND `tests/test_agy_runipd_cli.py` asserting that when `execute_merge_and_revalidate_gate` returns a non-passing `IntegrationGateResult` (e.g. `INTEGRATION_FAILED_CONFLICT`), main is left with NO conflict markers/partial merge, the item status is `merge-conflict` recording the gate's failing paths + preserved `aw/lane/<id6>` branch, the event is recorded in `events.jsonl`, and the orchestrator plan remains unfinalized (set not reported finished).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

1. Open questions: OQ-01 RESOLVED; execution requires explicit human approval AND requires child-02 (`emus4n`) executed first (`Item-Dependencies: executed:emus4n`).
2. Scope fence: touch ONLY `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/worktree_lease.py`, `agent_workflows/render_stream.py` (only the `_STATUS_COLOR` map for the two new states), and `tests/` (`test_oc_runipd.py`, `test_agy_runipd_cli.py`). CONSUME child-02's `execute_merge_and_revalidate_gate` result; do NOT fork a live-merge path and do NOT edit `orchestrate_isolation.py`. Do NOT build the optional cross-set warn/serialize or any automatic conflict RESOLUTION. If the work seems to need more, STOP and report.
3. Honesty rule (HARD MUST): when you report tests/validation passed, paste the ACTUAL runner output (`python -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -q`); never claim success you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move on completion: verify all V items with pasted test output, run `aw ipd lint --phase pre-transition`, then finalize via `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT mark executed or move the plan unless validation actually passed.
