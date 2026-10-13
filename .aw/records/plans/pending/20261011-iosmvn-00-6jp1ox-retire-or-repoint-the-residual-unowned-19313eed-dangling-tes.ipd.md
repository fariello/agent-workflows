# IPD: Retire or repoint the residual unowned 19313eed dangling test citations in shipped source

- Date: 2026-10-11
- Kind: orchestrator
- Concern: Backlog `iosmvn` is the rollup for `19313eed`-deleted test-path citations in shipped source (`agent_workflows/`, `tools/`) that no dedicated item owns. Re-measured at authoring HEAD `8538be828`: excluding the clusters already carried by sibling plans and items (`test_orchestrator_probe_cache.py` -> `046nys`/`dtelfb` and `3tov52`/`65d5zf`; `test_review_findings_cascade.py` and `test_runner_stop_triggers.py` -> `3tov52`/`65d5zf`; `test_runner_backlog_close.py` and `test_runner_layering.py` -> `yf1p8y`; `test_run_flag_surface.py` -> executed `rcp8c4`), 88 citation sites remain whose surrounding prose does not name `19313eed`: 41 in `runner_shared.py`, 19 in the host drivers and runner peripherals, 27 in 17 other modules, and one census fixture in `tools/`. Each tells a reader a nonexistent test guards a property.
- Scope: Orchestration only: sequence the four children below and confirm each reaches `executed`. No code, test or record of its own.
- Scope-Paths: .aw/records/plans/pending/20261011-iosmvn-00-6jp1ox-retire-or-repoint-the-residual-unowned-19313eed-dangling-tes.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: b2fb2458390bef2156739ead961888309141780fe4c3b3a611caf577e30565a3
- Coverage-Checked: 2026-10-12 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: chore
- Priority: low
- From-Backlog: iosmvn
- Set: iosmvn
- Order: 0
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 6jp1ox
- Approval: 2026-10-13, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-13 approved (aw set): status set to approved
- 2026-10-13 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): plan-review: APPROVE WITH REVISIONS APPLIED

- 2026-10-13 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004. Re-measured at HEAD 95763c6cf: UNRETIRED 88 split 41/19/27/1 as stated; children and dependency edges match the table; aw ipd coverage ready. Deferred sibling row split into per-owner carriers; gate states iosmvn is still open and adds the honesty rule; OQ-01 owner set.
- 2026-10-12 coverage pass (aw oc run): fingerprint b2fb2458390b, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-12 coverage pass (aw oc run): fingerprint 84011c27212e, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog `iosmvn`.

## Goal

Leave no `19313eed` dangling test citation in shipped source silently abandoned: each is repointed to a live test or rewritten as an honest retirement statement, and every behavioral guard the rewrite exposes as lost has a backlog carrier.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Children

- [ ] E-01 CONFIRM yuhl6o REACHED executed
  - Depends on: none
  - Expected outcome: `aw find plans yuhl6o` shows it under `executed/`.
  - Execution state: pending

- [ ] E-02 CONFIRM 9rthek REACHED executed
  - Depends on: none
  - Expected outcome: `aw find plans 9rthek` shows it under `executed/`.
  - Execution state: pending

- [ ] E-03 CONFIRM ev7t1w REACHED executed
  - Depends on: none
  - Expected outcome: `aw find plans ev7t1w` shows it under `executed/`.
  - Execution state: pending

- [ ] E-04 CONFIRM ellenm REACHED executed
  - Depends on: E-01, E-02, E-03
  - Expected outcome: `aw find plans ellenm` shows it under `executed/`.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `yuhl6o` | `20261011-iosmvn-01-yuhl6o-retire-or-repoint-the-residual-dangling-test-citations-in-ru.ipd.md` | Disposition and rewrite the 41 sites in `agent_workflows/runner_shared.py`; defines the Set measurement and AST-equivalence commands. | none |
| 02 | `9rthek` | `20261011-iosmvn-02-9rthek-retire-or-repoint-the-dangling-test-citations-in-the-host-dr.ipd.md` | The 19 sites in `oc_runipd`, `agy_runipd`, `ipd_lint`, `runner_shutdown`, `run_viewer`, `artifact_audit`. | none |
| 03 | `ev7t1w` | `20261011-iosmvn-03-ev7t1w-retire-or-repoint-the-dangling-test-citations-in-the-non-run.ipd.md` | The 27 sites in 17 non-runner modules; dispositions the two non-claim hits. | none |
| 04 | `ellenm` | `20261011-iosmvn-04-ellenm-reconcile-the-shipped-source-dangling-census-and-file-the-un.ipd.md` | Whole-population measurement, cross-check of the three disposition tables, and a backlog carrier per RETIRE-UNGUARDED group. | `executed:yuhl6o`, `executed:9rthek`, `executed:ev7t1w` |

