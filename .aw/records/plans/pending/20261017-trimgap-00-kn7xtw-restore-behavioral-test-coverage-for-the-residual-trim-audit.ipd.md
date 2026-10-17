# IPD: Restore behavioral test coverage for the residual trim-audit gaps across 45 modules

- Date: 2026-10-17
- Kind: orchestrator
- Concern: Backlog item `q86fxm` is the residual rollup of the uncited trim-audit (`b1mx2w` `## Filing plan` groups 16 through 60): 135 production keys across 44 modules that the routine non-slow test selection did not reach at baseline HEAD `86f0d88d`, plus 34 test names missing from the recreated `tests/test_run_summary_table.py` (group 40, `render_stream.py`), all because suite trim `19313eed` deleted the behavioral tests that drove them. This orchestrator sequences the eight child plans that restore that coverage, and is ALSO the Order-0 parent of the Set's thirteen per-item children (Orders 02, 04 to 15), each graduated from its own `trimgap` backlog item (groups 2 to 15 of the same filing plan), because the runner reads Set membership from disk (`runner_shared.read_set_membership`) and gates retirement on every one of them.
- Scope: Orchestration only: confirm each of the twenty-one children below reaches `executed`. No code, test, spec or record work of its own. The eight `q86fxm` children partition the 45 residual groups by module family; the thirteen per-item children each own one backlog item. No Scope-Paths file is shared between any two of the 21 children (checked at review).
- Scope-Paths: .aw/records/plans/pending/20261017-trimgap-00-kn7xtw-restore-behavioral-test-coverage-for-the-residual-trim-audit.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: fe4925e03a985f5112101827836a35fa4032a3a47b035731c23925f5b23e8005
- Coverage-Checked: 2026-10-17 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 0
- Highest E allocated: 21
- Author: opencode
- Id: kn7xtw
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003

- 2026-10-17 coverage pass (aw oc run): fingerprint fe4925e03a98, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-17 coverage pass (aw oc run): fingerprint c002fda2872c, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-17 to-review (opencode): authored from backlog `q86fxm` together with children `ivap17`, `vqr3xq`, `zhoul7`, `78g6ic`, `5e7czd`, `y4bt1c`, `9gjvrq`, `ya63p5`.
- 2026-10-17 draft (opencode): created.

## Goal

Graduate backlog `q86fxm` into executable children whose combined effect is that every one of the 135 residual keys is reached and mutation-guarded by the routine bare core-tier run, and 33 of the 34 missing run-summary tests are back; and confirm that the Set's thirteen per-item children, each governed by its own backlog item and its own Goal, also finished. This plan only confirms the children finished.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: confirm the children

- [ ] E-01 CONFIRM ivap17 REACHED executed
  - Depends on: none
  - Expected outcome: `ivap17` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-02 CONFIRM vqr3xq REACHED executed
  - Depends on: none
  - Expected outcome: `vqr3xq` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-03 CONFIRM zhoul7 REACHED executed
  - Depends on: none
  - Expected outcome: `zhoul7` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-04 CONFIRM 78g6ic REACHED executed
  - Depends on: none
  - Expected outcome: `78g6ic` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-05 CONFIRM 5e7czd REACHED executed
  - Depends on: none
  - Expected outcome: `5e7czd` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-06 CONFIRM y4bt1c REACHED executed
  - Depends on: none
  - Expected outcome: `y4bt1c` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-07 CONFIRM 9gjvrq REACHED executed
  - Depends on: none
  - Expected outcome: `9gjvrq` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-08 CONFIRM ya63p5 REACHED executed
  - Depends on: none
  - Expected outcome: `ya63p5` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

### Task group 2: confirm the per-item children

- [ ] E-09 CONFIRM znjxom REACHED executed
  - Depends on: none
  - Expected outcome: `znjxom` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-10 CONFIRM t8j7mn REACHED executed
  - Depends on: none
  - Expected outcome: `t8j7mn` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-11 CONFIRM 5jevb2 REACHED executed
  - Depends on: none
  - Expected outcome: `5jevb2` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-12 CONFIRM d2vfp2 REACHED executed
  - Depends on: none
  - Expected outcome: `d2vfp2` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-13 CONFIRM 438gkf REACHED executed
  - Depends on: none
  - Expected outcome: `438gkf` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-14 CONFIRM pdemar REACHED executed
  - Depends on: none
  - Expected outcome: `pdemar` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-15 CONFIRM 33f8tn REACHED executed
  - Depends on: none
  - Expected outcome: `33f8tn` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-16 CONFIRM jy7439 REACHED executed
  - Depends on: none
  - Expected outcome: `jy7439` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-17 CONFIRM syzi9i REACHED executed
  - Depends on: none
  - Expected outcome: `syzi9i` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-18 CONFIRM 94wi2f REACHED executed
  - Depends on: none
  - Expected outcome: `94wi2f` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-19 CONFIRM dwjfu4 REACHED executed
  - Depends on: none
  - Expected outcome: `dwjfu4` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-20 CONFIRM tf8fwt REACHED executed
  - Depends on: none
  - Expected outcome: `tf8fwt` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

