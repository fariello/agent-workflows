# IPD: Probe the 319 budget-exhausted rollup keys and carry every unguarded one to a restore owner

- Date: 2026-10-17
- Kind: orchestrator
- Concern: Backlog `lrnh5f` carries 319 production keys whose mutation verdict is `budget-exhausted`: Set `trimcarry` Order 05 (`rf1xxr`) stopped starting probes when its cumulative wall time reached the 10,800s cap (10833.66s, `b1mx2w` `## Rollup mutation totals`), after spending most of it on four keys with whole-file selections. Until each key is probed, nobody knows whether the surviving suite would catch a broken return in it, and so which deleted tests (from the suite trim `19313eed`) are worth restoring.
- Scope: Orchestration only: sequence the five children below and confirm each reaches `executed`. No code, test or record of its own.
- Scope-Paths: .aw/records/plans/**/20261017-trimprobe-00-roi8f1-probe-the-319-budget-exhausted-rollup-keys-and-carry-every-u.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: 3e5e837490288733d9267c48ab578ef659c0bc9a7a6d641b9ef6f3a610b6260c
- Coverage-Checked: 2026-10-17 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: chore
- Priority: low
- From-Backlog: lrnh5f
- Set: trimprobe
- Order: 0
- Highest E allocated: 05
- Author: opencode
- Id: roi8f1

## Workflow history
- 2026-10-17 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002

- 2026-10-17 coverage pass (aw oc run): fingerprint 3e5e83749028, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-17 coverage pass (aw oc run): fingerprint 021108d4a893, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-17 to-review (opencode): authored review-ready orchestrator graduating backlog `lrnh5f`.
- 2026-10-17 draft (opencode): created.

## Goal

Every one of the 319 keys ends with a final verdict recorded in the Set findings doc: a measured guard verdict (`guarded`, `unguarded`, `unprovable`) for every key a probe plan started, a no-probe verdict (`key-gone`, `unguarded-unreached`, `unprovable`) from Order 01, or, only for a key a probe plan could not start before its 10,800s cap, `budget-exhausted` with the cumulative time. Every key that is not carrier-free (anything but `guarded` or `key-gone`, a residual `budget-exhausted` included) is carried by a live backlog item that names the deleted test file to mine. Order 01 (`g00ljy`) records a `### Capacity warning` when its `P3` estimate exceeds 7,200s, so any expected residue is visible before Orders 02 and 03 run.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Children

- [ ] E-01 CONFIRM g00ljy REACHED executed
  - Depends on: none
  - Expected outcome: `aw find plans g00ljy` shows it under `executed/`.
  - Execution state: pending

- [ ] E-02 CONFIRM lictgf REACHED executed
  - Depends on: E-01
  - Expected outcome: `aw find plans lictgf` shows it under `executed/`.
  - Execution state: pending

- [ ] E-03 CONFIRM f4pbs5 REACHED executed
  - Depends on: E-02
  - Expected outcome: `aw find plans f4pbs5` shows it under `executed/`.
  - Execution state: pending

- [ ] E-04 CONFIRM pr6lo9 REACHED executed
  - Depends on: E-03
  - Expected outcome: `aw find plans pr6lo9` shows it under `executed/`.
  - Execution state: pending

- [ ] E-05 CONFIRM b83dpg REACHED executed
  - Depends on: E-04
  - Expected outcome: `aw find plans b83dpg` shows it under `executed/`.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `g00ljy` | `20261017-trimprobe-01-g00ljy-re-measure-head-reach-for-the-319-budget-exhausted-keys-and.ipd.md` | Create the Set findings doc; HEAD coverage baseline; reach class, operator check, control file, cost estimate and partition (`P2`/`P3`/`P4` or a no-probe verdict) for all 319 keys. | none |
| 02 | `lictgf` | `20261017-trimprobe-02-lictgf-mutation-probe-the-budget-exhausted-keys-with-small-survivin.ipd.md` | Probe the `P2` (cheapest reached) keys with node-id selections, file-level fallback and positive control under a 10,800s cap. | `executed:g00ljy` |
| 03 | `f4pbs5` | `20261017-trimprobe-03-f4pbs5-mutation-probe-the-budget-exhausted-keys-with-large-survivin.ipd.md` | Probe the `P3` (most-reached) keys the same way under its own cap. | `executed:g00ljy`, `executed:lictgf` |
| 04 | `pr6lo9` | `20261017-trimprobe-04-pr6lo9-mutation-probe-the-subprocess-only-budget-exhausted-keys.ipd.md` | Probe the `P4` subprocess-only keys with candidate-file selections, control, and a budgeted full-suite fallback. | `executed:g00ljy`, `executed:f4pbs5` |
| 05 | `b83dpg` | `20261017-trimprobe-05-b83dpg-file-restore-backlog-items-for-every-non-guarded-probed-key.ipd.md` | Group, dedupe and file `trimgap` restore items for every non-guarded key; reconcile all 319. | `executed:g00ljy`, `executed:lictgf`, `executed:f4pbs5`, `executed:pr6lo9` |