Orders 01, 02 and 03 touch disjoint files and are mutually independent.

## Completion criteria (the whole Set is done only when)

1. `runner_shared.py` measures `UNRETIRED 0`. [Owner: yuhl6o E-03]
2. The six driver and peripheral files measure `UNRETIRED 0`. [Owner: 9rthek E-03]
3. The 17 non-runner modules measure `UNRETIRED 0`. [Owner: ev7t1w E-03]
4. Every edit is prose-only (`AST-DIFFER []`) and the bare suite passes. [Owner: yuhl6o E-04, 9rthek E-04, ev7t1w E-04]
5. The whole shipped-source measurement leaves only the census-fixture line. [Owner: ellenm E-01]
6. Every RETIRE-UNGUARDED property has a filed backlog item or a named live owner. [Owner: ellenm E-03]

## Cross-IPD validation

- The three children's disposition-table row counts sum to the whole-population count less the census fixture. [Owner: ellenm E-02]
- All children use the identical measurement command recorded in `yuhl6o`. [Owner: ellenm E-01]

## Deferred / out of scope (with reason)

- The sibling-owned `test_orchestrator_probe_cache.py`, `test_review_findings_cascade.py` and `test_runner_stop_triggers.py` citations named in Concern.
  - Carrier: 65d5zf
  - Carrier-Evidence: .aw/records/plans/executed/20261011-3tov52-01-65d5zf-retire-dangling-citations-of-deleted-code-pin-tests-in-runne.ipd.md
- The sibling-owned `runner_shared` module-level import-pin citation of `test_orchestrator_probe_cache.py` named in Concern.
  - Carrier: dtelfb
  - Carrier-Evidence: .aw/records/plans/executed/20261011-046nys-01-dtelfb-record-retirement-of-the-runner-shared-module-level-import-p.ipd.md
- The sibling-owned `test_runner_backlog_close.py` and `test_runner_layering.py` citations named in Concern.
  - Carrier: z2ugxc
- The `test_run_flag_surface.py` citations named in Concern.
  - Carrier-Evidence: .aw/records/plans/executed/20261001-rcp8c4-01-8wpjeq-strike-the-seven-dangling-test-run-flag-surface-citations-in.ipd.md
- Restoring behavioral coverage for each lost guard: `ellenm` E-03 files one backlog carrier per RETIRE-UNGUARDED group; the restoration itself belongs to those items.
  - Carrier: ellenm
- Restoring any source-reading guard.
  - Carrier-Declined: forbidden by `AGENTS.md` and `GUIDING_PRINCIPLES` P16.

## Scope check

- Over-scope: none. This plan contributes no code, test or record of its own.
- Under-scope: none; all 88 measured sites are assigned to a child. Re-measured at review HEAD `95763c6cf` with `yuhl6o`'s measurement command over `git ls-files 'agent_workflows/*.py' 'tools/*'`: `UNRETIRED 88`, split `runner_shared.py` 41, the six driver and peripheral files 19 (`agy_runipd` 8, `oc_runipd` 7, `artifact_audit`, `ipd_lint`, `run_viewer`, `runner_shutdown` 1 each), 17 other modules 27, and `tools/lost_guard_census.py` 1.

## Required tests / validation

This plan runs no tests. Orders `yuhl6o`, `9rthek` and `ev7t1w` each run the bare suite; `ellenm` performs the whole-Set measurement.

## Open questions

### OQ-01: Why split by file group rather than by deleted test file?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Edits are per production file; splitting by file keeps each child's Scope-Paths disjoint, so the three can run independently, and keeps each one-pass. Grouping by deleted test file is used where it matters, for filing carriers (`ellenm`).

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw find plans yuhl6o` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw find plans 9rthek` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw find plans ev7t1w` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw find plans ellenm` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval of each child before execution. The runner retires this orchestrator once every child is `executed`; executing by hand, confirm each child in Order and finish with `aw ipd finalize`, never a hand `git mv`. This plan writes no code; never push. Paste the ACTUAL `aw find plans` output for every `V-*` item; never claim a child executed from memory. Open questions: OQ-01 is `resolved` and not blocking. Backlog `iosmvn` is still `open` at review HEAD `95763c6cf`; it moves to `graduated` through the graduation handoff once every plan in the Set is `to-review` or later (true at review) and this orchestrator passes `aw ipd coverage 6jp1ox` (passed at review, cached), and it closes `done` through the `From-Backlog` handoff once the Set is executed.
