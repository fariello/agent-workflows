# IPD: Prune, consolidate and speed up the test suite to a full retained run under 2 minutes without losing regression detection

- Date: 2026-10-16
- Kind: orchestrator
- Concern: Prompt `4ul37x` (Set `testprune`). Measured 2026-10-16 (research `7ry5kv`, `offdhr`): the full suite is 8794 tests taking 565s on 6 workers, 1922 of them parametrize cases from 92 functions (one function has 900 cases), with dozens of structure-pin candidates and two `doctor` conformance tests alone taking 118s and 64s. The maintainer asked to prune tests that do not check FUNCTION, eliminate change-freezing and marginal tests, merge and speed up the rest, and keep regression detection intact; the prompt targets a full retained run under 2 minutes.
- Scope: Orchestrate five children in strict order: (01) measurement tooling and decision table; (02) delete structure/name/architecture pins; (03) consolidate duplicates, marginal and combinatorial tests; (04) speed up to under 120s; (05) prove nothing was lost (coverage parity, mutation spot-check, flakes, final numbers). Runs after `hguae9` (Set `testtier`) so the `core` marker exists and is protected. Orchestration only.
- Scope-Paths: .aw/records/plans/pending/20261016-testprune-00-8wfzb5-prune-consolidate-and-speed-up-the-test-suite-to-a-full-reta.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: 153a062252c4516c10eb91dd738ba25a83ddee5a5c792aa03cd5f10046bdd40c
- Coverage-Checked: 2026-10-16 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: chore
- Priority: high
- Set: testprune
- Order: 0
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8wfzb5
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): status set to reviewed
- 2026-10-16 coverage pass (aw oc run): fingerprint 153a062252c4, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-16 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004
- 2026-10-16 to-review (aw set): authored from prompt 4ul37x (Set testprune)

- 2026-10-16 coverage pass (aw oc run): fingerprint b66a93808155, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-16 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The full retained suite runs in under 2 minutes on 6 workers, every remaining test proves behavior, and union line and branch coverage of `agent_workflows/` does not drop (each lost line restored or justified), with a mutation spot-check showing deletions lost no detection.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

THIS IS AN ORCHESTRATOR AND ITS ITEMS ARE ORCHESTRATION ONLY. Each item confirms one child reached `executed` and reads that child's own evidence; none produces an artifact.

### Task group 1: sequence and verify the Set

- [ ] E-01 CONFIRM qqrgv3 REACHED executed
  - Depends on: none
  - Expected outcome: `qqrgv3` is in `executed/`, and its own V-items record: Per-test line+branch coverage tooling (in-process and subprocess contexts) and the keep/consolidate/speed-up/delete decision table.
  - Execution state: pending
- [ ] E-02 CONFIRM tv72xy REACHED executed
  - Depends on: E-01
  - Expected outcome: `tv72xy` is in `executed/`, and its own V-items record: Delete tests that pin code structure, names or architecture; record each deletion.
  - Execution state: pending
- [ ] E-03 CONFIRM 83nnyn REACHED executed
  - Depends on: E-02
  - Expected outcome: `83nnyn` is in `executed/`, and its own V-items record: Consolidate duplicate, marginal and combinatorial tests and shared fixtures without losing a line or branch.
  - Execution state: pending
- [ ] E-04 CONFIRM c8bfp9 REACHED executed
  - Depends on: E-03
  - Expected outcome: `c8bfp9` is in `executed/`, and its own V-items record: Speed up slow tests and fixtures; full retained suite under 120s.
  - Execution state: pending
- [ ] E-05 CONFIRM vgus66 REACHED executed
  - Depends on: E-04
  - Expected outcome: `vgus66` is in `executed/`, and its own V-items record: Prove: coverage parity, mutation spot-check, flake check, final measurements, CHANGELOG.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `qqrgv3` | `20261016-testprune-01-qqrgv3-build-the-test-classification-and-per-test-coverage-tooling.ipd.md` | Per-test line+branch coverage tooling (in-process and subprocess contexts) and the keep/consolidate/speed-up/delete decision table | executed:hguae9 |