Orders 02 to 04 each append to the same findings doc; they are chained so their sections land in a fixed order, and the runner isolates each in its own worktree.

## Completion criteria (the whole Set is done only when)

1. All 319 keys have a HEAD-current reach class and a partition or no-probe final verdict. Owner: g00ljy (E-03, E-04).
2. Every `P2` key has a final verdict from a preflighted selection. Owner: lictgf (E-02, E-03).
3. Every `P3` key has a final verdict from a preflighted selection. Owner: f4pbs5 (E-02, E-03).
4. Every `P4` key has a final verdict whose reason names the deciding selection. Owner: pr6lo9 (E-02, E-03).
5. Every non-carrier-free key is carried by a filed or `owned-confirmed` backlog item, and the reconciliation totals 319. Owner: b83dpg (E-02, E-03).
6. The Set changed no production code and no test file. Owner: b83dpg (E-03 (c)).

## Cross-IPD validation

- The 319-key input of Order 01 equals the `budget-exhausted` rows of `b1mx2w`. Owner: g00ljy (V-01).
- The `P2` + `P3` + `P4` row counts in `## Budget probe results` equal the partition counts of `## Probe queue`. Owner: pr6lo9 (V-01) for `P2`/`P3` presence, b83dpg (E-03 (a)) for the total.
- No `unguarded` verdict rests on a selection that failed preflight or on a narrowed subprocess-only guess. Owner: lictgf (V-02), f4pbs5 (V-02), pr6lo9 (V-02).

## Deferred / out of scope (with reason)

- Writing the restored behavioral tests for keys found unguarded: the backlog items Order 05 files own that work, because the target keys and assertions are unknown until the probes run.
  - Carrier: b83dpg
- Changing `tools/mutation_probe.py` (for example to accept an argfile or a node-id list file): not needed to complete the probes, and a tool change would invalidate comparability with `rf1xxr`'s verdicts mid-measurement.
  - Carrier-Declined: deliberate non-goal; the plans pass explicit arguments and preflight instead.

## Scope check

- Over-scope: none. This plan contributes no code, test or record of its own.
- Under-scope: none. The backlog remedy's probe half maps to Orders 01 to 04; its restore half is carried by Order 05's filed items.

## Required tests / validation

This plan runs no tests. The whole-Set measurement is the 319-key reconciliation, performed by b83dpg (E-03), from verdicts produced by g00ljy, lictgf, f4pbs5 and pr6lo9.

## Open questions

### OQ-01: Does the Set restore tests itself, or only probe and file?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: probe and file. The backlog remedy says "probe unprobed keys ..., then restore killed behavioral test coverage". Which keys need restoring is the probe's output, so a review-ready restore plan cannot be written now; Order 05 (`b83dpg`) files a per-module restore item for each non-guarded group, each of which graduates to a concrete restore plan like the sibling `trimgap` plans `syzi9i` and `33f8tn`. This repeats how Set `trimcarry` (`z2xs98`) carried its gaps.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw find plans g00ljy` output showing the `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw find plans lictgf` output showing the `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw find plans f4pbs5` output showing the `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw find plans pr6lo9` output showing the `executed/` path.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `aw find plans b83dpg` output showing the `executed/` path.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Paste the ACTUAL `aw find plans <id6>` output into each `V-*`; never record a child as executed that you did not observe there. Scope fence: `- Scope-Paths:` declares only this plan; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. This plan performs no work of its own: execute the children in Order (01 to 05), each under its own execution contract, and confirm each reaches `executed`. Commit only this plan's own lifecycle changes, path-scoped through the tooling (`aw commit <this plan> -- <this plan path>` or the lifecycle verb), never `git add -A`, never push. Under a runner, the runner retires this orchestrator once every child is `executed`; in an unmanaged run, finalize it with `aw ipd finalize` only after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
