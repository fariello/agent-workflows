# IPD: Sweep pending and reusable plans against the writing standard

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-08 to R-10 require a one-time proofread of every plan in `.aw/records/plans/pending/` and `reusable/`. Approved plans keep their approval (MD-4), so for a plan in `reviewed`, `approved`, or `auto-approved` the sweep must not touch the inputs of `ipd_lifecycle.frozen_region_digest` (`- Scope-Paths:` and every E-item and V-item action block), because changing them makes `plan_readiness.review_staleness_index` report `substantive-edit`. Plans that a live run is executing or has queued are skipped (R-10). At authoring time Set `revsteps` was executing under `aw agy run`.
- Scope: Proofread every non-skipped plan in `pending/` and `reusable/` at execution time, limited to text outside the frozen region for reviewed or approved plans; add diagrams where requirement 12 applies; append one `## Workflow history` line per changed plan. EXCLUDES terminal plan directories, this Set's own plans other than to fix dashes and diagrams in prose, and any metadata, checkbox, `Execution state:`, `Result:`, or `Observed evidence:` change.
- Scope-Paths: .aw/records/plans/pending/, .aw/records/plans/reusable/, .aw/records/walkthroughs/
- Item-Dependencies: executed:g4719s, executed:gzhw9c, executed:k2x0yl, executed:e4n4p3, executed:sfez3e, executed:uog8nc
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Backlog: qph7c5
- From-Spec: ecmw83
- Set: writestd
- Order: 9
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 381ml6

## Workflow history
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Bring every live plan up to the writing standard once, without staling any review or disturbing any run.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline

- [ ] E-01 Record the baseline: `aw check all` summary, `aw ipd lint` over `pending/` and `reusable/`, `aw runners --once --json` output, and for every plan its status and `ipd_lifecycle.frozen_region_digest` (compute with `python3 -c` reading each file).
  - Depends on: none
  - Expected outcome: the baseline and the digest table are recorded.
  - Execution state: pending

### Task group 2: sweep

- [ ] E-02 Before each plan, re-run `aw runners --once --json`. Skip the plan if it is the current `id6` of any runner or belongs to the Set of a running runner whose queue includes it; record the skip and reason. Otherwise proofread it per the standard. For a plan in `reviewed`, `approved`, or `auto-approved`, edit only text outside `- Scope-Paths:` and outside every E-item and V-item action block (Goal, Findings, conventions, Proposed changes, Deferred, Scope check, Required tests, Spec sync, Open questions prose, Child IPDs table prose, gate prose), and list any defect left inside the frozen region in the walkthrough. For other plans edit any prose, keeping E/V ids, dependencies, and metadata unchanged. Add a diagram where requirement 12 applies (a Set's child dependency flow is a common case).
  - Depends on: E-01
  - Expected outcome: every non-skipped plan has been proofread.
  - Execution state: pending

- [ ] E-03 Append to each changed plan's `## Workflow history` the line `- <date> proofread (<agent/model>): per technical-artifact-writing standard (spec ecmw83); meaning unchanged; frozen region untouched`, dropping the last clause for plans below `reviewed`.
  - Depends on: E-02
  - Expected outcome: each changed plan carries the line.
  - Execution state: pending

- [ ] E-04 Recompute `frozen_region_digest` for every swept plan in `reviewed`, `approved`, or `auto-approved` and compare it with the E-01 table. Any mismatch: revert that plan's edits inside the frozen region and repeat.
  - Depends on: E-03
  - Expected outcome: every such digest equals its baseline.
  - Execution state: pending

- [ ] E-05 Run `aw ipd lint` over `pending/` and `reusable/` and confirm no plan changed disposition and no new `review may be stale` advisory appears (spec `ecmw83` AC-07).
  - Depends on: E-04
  - Expected outcome: dispositions unchanged; no new staleness advisory.
  - Execution state: pending

### Task group 3: report

- [ ] E-06 Write `.aw/records/walkthroughs/<date>-writestd-09-plan-sweep-walkthrough.md`: plans swept, plans skipped with reasons, diagrams added, frozen-region defects left unfixed, `Unresolved` annotations. If any plan was skipped or any frozen-region defect was left, file one backlog item with `aw backlog new --set writestd --work-kind followup --priority medium` listing them.
  - Depends on: E-05
  - Expected outcome: the walkthrough exists, and a follow-up backlog item exists when anything was skipped or left.
  - Execution state: pending

- [ ] E-07 Run `aw check all`, compare with the E-01 baseline, run the routine gate, and commit.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: no new `aw check` error; the bare suite passes; the commit holds only swept artifacts and the report.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Read `.aw/system/workflows/standards/technical-artifact-writing.md` in full before E-02; apply its "Proofreading procedure" section.
- A writing correction never changes scope, obligations, status, approval, identity, or provenance (standard "Purpose and scope"; spec `ecmw83` R-08).
- Status and history are owned by `aw specs`, `aw backlog`, and `aw ipd`; do not hand-edit status lines.
- Report sweep results in a walkthrough under `.aw/records/walkthroughs/`.
- `ipd_lifecycle.frozen_region_digest` covers `Scope-Paths` and each E/V action block via `ipd_lint.leaf_action_blocks`; prose sections are outside it (its docstring: prose sections are outside the requirement set).
- `plan_readiness.review_staleness_index` reports `substantive-edit` when that digest changes since the last `plan-review:` commit.

## Findings

- This plan runs after the spec and backlog sweeps so a plan's citations of spec sections are checked against the proofread specs.
- The runner's isolated worktree would merge the sweep's edits back through the merge gate; a plan executing at the same time in another lane would conflict on its own file, which is why R-10 skips it.

## Proposed changes (ordered, validatable)

1. Baseline with digests (E-01).
2. Sweep with live-run skip (E-02, E-03).
3. Prove digests and lint unchanged (E-04, E-05).
4. Report, check, gate, commit (E-06, E-07).

## Deferred / out of scope (with reason)

- Plans skipped because they were in a live run: proofread when they are next revised; E-06 files a follow-up backlog item listing them.
  - Carrier: 381ml6

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`aw ipd lint`, the digest comparison in V-04, `aw check all`, the bare suite.

## Spec / documentation sync

N/A: plans only; no spec contract changes.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the four outputs, the digest table included.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the per-plan list (proofread or skipped with reason) and `git diff --stat` per plan.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff` of the history sections.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the before and after digest table with a match column, every row `match`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `aw ipd lint --agent` summary beside the E-01 one.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste its path and its tables, and the `aw backlog new` output or the statement that nothing was skipped or left.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the `aw check all` summary beside the E-01 baseline, the summary line of bare `python3 -m pytest`, and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Before editing any spec, backlog item, or plan, read `.aw/system/workflows/standards/technical-artifact-writing.md` once Order 01 has shipped it (before that, the maintainer draft summarized in spec `ecmw83` Section 6). Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited and justified in the finalize scope reconciliation. Commit only through `aw commit 381ml6 -- <paths>`; never push. Paste actual test output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