| 02 | `tv72xy` | `20261016-testprune-02-tv72xy-delete-tests-that-pin-code-structure-names-or-architecture-r.ipd.md` | Delete tests that pin code structure, names or architecture; record each deletion | executed:qqrgv3 |
| 03 | `83nnyn` | `20261016-testprune-03-83nnyn-consolidate-duplicate-marginal-and-combinatorial-tests-into.ipd.md` | Consolidate duplicate, marginal and combinatorial tests and shared fixtures without losing a line or branch | executed:tv72xy |
| 04 | `c8bfp9` | `20261016-testprune-04-c8bfp9-speed-up-the-slowest-tests-and-shared-fixtures-so-the-retain.ipd.md` | Speed up slow tests and fixtures; full retained suite under 120s | executed:83nnyn |
| 05 | `vgus66` | `20261016-testprune-05-vgus66-prove-the-pruned-suite-still-catches-regressions-with-covera.ipd.md` | Prove: coverage parity, mutation spot-check, flake check, final measurements, CHANGELOG | executed:c8bfp9 |

## Completion criteria (the whole Set is done only when)

- Full retained suite median wall under 120s on 6 workers (three warm runs), OR the miss recorded with the remaining over-2s tests and their justifications for a maintainer decision (`c8bfp9` OQ-02); assertions are never weakened and tests never deleted to hit the number. Owner: c8bfp9 (measured), vgus66 (final measurement)
- Union line and branch coverage of `agent_workflows/` does not drop below the baseline `qqrgv3` records at its execution (post-`hguae9` main, so core markers and any tests `hguae9` added are in the baseline); every lost line or branch restored or justified. Owner: vgus66
- Mutation spot-check of at least 20 sampled deletions or consolidations plus every defect-citing one, all caught after any restorations (each restoration shown fail-then-pass). Owner: vgus66
- No retained test pins code structure, names or architecture except a recorded KEEP with its reason. Owner: tv72xy
- Every deletion recorded with node id, category and reason in the decision-table research. Owner: qqrgv3 (creates the table), tv72xy and 83nnyn (append their rows), vgus66 (finalizes counts)
- No flake: three randomized full runs and one serial run pass, or each flake dispositioned. Owner: vgus66
- CHANGELOG line and the Set's final report research record. Owner: vgus66

## Cross-IPD validation

- The core tier from `hguae9` keeps every module covered after pruning: checked by `vgus66`. Owner: vgus66

## Deferred / out of scope (with reason)

- Changing which tests are `core`: owned by plan `hguae9`.
  - Carrier: hguae9

## Scope check

- Over-scope: none.
- Under-scope: none; every whole-Set criterion names an owning child.

## Required tests / validation

This plan runs no tests; the whole-Set measurement is performed by `vgus66`.

## Open questions

### OQ-01: Can the baseline per-test numbers drive deletions?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved 2026-10-16: no. Research `offdhr` records that its per-test contexts were a measurement artifact (missed contexts under Python 3.14 and in subprocesses); child `qqrgv3` re-measures with a per-test-id context plugin and its table supersedes them.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: `qqrgv3`'s path in `executed/` and its V-items' pasted results quoted.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: `tv72xy`'s path in `executed/` and its V-items' pasted results quoted.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: `83nnyn`'s path in `executed/` and its V-items' pasted results quoted.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: `c8bfp9`'s path in `executed/` and its V-items' pasted results quoted.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: `vgus66`'s path in `executed/` and its V-items' pasted results quoted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Orchestration only: run with `aw oc run testprune` after `hguae9` executes and after review and approval of every child; each child runs in its own isolated worktree, and child `qqrgv3`'s `executed:hguae9` dependency makes the runner hold the Set (`dependency-blocked`) until then. This plan carries no work of its own: every completion criterion above names an owning child. Under the runner, the orchestrator is retired to `executed` automatically once every child is `executed`; executed by hand, perform E-01..E-05 in order (each confirms one child), paste each child's quoted evidence into its V-item (never claim a result you did not read), then run `aw ipd lint --phase pre-transition` and `aw ipd finalize 8wfzb5`, never a hand `git mv`. Commit only via `aw commit 8wfzb5 -- <this plan>`. Never push or tag.
