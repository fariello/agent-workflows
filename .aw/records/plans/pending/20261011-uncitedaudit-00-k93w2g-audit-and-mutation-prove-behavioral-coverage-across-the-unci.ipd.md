# IPD: Audit and mutation-prove behavioral coverage across the uncited trim-deleted test files

- Date: 2026-10-11
- Kind: orchestrator
- Concern: Backlog `e486tz`: commit `19313eed` deleted 298 test files; the lost-guard census (`tools/lost_guard_census.py`, plan `oyh28b`) reaches only those a live comment cites, and the rest were declared out of scope there with this item as their carrier. At authoring HEAD `fca848304` the uncited partition is 209 files holding 3,585 removed functions (`python3 tools/lost_guard_census.py --summary`: "Uncited deleted files: 209 files holding 3585 removed functions"; the item's 207 / 3,554 is the census's pinned review baseline). The audit cannot be done by reading (102,815 lines of deleted test source) and cannot be mutation-proven naively (one bare suite run is `201.44s` here), so this Set builds three small instruments, runs them, derives properties from data, mutation-proves a budgeted shortlist with positive controls, and files every gap.
- Scope: Orchestration only: sequence the eight children below and confirm each reaches `executed`. No code, test or record of its own.
- Scope-Paths: .aw/records/plans/pending/20261011-uncitedaudit-00-k93w2g-audit-and-mutation-prove-behavioral-coverage-across-the-unci.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: d726a52ad65c242b8ed20406c3bd86645978472bac3872090f938c7e8a2c51af
- Coverage-Checked: 2026-10-12 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 0
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: k93w2g
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): plan-review complete: APPROVE WITH REVISIONS APPLIED

- 2026-10-12 coverage pass (aw oc run): fingerprint d726a52ad65c, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002 (both fixed; all eight children exist with matching Order, Id, From-Backlog and Item-Dependencies; census re-run at `7028b6f22` reports 209 / 3585; `aw ipd coverage k93w2g` ready).
- 2026-10-11 coverage pass (aw oc run): fingerprint 7a35e51917db, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Answer, reproducibly, which behaviors the 209 uncited `19313eed`-deleted test files guarded that no surviving test now guards, proving "guarded" by mutation with a positive control, and leave every gap as a tracked backlog item.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Children

- [ ] E-01 CONFIRM 1ub8ex REACHED executed
  - Depends on: none
  - Expected outcome: `aw find plans 1ub8ex` shows it under `executed/`.
  - Execution state: pending

- [ ] E-02 CONFIRM nzzu8n REACHED executed
  - Depends on: none
  - Expected outcome: `aw find plans nzzu8n` shows it under `executed/`.
  - Execution state: pending

- [ ] E-03 CONFIRM g55j1e REACHED executed
  - Depends on: none
  - Expected outcome: `aw find plans g55j1e` shows it under `executed/`.
  - Execution state: pending

- [ ] E-04 CONFIRM sk2rbf REACHED executed
  - Depends on: E-02
  - Expected outcome: `aw find plans sk2rbf` shows it under `executed/`.
  - Execution state: pending

- [ ] E-05 CONFIRM 8d0qsg REACHED executed
  - Depends on: E-01, E-02, E-04
  - Expected outcome: `aw find plans 8d0qsg` shows it under `executed/`.
  - Execution state: pending

- [ ] E-06 CONFIRM anzu8q REACHED executed
  - Depends on: E-05
  - Expected outcome: `aw find plans anzu8q` shows it under `executed/`.
  - Execution state: pending

- [ ] E-07 CONFIRM rq3q7v REACHED executed
  - Depends on: E-03, E-06
  - Expected outcome: `aw find plans rq3q7v` shows it under `executed/`.
  - Execution state: pending

- [ ] E-08 CONFIRM xmr5qj REACHED executed
  - Depends on: E-07
  - Expected outcome: `aw find plans xmr5qj` shows it under `executed/`.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `1ub8ex` | `20261011-uncitedaudit-01-1ub8ex-add-a-reproducible-uncited-deleted-file-inventory-to-the-los.ipd.md` | `lost_guard_census.py --uncited [--format json]`: the per-file uncited inventory (funcs, pin annotation, imports and their existence, recreated-at-HEAD). | none |