- [ ] E-21 CONFIRM 8bhcd3 REACHED executed
  - Depends on: none
  - Expected outcome: `8bhcd3` is under `.aw/records/plans/executed/` with `- Status: executed`.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 2 | `znjxom` | `20261017-trimgap-02-znjxom-restore-behavioral-test-coverage-for-run-analytics-cli-analy.ipd.md` | Backlog `n6h5eg`: restores behavioral test coverage for run_analytics_cli analyze and query leaves. | none |
| 4 | `t8j7mn` | `20261017-trimgap-04-t8j7mn-restore-behavioral-test-coverage-for-run-analytics-taxonomy.ipd.md` | Backlog `aux1f6`: restores behavioral test coverage for run_analytics_taxonomy. | none |
| 5 | `5jevb2` | `20261017-trimgap-05-5jevb2-restore-behavioral-test-coverage-for-run-packet-step-packets.ipd.md` | Backlog `aq04yg`: restores behavioral test coverage for run_packet step packets and outcome envelopes. | none |
| 6 | `d2vfp2` | `20261017-trimgap-06-d2vfp2-restore-behavioral-test-coverage-for-run-analytics-submit-tr.ipd.md` | Backlog `gjmiuw`: restores behavioral test coverage for run_analytics_submit transport, consent and validation. | none |
| 7 | `438gkf` | `20261017-trimgap-07-438gkf-restore-behavioral-test-coverage-for-run-analytics-export.ipd.md` | Backlog `liybkg`: restores behavioral test coverage for run_analytics_export. | none |
| 8 | `pdemar` | `20261017-trimgap-08-pdemar-restore-behavioral-test-coverage-for-migration-complex-coord.ipd.md` | Backlog `x62jok`: restores behavioral test coverage for migration_complex coordinators, Fix Bar, consent gates and setup state machine. | none |
| 9 | `33f8tn` | `20261017-trimgap-09-33f8tn-restore-behavioral-test-coverage-for-engine-py-opt-in-hooks.ipd.md` | Backlog `7df9md`: restores behavioral test coverage for engine.py opt-in hooks, shim customization, managed blocks and lane merge. | none |
| 10 | `jy7439` | `20261017-trimgap-10-jy7439-restore-behavioral-test-coverage-for-lifecycle-fixtures-matr.ipd.md` | Backlog `lzn56i`: restores behavioral test coverage for lifecycle_fixtures matrix runners, registry and isolation. | none |
| 11 | `syzi9i` | `20261017-trimgap-11-syzi9i-restore-behavioral-test-coverage-for-migration-compact-contr.ipd.md` | Backlog `fdyjv6`: restores behavioral test coverage for migration_compact contracts, projections, shim resolution and promotion gates. | none |
| 12 | `94wi2f` | `20261017-trimgap-12-94wi2f-restore-behavioral-test-coverage-for-migration-inventory-dis.ipd.md` | Backlog `igefrj`: restores behavioral test coverage for migration_inventory disposition inventory, shared harnesses and plan-review views. | none |
| 13 | `dwjfu4` | `20261017-trimgap-13-dwjfu4-restore-behavioral-test-coverage-for-clean-delta-adapter-man.ipd.md` | Backlog `otc788`: restores behavioral test coverage for clean_delta adapter manifest, purity, conversion, drift, repair and uninstall. | none |
| 14 | `tf8fwt` | `20261017-trimgap-14-tf8fwt-restore-behavioral-test-coverage-for-run-gates-human-decisio.ipd.md` | Backlog `ziuj5c`: restores behavioral test coverage for run_gates human decision gates. | none |
| 15 | `8bhcd3` | `20261017-trimgap-15-8bhcd3-restore-behavioral-test-coverage-for-run-analytics-telemetry.ipd.md` | Backlog `yqpb7q`: restores behavioral test coverage for run_analytics_telemetry. | none |
| 16 | `ivap17` | `20261017-trimgap-16-ivap17-restore-behavioral-test-coverage-for-run-analytics-wizard-re.ipd.md` | Groups 16, 19, 21, 34, 39, 50 (22 keys): restores the run-analytics wizard, report, findings, config, e2e and privacy test modules with neutral canaries and core markers. | none |
| 17 | `vqr3xq` | `20261017-trimgap-17-vqr3xq-restore-behavioral-test-coverage-for-the-set-executor-worktr.ipd.md` | Groups 17, 20, 24, 28, 29, 31, 33, 35, 41, 43 (41 keys): restores the Set executor, exec-set workflow, host runner and host adapter skill tests, plus residual tests for `SkillPackage.to_dict`, `resource_paths` and `advertises_supported`. | none |
| 18 | `zhoul7` | `20261017-trimgap-18-zhoul7-restore-behavioral-test-coverage-for-check-engine-layout-dep.ipd.md` | Groups 18, 51, 53, 58 (8 keys): restores the layout, dependency-check, dependency-statement-hook, review-decision and doctor version-drift tests, plus residual tests for `_blocking_escalated_finding_ids` and `_on_staged_file`. | none |
| 19 | `78g6ic` | `20261017-trimgap-19-78g6ic-restore-behavioral-test-coverage-for-benchmark-manifest-corp.ipd.md` | Groups 22, 25, 27, 47 (25 keys): restores the benchmark corpus test module plus residual tests for `is_ground_truth_accessible` and `is_critical_class`. | none |
| 20 | `5e7czd` | `20261017-trimgap-20-5e7czd-restore-behavioral-test-coverage-for-layout-migration-litter.ipd.md` | Groups 23, 26 (7 keys): restores the layout-migration, grammar-facet rename and storage companion test modules with per-test core markers. | none |
| 21 | `y4bt1c` | `20261017-trimgap-21-y4bt1c-restore-behavioral-test-coverage-for-agy-cli-surfaces-term-c.ipd.md` | Groups 30, 32, 36, 38, 42, 48, 54, 56 (19 keys): restores the agy CLI surface, Term component, attention stem, renderer boundary, output contract, SIGINT handler and comms tests, plus residual tests for the comms validators, `has_findings` and `reset_signal_ladder`. | none |
| 22 | `9gjvrq` | `20261017-trimgap-22-9gjvrq-restore-behavioral-test-coverage-for-rename-history-selector.ipd.md` | Groups 37, 44, 45, 46, 49, 52, 55, 57, 59, 60 (13 keys): restores the rename, regroup, rename-ledger, research-priority, reference-matcher, selector, readiness-recheck, gate-answer and run-state tests, plus residual tests for `_synthetic_key` and `Resolution.is_unique`. | none |
| 23 | `ya63p5` | `20261017-trimgap-23-ya63p5-restore-the-stranded-run-and-dispatchable-work-tests-of-test.ipd.md` | Group 40 (34 missing names, `render_stream.py`): appends 33 of the missing run-summary tests to `tests/test_run_summary_table.py`, declining one identity-only test. | none |

