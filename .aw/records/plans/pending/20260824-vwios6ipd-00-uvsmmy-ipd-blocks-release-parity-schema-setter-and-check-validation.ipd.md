# IPD: IPD blocks-release parity: schema, setter, and check validation

- Date: 2026-08-24
- Kind: orchestrator
- Concern: AGENTS.md (Release gates) states any backlog item, spec, OR plan may carry a `- Blocks-Release: <release-id6|next>` front-matter field, but for plans this is untrue today: the IPD linter rejects the field as IPD-M103 "unknown field" (so a plan carrying it cannot pass `aw ipd lint` nor the execution checkpoints that call it), there is no `aw ipd set --blocks-release` setter, and `aw check` has no path to validate the field on a plan. Backlog item vwios6 (release-blocker for 2.0.0 / f33nrj).
- Scope: Achieve full release-gate parity for plans across the three enforcement surfaces (schema/lint, setter, check/attention), split into three dependency-ordered child IPDs so each is small and independently verifiable. Also fixes the shared blocks-release setter path (bug 61qk4a) so the fix is not duplicated as a broken code path.
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/ipd_lint.py, agent_workflows/status_set.py, agent_workflows/cli.py, agent_workflows/backlog.py, agent_workflows/releases.py, agent_workflows/check_engine.py, agent_workflows/attention.py, tests/
- Status: approved
- Set: vwios6ipd
- Order: 0
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: uvsmmy
- Approval: 2026-08-25, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-25 approved (aw set): status set to approved
- 2026-08-25 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002 fixed
- 2026-08-24 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): Completed drafting: fully authored, lint-conforming, ready to critique

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; orchestrator for backlog item vwios6 (IPD blocks-release parity), split into 3 dependency-ordered children. NOTE: this plan's own `- Blocks-Release: next` intent is DEFERRED (not written to front matter) until child 01 lands, because a plan carrying the field currently fails `aw ipd lint` (IPD-M103) - the exact bug this Set fixes. Interim release-blocker intent is tracked on backlog item vwios6 and the 2.0.0 (f33nrj) release record; re-mark via `aw ipd set --blocks-release next` after child 02 ships the setter.

## Goal

Make `- Blocks-Release: <release-id6|next>` a first-class, tool-managed field on IPDs with the same semantics it already has on backlog items and specs, so the AGENTS.md "any backlog item, spec, OR plan may carry Blocks-Release" statement becomes true for plans. This unblocks marking the approved execset/ipdgates/proclint/unifyfileio IPDs as release blockers via the tool instead of by hand-edit.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator does not itself edit code; each `E-*` below is the delivery of one child IPD. Execute the children in Order; mark an `E-*` complete only after that child has been fully executed (all its own V items verified and it has moved to `executed/`).

### Task group 1: Schema recognition (foundation)

- [ ] E-01 Deliver child IPD Order 01 (si3mmt): add `Blocks-Release` to the IPD schema recognized-field set so an IPD carrying it lints CONFORMING at every phase, with a regression test guarding against re-introducing IPD-M103.
  - Depends on: none
  - Expected outcome: an IPD with `- Blocks-Release: next` passes `aw ipd lint` at author/pre-execution/pre-transition/post-transition; a regression test asserts it.
  - Execution state: pending

### Task group 2: Setter and shared-path fix

- [ ] E-02 Deliver child IPD Order 02 (efnn74): add `--blocks-release <release-id6|next|->` to `aw ipd set` and fix the shared setter path so plans AND backlog persist the field (root-causing bug 61qk4a: backlog set --blocks-release silently no-ops).
  - Depends on: E-01
  - Expected outcome: `aw ipd set --blocks-release next <id6>` writes the field to the plan front matter; `aw backlog set --blocks-release next` persists it (no longer a no-op); `-` clears it; a workflow-history line is appended.
  - Evidence for the executor (verified during this review): in `status_set.apply_status_change` the `blocks_release` handler (`br = getattr(args, "blocks_release", None)` -> `releases.set_blocks_release_line`) is nested INSIDE the `if rec.record_type == "specs":` branch, so it runs for specs only and is silently skipped for `plans` and `backlog` record types. `aw ipd set` (p_ipd_set in cli.py) also exposes no `--blocks-release` argument at all (only `aw set`, `aw backlog set`, `aw spec set` do). The fix is to hoist the blocks-release write out of the specs-only branch into a shared, record-type-agnostic step (all setters funnel through the single `releases.set_blocks_release_line` primitive) and add the `--blocks-release` argument to `aw ipd set`. Backlog also has a second write site (`backlog.py` ~471) - reconcile to one path so the fix is not duplicated.
  - Execution state: pending