| 02 | `nzzu8n` | `20261011-uncitedaudit-02-nzzu8n-add-a-deleted-test-replay-harness-that-runs-a-trim-deleted-t.ipd.md` | `tools/deleted_test_replay.py`: run a deleted test blob against HEAD from a temp dir; per-file and per-test verdicts. | none |
| 03 | `g55j1e` | `20261011-uncitedaudit-03-g55j1e-add-a-worktree-isolated-mutation-probe-that-reports-whether.ipd.md` | `tools/mutation_probe.py`: baseline-subtracted mutant verdict in a disposable worktree, with `--extra-test` positive control. | none |
| 04 | `sk2rbf` | `20261011-uncitedaudit-04-sk2rbf-add-a-coverage-differential-that-finds-production-lines-only.ipd.md` | `tools/replay_coverage_diff.py`: production lines only a replayed deleted test reaches, and the surviving tests reaching each function. | `executed:nzzu8n` |
| 05 | `8d0qsg` | `20261011-uncitedaudit-05-8d0qsg-run-the-uncited-file-audit-and-record-each-file-s-verdict-an.ipd.md` | Run the instruments over the population; one verdict per file in a findings doc; grouped candidates. | `executed:1ub8ex`, `executed:nzzu8n`, `executed:sk2rbf` |
| 06 | `anzu8q` | `20261011-uncitedaudit-06-anzu8q-derive-the-asserted-production-property-for-each-lost-guard.ipd.md` | Derive each candidate's asserted property and operator; regression verdicts for replay failures; budgeted mutation shortlist. | `executed:8d0qsg` |
| 07 | `rq3q7v` | `20261011-uncitedaudit-07-rq3q7v-mutation-prove-the-derived-properties-on-a-bounded-probe-bud.ipd.md` | Survivor and control probes per shortlisted property; verdicts `guarded` / `unguarded` / `unprovable` / `import-only`. | `executed:g55j1e`, `executed:anzu8q` |
| 08 | `xmr5qj` | `20261011-uncitedaudit-08-xmr5qj-file-each-unguarded-or-regressed-property-as-grouped-backlog.ipd.md` | File grouped backlog items plus a rollup; owns the whole-Set reconciliation. | `executed:rq3q7v` |

Orders 01, 02 and 03 are mutually independent. They all touch `tools/README.md`, which is not a hazard: the runner isolates each item in its own worktree and merges through the revalidate gate.

## Completion criteria (the whole Set is done only when)

1. Every uncited deleted file of `19313eed` at the measured HEAD carries exactly one audit verdict, and the verdict totals equal the inventory count. The uncited count is a LIVE figure (it moves when docs cite or stop citing a deleted file: 207 at the census baseline, 209 at authoring and at review HEAD `7028b6f22`), so the bar is equality with `tools/lost_guard_census.py --summary` re-run on the same HEAD, never the number 209. [Owner: 8d0qsg E-03; reconciled by xmr5qj E-03 (a)]
2. Every `pass-exclusive` candidate group has a derived property, a classification and (if behavioral) a mutation operator. [Owner: anzu8q E-01; reconciled by xmr5qj E-03 (b)]
3. Every shortlisted behavioral property has a controlled mutation verdict or is listed `triaged-not-mutated` with a reason. [Owner: rq3q7v E-02; reconciled by xmr5qj E-03 (c)]
4. Every non-guarded outcome has a carrier: a filed backlog item or a confirmed live owner. [Owner: xmr5qj E-02; reconciled by xmr5qj E-03 (d)]
5. The Set changed no production code and no test file other than the four instrument tests. [Owner: xmr5qj E-03 (e)]

## Cross-IPD validation

- The inventory population used by Order 05 equals the census `--summary` uncited count on the same HEAD. [Owner: 8d0qsg V-01]
- Order 04 replays through Order 02's `replay_file` with a `python_prefix` hook rather than a second replay implementation. [Owner: sk2rbf E-04]
- Order 07 uses Order 06's operators and positive controls verbatim. [Owner: rq3q7v E-02]

## Deferred / out of scope (with reason)

- Writing replacement tests and fixing regressions found: each filed item's own work.
  - Carrier: 5slmvq, 9qvfie
- The cited deleted files: handled by the census citation axes and plan `oyh28b`'s filed items.
  - Carrier-Evidence: .aw/records/plans/executed/20260930-xvp5vx-01-oyh28b-build-a-reproducible-lost-guard-census-over-the-two-suite-tr.ipd.md
- Tests removed from MODIFIED files (`19313eed` modified 20 test files, removing 1,412 functions = 7,402 DM-multiset minus 5,990 D-only): the item's subject is the deleted files.
  - Carrier-Declined: Outside backlog `e486tz`'s stated population ("the 207 trim-deleted test files"); not fabricated into scope here. The census already prints the modified-file count, so the population is visible.

## Scope check

- Over-scope: none. This plan contributes no code, test or record of its own.
- Under-scope: modified-file removals declined above with reason.

## Required tests / validation

This plan runs no tests. Each instrument child (`1ub8ex`, `nzzu8n`, `g55j1e`, `sk2rbf`) runs the bare suite; `xmr5qj` performs the whole-Set reconciliation.

## Open questions

### OQ-01: Is building three instruments justified versus a manual read?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes on measurement: 102,815 lines across 209 files cannot be read and judged reliably by hand, the census's whole value is reproducibility (its docstring), and each instrument is a small stdlib script with behavioral tests. A reviewer who prefers a narrower Set can drop Order 04, at the cost of every mutant running the ~200 s full selection.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw find plans 1ub8ex` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw find plans nzzu8n` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw find plans g55j1e` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw find plans sk2rbf` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `aw find plans 8d0qsg` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `aw find plans anzu8q` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `aw find plans rq3q7v` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `aw find plans xmr5qj` showing it under `executed/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval of each child before execution. At this review, children `1ub8ex`, `nzzu8n` and `g55j1e` are `reviewed` and the other five are `to-review`: each still needs its own `/plan-review` and approval, which reviewing this orchestrator does not supply. The runner retires this orchestrator once every child is `executed`; executing by hand, confirm each child in Order and finish with `aw ipd finalize`, never a hand `git mv`. This plan writes no code; never push. Backlog `e486tz` is set `graduated` by the runner when the Set is authored.