The children are independent (no child consumes another's output, every child declares `- Item-Dependencies: none`, and no Scope-Paths file is shared), so any order is valid; the table order follows `b1mx2w` group rank. Orders 01 and 03 are unused: no plan on disk carries them.

## Completion criteria (the whole Set is done only when)

- Every one of the 22 run-analytics keys of groups 16, 19, 21, 34, 39 and 50 is reached by a core-marked test and killed by an early-return mutation. Owner: ivap17
- Every one of the 41 Set-execution and host-adapter keys of groups 17, 20, 24, 28, 29, 31, 33, 35, 41 and 43 is reached by a core-marked test and killed by an early-return mutation. Owner: vqr3xq
- Every one of the 8 checker keys of groups 18, 51, 53 and 58 is reached by a core-marked test and killed by an early-return mutation. Owner: zhoul7
- Every one of the 25 benchmark keys of groups 22, 25, 27 and 47 is reached by a core-marked test and killed by an early-return mutation. Owner: 78g6ic
- Every one of the 7 migration and storage keys of groups 23 and 26 is reached by a core-marked test and killed by an early-return mutation. Owner: 5e7czd
- Every one of the 19 output-surface keys of groups 30, 32, 36, 38, 42, 48, 54 and 56 is reached by a core-marked test and killed by an early-return mutation. Owner: y4bt1c
- Every one of the 13 keys of groups 37, 44, 45, 46, 49, 52, 55, 57, 59 and 60 is reached by a core-marked test and killed by an early-return mutation. Owner: 9gjvrq
- 33 of the 34 missing run-summary test names of group 40 pass in `tests/test_run_summary_table.py` under the core tier, with the 34th declined in that plan's deferred section. Owner: ya63p5
- Each per-item child meets its OWN Goal and validation for its own backlog item (not the `q86fxm` key criteria above; for example `znjxom` deliberately adds no core-marked tests). Owner: znjxom, t8j7mn, 5jevb2, d2vfp2, 438gkf, pdemar, 33f8tn, jy7439, syzi9i, 94wi2f, dwjfu4, tf8fwt, 8bhcd3, each for itself.

## Cross-IPD validation

- No two children change the same file: each of the 21 children's `- Scope-Paths:` is disjoint from every other child's, and each child's V-items demand diff evidence for its own declared paths. Owner: ivap17 (its V-06 final `git diff agent_workflows/` and diff evidence), and likewise vqr3xq V-05, zhoul7 V-06, 78g6ic V-02, 5e7czd V-03, y4bt1c V-05, 9gjvrq V-06 and ya63p5 V-01 for their own paths; each per-item child likewise for its own paths.
- The bare core tier still passes with each child's additions: each `q86fxm` child's final V-item pastes the bare `python3 -m pytest` summary line after its own restore (per-item children carry their own equivalent). Owner: ivap17 V-06, vqr3xq V-05, zhoul7 V-06, 78g6ic V-02, 5e7czd V-03, y4bt1c V-05, 9gjvrq V-06, ya63p5 V-02.
- The union of the children's key lists is exactly the 135 keys of `q86fxm` (22 + 41 + 8 + 25 + 7 + 19 + 13 = 135) plus group 40's 34 names; this was checked at authoring against `b1mx2w` `## Rollup mutation results` and is restated in each child's `- Scope:`. Owner: each child for its own list, as above.

## Deferred / out of scope (with reason)

- Core-tier wall time is load-dependent and has been measured both over its 30s budget (36 to 45s, `CORE TIER BUDGET EXCEEDED`, at HEAD `f84c3af26`) and under it (`753 passed in 22.97s` at HEAD `5c427b50c`, during this plan's review). This Set does not fix that; the children keep their own core additions small (about 10s of summed CPU across all eight, mostly per-test markers on expensive files).
  - Carrier: o58dro

## Scope check

- Over-scope: none. This plan touches only itself.
- Under-scope: none. Every group 16 through 60 of `q86fxm` is owned by exactly one child, and every other `trimgap` plan on disk is a row of the table above.

## Required tests / validation

This plan runs no tests. Each child runs its own reach, mutation, bare-suite and sanitizer checks (each per-item child under its own plan): run-analytics keys ivap17; Set-execution and host-adapter keys vqr3xq; checker keys zhoul7; benchmark keys 78g6ic; migration and storage keys 5e7czd; output-surface keys y4bt1c; rename, selector, readiness, gate-answer and run-state keys 9gjvrq; run-summary tests ya63p5.

## Open questions

### OQ-01: Why eight children rather than one per module (44) or one for everything?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: most modules carry one to three keys reached by the same deleted test file as a neighbor module (for example `worktree_lease`, `set_lifecycle` and `set_state` are all reached only by `tests/test_ipd_set_executor.py`), so splitting by module would put one file in several plans. Grouping by the deleted test files that reach the keys gives eight children, each one focused pass, with disjoint Scope-Paths.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep ivap17` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep vqr3xq` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep zhoul7` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep 78g6ic` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep 5e7czd` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep y4bt1c` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep 9gjvrq` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep ya63p5` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep znjxom` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep t8j7mn` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep 5jevb2` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep d2vfp2` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-13 validates E-13
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep 438gkf` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-14 validates E-14
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep pdemar` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-15 validates E-15
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep 33f8tn` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-16 validates E-16
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep jy7439` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-17 validates E-17
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep syzi9i` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-18 validates E-18
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep 94wi2f` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-19 validates E-19
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep dwjfu4` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-20 validates E-20
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep tf8fwt` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-21 validates E-21
  - Required evidence: pasted `ls .aw/records/plans/executed/ -R | grep 8bhcd3` output and its `- Status: executed` line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: the 21 E-items are one uniform orchestration act (confirm a child reached executed), one per child the runner already counts in this Set; each is a single ls/grep check, so the count reflects Set breadth, not conceptual density, and splitting the orchestrator would contradict the one-orchestrator-per-Set rule.

Execute only after explicit human approval (`Status: approved`). This orchestrator performs no work of its own: under `aw oc run` / `aw agy run` it is retired once every child is `executed`. By hand, execute all 21 children (each under its own gate, any order), then confirm each row above, pasting the ACTUAL command output each `V-*` demands. Open questions: OQ-01 is resolved; none block. Scope fence: `- Scope-Paths:` (this plan file only). Commit through `aw commit kn7xtw -- <paths>`; never `git add -A`, never push. Under a runner the runner retires this plan; by hand, `aw ipd finalize kn7xtw` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