### Task group 3: Validation and attention surfacing

- [ ] E-03 Deliver child IPD Order 03 (7mw7m5): extend `aw check` to validate a plan's `Blocks-Release` (clean when it resolves, flagged when dangling) and confirm `aw attention` surfaces a plan carrying it in the release-blocker set.
  - Depends on: E-01, E-02
  - Expected outcome: `aw check` flags a plan with a dangling `Blocks-Release`; a plan carrying `- Blocks-Release: next` appears in `aw attention`'s release-blocker set.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | 20260824-vwios6ipd-01-si3mmt-add-blocks-release-to-ipd-schema-recognized-fields.ipd.md | Adds `Blocks-Release` to `META_RECOGNIZED`; lint stays conforming; regression test | none |
| 02 | 20260824-vwios6ipd-02-efnn74-aw-ipd-set-blocks-release-and-shared-setter-fix-for-plans-an.ipd.md | Adds `aw ipd set --blocks-release`; fixes shared setter path so plans+backlog persist the field (61qk4a) | 01 |
| 03 | 20260824-vwios6ipd-03-7mw7m5-aw-check-validates-plan-blocks-release-and-attention-surfaci.ipd.md | `aw check` validates plan Blocks-Release (dangling); attention surfaces it | 01, 02 |

Dependency rationale: 01 must land first because until the schema recognizes the field, any plan carrying it (including test fixtures used by 02 and 03) fails `aw ipd lint` and cannot be exercised. 02 requires 01 so the setter's written field lints clean. 03 requires 01 (schema) and 02 (a persisted field to validate/surface).

## Completion criteria (the whole Set is done only when)

- An IPD that legally carries `- Blocks-Release: next` (or a real release id6) lints CONFORMING at every phase (author/pre-execution/pre-transition/post-transition).
- `aw ipd set --blocks-release <next|id6|->` writes/updates/clears the front-matter field and appends a workflow-history line.
- `aw backlog set open <id6> --blocks-release next` persists the field (bug 61qk4a resolved), verified against the previously-broken positional-status path.
- `aw check` validates a plan's `Blocks-Release` the same as backlog/specs (clean when it resolves, flagged when dangling).
- `aw attention` surfaces a plan carrying `Blocks-Release: next` in the release-blocker set for release f33nrj.
- Each child IPD's own validation passed with pasted evidence and each child moved to `executed/`.

## Cross-IPD validation

