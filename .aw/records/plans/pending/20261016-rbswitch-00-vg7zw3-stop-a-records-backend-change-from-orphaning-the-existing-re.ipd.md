# IPD: Stop a records-backend change from orphaning the existing records tree

- Date: 2026-10-16
- Kind: orchestrator
- Concern: Backlog `wbz75c`: `aw install <repo> --records-backend home -y --no-interactive` on an installed `private-target` repo exits `0`, rewrites `project.json` to `records_backend: home`, and `project_context.resolve_project_context` then resolves `<AW_HOME>/projects/<id>/records` while every existing record stays in `<repo>/.aw/records/`, unseen by any reader (authoring probe reproduced it at HEAD). The config directory does not move, so the Set `cfgreloc` guards and relocation (which key on config placement) never engage. Spec `20260810-1447-01` Section 8 requires that a placement change invoke migration planning rather than silently switching.
- Scope: Orchestration only: sequence the three children below and confirm each reaches `executed`. No code, test, spec or record work of its own.
- Scope-Paths: .aw/records/plans/pending/20261016-rbswitch-00-vg7zw3-stop-a-records-backend-change-from-orphaning-the-existing-re.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: a9685d7b1970dfd323440ae8659ff39dd4ca7ea358c46f0de3a2e6d3de0a8feb
- Coverage-Checked: 2026-10-16 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: bug
- Priority: medium
- From-Backlog: wbz75c
- Blocks-Release: next
- Set: rbswitch
- Order: 0
- Highest E allocated: 03
- Author: opencode
- Id: vg7zw3
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001

- 2026-10-16 coverage pass (aw oc run): fingerprint a9685d7b1970, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready orchestrator graduating backlog wbz75c.

## Goal

A records-backend change on an installed repository can never silently orphan records: by default it refuses before writing, and `aw install --records-backend <new> --relocate` moves the records as a journaled, previewable, resumable and reversible transaction that reuses the Set `cfgreloc` placement-switch machinery.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Children

- [ ] E-01 CONFIRM s07f73 REACHED executed
  - Depends on: none
  - Expected outcome: `aw find plans s07f73` shows it under `executed/`.
  - Execution state: pending

- [ ] E-02 CONFIRM fxbm7j REACHED executed
  - Depends on: E-01
  - Expected outcome: `aw find plans fxbm7j` shows it under `executed/`.
  - Execution state: pending

- [ ] E-03 CONFIRM vv9ki4 REACHED executed
  - Depends on: E-02
  - Expected outcome: `aw find plans vv9ki4` shows it under `executed/`.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `s07f73` | `20261016-rbswitch-01-s07f73-refuse-a-records-root-switch-at-every-install-entry-point-an.ipd.md` | Pure `install_wizard.records_root_switch` detector; refusal in `resolve_policy_noninteractive`, `persist_project_policy` and `cli._run_install` before any write; spec Section 8.2 records-root switch contract. | `executed:ppu39q` |
| 02 | `fxbm7j` | `20261016-rbswitch-02-fxbm7j-records-only-relocation-in-the-placement-switch-planner-and.ipd.md` | `plan_records_root_switch` and `execute_records_root_switch` in `placement_switch.py`, reusing the `cfgreloc` census, blockers, journal, lock, copy-verify, and mode-aware resume/rollback/status. | `executed:s07f73`, `executed:6u755v` |
| 03 | `vv9ki4` | `20261016-rbswitch-03-vv9ki4-wire-records-only-relocation-into-aw-install-relocate-with-e.ipd.md` | Routes a records-only switch through the `ozr356` `--relocate`/`--dry-run`/recovery flags; end-to-end subprocess tests in both directions; CHANGELOG, README, spec 8.2 status. | `executed:fxbm7j`, `executed:ozr356` |

Orders run strictly in sequence, and each also waits on the `cfgreloc` child whose surface it extends (`ppu39q`, `6u755v`, `ozr356`).

## Completion criteria (the whole Set is done only when)

1. No install entry point (noninteractive `--records-backend`, interactive wizard, `persist_project_policy`) changes the resolved records root of a repository whose current root holds records unless a relocation was requested. Owner: s07f73 (E-02, E-03).
2. The records-root switch contract is written into spec `20260810-1447-01` Section 8.2. Owner: s07f73 (E-04).
3. A journaled records-only move ends with every record at the new root, `project.json` changed only in its records keys, the resolver agreeing, and resumes or rolls back after an injected crash. Owner: fxbm7j (E-01..E-05).
4. `aw install --records-backend <new> --relocate` performs the move end-to-end in both directions, `--dry-run` previews it, the recovery flags finish or undo it, and every user-facing surface describes it. Owner: vv9ki4 (E-01..E-05).

## Cross-IPD validation

- Order 01's detector yields to `cfgreloc`'s `config_placement_switch` (a full placement switch is never also reported as a records switch), so exactly one refusal or one relocation path fires per request. Owner: s07f73 (V-02).
- Order 02's planner calls Order 01's `records_root_switch` for detection, so the refusal and the planner cannot disagree about what is a records switch. Owner: fxbm7j (V-01).
- Order 02's journal shares the `cfgreloc` control dir and is dispatched by `mode`, so a records journal and a placement journal block each other. Owner: fxbm7j (E-05 case 8, V-05).
- Order 03's end-to-end tests assert the same invariants Order 02's unit tests do, through the real CLI. Owner: vv9ki4 (V-05).

## Deferred / out of scope (with reason)

- Moving records to or from a companion records backend (a second git repository is involved); such a switch keeps refusing whenever the current records root holds records (`s07f73` E-02 `reason="companion"`), and proceeds as a plain policy update only when there is nothing to orphan.
  - Carrier: n9vd2h
- Config placement switches, which already move records as part of a full relocation.
  - Carrier: c54a4z

## Scope check

- Over-scope: none. This plan contributes no code, test or record of its own.
- Under-scope: none; refusal and contract (01), transaction (02) and user surface (03) together are the fix the backlog item names (a backend change that "repoints the records resolver without moving the existing records tree" must either move it or not repoint).

## Required tests / validation

This plan runs no tests. Each child runs its own module and the bare suite; Order 03 (`vv9ki4`) runs the end-to-end subprocess tests and `make test-all` that exercise the whole Set.

## Open questions

### OQ-01: A new Set, or new children in Set cfgreloc?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: A new Set. The `cfgreloc` orchestrator `c54a4z` and its five children are already `approved`, and its child table and coverage fingerprint would have to change, reopening an approved review; `c54a4z` itself lists `wbz75c` as a separately carried deferral ("distinct root cause"). Cross-Set `Item-Dependencies` (`executed:ppu39q`, `executed:6u755v`, `executed:ozr356`) give the same ordering, and the runner re-checks them at dispatch.

### OQ-02: Why three children?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: The refusal (01) is valuable alone and closes the silent data-loss path even if the move stalls; the transaction (02) is the only code that deletes records and stays reviewable in isolation; the CLI (03) depends on `ozr356`, the last `cfgreloc` child, so splitting it lets 01 and 02 ship earlier.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `aw find plans s07f73` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `aw find plans fxbm7j` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `aw find plans vv9ki4` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) of this plan and each child. EXECUTION CONTRACT: all open questions are resolved. This plan performs no work of its own; each child carries its own scope fence, test evidence and path-scoped `aw commit`. Paste ACTUAL output for every confirmation; never claim a child executed that `aw find plans` does not show under `executed/`. Never push. Under `aw oc run` / `aw agy run` the runner retires this orchestrator once every child is `executed`; by hand, finalize it through `aw ipd finalize` after every `V-*` is `pass`.
