# IPD: Support placement switches into and out of the public-target-private-companion preset

- Date: 2026-10-16
- Kind: orchestrator
- Concern: Backlog `n9vd2h`, deferred from Set `cfgreloc` (backlog `ui1aln`): the cfgreloc placement switch relocates config, durable state and records between the target and `AW_HOME`, but a switch into or out of `public-target-private-companion` also has to stage into or out of a second git repository (the companion) and attach or detach a companion identity (`storage.attach_companion`/`storage.detach_companion`). Those switches keep refusing (cfgreloc planner blocker `companion-unsupported`, plan `xvlemm` E-02; refusal message naming `n9vd2h`, plan `ozr356` E-01). This Set adds them on top of the cfgreloc planner, executor and CLI.
- Scope: Orchestration only: sequence the three children below and confirm each reaches `executed`. No code, test, spec or record work of its own.
- Scope-Paths: .aw/records/plans/pending/20261016-cmpreloc-00-aqun5z-support-placement-switches-into-and-out-of-the-public-target.ipd.md
- Item-Dependencies: none
- Status: to-review
- Coverage: pass
- Coverage-Fingerprint: a583eeb0933ce398ebae7504d3ce3ba13ce8a30a4b5a4a6ea718b66dacd47ca6
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

- 2026-10-16 coverage pass (aw oc run): fingerprint a583eeb0933c, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready orchestrator of Set cmpreloc graduating backlog n9vd2h.

## Goal

`aw install --relocate` switches a repository into or out of `public-target-private-companion` from or to every other preset, with the same preview, transaction, recovery and documentation guarantees the cfgreloc Set gives target and home placements.

## Detailed Implementation Checklist (TODO)

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
| 02 | `fo08zx` | `20261016-cmpreloc-02-fo08zx-execute-companion-placement-switches-with-companion-staging.ipd.md` | Executes companion plans inside the cfgreloc journal: companion creation, per-repository staging with an ignore filter, attach/detach, config retracking, resume, rollback, fault points and tests (also needs cfgreloc `6u755v`). | 01 |
| 03 | `y1e2m9` | `20261016-cmpreloc-03-y1e2m9-make-companion-placement-switches-reachable-from-aw-install.ipd.md` | Makes companion switches reachable from `aw install --relocate` with preview lines, updates the cfgreloc CLI test, adds end-to-end tests, CHANGELOG, README and the spec Section 8.1 item 3 amendment (also needs cfgreloc `ozr356`). | 02 |

## Completion criteria (the whole Set is done only when)

- The planner computes a populated plan, not `companion-unsupported`, for every pair into or out of `public-target-private-companion`, and blocks unsafe companion states. Owner: xc8nae
- A companion switch completes, resumes or rolls back with both repositories byte-checked, staged and never committed. Owner: fo08zx
- `aw install --relocate` reaches companion switches, previews them, and the CHANGELOG, README and spec Section 8.1 describe the shipped behavior. Owner: y1e2m9

## Cross-IPD validation

- The plan fields Order 01 adds (`companion_action`, `source_git`, `dest_git`, `companion_create`, `config_retrack`, `retire_side=None`) are exactly the fields Order 02 consumes; Order 02's tests drive real plans from `plan_placement_switch`, never hand-built ones. Owner: fo08zx
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
  - Required evidence: pasted `aw find plans xc8nae` (or `ls .aw/records/plans/executed/ | grep xc8nae`) output and its `- Status: executed` line.
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

Execute only after explicit human approval (`Status: approved`). This orchestrator performs no work: under `aw oc run` / `aw agy run` it is retired once every child is `executed`. By hand, execute the children in Order, then confirm each row above. Never push.
