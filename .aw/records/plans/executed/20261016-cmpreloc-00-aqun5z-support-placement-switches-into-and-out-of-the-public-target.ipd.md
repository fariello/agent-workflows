# IPD: Support placement switches into and out of the public-target-private-companion preset

- Date: 2026-10-16
- Kind: orchestrator
- Concern: Backlog `n9vd2h`, deferred from Set `cfgreloc` (backlog `ui1aln`): the cfgreloc placement switch relocates config, durable state and records between the target and `AW_HOME`, but a switch into or out of `public-target-private-companion` also has to stage into or out of a second git repository (the companion) and attach or detach a companion identity (`storage.attach_companion`/`storage.detach_companion`). Those switches keep refusing (cfgreloc planner blocker `companion-unsupported`, plan `xvlemm` E-02; refusal message naming `n9vd2h`, plan `ozr356` E-01). This Set adds them on top of the cfgreloc planner, executor and CLI.
- Scope: Orchestration only: sequence the three children below and confirm each reaches `executed`. No code, test, spec or record work of its own.
- Scope-Paths: .aw/records/plans/pending/20261016-cmpreloc-00-aqun5z-support-placement-switches-into-and-out-of-the-public-target.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: 90b83754d0a96fd787e8c0e1fe51517060b0acc8c5e18361ebc27834cf51a405
- Coverage-Checked: 2026-10-16 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: feature
- Priority: low
- From-Backlog: n9vd2h
- Set: cmpreloc
- Order: 0
- Highest E allocated: 03
- Author: opencode
- Id: aqun5z

## Workflow history
- 2026-10-17 executed (aw agy run model=Gemini-3.8-Flash-High): RETIRED as the orchestrator rollup step of a runner Set completion, not executed by an agent: every child of Set cmpreloc reached executed, so the runner (run run-20261017T051054Z-101189) retired this Order-0 plan as bookkeeping. Its own E-*/V-* items were NOT performed; the runner superseded them by enforcing the ordering, the isolation and the per-child merge gate. Justifying children: xc8nae, fo08zx, y1e2m9.
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 cross-reference (opencode, from /plan-review of fo08zx PR-001): ownership of the interim `companion-unsupported` blocker re-assigned: `fo08zx` E-06 adds an `allow_companion=True` library opt-in, `y1e2m9` removes the blocker from the default path; completion criteria and child rows reconciled.
- 2026-10-16 coverage pass (aw oc run): fingerprint 90b83754d0a9, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-16 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004

- 2026-10-16 coverage pass (aw oc run): fingerprint 13badcceab78, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-16 coverage pass (aw oc run): fingerprint a583eeb0933c, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready orchestrator of Set cmpreloc graduating backlog n9vd2h.

## Goal

`aw install --relocate` switches a repository into or out of `public-target-private-companion` from or to every other preset, with the same preview, transaction, recovery and documentation guarantees the cfgreloc Set gives target and home placements.

## Detailed Implementation Checklist (TODO)


> Its own E-*/V-* items were NOT performed; the runner superseded them by enforcing the ordering, the isolation and the per-child merge gate.

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Children

- [ ] E-01 CONFIRM xc8nae REACHED executed
  - Depends on: none
  - Expected outcome: `xc8nae` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-02 CONFIRM fo08zx REACHED executed
  - Depends on: E-01
  - Expected outcome: `fo08zx` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-03 CONFIRM y1e2m9 REACHED executed
  - Depends on: E-02
  - Expected outcome: `y1e2m9` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `xc8nae` | `20261016-cmpreloc-01-xc8nae-extend-the-placement-switch-planner-to-companion-pairs.ipd.md` | Read-only companion census for the six pairs, per-repository source/destination, attach/detach, companion blockers and warnings, with purity tests (also needs cfgreloc `xvlemm`, declared in its `- Item-Dependencies:`). | none |
