# IPD: Carry the uncited trim-audit carrier-needed outcomes to resolution

- Date: 2026-10-16
- Kind: orchestrator
- Concern: Backlog `9qvfie` is the rollup carrier for 770 carrier-needed outcomes of the uncited trim-deleted test audit (findings `hpjj44`, Set `uncitedaudit`): 1 `unprovable` property (`PROP-02`), 764 `triaged-not-mutated` items (747 production keys and 17 `pass-shared` test files), 1 `replay-env-limited` file and 4 `recreated` files with missing test names. None of them has a guard verdict yet: the keys were never probed because the earlier budget went to two full-selection survivor runs (`hpjj44` `## Mutation totals`), and two of the outcomes turn out to be fixable directly (the `PROP-02` module and the env-limited module both pass at HEAD with at most a one-line fixture fix and superseded-contract assertions in three tests). This Set restores what can be restored, measures and probes the rest at one HEAD, and files every remaining gap.
- Scope: Orchestration only: sequence the six children below and confirm each reaches `executed`. No code, test or record of its own.
- Scope-Paths: .aw/records/plans/pending/20261016-trimcarry-00-e5jijr-carry-the-uncited-trim-audit-carrier-needed-outcomes-to-reso.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: 9206f2fa887b74a99c4bcaf92fbba2ab7a16618802ba0abad3dca9d274170826
- Coverage-Checked: 2026-10-16 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: chore
- Priority: low
- From-Backlog: 9qvfie
- Set: trimcarry
- Order: 0
- Highest E allocated: 06
- Author: opencode
- Id: e5jijr

## Workflow history
- 2026-10-17 executed (aw agy run model=Gemini-3.8-Flash-High): RETIRED as the orchestrator rollup step of a runner Set completion, not executed by an agent: every child of Set trimcarry reached executed, so the runner (run run-20261016T221501Z-3469718) retired this Order-0 plan as bookkeeping. Its own E-*/V-* items were NOT performed; the runner superseded them by enforcing the ordering, the isolation and the per-child merge gate. Justifying children: 24h56i, x9z0ve, 8dyt88, we3kkb, rf1xxr, z2xs98.
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002

- 2026-10-16 coverage pass (aw oc run): fingerprint 9206f2fa887b, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-16 coverage pass (aw oc run): fingerprint 8065c13063c0, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready orchestrator graduating backlog 9qvfie.

## Goal

Every one of the 770 outcomes rolled into `9qvfie` ends either closed by evidence (a restored passing test, a measured `guarded` verdict, a recorded deliberate removal) or carried by a specific live backlog item.

## Detailed Implementation Checklist (TODO)


> Its own E-*/V-* items were NOT performed; the runner superseded them by enforcing the ordering, the isolation and the per-child merge gate.

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Children

- [ ] E-01 CONFIRM 24h56i REACHED executed
  - Depends on: none
  - Expected outcome: `aw find plans 24h56i` shows it under `executed/`.
  - Execution state: pending

- [ ] E-02 CONFIRM x9z0ve REACHED executed
  - Depends on: none
  - Expected outcome: `aw find plans x9z0ve` shows it under `executed/`.
  - Execution state: pending

- [ ] E-03 CONFIRM 8dyt88 REACHED executed
  - Depends on: E-01, E-02
  - Expected outcome: `aw find plans 8dyt88` shows it under `executed/`.
  - Execution state: pending

- [ ] E-04 CONFIRM we3kkb REACHED executed
  - Depends on: E-03
  - Expected outcome: `aw find plans we3kkb` shows it under `executed/`.
  - Execution state: pending

- [ ] E-05 CONFIRM rf1xxr REACHED executed
  - Depends on: E-03
  - Expected outcome: `aw find plans rf1xxr` shows it under `executed/`.
  - Execution state: pending

- [ ] E-06 CONFIRM z2xs98 REACHED executed
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: `aw find plans z2xs98` shows it under `executed/`.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `24h56i` | `20261016-trimcarry-01-24h56i-restore-the-deleted-benchmark-runners-and-reports-tests-and.ipd.md` | Restore `tests/test_benchmark_runners_reports.py` unchanged and settle `PROP-02` with a narrowed mutation probe. | none |
| 02 | `x9z0ve` | `20261016-trimcarry-02-x9z0ve-restore-the-env-limited-run-evidence-completion-tests-with-a.ipd.md` | Restore `tests/test_run_evidence_completion.py` with an id6 spec lookup and cited contract updates in three tests. | none |
| 03 | `8dyt88` | `20261016-trimcarry-03-8dyt88-re-measure-surviving-reach-for-every-rollup-key-and-pass-sha.ipd.md` | Create the Set findings doc; full-suite coverage baseline at HEAD; reach class for all 747 keys; re-diff the 17 pass-shared and 4 recreated files. | `executed:24h56i`, `executed:x9z0ve` |
| 04 | `we3kkb` | `20261016-trimcarry-04-we3kkb-classify-each-test-name-the-recreated-files-did-not-restore.ipd.md` | Classify each of the 136 missing recreated test names (removed, moved, pin, intended-change, regression, gap, covered). | `executed:8dyt88` |
| 05 | `rf1xxr` | `20261016-trimcarry-05-rf1xxr-mutation-probe-the-reached-rollup-properties-on-a-bounded-bu.ipd.md` | Final verdict for every key: non-probe classes from reach, then budgeted survivor plus control probes. | `executed:8dyt88` |
| 06 | `z2xs98` | `20261016-trimcarry-06-z2xs98-file-grouped-backlog-items-for-every-rollup-gap-and-reconcil.ipd.md` | Group, dedupe and file every remaining gap; whole-Set reconciliation of the 770 outcomes. | `executed:24h56i`, `executed:x9z0ve`, `executed:8dyt88`, `executed:we3kkb`, `executed:rf1xxr` |

