# IPD: Sweep live backlog items against the writing standard

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-08 and MD-5 require a one-time proofread of every live backlog item against the writing standard, including parked items. At authoring time: 18 open, 6 graduated, 15 parked, 0 blocked (about 76 KB), plus item `qph7c5`.
- Scope: Proofread every item in `.aw/records/backlog/{open,graduated,parked}/` (and `blocked/` if it exists at execution) at execution time, add diagrams where requirement 12 applies, and append one `aw backlog note` per changed item. EXCLUDES `done/` items and any change of status, priority, work kind, gate, release gate, or exemption fields.
- Scope-Paths: .aw/records/backlog/open/, .aw/records/backlog/graduated/, .aw/records/backlog/parked/, .aw/records/walkthroughs/
- Item-Dependencies: executed:g4719s, executed:gzhw9c, executed:k2x0yl, executed:e4n4p3
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Backlog: qph7c5
- From-Spec: ecmw83
- Set: writestd
- Order: 8
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: uog8nc

## Workflow history
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Bring every live backlog item up to the writing standard once, without changing what any item asks for.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline and sweep

- [ ] E-01 Record the baseline: the `aw check all` summary line, `aw backlog check` output, and the list of live items with status.
  - Depends on: none
  - Expected outcome: the baseline is recorded.
  - Execution state: pending

- [ ] E-02 For each live item, in path order: proofread per the standard (the "Backlog item" focus of the procedure: a bounded outcome and acceptance); replace prose em or en dashes (advisory `backlog.prose-dash`); add a diagram only where requirement 12 applies. Keep measured numbers, pasted evidence, and quoted commands unchanged. Where meaning is unclear, keep the original and add an `Unresolved` annotation.
  - Depends on: E-01
  - Expected outcome: every live item has been proofread.
  - Execution state: pending

- [ ] E-03 For each item changed by E-02, run `aw backlog note <id6> --message "proofread per technical-artifact-writing standard (spec ecmw83); meaning unchanged"`.
  - Depends on: E-02
  - Expected outcome: each changed item carries the note.
  - Execution state: pending

- [ ] E-04 Confirm no `- Status:`, `- Priority:`, `- Work-Kind:`, `- Gate-*:`, `- Blocks-Release:`, `- Release-Exempt-*:`, `- Id:`, `- Set:`, or `- Summary:` line changed, by diffing against the E-01 commit.
  - Depends on: E-03
  - Expected outcome: no metadata changed.
  - Execution state: pending

- [ ] E-05 Write `.aw/records/walkthroughs/<date>-writestd-08-backlog-sweep-walkthrough.md`: items swept, diagrams added, every `Unresolved` annotation, baseline and final outputs.
  - Depends on: E-04
  - Expected outcome: the walkthrough exists.
  - Execution state: pending

- [ ] E-06 Run `aw check all`, compare with the E-01 baseline, run the routine gate, and commit.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: no new `aw check` error; the bare suite passes; the commit holds only swept artifacts and the report.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Read `.aw/system/workflows/standards/technical-artifact-writing.md` in full before E-02; apply its "Proofreading procedure" section.
- A writing correction never changes scope, obligations, status, approval, identity, or provenance (standard "Purpose and scope"; spec `ecmw83` R-08).
- Status and history are owned by `aw specs`, `aw backlog`, and `aw ipd`; do not hand-edit status lines.
- Report sweep results in a walkthrough under `.aw/records/walkthroughs/`.
- `- Summary:` is a one-line identity surface used by duplicate detection; leave it unchanged even when its wording could improve, and record the suggested wording in the walkthrough.

## Findings

- No blocked items exist at authoring time; E-02 still covers `blocked/` if items appear.

## Proposed changes (ordered, validatable)

1. Baseline (E-01).
2. Sweep and note (E-02, E-03).
3. Prove metadata unchanged and report (E-04, E-05).
4. Check, gate, commit (E-06).

## Deferred / out of scope (with reason)

- `done/` items: spec `ecmw83` N3.
  - Carrier-Declined: deliberate non-goal.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`aw backlog check`, `aw check all`, V-04's metadata diff, the bare suite.

## Spec / documentation sync

N/A: backlog items only; no spec contract changes.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the three outputs.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste, per item, `git diff --stat <item>`; paste `aw backlog check` showing the tree conforms.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `aw backlog note` outputs.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a `git diff <E-01 commit> -- .aw/records/backlog/ | grep` over those keys printing nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the walkthrough path and its table of items.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `aw check all` summary beside the E-01 baseline, the summary line of bare `python3 -m pytest`, and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Before editing any spec, backlog item, or plan, read `.aw/system/workflows/standards/technical-artifact-writing.md` once Order 01 has shipped it (before that, the maintainer draft summarized in spec `ecmw83` Section 6). Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited and justified in the finalize scope reconciliation. Commit only through `aw commit uog8nc -- <paths>`; never push. Paste actual test output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