| 02 | `fo08zx` | `20261016-cmpreloc-02-fo08zx-execute-companion-placement-switches-with-companion-staging.ipd.md` | Executes companion plans inside the cfgreloc journal: companion creation, per-repository staging with an ignore filter, attach/detach, config retracking, resume, rollback, fault points and tests, and adds a library opt-in (`allow_companion=True`) past the interim `companion-unsupported` planner blocker Order 01 keeps (also needs cfgreloc `6u755v`). | 01 |
| 03 | `y1e2m9` | `20261016-cmpreloc-03-y1e2m9-make-companion-placement-switches-reachable-from-aw-install.ipd.md` | Makes companion switches reachable from `aw install --relocate` (removing the interim `companion-unsupported` blocker and the `allow_companion` opt-in) with preview lines, updates the cfgreloc CLI test, adds end-to-end tests, CHANGELOG, README and the spec Section 8.1 item 3 amendment (also needs cfgreloc `ozr356`). | 02 |

## Completion criteria (the whole Set is done only when)

- The planner computes a fully populated plan for every pair into or out of `public-target-private-companion` and blocks unsafe companion states, while still carrying `companion-unsupported` as an ordinary interim blocker so the cfgreloc executor and CLI keep refusing until execution support exists (`xc8nae` OQ-03). Owner: xc8nae
- A companion switch completes, resumes or rolls back with both repositories byte-checked, staged and never committed, when opted in past the interim `companion-unsupported` blocker (`allow_companion=True`, `fo08zx` E-06). Owner: fo08zx
- `aw install --relocate` reaches companion switches (the planner no longer emits `companion-unsupported` on the default path and the `allow_companion` keyword is gone), previews them, and the CHANGELOG, README and spec Section 8.1 describe the shipped behavior. Owner: y1e2m9

## Cross-IPD validation

- The plan fields Order 01 adds (`companion_action`, `companion_dir`, `source_git`, `dest_git`, `companion_create`, `config_retrack`, `direction="in-place"`, `retire_side=None`) are exactly the fields Order 02 consumes; Order 02's tests drive real plans from `plan_placement_switch`, never hand-built ones. Owner: fo08zx
- The preview Order 03 renders shows the warnings Order 01 computes. Owner: y1e2m9
- The full placement-switch suite (cfgreloc and cmpreloc modules) passes together under `make test-all`. Owner: y1e2m9

## Deferred / out of scope (with reason)

- Moving a binding between two companion directories: `aw storage move` (`storage.move_companion`) already does it; Order 01 blocks it with `companion-to-companion` naming that command.
  - Carrier-Declined: deliberate non-goal; an existing verb owns it.
- Deleting a detached companion repository or purging target history: destructive and outside an install.
  - Carrier-Declined: deliberate non-goal; recorded in `fo08zx`.

## Scope check

- Over-scope: none.
- Under-scope: none; planning, execution and CLI reachability each have a child, and every completion criterion names its owner.

## Required tests / validation

This plan runs no tests. Planner tests: xc8nae. Executor tests including every fault point: fo08zx. End-to-end CLI tests, bare `python3 -m pytest`, `make test-all` and `aw sanitize --agent` for the whole Set: y1e2m9.

## Open questions

### OQ-01: Must this Set wait for the whole cfgreloc Set?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Each child depends on exactly the cfgreloc plan it extends (`xc8nae` on `xvlemm`, `fo08zx` on `6u755v`, `y1e2m9` on `ozr356`), declared in their `- Item-Dependencies:` so the runner re-checks them at dispatch. No other cfgreloc ordering is needed.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `ls .aw/records/plans/executed/ | grep xc8nae` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `ls .aw/records/plans/executed/ | grep fo08zx` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `ls .aw/records/plans/executed/ | grep y1e2m9` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. This orchestrator performs no work of its own: under `aw oc run` / `aw agy run` it is retired once every child is `executed`. By hand, execute the children in Order (each under its own gate), then confirm each row above, pasting the ACTUAL command output each `V-*` demands (never claim a child executed without it). Scope fence: `- Scope-Paths:` (this plan file only); justify any other edit at finalize. Commit through `aw commit aqun5z -- <paths>`; never `git add -A`, never push. Under a runner the runner retires this plan; by hand, `aw ipd finalize aqun5z` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