Orders 01 and 02 are independent. Orders 04 and 05 both append to the same findings doc; the runner isolates each item in its own worktree and merges through the revalidate gate, so that is not a hazard.

## Completion criteria (the whole Set is done only when)

1. `PROP-02` (`compute_aggregate_metrics`) has a measured mutation verdict against a committed surviving test, replacing `unprovable`. Owner: 24h56i (E-03).
2. `tests/test_run_evidence_completion.py` is restored and passing, closing the `replay-env-limited` outcome. Owner: x9z0ve (E-02, E-03).
3. Every one of the 747 keys has a reach class at one HEAD, and every one of the 17 pass-shared files has a re-diff verdict. Owner: 8dyt88 (E-03, E-04).
4. Every missing name of the 4 recreated files has one evidence-backed class. Owner: we3kkb (E-02).
5. Every one of the 747 keys has a final verdict or `budget-exhausted`. Owner: rf1xxr (E-01, E-02).
6. Every remaining gap is carried by a filed or `owned-confirmed` backlog item, and the reconciliation totals 770. Owner: z2xs98 (E-02, E-03).
7. The Set changed no production code and no test file other than the two restored modules. Owner: z2xs98 (E-03 (c)).

## Cross-IPD validation

- Order 03's baseline is measured AFTER Orders 01 and 02 land, so their restored modules count as surviving reach. Owner: 8dyt88 (V-02).
- Order 05's key set equals Order 03's `keys.txt` (747). Owner: rf1xxr (V-01).
- Order 04 consumes Order 03's `## Recreated re-diff` for its `gap` versus `covered-by-shared-reach` rule. Owner: we3kkb (E-02).
- Order 06's reconciliation cites Order 01's `PROP-02` verdict and any suspected regression Order 02 recorded. Owner: z2xs98 (E-01, E-03).

## Deferred / out of scope (with reason)

- Writing replacement tests or fixing regressions for the gaps Order 06 files: each filed item's own work.
  - Carrier: lrnh5f, n6h5eg, 2mcirl, aux1f6, aq04yg, gjmiuw, liybkg, x62jok, 7df9md, lzn56i, fdyjv6, igefrj, otc788, ziuj5c, yqpb7q, q86fxm
- `PROP-01` (`_run_migrate_layout`): carried by backlog `5slmvq` and its pending plan `1ue3kr`, not by `9qvfie`.
  - Carrier: 1ue3kr
  - Carrier-Evidence: .aw/records/plans/executed/20261016-5slmvq-01-1ue3kr-restore-behavioral-test-coverage-for-run-migrate-layout.ipd.md
- Changing `pyproject.toml` `testpaths` to include the restored modules: routine-gate composition is a maintainer decision.
  - Carrier-Declined: deliberate non-goal; restored modules run in `make test-all` and release-review.

## Scope check

- Over-scope: none. This plan contributes no code, test or record of its own.
- Under-scope: none; the four outcome classes of `9qvfie` map to Orders 01 (unprovable), 02 (replay-env-limited), 03 and 05 (triaged-not-mutated), and 04 (recreated), with Order 06 carrying the residue.

## Required tests / validation

This plan runs no tests. Orders 01 (`24h56i`) and 02 (`x9z0ve`) run the restored modules and the bare suite; Order 06 (`z2xs98`) performs the whole-Set reconciliation and footprint check.

## Open questions

### OQ-01: Why not one plan?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: The work has three distinct deliverable kinds (two test restorations, a measurement record, a filing pass), long-running measurements that must happen in a fixed order on one HEAD, and two independent restorations that can land first. Separate children keep each pass reviewable and let the runner merge the restorations before the baseline is taken, which Order 03 depends on.

### OQ-02: The backlog body's details differ from the findings doc in two places; which governs?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: The findings doc `hpjj44`, which the backlog item names as the source ("details in hpjj44 ## Triaged not mutated"). The 17 `pass-shared` names in the backlog body include 12 that never existed in git history (`git log --all -- tests/test_cli_commands.py` is empty), and its fourth missing lane-manifest name does not exist at `19313eed^`. Orders 03 and 04 record both discrepancies; the item's requirement (carry these outcomes) is unchanged.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `aw find plans 24h56i` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `aw find plans x9z0ve` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `aw find plans 8dyt88` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `aw find plans we3kkb` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `aw find plans rf1xxr` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `aw find plans z2xs98` output showing an `executed/` path.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) of this plan and each child. EXECUTION CONTRACT: all open questions are resolved. This plan performs no work of its own; each child carries its own scope fence, test evidence and path-scoped `aw commit`. Scope fence: `- Scope-Paths:` declares only this plan; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. Paste ACTUAL output for every confirmation; never claim a child executed that `aw find plans` does not show under `executed/`. Never push. Under `aw oc run` / `aw agy run` the runner retires this orchestrator once every child is `executed`; by hand, finalize it through `aw ipd finalize` after every `V-*` is `pass`.
