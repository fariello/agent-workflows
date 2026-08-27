# IPD: Phase 3: event-derived lifecycle state and declared file scope

- Date: 2026-08-25
- Kind: child
- Concern: Findings bu9yij Phase 3 + section 7.3/7.5: a freely-editable `- Status:` field is trivially hand-editable, and file authorship in a shared dirty worktree cannot be reliably attributed. Lifecycle state should be DERIVED from validated events, and file scope should be DECLARED and compared to the actual index/diff, rather than inferred from timestamps or narrative.
- Scope: (1) Event-derived lifecycle state: represent transitions as validated events (e.g. IPD_CREATED -> WORK_STARTED -> TEST_EVIDENCE_RECORDED -> REVIEWED -> FINALIZED) with the visible status DERIVED from versioned events; the transition function rejects missing predecessors, stale tree ids, invalid actors, malformed evidence, and unauthorized terminal transitions. For ordinary repository assurance, versioned local events + CI validation suffice (authority countersigning is the deferred external-signing set). (2) Declared file scope: record an explicit task scope (the IPD `Scope-Paths` already exists) and COMPARE it to the git index + final diff; use isolated worktrees for concurrency; do NOT infer authorship from timestamps/narrative. This child integrates with the phase-1 engine (transition validity + scope drift are engine rules) and the phase-2 commands (which emit the events / enforce scope). Honest limit: local events are forgeable by a privileged local agent; authenticity depends on who can write/sign events (findings 5.4/7.3) - non-forgeable provenance is the deferred set.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/check_engine.py, agent_workflows/ipd_schema.py, agent_workflows/record_history.py, tests/
- Status: approved
- Set: agentadhere
- Order: 4
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: wqj1ne
- Approval: 2026-08-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 approved (aw set): status set to approved

- 2026-08-27 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001 gate execution contract added, PR-002 V-01/V-02 concrete falsifiable evidence, PR-003 E-02 no-fork reuse of finalize scope helpers named, PR-004 backward-compat characterization (V-01d) + anti-regression MUST, PR-005 OQ-01 resolved (run-alongside), PR-006 Status draft->reviewed
- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Derive lifecycle status from validated versioned events (rejecting invalid/out-of-order/unauthorized transitions) and enforce declared file scope by comparing the IPD's Scope-Paths to the actual git index/diff, so status and authorship are not freely editable or inferred.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: event-derived state

- [ ] E-01 Represent lifecycle transitions as validated versioned events built ON the existing `record_history` sidecar (`.aw/records/history.jsonl`, record_history.py:30,41 - do NOT introduce a parallel event log), with the visible status DERIVED from the versioned event stream. The transition function rejects missing predecessors, stale tree ids, invalid actors, malformed evidence, and unauthorized terminal transitions. Integrate transition validity as phase-1 `check_engine` rules (reuse the existing rule/finding shape from child uisjns; do not fork). Run derivation ALONGSIDE the existing `- Status:` read (backward-compatible; no big-bang migration) per OQ-01.
  - Depends on: none
  - Expected outcome: an invalid/out-of-order/unauthorized transition is rejected by the transition function (engine rule); a valid event sequence derives the expected visible status; existing `- Status:` reads still work unchanged.
  - Execution state: pending

### Task group 2: declared scope enforcement

- [ ] E-02 Surface declared-file-scope drift as a phase-1 `check_engine` rule by REUSING the existing finalize scope-comparison helpers in `ipd_lifecycle.py` - `_paths_changed_by_this_execution` (ipd_lifecycle.py:571), `_scope_match` (:616), and `_frozen_scope_paths` (:307) - which already compare changed paths against a plan's frozen `Scope-Paths` (the module docstring names Order 04 as the enforcer, ipd_lifecycle.py:21). Do NOT fork a second scope-comparison path; lift/share the existing logic. Rely on isolated worktrees for concurrency; do NOT infer authorship from timestamps/narrative.
  - Depends on: E-01
  - Expected outcome: a change touching paths outside declared `Scope-Paths` is flagged by the engine rule (via the shared finalize helpers); an in-scope change is clean; no duplicated scope-comparison logic is introduced (grep/import proof).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `Scope-Paths` already exists in the IPD schema (ipd_schema.py `META_SCOPE_PATHS`, with a `grandfathered` sentinel) and is checked at the ready-to-execute gate - extend it to a diff comparison, do not invent a new field.
- `record_history.py` already appends versioned history to `.aw/records/history.jsonl`; event derivation should build on this sidecar, not a parallel log.
- `ipd_lifecycle.py` already computes changed paths since a frozen base (diff --name-only) for finalize - reuse for scope comparison.

## Findings

The building blocks (Scope-Paths, history sidecar, finalize diff) exist; Phase 3 makes status a DERIVED function of validated events and turns Scope-Paths into an enforced diff comparison. Authenticity remains local (forgeable); non-forgeable signing is deferred.

## Proposed changes (ordered, validatable)

1. Event model + derived-status function (built on `record_history`).
2. Transition-validity + scope-drift rules in the phase-1 engine.
3. `tests/`: invalid-transition rejection + scope-drift detection.

## Deferred / out of scope (with reason)

