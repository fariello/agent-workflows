# IPD: Sweep live specs against the writing standard

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-08 and MD-3 to MD-5 require a one-time proofread of every live spec against the writing standard, adding diagrams where requirement 12 applies. Live specs at authoring time: 3 draft, 1 to-review, 1 reviewed, 10 approved, 2 implementing, 1 parked (about 12,700 lines), plus spec `ecmw83` itself. Approved specs keep their status (MD-4).
- Scope: Proofread every spec in `.aw/records/specs/{draft,to-review,reviewed,approved,implementing,parked}/` (and `deferred/` if it exists at execution) at execution time, add diagrams per requirement 12, and append one `aw specs note` per changed spec. EXCLUDES `implemented/` and `superseded/` specs (spec N3), any change of status, approval, requirement IDs, acceptance criteria, or decisions, and quoted or recorded evidence.
- Scope-Paths: .aw/records/specs/draft/, .aw/records/specs/to-review/, .aw/records/specs/reviewed/, .aw/records/specs/approved/, .aw/records/specs/implementing/, .aw/records/specs/parked/, .aw/records/walkthroughs/
- Item-Dependencies: executed:g4719s, executed:gzhw9c, executed:k2x0yl, executed:e4n4p3
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Backlog: qph7c5
- From-Spec: ecmw83
- Set: writestd
- Order: 7
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: sfez3e

## Workflow history
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Bring every live spec up to the writing standard once, without changing what any spec requires.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline and sweep

- [ ] E-01 Record the baseline: the `aw check all` summary line, the list of live specs with their statuses (`aw find specs` or a directory listing), and `aw specs check` output. Save them in the walkthrough (E-05) working section.
  - Depends on: none
  - Expected outcome: the baseline is recorded.
  - Execution state: pending

- [ ] E-02 For each live spec, in path order: proofread per the standard; replace every prose em or en dash (the Order 03 advisory `spec.prose-dash` lists them; quoted text and evidence are exempt); add an entity diagram and a flow or state diagram where requirement 12 applies and none exists; check every existing diagram against the text. Keep requirement IDs, acceptance-criterion IDs, decision IDs, headings that other artifacts cite, and identifiers unchanged. Where meaning is unclear, keep the original and add an `Unresolved` annotation (R-11). Do this one spec per commit-ready unit so a reviewer can read each diff alone.
  - Depends on: E-01
  - Expected outcome: every live spec has been proofread.
  - Execution state: pending

- [ ] E-03 For each spec changed by E-02, run `aw specs note <id6> --message "proofread per technical-artifact-writing standard (spec ecmw83); meaning unchanged"`, adding "; N Unresolved annotations" when E-02 added any.
  - Depends on: E-02
  - Expected outcome: each changed spec carries the note.
  - Execution state: pending

- [ ] E-04 Confirm no status, `- Blocks-Release:`, `- Id:`, `- From-*:`, `- Graduated-To:`, or approval line changed: diff the metadata blocks of every swept spec against the E-01 commit.
  - Depends on: E-03
  - Expected outcome: no metadata changed except none.
  - Execution state: pending

- [ ] E-05 Write `.aw/records/walkthroughs/<date>-writestd-07-spec-sweep-walkthrough.md`: the specs swept, diagrams added per spec, every `Unresolved` annotation with its location, and the baseline and final check outputs. Confirm `aw specs check` reports no `spec.prose-dash` advisory outside quotations and evidence.
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

## Findings

- Largest live specs: `25kzda` (about 1,800 lines), `yfz5u9` (about 2,150), `4sd62s` (about 1,690), `18hh1u` (about 1,470). Several already carry Mermaid diagrams, which E-02 checks rather than replaces.
- Spec `k3yx72` is amended by Order 06 before this plan runs; E-02 proofreads the amended text.

## Proposed changes (ordered, validatable)

1. Baseline (E-01).
2. Sweep and note (E-02, E-03).
3. Prove metadata unchanged and report (E-04, E-05).
4. Check, gate, commit (E-06).

## Deferred / out of scope (with reason)

- Terminal specs: out of scope by spec `ecmw83` N3.
  - Carrier-Declined: deliberate non-goal.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`aw specs check`, `aw check all`, the metadata diff in V-04, the bare suite.

## Spec / documentation sync

Edits the live specs listed above for wording only. Their requirements do not change, so no spec contract changes; each spec records the proofread in its history.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the three outputs.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste, per spec, `git diff --stat <spec>` and the count of diagrams added; paste `aw specs check` showing all specs conform.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `aw specs note` outputs and `git diff` showing only history lines added by this step.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a command such as `git diff <E-01 commit> -- .aw/records/specs/ | grep '^[-+]- \(Status\|Id\|Blocks-Release\|From-\|Graduated-To\|Approval\):'` printing nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the walkthrough path, its table of specs, and the final `aw specs check --agent` advisory count.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `aw check all` summary beside the E-01 baseline, the summary line of bare `python3 -m pytest`, and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Before editing any spec, backlog item, or plan, read `.aw/system/workflows/standards/technical-artifact-writing.md` once Order 01 has shipped it (before that, the maintainer draft summarized in spec `ecmw83` Section 6). Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited and justified in the finalize scope reconciliation. Commit only through `aw commit sfez3e -- <paths>`; never push. Paste actual test output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