- After all three children execute (setter available only once child 02 is `executed`), and WHILE this orchestrator is still non-terminal (`approved`, before its own finalize), hand-verify parity: use the new setter (`aw ipd set --blocks-release next <this-plan-id6>`) to mark this orchestrator itself, then run `aw ipd lint` on it plus `aw check` and `aw attention` to confirm the plan, backlog, and spec surfaces agree on release f33nrj (a plan carrying `- Blocks-Release: next` lints clean, is validated by `aw check`, and appears in `aw attention`'s release-blocker set). This doubles as the end-to-end acceptance of the whole Set.
- Timing note (why the self-mark must happen before finalize): once this orchestrator moves to `executed/`, its status maps to the attention `done` class (`attention_contract.py: executed -> DONE`) and `aw attention`'s `release_blockers` scan SKIPS `done` items (`attention.py:485-486`), so an executed plan carrying the field would NOT surface as an outstanding release blocker. Perform the attention-surfacing acceptance check while the plan is still `approved`.
- Standing release-blocker intent: keep the durable "this Set blocks 2.0.0" declaration on the OPEN backlog item vwios6 (and the f33nrj release record), NOT as a `- Blocks-Release:` line on this terminal orchestrator. On finalize, whether the self-mark line is left on the executed record or cleared with `aw ipd set --blocks-release - <this-plan-id6>` is immaterial to enforcement (an executed plan is `done` and no longer gates); do NOT rely on the executed orchestrator itself to enforce the gate. The acceptance evidence (the pre-finalize surfacing check above) is what proves parity.
- Confirm no duplicated blocks-release write logic remains: the field write must go through the single shared `releases.set_blocks_release_line` primitive from all setter call sites (verify no fourth copy was added; backlog's two call paths `run_set` at `backlog.py:467` and the positional path via `status_set.apply_status_change` both resolve to that one primitive).
- Anti-regression invariant (specs must not break): child 02 hoists the blocks_release write OUT of the `if rec.record_type == "specs":` guard (`status_set.py:416,449-455`). Confirm existing `aw spec set --blocks-release` behavior is unchanged after the hoist (a spec setter test must still pass), so widening the write path to plans/backlog does not regress the specs surface it was originally scoped to.

## Deferred / out of scope (with reason)

- Actually marking the execset/ipdgates/proclint/unifyfileio IPDs with `Blocks-Release` is out of scope here; that is a downstream action to perform with the new setter once this Set lands.
- Sibling bug 61qk4a has its own backlog record; its fix is folded into child 02 because it is the same shared code path, but no separate IPD is authored for it here.

## Scope check

- Over-scope: none. Confined to the blocks-release enforcement surfaces named in Scope-Paths.
- Under-scope: none. Covers all three DoD surfaces (schema/lint, setter, check/attention) plus the shared-path bug that would otherwise re-break the setter.

## Required tests / validation

- Each child ships its own tests (schema/lint regression, setter persist/clear/resolve + 61qk4a regression, check dangling + attention surfacing). This orchestrator is validated by the children passing and by the cross-IPD parity check above.
- Whole-suite `python3 -m pytest tests/` green after the last child.

## Open questions

### OQ-01: Should `aw check` scan the plans tree for Blocks-Release, or should the plan-side check fold into the `check_refs` per-type seam?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED to child 03, which owns the decision. Both are viable (extend `releases.check_blocks_release` to include the plans dir, or add via the `check_engine.check_refs` seam); child 03 picks the lower-drift option at execution time. Non-blocking for this orchestrator.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: child 01 moved to `executed/`; `aw ipd lint` output pasted showing an IPD carrying `- Blocks-Release: next` is CONFORMING; the regression test named and shown passing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: child 02 moved to `executed/`; pasted output of `aw ipd set --blocks-release next <id6>` and `aw ipd set --blocks-release - <id6>` showing write and clear; pasted output showing `aw backlog set open <id6> --blocks-release next` now persists the field (61qk4a regression test passing).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: child 03 moved to `executed/`; pasted `aw check` output flagging a dangling plan Blocks-Release; pasted `aw attention` output listing a plan with `Blocks-Release: next` in the release-blocker set.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (release-gate parity for plans) delivered as three dependency-ordered children, each a small single-surface change; splitting maximizes the likelihood of clean, independently-verifiable execution.

### Execution contract

1. Open questions RESOLVED: OQ-01 is non-blocking and deferred to child 03. No blocking open question remains.
2. Scope fence: this orchestrator authors no code; execute children in Order (01, then 02, then 03), each under its own scope fence. Do NOT begin a child before its declared dependencies are `executed`.
2a. Per-child approval gate: the three children are currently `Status: draft`. Each child MUST independently reach `Status: approved` (its own `/plan-review` completed and human sign-off recorded) BEFORE it is executed. Executing this orchestrator does NOT confer approval on the children; an executor MUST NOT run a child that is still `draft`/`to-review`/`reviewed`. Bring each child to `approved` (in Order) before beginning it.
3. Honesty rule (hard MUST): when reporting a child complete, rely on that child's pasted validation evidence; never mark an `E-*`/`V-*` here from narration.
4. Commit ONLY each child's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: this orchestrator moves to `executed/` only after all three children are `executed`, every V item here is verified with pasted evidence, the `## Workflow history` line is appended, and `Status: executed` is set, via the lifecycle workflow.