- External countersigning of protected events (authority assurance): deferred external-signing set.
- Migrating all existing status fields to PURE derivation (derived-only, dropping the backward-compatible `- Status:` read): deferred to a later separately-tracked step once derivation is stable (OQ-01); this phase runs derivation alongside the existing field.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- Invalid transitions (missing predecessor, stale tree id, invalid actor, malformed evidence, unauthorized terminal) are each rejected.
- A valid event sequence derives the correct visible status.
- A change outside declared `Scope-Paths` is flagged; in-scope is clean.

## Spec / documentation sync

- Document the event model + derived status and the scope-comparison rule (spec/docs); reconcile with the existing lifecycle docs.

## Open questions

### OQ-01: Migrate existing plans to event-derived status, or run derivation alongside the current field?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED - run derivation ALONGSIDE a backward-compatible `- Status:` read first (no big-bang migration); the existing field remains authoritative for reads this phase, with derivation validating/cross-checking it. Tightening to derived-only is a later, separately-tracked step once stable (recorded in Deferred/out-of-scope). E-01 and V-01(d) encode the backward-compatible-alongside requirement and its characterization test, so this is settled for authoring, not left to implementer discretion.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: (a) EACH invalid transition is rejected with its specific reason - paste test output for: missing predecessor, stale tree id, invalid actor, malformed evidence, and unauthorized terminal transition (five distinct assertions, not one blanket "rejected"); (b) a VALID ordered event sequence derives the expected visible status (paste the derived status for a known sequence); (c) events are appended to the existing `.aw/records/history.jsonl` sidecar via `record_history.append` and NOT to a parallel log (paste the import/grep and a sample line); (d) BACKWARD COMPATIBILITY (anti-regression, rubric D): existing `- Status:` reads and the callers that depend on them (`aw set`/`aw ipd set`, `finalize`, the installed hooks) still work unchanged - a characterization test pins the pre-change status-read behavior and confirms it is preserved when derivation runs alongside (paste the test run).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: (a) a change touching a path OUTSIDE the plan's declared `Scope-Paths` is flagged by the phase-1 engine rule with the correct rule id + recovery command (paste the `aw check` finding); (b) an in-scope-only change is CLEAN (paste output showing zero scope-drift findings); (c) NO-FORK proof: the engine rule reuses the existing `ipd_lifecycle` helpers (`_paths_changed_by_this_execution`/`_scope_match`/`_frozen_scope_paths`) rather than defining a second scope-comparison implementation - paste the import/grep showing the shared call and the absence of a duplicated comparator; (d) the `grandfathered` sentinel is honored (a `Scope-Paths: grandfathered` plan is advisory-satisfied, not hard-flagged) - paste output.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: two E-items, each a single focused pass with its own verification surface - E-01 (event-derived lifecycle state on the existing history sidecar + transition-validity engine rules) and E-02 (declared-scope-drift engine rule reusing the finalize scope helpers). Both center on the same phase-1 engine + `ipd_lifecycle` reuse, so they form one cohesive child rather than two.

### Open questions resolved

- OQ-01 (migrate existing plans to event-derived status vs. run derivation alongside): RESOLVED - run derivation ALONGSIDE a backward-compatible `- Status:` read this phase (the existing field stays authoritative for reads; derivation validates/cross-checks). Tighten to derived-only later (tracked in Deferred/out-of-scope). Encoded in E-01 + V-01(d).

### Execution contract

- Scope fence: touch ONLY the files in `Scope-Paths` - `agent_workflows/ipd_lifecycle.py`, `agent_workflows/check_engine.py`, `agent_workflows/ipd_schema.py`, `agent_workflows/record_history.py`, and `tests/`. REUSE the existing `record_history` sidecar (E-01) and the finalize scope helpers `_paths_changed_by_this_execution`/`_scope_match`/`_frozen_scope_paths` (E-02); do NOT fork a parallel event log or a second scope-comparison path, and do NOT build the phase-2 commands, phase-4 hooks, or phase-5 CI. If the work seems to need files outside this fence, STOP and report.
- Anti-regression MUST: preserve existing `- Status:` read behavior and its callers (`aw set`/`aw ipd set`, `finalize`, the installed hooks); the V-01(d) backward-compatibility characterization test is a hard requirement. Run event-derivation alongside, not as a big-bang migration (OQ-01).
- Authority honesty (hard MUST): local events are FORGEABLE by a privileged local agent (findings 5.4/7.3); do NOT describe the local event log as an authority boundary. Non-forgeable provenance / external countersigning is the deferred external-signing set. The transition function MUST NOT be presented as tamper-proof.
- Honesty rule (hard MUST): when a V-item reports a test/`aw check` run passed, paste the ACTUAL runner output; never claim a pass you did not run.
- Commit rule: commit ONLY this child's own changed files, path-scoped (`git commit -m <msg> -- <paths>`); never `git add -A`/bare/`-a`; never push.
- Lifecycle move: on completion, finalize via `aw ipd finalize <this plan> --actor <agent/model> --message <summary> --apply` (runs the pre/post-transition gates, verifies changed paths stayed within `Scope-Paths`, writes the attributed history line, `git mv`s to `.aw/records/plans/executed/`, sets `Status: executed`, and makes the path-scoped lifecycle commit atomically).
